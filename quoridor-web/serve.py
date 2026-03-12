import http.server
import socketserver
import os

PORT = 8080

class Handler(http.server.SimpleHTTPRequestHandler):
    # Correctly register WASM mime type
    extensions_map = http.server.SimpleHTTPRequestHandler.extensions_map.copy()
    extensions_map['.wasm'] = 'application/wasm'

    def end_headers(self):
        # Enable CORS just in case
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

# Ensure we are serving from the directory where this script is located
os.chdir(os.path.dirname(os.path.abspath(__file__)))

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
