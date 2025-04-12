# Shop Sentiment Analysis Typography Guide

This document outlines the typography system used in the Shop Sentiment Analysis application. Consistent typography helps create visual hierarchy, improves readability, and enhances the overall user experience.

## Font Family

We use a system of modern, highly legible web-safe fonts:

```css
font-family: 'Inter', 'Poppins', 'Nunito', sans-serif;
```

**Primary:** Inter - A versatile sans-serif typeface designed for computer screens
**Fallbacks:** Poppins, Nunito, sans-serif

## Font Weights

| Element | Weight | Variable |
|---------|--------|----------|
| Main Titles (H1) | 700 (Bold) | `--font-weight-bold` |
| Section Headings (H2) | 700 (Bold) | `--font-weight-bold` |
| Card Titles (H3) | 600 (Semibold) | `--font-weight-semibold` |
| Buttons | 600 (Semibold) | `--font-weight-semibold` |
| Labels | 500 (Medium) | `--font-weight-medium` |
| Body Text | 400 (Regular) | `--font-weight-normal` |
| Metadata | 400 (Regular) | `--font-weight-normal` |

## Font Sizes

| Element | Size (rem) | Variable |
|---------|------------|----------|
| Main Title (H1) | 2.25rem | `--font-size-h1` |
| Section Headings (H2) | 1.25rem | `--font-size-h2` |
| Subtitles | 1.125rem | `--font-size-subtitle` |
| Body Text | 1rem | `--font-size-body` |
| Button Text | 0.95rem | `--font-size-button` |
| Metadata Text | 0.875rem | `--font-size-metadata` |

## Line Heights

| Element | Line Height | Variable |
|---------|-------------|----------|
| Headings | 1.25 | `--line-height-tight` |
| Body Text | 1.5 | `--line-height-normal` |
| Long-form Text | 1.6 | `--line-height-loose` |

## Letter Spacing

| Element | Letter Spacing | Variable |
|---------|---------------|----------|
| Headings | -0.25px | `--letter-spacing-heading` |
| Buttons | -0.1px | `--letter-spacing-button` |

## Text Colors

| Element | Color | HEX | Variable |
|---------|-------|-----|----------|
| Headings | Dark Slate | #1F2937 | `--text-color` |
| Body Text | Gray 700 | #374151 | `--text-body` |
| Secondary Text | Gray 500 | #6B7280 | `--text-light` |

## Usage Examples

### Headings

```css
h1 {
    font-size: var(--font-size-h1);
    font-weight: var(--font-weight-bold);
    letter-spacing: var(--letter-spacing-heading);
    line-height: var(--line-height-tight);
    color: var(--text-color);
}

h2 {
    font-size: var(--font-size-h2);
    font-weight: var(--font-weight-bold);
    letter-spacing: var(--letter-spacing-heading);
    line-height: var(--line-height-tight);
    color: var(--text-color);
}

h3 {
    font-size: var(--font-size-body);
    font-weight: var(--font-weight-semibold);
    line-height: var(--line-height-tight);
    color: var(--text-color);
}
```

### Body Text

```css
p {
    font-size: var(--font-size-body);
    font-weight: var(--font-weight-normal);
    line-height: var(--line-height-loose);
    color: var(--text-body);
}
```

### Buttons

```css
.btn {
    font-size: var(--font-size-button);
    font-weight: var(--font-weight-semibold);
    letter-spacing: var(--letter-spacing-button);
}
```

### Metadata

```css
.metadata {
    font-size: var(--font-size-metadata);
    font-weight: var(--font-weight-normal);
    color: var(--text-light);
}
```

## Typography Best Practices

1. **Maintain Hierarchy:** Use font weights and sizes to create clear visual hierarchy
2. **Consistent Line Heights:** Use appropriate line heights for different text types
3. **Limited Weights:** Stick to the defined font weights for consistency
4. **Responsive Scaling:** Ensure text remains readable across device sizes
5. **Color Contrast:** Maintain WCAG AA standard (4.5:1) for text readability

## Implementation

The typography system is implemented through CSS variables in the `:root` selector in the main stylesheet. This approach enables easy updates and ensures consistency across the application. 