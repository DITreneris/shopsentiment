# Shop Sentiment iOS App

This directory contains the iOS-specific code for the Shop Sentiment mobile application.

## Setup Requirements

- macOS operating system
- Xcode 13 or later
- iOS 13.0+ deployment target
- CocoaPods 1.11 or later
- Node.js and npm/yarn for React Native dependencies

## Project Structure

```
ios/
├── assets/             # iOS-specific assets
├── ShopSentiment/      # Main iOS app code
│   ├── AppDelegate.h
│   ├── AppDelegate.m
│   ├── LaunchScreen.storyboard
│   ├── Images.xcassets
│   └── Info.plist
├── ShopSentimentTests/ # iOS app tests
├── Podfile             # CocoaPods dependency file
└── ShopSentiment.xcworkspace  # Xcode workspace
```

## Setup Instructions

1. Install CocoaPods if not already installed:
   ```
   sudo gem install cocoapods
   ```

2. Navigate to the `ios` directory and install dependencies:
   ```
   cd ios
   pod install
   ```

3. Open the `.xcworkspace` file in Xcode:
   ```
   open ShopSentiment.xcworkspace
   ```

4. Build and run the project in Xcode by selecting a simulator or device and clicking the Run button.

## Push Notifications Setup

1. Create an Apple Developer account if you don't have one.
2. Register your App ID in the Apple Developer Portal.
3. Create a push notification certificate for your App ID.
4. Download and convert the certificate to a .p12 file for the backend.
5. Enable push notification capability in Xcode.

## App Store Deployment

1. Create an app record in App Store Connect.
2. Configure app metadata, screenshots, and preview information.
3. Upload a build using Xcode or Transporter.
4. Submit for App Review when ready.

## Development Guidelines

- Follow Apple's Human Interface Guidelines.
- Ensure the app works well on all iPhone models and iPad if supported.
- Test thoroughly on physical devices before releases.
- Implement proper error handling for network requests.
- Use Swift for new native modules.

## Troubleshooting

- **Build errors**: Run `pod install` again and clean the project in Xcode.
- **Simulator issues**: Reset content and settings in the simulator.
- **Code signing problems**: Verify your development team and certificates in Xcode.

## Resources

- [Apple Developer Documentation](https://developer.apple.com/documentation/)
- [React Native iOS Setup Guide](https://reactnative.dev/docs/environment-setup)
- [CocoaPods Guide](https://guides.cocoapods.org/) 