import logging
import threading
import struct
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from p2p.message import Message, MessageID
from p2p.peer_communication import Communicator
from p2p.piece import Piece
from p2p.bitfield import Bitfield

# Số lượng tối đa các yêu cầu tải lên có thể xử lý đồng thời
MAX_UPLOAD_QUEUE = 5

class UploadingManager:
    def __init__(self, pieces, peer_id, info_hash, file_path):
        """
        Khởi tạo UploadingManager với các mảnh mà client sở hữu.
        :param pieces: Danh sách các mảnh mà client có.
        :param peer_id: Peer ID của client.
        :param info_hash: Info hash của torrent.
        :param file_path: Đường dẫn tới file gốc chứa dữ liệu.
        """
        self.pieces = {piece.index: piece for piece in pieces}  # Lưu trữ mảnh theo index để truy xuất nhanh
        self.peer_id = peer_id
        self.info_hash = info_hash
        self.file_path = file_path  # Đường dẫn tới file gốc chứa dữ liệu
        self.upload_queue = []
        self.peers = {}
        self.lock = threading.Lock()

    def add_peer(self, peer):
        """
        Thêm một peer vào danh sách và bắt đầu thread để xử lý tải lên cho peer này.
        :param peer: Đối tượng Peer muốn kết nối.
        """
        max_index = max(self.pieces.keys()) + 1
        bitfield_array = bytearray((max_index + 7) // 8)  # Create a bytearray to hold the bitfield
        bitfield = Bitfield(bitfield_array)

        for i in self.pieces.keys():
            bitfield.set_piece(i)
        communicator = Communicator(peer, self.peer_id, self.info_hash, bitfield.bitfield)
        communicator.send_unchoke()  # Unchoke để peer có thể gửi yêu cầu
        communicator.send_interested()  # Cho biết mình có dữ liệu

        self.peers[peer] = communicator
        threading.Thread(target=self.handle_peer_requests, args=(communicator,)).start()

    def handle_peer_requests(self, communicator):
        """
        Xử lý yêu cầu tải lên từ một peer cụ thể.
        """
        while True:
            try:
                message = communicator.read()  # Đọc thông điệp từ peer
                if message is None:
                    continue

                # Nếu nhận được yêu cầu tải lên
                if message.ID == MessageID.MsgRequest:
                    index, begin, length = struct.unpack('>III', message.payload)
                    logging.debug(f"Received request for piece {index} from {communicator.peer}")

                    # Gửi mảnh nếu client có mảnh được yêu cầu
                    with self.lock:
                        if index in self.pieces:
                            self.upload_piece(communicator, index, begin, length)
                        else:
                            logging.warning(f"Requested piece {index} not available for upload")

                elif message.ID == MessageID.MsgChoke:
                    logging.info(f"Peer {communicator.peer} has choked us")
                    break  # Dừng khi bị choked

                elif message.ID == MessageID.MsgUnchoke:
                    logging.info(f"Peer {communicator.peer} has unchoked us")

            except Exception as e:
                logging.error(f"Error handling peer request: {e}")
                break

    def upload_piece(self, communicator, index, begin, length):
        """
        Gửi mảnh dữ liệu cho peer khi có yêu cầu hợp lệ.
        :param communicator: Đối tượng Communicator để giao tiếp với peer.
        :param index: Index của mảnh.
        :param begin: Vị trí bắt đầu của block.
        :param length: Độ dài của block.
        """
        piece = self.pieces[index]
        if begin + length > piece.length:
            logging.error(f"Invalid request for piece {index} from {begin} to {begin + length}")
            return

        # Đọc dữ liệu từ file gốc
        with open(self.file_path, 'rb') as f:
            f.seek(piece.index * piece.length + begin)
            block = f.read(length)

        msg = Message.format_piece(index, begin, block)
        communicator.conn.send(msg.serialize())
        logging.debug(f"Uploaded block {begin}-{begin + length} of piece {index} to {communicator.peer}")

    def send_have(self, piece_index):
        """
        Gửi thông điệp Have tới tất cả các peers để thông báo rằng client đã có mảnh mới.
        :param piece_index: Index của mảnh mới mà client đã tải xuống.
        """
        for communicator in self.peers.values():
            communicator.send_have(piece_index)
            logging.info(f"Sent 'Have' for piece {piece_index} to peer {communicator.peer}")