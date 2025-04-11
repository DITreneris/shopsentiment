from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import pandas as pd
from data_collection import DataCollector
from model import RecommendationModel
from performance_optimization import PerformanceOptimizer
from config import API_HOST, API_PORT, API_WORKERS
import uvicorn
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Shop Sentiment Recommendation System",
    description="API for product recommendations and trend predictions",
    version="1.0.0"
)

# Initialize components
data_collector = DataCollector()
model = RecommendationModel()
optimizer = PerformanceOptimizer()

# Try to load model at startup
try:
    model.load_model()
    logger.info("Model loaded successfully at startup")
except Exception as e:
    logger.warning(f"Could not load model at startup: {str(e)}")

class ProductRequest(BaseModel):
    product_id: str
    name: str
    category: str
    price: float
    sales_data: Dict[str, Any] = None
    customer_reviews: Dict[str, Any] = None

class BatchProductRequest(BaseModel):
    products: List[ProductRequest]

class RecommendationResponse(BaseModel):
    product_id: str
    name: str
    predicted_popularity: float
    confidence_score: float
    similar_products: List[Dict[str, Any]]
    
class BatchRecommendationResponse(BaseModel):
    recommendations: List[RecommendationResponse]
    processing_time_ms: float

class PerformanceMetrics(BaseModel):
    endpoint: str
    response_time_ms: float
    timestamp: datetime
    request_size: int

# In-memory metrics store
performance_metrics = []

@app.middleware("http")
async def add_performance_metrics(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    
    # Store performance metric
    performance_metrics.append({
        "endpoint": request.url.path,
        "response_time_ms": process_time,
        "timestamp": datetime.now(),
        "request_size": int(request.headers.get("content-length", 0))
    })
    
    # Keep only the last 1000 metrics
    if len(performance_metrics) > 1000:
        performance_metrics.pop(0)
    
    return response

@app.get("/")
@optimizer.profile_function
async def root():
    return {"message": "Shop Sentiment Recommendation System API"}

@app.post("/recommend", response_model=RecommendationResponse)
@optimizer.profile_function
async def get_recommendation(product: ProductRequest):
    try:
        # Make prediction
        start_time = time.time()
        prediction = model.predict(product.dict())
        prediction_time = time.time() - start_time
        
        # Get similar products using optimized query
        similar_products = data_collector.collect_product_data()
        similar_products = sorted(
            similar_products,
            key=lambda x: abs(x['price'] - product.price)
        )[:5]
        
        logger.info(f"Recommendation for {product.product_id} generated in {prediction_time:.4f}s")
        
        return {
            "product_id": product.product_id,
            "name": product.name,
            "predicted_popularity": prediction,
            "confidence_score": 0.85,  # Placeholder, should be calculated based on model confidence
            "similar_products": similar_products
        }
        
    except Exception as e:
        logger.error(f"Error generating recommendation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch-recommend", response_model=BatchRecommendationResponse)
@optimizer.profile_function
async def batch_recommend(request: BatchProductRequest):
    try:
        start_time = time.time()
        
        # Extract product data
        product_data_list = [p.dict() for p in request.products]
        
        # Make batch predictions
        predictions = model.batch_predict(product_data_list)
        
        # Collect product data once for efficiency
        all_products = data_collector.collect_product_data()
        
        # Create recommendations
        recommendations = []
        for i, product in enumerate(request.products):
            # Get similar products - filter in Python memory for speed
            similar_products = sorted(
                all_products,
                key=lambda x: abs(x['price'] - product.price)
            )[:5]
            
            recommendations.append({
                "product_id": product.product_id,
                "name": product.name,
                "predicted_popularity": predictions[i],
                "confidence_score": 0.85,
                "similar_products": similar_products
            })
        
        processing_time = (time.time() - start_time) * 1000
        
        return {
            "recommendations": recommendations,
            "processing_time_ms": processing_time
        }
        
    except Exception as e:
        logger.error(f"Error generating batch recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/train")
@optimizer.profile_function
async def train_model(background_tasks: BackgroundTasks):
    try:
        # Start training in background
        background_tasks.add_task(train_model_task)
        
        return {
            "status": "Training started in background",
            "message": "Check /status endpoint for progress"
        }
        
    except Exception as e:
        logger.error(f"Error starting model training: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Global variable to track training status
training_status = {
    "is_training": False,
    "start_time": None,
    "end_time": None,
    "status": "not_started",
    "metrics": None
}

async def train_model_task():
    """Background task for model training"""
    global training_status
    
    if training_status["is_training"]:
        return
    
    training_status["is_training"] = True
    training_status["start_time"] = datetime.now()
    training_status["status"] = "in_progress"
    
    try:
        # Collect data
        products = data_collector.collect_product_data()
        
        # Train model
        metrics = model.train(pd.DataFrame(products))
        
        training_status["metrics"] = metrics
        training_status["status"] = "completed"
        logger.info("Model training completed successfully")
        
    except Exception as e:
        training_status["status"] = "failed"
        training_status["error"] = str(e)
        logger.error(f"Error in background training: {str(e)}")
        
    finally:
        training_status["is_training"] = False
        training_status["end_time"] = datetime.now()

@app.get("/status")
async def get_training_status():
    """Get the current training status"""
    return training_status

@app.get("/performance")
async def get_performance_metrics():
    """Get API performance metrics"""
    metrics_df = pd.DataFrame(performance_metrics)
    
    if metrics_df.empty:
        return {"metrics": "No performance data available yet"}
    
    # Calculate statistics
    endpoint_stats = metrics_df.groupby("endpoint").agg({
        "response_time_ms": ["mean", "min", "max", "count"]
    }).reset_index()
    
    # Format for response
    stats = []
    for _, row in endpoint_stats.iterrows():
        stats.append({
            "endpoint": row["endpoint"],
            "mean_response_time_ms": row[("response_time_ms", "mean")],
            "min_response_time_ms": row[("response_time_ms", "min")],
            "max_response_time_ms": row[("response_time_ms", "max")],
            "request_count": row[("response_time_ms", "count")]
        })
    
    return {
        "statistics": stats,
        "recent_metrics": performance_metrics[-10:]  # Last 10 requests
    }

if __name__ == "__main__":
    # Optimize collections at startup
    data_collector.optimize_collections()
    
    uvicorn.run(
        "api:app",
        host=API_HOST,
        port=API_PORT,
        workers=API_WORKERS,
        reload=True
    ) 