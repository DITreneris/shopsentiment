import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains


class TestUIEnhancements:
    """Test suite for UI enhancements as specified in the afternoon session plan."""
    
    def test_color_scheme(self, live_server, browser):
        """Test the modernized color scheme."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for the dashboard to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        
        # Get the main elements to check their colors
        header = browser.find_element(By.CLASS_NAME, "dashboard-header")
        card = browser.find_element(By.CLASS_NAME, "dashboard-card")
        
        # Check the color values against expected modern palette
        header_bg_color = header.value_of_css_property("background-color")
        card_bg_color = card.value_of_css_property("background-color")
        
        # Assert modern color scheme (adjust expected values as needed)
        assert header_bg_color != "rgba(0, 0, 0, 0)", "Header should have a background color"
        assert card_bg_color != "rgba(0, 0, 0, 0)", "Card should have a background color"
        
        # Check text contrast for accessibility
        header_text = header.find_element(By.TAG_NAME, "h1")
        header_text_color = header_text.value_of_css_property("color")
        
        # Ensure text color contrasts with background (simple check)
        assert header_text_color != header_bg_color, "Text color should contrast with background"
    
    def test_responsive_grid(self, live_server, browser):
        """Test the responsive grid system implementation."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for the dashboard to load
        dashboard_grid = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        
        # Check grid properties at desktop size
        desktop_columns = dashboard_grid.value_of_css_property("grid-template-columns")
        desktop_gap = dashboard_grid.value_of_css_property("gap")
        
        # Resize to tablet size
        browser.set_window_size(768, 1024)
        time.sleep(1)  # Allow time for resize to take effect
        
        # Check grid properties at tablet size
        tablet_columns = dashboard_grid.value_of_css_property("grid-template-columns")
        tablet_gap = dashboard_grid.value_of_css_property("gap")
        
        # Resize to mobile size
        browser.set_window_size(375, 667)
        time.sleep(1)  # Allow time for resize to take effect
        
        # Check grid properties at mobile size
        mobile_columns = dashboard_grid.value_of_css_property("grid-template-columns")
        mobile_gap = dashboard_grid.value_of_css_property("gap")
        
        # Verify responsive behavior
        assert desktop_columns != mobile_columns, "Grid columns should adapt to screen size"
        
        # Reset window size
        browser.set_window_size(1920, 1080)
    
    def test_animations(self, live_server, browser):
        """Test subtle animations for better user feedback."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for the dashboard to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        
        # Test button hover animations
        button = browser.find_element(By.ID, "refreshDashboard")
        
        # Get initial state
        initial_background = button.value_of_css_property("background-color")
        initial_transform = button.value_of_css_property("transform")
        
        # Hover over the button
        ActionChains(browser).move_to_element(button).perform()
        time.sleep(0.5)  # Wait for animation
        
        # Get hover state
        hover_background = button.value_of_css_property("background-color")
        hover_transform = button.value_of_css_property("transform")
        
        # Check for hover effects
        assert initial_background != hover_background or initial_transform != hover_transform, \
            "Button should have hover animation effects"
        
        # Test card transition effects
        toggle_button = browser.find_element(By.ID, "toggleFilters")
        toggle_button.click()
        
        # Get advanced filters element
        filter_section = browser.find_element(By.ID, "advancedFilters")
        
        # Check if transition property is set
        transition_property = filter_section.value_of_css_property("transition")
        assert "opacity" in transition_property or "height" in transition_property or "transform" in transition_property, \
            "Filters section should have transition animation"
    
    def test_typography_spacing(self, live_server, browser):
        """Test improved typography and spacing."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for the dashboard to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        
        # Check line height on paragraph text
        paragraph = browser.find_element(By.TAG_NAME, "p")
        line_height = paragraph.value_of_css_property("line-height")
        
        # Good typography typically has line-height >= 1.5
        line_height_value = float(line_height.replace("px", ""))
        font_size = float(paragraph.value_of_css_property("font-size").replace("px", ""))
        
        line_height_ratio = line_height_value / font_size
        assert line_height_ratio >= 1.4, "Line height should be at least 1.4x font size for readability"
        
        # Check spacing between elements
        cards = browser.find_elements(By.CLASS_NAME, "dashboard-card")
        card_margin = cards[0].value_of_css_property("margin")
        
        # Ensure margins are defined
        assert card_margin != "0px" and card_margin != "0px 0px 0px 0px", "Cards should have proper margins"


