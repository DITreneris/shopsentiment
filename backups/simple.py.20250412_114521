from flask import Flask, send_from_directory, jsonify, request
import os
import json
from datetime import datetime

app = Flask(__name__)

# Mock data
PRODUCTS = [
    {
        "id": "B123456789",
        "name": "Example Product 1",
        "sentiment": "positive",
        "reviews_count": 5,
        "description": "This is a high-quality product with excellent features. Users love its durability and ease of use.",
        "price": "$49.99",
        "rating": 4.7,
        "features": ["Durable", "Easy to use", "Long battery life", "Lightweight"],
        "image_url": "https://via.placeholder.com/300x200?text=Product+1"
    },
    {
        "id": "E123456789",
        "name": "Example Product 2",
        "sentiment": "neutral",
        "reviews_count": 3,
        "description": "A standard product that meets most user expectations. Some find it useful while others think it's just average.",
        "price": "$29.99",
        "rating": 3.5,
        "features": ["Affordable", "Standard quality", "Easy setup"],
        "image_url": "https://via.placeholder.com/300x200?text=Product+2"
    },
    {
        "id": "C123456789",
        "name": "Example Product 3",
        "sentiment": "negative",
        "reviews_count": 7,
        "description": "This product has received mixed reviews, with many users reporting issues with quality and reliability.",
        "price": "$39.99",
        "rating": 2.1,
        "features": ["Low cost", "Fast shipping", "Multiple colors"],
        "image_url": "https://via.placeholder.com/300x200?text=Product+3"
    }
]

# Mock reviews
REVIEWS = {
    "B123456789": [
        {"text": "Great product, very satisfied!", "sentiment": "positive", "author": "John D.", "date": "2025-03-15", "rating": 5},
        {"text": "Works as expected, good value.", "sentiment": "positive", "author": "Sarah M.", "date": "2025-03-10", "rating": 4},
        {"text": "Better than I expected!", "sentiment": "positive", "author": "Robert K.", "date": "2025-02-28", "rating": 5},
        {"text": "Good quality for the price.", "sentiment": "positive", "author": "Lisa T.", "date": "2025-02-22", "rating": 4},
        {"text": "Would recommend to friends.", "sentiment": "positive", "author": "Michael P.", "date": "2025-02-15", "rating": 5}
    ],
    "E123456789": [
        {"text": "It's okay, nothing special.", "sentiment": "neutral", "author": "David W.", "date": "2025-03-12", "rating": 3},
        {"text": "Average product, does the job.", "sentiment": "neutral", "author": "Emily R.", "date": "2025-02-25", "rating": 3},
        {"text": "Decent quality, expected more features.", "sentiment": "neutral", "author": "James L.", "date": "2025-02-10", "rating": 4}
    ],
    "C123456789": [
        {"text": "Disappointed with the quality.", "sentiment": "negative", "author": "Patricia G.", "date": "2025-03-20", "rating": 2},
        {"text": "Not worth the money.", "sentiment": "negative", "author": "Thomas H.", "date": "2025-03-05", "rating": 1},
        {"text": "Broke after a week of use.", "sentiment": "negative", "author": "Jessica F.", "date": "2025-02-28", "rating": 1},
        {"text": "Poor customer service experience.", "sentiment": "negative", "author": "Richard S.", "date": "2025-02-20", "rating": 2},
        {"text": "Would not recommend.", "sentiment": "negative", "author": "Jennifer B.", "date": "2025-02-15", "rating": 2},
        {"text": "Doesn't work as advertised.", "sentiment": "negative", "author": "Charles M.", "date": "2025-02-10", "rating": 2},
        {"text": "Very frustrating to use.", "sentiment": "negative", "author": "Karen L.", "date": "2025-02-05", "rating": 3}
    ]
}

# Mock sentiment analysis
SENTIMENT = {
    "B123456789": {"positive": 80, "neutral": 15, "negative": 5, "score": 0.8},
    "E123456789": {"positive": 30, "neutral": 60, "negative": 10, "score": 0.55},
    "C123456789": {"positive": 10, "neutral": 15, "negative": 75, "score": 0.2}
}

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify({"products": PRODUCTS})

@app.route('/api/products/<product_id>', methods=['GET'])
def get_product(product_id):
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        return jsonify({"error": "Product not found"}), 404
    return jsonify({"product": product})

@app.route('/api/products/<product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    if product_id not in REVIEWS:
        return jsonify({"error": "Reviews not found"}), 404
    return jsonify({"reviews": REVIEWS[product_id]})

@app.route('/api/products/<product_id>/sentiment', methods=['GET'])
def get_product_sentiment(product_id):
    if product_id not in SENTIMENT:
        return jsonify({"error": "Sentiment data not found"}), 404
    return jsonify({"sentiment": SENTIMENT[product_id]})

@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"error": "Text is required"}), 400
    
    text = data['text']
    # Simple sentiment analysis
    if any(word in text.lower() for word in ['great', 'good', 'excellent', 'happy', 'satisfied']):
        sentiment = "positive"
        score = 0.8
    elif any(word in text.lower() for word in ['bad', 'poor', 'terrible', 'awful', 'disappointed']):
        sentiment = "negative"
        score = 0.2
    else:
        sentiment = "neutral"
        score = 0.5
    
    return jsonify({
        "result": {
            "sentiment": sentiment,
            "score": score,
            "timestamp": datetime.now().isoformat()
        }
    })

@app.route('/product/<product_id>')
def product_detail(product_id):
    product = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not product:
        return "Product not found", 404
        
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{product['name']} - Shop Sentiment Analysis</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
                background-color: #f5f5f5;
            }}
            .container {{
                max-width: 1000px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            h1, h2, h3 {{
                color: #4285f4;
            }}
            .header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }}
            .back-button {{
                background-color: #f1f1f1;
                color: #333;
                border: none;
                padding: 8px 15px;
                border-radius: 4px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
            }}
            .back-button:hover {{
                background-color: #e0e0e0;
            }}
            .product-details {{
                display: flex;
                margin-bottom: 30px;
            }}
            .product-image {{
                flex: 0 0 300px;
                margin-right: 30px;
            }}
            .product-image img {{
                max-width: 100%;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .product-info {{
                flex: 1;
            }}
            .rating {{
                font-size: 24px;
                color: #ffc107;
                margin-bottom: 10px;
            }}
            .price {{
                font-size: 22px;
                color: #4CAF50;
                font-weight: bold;
                margin-bottom: 15px;
            }}
            .badge {{
                display: inline-block;
                padding: 5px 10px;
                border-radius: 15px;
                color: white;
                font-size: 12px;
                font-weight: bold;
                margin-left: 10px;
            }}
            .badge.positive {{
                background-color: #28a745;
            }}
            .badge.neutral {{
                background-color: #ffc107;
                color: #333;
            }}
            .badge.negative {{
                background-color: #dc3545;
            }}
            .features {{
                margin-top: 20px;
            }}
            .features ul {{
                padding-left: 20px;
            }}
            .sentiment-summary {{
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 30px;
            }}
            .sentiment-bars {{
                margin-top: 15px;
            }}
            .sentiment-bar {{
                display: flex;
                align-items: center;
                margin-bottom: 10px;
            }}
            .sentiment-label {{
                width: 80px;
                font-weight: bold;
            }}
            .bar-container {{
                flex: 1;
                background-color: #e9ecef;
                height: 20px;
                border-radius: 10px;
                overflow: hidden;
            }}
            .bar {{
                height: 100%;
                width: 0%;
                transition: width 1s ease-in-out;
            }}
            .bar.positive {{
                background-color: #28a745;
            }}
            .bar.neutral {{
                background-color: #ffc107;
            }}
            .bar.negative {{
                background-color: #dc3545;
            }}
            .sentiment-percentage {{
                width: 50px;
                text-align: right;
                padding-left: 10px;
            }}
            .reviews {{
                margin-top: 30px;
            }}
            .review-card {{
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 15px;
            }}
            .review-header {{
                display: flex;
                justify-content: space-between;
                margin-bottom: 10px;
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }}
            .review-rating {{
                color: #ffc107;
            }}
            .review-text {{
                margin-bottom: 10px;
            }}
            .review-meta {{
                font-size: 12px;
                color: #666;
                text-align: right;
            }}
            .review-sentiment {{
                font-weight: bold;
            }}
            .review-sentiment.positive {{
                color: #28a745;
            }}
            .review-sentiment.neutral {{
                color: #ffc107;
            }}
            .review-sentiment.negative {{
                color: #dc3545;
            }}
            .loader {{
                border: 5px solid #f3f3f3;
                border-top: 5px solid #3498db;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 2s linear infinite;
                margin: 20px auto;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <a href="/" class="back-button">← Back to Products</a>
                <h1>Shop Sentiment Analysis</h1>
            </div>
            
            <div class="product-details">
                <div class="product-image">
                    <img src="{product['image_url']}" alt="{product['name']}">
                </div>
                <div class="product-info">
                    <h2>{product['name']} <span class="badge {product['sentiment']}">{product['sentiment']}</span></h2>
                    <div class="rating">
                        {'★' * int(product['rating'])}{'☆' * (5 - int(product['rating']))} {product['rating']}
                    </div>
                    <div class="price">{product['price']}</div>
                    <p>{product['description']}</p>
                    <div class="features">
                        <h3>Features:</h3>
                        <ul>
                            {''.join([f'<li>{feature}</li>' for feature in product['features']])}
                        </ul>
                    </div>
                </div>
            </div>
            
            <div class="sentiment-summary">
                <h2>Sentiment Analysis</h2>
                <p>Overall sentiment score: <strong id="sentiment-score"></strong></p>
                <div class="sentiment-bars">
                    <div class="sentiment-bar">
                        <div class="sentiment-label">Positive</div>
                        <div class="bar-container">
                            <div class="bar positive" id="positive-bar"></div>
                        </div>
                        <div class="sentiment-percentage" id="positive-percentage"></div>
                    </div>
                    <div class="sentiment-bar">
                        <div class="sentiment-label">Neutral</div>
                        <div class="bar-container">
                            <div class="bar neutral" id="neutral-bar"></div>
                        </div>
                        <div class="sentiment-percentage" id="neutral-percentage"></div>
                    </div>
                    <div class="sentiment-bar">
                        <div class="sentiment-label">Negative</div>
                        <div class="bar-container">
                            <div class="bar negative" id="negative-bar"></div>
                        </div>
                        <div class="sentiment-percentage" id="negative-percentage"></div>
                    </div>
                </div>
            </div>
            
            <div class="reviews">
                <h2>Customer Reviews ({product['reviews_count']})</h2>
                <div id="reviews-container">
                    <div class="loader" id="reviews-loader"></div>
                </div>
            </div>
        </div>
        
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                // Fetch and display sentiment data
                fetchSentimentData('{product['id']}');
                
                // Fetch and display reviews
                fetchReviews('{product['id']}');
            }});
            
            function fetchSentimentData(productId) {{
                fetch(`/api/products/${{productId}}/sentiment`)
                    .then(response => response.json())
                    .then(data => {{
                        if (data.sentiment) {{
                            const sentiment = data.sentiment;
                            document.getElementById('sentiment-score').textContent = sentiment.score.toFixed(2) + ' / 1.0';
                            
                            setTimeout(() => {{
                                // Update the bars with animation
                                const positiveBar = document.getElementById('positive-bar');
                                const neutralBar = document.getElementById('neutral-bar');
                                const negativeBar = document.getElementById('negative-bar');
                                
                                positiveBar.style.width = sentiment.positive + '%';
                                neutralBar.style.width = sentiment.neutral + '%';
                                negativeBar.style.width = sentiment.negative + '%';
                                
                                document.getElementById('positive-percentage').textContent = sentiment.positive + '%';
                                document.getElementById('neutral-percentage').textContent = sentiment.neutral + '%';
                                document.getElementById('negative-percentage').textContent = sentiment.negative + '%';
                            }}, 300);
                        }}
                    }}
                    .catch(error => {{
                        console.error('Error fetching sentiment data:', error);
                    }});
            }}
            
            function fetchReviews(productId) {{
                const reviewsLoader = document.getElementById('reviews-loader');
                reviewsLoader.style.display = 'block';
                
                fetch(`/api/products/${{productId}}/reviews`)
                    .then(response => response.json())
                    .then(data => {{
                        reviewsLoader.style.display = 'none';
                        const reviewsContainer = document.getElementById('reviews-container');
                        
                        if (data.reviews && data.reviews.length > 0) {{
                            let reviewsHTML = '';
                            
                            data.reviews.forEach(review => {{
                                reviewsHTML += `
                                    <div class="review-card">
                                        <div class="review-header">
                                            <div class="review-author">${{review.author}}</div>
                                            <div class="review-rating">${{'★'.repeat(review.rating)}}${'☆'.repeat(5 - review.rating)}}</div>
                                        </div>
                                        <div class="review-text">${{review.text}}</div>
                                        <div class="review-meta">
                                            <span class="review-date">${{review.date}}</span> | 
                                            Sentiment: <span class="review-sentiment ${{review.sentiment}}">${{review.sentiment}}</span>
                                        </div>
                                    </div>
                                `;
                            }});
                            
                            reviewsContainer.innerHTML = reviewsHTML;
                        }} else {{
                            reviewsContainer.innerHTML = '<p>No reviews available for this product.</p>';
                        }}
                    }}
                    .catch(error => {{
                        reviewsLoader.style.display = 'none';
                        console.error('Error fetching reviews:', error);
                        document.getElementById('reviews-container').innerHTML = '<p>Error loading reviews.</p>';
                    }});
            }}
        </script>
    </body>
    </html>
    """

@app.route('/')
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Shop Sentiment Analysis</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
                background-color: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            h1, h2 {
                color: #4285f4;
                text-align: center;
            }
            .success-message {
                background-color: #d4edda;
                color: #155724;
                padding: 10px;
                border-radius: 4px;
                text-align: center;
                margin-bottom: 20px;
            }
            .product-card {
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 15px;
                margin-bottom: 15px;
                transition: transform 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            .product-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            }
            .product-card a {
                text-decoration: none;
                color: inherit;
                display: block;
            }
            .positive {
                border-left: 5px solid #28a745;
            }
            .neutral {
                border-left: 5px solid #ffc107;
            }
            .negative {
                border-left: 5px solid #dc3545;
            }
            .products-container {
                margin-top: 30px;
            }
            .sentiment-analyzer {
                margin-top: 30px;
                padding: 20px;
                background-color: #f8f9fa;
                border-radius: 5px;
            }
            textarea {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-height: 100px;
                margin-bottom: 10px;
            }
            button {
                background-color: #4285f4;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
                transition: background-color 0.3s ease;
            }
            button:hover {
                background-color: #3367d6;
            }
            .result {
                margin-top: 20px;
                padding: 15px;
                border-radius: 4px;
                background-color: #e9ecef;
                display: none;
            }
            .loader {
                display: none;
                border: 5px solid #f3f3f3;
                border-top: 5px solid #3498db;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 2s linear infinite;
                margin: 20px auto;
            }
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            .badge {
                display: inline-block;
                padding: 5px 10px;
                border-radius: 15px;
                color: white;
                font-size: 12px;
                font-weight: bold;
                margin-left: 10px;
            }
            .badge.positive {
                background-color: #28a745;
                border: none;
            }
            .badge.neutral {
                background-color: #ffc107;
                color: #333;
                border: none;
            }
            .badge.negative {
                background-color: #dc3545;
                border: none;
            }
            .view-details {
                position: absolute;
                bottom: 15px;
                right: 15px;
                background-color: #f8f9fa;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 12px;
                color: #666;
            }
            .product-card:hover .view-details {
                color: #4285f4;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Shop Sentiment Analysis</h1>
            <div class="success-message">
                <p>🎉 Application successfully deployed to Heroku! 🎉</p>
                <p>The application is working correctly.</p>
            </div>
            
            <h2>Products</h2>
            <div class="products-container" id="products">
                <!-- Products will be loaded here -->
                <div class="loader" id="products-loader"></div>
            </div>
            
            <div class="sentiment-analyzer">
                <h2>Analyze Sentiment</h2>
                <p>Type or paste some text to analyze its sentiment:</p>
                <textarea id="sentiment-text" placeholder="Enter text to analyze sentiment..."></textarea>
                <button id="analyze-btn">Analyze Sentiment</button>
                <div class="loader" id="analyze-loader"></div>
                <div class="result" id="result"></div>
            </div>
        </div>
        
        <script>
            // Fetch products when page loads
            document.addEventListener('DOMContentLoaded', function() {
                fetchProducts();
                
                // Set up the analyze button
                document.getElementById('analyze-btn').addEventListener('click', function() {
                    analyzeSentiment();
                });
            });
            
            // Fetch products from the API
            function fetchProducts() {
                const productsLoader = document.getElementById('products-loader');
                productsLoader.style.display = 'block';
                
                fetch('/api/products')
                    .then(response => response.json())
                    .then(data => {
                        productsLoader.style.display = 'none';
                        const productsContainer = document.getElementById('products');
                        
                        if (data.products && data.products.length > 0) {
                            let productsHTML = '';
                            
                            data.products.forEach(product => {
                                productsHTML += `
                                    <div class="product-card ${product.sentiment}">
                                        <a href="/product/${product.id}">
                                            <h3>${product.name} <span class="badge ${product.sentiment}">${product.sentiment}</span></h3>
                                            <p>ID: ${product.id}</p>
                                            <p>Reviews: ${product.reviews_count}</p>
                                            <p>${product.description.substring(0, 100)}...</p>
                                            <div class="view-details">View Details →</div>
                                        </a>
                                    </div>
                                `;
                            });
                            
                            productsContainer.innerHTML = productsHTML;
                        } else {
                            productsContainer.innerHTML = '<p>No products found.</p>';
                        }
                    })
                    .catch(error => {
                        productsLoader.style.display = 'none';
                        console.error('Error fetching products:', error);
                        document.getElementById('products').innerHTML = '<p>Error loading products.</p>';
                    });
            }
            
            // Analyze sentiment of text
            function analyzeSentiment() {
                const text = document.getElementById('sentiment-text').value.trim();
                
                if (!text) {
                    alert('Please enter some text to analyze.');
                    return;
                }
                
                const analyzeLoader = document.getElementById('analyze-loader');
                const resultDiv = document.getElementById('result');
                
                analyzeLoader.style.display = 'block';
                resultDiv.style.display = 'none';
                
                fetch('/api/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ text: text })
                })
                    .then(response => response.json())
                    .then(data => {
                        analyzeLoader.style.display = 'none';
                        resultDiv.style.display = 'block';
                        
                        if (data.result) {
                            const sentiment = data.result.sentiment;
                            const score = data.result.score;
                            
                            let sentimentColor = '';
                            if (sentiment === 'positive') {
                                sentimentColor = '#28a745';
                            } else if (sentiment === 'negative') {
                                sentimentColor = '#dc3545';
                            } else {
                                sentimentColor = '#ffc107';
                            }
                            
                            resultDiv.innerHTML = `
                                <h3>Sentiment Analysis Result</h3>
                                <p>Sentiment: <strong style="color: ${sentimentColor}">${sentiment}</strong></p>
                                <p>Score: <strong>${score}</strong></p>
                                <p><small>Analyzed at: ${new Date().toLocaleString()}</small></p>
                            `;
                        } else {
                            resultDiv.innerHTML = '<p>Error analyzing sentiment.</p>';
                        }
                    })
                    .catch(error => {
                        analyzeLoader.style.display = 'none';
                        console.error('Error analyzing sentiment:', error);
                        resultDiv.style.display = 'block';
                        resultDiv.innerHTML = '<p>Error analyzing sentiment.</p>';
                    });
            }
        </script>
    </body>
    </html>
    """

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 