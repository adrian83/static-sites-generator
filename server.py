import http.server
import os
import socketserver
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / 'public'
PORT = 8000

if __name__ == '__main__':
    handler = http.server.SimpleHTTPRequestHandler
    
    try:
        PUBLIC_DIR.mkdir(parents=True, exist_ok=True)
        os.chdir(PUBLIC_DIR)
    except Exception:
        pass
    
    with socketserver.TCPServer(('0.0.0.0', PORT), handler) as httpd:
        print(f'Serving static files from {PUBLIC_DIR} at http://0.0.0.0:{PORT}')
        print('Press Ctrl+C to stop.')
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print('\nServer stopped.')
