from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'status': 'ok',
        'message': 'Simple test app is working'
    })

@app.route('/env')
def env_info():
    env_vars = {
        'FLASK_ENV': os.environ.get('FLASK_ENV', 'not set'),
        'USE_SQLITE': os.environ.get('USE_SQLITE', 'not set'),
        'SECRET_KEY': 'present' if os.environ.get('SECRET_KEY') else 'not set',
        'REDIS_URL': os.environ.get('REDIS_URL', 'not set'),
    }
    return jsonify(env_vars)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 