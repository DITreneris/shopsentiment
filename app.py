"""
ShopSentiment Main Application

This is the main entry point for the ShopSentiment application.
It initializes the Flask application and sets up the routes.
"""

from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Mock product data
PRODUCTS = [
    {"id": "p1", "name": "Smartphone XYZ", "sentiment": "positive", "rating": 4.8},
    {"id": "p2", "name": "Laptop ABC", "sentiment": "neutral", "rating": 3.5},
    {"id": "p3", "name": "Headphones 123", "sentiment": "negative", "rating": 2.1}
]

@app.route('/')
def index():
    # Create HTML for product listings
    products_html = ""
    for p in PRODUCTS:
        sentiment_class = p["sentiment"]
        products_html += f"""
        <div class="product-card {sentiment_class}">
            <h3>{p["name"]} <span class="badge {sentiment_class}">{sentiment_class}</span></h3>
            <p>Rating: {p["rating"]}/5.0</p>
        </div>
        """
    
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Shop Sentiment Analysis</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { 
                font-family: Arial, sans-serif; 
                max-width: 800px; 
                margin: 0 auto; 
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }
            h1 { color: #4285f4; text-align: center; }
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
                position: relative;
            }
            .badge {
                display: inline-block;
                padding: 3px 8px;
                border-radius: 3px;
                font-size: 12px;
                color: white;
                margin-left: 10px;
            }
            .positive { border-left: 5px solid #28a745; }
            .negative { border-left: 5px solid #dc3545; }
            .neutral { border-left: 5px solid #ffc107; }
            .badge.positive { background-color: #28a745; }
            .badge.negative { background-color: #dc3545; }
            .badge.neutral { background-color: #ffc107; color: black; }
            
            .analyzer {
                background-color: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin-top: 30px;
            }
            textarea {
                width: 100%;
                height: 100px;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                box-sizing: border-box;
                margin-bottom: 10px;
            }
            button {
                background-color: #4285f4;
                color: white;
                border: none;
                padding: 10px 15px;
                border-radius: 4px;
                cursor: pointer;
            }
            #result {
                margin-top: 20px;
                padding: 15px;
                border-radius: 4px;
                display: none;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Shop Sentiment Analysis</h1>
            
            <div class="success-message">
                <p>✓ Application is working correctly!</p>
            </div>
            
            <h2>Products</h2>
            """ + products_html + """
            
            <div class="analyzer">
                <h2>Analyze Sentiment</h2>
                <p>Enter some text to analyze:</p>
                <textarea id="text-input" placeholder="Type or paste text here..."></textarea>
                <button id="analyze-btn">Analyze Sentiment</button>
                <div id="result"></div>
            </div>
        </div>
        
        <script>
            document.getElementById('analyze-btn').addEventListener('click', function() {
                const text = document.getElementById('text-input').value.trim();
                const result = document.getElementById('result');
                
                if (!text) {
                    alert('Please enter some text to analyze');
                    return;
                }
                
                // Make API request
                fetch('/api/analyze', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ text: text })
                })
                .then(response => response.json())
                .then(data => {
                    result.style.display = 'block';
                    
                    if (data.error) {
                        result.style.backgroundColor = '#f8d7da';
                        result.innerHTML = `<p>Error: ${data.error}</p>`;
                        return;
                    }
                    
                    const sentiment = data.sentiment;
                    let bgColor, textColor;
                    
                    if (sentiment === 'positive') {
                        bgColor = '#d4edda';
                        textColor = '#28a745';
                    } else if (sentiment === 'negative') {
                        bgColor = '#f8d7da';
                        textColor = '#dc3545';
                    } else {
                        bgColor = '#fff3cd';
                        textColor = '#856404';
                    }
                    
                    result.style.backgroundColor = bgColor;
                    result.innerHTML = `
                        <h3>Result</h3>
                        <p>Sentiment: <strong style="color:${textColor}">${sentiment}</strong></p>
                        <p>Score: ${data.score}</p>
                    `;
                })
                .catch(error => {
                    result.style.display = 'block';
                    result.style.backgroundColor = '#f8d7da';
                    result.innerHTML = '<p>Error connecting to the server</p>';
                    console.error('Error:', error);
                });
            });
        </script>
    </body>
    </html>
    """

@app.route('/api/analyze', methods=['POST'])
def analyze_sentiment():
    data = request.json
    
    if not data or 'text' not in data:
        return jsonify({"error": "No text provided"}), 400
    
    text = data['text'].lower()
    
    # Simple sentiment analysis logic
    positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'best', 'fantastic', 'perfect']
    negative_words = ['bad', 'terrible', 'awful', 'hate', 'poor', 'worst', 'horrible', 'disappointed']
    
    pos_count = sum(1 for word in positive_words if word in text)
    neg_count = sum(1 for word in negative_words if word in text)
    
    if pos_count > neg_count:
        sentiment = "positive"
        score = min(0.5 + (pos_count * 0.1), 0.9)
    elif neg_count > pos_count:
        sentiment = "negative"
        score = max(0.5 - (neg_count * 0.1), 0.1)
    else:
        sentiment = "neutral"
        score = 0.5
    
    return jsonify({
        "sentiment": sentiment,
        "score": round(score, 2)
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 