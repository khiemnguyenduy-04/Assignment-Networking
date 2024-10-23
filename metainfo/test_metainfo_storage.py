import unittest
from file_manager import FileManager

class TestFileManager(unittest.TestCase):
    def setUp(self):
        self.manager = FileManager('file.txt', 262144, 1048576)

    def test_write_read_piece(self):
        data = b'some binary data'
        self.manager.write_piece(0, data)
        self.assertEqual(self.manager.read_piece(0), data)

    def test_verify_piece(self):
        data = b'some binary data'
        self.manager.write_piece(0, data)
        expected_hash = self.manager.calculate_hash(data)  # Giả định rằng bạn có phương thức này
        self.assertTrue(self.manager.verify_piece(0, expected_hash))

if __name__ == '__main__':
    unittest.main()
