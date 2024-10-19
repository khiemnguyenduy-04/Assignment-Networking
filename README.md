# Bài tập lớn mạng máy tính
## Nhóm 4 thành viên

-   Minh: client-branch
-   Nam: tracker-server-branch
-   Khiêm: peer-communication-branch
-   Lâm: metainfo-file-management-branch

### Cấu trúc BTL:
```bash
P2P-Torrent-Demo/
│
├── client/                                   # Nhánh `client-branch`
│   ├── __init__.py                           # Đánh dấu thư mục là package
│   ├── client_node.py                        # Xử lý client-side logic (announce, scrape, etc.)
│   ├── client_cli.py                         # Giao diện dòng lệnh cho client
│   └── tests/                                # Thư mục test cho nhánh client
│       └── test_client.py                    # Unit test cho client (mock Tracker)
│
├── tracker/                                  # Nhánh `tracker-server-branch`
│   ├── __init__.py                           # Đánh dấu thư mục là package
│   ├── tracker_server.py                     # Chạy Tracker Server để quản lý Peers
│   ├── client_list.py                        # Quản lý danh sách các peers
│   └── tests/                                # Thư mục test cho nhánh tracker
│       └── test_tracker.py                   # Unit test cho tracker (announce, scrape, etc.)
│
├── peer/                                     # Nhánh `peer-communication-branch`
│   ├── __init__.py                           # Đánh dấu thư mục là package
│   ├── peer_communication.py                 # Giao tiếp giữa các peers (handshake, interested, etc.)
│   ├── download_manager.py                   # Quản lý tải dữ liệu từ nhiều peer
│   └── tests/                                # Thư mục test cho nhánh peer
│       └── test_peer_communication.py        # Unit test cho giao tiếp giữa các peers
│
├── metainfo/                                 # Nhánh `metainfo-file-management-branch`
│   ├── __init__.py                           # Đánh dấu thư mục là package
│   ├── metainfo_storage.py                   # Xử lý phân tích file .torrent
│   ├── file_manager.py                       # Quản lý việc chia tệp thành mảnh và ghép tệp
│   └── tests/                                # Thư mục test cho nhánh metainfo
│       └── test_metainfo_storage.py          # Unit test cho metainfo (hash, piece length, etc.)
│
├── tests/                                    # Thư mục test tích hợp chung
│   ├── test_integration_client_tracker.py    # Test tích hợp client với tracker
│   ├── test_integration_client_peer.py       # Test tích hợp client với peer communication
│
├── README.md                                 # Tài liệu mô tả dự án
└── requirements.txt                          # Danh sách các thư viện phụ thuộc cần cài đặt
```

### Chi tiết các Thư mục và Files
__client/ - Nhánh client-branch -Minh__ 

-   client_node.py: Chứa logic chính của client như gửi yêu cầu announce, scrape, và quản lý giao tiếp với tracker.

    _Hàm cần hiện thực:_

    ```python
    def announce(info_hash, peer_id, port, event='started'):
        """Gửi yêu cầu announce tới tracker và cập nhật trạng thái của client."""

    ```

    ```python
    def scrape(info_hash):
        """Gửi yêu cầu scrape tới tracker để lấy danh sách các peers có tệp với info_hash."""
    ```

    **Bổ sung thêm các hàm: parse_magnet_link(magnet_link), magnet_handshake(s, digest), magnet_info(s, ext_id, metadata_size), magnet_download_piece(s, data, index), magnet_download(digest, data, peers_list, output_file)**  _xử lý magnet hết trong phần này_

-   client_cli.py: Cung cấp giao diện dòng lệnh (CLI) cho người dùng để chạy các lệnh announce, scrape, và các lệnh liên quan đến magnet link.

    _Hàm cần hiện thực:_
    ```python
    def main():
        """Giao diện dòng lệnh để thực hiện các lệnh như announce, scrape, và các lệnh liên quan đến magnet link."""

    ```

