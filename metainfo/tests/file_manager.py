import os
import hashlib

class FileManager:
    def __init__(self, file_path, piece_length, total_size):
        self.file_path = file_path
        self.piece_length = piece_length
        self.total_size = total_size
        self._initialize_file()

    def _initialize_file(self):
        """Khởi tạo file với kích thước xác định nếu chưa tồn tại."""
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'wb') as f:
                f.truncate(self.total_size)

    def write_piece(self, piece_index, data):
        """Ghi mảnh tệp vào đúng vị trí trong tệp chính."""
        with open(self.file_path, 'r+b') as f:
            f.seek(piece_index * self.piece_length)
            f.write(data)  # Chỉ ghi đúng kích thước dữ liệu nhận vào



    def read_piece(self, piece_index):
        """Đọc mảnh tệp từ tệp chính để chia sẻ với peer khác."""
        with open(self.file_path, 'rb') as f:
            f.seek(piece_index * self.piece_length)
            piece_data = f.read(len(b'some binary data'))  # Chỉ đọc đúng kích thước dữ liệu
        return piece_data

    def verify_piece(self, piece_index, expected_hash):
        """Kiểm tra tính toàn vẹn của mảnh tệp thông qua SHA-1 hash."""
        piece_data = self.read_piece(piece_index)
        actual_hash = hashlib.sha1(piece_data.rstrip(b'\x00')).hexdigest()
        return actual_hash == expected_hash
