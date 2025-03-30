# ShopSentiment Tooltips and Guided Tour Documentation

This document provides technical details about the tooltips and guided tour implementation in ShopSentiment.

## Overview

The tooltips and guided tour system provides contextual help information to users and offers an interactive walkthrough of application features.

## Core Components

### 1. TooltipManager Class

The core of the system is the `TooltipManager` class in `app/static/js/tooltips.js`, which:

- Manages tooltip content definitions
- Initializes tooltips for elements with `data-tooltip` attributes
- Controls the guided tour functionality
- Handles the step-by-step progression of the tour

### 2. Tooltip Content

Tooltips are defined in a central object within the `TooltipManager` class:

```javascript
this.tooltips = {
    'platform-select': 'Choose the e-commerce platform to analyze.',
    'product-id': 'Enter the product ID or URL from the e-commerce site.',
    // Additional tooltips...
};
```

### 3. Tour Steps

Tour steps are defined as an object containing arrays of steps for different pages:

```javascript
this.tourSteps = {
    'home': [
        {
            element: '.platform-select',
            title: 'Select Platform',
            content: 'Choose which e-commerce platform you want to analyze.'
        },
        // Additional steps...
    ],
    'dashboard': [
        // Dashboard-specific steps...
    ]
};
```

## Implementation Details

### Tooltip Initialization

```javascript
initTooltips() {
    // Find all elements with data-tooltip attribute
    const elements = document.querySelectorAll('[data-tooltip]');
    
    elements.forEach(element => {
        const tooltipKey = element.dataset.tooltip;
        const tooltipContent = this.tooltips[tooltipKey];
        
        // Set up event listeners for showing/hiding tooltips
        if (tooltipContent) {
            element.addEventListener('mouseenter', () => this._showTooltip(element, tooltipContent));
            element.addEventListener('mouseleave', () => this._hideTooltip());
            element.addEventListener('focus', () => this._showTooltip(element, tooltipContent));
            element.addEventListener('blur', () => this._hideTooltip());
        }
    });
}
```

### Tour Navigation

```javascript
_showTourStep(steps, index) {
    // Get the current step
    const step = steps[index];
    const element = document.querySelector(step.element);
    
    if (!element) {
        console.warn(`Element ${step.element} not found for tour step ${index}`);
        return;
    }
    
    // Create the tour popup
    const popup = document.createElement('div');
    popup.className = 'tour-popup';
    popup.innerHTML = `
        <div class="tour-popup-header">${step.title}</div>
        <div class="tour-popup-body">${step.content}</div>
        <div class="tour-popup-footer">
            <button class="btn btn-sm ${index === 0 ? 'btn-outline-secondary disabled' : 'btn-outline-primary'}" 
                    id="tour-prev" ${index === 0 ? 'disabled' : ''}>Previous</button>
            <span class="tour-counter">${index + 1}/${steps.length}</span>
            <button class="btn btn-sm btn-primary" id="tour-next">
                ${index === steps.length - 1 ? 'Finish' : 'Next'}
            </button>
        </div>
    `;
    
    // Position and navigate between steps
    // ...additional implementation details...
}
```

## CSS Styling

Tooltips and tour elements are styled using theme-aware CSS:

```css
.tooltip-wrapper {
    position: absolute;
    z-index: 1000;
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    border-radius: 0.25rem;
    padding: 0.75rem;
    box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.15);
    max-width: 300px;
    font-size: 0.875rem;
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.tour-highlight {
    position: relative;
}

.tour-highlight:after {
    content: '';
    position: absolute;
    top: -4px;
    left: -4px;
    right: -4px;
    bottom: -4px;
    border: 2px solid var(--accent-color);
    border-radius: 4px;
    pointer-events: none;
    animation: pulse 1.5s infinite;
}
```

## Extending the System

### Adding New Tooltips

To add a new tooltip:

1. Add a `data-tooltip` attribute to the HTML element:
   ```html
   <button data-tooltip="my-new-tooltip">Click Me</button>
   ```

2. Add the tooltip content to the `tooltips` object in `TooltipManager`:
   ```javascript
   this.tooltips = {
       // Existing tooltips...
       'my-new-tooltip': 'This is a helpful explanation of what this button does.'
   };
   ```

### Adding New Tour Steps

To add a new step to the guided tour:

1. Identify the page where the step should appear ('home' or 'dashboard')
2. Add a new step object to the appropriate array in `tourSteps`:
   ```javascript
   this.tourSteps = {
       'home': [
           // Existing steps...
           {
               element: '.my-new-element',
               title: 'New Feature',
               content: 'This feature helps you accomplish a specific task...',
               condition: () => document.querySelector('.my-new-element') !== null
           }
       ]
   };
   ```

### Creating Conditional Tour Steps

Steps can be conditionally shown based on the page state:

```javascript
{
    element: '.advanced-feature',
    title: 'Advanced Settings',
    content: 'These settings are for advanced users...',
    condition: () => userIsAdvanced() 
}
```

## Best Practices

1. Keep tooltip text concise and helpful
2. Use consistent language across all tooltips
3. Ensure tour steps follow a logical progression
4. Make sure highlighted elements are visible (scrolling if necessary)
5. Test tour functionality in both light and dark themes
6. Ensure accessibility for keyboard users and screen readers

## Accessibility Considerations

- All tooltip and tour elements use proper ARIA attributes
- Tour navigation supports keyboard controls
- Color contrast meets WCAG guidelines in both themes
- Tour can be exited at any point
- Non-modal tooltips don't interfere with keyboard navigation 