-   tests/test_client.py: Kiểm tra tính đúng đắn của các chức năng client bằng cách mock tracker. (giả lập phản hồi từ tracker)

    ```python
    import unittest
    from unittest.mock import patch
    from client_node import ClientNode

    class TestClientNode(unittest.TestCase):
        @patch('requests.get')
        def test_announce(self, mock_get):
            mock_get.return_value.status_code = 200
            mock_get.return_value.json = lambda: {"interval": 1800, "peers": []}
            
            client = ClientNode(tracker_url="http://localhost:6881/announce")
            peers = client.announce(info_hash=b'some_info_hash', peer_id=b'peer1', port=6882)
            self.assertEqual(peers, [])

        @patch('requests.get')
        def test_magnet_parse(self, mock_get):
            magnet_link = "magnet:?xt=urn:btih:abcdef1234567890&tr=http://tracker.example.com/announce"
            tracker, info_hash = client.parse_magnet_link(magnet_link)
            self.assertEqual(tracker, "http://tracker.example.com/announce")
            self.assertEqual(info_hash, "abcdef1234567890")

    if __name__ == '__main__':
        unittest.main()

    ```
            client = ClientNode(tracker_url="http://localhost:6881/announce")
            peers = client.announce(info_hash=b'some_info_hash', peer_id=b'peer1', port=6882)
            self.assertEqual(peers, [])

    if __name__ == '__main__':
        unittest.main()

    ```

__tracker/ - Nhánh tracker-server-branch -Nam__

-   tracker_server.py: Xử lý logic của Tracker Server. Quản lý thông tin về các peers và các tệp họ chia sẻ. Lắng nghe các yêu cầu announce, scrape. 

    _Hàm cần hiện thực (tối thiểu):_
    ```python
    def start_tracker_server():
    """Khởi động Tracker Server, lắng nghe kết nối và xử lý yêu cầu từ client."""

    ```
    ```python
    def handle_tracker_request(query_string, addr):
    """Xử lý yêu cầu của client dựa trên query string và địa chỉ IP của lient."""

    ```

    ```python
    def handle_announce(params, client_ip):
    """Xử lý yêu cầu announce từ client và cập nhật thông tin peer."""

    ```

    ```python
    def handle_scrape(info_hash):
        """Trả về danh sách các peers có file có info_hash."""

    ```
    

-   client_list.py: Quản lý danh sách các peers, thêm và xoá peer khi cần thiết. 

    _Hàm cần hiện thực:_
    ```python
    def add_peer(info_hash, peer_id, ip, port):
        """Thêm peer mới vào danh sách peers cho file info_hash."""

    ```

    ```python
    def remove_peer(info_hash, peer_id):
        """Xóa một peer khỏi danh sách khi họ dừng chia sẻ."""

    ```

    ```python
    def get_peers(info_hash):
        """Trả về danh sách các peers đang chia sẻ tệp với info_hash."""

    ```
-   tests/test_tracker.py: Unit test cho các hàm xử lý của Tracker Server (announce, scrape, etc.).

    ```python
    import unittest
    from tracker_server import handle_announce, client_list

    class TestTrackerServer(unittest.TestCase):
        def setUp(self):
            self.client_list = client_list

        def test_announce(self):
            params = {'info_hash': ['some_info_hash'], 'peer_id': ['peer1'], 'port': ['6882']}
            handle_announce(params, '127.0.0.1')
            peers = self.client_list.get_peers('some_info_hash')
            self.assertEqual(len(peers), 1)
            self.assertEqual(peers[0]['peer_id'], 'peer1')

    if __name__ == '__main__':
        unittest.main()

    ```

__peer/ - Nhánh peer-communication-branch - Khiêm__

-   peer_communication.py: Quản lý giao tiếp giữa các peers, xử lý handshake, interested, và trao đổi mảnh tệp.

    _Hàm cần hiện thực:_
    ```python
    def peer_handshake(peer_ip, peer_port, info_hash, peer_id):
        """Thực hiện handshake giữa các peers và trả về kết nối peer."""

    ```
    ```python
    def send_interested(peer_conn):
        """Gửi thông điệp interested tới peer."""

    ```
    ```python
    def request_piece(peer_conn, piece_index, begin, length):
        """Gửi yêu cầu tải mảnh tệp từ peer."""

    ```
    ```python
    def receive_piece(peer_conn):
        """Nhận mảnh tệp từ peer và trả về dữ liệu mảnh."""

    ```
    ```python
    def handle_incoming_connection(peer_conn, file_manager):
    """Xử lý yêu cầu từ peer khác muốn tải dữ liệu."""
    # Bước 1: Handshake
    handshake = peer_conn.recv(68)  # Nhận handshake từ peer
    if not validate_handshake(handshake):
        return
        .....
    ```
    ```python
    def send_unchoke(peer_conn):
        """Gửi thông điệp unchoke tới peer."""
    ```
    ```python
    def send_piece(peer_conn, piece_index, begin, piece_data):
        """Gửi mảnh tệp cho peer."""
    ```
-   download_manager.py: Quản lý việc tải mảnh tệp từ nhiều peer cùng lúc, sử dụng multithreading.
    ```python
    def download_from_peers(peers):
        """Tải các mảnh tệp từ nhiều peer đồng thời bằng cách sử dụng multithreading."""

    ```
    ```python
    def download_from_peer(peer_ip, peer_port, file_manager):
        """Kết nối đến peer và tải các mảnh tệp."""
    ```
-   tests/test_peer_communication.py: Unit test cho giao tiếp P2P, kiểm tra quá trình handshake và gửi nhận dữ liệu.

    ```python
    import unittest
    from peer_communication import peer_handshake, send_interested, receive_piece

    class TestPeerCommunication(unittest.TestCase):
        def test_handshake(self):
            conn = peer_handshake('127.0.0.1', 6882, b'some_info_hash', b'peer1')
            self.assertIsNotNone(conn)

        def test_receive_piece(self):
            conn = peer_handshake('127.0.0.1', 6882, b'some_info_hash', b'peer1')
            send_interested(conn)
            piece = receive_piece(conn)
            self.assertIsNotNone(piece)

    if __name__ == '__main__':
        unittest.main()

    ```

__metainfo/ - Nhánh metainfo-file-management-branch - Lâm__

-   metainfo_storage.py: Phân tích file .torrent, trích xuất các thông tin như info_hash, piece_length, và các hash của mảnh tệp.

    _Hàm cần hiện thực:_
    ```python
    def load_metainfo(torrent_file):
        """Phân tích file .torrent và lưu trữ thông tin về tệp."""

    ```
    ```python
    def get_info_hash():
        """Trả về info_hash của tệp từ file .torrent."""

    ```
    ```python
    def get_piece_length():
        """Trả về kích thước mỗi mảnh tệp."""

    ```
    ```python
    def get_total_size():
        """Trả về tổng kích thước tệp."""

    ```

-   file_manager.py: Quản lý việc chia tệp thành các mảnh, ghi và đọc các mảnh từ tệp, kiểm tra tính toàn vẹn của mảnh qua hash.

    _Hàm cần hiện thực:_
    ```python
    def write_piece(piece_index, data):
        """Ghi mảnh tệp vào đúng vị trí trong tệp chính."""

    ```
    ```python
    def read_piece(piece_index):
        """Đọc mảnh tệp từ tệp chính để chia sẻ với peer khác."""

    ```
    ```python
    def verify_piece(piece_index, expected_hash):
        """Kiểm tra tính toàn vẹn của mảnh tệp thông qua SHA-1 hash."""

    ```


-   tests/test_metainfo_storage.py: Unit test cho việc phân tích file .torrent và quản lý mảnh tệp.

    ```python
    import unittest
    from metainfo_storage import MetainfoStorage

    class TestMetainfoStorage(unittest.TestCase):
        def setUp(self):
            self.storage = MetainfoStorage('test.torrent')

        def test_info_hash(self):
            self.assertIsNotNone(self.storage.get_info_hash())

        def test_piece_length(self):
            self.assertEqual(self.storage.get_piece_length(), 262144)

    if __name__ == '__main__':
        unittest.main()

    ```
-   tests/test_file_manager:  Unit test Kiểm tra việc ghi mảnh tệp vào tệp chính và kiểm tra tính toàn vẹn của từng mảnh thông qua hash.
    ```python
    import unittest
    from file_manager import FileManager

    class TestFileManager(unittest.TestCase):
        def setUp(self):
            self.manager = FileManager('file.txt', 262144, 1048576)

        def test_write_read_piece(self):
            data = b'some binary data'
            self.manager.write_piece(0, data)
            self.assertEqual(self.manager.read_piece(0), data)

    if __name__ == '__main__':
        unittest.main()

    ```

__tests/ - Thư mục Test Tích Hợp Chung__

-   test_integration_client_tracker.py: Test tích hợp giữa client và tracker để kiểm tra toàn bộ luồng từ việc gửi yêu cầu announce, scrape và nhận danh sách peers.
-   test_integration_client_peer.py: Test tích hợp giữa client và peer communication, kiểm tra việc giao tiếp giữa các peers, tải mảnh tệp và chia sẻ mảnh tệp.


### Quy trình kiểm tra code
-   Kiểm tra code cho từng chức năng:
```bash
python -m unittest discover client/tests
python -m unittest discover tracker/tests
python -m unittest discover peer/tests
python -m unittest discover metainfo/tests
```
-   Test tích hợp
```bash
python -m unittest discover tests/
```


### Quy trình làm việc trên github:

**GỒM 5 NHÁNH:**
-   **main**: Nhánh chính, chứa phiên bản ổn định của dự án.

-   **develop**: Nhánh phát triển, nơi tích hợp các tính năng mới trước khi đưa vào nhánh chính.
-   **client-branch**: Nhánh dành riêng cho các chức năng liên quan đến client.

-   **tracker-server-branch**: Nhánh dành cho các chức năng liên quan đến tracker server.

-   **peer-communication-branch**: Nhánh dành cho giao tiếp giữa các peers.


-   **metainfo-file-management-branch**: Nhánh dành cho quản lý file .torrent và các chức năng liên quan.

Trước khi mỗi thành viên bắt đầu làm việc trên branch cá nhân, họ cần đảm bảo branch của mình đang được đồng bộ với **develop** để tránh xung đột.

__1__

 **Bước 1**: Chuyển sang nhánh **develop**:
  ```bash
  git checkout develop
  ```

  **Bước 2**: Kéo về bản cập nhật mới nhất từ **develop**:
  ```bash
  git pull origin develop
  ```

  **Bước 3**: Chuyển trở lại branch cá nhân:
  ```bash
  git checkout <branch-name>
  ```

  **Bước 4**: Rebase branch cá nhân với **develop**:
  ```bash
  git rebase develop
  ```

__2: Push code lên GitHub__

push vào branch của mình

__3:Pull Request__

Nhấp vào Compare & pull request, điền mô tả về các thay đổi, và yêu cầu review từ các thành viên khác

__4.Merge sau khi review__

Sau khi PR đã được review và thông qua, bạn hoặc người khác có thể merge PR vào develop branch.

### Lưu ý về Quản lý xung đột (Conflicts)
 __Trường hợp có xung đột__

Nếu quá trình rebase phát hiện ra xung đột, Git sẽ thông báo những file nào bị xung đột và yêu cầu bạn sửa xung đột đó.

Sửa xung đột bằng cách mở các file bị xung đột và chỉnh sửa thủ công:

```bash
<<<<<<< HEAD
# Code của develop
=======
# Code của bạn
>>>>>>> <branch-name>
```
Sau khi sửa xung đột, chạy lệnh để hoàn tất rebase:

```bash
git rebase --continue
```

### Quy trình Merge vào nhánh Main
Khi tất cả các thành viên đã hoàn thành công việc của mình và mọi **Pull Request** đã được merge vào **develop**, nhóm sẽ thực hiện test tích hợp đầy đủ trên **develop**.

Nếu mọi thứ hoạt động ổn định, quản lý dự án hoặc thành viên được phân công sẽ merge nhánh **develop** vào **main** để chính thức cập nhật phiên bản ổn định của dự án:

```bash
git checkout main
git merge develop
```


### Python version :3.12.0

Dùng `pip install -r requirements.txt` để tải thư viện cần thiết trong requirements.txt. Nếu lúc code cần them thư viện mới thì thêm rồi liệt kê ra trong requirements.txt
