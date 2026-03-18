import os
import socket
import sys
import logging
from http.server import HTTPServer
from socketserver import ThreadingMixIn
from concurrent.futures import ThreadPoolExecutor
from https_proxy_handler import ProxyRequestHandler

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.thread_pool = ThreadPoolExecutor(max_workers=50)  # 최대 50개의 스레드

    def process_request(self, request, client_address):
        # 스레드 풀을 사용하여 요청을 처리
        self.thread_pool.submit(self.process_request_thread, request, client_address)

    def handle_error(self, request, client_address):
        cls, e = sys.exc_info()[:2]
        if cls in (socket.error, ssl.SSLError):
            logger.warning(f"Socket or SSL error from {client_address}: {e}")
        else:
            logger.error(f"Unexpected error from {client_address}: {e}")
            return HTTPServer.handle_error(self, request, client_address)

def run_server():
    protocol = "HTTP/1.1"
    server_address = (os.getenv("PROXY_BIND", "0.0.0.0"), int(os.getenv("PROXY_PORT", 8888)))
    ProxyRequestHandler.protocol_version = protocol
    
    # 서버 초기화 (SSL/TLS 설정 없음)
    httpd = ThreadingHTTPServer(server_address, ProxyRequestHandler)
    
    sa = httpd.socket.getsockname()
    logger.info(f"Serving HTTP Proxy on {sa[0]}:{sa[1]} ...")
    httpd.serve_forever()

# 바로 서버 실행
run_server()
