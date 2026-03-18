from http.server import BaseHTTPRequestHandler, HTTPServer
import threading


class SSRFRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Request received')
        self.server.trigger = True # SSRF 모듈과 소통할 trigger

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        if post_data.decode() == 'localhost close':
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Shutting down server')
            self.server.shutdown()
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'POST request received')
            self.server.trigger = True # SSRF 모듈과 소통할 trigger

class LOCAL:
    def __init__(self, host='localhost', port=8080):
        self.server = HTTPServer((host, port), SSRFRequestHandler)
        self.trigger = False

    def start_server(self):
        print(f"Starting local server at http://{self.server.server_address[0]}:{self.server.server_address[1]}")
        thread = threading.Thread(target=self.server.serve_forever)
        thread.daemon = True
        thread.start()

    def get_trigger(self):
        return self.trigger

    def reset_trigger(self):
        self.trigger = False

    def shutdown(self):
        self.server.server_close()
        print("Local Server Closed")
