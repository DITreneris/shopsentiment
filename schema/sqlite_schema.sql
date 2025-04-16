-- SQLite Schema for ShopSentiment Application
-- This file defines the database structure for the ShopSentiment application

-- Products table to store product information
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    price REAL,
    image_url TEXT,
    external_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Reviews table to store product reviews
CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    user_name TEXT,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    text TEXT,
    sentiment_score REAL,
    sentiment_label TEXT CHECK (sentiment_label IN ('positive', 'neutral', 'negative')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source TEXT DEFAULT 'manual',
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);

-- Categories table to store product categories
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    parent_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES categories (id) ON DELETE SET NULL
);

-- Product-Category relationship table
CREATE TABLE IF NOT EXISTS product_categories (
    product_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    PRIMARY KEY (product_id, category_id),
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE CASCADE
);

-- Users table to store application users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Analytics table to store aggregated sentiment data
CREATE TABLE IF NOT EXISTS sentiment_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    date DATE NOT NULL,
    average_sentiment REAL,
    review_count INTEGER DEFAULT 0,
    positive_count INTEGER DEFAULT 0,
    neutral_count INTEGER DEFAULT 0,
    negative_count INTEGER DEFAULT 0,
    UNIQUE(product_id, date),
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_reviews_product_id ON reviews (product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_sentiment_score ON reviews (sentiment_score);
CREATE INDEX IF NOT EXISTS idx_products_name ON products (name);
CREATE INDEX IF NOT EXISTS idx_products_category ON products (category);
CREATE INDEX IF NOT EXISTS idx_analytics_date ON sentiment_analytics (date);

-- Create trigger to update the updated_at timestamp when a product is modified
CREATE TRIGGER IF NOT EXISTS update_product_timestamp 
AFTER UPDATE ON products
BEGIN
    UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Create view for product sentiment summary
CREATE VIEW IF NOT EXISTS product_sentiment_summary AS
SELECT 
    p.id,
    p.name,
    p.category,
    COUNT(r.id) AS review_count,
    AVG(r.sentiment_score) AS average_sentiment,
    SUM(CASE WHEN r.sentiment_label = 'positive' THEN 1 ELSE 0 END) AS positive_reviews,
    SUM(CASE WHEN r.sentiment_label = 'neutral' THEN 1 ELSE 0 END) AS neutral_reviews,
    SUM(CASE WHEN r.sentiment_label = 'negative' THEN 1 ELSE 0 END) AS negative_reviews
FROM products p
LEFT JOIN reviews r ON p.id = r.product_id
GROUP BY p.id, p.name, p.category; 