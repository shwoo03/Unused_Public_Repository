import os
import ssl
from subprocess import Popen
import shutil
import glob

# TLS 프로토콜을 사용하여 안전한 통신을 할 수 있도록 하는 함수 
def create_ssl_context(certpath, keypath):
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER) # SSL 컨텍스트 생성
    context.load_cert_chain(certpath, keypath) # 인증서와 개인 키 로드 
    return context # SSL 컨텍스트 반환

def make_certs(args):
    # 인증서와 개인 키 생성
    Popen(["openssl", "genrsa", "-out", args.ca_key, "2048"]).communicate()
    Popen([
        "openssl", "req", "-new", "-x509", "-days", "3650", "-key", args.ca_key,
        "-sha256", "-out", args.ca_cert, "-subj", "/CN=Fuzzingzzingi CA"
    ]).communicate()
    Popen(["openssl", "genrsa", "-out", args.cert_key, "2048"]).communicate()
    os.makedirs(args.cert_dir, exist_ok=True)
    for old_cert in glob.glob(os.path.join(args.cert_dir, "*.pem")):
        os.remove(old_cert)

def make_example():
    example_file = os.path.join(os.path.dirname(__file__), "examples/example.py")
    shutil.copy(example_file, "proxy3_handlers_example.py")