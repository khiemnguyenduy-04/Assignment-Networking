import unittest
from unittest.mock import MagicMock, patch
from tracker.tracker_server import TrackerServer


class TestTrackerServer(unittest.TestCase):

    def setUp(self):
        # Mock request, client_address, and server
        self.request = MagicMock()
        self.client_address = ('127.0.0.1', 6881)
        self.server = MagicMock()
        
        # Khởi tạo TrackerServer với các đối tượng đã mock
        self.tracker_server = TrackerServer(self.request, self.client_address, self.server)

    @patch('tracker.tracker_server.bencodepy.encode')
    def test_handle_announce_valid_request(self, mock_encode):
        # Giả lập tham số
        self.tracker_server.path = "/announce?info_hash=%E6%0D%DC%13%08s%A2%91%94.%9E%DC%B1%DC%E1%EE%F0%2A%DFv&peer_id=wjnirTCJdFzqtvFKinQL&port=6881&uploaded=0&downloaded=0&left=33&event=started"
        
        # Gọi phương thức do_GET
        self.tracker_server.do_GET()

        # Kiểm tra xem response có được gửi không
        self.tracker_server.send_response.assert_called_with(200)
        mock_encode.assert_called()  # Đảm bảo rằng bencodepy.encode đã được gọi

    @patch('tracker.tracker_server.bencodepy.encode')
    def test_handle_announce_invalid_info_hash(self, mock_encode):
        # Giả lập tham số với info_hash không hợp lệ
        self.tracker_server.path = "/announce?info_hash=invalid_info_hash&peer_id=wjnirTCJdFzqtvFKinQL&port=6881&uploaded=0&downloaded=0&left=33&event=started"
        
        # Gọi phương thức do_GET
        self.tracker_server.do_GET()

        # Kiểm tra xem response có phải là 400 không
        self.tracker_server.send_error.assert_called_with(400, "Invalid info_hash encoding")


if __name__ == '__main__':
    unittest.main()
