#!/usr/bin/env python3
"""
Simple HTTP server for OpenAvatarChat frontend
"""

import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import mimetypes

class OpenAvatarChatHandler(SimpleHTTPRequestHandler):
    """Custom handler for serving the frontend with proper MIME types"""
    
    def __init__(self, *args, **kwargs):
        # Set the directory to serve files from
        super().__init__(*args, directory=Path(__file__).parent, **kwargs)
    
    def end_headers(self):
        # Add CORS headers for API communication
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()
    
    def guess_type(self, path):
        # Ensure proper MIME types
        mimetype, encoding = mimetypes.guess_type(path)
        
        # Fix common issues
        if path.endswith('.js'):
            mimetype = 'application/javascript'
        elif path.endswith('.css'):
            mimetype = 'text/css'
        elif path.endswith('.html'):
            mimetype = 'text/html'
        
        return mimetype, encoding

def run_server(port=3000):
    """Run the frontend server"""
    
    # Change to frontend directory
    frontend_dir = Path(__file__).parent
    os.chdir(frontend_dir)
    
    print(f"🌐 Starting OpenAvatarChat Frontend Server")
    print(f"📁 Serving from: {frontend_dir}")
    print(f"🚀 Server running at: http://localhost:{port}")
    print(f"🔗 Open in browser: http://localhost:{port}")
    print(f"⏹️  Press Ctrl+C to stop")
    print()
    
    try:
        with HTTPServer(('', port), OpenAvatarChatHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        sys.exit(0)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {port} is already in use")
            print(f"💡 Try a different port: python serve.py --port 3001")
        else:
            print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='OpenAvatarChat Frontend Server')
    parser.add_argument('--port', type=int, default=3000, help='Port to serve on (default: 3000)')
    args = parser.parse_args()
    
    run_server(args.port)
