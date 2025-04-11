import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestPagePerformance:
    """Test suite for performance testing."""
    
    def test_dashboard_load_time(self, live_server, browser):
        """Test dashboard page load time."""
        # Record start time
        start_time = time.time()
        
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for the dashboard to fully load by checking for key elements
        WebDriverWait(browser, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        
        # Calculate load time
        load_time = time.time() - start_time
        
        # Print the load time for reporting
        print(f"\nDashboard load time: {load_time:.2f} seconds")
        
        # Assert that load time is under threshold (adjust as needed)
        assert load_time < 3.0, f"Dashboard load time ({load_time:.2f}s) exceeds threshold (3.0s)"
    
    def test_search_response_time(self, live_server, browser):
        """Test search response time."""
        # Navigate to the search page
        browser.get(f"{live_server}/search")
        
        # Wait for search form to load
        search_form = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "searchForm"))
        )
        
        # Enter search query
        search_input = browser.find_element(By.ID, "searchQuery")
        search_query = "test product"
        search_input.send_keys(search_query)
        
        # Record start time before submitting search
        start_time = time.time()
        
        # Submit the search
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()
        
        # Wait for results to load
        results_container = WebDriverWait(browser, 15).until(
            EC.presence_of_element_located((By.ID, "searchResults"))
        )
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Print the response time for reporting
        print(f"\nSearch response time: {response_time:.2f} seconds")
        
        # Assert that response time is under threshold (adjust as needed)
        assert response_time < 2.0, f"Search response time ({response_time:.2f}s) exceeds threshold (2.0s)"
    
    def test_chart_render_time(self, live_server, browser):
        """Test chart rendering performance."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for the dashboard to load without charts first
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        
        # Record start time before charts load
        start_time = time.time()
        
        # Wait for all chart canvases to be present
        WebDriverWait(browser, 20).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "canvas"))
        )
        
        # Calculate render time
        render_time = time.time() - start_time
        
        # Print the render time for reporting
        print(f"\nChart render time: {render_time:.2f} seconds")
        
        # Assert that render time is under threshold (adjust as needed)
        assert render_time < 1.5, f"Chart render time ({render_time:.2f}s) exceeds threshold (1.5s)"


class TestSlowConnectionSimulation:
    """Test suite for simulating slow connections."""
    
    @pytest.mark.slow_network
    def test_dashboard_on_slow_connection(self, live_server, browser):
        """Test dashboard performance on simulated slow connection."""
        # Simulate slow connection using Chrome DevTools Protocol
        if browser.capabilities['browserName'] == 'chrome':
            # Setting network conditions (download: 50kb/s, upload: 20kb/s, latency: 500ms)
            browser.execute_cdp_cmd('Network.emulateNetworkConditions', {
                'offline': False,
                'downloadThroughput': 50 * 1024 / 8,  # Convert from kbps to bytes/s
                'uploadThroughput': 20 * 1024 / 8,
                'latency': 500
            })
        
        # Record start time
        start_time = time.time()
        
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for critical elements to appear
        WebDriverWait(browser, 60).until(  # Increased timeout for slow connection
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        
        # Calculate load time
        load_time = time.time() - start_time
        
        # Print the load time for reporting
        print(f"\nDashboard load time on slow connection: {load_time:.2f} seconds")
        
        # Check for loading indicators or fallback content during load
        try:
            skeleton_loaders = browser.find_elements(By.CLASS_NAME, "skeleton-loader")
            assert len(skeleton_loaders) > 0, "Skeleton loaders should be visible during slow loading"
        except:
            # If no skeleton loaders, check for other loading indicators
            loading_indicators = browser.find_elements(By.CSS_SELECTOR, ".loading, .spinner, [aria-busy='true']")
            assert len(loading_indicators) > 0, "Loading indicators should be visible during slow loading"
        
        # Reset network conditions if using Chrome
        if browser.capabilities['browserName'] == 'chrome':
            browser.execute_cdp_cmd('Network.emulateNetworkConditions', {
                'offline': False,
                'latency': 0,
                'downloadThroughput': -1,
                'uploadThroughput': -1
            })
    
    @pytest.mark.slow_network
    def test_progressive_image_loading(self, live_server, browser):
        """Test progressive image loading on slow connections."""
        # Simulate slow connection if using Chrome
        if browser.capabilities['browserName'] == 'chrome':
            browser.execute_cdp_cmd('Network.emulateNetworkConditions', {
                'offline': False,
                'downloadThroughput': 50 * 1024 / 8,
                'uploadThroughput': 20 * 1024 / 8,
                'latency': 500
            })
        
        # Navigate to a page with images
        browser.get(f"{live_server}/")
        
        # Wait for page to start loading
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Find images
        images = browser.find_elements(By.TAG_NAME, "img")
        
        # Check for lazy loading attribute
        lazy_loaded_images = [img for img in images if img.get_attribute("loading") == "lazy"]
        assert len(lazy_loaded_images) > 0, "Images should use lazy loading"
        
        # Check for responsive image attributes
        responsive_images = [
            img for img in images if 
            img.get_attribute("srcset") or 
            img.get_attribute("sizes") or
            "placeholder" in img.get_attribute("class").lower()
        ]
        assert len(responsive_images) > 0, "Images should use responsive loading techniques"
        
        # Reset network conditions if using Chrome
        if browser.capabilities['browserName'] == 'chrome':
            browser.execute_cdp_cmd('Network.emulateNetworkConditions', {
                'offline': False,
                'latency': 0,
                'downloadThroughput': -1,
                'uploadThroughput': -1
            })


class TestCachingVerification:
    """Test suite for verifying caching behavior."""
    
    def test_static_asset_caching(self, live_server, browser):
        """Test that static assets are properly cached."""
        # Navigate to the dashboard first time
        browser.get(f"{live_server}/dashboard")
        
        # Wait for the page to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        
        # Get performance timing data
        first_load_timing = browser.execute_script("return window.performance.timing")
        
        # Navigate to another page
        browser.get(f"{live_server}/search")
        
        # Wait for the search page to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "searchForm"))
        )
        
        # Navigate back to dashboard for second load (should use cached assets)
        start_time = time.time()
        browser.get(f"{live_server}/dashboard")
        
        # Wait for the dashboard to load again
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        
        # Calculate second load time
        second_load_time = time.time() - start_time
        
        # Print the load times for reporting
        print(f"\nDashboard second load time (with caching): {second_load_time:.2f} seconds")
        
        # Verify that cached load is faster (should be significantly faster)
        try:
            # Try to get detailed performance metrics if available
            cached_resources = browser.execute_script("""
                const resources = performance.getEntriesByType('resource');
                return resources.filter(r => r.transferSize === 0).length;
            """)
            
            print(f"Number of cached resources: {cached_resources}")
            assert cached_resources > 0, "Some resources should be loaded from cache"
        except:
            # Fallback to simpler time-based assertion
            assert second_load_time < 2.0, "Second load with caching should be fast"
    
    def test_memory_usage(self, live_server, browser):
        """Test memory usage during app usage."""
        # Only works on Chrome
        if browser.capabilities['browserName'] != 'chrome':
            pytest.skip("Memory usage test only supported in Chrome")
        
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for the dashboard to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        
        # Get initial memory info
        initial_memory = browser.execute_script("return performance.memory")
        initial_heap_size = initial_memory.get('usedJSHeapSize', 0)
        
        # Perform several actions to simulate usage
        # 1. Toggle filters
        toggle_button = browser.find_element(By.ID, "toggleFilters")
        toggle_button.click()
        
        # 2. Change time period
        time_filter = browser.find_element(By.ID, "timeframeSelector")
        time_filter.click()
        options = browser.find_elements(By.TAG_NAME, "option")
        for option in options:
            if option.get_attribute("value") != time_filter.get_attribute("value"):
                option.click()
                break
        
        # 3. Refresh data
        refresh_button = browser.find_element(By.ID, "refreshDashboard")
        refresh_button.click()
        
        # Wait for potential memory leaks to manifest
        time.sleep(2)
        
        # Get final memory info
        final_memory = browser.execute_script("return performance.memory")
        final_heap_size = final_memory.get('usedJSHeapSize', 0)
        
        # Calculate memory increase
        memory_increase = final_heap_size - initial_heap_size
        memory_increase_mb = memory_increase / (1024 * 1024)
        
        # Print memory usage for reporting
        print(f"\nMemory usage increase: {memory_increase_mb:.2f} MB")
        
        # Memory usage should not increase dramatically (adjust threshold as needed)
        assert memory_increase_mb < 50, f"Memory increase ({memory_increase_mb:.2f} MB) exceeds threshold (50 MB)" 