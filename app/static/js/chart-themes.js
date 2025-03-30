/**
 * Chart.js Theming Support
 * 
 * This file adds theme support for Chart.js to match light/dark mode
 */

/**
 * Get the current theme colors for charts
 * @returns {Object} Theme colors and options
 */
function getChartTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
    const isDark = currentTheme === 'dark';
    
    // Get CSS variables for the current theme
    const textColor = getComputedStyle(document.documentElement)
        .getPropertyValue('--text-primary')
        .trim();
    
    const gridColor = getComputedStyle(document.documentElement)
        .getPropertyValue('--chart-grid-color')
        .trim();
    
    return {
        textColor: textColor,
        gridColor: gridColor,
        isDark: isDark
    };
}

/**
 * Apply theme to Chart.js defaults
 */
function applyChartTheme() {
    const theme = getChartTheme();
    console.log('Applying chart theme:', theme.isDark ? 'dark' : 'light');
    
    // Set Chart.js global defaults
    Chart.defaults.color = theme.textColor;
    Chart.defaults.borderColor = theme.gridColor;
    
    Chart.defaults.scale.grid.color = theme.gridColor;
    Chart.defaults.scale.ticks.color = theme.textColor;
    
    // Update existing charts if available
    updateExistingCharts();
}

/**
 * Update existing charts with new theme
 */
function updateExistingCharts() {
    // Sentiment chart
    if (window.sentimentChart) {
        window.sentimentChart.update();
    }
    
    // Keywords chart
    if (window.keywordsChart) {
        window.keywordsChart.update();
    }
    
    // Trend chart
    if (window.trendChart) {
        window.trendChart.update();
    }
}

// Apply theme on page load
document.addEventListener('DOMContentLoaded', () => {
    applyChartTheme();
    
    // Listen for theme changes
    document.addEventListener('themeChanged', () => {
        applyChartTheme();
    });
});

// Create a MutationObserver to watch for theme changes via attribute
const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
        if (
            mutation.type === 'attributes' && 
            mutation.attributeName === 'data-theme'
        ) {
            applyChartTheme();
        }
    });
});

// Start observing the document
observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme']
}); 