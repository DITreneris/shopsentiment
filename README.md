# ShopSentiment

*Last updated: March 30, 2025 - 16:55 UTC*

ShopSentiment is a web application for analyzing product reviews from e-commerce platforms, providing sentiment analysis, keyword extraction, and trend visualization to help users understand customer feedback.

## Features

### Recently Implemented Features
- **Theme Switching**: Light and dark mode support with persistent user preferences
- **User Authentication**: Secure login, registration, and profile management
- **Product Analysis**: Sentiment analysis of reviews from multiple platforms
- **Interactive Dashboard**: Visual representation of sentiment distribution, top keywords, and trends
- **Data Export**: Export review data and analysis in CSV and JSON formats
- **Caching**: Performance optimization through client and server-side caching
- **Tooltips & Guided Tour**: Enhanced user experience with contextual help
- **Responsive Design**: Mobile-friendly interface that works on all devices

### Core Functionality
- Extract and analyze product reviews from Amazon, eBay, and custom sources
- Calculate sentiment scores using NLTK's VADER sentiment analyzer
- Identify and visualize the most common keywords in reviews
- Track sentiment trends over time
- Filter reviews by sentiment or keywords
- Secure user accounts with dedicated analysis storage

## Getting Started

### Prerequisites
- Python 3.7+
- SQLite (included in Python)
- Web browser with JavaScript enabled

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/shop-sentiment.git
   cd shop-sentiment
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python single_app.py
   ```

4. Access the application in your browser:
   ```
   http://127.0.0.1:5000
   ```

## Usage

### Analyzing a Product

1. **Register/Login**: Create an account or log in to save your analyses
2. **Submit a Product**: Enter the product URL or ID from supported platforms
3. **View Analysis**: Explore the sentiment distribution, keywords, and trends
4. **Filter Results**: Use the filtering options to focus on specific sentiments
5. **Export Data**: Download the analysis in CSV or JSON format for further processing

### Theme Switching

- Toggle between light and dark modes using the theme switch in the navigation bar
- Your preference is automatically saved for future visits

### Account Management

- Update your profile information from the profile page
- View all your saved analyses in the "My Analyses" section

## Testing

Run the comprehensive test suite:
```
python tests/run_tests.py
```

The test runner will execute:
- Unit tests for core functionality
- Integration tests for API endpoints
- UI tests for client-side components

## Development Stages

The application was developed in several stages:

1. **Foundation**: Core functionality and data processing
2. **User Interface**: Dashboard and visualization components
3. **Performance**: Caching and optimization
4. **User Experience**: Theme switching, tooltips, and guided tour
5. **User Management**: Authentication, profiles, and user-specific analyses

## Technical Details

### Architecture
- **Backend**: Flask (Python web framework)
- **Database**: SQLite for data storage
- **Authentication**: Flask-Login for user management
- **Frontend**: HTML, CSS (Bootstrap), JavaScript
- **Visualization**: Chart.js for interactive charts
- **NLP**: NLTK library for natural language processing
- **API**: RESTful endpoints for data access

### Database Schema
- **products**: Store product information and metadata
- **reviews**: Contains review text, ratings, sentiment scores
- **users**: User authentication and profile data

### API Endpoints
- `/api/reviews/<product_id>`: Get all reviews for a product
- `/export/csv/<product_id>`: Download reviews as CSV
- `/export/json/<product_id>`: Download reviews as JSON

## Future Development

Planned enhancements include:
- Advanced filtering options
- Competitor analysis
- Sentiment trend predictions
- Notification system for new reviews
- API integrations with e-commerce platforms
- Multi-language support

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- NLTK team for their sentiment analysis tools
- Chart.js for visualization components
- Bootstrap for responsive design framework

## Screenshots

![ShopSentiment Home Page](screenshots/shopsentiment_home.png)
*ShopSentiment home page with light theme, showing the platform selection and product ID input interface.*

## Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv shopenv
   ```
3. Activate the virtual environment:
   - Windows: `shopenv\Scripts\activate`
   - Mac/Linux: `source shopenv/bin/activate`
4. Install dependencies: 
   ```
   pip install -r requirements.txt
   ```
