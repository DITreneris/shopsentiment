"""
Simplified Integration Test for Local Demo Page

This script tests our local demo_page.html that covers the four key integration testing areas:
1. Form Submissions
2. Data Visualization Updates
3. Navigation Flows
4. Error Handling
"""

import pytest
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Get the absolute path to the demo page
DEMO_PAGE_PATH = os.path.abspath("demo_page.html")
DEMO_PAGE_URL = f"file:///{DEMO_PAGE_PATH}"

class TestLocalIntegration:
    """Test suite for integration testing with local demo page."""
    
    @pytest.fixture
    def browser(self):
        """Set up browser for testing."""
        options = Options()
        # Running in visible mode (not headless) for better debugging
        # options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        yield driver
        driver.quit()
    
    def test_form_submission(self, browser):
        """Test form submission and validation (Task 3.2)."""
        try:
            browser.get(DEMO_PAGE_URL)
            print("\n[Form Test] Loaded demo page")
            
            # Navigate to feedback page
            feedback_link = browser.find_element(By.ID, "feedback-link")
            feedback_link.click()
            print("[Form Test] Navigated to feedback page")
            
            # Wait for form to be visible
            WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.ID, "feedback-form"))
            )
            
            # Test form validation with empty fields
            submit_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
            submit_button.click()
            print("[Form Test] Submitted form with empty fields")
            
            # Check that validation errors appear
            WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.ID, "name-error"))
            )
            assert browser.find_element(By.ID, "name-error").is_displayed()
            assert browser.find_element(By.ID, "email-error").is_displayed()
            assert browser.find_element(By.ID, "rating-error").is_displayed()
            assert browser.find_element(By.ID, "comment-error").is_displayed()
            print("[Form Test] Validation errors displayed correctly")
            
            # Fill out the form with valid data
            browser.find_element(By.ID, "name").send_keys("Test User")
            browser.find_element(By.ID, "email").send_keys("test@example.com")
            browser.find_element(By.ID, "rating").send_keys("5 - Excellent")
            browser.find_element(By.ID, "comment").send_keys("This is a test comment")
            print("[Form Test] Filled out form with valid data")
            
            # Submit the form
            submit_button.click()
            print("[Form Test] Submitted form with valid data")
            
            # Check for success message
            WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.ID, "form-success"))
            )
            assert browser.find_element(By.ID, "form-success").is_displayed()
            assert "Thank you for your feedback" in browser.find_element(By.ID, "form-success").text
            print("[Form Test] Success message displayed correctly")
            
            print("[Form Test] Form submission integration test passed!")
            return True
        except Exception as e:
            print(f"[Form Test] Test failed: {e}")
            return False
    
    def test_data_visualization_update(self, browser):
        """Test data visualization updates (Task 3.2)."""
        try:
            browser.get(DEMO_PAGE_URL)
            print("\n[Visualization Test] Loaded demo page")
            
            # Navigate to dashboard page
            dashboard_link = browser.find_element(By.ID, "dashboard-link")
            dashboard_link.click()
            print("[Visualization Test] Navigated to dashboard page")
            
            # Wait for visualization to be visible
            WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "visualization"))
            )
            
            # Get initial chart state - heights of bars
            bars = browser.find_elements(By.CSS_SELECTOR, ".chart-container .bar")
            initial_heights = [bar.get_attribute("style") for bar in bars]
            print(f"[Visualization Test] Found {len(bars)} bars in the chart")
            
            # Click on 30 days button to update chart
            time_button = browser.find_element(By.CSS_SELECTOR, ".time-btn[data-days='30']")
            time_button.click()
            print("[Visualization Test] Clicked on 30 days button")
            
            # Wait for loading indicator to appear and then disappear
            WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.CLASS_NAME, "loading"))
            )
            WebDriverWait(browser, 10).until(
                EC.invisibility_of_element_located((By.CLASS_NAME, "loading"))
            )
            print("[Visualization Test] Chart updated")
            
            # Verify chart has been updated
            updated_bars = browser.find_elements(By.CSS_SELECTOR, ".chart-container .bar")
            updated_heights = [bar.get_attribute("style") for bar in updated_bars]
            
            # Check that heights have changed
            assert initial_heights != updated_heights
            print("[Visualization Test] Chart heights changed as expected")
            
            print("[Visualization Test] Data visualization update test passed!")
            return True
        except Exception as e:
            print(f"[Visualization Test] Test failed: {e}")
            return False
    
    def test_navigation_flow(self, browser):
        """Test navigation flows and breadcrumbs (Task 3.2)."""
        try:
            browser.get(DEMO_PAGE_URL)
            print("\n[Navigation Test] Loaded demo page")
            
            # Check initial page and breadcrumb
            assert browser.find_element(By.ID, "home-page").is_displayed()
            assert browser.find_element(By.ID, "breadcrumb").text == "Home"
            print("[Navigation Test] Verified home page and breadcrumb")
            
            # Navigate to dashboard
            dashboard_link = browser.find_element(By.ID, "dashboard-link")
            dashboard_link.click()
            
            # Verify dashboard page is displayed and breadcrumb updated
            WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.ID, "dashboard-page"))
            )
            assert browser.find_element(By.ID, "dashboard-page").is_displayed()
            assert browser.find_element(By.ID, "breadcrumb").text == "Home > Dashboard"
            print("[Navigation Test] Verified dashboard page and breadcrumb")
            
            # Navigate to feedback page
            feedback_link = browser.find_element(By.ID, "feedback-link")
            feedback_link.click()
            
            # Verify feedback page is displayed and breadcrumb updated
            WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.ID, "feedback-page"))
            )
            assert browser.find_element(By.ID, "feedback-page").is_displayed()
            assert browser.find_element(By.ID, "breadcrumb").text == "Home > Feedback"
            print("[Navigation Test] Verified feedback page and breadcrumb")
            
            # Navigate back to home
            home_link = browser.find_element(By.ID, "home-link")
            home_link.click()
            
            # Verify home page is displayed and breadcrumb updated
            WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.ID, "home-page"))
            )
            assert browser.find_element(By.ID, "home-page").is_displayed()
            assert browser.find_element(By.ID, "breadcrumb").text == "Home"
            print("[Navigation Test] Verified navigation back to home page")
            
            print("[Navigation Test] Navigation flow test passed!")
            return True
        except Exception as e:
            print(f"[Navigation Test] Test failed: {e}")
            return False
    
    def test_error_handling(self, browser):
        """Test error handling and recovery (Task 3.2)."""
        try:
            browser.get(DEMO_PAGE_URL)
            print("\n[Error Test] Loaded demo page")
            
            # Trigger error page
            error_link = browser.find_element(By.ID, "error-link")
            error_link.click()
            print("[Error Test] Clicked error link")
            
            # Verify error page is displayed
            WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.ID, "error-page"))
            )
            assert browser.find_element(By.ID, "error-page").is_displayed()
            assert "404" in browser.find_element(By.ID, "error-page").text
            print("[Error Test] Verified error page is displayed")
            
            # Test recovery by clicking "Back to Home" button
            back_button = browser.find_element(By.ID, "back-to-home")
            back_button.click()
            print("[Error Test] Clicked 'Back to Home' button")
            
            # Verify returned to home page
            WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.ID, "home-page"))
            )
            assert browser.find_element(By.ID, "home-page").is_displayed()
            print("[Error Test] Verified recovery to home page")
            
            print("[Error Test] Error handling test passed!")
            return True
        except Exception as e:
            print(f"[Error Test] Test failed: {e}")
            return False

