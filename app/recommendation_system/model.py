import logging
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from typing import Tuple, Dict, Any, List
from config import MODEL_SAVE_PATH, MIN_TRAINING_SAMPLES
from performance_optimization import PerformanceOptimizer

logger = logging.getLogger(__name__)

class RecommendationModel:
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.optimizer = PerformanceOptimizer()
        
    @PerformanceOptimizer.profile_function
    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Prepare features for model training
        """
        try:
            # Optimize memory usage before processing
            df = self.optimizer.optimize_dataframe(df)
            
            # Basic feature engineering
            features = pd.DataFrame()
            
            # Price features
            features['price'] = df['price']
            features['price_log'] = np.log1p(df['price'])
            
            # Category features (one-hot encoding)
            category_dummies = pd.get_dummies(df['category'], prefix='category')
            features = pd.concat([features, category_dummies], axis=1)
            
            # Process sales features in batches if dataframe is large
            if 'sales_data' in df.columns and len(df) > 10000:
                def process_sales_batch(batch):
                    return [
                        {'total': x.get('total', 0), 'avg_daily': x.get('avg_daily', 0)}
                        for x in batch
                    ]
                
                sales_data = self.optimizer.batch_process(
                    df['sales_data'].tolist(),
                    process_sales_batch,
                    batch_size=1000
                )
                
                features['total_sales'] = [x['total'] for x in sales_data]
                features['avg_daily_sales'] = [x['avg_daily'] for x in sales_data]
            elif 'sales_data' in df.columns:
                features['total_sales'] = df['sales_data'].apply(lambda x: x.get('total', 0))
                features['avg_daily_sales'] = df['sales_data'].apply(lambda x: x.get('avg_daily', 0))
            
            # Process review features
            if 'customer_reviews' in df.columns:
                features['avg_rating'] = df['customer_reviews'].apply(lambda x: x.get('avg_rating', 0))
                features['review_count'] = df['customer_reviews'].apply(lambda x: x.get('count', 0))
            
            # Target variable (using sales as proxy for popularity)
            target = features['total_sales'] if 'total_sales' in features.columns else features['price']
            
            # Remove target from features
            features = features.drop(['total_sales'], axis=1, errors='ignore')
            
            # Optimize memory of final feature dataframe
            features = self.optimizer.optimize_dataframe(features)
            
            self.feature_columns = features.columns
            
            return features, target
            
        except Exception as e:
            logger.error(f"Error preparing features: {str(e)}")
            raise
            
    @PerformanceOptimizer.profile_function
    @PerformanceOptimizer.cache_result(ttl=86400)  # Cache for 24 hours
    def train(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Train the recommendation model
        """
        try:
            if len(df) < MIN_TRAINING_SAMPLES:
                raise ValueError(f"Not enough training samples. Minimum required: {MIN_TRAINING_SAMPLES}")
            
            # Prepare features
            X, y = self.prepare_features(df)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model with parallel processing
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1  # Use all available cores
            )
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Compute feature importance and find most important features
            feature_importance = dict(zip(X.columns, self.model.feature_importances_))
            important_features = sorted(
                feature_importance.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]  # Top 10 features
            
            # Save model
            self.save_model()
            
            return {
                'mse': mse,
                'r2_score': r2,
                'feature_importance': feature_importance,
                'important_features': important_features
            }
            
        except Exception as e:
            logger.error(f"Error training model: {str(e)}")
            raise
            
    @PerformanceOptimizer.profile_function
    @PerformanceOptimizer.cache_result(ttl=3600)  # Cache for 1 hour
    def predict(self, product_data: Dict[str, Any]) -> float:
        """
        Make predictions for a single product
        """
        try:
            if self.model is None:
                self.load_model()
                if self.model is None:
                    raise ValueError("Model could not be loaded")
            
            # Convert input to DataFrame
            df = pd.DataFrame([product_data])
            
            # Prepare features
            X, _ = self.prepare_features(df)
            
            # Scale features
            X_scaled = self.scaler.transform(X)
            
            # Make prediction
            prediction = self.model.predict(X_scaled)[0]
            
            return prediction
            
        except Exception as e:
            logger.error(f"Error making prediction: {str(e)}")
            raise
    
    @PerformanceOptimizer.profile_function
    def batch_predict(self, product_data_list: List[Dict[str, Any]]) -> List[float]:
        """
        Make predictions for multiple products in batch
        """
        try:
            if self.model is None:
                self.load_model()
                if self.model is None:
                    raise ValueError("Model could not be loaded")
            
            # Process in batches
            def predict_batch(batch):
                # Convert batch to DataFrame
                batch_df = pd.DataFrame(batch)
                
                # Prepare features
                X, _ = self.prepare_features(batch_df)
                
                # Scale features
                X_scaled = self.scaler.transform(X)
                
                # Make predictions
                return self.model.predict(X_scaled).tolist()
            
            # Use batch processing for predictions
            predictions = self.optimizer.batch_process(
                product_data_list,
                predict_batch,
                batch_size=100,
                use_multiprocessing=True  # Use multiprocessing for CPU-bound predictions
            )
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error making batch predictions: {str(e)}")
            raise
            
    @PerformanceOptimizer.profile_function
    def save_model(self):
        """
        Save the trained model and scaler
        """
        try:
            model_data = {
                'model': self.model,
                'scaler': self.scaler,
                'feature_columns': self.feature_columns
            }
            joblib.dump(model_data, MODEL_SAVE_PATH, compress=3)  # Use compression
            logger.info(f"Model saved to {MODEL_SAVE_PATH}")
            
        except Exception as e:
            logger.error(f"Error saving model: {str(e)}")
            raise
            
    @PerformanceOptimizer.profile_function
    def load_model(self):
        """
        Load the trained model and scaler
        """
        try:
            model_data = joblib.load(MODEL_SAVE_PATH)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            self.feature_columns = model_data['feature_columns']
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise 