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
        "reviews_count": 5
    },
    {
        "id": "E123456789",
        "name": "Example Product 2",
        "sentiment": "neutral",
        "reviews_count": 3
    },
    {
        "id": "C123456789",
        "name": "Example Product 3",
        "sentiment": "negative",
        "reviews_count": 7
    }
]

@app.route('/api/products', methods=['GET'])
def get_products():
    return jsonify({"products": PRODUCTS})

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
            }
            .product-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 5px 15px rgba(0,0,0,0.1);
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
                                        <h3>${product.name} <span class="badge ${product.sentiment}">${product.sentiment}</span></h3>
                                        <p>ID: ${product.id}</p>
                                        <p>Reviews: ${product.reviews_count}</p>
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