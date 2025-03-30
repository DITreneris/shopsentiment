/**
 * Client-side cache manager tests
 * 
 * This file contains tests for the cache-manager.js functionality.
 * Run these tests in a browser environment or with a JavaScript test runner.
 */

// Mock localStorage for testing
class LocalStorageMock {
    constructor() {
        this.store = {};
    }

    getItem(key) {
        return this.store[key] || null;
    }

    setItem(key, value) {
        this.store[key] = String(value);
    }

    removeItem(key) {
        delete this.store[key];
    }

    clear() {
        this.store = {};
    }
}

// Set up global localStorage mock
global.localStorage = new LocalStorageMock();

// Import or define the CacheManager class for testing
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

/**
 * Test runner
 */
function runTests() {
    console.log("Running client-side cache tests...");
    
    let testsPassed = 0;
    let testsFailed = 0;
    
    // Helper for assertions
    function assert(condition, message) {
        if (!condition) {
            console.error(`❌ Failed: ${message}`);
            testsFailed++;
            return false;
        } else {
            console.log(`✅ Passed: ${message}`);
            testsPassed++;
            return true;
        }
    }
    
    // Create a new cache instance for each test
    function setupTest() {
        localStorage.clear();
        return new CacheManager(1000); // 1 second timeout for faster testing
    }
    
    // Test: Setting and getting from cache
    function testSetGet() {
        const cache = setupTest();
        const testData = { name: "test", value: 123 };
        
        cache.set("testKey", testData);
        const retrieved = cache.get("testKey");
        
        assert(retrieved !== null, "Retrieved value should not be null");
        assert(retrieved.name === testData.name, "Retrieved object should have same properties");
        assert(retrieved.value === testData.value, "Retrieved object should have same values");
    }
    
    // Test: Cache expiration
    function testExpiration() {
        const cache = setupTest();
        cache.set("expiringKey", "test value");
        
        assert(cache.has("expiringKey"), "Key should exist after setting");
        
        // Mock date to simulate expiration
        const originalNow = Date.now;
        Date.now = () => originalNow() + 2000; // 2 seconds later (beyond our 1s timeout)
        
        assert(cache.get("expiringKey") === null, "Expired key should return null");
        assert(!cache.has("expiringKey"), "Expired key should not exist in cache");
        
        // Restore original Date.now
        Date.now = originalNow;
    }
    
    // Test: Cache has method
    function testHasMethod() {
        const cache = setupTest();
        
        assert(!cache.has("nonexistentKey"), "Non-existent key should return false");
        
        cache.set("existingKey", "test value");
        assert(cache.has("existingKey"), "Existing key should return true");
    }
    
    // Test: Cache removal
    function testRemoval() {
        const cache = setupTest();
        cache.set("keyToRemove", "test value");
        
        assert(cache.has("keyToRemove"), "Key should exist before removal");
        
        cache.remove("keyToRemove");
        assert(!cache.has("keyToRemove"), "Key should not exist after removal");
    }
    
    // Test: Cache cleanup
    function testCleanup() {
        const cache = setupTest();
        
        // Add some items
        cache.set("freshKey", "fresh value");
        cache.set("expiredKey1", "expired value 1");
        cache.set("expiredKey2", "expired value 2");
        
        // Force some items to be expired
        const cacheData = cache.getCache();
        const originalNow = Date.now;
        const now = originalNow();
        
        // Modify timestamps directly to simulate older entries
        cacheData["expiredKey1"].timestamp = now - 2000; // 2 seconds ago
        cacheData["expiredKey2"].timestamp = now - 1500; // 1.5 seconds ago
        cache.saveCache(cacheData);
        
        // Run cleanup
        const removed = cache.cleanup();
        
        assert(removed === 2, "Cleanup should remove 2 expired items");
        assert(cache.has("freshKey"), "Fresh key should still exist");
        assert(!cache.has("expiredKey1"), "Expired key 1 should be removed");
        assert(!cache.has("expiredKey2"), "Expired key 2 should be removed");
        
        // Restore original Date.now
        Date.now = originalNow;
    }
    
    // Test: Cache clear
    function testClear() {
        const cache = setupTest();
        
        // Add multiple items
        cache.set("key1", "value1");
        cache.set("key2", "value2");
        cache.set("key3", "value3");
        
        assert(cache.has("key1"), "Key1 should exist before clear");
        assert(cache.has("key2"), "Key2 should exist before clear");
        assert(cache.has("key3"), "Key3 should exist before clear");
        
        cache.clear();
        
        assert(!cache.has("key1"), "Key1 should not exist after clear");
        assert(!cache.has("key2"), "Key2 should not exist after clear");
        assert(!cache.has("key3"), "Key3 should not exist after clear");
    }
    
    // Run all tests
    testSetGet();
    testExpiration();
    testHasMethod();
    testRemoval();
    testCleanup();
    testClear();
    
    // Report results
    console.log(`\nTest Results: ${testsPassed} passed, ${testsFailed} failed`);
    return testsFailed === 0;
}

// Run tests if in a suitable environment
if (typeof window === 'undefined') {
    // Node.js or similar environment
    runTests();
} else {
    // Browser environment - run when DOM is ready
    window.addEventListener('DOMContentLoaded', function() {
        runTests();
    });
}

// Export for test runners
if (typeof module !== 'undefined') {
    module.exports = { CacheManager, runTests };
} 