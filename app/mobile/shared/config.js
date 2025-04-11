/**
 * Shop Sentiment Mobile App Configuration
 * Centralizes configuration for the mobile application
 */

import { Platform } from 'react-native';

// Environment-specific configuration
const ENV = {
  dev: {
    apiUrl: 'http://localhost:8000',
    logLevel: 'debug',
    refreshInterval: 60000, // 1 minute
    analyticsEnabled: false,
  },
  staging: {
    apiUrl: 'https://staging-api.shopsentiment.com',
    logLevel: 'info',
    refreshInterval: 300000, // 5 minutes
    analyticsEnabled: true,
  },
  prod: {
    apiUrl: 'https://api.shopsentiment.com',
    logLevel: 'warn',
    refreshInterval: 600000, // 10 minutes
    analyticsEnabled: true,
  },
};

// Current environment
const currentEnv = __DEV__ ? 'dev' : 'prod';

// Base configuration object
const config = {
  // API settings
  api: {
    baseUrl: ENV[currentEnv].apiUrl,
    timeout: 10000,
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
  },
  
  // App settings
  app: {
    version: '1.0.0',
    name: 'Shop Sentiment',
    team: {
      name: 'Shop Sentiment Team',
      email: 'support@shopsentiment.com',
    },
    theme: {
      primaryColor: '#2196F3',
      secondaryColor: '#FF9800',
      accentColor: '#4CAF50',
      backgroundColor: '#FFFFFF',
      textColor: '#212121',
      errorColor: '#F44336',
    },
  },
  
  // Feature flags
  features: {
    offlineMode: true,
    pushNotifications: true,
    darkMode: true,
    analytics: ENV[currentEnv].analyticsEnabled,
    feedback: true,
    crashReporting: currentEnv !== 'dev',
  },
  
  // Cache settings
  cache: {
    recommendationExpiry: 24 * 60 * 60 * 1000, // 24 hours
    productDataExpiry: 12 * 60 * 60 * 1000, // 12 hours
    maxCacheSize: 50 * 1024 * 1024, // 50 MB
  },
  
  // Sync settings
  sync: {
    autoSyncInterval: 15 * 60 * 1000, // 15 minutes
    maxRetries: 5,
    retryDelay: 60 * 1000, // 1 minute
  },
  
  // Notification settings
  notifications: {
    defaultIcon: Platform.OS === 'android' ? 'ic_notification' : undefined,
    channels: [
      {
        id: 'critical_alerts',
        name: 'Critical Alerts',
        description: 'Important alerts that require immediate attention',
        importance: 'high',
      },
      {
        id: 'recommendations',
        name: 'Recommendations',
        description: 'Notifications about new product recommendations',
        importance: 'default',
      },
      {
        id: 'price_alerts',
        name: 'Price Alerts',
        description: 'Alerts about price changes for tracked products',
        importance: 'high',
      },
    ],
  },
  
  // Analytics settings
  analytics: {
    sessionTimeout: 30 * 60 * 1000, // 30 minutes
    trackScreenViews: true,
    trackUserInteractions: true,
    trackErrors: true,
    samplingRate: currentEnv === 'prod' ? 0.1 : 1, // 10% in production, 100% otherwise
  },
  
  // Logging
  logging: {
    level: ENV[currentEnv].logLevel,
    remoteLogging: currentEnv !== 'dev',
    sensitiveKeys: ['password', 'token', 'auth', 'key', 'secret'],
  },
  
  // Refresh intervals
  refreshIntervals: {
    productList: ENV[currentEnv].refreshInterval,
    productDetails: ENV[currentEnv].refreshInterval,
    recommendations: ENV[currentEnv].refreshInterval,
  },
  
  // Device-specific configuration
  device: {
    ios: {
      minimumVersion: '13.0',
      recommendedVersion: '15.0',
      appStoreId: 'com.shopsentiment.app',
    },
    android: {
      minimumVersion: 21, // Android 5.0 (Lollipop)
      recommendedVersion: 29, // Android 10
      playStoreId: 'com.shopsentiment.app',
    },
  },
};

export default config; 