5. Run the application: 
   ```
   python app.py
   ```

## Usage

1. Access the application at http://localhost:5000
2. On the home page, enter the following information:
   - Select platform (Amazon, eBay, or Custom)
   - Enter the product ID or URL
   - For custom sites, provide CSS selectors for reviews, ratings, and dates
3. Click "Analyze" to start the scraping and analysis process
4. While processing, you'll see a waiting screen with status updates
5. Once complete, the dashboard will display:
   - Overall sentiment distribution (positive, neutral, negative)
   - Top keywords from reviews
   - Timeline of sentiment trends
   - Full review list with individual sentiment scores

## Testing

The application includes comprehensive tests for backend and frontend components.

### Running Tests

To run all tests with coverage reporting:

```
python run_tests.py
```

This will:
- Run all Python unit and integration tests
- Generate a coverage report
- Run JavaScript tests (if Node.js is installed)
- Output a summary of test results

### Test Structure

- `test_sentiment.py` - Tests for sentiment analysis functionality
- `test_cache.py` - Tests for server-side caching
- `test_routes.py` - Tests for Flask routes and API endpoints
- `test_client_cache.js` - Tests for client-side caching (requires Node.js)

### Coverage Reports

After running tests, view the HTML coverage report at:
```
coverage_html/index.html
```

## User Experience (UX)

The application provides an intuitive workflow:

1. **Simple Input Form**: Clean, minimalist design focusing on essential inputs
2. **Real-time Feedback**: Progress indicators during scraping and analysis
3. **Interactive Dashboard**: 
   - Color-coded sentiment visualization (green for positive, red for negative)
   - Sortable review tables
   - Clickable keywords for filtering
   - Responsive design for desktop and mobile
4. **Data Export**: Options to download results in CSV or JSON format
5. **Theme Support**: 
   - Toggle between light and dark modes for comfortable viewing
   - Automatic theme detection based on system preferences
   - Persistent theme selection using localStorage
   - Themed visualizations in Chart.js that adapt to the current theme
6. **Guided Tour & Tooltips**:
   - Interactive guided tours for new users
   - Contextual tooltips for quick feature explanations
   - Step-by-step walkthrough of main application features

## Technology Stack

- **Backend**: Python, Flask
- **Scraping**: Scrapy, Selenium (for dynamic sites)
- **Analysis**: NLTK, VADER, Pandas
- **Database**: SQLite
- **Frontend**: 
  - HTML5, CSS3, JavaScript (ES6+)
  - Bootstrap 5 for responsive design
  - Chart.js for interactive data visualization
  - Custom theme management system
  - Interactive guided tour implementation
- **Deployment**: Heroku

## Project Structure

```
shop_sentiment/
├── app/
│   ├── scrapers/       # Scrapy spiders for different platforms
│   ├── static/         # CSS, JavaScript, and other static files
│   │   ├── css/        # Stylesheets, including theme.css
│   │   ├── js/         # JavaScript files for functionality
│   │   └── img/        # Application images and icons
│   ├── templates/      # HTML templates
│   └── models/         # Data models
├── docs/               # Detailed documentation
│   ├── index.md        # Documentation home page
│   ├── theme_system.md # Theme system documentation
│   └── tooltips_system.md # Tooltips and tour documentation
├── shopenv/            # Virtual environment (not tracked in git)
├── reviews.db          # SQLite database
├── requirements.txt    # Project dependencies
├── app.py              # Application entry point
├── main.py             # App launcher with environment setup
├── .gitignore          # Git ignore file
├── Procfile            # Heroku deployment configuration
├── README.md           # This file
├── screenshots/        # Application screenshots for documentation
├── test_*.py           # Test files
└── run_tests.py        # Test runner script
```

## Troubleshooting

If you encounter issues with Scrapy or other dependencies:
1. Ensure you're using the virtual environment
2. Verify that all required packages are installed correctly
3. For Windows users, some packages may require Microsoft Visual C++ Build Tools

### Theme Switching Issues

If theme switching is not working:
1. Check browser console for JavaScript errors
2. Verify that localStorage is enabled in your browser
3. Try clearing browser cache and hard-refreshing the page

