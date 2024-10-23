#   parse file .torrent and store metadata in a dictionary
#   store metadata in a file
#   for tracker: info_hash
#   for peers: support download and upload states between peers

import bencodepy
import hashlib

class MetainfoStorage:
    def __init__(self):
        self.metainfo = {}
        self.info_hash = None

    def load_metainfo(self, torrent_file):
        """Phân tích file .torrent và lưu trữ thông tin về tệp."""
        with open(torrent_file, 'rb') as f:
            self.metainfo = bencodepy.decode(f.read())
        
        # Tính toán info_hash
        info = self.metainfo[b'info']
        self.info_hash = hashlib.sha1(bencodepy.encode(info)).hexdigest()

    def get_info_hash(self):
        """Trả về info_hash của tệp từ file .torrent."""
        return self.info_hash

    def get_piece_length(self):
        """Trả về kích thước mỗi mảnh tệp."""
        return self.metainfo[b'info'][b'piece length']

    def get_total_size(self):
        """Trả về tổng kích thước tệp."""
        total_size = 0
        info = self.metainfo[b'info']
        
        if b'length' in info:  # Tệp đơn
            total_size = info[b'length']
        elif b'files' in info:  # Tệp đa
            total_size = sum(file[b'length'] for file in info[b'files'])
        
        return total_size

print("done test file metainfo_storage.py")