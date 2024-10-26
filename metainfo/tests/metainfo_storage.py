import hashlib
import bencodepy

class MetainfoStorage:
    def __init__(self, torrent_file):
        self.torrent_file = torrent_file
        self.meta_info = self.load_metainfo()

    def load_metainfo(self):
        """Phân tích file .torrent và lưu trữ thông tin về tệp."""
        with open(self.torrent_file, 'rb') as f:
            return bencodepy.decode(f.read())

    def get_info_hash(self):
        """Trả về info_hash của tệp từ file .torrent."""
        info = bencodepy.encode(self.meta_info[b'info'])
        return hashlib.sha1(info).hexdigest()

    def get_piece_length(self):
        """Trả về kích thước mỗi mảnh tệp."""
        return self.meta_info[b'info'].get(b'piece length', None)

    def get_total_size(self):
        """Trả về tổng kích thước tệp."""
        files = self.meta_info[b'info'].get(b'files', None)
        if files:
            return sum(f[b'length'] for f in files)
        return self.meta_info[b'info'].get(b'length', 0)