if __name__ == "__main__":
    # Run tests individually with descriptive output
    print("Running Integration Tests for Shop Sentiment Demo...")
    
    # Create test instance
    test = TestLocalIntegration()
    
    # Set up browser - using visible mode for debugging
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1200,800")
    
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    # Track test results
    results = {
        "form_submission": False,
        "data_visualization": False,
        "navigation_flow": False,
        "error_handling": False
    }
    
    try:
        # Run tests with proper error handling
        print("\n--- Running Form Submission Test ---")
        results["form_submission"] = test.test_form_submission(browser)
        
        print("\n--- Running Data Visualization Test ---")
        results["data_visualization"] = test.test_data_visualization_update(browser)
        
        print("\n--- Running Navigation Flow Test ---")
        results["navigation_flow"] = test.test_navigation_flow(browser)
        
        print("\n--- Running Error Handling Test ---")
        results["error_handling"] = test.test_error_handling(browser)
        
        # Print summary
        print("\n--- Integration Test Results Summary ---")
        for test_name, passed in results.items():
            print(f"{test_name}: {'PASSED' if passed else 'FAILED'}")
        
        if all(results.values()):
            print("\nAll integration tests passed successfully!")
        else:
            print("\nSome tests failed. Please check the logs above for details.")
    except Exception as e:
        print(f"\nUnexpected error during testing: {e}")
    finally:
        # Clean up - pause for a moment to see the final state
        time.sleep(2)
        browser.quit() 