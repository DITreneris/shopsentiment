/**
 * Shop Sentiment Mobile App Notification Manager
 * Handles push notifications for critical alerts and recommendation updates
 */

import { Platform } from 'react-native';
import PushNotification from 'react-native-push-notification';
import PushNotificationIOS from '@react-native-community/push-notification-ios';
import { AsyncStorage } from 'react-native';

class NotificationManager {
  constructor() {
    this.isInitialized = false;
    this.deviceToken = null;
    this.notificationListeners = [];
    
    // Notification channels for Android
    this.channels = [
      {
        id: 'critical_alerts',
        name: 'Critical Alerts',
        description: 'Important alerts that require immediate attention',
        importance: 5, // High importance
        vibration: true,
        sound: 'default',
      },
      {
        id: 'recommendations',
        name: 'Recommendations',
        description: 'Notifications about new product recommendations',
        importance: 3, // Default importance
        vibration: true,
        sound: 'default',
      },
      {
        id: 'price_alerts',
        name: 'Price Alerts',
        description: 'Alerts about price changes for tracked products',
        importance: 4, // Medium-high importance
        vibration: true,
        sound: 'default',
      },
    ];
  }
  
  /**
   * Initialize push notifications
   * @returns {Promise}
   */
  async initialize() {
    if (this.isInitialized) {
      return;
    }
    
    // Configure push notifications
    PushNotification.configure({
      // Called when a remote or local notification is opened or received
      onNotification: this.handleNotification.bind(this),
      
      // Called when token is generated
      onRegister: this.handleRegistration.bind(this),
      
      // Should the initial notification be popped automatically
      popInitialNotification: true,
      
      // Request permissions (required for iOS)
      requestPermissions: Platform.OS === 'ios',
      
      // IOS ONLY
      permissions: {
        alert: true,
        badge: true,
        sound: true,
      },
    });
    
    // Create notification channels for Android
    if (Platform.OS === 'android') {
      this.createChannels();
    }
    
    // Try to load previously stored device token
    try {
      const token = await AsyncStorage.getItem('push_token');
      if (token) {
        this.deviceToken = token;
      }
    } catch (error) {
      console.warn('Error loading saved push token:', error);
    }
    
    this.isInitialized = true;
  }
  
  /**
   * Create notification channels for Android
   */
  createChannels() {
    this.channels.forEach(channel => {
      PushNotification.createChannel(
        channel,
        (created) => console.log(`Channel ${channel.id} created: ${created}`)
      );
    });
  }
  
  /**
   * Handle registration of device for push notifications
   * @param {Object} tokenData - Contains the device token
   */
  async handleRegistration(tokenData) {
    // Save the device token
    this.deviceToken = tokenData.token;
    
    // Store token in AsyncStorage
    try {
      await AsyncStorage.setItem('push_token', tokenData.token);
    } catch (error) {
      console.error('Error saving push token:', error);
    }
    
    // TODO: Send token to backend for registration
    console.log('Push notification token:', tokenData.token);
  }
  
  /**
   * Handle incoming notifications
   * @param {Object} notification - The notification object
   */
  handleNotification(notification) {
    // Notify all listeners
    this.notificationListeners.forEach(listener => {
      try {
        listener(notification);
      } catch (error) {
        console.error('Error in notification listener:', error);
      }
    });
    
    // Required on iOS
    if (Platform.OS === 'ios') {
      notification.finish(PushNotificationIOS.FetchResult.NoData);
    }
  }
  
  /**
   * Register a listener for notifications
   * @param {Function} listener - Function to call when notification is received
   * @returns {Function} Function to call to unregister the listener
   */
  addNotificationListener(listener) {
    this.notificationListeners.push(listener);
    
    // Return function to remove listener
    return () => {
      this.notificationListeners = this.notificationListeners.filter(
        l => l !== listener
      );
    };
  }
  
  /**
   * Schedule a local notification
   * @param {Object} options - Notification options
   * @returns {string} Notification ID
   */
  scheduleNotification(options) {
    const notificationId = Math.floor(Math.random() * 1000000).toString();
    
    const defaultOptions = {
      id: notificationId,
      title: 'Shop Sentiment',
      message: options.message || 'Notification from Shop Sentiment',
      date: options.date || new Date(Date.now() + 5 * 1000), // 5 seconds from now
      channelId: options.channelId || 'recommendations',
      priority: 'high',
    };
    
    // Additional options for Android
    if (Platform.OS === 'android') {
      defaultOptions.smallIcon = 'ic_notification';
      defaultOptions.largeIcon = 'ic_launcher';
      defaultOptions.color = '#2196F3';
      defaultOptions.vibrate = true;
      defaultOptions.vibration = 300;
    }
    
    // Schedule the notification
    PushNotification.localNotificationSchedule({
      ...defaultOptions,
      ...options,
    });
    
    return notificationId;
  }
  
  /**
   * Send immediate local notification
   * @param {Object} options - Notification options
   * @returns {string} Notification ID
   */
  sendNotification(options) {
    const notificationId = Math.floor(Math.random() * 1000000).toString();
    
    const defaultOptions = {
      id: notificationId,
      title: 'Shop Sentiment',
      message: options.message || 'Notification from Shop Sentiment',
      channelId: options.channelId || 'recommendations',
      priority: 'high',
    };
    
    // Additional options for Android
    if (Platform.OS === 'android') {
      defaultOptions.smallIcon = 'ic_notification';
      defaultOptions.largeIcon = 'ic_launcher';
      defaultOptions.color = '#2196F3';
      defaultOptions.vibrate = true;
      defaultOptions.vibration = 300;
    }
    
    // Send the notification
    PushNotification.localNotification({
      ...defaultOptions,
      ...options,
    });
    
    return notificationId;
  }
  
  /**
   * Cancel a scheduled notification
   * @param {string} notificationId - ID of notification to cancel
   */
  cancelNotification(notificationId) {
    PushNotification.cancelLocalNotification(notificationId);
  }
  
  /**
   * Cancel all scheduled notifications
   */
  cancelAllNotifications() {
    PushNotification.cancelAllLocalNotifications();
  }
  
  /**
   * Set app badge number (iOS only)
   * @param {number} count - Badge count to display
   */
  setBadgeCount(count) {
    if (Platform.OS === 'ios') {
      PushNotification.setApplicationIconBadgeNumber(count);
    }
  }
  
  /**
   * Get the device token
   * @returns {string|null} Device token
   */
  getDeviceToken() {
    return this.deviceToken;
  }
  
  /**
   * Request permission to receive notifications (iOS only)
   * @returns {Promise<boolean>} Whether permission was granted
   */
  async requestPermission() {
    if (Platform.OS === 'ios') {
      const permission = await PushNotificationIOS.requestPermissions({
        alert: true,
        badge: true,
        sound: true,
      });
      
      return permission.alert && permission.badge && permission.sound;
    }
    
    return true; // Permission is implied on Android
  }
}

// Export as singleton
export default new NotificationManager(); 