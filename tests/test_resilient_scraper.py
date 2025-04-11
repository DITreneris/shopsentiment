import pytest
import responses
import requests
from unittest import mock
from app.utils.resilient_scraper import ResilientScraper, CAPTCHA_PATTERNS

class TestResilientScraper:
    """Tests for the ResilientScraper class."""
    
    @pytest.fixture
    def scraper(self):
        """Create a ResilientScraper instance with minimal delays for testing."""
        # Use small delays to speed up tests
        return ResilientScraper(use_proxies=False, min_delay=0.01, max_delay=0.02)
    
    @responses.activate
    def test_get_request_success(self, scraper):
        """Test a basic successful GET request."""
        # Mock a successful response
        responses.add(
            responses.GET,
            'https://example.com/test',
            body='<html><body>Test content</body></html>',
            status=200
        )
        
        # Make the request
        response = scraper.get('https://example.com/test')
        
        # Assert the response
        assert response.status_code == 200
        assert response.text == '<html><body>Test content</body></html>'
    
    @responses.activate
    def test_user_agent_rotation(self, scraper):
        """Test that user agents are rotated."""
        # Track user agents
        user_agents = []
        
        def callback(request):
            user_agents.append(request.headers['User-Agent'])
            return (200, {}, '<html><body>Test content</body></html>')
        
        # Add the callback to mock responses
        responses.add_callback(
            responses.GET,
            'https://example.com/user-agent-test',
            callback=callback
        )
        
        # Make 3 requests
        for _ in range(3):
            scraper.get('https://example.com/user-agent-test')
        
        # Assert that user agents were used and are not all the same
        assert len(user_agents) == 3
        assert len(set(user_agents)) > 1  # At least some should be different
    
    @responses.activate
    def test_retry_on_failure(self, scraper):
        """Test retry mechanism on request failure."""
        # Mock a series of failures followed by success
        responses.add(
            responses.GET, 
            'https://example.com/fail-then-succeed',
            status=500
        )
        responses.add(
            responses.GET, 
            'https://example.com/fail-then-succeed',
            status=500
        )
        responses.add(
            responses.GET, 
            'https://example.com/fail-then-succeed',
            status=200,
            body='<html><body>Success after failure</body></html>'
        )
        
        # Patch the retry decorator to not wait between attempts
        with mock.patch('app.utils.resilient_scraper.wait_exponential', return_value=lambda attempt: 0):
            # Make the request
            response = scraper.get('https://example.com/fail-then-succeed')
            
            # Assert the response
            assert response.status_code == 200
            assert response.text == '<html><body>Success after failure</body></html>'
            
            # Verify that we made 3 requests (2 failures + 1 success)
            assert len(responses.calls) == 3
    
    @responses.activate
    def test_captcha_detection(self, scraper):
        """Test CAPTCHA detection."""
        # Create HTML with CAPTCHA indicators
        captcha_html = f'<html><body>Please complete this security check to continue</body></html>'
        
        # Mock a response with CAPTCHA
        responses.add(
            responses.GET,
            'https://example.com/captcha-test',
            body=captcha_html,
            status=200
        )
        
        # Patch the _handle_captcha method to avoid waiting
        with mock.patch.object(scraper, '_handle_captcha'):
            # Make the request and expect it to raise an exception
            with pytest.raises(requests.exceptions.RequestException, match="CAPTCHA detected"):
                scraper.get('https://example.com/captcha-test')
    
    @responses.activate
    def test_scrape_page(self, scraper):
        """Test the scrape_page method."""
        # Mock HTML content with elements to extract
        html_content = '''
        <html>
            <body>
                <div class="product">Product 1</div>
                <div class="product">Product 2</div>
                <div class="product">Product 3</div>
            </body>
        </html>
        '''
        
        # Mock the response
        responses.add(
            responses.GET,
            'https://example.com/products',
            body=html_content,
            status=200
        )
        
        # Scrape the page
        elements = scraper.scrape_page('https://example.com/products', '.product')
        
        # Assert that we found the expected elements
        assert len(elements) == 3
        assert elements[0].text == 'Product 1'
        assert elements[1].text == 'Product 2'
        assert elements[2].text == 'Product 3'
    
    def test_random_delay(self, scraper):
        """Test that _random_delay produces a delay within the specified range."""
        with mock.patch('time.sleep') as mock_sleep:
            # Call the method multiple times
            for _ in range(10):
                scraper._random_delay()
                
            # Assert that sleep was called with values in the correct range
            for call in mock_sleep.call_args_list:
                delay = call[0][0]
                assert scraper.min_delay <= delay <= scraper.max_delay
    
    def test_detect_captcha(self, scraper):
        """Test that CAPTCHA detection works for various patterns."""
        # Test positive cases
        for pattern in CAPTCHA_PATTERNS:
            html = f'<html><body>This page contains a {pattern}</body></html>'
            assert scraper._detect_captcha(html) is True
        
        # Test negative case
        html = '<html><body>This is a normal page without security checks</body></html>'
        assert scraper._detect_captcha(html) is False 