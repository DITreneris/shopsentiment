# Shop Sentiment Mobile Application

This directory contains the Shop Sentiment mobile application for iOS and Android platforms. The application is built using React Native with platform-specific native components as needed.

## Project Structure

```
mobile/
├── shared/             # Shared code between platforms
│   ├── api_client.js   # API interaction layer
│   ├── components/     # Shared React components
│   ├── config.js       # App configuration
│   ├── data_sync.js    # Offline data synchronization
│   └── notification_manager.js  # Push notification handling
├── ios/                # iOS-specific code
│   └── README.md       # iOS setup instructions
├── android/            # Android-specific code
│   └── README.md       # Android setup instructions
├── package.json        # NPM dependencies
└── README.md           # This file
```

## Architecture Overview

The mobile application follows a cross-platform architecture with React Native, while allowing for platform-specific optimizations where needed.

### Key Components

1. **API Client**: Centralized communication with the backend recommendation system API, including caching and offline support.

2. **Notification Manager**: Handles push notifications for both platforms, including registration, displaying notifications, and handling user interactions.

3. **Data Sync Service**: Provides offline-first capabilities by queuing actions when offline and synchronizing when connectivity is restored.

4. **Shared Components**: Reusable UI components that maintain consistent look and feel across platforms while respecting platform-specific design guidelines.

5. **Platform-Specific Code**: Native modules and components for iOS and Android that handle platform-specific features and optimizations.

### Features

- **Real-time Recommendations**: View product recommendations powered by the sentiment analysis system
- **Push Notifications**: Receive alerts for critical events like price changes or trending products
- **Offline Support**: Use the app without internet connection and sync when back online
- **Mobile-Optimized Visualizations**: Interactive charts and graphs for product sentiment data
- **Multi-language Support**: Interface available in multiple languages

## Development Setup

### Prerequisites

- Node.js (v14 or newer)
- npm or yarn
- React Native CLI
- For iOS: macOS with Xcode 13+
- For Android: Android Studio with SDK tools

### Installation

1. Install dependencies:
   ```
   npm install
   ```
   or
   ```
   yarn install
   ```

2. For iOS specific setup:
   ```
   cd ios
   pod install
   ```

3. For Android specific setup, see the Android README.md file.

### Running the App

For iOS:
```
npm run ios
```

For Android:
```
npm run android
```

## Implementation Guidelines

- All API calls should go through the shared API client
- Use the shared notification manager for all push notification handling
- Follow platform-specific design guidelines while maintaining a consistent experience
- Implement proper error handling and offline capabilities
- Use TypeScript for type safety where possible
- Write unit tests for business logic

## Deployment

See platform-specific README files for detailed deployment instructions for iOS and Android app stores. 