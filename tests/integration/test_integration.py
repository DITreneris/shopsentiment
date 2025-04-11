import pytest
import time
import json
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys


class TestFormSubmissions:
    """Test suite for form submission integration with backend processing."""
    
    def test_feedback_form_submission(self, live_server, browser, mocker):
        """Test that feedback form submissions are processed correctly."""
        # Mock the form submission handler to avoid actual email sending
        mock_submit = mocker.patch('app.routes.submit_feedback')
        mock_submit.return_value = True
        
        # Navigate to the feedback form
        browser.get(f"{live_server}/feedback")
        
        # Wait for the form to load
        form = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "feedbackForm"))
        )
        
        # Fill out the form
        name_field = browser.find_element(By.ID, "name")
        email_field = browser.find_element(By.ID, "email")
        message_field = browser.find_element(By.ID, "message")
        
        test_name = "Integration Test User"
        test_email = "integration@test.com"
        test_message = "This is an integration test message"
        
        name_field.send_keys(test_name)
        email_field.send_keys(test_email)
        message_field.send_keys(test_message)
        
        # Submit the form
        submit_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Wait for success notification
        notification = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "notification"))
        )
        
        # Verify the form was submitted with correct data
        assert mock_submit.called, "Form submission handler should be called"
        call_args = mock_submit.call_args[0][0]  # First positional argument of the first call
        
        assert call_args.get('name') == test_name, "Name should match submitted value"
        assert call_args.get('email') == test_email, "Email should match submitted value"
        assert call_args.get('message') == test_message, "Message should match submitted value"
        
        # Verify the notification indicates success
        notification_text = notification.text.lower()
        assert "success" in notification_text or "thank you" in notification_text, \
               "Notification should indicate successful submission"
    
    def test_search_form_and_results(self, live_server, browser):
        """Test search form submission and results display integration."""
        # Navigate to the search page
        browser.get(f"{live_server}/search")
        
        # Wait for the search form to load
        search_form = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "searchForm"))
        )
        
        # Enter search query
        search_input = browser.find_element(By.ID, "searchQuery")
        search_query = "test product"
        search_input.send_keys(search_query)
        
        # Submit the search
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()
        
        # Wait for results to load
        results_container = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "searchResults"))
        )
        
        # Check that results are displayed
        results = browser.find_elements(By.CLASS_NAME, "search-result-item")
        assert len(results) > 0, "Search should return results"
        
        # Verify search query appears in the results heading
        results_heading = browser.find_element(By.ID, "resultsHeading")
        assert search_query in results_heading.text, "Search query should appear in results heading"
        
        # Test pagination if available
        try:
            pagination = browser.find_element(By.CLASS_NAME, "pagination")
            page_links = pagination.find_elements(By.TAG_NAME, "a")
            
            if len(page_links) > 1:
                # Click on page 2
                page_2 = next((link for link in page_links if link.text.strip() == "2"), None)
                if page_2:
                    page_2.click()
                    
                    # Wait for new results to load
                    WebDriverWait(browser, 10).until(
                        EC.staleness_of(results[0])  # First result from previous page should be gone
                    )
                    
                    # Verify new results loaded
                    new_results = browser.find_elements(By.CLASS_NAME, "search-result-item")
                    assert len(new_results) > 0, "Second page should have results"
                    assert new_results[0] != results[0], "Results should be different on page 2"
        except:
            # Pagination might not be present if few results
            pass


