import unittest
import hashlib 
from file_manager import FileManager

class TestFileManager(unittest.TestCase):
    def setUp(self):
        # Khởi tạo lại file mỗi lần test để tránh dư thừa dữ liệu
        # 1048576 bytes = 1 MB file size, 262144 bytes per piece
        self.manager = FileManager('file.txt', 262144, 1048576)
        with open('file.txt', 'wb') as f:
            f.truncate(1048576)

    def test_write_read_piece(self):
        data = b'some binary data'
        self.manager.write_piece(0, data)
        self.assertEqual(self.manager.read_piece(0), data)

    def test_verify_piece(self):
        data = b'some binary data'
        expected_hash = hashlib.sha1(data).hexdigest()
        self.manager.write_piece(0, data)  # Ghi dữ liệu
        self.assertTrue(self.manager.verify_piece(0, expected_hash))  # Kiểm tra hash

if __name__ == '__main__':
    unittest.main()
