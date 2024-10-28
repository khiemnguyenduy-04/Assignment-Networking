class Bitfield:
    def __init__(self, byte_array):
        """Khởi tạo một Bitfield từ một danh sách byte."""
        self.bitfield = byte_array

    def has_piece(self, index):
        """Kiểm tra xem một bitfield có chỉ số cụ thể đã được thiết lập hay không."""
        byte_index = index // 8
        offset = index % 8
        
        # Kiểm tra xem chỉ số byte có hợp lệ hay không
        if byte_index < 0 or byte_index >= len(self.bitfield):
            return False
        
        return (self.bitfield[byte_index] >> (7 - offset)) & 1 != 0

    def set_piece(self, index):
        """Thiết lập một bit trong bitfield."""
        byte_index = index // 8
        offset = index % 8
        
        # Bỏ qua chỉ số không hợp lệ
        if byte_index < 0 or byte_index >= len(self.bitfield):
            return
        
        self.bitfield[byte_index] |= 1 << (7 - offset)