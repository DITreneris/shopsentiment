from flask import Flask, render_template, request, jsonify
import os
import json

# Create a simple Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'development-key')

# In-memory user database for simple app
users = [
    {
        "id": "1",
        "username": "testuser",
        "email": "test@example.com",
        "password_hash": "pbkdf2:sha256:260000$5w0ivGWeqYEeuAIQ$ace2b9622132ed8b60e3748eaab4ff044ee6bc458efd377b737862a593d7b51d",
        "created_at": "2025-04-11T18:00:00.000000",
        "role": "user",
        "is_active": True
    }
]

@app.route('/')
def home():
    return jsonify({
        "status": "ok", 
        "message": "Shop Sentiment Analysis API is running",
        "endpoints": [
            "/api/products",
            "/api/reviews",
            "/auth/login",
            "/auth/register",
            "/auth/logout",
            "/auth/me"
        ]
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

# Simple auth endpoints
@app.route('/auth/test', methods=['GET'])
def auth_test():
    return jsonify({"message": "Auth endpoints are working", "status": "ok"}), 200

@app.route('/auth/login', methods=['POST'])
def auth_login():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    # Simplified login logic for testing
    for user in users:
        if user['email'] == email:
            # In a real app, we would check the password hash here
            return jsonify({"message": "Login successful", "user": user['username']}), 200
    
    return jsonify({"error": "Invalid email or password"}), 401

@app.route('/auth/register', methods=['POST'])
def auth_register():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({"error": "Username, email, and password are required"}), 400
    
    # Check if email is already registered
    for user in users:
        if user['email'] == email:
            return jsonify({"error": "Email already registered"}), 400
        if user['username'] == username:
            return jsonify({"error": "Username already taken"}), 400
    
    # Create new user (simplified)
    new_user = {
        "id": str(len(users) + 1),
        "username": username,
        "email": email,
        "password_hash": f"simulated_hash_{password}",  # Obviously not secure, just for testing
        "created_at": "2025-04-11T18:00:00.000000",
        "role": "user",
        "is_active": True
    }
    
    users.append(new_user)
    
    return jsonify({"message": "Registration successful", "user": username}), 201

@app.route('/auth/me', methods=['GET'])
def auth_me():
    # Simplified endpoint that always returns the first user (just for testing)
    if len(users) > 0:
        user = users[0]
        return jsonify({
            "id": user['id'],
            "username": user['username'],
            "email": user['email'],
            "role": user['role']
        }), 200
    else:
        return jsonify({"error": "Not authenticated"}), 401

@app.route('/auth/logout', methods=['POST'])
def auth_logout():
    return jsonify({"message": "Logout successful"}), 200

# Simple API endpoints
@app.route('/api/products/', methods=['GET'])
def get_products():
    return jsonify([]), 200

@app.route('/api/reviews/', methods=['GET'])
def get_reviews():
    return jsonify([]), 200

# Run the app if executed directly
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 