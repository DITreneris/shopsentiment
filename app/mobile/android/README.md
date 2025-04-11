# Shop Sentiment Android App

This directory contains the Android-specific code for the Shop Sentiment mobile application.

## Setup Requirements

- Android Studio Arctic Fox (2020.3.1) or newer
- Java Development Kit (JDK) 11
- Android SDK 21+ (Android 5.0 Lollipop or newer)
- Gradle 7.0.2 or newer
- Node.js and npm/yarn for React Native dependencies

## Project Structure

```
android/
├── app/                    # Main Android app module
│   ├── src/                # Source files
│   │   ├── main/           # Main source set
│   │   │   ├── java/       # Java code
│   │   │   ├── res/        # Android resources
│   │   │   └── AndroidManifest.xml
│   │   └── debug/          # Debug configuration
│   ├── build.gradle        # App module build script
│   └── proguard-rules.pro  # ProGuard rules
├── build.gradle            # Project build script
├── gradle/                 # Gradle wrapper directory
├── gradle.properties       # Gradle properties
├── gradlew                 # Gradle wrapper script (Unix)
└── gradlew.bat             # Gradle wrapper script (Windows)
```

## Setup Instructions

1. Make sure you have Android Studio installed with the Android SDK.

2. Set up the Android SDK:
   - Open Android Studio
   - Go to SDK Manager (Tools > SDK Manager)
   - Install Android SDK platforms (minimum SDK 21)
   - Install Android SDK tools

3. Clone the repository and navigate to the project directory.

4. Open the `android` directory in Android Studio.

5. Let Gradle sync and build the project.

6. Run the app by clicking the Run button or using:
   ```
   ./gradlew :app:installDebug
   ```

## Push Notifications Setup

1. Set up Firebase for the project:
   - Create a Firebase project in the Firebase Console
   - Add the Android app to your Firebase project
   - Download the `google-services.json` file and place it in the `app` directory
   - Add Firebase Cloud Messaging dependencies to your build.gradle files

2. Implement Firebase Cloud Messaging in the app for push notifications.

## Google Play Store Deployment

1. Generate a signed APK/AAB:
   - In Android Studio, choose Build > Generate Signed Bundle/APK
   - Follow the wizard to create or use an existing key store
   - Choose release build variant

2. Create a Google Play Console account if you don't have one.

3. Create a new application in the Google Play Console.

4. Upload the signed APK/AAB file.

5. Fill in store listing information, screenshots, and other required details.

6. Submit the app for review.

## Development Guidelines

- Follow Material Design guidelines for UI/UX.
- Support different screen sizes and orientations.
- Implement proper error handling and offline capabilities.
- Use Kotlin for new native modules.
- Consider backward compatibility with older Android versions.

## Troubleshooting

- **Build errors**: Try clean build with `./gradlew clean build`
- **Emulator issues**: Update Android Studio and emulator components
- **Gradle sync issues**: Check for dependency compatibility

## Resources

- [Android Developer Documentation](https://developer.android.com/docs)
- [React Native Android Setup Guide](https://reactnative.dev/docs/environment-setup)
- [Firebase Documentation](https://firebase.google.com/docs)
- [Material Design Guidelines](https://material.io/design) 