class TestDataVisualization:
    """Test suite for enhanced data visualization components."""
    
    def test_chart_appearance(self, live_server, browser):
        """Test chart visual appearance improvements."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for charts to load
        WebDriverWait(browser, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "chart-container"))
        )
        
        # Get all chart containers
        chart_containers = browser.find_elements(By.CLASS_NAME, "chart-container")
        assert len(chart_containers) > 0, "No charts found on the dashboard"
        
        # Check for canvas elements (Chart.js uses canvas)
        canvas_elements = browser.find_elements(By.TAG_NAME, "canvas")
        assert len(canvas_elements) > 0, "No chart canvas elements found"
        
        # Check for chart title styling
        chart_titles = browser.find_elements(By.CLASS_NAME, "chart-title")
        for title in chart_titles:
            font_weight = title.value_of_css_property("font-weight")
            font_size = title.value_of_css_property("font-size")
            
            # Convert font-weight to numeric value if it's not already
            if not font_weight.isdigit():
                weight_map = {"normal": 400, "bold": 700}
                font_weight = weight_map.get(font_weight, 400)
            
            assert int(font_weight) >= 500, "Chart titles should have medium or bold font weight"
            assert float(font_size.replace("px", "")) >= 16, "Chart titles should be at least 16px"
    
    def test_interactive_tooltips(self, live_server, browser):
        """Test interactive tooltips with detailed information."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for charts to load
        WebDriverWait(browser, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "chart-container"))
        )
        
        # Find a chart canvas to interact with
        canvas_elements = browser.find_elements(By.TAG_NAME, "canvas")
        assert len(canvas_elements) > 0, "No chart canvas elements found"
        
        # Move to the center of the chart to trigger tooltip
        canvas = canvas_elements[0]
        action = ActionChains(browser)
        action.move_to_element(canvas)
        action.move_by_offset(10, 10)  # Move to a point likely to have data
        action.perform()
        
        # Wait for tooltip to appear
        time.sleep(1)  # Brief pause to allow tooltip to render
        
        # Check for tooltip elements
        # Note: Chart.js tooltips are often rendered as div elements with specific classes
        try:
            tooltip = browser.find_element(By.CLASS_NAME, "chartjs-tooltip")
            assert tooltip.is_displayed(), "Tooltip should be visible on hover"
        except:
            # If the specific class isn't found, look for any tooltip-like element that appeared
            tooltips = browser.find_elements(By.CSS_SELECTOR, "[class*='tooltip']")
            assert len(tooltips) > 0, "No tooltip elements found"
    
    def test_chart_transitions(self, live_server, browser):
        """Test smooth transitions between chart states."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for charts to load
        WebDriverWait(browser, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "chart-container"))
        )
        
        # Find time period selector to change chart data
        time_selector = browser.find_element(By.ID, "timeframeSelector")
        
        # Get initial chart state (screenshot or canvas reference)
        charts = browser.find_elements(By.TAG_NAME, "canvas")
        
        # Change the time period
        time_selector.click()
        options = browser.find_elements(By.TAG_NAME, "option")
        for option in options:
            if option.get_attribute("value") != time_selector.get_attribute("value"):
                option.click()
                break
        
        # Check for animation class or property
        chart_containers = browser.find_elements(By.CLASS_NAME, "chart-container")
        for container in chart_containers:
            animation_property = container.value_of_css_property("transition") or container.value_of_css_property("animation")
            assert animation_property and animation_property != "none", "Charts should have transition/animation properties"


class TestFormInteractions:
    """Test suite for improved form interactions."""
    
    def test_real_time_validation(self, live_server, browser):
        """Test real-time validation feedback on forms."""
        # Navigate to the feedback form
        browser.get(f"{live_server}/feedback")
        
        # Wait for the form to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "feedbackForm"))
        )
        
        # Find email input field
        email_field = browser.find_element(By.ID, "email")
        
        # Enter invalid email
        email_field.clear()
        email_field.send_keys("invalid-email")
        
        # Click elsewhere to trigger validation
        browser.find_element(By.TAG_NAME, "body").click()
        
        # Check for validation message
        time.sleep(0.5)  # Allow time for validation to occur
        
        # Look for validation feedback elements
        validation_message = browser.find_element(By.CSS_SELECTOR, ".invalid-feedback")
        assert validation_message.is_displayed(), "Validation message should be visible"
        assert "valid email" in validation_message.text.lower(), "Validation message should mention email format"
        
        # Check that input has invalid class
        assert "is-invalid" in email_field.get_attribute("class"), "Invalid input should have is-invalid class"
        
        # Fix the email and check validation passes
        email_field.clear()
        email_field.send_keys("valid@example.com")
        browser.find_element(By.TAG_NAME, "body").click()
        
        time.sleep(0.5)  # Allow time for validation to occur
        
        # Check for valid state
        assert "is-valid" in email_field.get_attribute("class"), "Valid input should have is-valid class"
    
    def test_form_feedback_styling(self, live_server, browser):
        """Test improved error message styling."""
        # Navigate to the feedback form
        browser.get(f"{live_server}/feedback")
        
        # Wait for the form to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "feedbackForm"))
        )
        
        # Find required field
        name_field = browser.find_element(By.ID, "name")
        
        # Submit form without filling required field
        submit_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Check for styled error message
        error_message = browser.find_element(By.CSS_SELECTOR, ".invalid-feedback")
        
        # Verify error styling
        error_color = error_message.value_of_css_property("color")
        error_font_weight = error_message.value_of_css_property("font-weight")
        
        # Error messages are typically red and bold
        assert "rgb(220, 53, 69)" in error_color or "rgb(255, 0, 0)" in error_color or "#dc3545" in error_color, \
            "Error message should have red text color"
        
        # Convert font-weight to numeric if needed
        if not error_font_weight.isdigit():
            weight_map = {"normal": 400, "bold": 700}
            error_font_weight = weight_map.get(error_font_weight, 0)
            
        assert int(error_font_weight) >= 400, "Error message should have normal or bold font weight"
    
    def test_notifications(self, live_server, browser):
        """Test success/error notifications."""
        # Navigate to the feedback form
        browser.get(f"{live_server}/feedback")
        
        # Wait for the form to load
        form = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "feedbackForm"))
        )
        
        # Fill out the form correctly
        name_field = browser.find_element(By.ID, "name")
        email_field = browser.find_element(By.ID, "email")
        message_field = browser.find_element(By.ID, "message")
        
        name_field.send_keys("Test User")
        email_field.send_keys("test@example.com")
        message_field.send_keys("This is a test message for notification testing")
        
        # Submit the form
        submit_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Wait for notification to appear
        notification = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "notification"))
        )
        
        # Verify notification styling
        assert notification.is_displayed(), "Notification should be visible"
        assert "show" in notification.get_attribute("class"), "Notification should have show class"
        
        # Check content based on success/error state
        notification_content = notification.text.lower()
        assert "success" in notification_content or "thank you" in notification_content or \
               "error" in notification_content or "problem" in notification_content, \
               "Notification should indicate success or error"
        
        # Verify notification has proper styling
        notification_bg = notification.value_of_css_property("background-color")
        notification_border = notification.value_of_css_property("border")
        
        assert notification_bg != "rgba(0, 0, 0, 0)", "Notification should have background color"
        assert "px" in notification_border, "Notification should have a visible border" 