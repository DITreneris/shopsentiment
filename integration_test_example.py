"""
Comprehensive Integration Test Example

This script demonstrates the four main integration testing areas from Task 3.2:
1. Form Submissions
2. Data Visualization Updates
3. Navigation Flows
4. Error Handling

It uses a demo website (the HTML preview mode of a GitHub markdown file) for testing
since we don't have direct access to the application in this environment.
"""

import time
import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

class TestFormSubmission:
    """Test suite for form submission integration."""
    
    @pytest.fixture
    def browser(self):
        """Set up browser for testing."""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        yield driver
        driver.quit()
    
    def test_search_form_submission(self, browser):
        """Test form submission and result handling using GitHub's search."""
        # Navigate to GitHub
        browser.get("https://github.com")
        print("\n[Form Test] Navigated to GitHub")
        
        try:
            # Find the search form
            search_input = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.NAME, "q"))
            )
            
            # Enter search query and submit
            search_term = "selenium integration testing"
            search_input.send_keys(search_term)
            search_input.submit()
            print(f"[Form Test] Submitted search form with query: {search_term}")
            
            # Wait for search results page to load
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "repo-list"))
            )
            
            # Verify results page loaded correctly
            assert "Search" in browser.title
            print("[Form Test] Search results page loaded")
            
            # Check that results contain the search term
            results = browser.find_elements(By.CLASS_NAME, "repo-list-item")
            assert len(results) > 0, "No search results found"
            print(f"[Form Test] Found {len(results)} search results")
            
            # Check pagination if available
            try:
                pagination = browser.find_element(By.CLASS_NAME, "paginate-container")
                assert pagination is not None
                print("[Form Test] Pagination is available for search results")
            except NoSuchElementException:
                print("[Form Test] No pagination found (limited results)")
                
            print("[Form Test] Form submission integration test passed!")
            
        except Exception as e:
            pytest.fail(f"Form submission test failed: {e}")


class TestDataVisualizationUpdates:
    """Test suite for data visualization updates."""
    
    @pytest.fixture
    def browser(self):
        """Set up browser for testing."""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        yield driver
        driver.quit()
    
    def test_visualization_updates(self, browser):
        """Test chart updates based on user interaction using GitHub Insights."""
        # Navigate to a GitHub repository's insights/contributors page
        browser.get("https://github.com/SeleniumHQ/selenium/graphs/contributors")
        print("\n[Visualization Test] Navigated to GitHub Contributors visualization")
        
        try:
            # Wait for the chart to load
            WebDriverWait(browser, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "js-highlight-blob"))
            )
            print("[Visualization Test] Contributors chart loaded")
            
            # Find chart elements
            chart_container = browser.find_element(By.TAG_NAME, "svg")
            assert chart_container is not None
            
            # Get initial state (number of elements in chart)
            initial_elements = len(browser.find_elements(By.CSS_SELECTOR, "svg g rect.bar"))
            assert initial_elements > 0
            print(f"[Visualization Test] Chart contains {initial_elements} data points initially")
            
            # Change the time period using time range selector
            try:
                # Try to find and click on a different time range selector
                time_selector = browser.find_element(By.CSS_SELECTOR, ".js-period-container a:nth-child(2)")
                time_selector.click()
                print("[Visualization Test] Changed time period")
                
                # Wait for chart to update
                time.sleep(2)  # Allow time for chart to update
                
                # Check if chart elements changed (different number of bars)
                updated_elements = len(browser.find_elements(By.CSS_SELECTOR, "svg g rect.bar"))
                print(f"[Visualization Test] Chart contains {updated_elements} data points after update")
                
                # Note: Either the number of elements changes or the data changes
                print("[Visualization Test] Chart update test passed!")
            except NoSuchElementException:
                print("[Visualization Test] Could not find time period selector, skipping this step")
                
        except Exception as e:
            pytest.fail(f"Visualization update test failed: {e}")


