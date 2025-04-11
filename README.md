# ShopSentiment

*Last updated: April 25, 2025 - 15:45 UTC*

ShopSentiment is a web-based application that scrapes product reviews from e-commerce platforms, performs sentiment analysis, and presents insights through an interactive dashboard.

## Features

- **Multi-platform Scraping**: Support for Amazon, eBay, and custom websites
- **Sentiment Analysis**: Powered by NLTK's VADER for accurate sentiment scoring
- **Interactive Dashboard**: Visualize sentiment trends, keywords, and review metrics
- **User Authentication**: Secure user accounts with profile management
- **Export Options**: Export analysis data in CSV or JSON formats
- **Advanced Filtering**: Filter reviews by sentiment, rating, date, and keywords
- **Responsive Design**: Mobile-friendly interface with dark/light mode
- **Security Features**: CSRF protection, rate limiting, and secure headers
- **Resilient Scraping**: Built-in retry mechanisms, user agent rotation, and CAPTCHA detection
- **Asynchronous Processing**: Background tasks handled with Celery and Redis

## Recent Enhancements (April 2025)

### UI/UX Improvements
The application has recently undergone significant UI/UX enhancements:

- **Modernized Dashboard**: Updated with an accessible color palette, responsive grid system, and improved typography
- **Enhanced Visualizations**: Interactive charts with tooltips, smooth transitions, and time-range filtering
- **Improved Form Interactions**: Real-time validation, styled error messages, and success notifications
- **Better Navigation**: Breadcrumb navigation, quick action buttons, and keyboard support
- **Optimized Loading States**: Skeleton screens, progress indicators, and loading animations
- **Accessibility Upgrades**: ARIA labels, improved color contrast, and screen reader support

### Testing Infrastructure
Comprehensive testing has been implemented:

- **UI Component Tests**: Test cases for visual components with regression testing
- **Integration Tests**: End-to-end testing for forms, visualizations, navigation, and error handling
- **Performance Tests**: Load time measurement, network simulation, and memory usage verification

### Heroku Deployment
The application is now configured for seamless Heroku deployment:

- **Complete Setup**: Procfile, environment variables, and buildpacks configuration
- **Database Integration**: MongoDB Atlas connection with optimized performance
- **Monitoring**: Error tracking and performance metrics reporting

For detailed information about these enhancements, see the `IMPLEMENTATION_SUMMARY.md` file.

## Quick Start

### Using Docker (Recommended)

1. Clone the repository
```
git clone https://github.com/yourusername/shop-sentiment.git
cd shop-sentiment
```

2. Create a `.env` file based on the example
```
cp .env.example .env
```

3. Start the application with Docker Compose
```
docker-compose up -d
```

4. Access the application at http://localhost:5000

### Manual Installation

1. Clone the repository
```
git clone https://github.com/yourusername/shop-sentiment.git
cd shop-sentiment
```

2. Create and activate a virtual environment
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```
pip install -r requirements.txt
```

4. Set up the database
```
flask init-db
```

5. Download NLTK data
```
python -c "import nltk; nltk.download('vader_lexicon'); nltk.download('punkt'); nltk.download('stopwords')"
```

6. Create a `.env` file based on the example
```
cp .env.example .env
```

7. Start Redis (needed for Celery and caching)
```
redis-server
```

8. In a separate terminal, start Celery workers (with the virtual environment activated)
```
celery -A app.tasks.celery worker --loglevel=info
```

9. In another separate terminal, start Celery beat for scheduled tasks (optional)
```
celery -A app.tasks.celery beat --loglevel=info
```

10. Start the development server
```
flask run
```

### Python 3.10 Migration

ShopSentiment now supports Python 3.10, which brings performance improvements and modern language features.

To migrate an existing installation:

1. Run the migration script
```
python scripts/migrate_to_python310.py
```

2. Follow the instructions printed by the script
3. After migration, use the new requirements file:
```
pip install -r requirements-py310.txt
```

4. Test your installation:
```
pytest
```

If you're setting up a new installation, you can use Python 3.10 directly:

```
python -m venv venv --python=python3.10
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-py310.txt
```

The Docker configuration already uses Python 3.10 by default.

## System Requirements

- Python 3.10 or higher
- Redis 7.0 or higher
- 2GB+ RAM recommended
- Internet connection for scraping

## Environment Variables

Create a `.env` file in the project root by copying the provided `.env.example`:

```
# Flask configuration
FLASK_APP=wsgi.py
FLASK_ENV=development  # Change to 'production' for production environment
SECRET_KEY=your-secure-secret-key  # Generate a strong random key for production

# Database configuration
DATABASE_URL=sqlite:///data/shopsentiment.db

# Redis configuration
REDIS_URL=redis://localhost:6379/0

# Celery configuration
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Security configuration
WTF_CSRF_ENABLED=True
WTF_CSRF_SECRET_KEY=generate-another-secure-key-here
SECURITY_PASSWORD_SALT=generate-a-secure-salt-here

# Rate limiting
RATELIMIT_STORAGE_URL=redis://localhost:6379/3
RATELIMIT_STRATEGY=fixed-window
```

