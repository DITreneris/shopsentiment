# Resilient Scraper Documentation

The Resilient Scraper is a robust web scraping utility designed to handle common challenges in web scraping, including rate limiting, CAPTCHA detection, network errors, and anti-scraping measures.

## Features

- **Retry Mechanism**: Automatically retries failed requests with exponential backoff
- **User Agent Rotation**: Rotates user agents to avoid detection
- **Request Throttling**: Implements randomized delays between requests
- **CAPTCHA Detection**: Detects and handles CAPTCHA challenges
- **Proxy Support**: Optional proxy rotation for high-volume scraping
- **Error Handling**: Comprehensive error handling and logging

## Usage

### Basic Usage

```python
from app.utils.resilient_scraper import ResilientScraper

# Create a scraper instance
scraper = ResilientScraper(min_delay=2.0, max_delay=5.0)

# Make a request
response = scraper.get('https://example.com/products/123')

# Parse HTML content
soup = scraper.parse_html(response.text)

# Extract elements with CSS selectors
products = soup.select('.product-item')
```

### Scraping with CSS Selectors

```python
# Scrape elements directly using CSS selectors
elements = scraper.scrape_page('https://example.com/products', '.product-item')

# Process the elements
for element in elements:
    name = element.select_one('.product-name').text
    price = element.select_one('.product-price').text
    print(f"Product: {name}, Price: {price}")
```

### Advanced Configuration

```python
# Create a scraper with proxy support and custom retry settings
scraper = ResilientScraper(
    use_proxies=True,
    min_delay=3.0,
    max_delay=10.0,
    max_retries=10
)

# Make a request with custom headers
headers = {'Accept-Language': 'en-US,en;q=0.9'}
response = scraper.get('https://example.com/products', headers=headers)
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `use_proxies` | bool | `False` | Whether to use proxy rotation |
| `max_retries` | int | `5` | Maximum number of retry attempts |
| `min_delay` | float | `1.0` | Minimum delay between requests in seconds |
| `max_delay` | float | `5.0` | Maximum delay between requests in seconds |

## Error Handling

The scraper handles various error conditions:

- HTTP errors (4xx, 5xx status codes)
- Network connectivity issues
- Timeouts
- CAPTCHA challenges

Errors are logged and, in most cases, automatically retried with an exponential backoff strategy.

## CAPTCHA Detection

The scraper includes built-in CAPTCHA detection by looking for common patterns in the HTML content. When a CAPTCHA is detected, the scraper raises an exception that can be caught and handled by the calling code.

Current CAPTCHA patterns detected:
- "captcha"
- "robot"
- "security check"
- "human verification"
- "are you a robot"
- "automated access"
- "security challenge"
- "human test"
- "verify you are human"

## Best Practices

1. **Respect Robots.txt**: Always check and respect the target website's robots.txt file
2. **Use Reasonable Delays**: Set appropriate min_delay and max_delay values to avoid overloading the target server
3. **Handle Errors Gracefully**: Catch and handle exceptions from the scraper to ensure your application remains resilient
4. **Monitor Logs**: Keep an eye on the scraper logs to identify patterns of failure that might require adjustments
5. **Legal Compliance**: Ensure your scraping activities comply with the website's terms of service and applicable laws

## Implementation Details

### Retry Logic

The scraper uses the `tenacity` library to implement retry logic with exponential backoff. The retry mechanism is configured to:

- Retry on specific exception types (`RequestException`, `HTTPError`)
- Use exponential backoff with a multiplier of 1
- Start with a 4-second delay, increasing up to 60 seconds
- Stop after 5 failed attempts

### User Agent Rotation

The scraper uses the `fake_useragent` library to generate random, realistic user agents. If the library fails, it falls back to a predefined list of common user agents.

### Request Delays

The scraper implements randomized delays between requests using `random.uniform(min_delay, max_delay)`. This helps to make the request pattern less predictable and more human-like.

## Extension Points

The Resilient Scraper is designed to be extended for specific scraping needs:

1. **Custom CAPTCHA Handlers**: Override the `_handle_captcha` method to implement custom CAPTCHA solving
2. **Proxy Management**: Extend the `_load_proxies` method to implement your proxy rotation strategy
3. **Custom Parsers**: Create domain-specific subclasses that extract particular data structures

## Example: Amazon Scraper

The `AmazonScraper` class in `app/scrapers/amazon_scraper.py` demonstrates how to use the Resilient Scraper to implement a domain-specific scraper for Amazon product reviews.

```python
from app.utils.resilient_scraper import ResilientScraper

class AmazonScraper:
    def __init__(self, min_delay=2.0, max_delay=5.0, use_proxies=False):
        self.scraper = ResilientScraper(
            use_proxies=use_proxies,
            min_delay=min_delay,
            max_delay=max_delay
        )
        
    def scrape_reviews(self, asin, max_pages=5):
        all_reviews = []
        # Implementation details...
        return all_reviews 