import pytest
from app.forms import LoginForm, RegistrationForm, AnalysisForm, FilterForm, ExportForm
from werkzeug.datastructures import MultiDict

class TestLoginForm:
    def test_valid_login_form(self):
        form_data = MultiDict({
            'email': 'test@example.com',
            'password': 'password123'
        })
        form = LoginForm(formdata=form_data)
        assert form.validate() is True

    def test_invalid_email_login_form(self):
        form_data = MultiDict({
            'email': 'not-an-email',
            'password': 'password123'
        })
        form = LoginForm(formdata=form_data)
        assert form.validate() is False
        assert 'Invalid email address' in form.email.errors

    def test_missing_fields_login_form(self):
        form_data = MultiDict({})
        form = LoginForm(formdata=form_data)
        assert form.validate() is False
        assert 'Email is required' in form.email.errors
        assert 'Password is required' in form.password.errors

class TestRegistrationForm:
    def test_valid_registration_form(self):
        form_data = MultiDict({
            'email': 'new@example.com',
            'username': 'newuser',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        form = RegistrationForm(formdata=form_data)
        assert form.validate() is True

    def test_password_mismatch(self):
        form_data = MultiDict({
            'email': 'new@example.com',
            'username': 'newuser',
            'password': 'password123',
            'confirm_password': 'different'
        })
        form = RegistrationForm(formdata=form_data)
        assert form.validate() is False
        assert 'Passwords must match' in form.confirm_password.errors

    def test_invalid_username(self):
        form_data = MultiDict({
            'email': 'new@example.com',
            'username': 'invalid user$%',
            'password': 'password123',
            'confirm_password': 'password123'
        })
        form = RegistrationForm(formdata=form_data)
        assert form.validate() is False
        assert 'Username can only contain letters, numbers, and underscores' in form.username.errors

class TestAnalysisForm:
    def test_valid_amazon_analysis(self):
        form_data = MultiDict({
            'platform': 'amazon',
            'product_id': 'B01LYCLS24',
            'submit': 'Analyze'
        })
        form = AnalysisForm(formdata=form_data)
        assert form.validate() is True

    def test_valid_custom_analysis(self):
        form_data = MultiDict({
            'platform': 'custom',
            'product_id': 'custom_product',
            'url': 'https://example.com/product',
            'review_selector': '.review-text',
            'rating_selector': '.rating',
            'date_selector': '.date',
            'submit': 'Analyze'
        })
        form = AnalysisForm(formdata=form_data)
        assert form.validate() is True

    def test_invalid_custom_analysis_missing_url(self):
        form_data = MultiDict({
            'platform': 'custom',
            'product_id': 'custom_product',
            'review_selector': '.review-text',
            'submit': 'Analyze'
        })
        form = AnalysisForm(formdata=form_data)
        assert form.validate() is False
        assert 'URL is required for custom websites' in form.url.errors

    def test_invalid_custom_analysis_missing_review_selector(self):
        form_data = MultiDict({
            'platform': 'custom',
            'product_id': 'custom_product',
            'url': 'https://example.com/product',
            'submit': 'Analyze'
        })
        form = AnalysisForm(formdata=form_data)
        assert form.validate() is False
        assert 'Review selector is required for custom websites' in form.review_selector.errors

class TestFilterForm:
    def test_valid_filter_form(self):
        form_data = MultiDict({
            'min_rating': '3',
            'max_rating': '5',
            'sentiment': 'positive',
            'keyword': 'great',
            'date_from': '2023-01-01',
            'date_to': '2023-12-31'
        })
        form = FilterForm(formdata=form_data)
        assert form.validate() is True

    def test_min_rating_greater_than_max(self):
        form_data = MultiDict({
            'min_rating': '4',
            'max_rating': '2'
        })
        form = FilterForm(formdata=form_data)
        assert form.validate() is False
        assert 'Maximum rating must be greater than or equal to minimum rating' in form.max_rating.errors

    def test_filter_form_empty(self):
        form_data = MultiDict({})
        form = FilterForm(formdata=form_data)
        assert form.validate() is True  # All fields are optional

class TestExportForm:
    def test_valid_export_form(self):
        form_data = MultiDict({
            'export_format': 'csv',
            'include_sentiment': 'y',
            'include_product_info': 'y'
        })
        form = ExportForm(formdata=form_data)
        assert form.validate() is True

    def test_missing_export_format(self):
        form_data = MultiDict({
            'include_sentiment': 'y',
            'include_product_info': 'y'
        })
        form = ExportForm(formdata=form_data)
        assert form.validate() is False
        assert 'Please select an export format' in form.export_format.errors 