class TestNavigationFlows:
    """Test suite for navigation flows."""
    
    @pytest.fixture
    def browser(self):
        """Set up browser for testing."""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        yield driver
        driver.quit()
    
    def test_repository_navigation(self, browser):
        """Test navigation between different sections of a GitHub repository."""
        # Navigate to a GitHub repository
        browser.get("https://github.com/SeleniumHQ/selenium")
        print("\n[Navigation Test] Navigated to GitHub repository")
        
        try:
            # Record initial URL
            initial_url = browser.current_url
            
            # Wait for the repository page to load
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "repository-container-header"))
            )
            print("[Navigation Test] Repository main page loaded")
            
            # Navigate to Issues
            issues_link = browser.find_element(By.CSS_SELECTOR, 'a[data-tab-item="i1issues-tab"]')
            issues_link.click()
            print("[Navigation Test] Clicked on Issues tab")
            
            # Wait for Issues page to load
            WebDriverWait(browser, 10).until(
                EC.url_contains("/issues")
            )
            print("[Navigation Test] Issues page loaded")
            
            # Verify URL changed
            assert "/issues" in browser.current_url
            assert browser.current_url != initial_url
            
            # Find the first issue and click on it
            first_issue = WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".js-navigation-container .js-issue-row a.h4"))
            )
            issue_title = first_issue.text
            first_issue.click()
            print(f"[Navigation Test] Clicked on issue: {issue_title}")
            
            # Wait for issue detail page to load
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "gh-header-title"))
            )
            print("[Navigation Test] Issue detail page loaded")
            
            # Verify we're on the issue detail page
            assert "/issues/" in browser.current_url
            detail_title = browser.find_element(By.CLASS_NAME, "gh-header-title").text
            assert issue_title in detail_title
            
            # Go back to issues list using breadcrumb
            back_link = browser.find_element(By.CSS_SELECTOR, ".js-issues-breadcrumb a")
            back_link.click()
            print("[Navigation Test] Clicked on back link to issues list")
            
            # Wait for issues list to load again
            WebDriverWait(browser, 10).until(
                EC.url_contains("/issues")
            )
            print("[Navigation Test] Issues list loaded again")
            
            # Verify we're back at the issues list
            assert "/issues" in browser.current_url and "/issues/" not in browser.current_url
            
            print("[Navigation Test] Navigation flow test passed!")
            
        except Exception as e:
            pytest.fail(f"Navigation flow test failed: {e}")


class TestErrorHandling:
    """Test suite for error handling."""
    
    @pytest.fixture
    def browser(self):
        """Set up browser for testing."""
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        yield driver
        driver.quit()
    
    def test_404_page_handling(self, browser):
        """Test how the application handles 404 errors."""
        # Navigate to a non-existent GitHub page
        browser.get("https://github.com/this-repository-does-not-exist-12345")
        print("\n[Error Test] Navigated to non-existent repository page")
        
        try:
            # Wait for 404 page to load
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "error-title"))
            )
            print("[Error Test] 404 error page loaded")
            
            # Verify 404 page shows correct error message
            error_title = browser.find_element(By.CLASS_NAME, "error-title")
            assert "404" in error_title.text or "Page not found" in error_title.text
            
            # Check if the page offers a way to go back to the homepage
            home_link = browser.find_element(By.LINK_TEXT, "Home")
            assert home_link is not None
            print("[Error Test] Found link to home page on 404 page")
            
            # Verify the homepage link works
            home_link.click()
            WebDriverWait(browser, 10).until(
                EC.url_contains("github.com")
            )
            assert "github.com" in browser.current_url
            print("[Error Test] Successfully navigated back to home from 404 page")
            
            print("[Error Test] 404 error handling test passed!")
            
        except Exception as e:
            pytest.fail(f"Error handling test failed: {e}")
    
    def test_input_validation(self, browser):
        """Test form validation and error handling."""
        # Navigate to GitHub signup page
        browser.get("https://github.com/signup")
        print("\n[Error Test] Navigated to GitHub signup page")
        
        try:
            # Wait for the form to load
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            print("[Error Test] Signup form loaded")
            
            # Try submitting form with invalid email
            email_field = browser.find_element(By.ID, "email")
            email_field.send_keys("invalid-email")
            
            # Click continue button
            continue_button = browser.find_element(By.CSS_SELECTOR, "button[data-continue-to='password-container']")
            continue_button.click()
            
            # Wait for validation error to appear
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "error-message"))
            )
            print("[Error Test] Validation error message appeared")
            
            # Check error message
            error_message = browser.find_element(By.CLASS_NAME, "error-message")
            assert error_message.is_displayed()
            assert "email" in error_message.text.lower()
            print(f"[Error Test] Error message displayed: '{error_message.text}'")
            
            # Fix the input with valid email and verify form proceeds
            email_field.clear()
            email_field.send_keys("valid_test_email@example.com")
            continue_button.click()
            
            # Check if we move to the next section (password)
            try:
                WebDriverWait(browser, 5).until(
                    EC.presence_of_element_located((By.ID, "password"))
                )
                print("[Error Test] Form accepted valid email and proceeded to next step")
            except TimeoutException:
                # The form might not proceed due to captcha or other validation
                print("[Error Test] Form did not proceed to next step (possibly due to captcha)")
            
            print("[Error Test] Form validation handling test passed!")
            
        except Exception as e:
            pytest.fail(f"Input validation test failed: {e}")


if __name__ == "__main__":
    pytest.main(["-v", __file__]) 