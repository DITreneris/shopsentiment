from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from app.models.user import User
from app.forms import LoginForm, RegistrationForm
from app import limiter
import os
import json

auth_bp = Blueprint('auth', __name__)

USERS_FILE = 'data/users.json'

def get_users_db():
    """Load users from JSON file or create empty list if file doesn't exist"""
    if not os.path.exists(USERS_FILE):
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        # Create empty users file
        with open(USERS_FILE, 'w') as f:
            json.dump([], f)
        return []
    
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_users_db(users):
    """Save users to JSON file"""
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Rate limiting for login attempts
def login():
    """Handle user login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        remember = form.remember.data
        
        users_db = get_users_db()
        user = User.get_by_email(email, users_db)
        
        if user and user.check_password(password):
            login_user(user, remember=remember)
            user.update_last_login()
            
            # Update the last_login in the database
            for u in users_db:
                if u['email'] == email:
                    u['last_login'] = user.last_login.isoformat()
                    break
            save_users_db(users_db)
            
            next_page = request.args.get('next', '')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        
        flash('Invalid email or password', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")  # Rate limiting for registration
def register():
    """Handle user registration"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = form.password.data
        
        users_db = get_users_db()
        
        # Check if email or username already exists
        if User.get_by_email(email, users_db):
            flash('Email already registered', 'error')
            return render_template('auth/register.html', form=form)
        
        if User.get_by_username(username, users_db):
            flash('Username already taken', 'error')
            return render_template('auth/register.html', form=form)
        
        # Generate a new ID (max id + 1)
        user_id = 1
        if users_db:
            user_id = max(user['id'] for user in users_db) + 1
        
        # Create new user
        user = User(user_id, username, email, password=password)
        
        # Add user to database
        users_db.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'password_hash': user.password_hash,
            'created_at': user.created_at.isoformat(),
            'last_login': None
        })
        save_users_db(users_db)
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Log out the current user"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login'))

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