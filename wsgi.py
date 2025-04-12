from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Hello World! This is a working Heroku Flask app."

if __name__ == "__main__":
    app.run() 