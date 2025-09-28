#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time
import sys

class MockHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/v1/query'):
            ts = int(time.time())
            payload = {
                'status': 'success',
                'data': {
                    'resultType': 'vector',
                    'result': [
                        {
                            'metric': {'instance': 'mock', 'gpu': '0'},
                            'value': [ts, '42.5']
                        }
                    ]
                }
            }
            body = json.dumps(payload).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        # reduce noise
        return

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    httpd = HTTPServer(('127.0.0.1', port), MockHandler)
    print(f"Mock Prometheus server listening on 127.0.0.1:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