### Running the Application

To start the application:
```
python main.py
```

This will launch the app in development mode with debugging enabled.

## Documentation

Comprehensive documentation for ShopSentiment's key features:

- **[Theme System Documentation](docs/theme_system.md)**: Detailed guide for the theming implementation
- **[Tooltips & Guided Tour Documentation](docs/tooltips_system.md)**: Detailed documentation for tooltips and tour features
- **[Development Roadmap](roadmap.md)**: Future plans and development timeline

The documentation includes implementation details, customization guides, and best practices for developers who want to extend or modify these features.

## Theme System

ShopSentiment includes a comprehensive theme system that provides users with both light and dark mode options.

### Theme Features

- **Toggle Switch**: Easy-to-use switch in the navigation bar
- **System Preference Detection**: Automatically matches the user's system preference
- **Persistence**: Remembers user's theme preference between sessions using localStorage
- **Comprehensive Styling**: All UI elements styled appropriately for both themes
- **Chart Theme Integration**: Data visualizations adapt to the current theme

### Implementation Details

The theme system is implemented through several key components:

1. **CSS Variables**: Theme-specific colors and styles defined as CSS variables in `theme.css`
2. **ThemeManager Class**: JavaScript class in `theme-manager.js` that manages theme switching logic
3. **Chart Theme Integration**: Custom theming for Chart.js in `chart-themes.js`
4. **HTML Structure**: Data attributes (`data-theme`) used to apply theme styles

### Customizing Themes

To customize the themes:

1. Edit the CSS variables in `app/static/css/theme.css`
2. Light theme variables are defined in the `:root` selector
3. Dark theme variables are defined in the `[data-theme="dark"]` selector

Example of theme variables:
```css
:root {
    --bg-primary: #ffffff;
    --text-primary: #212529;
    --accent-color: #007bff;
    /* More variables */
}

[data-theme="dark"] {
    --bg-primary: #121212;
    --text-primary: #e0e0e0;
    --accent-color: #0d6efd;
    /* More variables */
}
```

### Using the Theme System

End users can:
1. Click the sun/moon toggle in the navigation bar to switch themes
2. See an immediate visual update as the theme changes
3. Return to the site later and have their preference remembered

Developers can:
1. Access the current theme using `document.documentElement.getAttribute('data-theme')`
2. Listen for theme changes with the `themeChanged` event
3. Create theme-aware components by using CSS variables

## Tooltips and Guided Tour

ShopSentiment includes an informative tooltips system and guided tour to help users understand the functionality.

### Tooltips System

- **Context-Sensitive Information**: Tooltips provide explanations for UI elements
- **Non-Intrusive Design**: Appear on hover/focus without disrupting the workflow
- **Theme Integration**: Tooltips match the current theme (light/dark)
- **Accessible**: Support for keyboard navigation and screen readers

### Guided Tour

The application offers a step-by-step guided tour to help new users get familiar with the features:

- **Interactive Walkthrough**: Highlights key elements of the interface
- **Page-Specific Tours**: Different tours for home page and dashboard
- **Progress Tracking**: Shows current step and total steps
- **Navigation Controls**: Easy to move forward, backward, or exit the tour
- **Visual Highlighting**: Clearly indicates which element is being explained

### Implementation Details

The tooltips and tour functionality is implemented in `app/static/js/tooltips.js`:

1. **TooltipManager Class**: Manages both tooltips and guided tour functionality
2. **Data Attributes**: Elements use `data-tooltip` attributes to connect with tooltip content
3. **Tour Configuration**: Defined tour steps with element selectors, titles, and descriptions
4. **Theme Integration**: Uses theme-aware CSS for consistent styling

### Customizing Tooltips and Tours

To add or modify tooltips:

1. Add `data-tooltip="tooltip-key"` to any HTML element
2. Define the tooltip content in the `tooltips` object in `tooltips.js`

To customize the guided tour:

1. Modify the `tourSteps` object in `tooltips.js`
2. Each step includes:
   - `element`: Selector for the element to highlight
   - `title`: Step title
   - `content`: Descriptive text
   - Optional `condition`: Function to determine if the step should be shown