from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from app import app, get_db_connection
from app.models.user import User
from werkzeug.security import generate_password_hash

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect to home
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        
        # Basic validation
        if not email or not password:
            flash('Please enter both email and password', 'danger')
            return render_template('auth/login.html')
        
        # Check if user exists
        conn = get_db_connection()
        user = User.get_by_email(conn, email)
        
        if user and user.check_password(password):
            # Update last login time
            user.update_last_login()
            user.update(conn)
            conn.close()
            
            # Log the user in
            login_user(user, remember=remember)
            
            # Redirect to the page they were trying to access or home
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        
        conn.close()
        flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # If user is already logged in, redirect to home
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Basic validation
        if not username or not email or not password:
            flash('Please fill in all required fields', 'danger')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/register.html')
        
        if len(password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
            return render_template('auth/register.html')
        
        # Check if user already exists
        conn = get_db_connection()
        existing_user = User.get_by_email(conn, email)
        
        if existing_user:
            conn.close()
            flash('Email already registered', 'danger')
            return render_template('auth/register.html')
        
        existing_username = User.get_by_username(conn, username)
        if existing_username:
            conn.close()
            flash('Username already taken', 'danger')
            return render_template('auth/register.html')
        
        # Create and save the new user
        new_user = User(username=username, email=email, password=password)
        new_user.save(conn)
        conn.close()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    conn = get_db_connection()
    
    # Get user's analyses
    user_products = conn.execute(
        'SELECT * FROM products WHERE user_id = ? ORDER BY created_at DESC',
        (current_user.id,)
    ).fetchall()
    
    conn.close()
    
    return render_template('auth/profile.html', user=current_user, products=user_products)

@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        conn = get_db_connection()
        
        # Validate username and email
        if username != current_user.username:
            existing_user = User.get_by_username(conn, username)
            if existing_user:
                conn.close()
                flash('Username already taken', 'danger')
                return render_template('auth/edit_profile.html')
        
        if email != current_user.email:
            existing_user = User.get_by_email(conn, email)
            if existing_user:
                conn.close()
                flash('Email already registered', 'danger')
                return render_template('auth/edit_profile.html')
        
        # Update user information
        current_user.username = username
        current_user.email = email
        
        # Update password if provided
        if new_password:
            if not current_password:
                conn.close()
                flash('Current password is required to set a new password', 'danger')
                return render_template('auth/edit_profile.html')
            
            if not current_user.check_password(current_password):
                conn.close()
                flash('Current password is incorrect', 'danger')
                return render_template('auth/edit_profile.html')
            
            if new_password != confirm_password:
                conn.close()
                flash('New passwords do not match', 'danger')
                return render_template('auth/edit_profile.html')
            
            if len(new_password) < 8:
                conn.close()
                flash('New password must be at least 8 characters long', 'danger')
                return render_template('auth/edit_profile.html')
            
            current_user.password_hash = generate_password_hash(new_password)
        
        # Save changes
        current_user.update(conn)
        conn.close()
        
        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))
    
    return render_template('auth/edit_profile.html') 