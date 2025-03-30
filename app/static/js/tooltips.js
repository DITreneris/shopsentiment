/**
 * ShopSentiment Tooltips and Guided Tour
 * 
 * Provides helpful tooltips and a guided tour of the application
 */

class TooltipManager {
    constructor() {
        console.log('TooltipManager: Initializing...');
        this.tooltips = {
            // Home page tooltips
            'platform-select': 'Choose the e-commerce platform to analyze.',
            'product-id': 'Enter the product ID or URL from the e-commerce site.',
            'analyze-button': 'Start the analysis process for the selected product.',
            'recent-products': 'Recently analyzed products and their sentiment scores.',
            'view-dashboard': 'View detailed analysis for this product.',
            'start-tour': 'Take a guided tour of the application features.',
            
            // Dashboard tooltips
            'sentiment-chart': 'Shows the distribution of positive, neutral, and negative reviews.',
            'filter-sentiment': 'Filter reviews by sentiment category.',
            'keywords-chart': 'Displays the most common words found in reviews.',
            'keyword-filter': 'Filter keywords by sentiment category.',
            'trend-chart': 'Shows how sentiment changes over time.',
            'timeframe-filter': 'Change the time period for the sentiment trend chart.',
            'export-csv': 'Export review data to CSV format.',
            'export-json': 'Export review data to JSON format.',
            'reviews-table': 'All reviews for this product with sentiment analysis.',
            'search-reviews': 'Search for specific content within reviews.',
            
            // Theme toggle
            'theme-toggle': 'Switch between light and dark theme.'
        };
        
        // Tour steps configuration for different pages
        this.tourSteps = {
            'home': [
                { element: '#platform', title: 'Select Platform', content: 'Start by selecting which platform the product is from.' },
                { element: '#product_id', title: 'Product ID', content: 'Enter the product ID (ASIN for Amazon, Item ID for eBay).' },
                { element: '#url', title: 'Product URL', content: 'Enter the complete URL to the product page.' },
                { element: '#custom_selectors', title: 'Custom Selectors', content: 'For custom websites, provide CSS selectors to locate review elements.', condition: () => document.querySelector('#platform').value === 'custom' },
                { element: 'button[type="submit"]', title: 'Analyze', content: 'Click to start scraping and analyzing the product reviews.' }
            ],
            'dashboard': [
                { element: '#sentimentChart', title: 'Sentiment Distribution', content: 'This pie chart shows how many reviews are positive, neutral, or negative.' },
                { element: '#keywordsChart', title: 'Top Keywords', content: 'This chart shows the most common words found in reviews.' },
                { element: '#trendChart', title: 'Sentiment Trend', content: 'This chart shows how sentiment has changed over time.' },
                { element: '#reviewsTable', title: 'Reviews Table', content: 'This table lists all reviews with their sentiment analysis scores.' },
                { element: '#filter-positive', title: 'Sentiment Filters', content: 'Use these checkboxes to filter reviews by sentiment.' },
                { element: '#keyword-filter-sentiment', title: 'Keyword Filters', content: 'Filter keywords based on the sentiment of reviews they appear in.' },
                { element: '[data-timeframe="all"]', title: 'Timeframe Filters', content: 'View sentiment trends over different time periods.' },
                { element: '#review-search', title: 'Search Reviews', content: 'Search for specific words or phrases in the reviews.' },
                { element: '.btn-outline-primary', title: 'Export Data', content: 'Download the reviews data as CSV or JSON for further analysis.' },
                { element: '#theme-toggle', title: 'Theme Toggle', content: 'Switch between light and dark modes for comfortable viewing.' }
            ]
        };
    }
    
    /**
     * Initialize tooltips on the page
     */
    initTooltips() {
        // Add tooltips to elements with data-tooltip attribute
        document.querySelectorAll('[data-tooltip]').forEach(element => {
            const tooltipKey = element.dataset.tooltip;
            if (this.tooltips[tooltipKey]) {
                element.setAttribute('title', this.tooltips[tooltipKey]);
                // Bootstrap tooltips initialization would go here if using Bootstrap's tooltip component
            }
        });
    }
    
