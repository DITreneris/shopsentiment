import http.server
import socketserver
import os

PORT = 5000

# Change directory to the frontend directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Create a handler to ensure index.html is served correctly
class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # If path is / or empty, serve index.html
        if self.path == '/' or self.path == '':
            self.path = '/index.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

# Set up the server
Handler = CustomHandler
httpd = socketserver.TCPServer(("", PORT), Handler)

print(f"Server running at http://localhost:{PORT}/")
print(f"You can also try: http://127.0.0.1:{PORT}/")
print("Press Ctrl+C to stop the server")

# Start the server
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped.")
    httpd.server_close() 