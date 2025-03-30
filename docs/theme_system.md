# ShopSentiment Theme System Documentation

This document provides detailed technical information about the ShopSentiment theme system implementation.

## Overview

The theme system allows users to switch between light and dark modes throughout the application. It's built on modern web standards and best practices for theme implementation.

## Core Components

### 1. CSS Variables

The foundation of the theme system is in `app/static/css/theme.css`, which defines two sets of CSS variables:

- **Light theme** (default): Defined in the `:root` selector
- **Dark theme**: Defined in the `[data-theme="dark"]` selector

These variables control colors, shadows, borders, and other visual aspects of the UI.

### 2. Theme Manager

The `ThemeManager` class in `app/static/js/theme-manager.js` handles:

- Theme initialization based on:
  - Previously saved preference (via localStorage)
  - System preference (using `prefers-color-scheme` media query)
  - Default fallback (light theme)
- Toggling between themes
- Saving theme preference
- Dispatching theme change events

### 3. Chart Theme Integration

`app/static/js/chart-themes.js` extends the theme system to Chart.js visualizations by:

- Reading current theme variables
- Applying them to Chart.js defaults
- Updating existing charts on theme changes
- Using a MutationObserver to watch for theme attribute changes

## Implementation Details

### Theme Detection and Application

```javascript
// Get system preference
const prefersDarkScheme = window.matchMedia('(prefers-color-scheme: dark)');

// Get saved preference
const savedTheme = localStorage.getItem('theme');

// Apply theme
document.documentElement.setAttribute('data-theme', themeValue);
```

### Theme Switch Logic

```javascript
// Toggle theme
switchTheme() {
    const newTheme = this.themeToggle.checked ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // Notify other components about theme change
    document.dispatchEvent(new CustomEvent('themeChanged', {
        detail: { theme: newTheme }
    }));
}
```

### Chart Theme Application

```javascript
// Apply theme to chart
function applyChartTheme() {
    const theme = getChartTheme();
    
    Chart.defaults.color = theme.textColor;
    Chart.defaults.borderColor = theme.gridColor;
    Chart.defaults.scale.grid.color = theme.gridColor;
    Chart.defaults.scale.ticks.color = theme.textColor;
    
    updateExistingCharts();
}
```

## CSS Structure

The CSS is organized with these key sections:

1. **Root Variables**: Default (light) theme variables
2. **Dark Theme Variables**: Overrides for dark theme
3. **Element Styling**: Applies variables to HTML elements
4. **Component-Specific Theming**: Special handling for complex components
5. **Transitions**: Smooth animations between theme states

## Extending the Theme System

### Adding New Theme Variables

To add a new theme variable:

1. Add it to both `:root` and `[data-theme="dark"]` in `theme.css`
2. Use the variable in your CSS with `var(--variable-name)`

Example:
```css
:root {
    --new-color: #ff5500;
}

[data-theme="dark"] {
    --new-color: #ff8800;
}

.my-element {
    color: var(--new-color);
}
```

### Creating Theme-Aware Components

For JavaScript components that need to respond to theme changes:

1. Listen for theme changes:
```javascript
document.addEventListener('themeChanged', (e) => {
    const theme = e.detail.theme;
    updateComponentForTheme(theme);
});
```

2. Check current theme at initialization:
```javascript
const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
```

### Adding Additional Themes

To add a new theme beyond light/dark:

1. Add a new selector in `theme.css`:
```css
[data-theme="new-theme-name"] {
    --bg-primary: #value;
    --text-primary: #value;
    /* etc... */
}
```

2. Modify `ThemeManager` to support the new theme option

## Best Practices

1. Always use CSS variables for themed elements, never hardcode colors
2. Test all components in both light and dark themes
3. Ensure sufficient contrast in both themes for accessibility
4. Use transitions for smooth theme changes
5. Consider both color and layout changes between themes

## Browser Support

The theme system requires browsers that support:
- CSS Variables (Custom Properties)
- JavaScript localStorage
- ES6 features including classes and arrow functions

Modern versions of Chrome, Firefox, Safari, and Edge are all supported. 