    /**
     * Start the guided tour for the current page
     * @param {string} page - The page type ('home' or 'dashboard')
     */
    startTour(page) {
        // Determine which page we're on if not specified
        let tourType = page || 'home';
        if (!page && window.location.pathname.includes('dashboard')) {
            tourType = 'dashboard';
        }
        
        // Get the steps for this page
        const steps = this.tourSteps[tourType];
        if (!steps || steps.length === 0) {
            console.warn('No tour steps defined for this page');
            return;
        }
        
        // Filter steps based on conditions
        const validSteps = steps.filter(step => {
            if (step.condition && typeof step.condition === 'function') {
                return step.condition();
            }
            return document.querySelector(step.element) !== null;
        });
        
        if (validSteps.length === 0) {
            console.warn('No valid tour steps for this page');
            return;
        }
        
        // Start the tour
        this._showTourStep(validSteps, 0);
    }
    
    /**
     * Show a tour step (simple implementation - would use a proper tour library in production)
     * @private
     */
    _showTourStep(steps, index) {
        if (index >= steps.length) {
            this._endTour();
            return;
        }
        
        const step = steps[index];
        const element = document.querySelector(step.element);
        
        if (!element) {
            // Skip this step if element doesn't exist
            this._showTourStep(steps, index + 1);
            return;
        }
        
        // Create and show a simple tour popup
        const popup = document.createElement('div');
        popup.className = 'tour-popup';
        popup.innerHTML = `
            <div class="tour-popup-header">${step.title}</div>
            <div class="tour-popup-body">${step.content}</div>
            <div class="tour-popup-footer">
                <button class="btn btn-sm ${index === 0 ? 'btn-outline-secondary disabled' : 'btn-outline-primary'}" id="tour-prev" ${index === 0 ? 'disabled' : ''}>Previous</button>
                <span class="tour-counter">${index + 1}/${steps.length}</span>
                <button class="btn btn-sm btn-primary" id="tour-next">${index === steps.length - 1 ? 'Finish' : 'Next'}</button>
            </div>
        `;
        
        // Add to document
        document.body.appendChild(popup);
        this._positionPopup(popup, element);
        
        // Highlight the element
        const elemPosition = element.getBoundingClientRect();
        const highlight = document.createElement('div');
        highlight.className = 'tour-highlight';
        
        // Position the highlight
        highlight.style.top = elemPosition.top + window.scrollY + 'px';
        highlight.style.left = elemPosition.left + window.scrollX + 'px';
        highlight.style.width = elemPosition.width + 'px';
        highlight.style.height = elemPosition.height + 'px';
        document.body.appendChild(highlight);
        
        // Add event listeners for navigation
        popup.querySelector('#tour-next').addEventListener('click', () => {
            popup.remove();
            highlight.remove();
            this._showTourStep(steps, index + 1);
        });
        
        if (index > 0) {
            popup.querySelector('#tour-prev').addEventListener('click', () => {
                popup.remove();
                highlight.remove();
                this._showTourStep(steps, index - 1);
            });
        }
        
        // Scroll element into view if needed
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
    
    /**
     * Position the popup near the target element
     * @private
     */
    _positionPopup(popup, targetElement) {
        const rect = targetElement.getBoundingClientRect();
        const popupRect = popup.getBoundingClientRect();
        
        // Try to position below the element first
        let top = rect.bottom + window.scrollY + 10;
        let left = rect.left + window.scrollX + (rect.width / 2) - (popupRect.width / 2);
        
        // Make sure the popup is within viewport
        if (left < 10) left = 10;
        if (left + popupRect.width > window.innerWidth - 10) {
            left = window.innerWidth - popupRect.width - 10;
        }
        
        popup.style.top = top + 'px';
        popup.style.left = left + 'px';
    }
    
    /**
     * End the tour
     * @private
     */
    _endTour() {
        const tourElements = document.querySelectorAll('.tour-popup, .tour-highlight');
        tourElements.forEach(el => el.remove());
    }
}

// Initialize tooltips and tour on page load
document.addEventListener('DOMContentLoaded', function() {
    // Create tooltip manager
    window.tooltipManager = new TooltipManager();
    
    // Initialize tooltips
    window.tooltipManager.initTooltips();
    
    // Add start tour button if needed
    if (!document.querySelector('#start-tour')) {
        const tourButton = document.createElement('button');
        tourButton.id = 'start-tour';
        tourButton.className = 'btn btn-sm btn-primary tour-button';
        tourButton.innerHTML = '<i class="bi bi-info-circle-fill me-1"></i> Quick Tour';
        tourButton.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
        `;
        
        tourButton.addEventListener('click', function() {
            window.tooltipManager.startTour();
        });
        
        document.body.appendChild(tourButton);
    }
}); 