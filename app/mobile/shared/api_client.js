/**
 * Shop Sentiment Mobile App API Client
 * This shared module handles all API interactions with the recommendation system
 */

import axios from 'axios';
import { AsyncStorage } from 'react-native';

// Configuration (can be overridden by environment)
const API_CONFIG = {
  BASE_URL: 'https://api.shopsentiment.com',
  TIMEOUT: 10000,
  CACHE_DURATION: 15 * 60 * 1000, // 15 minutes in milliseconds
};

class APIClient {
  constructor() {
    this.client = axios.create({
      baseURL: API_CONFIG.BASE_URL,
      timeout: API_CONFIG.TIMEOUT,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    });
    
    this.setupInterceptors();
  }
  
  /**
   * Set up request/response interceptors for auth tokens and error handling
   */
  setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      async (config) => {
        // Add auth token if available
        const token = await AsyncStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        // Handle 401 Unauthorized errors (expired token)
        if (error.response && error.response.status === 401) {
          await AsyncStorage.removeItem('auth_token');
          // Could dispatch an event to notify the app to show login
        }
        
        return Promise.reject(error);
      }
    );
  }
  
  /**
   * Get recommended products
   * @param {Object} productData - Product data to get recommendations for
   * @returns {Promise} Recommendation data
   */
  async getRecommendation(productData) {
    try {
      const cacheKey = `recommendation_${productData.product_id}`;
      
      // Try to get from cache first
      const cachedData = await this.getFromCache(cacheKey);
      if (cachedData) {
        return cachedData;
      }
      
      // Call the API
      const response = await this.client.post('/recommend', productData);
      
      // Cache the result
      await this.saveToCache(cacheKey, response.data);
      
      return response.data;
    } catch (error) {
      console.error('Error getting recommendation:', error);
      throw error;
    }
  }
  
  /**
   * Get batch recommendations
   * @param {Array} products - Array of product data to get recommendations for
   * @returns {Promise} Batch recommendation data
   */
  async getBatchRecommendations(products) {
    try {
      const response = await this.client.post('/batch-recommend', { products });
      return response.data;
    } catch (error) {
      console.error('Error getting batch recommendations:', error);
      throw error;
    }
  }
  
  /**
   * Get latest model training status
   * @returns {Promise} Training status data
   */
  async getTrainingStatus() {
    try {
      const response = await this.client.get('/status');
      return response.data;
    } catch (error) {
      console.error('Error getting training status:', error);
      throw error;
    }
  }
  
  /**
   * Get cached data if it's not expired
   * @param {string} key - Cache key
   * @returns {Promise} Cached data or null if not found/expired
   */
  async getFromCache(key) {
    try {
      const cachedItem = await AsyncStorage.getItem(key);
      
      if (!cachedItem) {
        return null;
      }
      
      const { data, timestamp } = JSON.parse(cachedItem);
      const now = new Date().getTime();
      
      // Check if cache has expired
      if (now - timestamp > API_CONFIG.CACHE_DURATION) {
        await AsyncStorage.removeItem(key);
        return null;
      }
      
      return data;
    } catch (error) {
      console.warn('Error reading from cache:', error);
      return null;
    }
  }
  
  /**
   * Save data to cache
   * @param {string} key - Cache key
   * @param {Object} data - Data to cache
   * @returns {Promise} 
   */
  async saveToCache(key, data) {
    try {
      const cacheItem = {
        data,
        timestamp: new Date().getTime(),
      };
      
      await AsyncStorage.setItem(key, JSON.stringify(cacheItem));
    } catch (error) {
      console.warn('Error saving to cache:', error);
    }
  }
  
  /**
   * Clear all cached data
   * @returns {Promise}
   */
  async clearCache() {
    try {
      const keys = await AsyncStorage.getAllKeys();
      const cacheKeys = keys.filter(key => 
        key.startsWith('recommendation_')
      );
      
      await AsyncStorage.multiRemove(cacheKeys);
    } catch (error) {
      console.error('Error clearing cache:', error);
      throw error;
    }
  }
}

// Export as singleton instance
export default new APIClient(); 