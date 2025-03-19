# ShopSentiment

A web-based application that scrapes product reviews from e-commerce platforms (Amazon, eBay, and user-defined shops), performs sentiment analysis, and presents insights through a dashboard.

## Features

- Scrapes reviews from Amazon, eBay, and custom e-commerce platforms
- Performs sentiment analysis on review text using VADER
- Extracts keywords and identifies trends
- Visualizes sentiment distribution and key insights in a dashboard
- Supports user-defined scraping targets via configuration

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
5. **Dark/Light Mode**: Toggle between display modes for different viewing preferences

## Technology Stack

- **Backend**: Python, Flask
- **Scraping**: Scrapy, Selenium (for dynamic sites)
- **Analysis**: NLTK, VADER, Pandas
- **Database**: SQLite
- **Frontend**: HTML/CSS/JavaScript, Chart.js
- **Deployment**: Heroku

## Project Structure

```
shop_sentiment/
├── app/
│   ├── scrapers/       # Scrapy spiders for different platforms
│   ├── static/         # CSS, JavaScript, and other static files
│   ├── templates/      # HTML templates
├── shopenv/            # Virtual environment (not tracked in git)
├── reviews.db          # SQLite database
├── requirements.txt    # Project dependencies
├── app.py              # Application entry point
├── .gitignore          # Git ignore file
├── Procfile            # Heroku deployment configuration
└── README.md           # This file
```

## Troubleshooting

If you encounter issues with Scrapy or other dependencies:
1. Ensure you're using the virtual environment
2. Verify that all required packages are installed correctly
3. For Windows users, some packages may require Microsoft Visual C++ Build Tools 