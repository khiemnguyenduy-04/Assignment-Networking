import logging
import threading
import struct
import sys
import os
import hashlib
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from p2p.message import Message, MessageID
from p2p.peer_communication import Communicator
from p2p.piece import Piece
from p2p.bitfield import Bitfield

# Số lượng tối đa các yêu cầu tải lên có thể xử lý đồng thời
MAX_UPLOAD_QUEUE = 5

class UploadingManager:
    def __init__(self, pieces, peer_id, info_hash, file_path, total_length):
        """
        Khởi tạo UploadingManager với các mảnh mà client sở hữu.
        :param pieces: Danh sách các mảnh mà client có.
        :param peer_id: Peer ID của client.
        :param info_hash: Info hash của torrent.
        :param file_path: Đường dẫn tới file gốc chứa dữ liệu.
        :param total_length: Tổng chiều dài của file.
        """
        self.pieces = {piece.index: piece for piece in pieces}  # Lưu trữ mảnh theo index để truy xuất nhanh
        self.peer_id = peer_id
        self.info_hash = info_hash
        self.file_path = file_path  # Đường dẫn tới file gốc chứa dữ liệu
        self.total_length = total_length  # Tổng chiều dài của file
        self.upload_queue = []
        self.peers = {}
        self.lock = threading.Lock()
        self.piece_hashes = self.calculate_piece_hashes()

    def calculate_piece_hashes(self):
        """
        Tính toán hash của từng mảnh dữ liệu gốc và lưu trữ chúng.
        """
        piece_hashes = {}
        for piece in self.pieces.values():
            with open(self.file_path, 'rb') as f:
                f.seek(piece.index * piece.length)
                data = f.read(piece.length)
                piece_hash = hashlib.sha1(data).digest()
                piece_hashes[piece.index] = piece_hash
        return piece_hashes

    def add_peer(self, peer, client_socket):
        """
        Thêm một peer vào danh sách và bắt đầu thread để xử lý tải lên cho peer này.
        :param peer: Đối tượng Peer muốn kết nối.
        :param client_socket: Socket đã được chấp nhận từ peer.
        """
        max_index = max(self.pieces.keys()) + 1
        bitfield_array = bytearray((max_index + 7) // 8)  # Create a bytearray to hold the bitfield
        bitfield = Bitfield(bitfield_array)

        for i in self.pieces.keys():
            bitfield.set_piece(i)
        communicator = Communicator(peer, self.peer_id, self.info_hash, bitfield.bitfield, client_socket)
        communicator.send_unchoke()  # Unchoke để peer có thể gửi yêu cầu
        #communicator.send_interested()  # Cho biết mình có dữ liệu
        logging.info("check bitfield") 
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
                    index, begin, length = struct.unpack('>III', message.Payload)
                    logging.debug(f"Received request for piece {index} from {communicator.peer}")

                    # Gửi mảnh nếu client có mảnh được yêu cầu
                    with self.lock:
                        if index in self.pieces:
                            self.upload_piece(communicator, index, begin, length)
                            logging.debug(f"Uploaded piece {index} to {communicator.peer}")
                        else:
                            logging.warning(f"Requested piece {index} not available for upload")

                elif message.ID == MessageID.MsgChoke:
                    logging.info(f"Peer {communicator.peer} has choked us")
                    break  # Dừng khi bị choked

                elif message.ID == MessageID.MsgUnchoke:
                    logging.info(f"Peer {communicator.peer} has unchoked us")

                elif message.ID == MessageID.MsgHave:
                    piece_index = struct.unpack('>I', message.Payload)[0]
                    logging.info(f"Peer {communicator.peer} has piece {piece_index}")

                elif message.ID == MessageID.MsgNotInterested:
                    logging.info(f"Peer {communicator.peer} is not interested")
                    communicator.send_choke()  # Gửi lại thông điệp Unchoke
                    break
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
        # verify = self.verify_piece(index)
        # logging.debug(f"Piece {index} is verified: {verify}")

        # Kiểm tra xem yêu cầu có hợp lệ không
        # if not verify:
        #     logging.error(f"Piece {index} is not verified, cannot upload.")
        #     return

        if begin < 0 or begin + length > piece.length:
            logging.error(f"Invalid request for piece {index} from {begin} to {begin + length}")
            return

        # Đọc dữ liệu từ file gốc
        try:
            with open(self.file_path, 'rb') as f:
                # Tính toán offset cho mảnh
                offset = piece.index * piece.length

                # Nếu là mảnh cuối cùng, điều chỉnh offset
                if index == len(self.pieces) - 1:
                    offset = self.total_length - piece.length  # Đảm bảo không vượt quá tổng chiều dài

                f.seek(offset + begin)  # Đọc dữ liệu từ vị trí tính toán
                block = f.read(length)

            # Kiểm tra xem dữ liệu đọc được có hợp lệ không
            if len(block) != length:
                logging.error(f"Expected to read {length} bytes, but read {len(block)} bytes for piece {index}.")
                return

            msg = Message.format_piece(index, begin, block)
            communicator.conn.send(msg.serialize())
            logging.debug(f"Uploaded block {begin}-{begin + length} of piece {index} to {communicator.peer}")

        except FileNotFoundError:
            logging.error(f"File not found: {self.file_path}")
        except IOError as e:
            logging.error(f"I/O error occurred while reading piece {index}: {e}")
        except Exception as e:
            logging.error(f"Failed to read or send piece {index}: {e}")

    def send_have(self, piece_index):
        """
        Gửi thông điệp Have tới tất cả các peers để thông báo rằng client đã có mảnh mới.
        :param piece_index: Index của mảnh mới mà client đã tải xuống.
        """
        for communicator in self.peers.values():
            communicator.send_have(piece_index)
            logging.info(f"Sent 'Have' for piece {piece_index} to peer {communicator.peer}")

    # FOR TESTING
    # def verify_piece(self, index):
    #     """
    #     Kiểm tra tính toàn vẹn của một piece đã tải về.
    #     :param index: Index của piece cần kiểm tra.
    #     :return: True nếu piece hợp lệ, ngược lại là False.
    #     """
    #     piece = self.pieces.get(index)
    #     if not piece:
    #         logging.error(f"Không tìm thấy piece {index} để kiểm tra")
    #         return False

    #     # Đọc dữ liệu từ file gốc và tính hash của cả piece
    #     with open(self.file_path, 'rb') as f:
    #         f.seek(piece.index * piece.length)
    #         data = f.read(piece.length)
        
    #     calculated_hash = hashlib.sha1(data).digest()
    #     expected_hash = self.piece_hashes.get(index)

    #     if calculated_hash == expected_hash:
    #         logging.debug(f"Piece {index} đã xác nhận chính xác với hash {calculated_hash.hex()}")
    #         return True
    #     else:
    #         logging.error(f"Piece {index} không hợp lệ: hash tính được {calculated_hash.hex()} không khớp với mong đợi {expected_hash.hex()}")
    #         return False