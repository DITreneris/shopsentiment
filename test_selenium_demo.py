"""
Selenium Demo for UI and Integration Tests
This script demonstrates how to run Selenium-based tests for UI components and integration
without needing to fully integrate with the actual application.
"""
import pytest
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys

def run_ui_test():
    """Run a simple UI test demo."""
    # Set up Chrome WebDriver with headless option
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    try:
        # Create WebDriver instance
        driver = webdriver.Chrome(options=options)
        
        # Navigate to a website for testing
        driver.get("https://www.example.com")
        print("\n[UI Test] Navigated to example.com")
        
        # Check the page title
        assert "Example Domain" in driver.title
        print("[UI Test] Page title verified")
        
        # Find elements on the page
        heading = driver.find_element(By.TAG_NAME, "h1")
        assert heading.text == "Example Domain"
        print("[UI Test] Heading verified")
        
        # Check the main paragraph
        paragraph = driver.find_element(By.TAG_NAME, "p")
        assert "for illustrative examples" in paragraph.text
        print("[UI Test] Paragraph content verified")
        
        # Check the links
        links = driver.find_elements(By.TAG_NAME, "a")
        assert any("More information" in link.text for link in links)
        print("[UI Test] Links verified")
        
        print("[UI Test] All tests passed!")
        
    except Exception as e:
        print(f"[UI Test] Test failed: {e}")
        
    finally:
        # Clean up
        driver.quit()
        
def run_integration_test():
    """Run a simple integration test demo."""
    # Set up Chrome WebDriver with headless option
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    
    try:
        # Create WebDriver instance
        driver = webdriver.Chrome(options=options)
        
        # Navigate to a website that has forms (GitHub login)
        driver.get("https://github.com/login")
        print("\n[Integration Test] Navigated to GitHub login page")
        
        # Check the page title
        assert "Sign in to GitHub" in driver.title
        print("[Integration Test] Page title verified")
        
        # Find the login form
        login_form = driver.find_element(By.TAG_NAME, "form")
        assert login_form is not None
        print("[Integration Test] Login form found")
        
        # Find the username and password fields
        username_field = driver.find_element(By.ID, "login_field")
        password_field = driver.find_element(By.ID, "password")
        assert username_field is not None and password_field is not None
        print("[Integration Test] Username and password fields found")
        
        # Test form validation (don't actually submit)
        # Enter a username but no password
        username_field.send_keys("test_user")
        
        # Try to submit the form
        submit_button = driver.find_element(By.NAME, "commit")
        submit_button.click()
        
        # Wait for error message (since we didn't enter a password)
        error_message = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "flash-error"))
        )
        
        # Verify error message appears
        assert error_message is not None
        assert "Incorrect username or password" in error_message.text
        print("[Integration Test] Form validation works - error message displayed for incomplete form")
        
        print("[Integration Test] All tests passed!")
        
    except Exception as e:
        print(f"[Integration Test] Test failed: {e}")
        
    finally:
        # Clean up
        driver.quit()

if __name__ == "__main__":
    print("Running UI Test Demo...")
    run_ui_test()
    
    print("\nRunning Integration Test Demo...")
    run_integration_test() 