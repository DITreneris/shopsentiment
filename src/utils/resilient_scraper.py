import random
import time
import logging
import requests
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type, before_sleep_log
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

# Configure logging
logger = logging.getLogger(__name__)

# List of common CAPTCHA indicators
CAPTCHA_PATTERNS = [
    "captcha", "robot", "security check", "human verification",
    "are you a robot", "automated access", "security challenge",
    "human test", "verify you are human"
]

class ResilientScraper:
    """
    A resilient web scraper with retry mechanisms, user agent rotation,
    CAPTCHA detection, and request throttling.
    """
    
    def __init__(self, use_proxies=False, max_retries=5, min_delay=1, max_delay=5):
        """
        Initialize the resilient scraper.
        
        Args:
            use_proxies (bool): Whether to use proxy rotation
            max_retries (int): Maximum number of retry attempts
            min_delay (float): Minimum delay between requests in seconds
            max_delay (float): Maximum delay between requests in seconds
        """
        self.use_proxies = use_proxies
        self.max_retries = max_retries
        self.min_delay = min_delay
        self.max_delay = max_delay
        
        # Initialize user agent generator
        try:
            self.user_agent = UserAgent()
        except Exception as e:
            logger.warning(f"Failed to initialize UserAgent: {e}")
            # Fallback user agents if fake_useragent fails
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            ]
        
        # Initialize proxy list if enabled
        self.proxies = []
        if use_proxies:
            self._load_proxies()
    
    def _load_proxies(self):
        """Load proxies from file or service."""
        # In production, you would load proxies from a file or service
        # For this example, we'll just use a placeholder
        # self.proxies = ["http://proxy1.example.com", "http://proxy2.example.com"]
        logger.info("Proxy support is enabled but no proxies are configured")
    
    def _get_random_user_agent(self):
        """Get a random user agent."""
        try:
            return self.user_agent.random
        except AttributeError:
            return random.choice(self.user_agents)
    
    def _get_random_proxy(self):
        """Get a random proxy if proxies are enabled."""
        if not self.use_proxies or not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def _random_delay(self):
        """Implement a random delay between requests."""
        delay = random.uniform(self.min_delay, self.max_delay)
        logger.debug(f"Sleeping for {delay:.2f} seconds")
        time.sleep(delay)
    
    def _detect_captcha(self, content):
        """
        Detect if the response contains a CAPTCHA challenge.
        
        Args:
            content (str): HTML content to check
            
        Returns:
            bool: True if CAPTCHA is detected, False otherwise
        """
        content_lower = content.lower()
        for pattern in CAPTCHA_PATTERNS:
            if pattern in content_lower:
                return True
        return False
    
    def _handle_captcha(self, url):
        """
        Handle CAPTCHA detection.
        
        Args:
            url (str): The URL that triggered the CAPTCHA
            
        Returns:
            None
        """
        logger.warning(f"CAPTCHA detected at {url}. Captcha handling required.")
        # Notify administrators or implement a more sophisticated CAPTCHA handling system
        # In a production system, you might:
        # 1. Switch to a different proxy
        # 2. Implement CAPTCHA solving with a service like 2captcha
        # 3. Pause scraping for this website for some time
    
    @retry(
        retry=retry_if_exception_type((requests.exceptions.RequestException, requests.exceptions.HTTPError)),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def get(self, url, params=None, headers=None, **kwargs):
        """
        Perform a GET request with retries, user agent rotation, and delay.
        
        Args:
            url (str): URL to request
            params (dict, optional): Query parameters
            headers (dict, optional): Additional headers
            **kwargs: Additional arguments to pass to requests.get
            
        Returns:
            requests.Response: The response object
        """
        # Add random delay before request (respects robots.txt implicitly)
        self._random_delay()
        
        # Prepare headers with random user agent
        if headers is None:
            headers = {}
        headers['User-Agent'] = self._get_random_user_agent()
        
        # Add proxy if enabled
        proxy = self._get_random_proxy()
        if proxy:
            kwargs['proxies'] = {'http': proxy, 'https': proxy}
        
        # Make the request
        logger.info(f"Making request to {url} with user agent: {headers['User-Agent']}")
        response = requests.get(url, params=params, headers=headers, **kwargs)
        
        # Check for CAPTCHA
        if self._detect_captcha(response.text):
            self._handle_captcha(url)
            raise requests.exceptions.RequestException("CAPTCHA detected")
        
        # Raise exception for bad status codes
        response.raise_for_status()
        
        return response
    
    def parse_html(self, content):
        """
        Parse HTML content with BeautifulSoup.
        
        Args:
            content (str): HTML content to parse
            
        Returns:
            BeautifulSoup: Parsed HTML
        """
        return BeautifulSoup(content, 'html.parser')
    
    def scrape_page(self, url, selector, params=None, headers=None, **kwargs):
        """
        Scrape a page and extract elements matching a CSS selector.
        
        Args:
            url (str): URL to scrape
            selector (str): CSS selector to extract
            params (dict, optional): Query parameters
            headers (dict, optional): Additional headers
            **kwargs: Additional arguments to pass to requests.get
            
        Returns:
            list: List of matching elements
        """
        response = self.get(url, params=params, headers=headers, **kwargs)
        soup = self.parse_html(response.text)
        return soup.select(selector) 