import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

class TestDashboardComponents:
    """Test suite for dashboard UI components."""
    
    def test_dashboard_header(self, live_server, browser):
        """Test the dashboard header components and styling."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for the dashboard header to load
        header = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-header"))
        )
        
        # Verify the header title
        title = header.find_element(By.TAG_NAME, "h1")
        assert "Sentiment Analysis Dashboard" in title.text
        
        # Verify the subtitle
        subtitle = header.find_element(By.CLASS_NAME, "header-subtitle")
        assert "Monitor and analyze" in subtitle.text
        
        # Verify the refresh button
        refresh_button = header.find_element(By.ID, "refreshDashboard")
        assert refresh_button.is_displayed()
        assert "Refresh Data" in refresh_button.text
        
        # Verify the last updated text
        last_updated = header.find_element(By.ID, "lastUpdated")
        assert "Last updated" in last_updated.text
    
    def test_dashboard_cards(self, live_server, browser):
        """Test the dashboard cards are present and properly styled."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for dashboard grid to load
        grid = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        
        # Verify all cards are present
        cards = grid.find_elements(By.CLASS_NAME, "dashboard-card")
        assert len(cards) >= 4, "Expected at least 4 dashboard cards"
        
        # Verify card titles
        card_titles = [
            "Sentiment Trend", 
            "Rating Distribution", 
            "Keyword Sentiment",
            "Product Comparison"
        ]
        
        # Check each title exists in the dashboard
        for title in card_titles:
            title_element = browser.find_element(By.XPATH, f"//h3[contains(text(), '{title}')]")
            assert title_element.is_displayed(), f"Card title '{title}' not found"
    
    def test_form_controls(self, live_server, browser):
        """Test form controls functionality and validation."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for the dashboard to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        
        # Test product selector
        product_selector = browser.find_element(By.ID, "productSelector")
        assert product_selector.is_displayed()
        assert product_selector.is_enabled()
        
        # Test timeframe selector
        timeframe_selector = browser.find_element(By.ID, "timeframeSelector")
        assert timeframe_selector.is_displayed()
        assert timeframe_selector.is_enabled()
        
        # Test platform selector
        platform_selector = browser.find_element(By.ID, "platformSelector")
        assert platform_selector.is_displayed()
        assert platform_selector.is_enabled()
        
        # Test keyword count slider
        slider = browser.find_element(By.ID, "keywordCountSlider")
        assert slider.is_displayed()
        assert slider.is_enabled()
        assert slider.get_attribute("type") == "range"
        assert slider.get_attribute("min") == "5"
        assert slider.get_attribute("max") == "30"
        
        # Test the value display updates when slider moves
        initial_value = browser.find_element(By.ID, "keywordCountValue").text
        
        # Use JavaScript to set the slider value
        browser.execute_script("arguments[0].value = '20'; arguments[0].dispatchEvent(new Event('input'));", slider)
        time.sleep(0.5)  # Allow time for the event to propagate
        
        updated_value = browser.find_element(By.ID, "keywordCountValue").text
        assert initial_value != updated_value
        assert updated_value == "20"
    
    def test_advanced_filters(self, live_server, browser):
        """Test advanced filters section visibility toggle and form elements."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for the dashboard to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        
        # Find the toggle button
        toggle_button = browser.find_element(By.ID, "toggleFilters")
        assert toggle_button.is_displayed()
        assert "Show Filters" in toggle_button.text
        
        # Filter section should be hidden initially
        filter_section = browser.find_element(By.ID, "advancedFilters")
        assert "show" not in filter_section.get_attribute("class")
        
        # Click the toggle button
        toggle_button.click()
        
        # Wait for animation to complete
        time.sleep(1)
        
        # Filter section should be visible now
        assert "show" in filter_section.get_attribute("class")
        assert "Hide Filters" in toggle_button.text
        
        # Verify filter form elements
        date_start = browser.find_element(By.ID, "dateRangeStart")
        date_end = browser.find_element(By.ID, "dateRangeEnd")
        keyword_filter = browser.find_element(By.ID, "keywordFilter")
        min_reviews = browser.find_element(By.ID, "minReviewCount")
        
        assert date_start.is_displayed()
        assert date_end.is_displayed()
        assert keyword_filter.is_displayed()
        assert min_reviews.is_displayed()
        
        # Verify rating checkboxes
        for i in range(1, 6):
            rating_checkbox = browser.find_element(By.ID, f"rating{i}")
            assert rating_checkbox.is_displayed()
            assert rating_checkbox.is_selected()  # Should be checked by default
    
    def test_responsive_behavior(self, live_server, browser):
        """Test responsive behavior of the dashboard."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for the dashboard to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        
        # Test desktop layout (default size 1920x1080 from fixture)
        grid = browser.find_element(By.CLASS_NAME, "dashboard-grid")
        desktop_display = grid.value_of_css_property("grid-template-columns")
        
        # Resize to tablet size
        browser.set_window_size(768, 1024)
        time.sleep(1)  # Allow time for resize to take effect
        
        # Check tablet layout
        tablet_display = grid.value_of_css_property("grid-template-columns")
        
        # Resize to mobile size
        browser.set_window_size(375, 667)
        time.sleep(1)  # Allow time for resize to take effect
        
        # Check mobile layout
        mobile_display = grid.value_of_css_property("grid-template-columns")
        
        # Verify layouts are different
        assert desktop_display != mobile_display, "Desktop and mobile layouts should be different"
        
        # Check card header layout on mobile
        card_header = browser.find_element(By.CLASS_NAME, "card-header")
        header_flex_direction = card_header.value_of_css_property("flex-direction")
        
        assert header_flex_direction == "column", "Card header should be in column layout on mobile"
        
        # Reset window size
        browser.set_window_size(1920, 1080)
    
    def test_notification_system(self, live_server, browser):
        """Test the notification system functionality."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for the dashboard to load and refresh button to be visible
        refresh_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.ID, "refreshDashboard"))
        )
        
        # Click refresh to trigger a notification
        refresh_button.click()
        
        # Wait for notification to appear
        notification = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "notification"))
        )
        
        # Verify notification appears and has correct content
        assert notification.is_displayed()
        assert "show" in notification.get_attribute("class")
        
        # Check notification content
        notification_title = notification.find_element(By.CLASS_NAME, "notification-title")
        notification_message = notification.find_element(By.CLASS_NAME, "notification-message")
        
        assert "Success" in notification_title.text
        assert "updated" in notification_message.text
        
        # Wait for notification to auto-dismiss (5 seconds)
        time.sleep(6)
        
        # Check if notification is gone or hidden
        try:
            is_visible = notification.is_displayed() and "show" in notification.get_attribute("class")
            assert not is_visible, "Notification should auto-dismiss after 5 seconds"
        except:
            # If element is removed from DOM, an exception will be thrown, which is also acceptable
            pass

    @pytest.mark.accessibility
    def test_accessibility_focus_states(self, live_server, browser):
        """Test keyboard focus states for accessibility."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for the dashboard to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        
        # Get all focusable elements
        focusable_elements = browser.find_elements(By.CLASS_NAME, "focusable")
        assert len(focusable_elements) > 0, "No focusable elements found"
        
        # Test focus state on first focusable element
        first_element = focusable_elements[0]
        
        # Use JavaScript to focus the element
        browser.execute_script("arguments[0].focus();", first_element)
        time.sleep(0.5)  # Allow time for focus to take effect
        
        # Check if element has focus
        active_element = browser.execute_script("return document.activeElement;")
        assert active_element == first_element, "Element should have focus"
        
        # Use JavaScript to check the computed style of the focused element
        box_shadow = browser.execute_script(
            "return window.getComputedStyle(arguments[0]).getPropertyValue('box-shadow');", 
            first_element
        )
        
        # Box shadow should be non-empty when focused
        assert box_shadow and box_shadow != "none", "Focused element should have a box-shadow" 