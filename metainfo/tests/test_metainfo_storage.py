import unittest
from metainfo_storage import MetainfoStorage

class TestMetainfoStorage(unittest.TestCase):
    def setUp(self):
        self.storage = MetainfoStorage('big-buck-bunny.torrent')

    def test_info_hash(self):
        self.assertIsNotNone(self.storage.get_info_hash())

    def test_piece_length(self):
        # Điều chỉnh giá trị mong đợi theo dữ liệu thực tế của file .torrent
        expected_piece_length = 262144  # Cập nhật theo giá trị thực
        self.assertEqual(self.storage.get_piece_length(), expected_piece_length)

    def test_total_size(self):
        self.assertGreater(self.storage.get_total_size(), 0)

if __name__ == '__main__':
    unittest.main()
