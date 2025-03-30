/**
 * ShopSentiment Cache Manager
 * 
 * Provides client-side caching for dashboard data to improve performance
 * and reduce server load.
 */

class CacheManager {
    constructor(expiryTime = 300000) { // Default 5 minutes
        this.cacheKey = 'shopSentimentCache';
        this.expiryTime = expiryTime; // milliseconds
    }

    /**
     * Store data in cache
     * @param {string} key - Unique identifier for the data
     * @param {any} data - Data to cache
     */
    set(key, data) {
        const cache = this.getCache();
        cache[key] = {
            timestamp: Date.now(),
            data: data
        };
        this.saveCache(cache);
    }

    /**
     * Retrieve data from cache
     * @param {string} key - Unique identifier for the data
     * @returns {any|null} - Cached data or null if not found/expired
     */
    get(key) {
        const cache = this.getCache();
        if (cache[key]) {
            // Check if cache is still valid
            if (Date.now() - cache[key].timestamp < this.expiryTime) {
                return cache[key].data;
            } else {
                // Expired, remove it
                delete cache[key];
                this.saveCache(cache);
            }
        }
        return null;
    }

    /**
     * Check if a key exists in cache and is valid
     * @param {string} key - Key to check
     * @returns {boolean} - Whether key exists in valid cache
     */
    has(key) {
        const cache = this.getCache();
        return cache[key] && (Date.now() - cache[key].timestamp < this.expiryTime);
    }

    /**
     * Remove an item from cache
     * @param {string} key - Key to remove
     */
    remove(key) {
        const cache = this.getCache();
        if (cache[key]) {
            delete cache[key];
            this.saveCache(cache);
        }
    }

    /**
     * Clear all cached data
     */
    clear() {
        localStorage.removeItem(this.cacheKey);
    }

    /**
     * Get the full cache object
     * @private
     * @returns {Object} - The cache object
     */
    getCache() {
        const cache = localStorage.getItem(this.cacheKey);
        return cache ? JSON.parse(cache) : {};
    }

    /**
     * Save the cache object to storage
     * @private
     * @param {Object} cache - The cache object
     */
    saveCache(cache) {
        localStorage.setItem(this.cacheKey, JSON.stringify(cache));
    }

    /**
     * Remove all expired items from cache
     * @returns {number} - Number of items removed
     */
    cleanup() {
        const cache = this.getCache();
        let removed = 0;
        const now = Date.now();
        
        Object.keys(cache).forEach(key => {
            if (now - cache[key].timestamp >= this.expiryTime) {
                delete cache[key];
                removed++;
            }
        });
        
        if (removed > 0) {
            this.saveCache(cache);
        }
        
        return removed;
    }
}

// Create a global cache instance
window.shopCache = new CacheManager();

// Run cache cleanup periodically
setInterval(() => {
    window.shopCache.cleanup();
}, 60000); // Check every minute 