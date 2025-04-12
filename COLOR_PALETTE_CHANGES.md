# Shop Sentiment Analysis Updated Color Palette

## Refined Color Palette

| Role | Color Name | HEX | Usage |
|------|------------|-----|-------|
| primary | Bright Blue | #3B82F6 | Primary CTAs like Search |
| primary_hover | Deep Blue | #2563EB | Primary button hover states |
| secondary | Soft Coral | #FB7185 | Secondary CTAs (Login, Add Product) |
| secondary_hover | Bright Coral | #F43F5E | Secondary button hover states |
| background | Neutral Canvas | #F9FAFB | Main background |
| hero_background | Clean Blue Tint | #DBEAFE | Hero section background |
| card_background | White | #FFFFFF | Card and panel backgrounds |
| text_primary | Dark Slate | #1F2937 | Main headings and body text |
| text_secondary | Muted Gray | #6B7280 | Secondary text and sublabels |
| sentiment_positive | Sky Blue | #60A5FA | Positive sentiment indicators |
| sentiment_neutral | Amber | #FBBF24 | Neutral sentiment indicators |
| sentiment_negative | Rose Red | #F43F5E | Negative sentiment indicators |

## Implementation Details

### CSS Variables

Updated the CSS variables to use more semantic naming that matches the specific purpose of each color:

```css
:root {
    --primary-color: #3B82F6;
    --primary-hover: #2563EB;
    --secondary-color: #FB7185;
    --secondary-hover: #F43F5E;
    --background-color: #F9FAFB;
    --hero-background: #DBEAFE;
    --card-background: #FFFFFF;
    --text-color: #1F2937;
    --text-light: #6B7280;
    --border-color: #E5E7EB;
    --sentiment-positive: #60A5FA;
    --sentiment-positive-light: #E0F2FE;
    --sentiment-neutral: #FBBF24;
    --sentiment-neutral-light: #FEF3C7;
    --sentiment-negative: #F43F5E;
    --sentiment-negative-light: #FEE2E2;
}
```

### Key UI Components Updated

1. **Hero Section**
   - Updated to use the Clean Blue Tint background
   - Bright Blue for headings and emphasis

2. **Button System**
   - Primary Buttons (Bright Blue): Used for main actions like Search
   - Secondary Buttons (Soft Coral): Used for special actions like Login and Add Product
   - Hover states use deeper variants of each color

3. **Sentiment Visualization**
   - Positive: Sky Blue (#60A5FA)
   - Neutral: Amber (#FBBF24)
   - Negative: Rose Red (#F43F5E)
   - Consistent color use across badges, charts, and review indicators

4. **Form Elements**
   - Focus states using Bright Blue highlight
   - Animation effects for input focus
   - Clean white backgrounds with gray text

5. **Notifications**
   - Success: Uses the positive sentiment colors
   - Error: Uses the negative sentiment colors
   - Warning: Uses the neutral sentiment colors
   - Info: Uses the primary blue colors

## Color Psychology Benefits

1. **Bright Blue Primary Color**
   - Conveys trustworthiness and reliability
   - Associated with clarity and communication
   - Provides visual stability for the interface

2. **Soft Coral Secondary Color**
   - Creates visual interest and draws attention
   - Adds warmth and approachability
   - Helps highlight key conversion actions

3. **Clean Backgrounds**
   - Neutral Canvas background maintains readability
   - Clean Blue Tint hero adds subtle color without overwhelming
   - White cards create visual separation and focus

4. **Sentiment Colors**
   - Intuitive color mapping (blue=positive, amber=neutral, red=negative)
   - Consistent use builds user understanding
   - Light variants provide context without overwhelming

## Accessibility Considerations

1. **Contrast Ratios**
   - Text colors maintain strong contrast with backgrounds
   - Interactive elements are clearly distinguishable

2. **Semantic Color Usage**
   - Colors consistently represent the same concepts throughout
   - Not relying solely on color to convey information (using icons as well)

3. **Focus States**
   - Clear visual indicators for keyboard navigation
   - Enhanced focus styles for better accessibility 