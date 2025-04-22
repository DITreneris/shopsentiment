"""
Sentiment Analysis API endpoints for the ShopSentiment application.
Provides routes for analyzing sentiment in text.
"""

import logging
from flask import Blueprint, jsonify, request
from flask import current_app

logger = logging.getLogger(__name__)

# Create a Blueprint for the sentiment API
sentiment_bp = Blueprint('sentiment_api', __name__)


@sentiment_bp.route('/analyze', methods=['POST'])
def analyze_sentiment():
    """Analyze the sentiment of provided text."""
    try:
        # Get the analyzer from the app context
        sentiment_service = current_app.extensions.get('sentiment_service')
        if not sentiment_service or not hasattr(sentiment_service, 'analyzer'):
            logger.error("Sentiment service or analyzer not available in app context.")
            return jsonify({'error': 'Service unavailable', 'message': 'Sentiment analysis service is not configured.'}), 503

        analyzer = sentiment_service.analyzer

        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({
                'error': 'Bad request',
                'message': 'Missing text parameter'
            }), 400
            
        text = data['text']
        logger.info(f'API request to analyze sentiment for text: {text[:50]}...')
        
        # Try both methods to be compatible with different analyzer implementations
        if hasattr(analyzer, 'analyze_text'):
            sentiment = analyzer.analyze_text(text)
        elif hasattr(analyzer, 'analyze'): # Check for older 'analyze' method
            sentiment = analyzer.analyze(text)
        else:
            logger.error("Analyzer object does not have a recognized analysis method.")
            return jsonify({'error': 'Configuration error', 'message': 'Sentiment analyzer is not correctly configured.'}), 500
        
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
        # Get the analyzer from the app context
        sentiment_service = current_app.extensions.get('sentiment_service')
        if not sentiment_service or not hasattr(sentiment_service, 'analyzer'):
            logger.error("Sentiment service or analyzer not available in app context.")
            return jsonify({'error': 'Service unavailable', 'message': 'Sentiment analysis service is not configured.'}), 503

        analyzer = sentiment_service.analyzer

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
                
            # Try both methods to be compatible with different analyzer implementations
            if hasattr(analyzer, 'analyze_text'):
                sentiment = analyzer.analyze_text(text)
            elif hasattr(analyzer, 'analyze'): # Check for older 'analyze' method
                sentiment = analyzer.analyze(text)
            else:
                logger.error(f"Analyzer object does not have a recognized analysis method for text: {text[:30]}...")
                # Add error for this specific text, but continue batch
                results.append({
                    'text': text,
                    'error': 'Analyzer configuration error for this item.'
                })
                continue
                
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