For production, ensure you set `FLASK_ENV=production` and configure secure, randomly generated keys.

## Usage Guide

### Analyzing a Product

1. Register or log in to your account
2. From the homepage, select a platform (Amazon, eBay, or custom website)
3. Enter the product ID or URL
4. For custom websites, provide CSS selectors for reviews, ratings, and dates
5. Click "Analyze Reviews"
6. Wait for the analysis to complete - you'll see a progress bar with real-time updates
7. Explore the interactive dashboard once complete

### Filtering Reviews

1. On the product dashboard, use the filter panel on the right
2. Select filtering criteria (rating, sentiment, date range, keywords)
3. Click "Apply Filters"
4. View the filtered results and metrics
5. Save filters for future use (optional)

### Exporting Data

1. On the product dashboard, find the export options
2. Choose CSV or JSON format
3. Select what data to include (reviews, sentiment, product info)
4. Click "Export" to download the file

## Development

### Project Structure

```
shop-sentiment/
├── app/                      # Application code
│   ├── __init__.py           # App initialization
│   ├── forms.py              # Form definitions
│   ├── routes/               # Route handlers
│   │   ├── __init__.py       # Routes initialization
│   │   ├── auth.py           # Authentication routes
│   │   ├── main.py           # Main application routes
│   │   └── api.py            # API routes
│   ├── tasks.py              # Celery tasks
│   ├── scrapers/             # Scraper modules
│   │   ├── __init__.py       # Scrapers initialization
│   │   ├── amazon_scraper.py # Amazon scraper
│   │   ├── ebay_scraper.py   # eBay scraper
│   │   ├── custom_scraper.py # Custom site scraper
│   │   └── resilient_scraper.py # Resilient scraper utility
│   ├── static/               # Static assets
│   ├── templates/            # HTML templates
│   └── utils/                # Utility functions
├── tests/                    # Test suite
├── docs/                     # Documentation
│   ├── api.md                # API documentation
│   ├── deployment.md         # Deployment guide
│   └── resilient_scraper.md  # Resilient scraper documentation
├── data/                     # Data storage
├── .dockerignore             # Docker ignore file
├── .env.example              # Example environment variables
├── docker-compose.yml        # Production Docker compose config
├── docker-compose.dev.yml    # Development Docker compose config
├── Dockerfile                # Docker build file
├── nginx/                    # Nginx configuration
├── wsgi.py                   # WSGI entry point
├── requirements.txt          # Python dependencies
├── test_docker.py            # Docker deployment test script
└── README.md                 # This file
```

### Running Tests

```
pytest
```

For test coverage report:
```
pytest --cov=app tests/
```

### Docker Development Environment

To start the development environment with Docker:

```
docker-compose -f docker-compose.dev.yml up -d
```

This configuration:
- Mounts the current directory as a volume for live code changes
- Runs Flask in development mode with debugging enabled
- Provides hot-reloading for fast development

### Build and Deployment

#### Docker Production Deployment

1. Configure environment variables in `.env`
2. Start the production environment:
```
docker-compose up -d
```

3. Test the deployment:
```
python test_docker.py
```

#### Manual Production Deployment

1. Set up a production database (PostgreSQL recommended)
2. Configure environment variables
3. Install dependencies: `pip install -r requirements.txt`
4. Run with Gunicorn: `gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 wsgi:app`
5. Configure Nginx as a reverse proxy (see `nginx/shopsentiment.conf`)

## Security Features

ShopSentiment implements several security features:

- **CSRF Protection**: All forms are protected against Cross-Site Request Forgery
- **Rate Limiting**: API endpoints and sensitive routes are rate-limited
- **Secure HTTP Headers**: Including Content-Security-Policy, X-XSS-Protection
- **Input Validation**: All user inputs are validated using WTForms
- **Permission-Based Access Control**: Users can only access their own data
- **Password Security**: Passwords are hashed and salted
- **HTTPS Enforcement**: In production, HTTPS is enforced

## API Access

ShopSentiment provides a RESTful API for programmatic access to review data and analysis features.

See the [API Documentation](docs/api.md) for details on endpoints, authentication, and example requests.

## Resilient Scraping

The application uses a resilient scraping approach to handle common web scraping challenges:

- **Retry Mechanism**: Automatically retries failed requests with exponential backoff
- **User Agent Rotation**: Cycles through different user agents to avoid detection
- **Request Throttling**: Adds delays between requests to avoid rate limiting
- **CAPTCHA Detection**: Identifies CAPTCHA challenges and logs them for manual resolution
- **Comprehensive Error Handling**: Provides detailed logging for all scraping operations

See the [Resilient Scraper Documentation](docs/resilient_scraper.md) for more details.

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- NLTK team for their sentiment analysis tools
- Chart.js for visualization components
- Bootstrap for responsive design framework