import os
import sys
import time
import logging
import queue
import threading
import hashlib
from p2p.peer_communication import Communicator
from p2p.peer import Peer
from p2p.message import Message, MessageID
from p2p.piece import Piece


# Configure logging to write to a file
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
# Constants
MAX_BLOCK_SIZE = 16384  # 16 KB
MAX_BACKLOG = 5  # Number of unfulfilled requests

# Global variables
downloaded_pieces = 0
downloaded_pieces_lock = threading.Lock()
downloaded_indices = set()


# Worker to download pieces from peers
def download_worker(peer, work_queue, results_queue, info_hash, peer_id, total_pieces):
    client = Communicator(peer, peer_id, info_hash)
    logging.info(f"Starting download from peer {peer}")

    # gửi ngay sau khi kết nối
    client.send_interested()
    # client.send_unchoke()

    while not work_queue.empty():
        piece = work_queue.get()
        logging.debug(f"Downloading piece {piece.index} from peer {peer}")
        logging.debug(f"Client bitfield: {client.bitfield}")
        if client.bitfield.has_piece(piece.index):
            logging.debug(f"Peer {peer} has piece {piece.index}")
            try:
                data = download_piece(client, piece)
                if data:
                    logging.debug(f"HAS DATA")
                else:
                    logging.debug(f"NO DATA")
                if check_piece_integrity(piece, data):
                    ####TEST
                    # print(f"Data of piece {piece.index}: {data}")
                    # sys.exit(0)
                    results_queue.put((piece.index, data))
                    with downloaded_pieces_lock:
                        global downloaded_pieces
                        downloaded_pieces += 1
                        logging.info(f"DOWLOADED_PIECES: {downloaded_pieces} - TOTAL_PIECES: {total_pieces}")  
                        if downloaded_pieces >= total_pieces:
                            client.send_not_interested()
                            logging.info("All pieces downloaded, sent NotInterested message")
                else:
                    logging.info(f"Piece {piece.index} failed integrity check")
                    # Log the pieces that have been successfully downloaded and passed integrity check
                    with downloaded_pieces_lock:
                        logging.info(f"Downloaded pieces so far: {downloaded_pieces}")
                    logging.warning(f"Piece {piece.index} failed integrity check, retrying...")
                    work_queue.put(piece)
            except TimeoutError:
                logging.warning("Timeout while downloading piece, retrying...")
                work_queue.put(piece)
                time.sleep(1)
            except ValueError as e:
                logging.error(f"Error: {e}")
                work_queue.put(piece)
                time.sleep(1)
        else:
            work_queue.put(piece)

# Function to download a specific piece from a peer
def download_piece(client, piece):
    downloaded = 0
    requested = 0
    backlog = 0
    buffer = bytearray(piece.length)

    while downloaded < piece.length:
        logging.debug(f"Downloaded {downloaded} bytes out of {piece.length} bytes")
        logging.debug(f"client.choked: {client.choked}, backlog: {backlog}, requested: {requested}")
        if not client.choked and backlog < MAX_BACKLOG:
            block_size = min(piece.length - requested, MAX_BLOCK_SIZE)
            logging.debug(f"Before request")
            client.send_request(piece.index, requested, block_size)
            logging.debug(f"Requested block {requested} - {requested + block_size} from peer {client.peer}")
            backlog += 1
            requested += block_size

        client.conn.settimeout(5)  # Set a timeout for reads

        try:
            message = client.read()
            if message is None:
                logging.warning("Received None message, retrying...")
                continue

            if message.ID == MessageID.MsgPiece:
                block_length = Message.parse_piece(piece.index, buffer, message)
                downloaded += block_length
                backlog -= 1
            elif message.ID == MessageID.MsgHave:
                logging.info(f"Received have for piece {message.index} from peer")
            elif message.ID == MessageID.MsgChoke:
                client.choked = True
                logging.info("Peer has choked us")
            elif message.ID == MessageID.MsgUnchoke:
                client.choked = False
                logging.info("Peer has unchoked us")
        except TimeoutError:
            logging.warning("Timeout while reading message, retrying...")
            continue
        
    client.send_have(piece.index)
    # logging.debug(f"Data of piece {piece.index}: {buffer}")
    return buffer

# Check the integrity of a downloaded piece
def check_piece_integrity(piece, data):
    # Hash the data and compare with the expected hash
    piece_hash = hashlib.sha1(data).digest()
    expected_hash = piece.hash
    logging.debug(f"Calculated hash: {piece_hash.hex()}, Expected hash: {expected_hash.hex()}")
    return piece_hash == expected_hash

# Assemble all downloaded pieces into the final file
def assemble_file(results_queue, file_path):
    pieces = []
    while not results_queue.empty():
        index, piece_data = results_queue.get()
        pieces.append((index, piece_data))
    
    # Sắp xếp dữ liệu theo index
    pieces.sort()
    
    # Ghép nối dữ liệu đã sắp xếp
    file_data = bytearray()
    for _, piece_data in pieces:
        file_data.extend(piece_data)

    with open(file_path, "wb") as f:
        f.write(file_data)

# Hàm tạo file nếu chưa tồn tại
def prepare_download_file(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            pass  # Tạo file rỗng

def start_download(peers, pieces, info_hash, peer_id, file_path):
    prepare_download_file(file_path)

    # Tạo hàng đợi công việc và hàng đợi kết quả
    work_queue = queue.Queue()
    results_queue = queue.Queue()
    
    # Thêm tất cả các mảnh vào hàng đợi công việc
    for piece in pieces:
        work_queue.put(piece)
    
    # Khởi động một luồng cho mỗi peer
    threads = []
    download_successful = True  # Cờ để kiểm tra xem quá trình tải có hoàn tất không
    total_pieces = len(pieces)
    for peer in peers:
        t = threading.Thread(target=download_worker, args=(peer, work_queue, results_queue, info_hash, peer_id, total_pieces))
        t.start()
        threads.append(t)
    
    # Chờ tất cả luồng hoàn tất
    for t in threads:
        t.join()

    # Kiểm tra xem tất cả các mảnh đã tải thành công chưa
    downloaded_pieces = results_queue.qsize()
    if downloaded_pieces == total_pieces:
        assemble_file(results_queue, file_path)
        logging.info(f"Download completed. File saved to {file_path}")
    else:
        download_successful = False
        logging.error("Download incomplete: Some pieces failed to download due to timeouts.")

    # Thông báo cuối cùng chỉ ra lỗi nếu quá trình tải không thành công
    if not download_successful:
        logging.info("Download was incomplete. Please check network and retry.")