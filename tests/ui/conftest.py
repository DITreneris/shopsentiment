import os
import pytest
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

from app import create_app

@pytest.fixture(scope="session")
def app():
    """Create and configure a Flask app for testing."""
    app = create_app(testing=True)
    
    # Create a temporary database for testing
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SERVER_NAME'] = 'localhost.localdomain'
    
    yield app
    
    # Clean up temporary database
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])

@pytest.fixture(scope="session")
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope="session")
def browser(request):
    """Provide a selenium webdriver instance."""
    browser_name = request.config.getoption("--browser") or "chrome"
    headless = request.config.getoption("--headless", True)
    
    if browser_name.lower() == "chrome":
        options = Options()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        
        browser = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
    elif browser_name.lower() == "firefox":
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        
        browser = webdriver.Firefox(
            service=Service(GeckoDriverManager().install()),
            options=options
        )
    else:
        raise ValueError(f"Unsupported browser: {browser_name}")
    
    browser.set_window_size(1920, 1080)
    
    yield browser
    
    # Quit the browser after the test
    browser.quit()

@pytest.fixture(scope="session")
def live_server(app, request):
    """Run the Flask app in a background process for end-to-end testing."""
    import multiprocessing
    import time
    
    port = request.config.getoption("--port") or 8000
    
    def run_app():
        app.run(host="localhost", port=port, use_reloader=False)
    
    # Start the Flask app in a separate process
    process = multiprocessing.Process(target=run_app)
    process.start()
    
    # Wait for the server to start
    time.sleep(1)
    
    # Return the URL to the Flask app
    url = f"http://localhost:{port}"
    
    yield url
    
    # Terminate the Flask app after testing
    process.terminate()
    process.join()

def pytest_addoption(parser):
    """Add command line options for UI testing."""
    parser.addoption("--browser", action="store", default="chrome", help="Browser to use for UI tests (chrome or firefox)")
    parser.addoption("--headless", action="store_true", default=True, help="Run browser in headless mode")
    parser.addoption("--port", action="store", default=8000, help="Port to run Flask app on for testing") 