/**
 * Dynamic favicon generator for ShopSentiment
 * This script creates a simple favicon on the fly to avoid 404 errors
 */

(function() {
    // Create a canvas element to draw the favicon
    const canvas = document.createElement('canvas');
    canvas.width = 32;
    canvas.height = 32;
    
    const ctx = canvas.getContext('2d');
    
    // Get current theme
    const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
    
    // Define colors based on theme
    const bgColor = isDarkMode ? '#222' : '#fff';
    const letterColor = isDarkMode ? '#fff' : '#0d6efd';
    const borderColor = '#0d6efd';
    
    // Draw background
    ctx.fillStyle = bgColor;
    ctx.fillRect(0, 0, 32, 32);
    
    // Draw border
    ctx.strokeStyle = borderColor;
    ctx.lineWidth = 2;
    ctx.strokeRect(1, 1, 30, 30);
    
    // Draw letter 'S'
    ctx.fillStyle = letterColor;
    ctx.font = 'bold 24px Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('S', 16, 16);
    
    // Convert to favicon and add to document
    const link = document.createElement('link');
    link.rel = 'icon';
    link.type = 'image/x-icon';
    link.href = canvas.toDataURL('image/png');
    document.head.appendChild(link);
    
    // Update favicon when theme changes
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.attributeName === 'data-theme') {
                // Regenerate favicon when theme changes
                const isDarkMode = document.documentElement.getAttribute('data-theme') === 'dark';
                const bgColor = isDarkMode ? '#222' : '#fff';
                const letterColor = isDarkMode ? '#fff' : '#0d6efd';
                
                ctx.fillStyle = bgColor;
                ctx.fillRect(0, 0, 32, 32);
                
                ctx.strokeStyle = borderColor;
                ctx.lineWidth = 2;
                ctx.strokeRect(1, 1, 30, 30);
                
                ctx.fillStyle = letterColor;
                ctx.font = 'bold 24px Arial';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillText('S', 16, 16);
                
                link.href = canvas.toDataURL('image/png');
            }
        });
    });
    
    observer.observe(document.documentElement, { attributes: true });
})(); 