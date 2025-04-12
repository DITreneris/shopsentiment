/**
 * Main JavaScript file for Shop Sentiment Analysis
 */

// Helper function to show error messages
function showError(message, targetElement) {
    const errorElement = document.createElement('div');
    errorElement.className = 'error-message';
    errorElement.textContent = message;
    
    if (targetElement) {
        targetElement.innerHTML = '';
        targetElement.appendChild(errorElement);
    } else {
        console.error(message);
    }
}

// Format date in a more readable way
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
} 