"""
Sentiment Analysis API endpoints for the ShopSentiment application.
Provides routes for analyzing sentiment in text.
"""

import logging
from flask import Blueprint, jsonify, request

# Use a try/except block to handle different import structures
try:
    # Try relative import first (preferred on Heroku)
    from ...services.sentiment_analyzer import sentiment_analyzer
except ImportError:
    try:
        # Fall back to absolute import if relative fails
        from src.services.sentiment_analyzer import sentiment_analyzer
    except ImportError:
        # Create a fallback analyzer if all imports fail
        class FallbackAnalyzer:
            def analyze(self, text):
                return {"score": 0.5, "label": "Neutral"}
                
        sentiment_analyzer = FallbackAnalyzer()
        logging.warning("Using fallback sentiment analyzer due to import errors")

logger = logging.getLogger(__name__)

# Create a Blueprint for the sentiment API
sentiment_bp = Blueprint('sentiment_api', __name__)


@sentiment_bp.route('/analyze', methods=['POST'])
def analyze_sentiment():
    """Analyze the sentiment of provided text."""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Bad request',
                'message': 'Missing text parameter'
            }), 400
            
        text = data['text']
        logger.info(f'API request to analyze sentiment for text: {text[:50]}...')
        
        # Analyze the sentiment
        sentiment = sentiment_analyzer.analyze(text)
        
        return jsonify({
            'text': text,
            'sentiment': sentiment
        })
    except Exception as e:
        logger.error(f'Error in API analyze route: {str(e)}')
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to analyze sentiment'
        }), 500


@sentiment_bp.route('/batch-analyze', methods=['POST'])
def batch_analyze_sentiment():
    """Analyze the sentiment of multiple text inputs."""
    try:
        data = request.get_json()
        if not data or 'texts' not in data or not isinstance(data['texts'], list):
            return jsonify({
                'error': 'Bad request',
                'message': 'Missing or invalid texts parameter'
            }), 400
            
        texts = data['texts']
        logger.info(f'API request to batch analyze sentiment for {len(texts)} texts')
        
        # Analyze each text
        results = []
        for text in texts:
            if not isinstance(text, str):
                results.append({
                    'text': str(text),
                    'error': 'Text must be a string'
                })
                continue
                
            sentiment = sentiment_analyzer.analyze(text)
            results.append({
                'text': text,
                'sentiment': sentiment
            })
        
        return jsonify({
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        logger.error(f'Error in API batch analyze route: {str(e)}')
        return jsonify({
            'error': 'Internal server error',
            'message': 'Failed to batch analyze sentiment'
        }), 500 