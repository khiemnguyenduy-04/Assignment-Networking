import socket
import threading
from urllib.parse import urlparse, parse_qs
from client_list import ClientList

class TrackerServer:
    def __init__(self, host='0.0.0.0', port=6881):
        self.host = host
        self.port = port
        self.client_list = ClientList()

    def start_tracker_server(self):
        """Khởi động Tracker Server, lắng nghe kết nối và xử lý yêu cầu từ client."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)
        print(f"Tracker Server started on {self.host}:{self.port}")

        while True:
            client_socket, addr = server_socket.accept()
            threading.Thread(target=self.handle_tracker_request, args=(client_socket, addr)).start()

    def handle_tracker_request(self, client_socket, addr):
        """Xử lý yêu cầu của client dựa trên query string và địa chỉ IP của client."""
        request = client_socket.recv(1024).decode('utf-8')
        query_string = urlparse(request.split(' ')[1]).query
        params = parse_qs(query_string)

        if 'announce' in request:
            self.handle_announce(params, addr[0])
        elif 'scrape' in request:
            info_hash = params.get('info_hash', [None])[0]
            peers = self.handle_scrape(info_hash)
            response = f"Peers: {peers}"
            client_socket.send(response.encode('utf-8'))
        elif 'discover' in request:
            self.discover()
        elif 'ping' in request:
            self.ping()

        client_socket.close()

    def handle_announce(self, params, client_ip):
        """Xử lý yêu cầu announce từ client và cập nhật thông tin peer."""
        info_hash = params['info_hash'][0]
        peer_id = params['peer_id'][0]
        port = params['port'][0]
        self.client_list.add_peer(info_hash, peer_id, client_ip, port)

    def handle_scrape(self, info_hash):
        """Trả về danh sách các peers có file có info_hash."""
        return self.client_list.get_peers(info_hash)

    def discover(self):
        """Tìm kiếm và cập nhật các client mới tham gia vào mạng P2P."""
        print("Discovering new clients...")

    def ping(self):
        """Kiểm tra tình trạng các client (online/offline)."""
        print("Pinging clients to check status...")
