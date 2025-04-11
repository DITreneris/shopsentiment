from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, URL, Optional, ValidationError
import re

class LoginForm(FlaskForm):
    """Form for user login"""
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Invalid email address")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required")
    ])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegistrationForm(FlaskForm):
    """Form for user registration"""
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Invalid email address"),
        Length(max=100, message="Email must be less than 100 characters")
    ])
    username = StringField('Username', validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=20, message="Username must be between 3 and 20 characters")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
        Length(min=8, message="Password must be at least 8 characters long")
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm your password"),
        EqualTo('password', message="Passwords must match")
    ])
    submit = SubmitField('Register')

    def validate_username(self, username):
        """Custom validation for username"""
        # Allow only alphanumeric characters and underscores
        if not re.match(r'^[A-Za-z0-9_]+$', username.data):
            raise ValidationError('Username can only contain letters, numbers, and underscores')

class AnalysisForm(FlaskForm):
    """Form for submitting product analysis requests"""
    platform = SelectField('Platform', validators=[
        DataRequired(message="Please select a platform")
    ], choices=[
        ('amazon', 'Amazon'),
        ('ebay', 'eBay'),
        ('custom', 'Custom Website')
    ])
    
    product_id = StringField('Product ID', validators=[
        DataRequired(message="Product ID is required"),
        Length(min=2, max=50, message="Product ID must be between 2 and 50 characters")
    ])
    
    url = StringField('URL', validators=[
        Optional(),
        URL(message="Please enter a valid URL")
    ])
    
    # For custom website scraping
    review_selector = StringField('Review Selector', validators=[Optional()])
    rating_selector = StringField('Rating Selector', validators=[Optional()])
    date_selector = StringField('Date Selector', validators=[Optional()])
    
    submit = SubmitField('Analyze')
    
    def validate(self):
        """Custom validation for the form"""
        if not super().validate():
            return False
            
        # If custom platform is selected, URL is required
        if self.platform.data == 'custom' and not self.url.data:
            self.url.errors.append('URL is required for custom websites')
            return False
            
        # Custom platform requires at least the review selector
        if self.platform.data == 'custom' and not self.review_selector.data:
            self.review_selector.errors.append('Review selector is required for custom websites')
            return False
            
        return True

class FilterForm(FlaskForm):
    """Form for filtering reviews"""
    # Rating filter (1-5 stars)
    min_rating = SelectField('Minimum Rating', choices=[
        ('', 'Any'),
        ('1', '1 Star'),
        ('2', '2 Stars'),
        ('3', '3 Stars'),
        ('4', '4 Stars'),
        ('5', '5 Stars')
    ], validators=[Optional()])
    
    max_rating = SelectField('Maximum Rating', choices=[
        ('', 'Any'),
        ('1', '1 Star'),
        ('2', '2 Stars'),
        ('3', '3 Stars'),
        ('4', '4 Stars'),
        ('5', '5 Stars')
    ], validators=[Optional()])
    
    # Sentiment filter
    sentiment = SelectField('Sentiment', choices=[
        ('', 'All'),
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative')
    ], validators=[Optional()])
    
    # Keyword filter
    keyword = StringField('Keyword', validators=[Optional()])
    
    # Date range filter
    date_from = StringField('From Date', validators=[Optional()])
    date_to = StringField('To Date', validators=[Optional()])
    
    submit = SubmitField('Apply Filters')
    
    def validate(self):
        """Custom validation for the filter form"""
        if not super().validate():
            return False
        
        # Validate min and max rating
        if self.min_rating.data and self.max_rating.data:
            if int(self.min_rating.data) > int(self.max_rating.data):
                self.max_rating.errors.append('Maximum rating must be greater than or equal to minimum rating')
                return False
        
        return True

class ExportForm(FlaskForm):
    """Form for exporting data"""
    export_format = SelectField('Export Format', choices=[
        ('csv', 'CSV'),
        ('json', 'JSON')
    ], validators=[DataRequired(message="Please select an export format")])
    
    include_sentiment = BooleanField('Include Sentiment Analysis', default=True)
    include_product_info = BooleanField('Include Product Information', default=True)
    
    submit = SubmitField('Export') 