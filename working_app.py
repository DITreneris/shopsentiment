"""
Simple Flask app with cache monitoring.
"""
from flask import Flask, Blueprint, render_template, redirect, request, flash
import logging
import os
import time
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'testing_key'
app.config['DEBUG'] = True

# Simple cache implementation
class SimpleCache:
    def __init__(self):
        self.cache = {}
        self.hits = 0
        self.misses = 0
        
    def get(self, key):
        if key in self.cache:
            self.hits += 1
            logger.info(f"Cache HIT for {key}")
            return self.cache[key]
        else:
            self.misses += 1
            logger.info(f"Cache MISS for {key}")
            return None
    
    def set(self, key, value):
        self.cache[key] = value
        return True
    
    def stats(self):
        total = self.hits + self.misses
        hit_ratio = self.hits / total if total > 0 else 0
        return {
            'hits': self.hits,
            'misses': self.misses,
            'total': total,
            'hit_ratio': hit_ratio
        }
    
    def reset_stats(self):
        self.hits = 0
        self.misses = 0

# Create a global cache instance
cache = SimpleCache()

# Create a blueprint for the cache monitoring
monitor_bp = Blueprint('monitor', __name__, url_prefix='/monitor')

@app.route('/')
def index():
    """Home page with diagnostics"""
    # Get a list of all routes
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            routes.append(rule.rule)
    
    # Cache some test data
    for i in range(5):
        key = f"test_key_{i}"
        if i % 2 == 0:  # Force some cache hits and misses
            cache.get(key)
        if i % 3 == 0:  # Set some values
            cache.set(key, f"value_{i}")
            
    cache_stats = cache.stats()
    
    return f"""
    <html>
        <head>
            <title>Cache Monitor Demo</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                h1 {{ color: #4285f4; }}
                .card {{ border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin-bottom: 15px; }}
                .stat {{ display: inline-block; margin-right: 20px; font-size: 1.2em; }}
                .value {{ font-weight: bold; color: #4285f4; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Cache Monitoring Demo</h1>
                
                <div class="card">
                    <h2>Cache Statistics</h2>
                    <div class="stat">Hits: <span class="value">{cache_stats['hits']}</span></div>
                    <div class="stat">Misses: <span class="value">{cache_stats['misses']}</span></div>
                    <div class="stat">Total: <span class="value">{cache_stats['total']}</span></div>
                    <div class="stat">Hit Ratio: <span class="value">{cache_stats['hit_ratio']:.1%}</span></div>
                </div>
                
                <div class="card">
                    <h2>Available Routes</h2>
                    <ul>
                        {''.join([f'<li><a href="{route}">{route}</a></li>' for route in sorted(routes)])}
                    </ul>
                </div>
                
                <div class="card">
                    <h2>Cache Contents</h2>
                    <ul>
                        {''.join([f'<li>{k}: {v}</li>' for k, v in cache.cache.items()])}
                    </ul>
                </div>
                
                <div class="card">
                    <a href="/monitor/stats" class="button">View Detailed Stats</a>
                    <form method="POST" action="/monitor/reset" style="display: inline-block; margin-left: 10px;">
                        <button type="submit">Reset Stats</button>
                    </form>
                </div>
                
                <p>Server time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </body>
    </html>
    """

@monitor_bp.route('/stats')
def stats():
    """Detailed cache statistics page"""
    cache_stats = cache.stats()
    
    return f"""
    <html>
        <head>
            <title>Cache Monitoring Stats</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                h1 {{ color: #4285f4; }}
                .card {{ border: 1px solid #ddd; border-radius: 4px; padding: 15px; margin-bottom: 15px; }}
                .stat {{ font-size: 1.2em; margin-bottom: 10px; }}
                .value {{ font-weight: bold; color: #4285f4; }}
                .progress {{ width: 100%; background-color: #f3f3f3; border-radius: 5px; margin-bottom: 10px; }}
                .progress-bar {{ height: 20px; border-radius: 5px; }}
                .hit-ratio {{ background-color: #4CAF50; }}
                .miss-ratio {{ background-color: #F44336; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Cache Monitoring Statistics</h1>
                
                <div class="card">
                    <h2>Overview</h2>
                    <div class="stat">Total Operations: <span class="value">{cache_stats['total']}</span></div>
                    <div class="stat">Cache Hits: <span class="value">{cache_stats['hits']}</span></div>
                    <div class="stat">Cache Misses: <span class="value">{cache_stats['misses']}</span></div>
                </div>
                
                <div class="card">
                    <h2>Hit Ratio: <span class="value">{cache_stats['hit_ratio']:.1%}</span></h2>
                    <div class="progress">
                        <div class="progress-bar hit-ratio" style="width: {cache_stats['hit_ratio'] * 100}%;"></div>
                    </div>
                    <div class="progress">
                        <div class="progress-bar miss-ratio" style="width: {(1 - cache_stats['hit_ratio']) * 100}%;"></div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>Cache Contents ({len(cache.cache)} items)</h2>
                    <ul>
                        {''.join([f'<li>{k}: {v}</li>' for k, v in cache.cache.items()])}
                    </ul>
                </div>
                
                <div>
                    <a href="/">&larr; Back to Home</a>
                    <form method="POST" action="/monitor/reset" style="display: inline-block; margin-left: 10px;">
                        <button type="submit">Reset Stats</button>
                    </form>
                </div>
            </div>
        </body>
    </html>
    """

@monitor_bp.route('/reset', methods=['POST'])
def reset():
    """Reset cache statistics"""
    cache.reset_stats()
    return redirect('/')

# Register the blueprint
app.register_blueprint(monitor_bp)

if __name__ == '__main__':
    logger.info("Starting Flask application with cache monitoring")
    app.run(debug=True, host='127.0.0.1', port=5000) 