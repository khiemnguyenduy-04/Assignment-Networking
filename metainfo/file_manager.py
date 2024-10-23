import os
import hashlib

class FileManager:
    def __init__(self, total_pieces, piece_length, file_path):
        self.total_pieces = total_pieces
        self.piece_length = piece_length
        self.file_path = file_path

    def write_piece(self, piece_index, data):
        """Ghi mảnh tệp vào đúng vị trí trong tệp chính."""
        with open(self.file_path, 'r+b') as f:
            f.seek(piece_index * self.piece_length)
            f.write(data)

    def read_piece(self, piece_index):
        """Đọc mảnh tệp từ tệp chính để chia sẻ với peer khác."""
        with open(self.file_path, 'rb') as f:
            f.seek(piece_index * self.piece_length)
            return f.read(self.piece_length)

    def verify_piece(self, piece_index, expected_hash):
        """Kiểm tra tính toàn vẹn của mảnh tệp thông qua SHA-1 hash."""
        piece_data = self.read_piece(piece_index)
        piece_hash = hashlib.sha1(piece_data).hexdigest()
        return piece_hash == expected_hash
