/**
 * Theme Manager for ShopSentiment
 * Handles switching between light and dark themes
 */

class ThemeManager {
    constructor() {
        this.themeToggle = document.getElementById('theme-toggle');
        this.prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');
        this.currentTheme = localStorage.getItem('theme');
        
        this.init();
    }
    
    init() {
        console.log('ThemeManager: Initializing...');
        
        // Set initial theme based on saved preference or system preference
        if (this.currentTheme) {
            console.log(`ThemeManager: Using saved theme: ${this.currentTheme}`);
            document.documentElement.setAttribute('data-theme', this.currentTheme);
            if (this.currentTheme === 'dark') {
                this.themeToggle.checked = true;
            }
        } else if (this.prefersDarkScheme.matches) {
            console.log('ThemeManager: Using system dark mode preference');
            document.documentElement.setAttribute('data-theme', 'dark');
            this.themeToggle.checked = true;
            localStorage.setItem('theme', 'dark');
        } else {
            console.log('ThemeManager: Using default light theme');
            document.documentElement.setAttribute('data-theme', 'light');
            localStorage.setItem('theme', 'light');
        }
        
        // Add event listener for theme toggle
        this.themeToggle.addEventListener('change', () => this.switchTheme());
        
        // Listen for system preference changes
        this.prefersDarkScheme.addEventListener('change', (e) => this.handleSystemPreferenceChange(e));
    }
    
    switchTheme() {
        const newTheme = this.themeToggle.checked ? 'dark' : 'light';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Dispatch an event that the theme has changed
        const event = new CustomEvent('themeChanged', {
            detail: { theme: newTheme }
        });
        document.dispatchEvent(event);
        
        console.log(`Theme switched to: ${newTheme}`);
    }
    
    handleSystemPreferenceChange(e) {
        // Only update if user hasn't manually set a preference
        if (!localStorage.getItem('theme')) {
            const newTheme = e.matches ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', newTheme);
            this.themeToggle.checked = e.matches;
            
            // Dispatch theme change event
            const event = new CustomEvent('themeChanged', {
                detail: { theme: newTheme }
            });
            document.dispatchEvent(event);
        }
    }
}

// Initialize theme manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Wait a short time to ensure the toggle element is available
    setTimeout(() => {
        const themeToggle = document.getElementById('theme-toggle');
        if (themeToggle) {
            window.themeManager = new ThemeManager();
        } else {
            console.warn('Theme toggle element not found');
        }
    }, 100);
}); 