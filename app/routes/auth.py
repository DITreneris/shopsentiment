from flask import Blueprint, render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models.user import User
from app.forms import LoginForm, RegistrationForm
import os
import json
import logging

# Configure logging
logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)

USERS_FILE = 'data/users.json'

def get_users_db():
    """Load users from JSON file or create empty list if file doesn't exist"""
    users_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'users.json')
    
    if not os.path.exists(users_file):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(users_file), exist_ok=True)
        # Create empty users file
        with open(users_file, 'w') as f:
            json.dump([], f)
        return []
    
    try:
        with open(users_file, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_users_db(users_db):
    """Save users to JSON file"""
    users_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'data', 'users.json')
    
    with open(users_file, 'w') as f:
        json.dump(users_db, f, indent=2)

@auth_bp.route('/login', methods=['POST'])
def login():
    logger.info("Login endpoint called")
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    
    if not data:
        return jsonify({"error": "No input data provided"}), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400
    
    users_db = get_users_db()
    user = User.get_by_email(email, users_db)
    
    if user and user.check_password(password):
        login_user(user)
        return jsonify({"message": "Login successful", "user": user.username}), 200
    
    return jsonify({"error": "Invalid email or password"}), 401

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logger.info("Logout endpoint called")
    logout_user()
    return jsonify({"message": "Logout successful"}), 200

@auth_bp.route('/register', methods=['POST'])
def register():
    logger.info("Register endpoint called")
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
    
    users_db = get_users_db()
    
    if User.get_by_email(email, users_db):
        return jsonify({"error": "Email already registered"}), 400
    
    if User.get_by_username(username, users_db):
        return jsonify({"error": "Username already taken"}), 400
    
    # Create user
    user = User.create_user(username, email, password, users_db)
    
    # Save user to database
    save_users_db(users_db)
    
    login_user(user)
    return jsonify({"message": "Registration successful", "user": user.username}), 201

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_me():
    logger.info("Me endpoint called")
    return jsonify({
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": getattr(current_user, 'role', 'user')
    }), 200

@auth_bp.route('/profile')
@login_required
def profile():
    """Display user profile"""
    return render_template('auth/profile.html')

@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Edit user profile"""
    form = RegistrationForm(obj=current_user)
    
    # Remove password validators for edit profile
    form.password.validators = []
    form.confirm_password.validators = []
    
    # Only validate if password fields are empty
    if request.method == 'POST':
        if not form.password.data and not form.confirm_password.data:
            # If password fields are empty, don't validate them
            del form.password
            del form.confirm_password
    
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        
        users_db = get_users_db()
        
        # Check if username or email is already taken by another user
        for user in users_db:
            if user['id'] != current_user.id:
                if user['username'] == username:
                    flash('Username already taken', 'error')
                    return render_template('auth/edit_profile.html', form=form)
                if user['email'] == email:
                    flash('Email already registered', 'error')
                    return render_template('auth/edit_profile.html', form=form)
        
        # Update the current user
        for user in users_db:
            if user['id'] == current_user.id:
                user['username'] = username
                user['email'] = email
                current_user.username = username
                current_user.email = email
                
                # Update password if provided
                if form.password.data:
                    user['password_hash'] = generate_password_hash(form.password.data)
                    current_user.password_hash = user['password_hash']
                break
                
        save_users_db(users_db)
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('auth.profile'))
    
    return render_template('auth/edit_profile.html', form=form)

# New test endpoint to check if auth blueprint is working
@auth_bp.route('/test', methods=['GET'])
def test():
    logger.info("Auth test endpoint called")
    return jsonify({"message": "Auth blueprint is working"}), 200 