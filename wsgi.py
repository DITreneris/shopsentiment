from flask import Flask, jsonify, request
from datetime import datetime

app = Flask(__name__)

# Mock product data
PRODUCTS = [
    {
        "id": "B123456789",
        "name": "Example Product 1",
        "sentiment": "positive",
        "reviews_count": 5,
        "description": "This is a high-quality product with excellent features.",
        "price": "$49.99",
        "rating": 4.7
    },
    {
        "id": "E123456789",
        "name": "Example Product 2",
        "sentiment": "neutral",
        "reviews_count": 3,
        "description": "A standard product that meets expectations.",
        "price": "$29.99",
        "rating": 3.5
    },
    {
        "id": "C123456789",
        "name": "Example Product 3",
        "sentiment": "negative",
        "reviews_count": 7,
        "description": "This product has received mixed reviews.",
        "price": "$39.99",
        "rating": 2.1
    }
]

@app.route('/')
def home():
    # Create HTML for product cards
    product_cards = ""
    for product in PRODUCTS:
        sentiment_class = product["sentiment"]
        product_cards += f"""
        <div class="product-card {sentiment_class}">
            <h3>{product["name"]} <span class="badge {sentiment_class}">{sentiment_class}</span></h3>
            <p>Price: {product["price"]}</p>
            <p>Rating: {product["rating"]}/5 ({product["reviews_count"]} reviews)</p>
            <p>{product["description"]}</p>
            <div class="view-details">View Details →</div>
        </div>
        """
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Shop Sentiment Analysis</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
                color: #333;
            }}
            
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            
            h1, h2 {{
                color: #4285f4;
            }}
            
            h1 {{
                text-align: center;
                margin-bottom: 30px;
            }}
            
            h2 {{
                border-bottom: 1px solid #eee;
                padding-bottom: 10px;
            }}
            
            .success-message {{
                background-color: #d4edda;
                color: #155724;
                padding: 10px;
                border-radius: 4px;
                text-align: center;
                margin-bottom: 20px;
            }}
            
            .product-card {{
                border: 1px solid #ddd;
                padding: 15px;
                margin-bottom: 15px;
                border-radius: 5px;
                position: relative;
            }}
            
            .product-card h3 {{
                margin-top: 0;
            }}
            
            .badge {{
                display: inline-block;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 12px;
                margin-left: 10px;
                color: white;
            }}
            
            .positive {{ border-left: 5px solid #28a745; }}
            .neutral {{ border-left: 5px solid #ffc107; }}
            .negative {{ border-left: 5px solid #dc3545; }}
            
            .badge.positive {{ background-color: #28a745; }}
            .badge.neutral {{ background-color: #ffc107; color: black; }}
            .badge.negative {{ background-color: #dc3545; }}
            
            .view-details {{
                position: absolute;
                bottom: 15px;
                right: 15px;
                font-size: 14px;
                color: #666;
            }}
            
            .sentiment-analyzer {{
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 5px;
                margin-top: 30px;
            }}
            
            textarea {{
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                height: 100px;
                margin-bottom: 10px;
                box-sizing: border-box;
            }}
            
            button {{
                background-color: #4285f4;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }}
            
            button:hover {{
                background-color: #3367d6;
            }}
            
            #result {{
                margin-top: 20px;
                padding: 15px;
                border-radius: 4px;
                display: none;
            }}
            
            .loader {{
                border: 5px solid #f3f3f3;
                border-top: 5px solid #3498db;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 2s linear infinite;
                margin: 20px auto;
                display: none;
            }}
            
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
            
            footer {{
                text-align: center;
                margin-top: 20px;
                color: #666;
                font-size: 14px;
            }}
            
            @media (max-width: 600px) {{
                .container {{
                    padding: 10px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Shop Sentiment Analysis</h1>
            
            <div class="success-message">
                <p>🎉 Application is working correctly! 🎉</p>
            </div>
            
            <div class="products">
                <h2>Products</h2>
                {product_cards}
            </div>
            
            <div class="sentiment-analyzer">
                <h2>Analyze Sentiment</h2>
                <p>Type or paste some text to analyze its sentiment:</p>
                <textarea id="sentiment-text" placeholder="Enter text to analyze sentiment..."></textarea>
                <button id="analyze-btn">Analyze Sentiment</button>
                <div class="loader" id="analyze-loader"></div>
                <div id="result"></div>
            </div>
            
            <footer>
                <p>&copy; 2025 Shop Sentiment Analysis</p>
            </footer>
        </div>
        
        <script>
            document.getElementById('analyze-btn').addEventListener('click', function() {
                const text = document.getElementById('sentiment-text').value.trim();
                const loader = document.getElementById('analyze-loader');
                const result = document.getElementById('result');
                
                if (!text) {
                    alert('Please enter some text to analyze.');
                    return;
                }
                
                // Show loader, hide result
                loader.style.display = 'block';
                result.style.display = 'none';
                
                // Make API request
                fetch('/api/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ text: text })
                })
                .then(response => response.json())
                .then(data => {
                    // Hide loader
                    loader.style.display = 'none';
                    
                    // Show result
                    result.style.display = 'block';
                    
                    if (data.result) {
                        const sentiment = data.result.sentiment;
                        const score = data.result.score;
                        
                        let sentimentColor = '';
                        if (sentiment === 'positive') {
                            sentimentColor = '#28a745';
                            result.style.backgroundColor = '#d4edda';
                        } else if (sentiment === 'negative') {
                            sentimentColor = '#dc3545';
                            result.style.backgroundColor = '#f8d7da';
                        } else {
                            sentimentColor = '#ffc107';
                            result.style.backgroundColor = '#fff3cd';
                        }
                        
                        result.innerHTML = `
                            <h3>Sentiment Analysis Result</h3>
                            <p>Sentiment: <strong style="color: ${sentimentColor}">${sentiment}</strong></p>
                            <p>Score: <strong>${score}</strong></p>
                            <p><small>Analyzed at: ${new Date().toLocaleString()}</small></p>
                        `;
                    } else {
                        result.style.backgroundColor = '#f8d7da';
                        result.innerHTML = '<p>Error analyzing sentiment.</p>';
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    loader.style.display = 'none';
                    result.style.display = 'block';
                    result.style.backgroundColor = '#f8d7da';
                    result.innerHTML = '<p>Error analyzing sentiment. Please try again later.</p>';
                });
            });
        </script>
    </body>
    </html>
    """

@app.route('/api/products')
def get_products():
    return jsonify({"products": PRODUCTS})

@app.route('/api/analyze', methods=['POST'])
def analyze_text():
    data = request.json
    if not data or 'text' not in data:
        return jsonify({"error": "Text is required"}), 400
    
    text = data['text']
    # Simple sentiment analysis
    if any(word in text.lower() for word in ['great', 'good', 'excellent', 'happy', 'satisfied', 'love', 'awesome', 'perfect']):
        sentiment = "positive"
        score = 0.8
    elif any(word in text.lower() for word in ['bad', 'poor', 'terrible', 'awful', 'disappointed', 'hate', 'worst', 'useless']):
        sentiment = "negative"
        score = 0.2
    else:
        sentiment = "neutral"
        score = 0.5
    
    return jsonify({
        "result": {
            "sentiment": sentiment,
            "score": score,
            "timestamp": str(datetime.now())
        }
    })

@app.route('/api/health')
def health_check():
    return jsonify({
        "status": "ok",
        "message": "Application is running"
    })

if __name__ == "__main__":
    app.run() 