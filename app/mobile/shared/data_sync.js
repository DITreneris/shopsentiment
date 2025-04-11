/**
 * Shop Sentiment Mobile App Data Sync Service
 * Handles offline-first data synchronization between mobile app and backend
 */

import NetInfo from '@react-native-community/netinfo';
import { AsyncStorage } from 'react-native';
import apiClient from './api_client';

class DataSyncService {
  constructor() {
    this.isInitialized = false;
    this.isOnline = true;
    this.pendingActions = [];
    this.syncInProgress = false;
    this.syncListeners = [];
    this.netInfoUnsubscribe = null;
  }

  /**
   * Initialize the data sync service
   * @returns {Promise}
   */
  async initialize() {
    if (this.isInitialized) {
      return;
    }

    // Load pending actions from storage
    await this.loadPendingActions();

    // Subscribe to network state changes
    this.netInfoUnsubscribe = NetInfo.addEventListener(this.handleNetworkChange.bind(this));

    // Check initial network state
    const networkState = await NetInfo.fetch();
    this.isOnline = networkState.isConnected && networkState.isInternetReachable;

    // Try to sync if we're online
    if (this.isOnline) {
      this.scheduleSyncAttempt();
    }

    this.isInitialized = true;
  }

  /**
   * Handle network state changes
   * @param {Object} state - NetInfo state
   */
  handleNetworkChange(state) {
    const wasOnline = this.isOnline;
    this.isOnline = state.isConnected && state.isInternetReachable;

    // If we just came online, try to sync
    if (!wasOnline && this.isOnline) {
      this.scheduleSyncAttempt();
    }

    // Notify listeners about network state change
    this.notifyListeners({ type: 'networkChange', isOnline: this.isOnline });
  }

  /**
   * Schedule a sync attempt
   * Debounces sync attempts to avoid multiple syncs at once
   */
  scheduleSyncAttempt() {
    if (this.syncTimer) {
      clearTimeout(this.syncTimer);
    }

    this.syncTimer = setTimeout(() => {
      this.syncPendingActions();
    }, 1000); // Wait 1 second before syncing
  }

  /**
   * Add a pending action to be synchronized later
   * @param {Object} action - Action to be performed when online
   * @returns {Promise<string>} Action ID
   */
  async addPendingAction(action) {
    if (!action.type || !action.data) {
      throw new Error('Invalid action format');
    }

    const actionId = Date.now().toString() + Math.floor(Math.random() * 1000).toString();
    const pendingAction = {
      id: actionId,
      type: action.type,
      data: action.data,
      timestamp: Date.now(),
      attempts: 0,
    };

    this.pendingActions.push(pendingAction);
    await this.savePendingActions();

    // Try to sync immediately if online
    if (this.isOnline) {
      this.scheduleSyncAttempt();
    }

    this.notifyListeners({ type: 'actionAdded', action: pendingAction });
    return actionId;
  }

  /**
   * Sync all pending actions with the server
   * @returns {Promise<Object>} Sync result
   */
  async syncPendingActions() {
    if (this.syncInProgress || !this.isOnline || this.pendingActions.length === 0) {
      return { synced: 0, failed: 0, pending: this.pendingActions.length };
    }

    this.syncInProgress = true;
    this.notifyListeners({ type: 'syncStarted' });

    let synced = 0;
    let failed = 0;

    // Process each pending action
    const actionsToProcess = [...this.pendingActions];
    const successfulActions = [];

    for (const action of actionsToProcess) {
      try {
        // Increment attempt counter
        action.attempts += 1;

        switch (action.type) {
          case 'saveRecommendation':
            await apiClient.client.post('/save-recommendation', action.data);
            successfulActions.push(action.id);
            synced += 1;
            break;

          case 'updatePreferences':
            await apiClient.client.post('/update-preferences', action.data);
            successfulActions.push(action.id);
            synced += 1;
            break;

          case 'trackProduct':
            await apiClient.client.post('/track-product', action.data);
            successfulActions.push(action.id);
            synced += 1;
            break;

          default:
            console.warn(`Unknown action type: ${action.type}`);
            // Remove unknown action types
            successfulActions.push(action.id);
            break;
        }
      } catch (error) {
        console.error(`Failed to sync action ${action.id}:`, error);
        failed += 1;

        // If we've tried too many times, mark for removal
        if (action.attempts >= 5) {
          successfulActions.push(action.id);
          this.notifyListeners({
            type: 'actionFailed',
            action,
            error: 'Too many failed attempts',
          });
        }
      }
    }

    // Remove synced actions
    this.pendingActions = this.pendingActions.filter(
      action => !successfulActions.includes(action.id)
    );
    await this.savePendingActions();

    this.syncInProgress = false;
    this.notifyListeners({
      type: 'syncCompleted',
      synced,
      failed,
      pending: this.pendingActions.length,
    });

    return { synced, failed, pending: this.pendingActions.length };
  }

  /**
   * Load pending actions from AsyncStorage
   * @returns {Promise}
   */
  async loadPendingActions() {
    try {
      const actionsString = await AsyncStorage.getItem('pending_actions');
      if (actionsString) {
        this.pendingActions = JSON.parse(actionsString);
      } else {
        this.pendingActions = [];
      }
    } catch (error) {
      console.error('Error loading pending actions:', error);
      this.pendingActions = [];
    }
  }

  /**
   * Save pending actions to AsyncStorage
   * @returns {Promise}
   */
  async savePendingActions() {
    try {
      await AsyncStorage.setItem('pending_actions', JSON.stringify(this.pendingActions));
    } catch (error) {
      console.error('Error saving pending actions:', error);
    }
  }

  /**
   * Register a listener for sync events
   * @param {Function} listener - Function to call on sync events
   * @returns {Function} Function to call to unregister the listener
   */
  addSyncListener(listener) {
    this.syncListeners.push(listener);

    // Return function to remove listener
    return () => {
      this.syncListeners = this.syncListeners.filter(l => l !== listener);
    };
  }

  /**
   * Notify all listeners about an event
   * @param {Object} event - Event object
   */
  notifyListeners(event) {
    this.syncListeners.forEach(listener => {
      try {
        listener(event);
      } catch (error) {
        console.error('Error in sync listener:', error);
      }
    });
  }

  /**
   * Clean up resources
   */
  cleanup() {
    if (this.netInfoUnsubscribe) {
      this.netInfoUnsubscribe();
    }

    if (this.syncTimer) {
      clearTimeout(this.syncTimer);
    }
  }

  /**
   * Get current connection status
   * @returns {boolean} Whether device is online
   */
  isConnected() {
    return this.isOnline;
  }

  /**
   * Get pending actions count
   * @returns {number} Number of pending actions
   */
  getPendingCount() {
    return this.pendingActions.length;
  }

  /**
   * Force a sync attempt regardless of network state
   * @returns {Promise<Object>} Sync result
   */
  async forceSyncNow() {
    // Check network first
    const networkState = await NetInfo.fetch();
    this.isOnline = networkState.isConnected && networkState.isInternetReachable;

    if (!this.isOnline) {
      return {
        success: false,
        error: 'No network connection',
        pending: this.pendingActions.length,
      };
    }

    return this.syncPendingActions();
  }
}

// Export as singleton
export default new DataSyncService(); 