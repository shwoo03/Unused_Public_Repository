import socket


class LOCAL:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.HOST = '127.0.0.1'
        self.PORT = 8080
        self.trigger = False
        self.running = True

    def open_local(self):
        self.server_socket.bind((self.HOST, self.PORT))
        self.server_socket.listen(500)

        print(f"LOCALHOST OPEN {self.HOST}:{self.PORT}")

        while self.running:
            try:
                self.server_socket.settimeout(1.0)  # 1초 타임아웃 설정
                try:
                    client_socket, client_address = self.server_socket.accept()
                except socket.timeout:
                    continue  # 타임아웃 발생 시 루프 재개

                print(f"연결됨: {client_address}")
                request_data = client_socket.recv(1024)
                print(f"요청 데이터: {request_data.decode('utf-8')}")

                # 요청이 들어왔을 때 trigger를 True로 설정
                self.trigger = True

                # HTTP 응답 생성
                http_response = b"""\
                                HTTP/1.1 200 OK
                                
                                Hello, World!
                                """
                # 클라이언트로 응답 전송
                client_socket.sendall(http_response)
                client_socket.close()

            except Exception as e:
                print(f"LOCAL HOST CLOSE")
                self.running = False

    def get_trigger(self):
        # trigger 값을 반환하고 다시 False로 초기화
        current_trigger = self.trigger
        self.trigger = False
        return current_trigger

    def stop_server(self):
        self.running = False
        self.server_socket.close()