class TestDataVisualizationUpdates:
    """Test suite for data visualization updates based on user input."""
    
    def test_chart_updates_on_filter_change(self, live_server, browser):
        """Test that charts update when filter criteria change."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for charts to load
        WebDriverWait(browser, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "chart-container"))
        )
        
        # Find timeline chart (assuming it has a specific ID)
        timeline_chart = browser.find_element(By.ID, "timelineChart")
        
        # Get initial state (can be done by checking data attributes or canvas properties)
        initial_state = timeline_chart.get_attribute("data-last-update")
        
        # Find time period filter
        time_filter = browser.find_element(By.ID, "timeframeSelector")
        
        # Change the time period
        current_value = time_filter.get_attribute("value")
        new_options = browser.find_elements(By.CSS_SELECTOR, f"#timeframeSelector option:not([value='{current_value}'])")
        if new_options:
            new_value = new_options[0].get_attribute("value")
            time_filter.click()
            browser.find_element(By.CSS_SELECTOR, f"option[value='{new_value}']").click()
            
            # Wait for chart to update
            WebDriverWait(browser, 10).until(
                lambda browser: timeline_chart.get_attribute("data-last-update") != initial_state
            )
            
            # Verify the chart was updated
            updated_state = timeline_chart.get_attribute("data-last-update")
            assert updated_state != initial_state, "Chart should update after filter change"
    
    def test_realtime_sentiment_updates(self, live_server, browser, mocker):
        """Test that sentiment dashboard updates with new data."""
        # Mock WebSocket or polling mechanism to inject a test update
        mock_update = {"sentiment_score": 0.75, "product_id": "test-product", "timestamp": int(time.time())}
        
        # Navigate to dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for sentiment display to load
        sentiment_display = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "sentimentScore"))
        )
        
        # Record initial score value
        initial_score = sentiment_display.text
        
        # Inject mock data update via JavaScript
        update_script = f"""
        // Simulate receiving a WebSocket message
        const event = new CustomEvent('sentiment-update', {{
            detail: {json.dumps(mock_update)}
        }});
        document.dispatchEvent(event);
        """
        browser.execute_script(update_script)
        
        # Wait for display to update
        WebDriverWait(browser, 10).until(
            lambda browser: sentiment_display.text != initial_score
        )
        
        # Verify display was updated
        updated_score = sentiment_display.text
        assert updated_score != initial_score, "Sentiment score should update after receiving new data"
        assert str(mock_update["sentiment_score"]) in updated_score, "Display should show the updated score"


class TestNavigationFlows:
    """Test suite for navigation flow integration."""
    
    def test_dashboard_to_detail_flow(self, live_server, browser):
        """Test navigation from dashboard to detail views."""
        # Navigate to the dashboard
        browser.get(f"{live_server}/dashboard")
        
        # Wait for dashboard to load
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        
        # Find a clickable element that should navigate to a detail view
        detail_links = browser.find_elements(By.CSS_SELECTOR, ".chart-drill-down")
        assert len(detail_links) > 0, "Dashboard should have drill-down links"
        
        # Click the first drill-down link
        initial_url = browser.current_url
        detail_links[0].click()
        
        # Wait for navigation to complete
        WebDriverWait(browser, 10).until(
            lambda browser: browser.current_url != initial_url
        )
        
        # Verify we've navigated to a detail page
        assert "/detail" in browser.current_url or "/product/" in browser.current_url, \
               "Should navigate to a detail page"
        
        # Verify the breadcrumb navigation shows the flow
        breadcrumb = browser.find_element(By.CLASS_NAME, "breadcrumb")
        breadcrumb_items = breadcrumb.find_elements(By.CLASS_NAME, "breadcrumb-item")
        
        # Check for Dashboard in breadcrumb items
        breadcrumb_texts = [item.text for item in breadcrumb_items]
        assert "Dashboard" in breadcrumb_texts, "Breadcrumb should show Dashboard as previous page"
        
        # Test navigation back to dashboard via breadcrumb
        dashboard_link = breadcrumb.find_element(By.LINK_TEXT, "Dashboard")
        dashboard_link.click()
        
        # Verify we're back at the dashboard
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "dashboard-grid"))
        )
        assert "/dashboard" in browser.current_url, "Should navigate back to dashboard"
    
    def test_global_navigation_menu(self, live_server, browser):
        """Test the global navigation menu links and states."""
        # Navigate to the home page
        browser.get(f"{live_server}/")
        
        # Wait for navigation menu to load
        nav_menu = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "main-nav"))
        )
        
        # Get all navigation links
        nav_links = nav_menu.find_elements(By.TAG_NAME, "a")
        assert len(nav_links) >= 3, "Navigation should have at least 3 links"
        
        # Store original URL
        original_url = browser.current_url
        
        # Test each link
        for i, link in enumerate(nav_links):
            if i > 0:  # Skip the first link as we're already on that page
                # Get link text for verification
                link_text = link.text
                
                # Click the link
                link.click()
                
                # Wait for new page to load
                WebDriverWait(browser, 10).until(
                    lambda browser: browser.current_url != original_url
                )
                
                # Verify page title or heading contains link text
                try:
                    heading = WebDriverWait(browser, 5).until(
                        EC.presence_of_element_located((By.TAG_NAME, "h1"))
                    )
                    assert link_text.lower() in heading.text.lower(), \
                           f"Page heading should contain nav link text '{link_text}'"
                except:
                    # If no h1, check the title
                    assert link_text.lower() in browser.title.lower(), \
                           f"Page title should contain nav link text '{link_text}'"
                
                # Check active state in navigation
                new_nav = browser.find_element(By.CLASS_NAME, "main-nav")
                active_link = new_nav.find_element(By.CLASS_NAME, "active")
                assert link_text.lower() in active_link.text.lower(), \
                       f"Navigation should mark '{link_text}' as active"
                
                # Go back to original page for next iteration
                browser.get(original_url)
                
                # Wait for original page to reload
                WebDriverWait(browser, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "main-nav"))
                )
                
                # Re-fetch navigation menu and links for next iteration
                nav_menu = browser.find_element(By.CLASS_NAME, "main-nav")
                nav_links = nav_menu.find_elements(By.TAG_NAME, "a")


class TestErrorHandling:
    """Test suite for error handling integration."""
    
    def test_form_error_handling(self, live_server, browser, mocker):
        """Test error handling during form submission."""
        # Mock the form submission to simulate a server error
        mock_submit = mocker.patch('app.routes.submit_feedback')
        mock_submit.side_effect = Exception("Simulated server error")
        
        # Navigate to the feedback form
        browser.get(f"{live_server}/feedback")
        
        # Wait for the form to load
        form = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "feedbackForm"))
        )
        
        # Fill out the form
        name_field = browser.find_element(By.ID, "name")
        email_field = browser.find_element(By.ID, "email")
        message_field = browser.find_element(By.ID, "message")
        
        name_field.send_keys("Error Test User")
        email_field.send_keys("error@test.com")
        message_field.send_keys("This should trigger an error")
        
        # Submit the form
        submit_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()
        
        # Wait for error notification
        error_notification = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "notification-error"))
        )
        
        # Verify error notification is displayed properly
        assert error_notification.is_displayed(), "Error notification should be visible"
        
        # Check error message content
        error_text = error_notification.text.lower()
        assert "error" in error_text or "failed" in error_text or "sorry" in error_text, \
               "Error notification should indicate something went wrong"
        
        # Check that form is still accessible and data is preserved
        assert name_field.get_attribute("value") == "Error Test User", \
               "Form should preserve user input after error"
    
    def test_empty_search_results_handling(self, live_server, browser, mocker):
        """Test handling of empty search results."""
        # Mock the search function to return empty results
        mock_search = mocker.patch('app.routes.search_products')
        mock_search.return_value = []
        
        # Navigate to search page
        browser.get(f"{live_server}/search")
        
        # Wait for search form
        search_form = WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "searchForm"))
        )
        
        # Enter search query
        search_input = browser.find_element(By.ID, "searchQuery")
        search_input.send_keys("nonexistent product")
        
        # Submit search
        search_button = browser.find_element(By.CSS_SELECTOR, "button[type='submit']")
        search_button.click()
        
        # Wait for results container to load (even with no results)
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.ID, "searchResults"))
        )
        
        # Check for no results message
        no_results = browser.find_element(By.CLASS_NAME, "no-results")
        assert no_results.is_displayed(), "No results message should be shown"
        assert "no results" in no_results.text.lower(), "Message should indicate no results found"
        
        # Verify search form is still present for new search
        assert search_form.is_displayed(), "Search form should remain accessible"
        
        # Verify there are suggested alternatives or a try again message
        try:
            suggestions = browser.find_element(By.CLASS_NAME, "search-suggestions")
            assert suggestions.is_displayed(), "Search suggestions should be shown"
        except:
            # If no suggestions element, look for try again messaging
            assert "try again" in no_results.text.lower() or "try different" in no_results.text.lower(), \
                   "Should suggest trying a different search" 