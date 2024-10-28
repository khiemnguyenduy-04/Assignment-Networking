import socket
import time
import os
import sys
import logging
import threading
import queue
import hashlib

# Thêm thư mục gốc của dự án vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from p2p.bitfield import Bitfield  
from p2p.peer import Peer 
from p2p.message import Message, MessageID
from p2p.handshake import Handshake

MAX_BLOCK_SIZE = 16384  # 16 KB
MAX_BACKLOG = 5         # Number of unfulfilled requests
downloaded_pieces = 0
downloaded_pieces_lock = threading.Lock()

class Communicator:
    def __init__(self, peer: Peer, peer_id: bytes, info_hash: bytes, bitfield: Bitfield = None, conn=None):
        self.conn = conn
        self.choked = True
        self.bitfield = bitfield
        self.peer = peer
        self.info_hash = info_hash
        self.peer_id = peer_id
        logging.debug(f"Created communicator with peer {peer}")
        
        if self.conn is None:
            self.conn = self.connect(peer)
        
        self.complete_handshake()
        if self.bitfield is None:
            self.recv_bitfield()
        else:
            logging.debug("Bitfield already present (seeder), skipping recv_bitfield")

    def connect(self, peer: Peer):
        """Kết nối đến một peer."""
        try:
            conn = socket.create_connection((peer.ip, peer.port), timeout=1.5)
            logging.debug(f"Connected to peer {peer}")
            return conn
        except (socket.timeout, socket.error) as e:
            logging.error(f"Error connecting to peer {peer}: {e}")
            raise e

    def complete_handshake(self):
        """Thực hiện handshake với peer và gửi bitfield nếu có."""
        req = Handshake(info_hash=self.info_hash, peer_id=self.peer_id)
        self.conn.settimeout(7)
        
        try:
            self.conn.send(req.serialize())
            logging.debug("Sent handshake")
            
            res = Handshake.read(self.conn)
            if res.info_hash != self.info_hash:
                raise ValueError(f"Expected infohash {self.info_hash.hex()} but got {res.info_hash.hex()}")
            logging.debug("Received valid handshake response")
        
            # Send bitfield sau khi handshake nếu có
            if self.bitfield:
                bitfield_msg = Message(message_id=MessageID.MsgBitfield, payload=self.bitfield)
                self.conn.send(bitfield_msg.serialize())
                logging.debug("Sent bitfield")
            else:
                logging.debug("No bitfield to send")
        except (socket.timeout, socket.error) as e:
            logging.error(f"Error during handshake with peer {self.peer}: {e}")
            raise e

    def recv_bitfield(self):
        """Nhận bitfield từ peer và gửi xác nhận 'Interested' nếu có thể download."""
        self.conn.settimeout(10)
        try:
            msg, err = Message.read(self.conn)
            if err:
                raise ValueError(f"Error reading message: {err}")
            if msg is None:
                raise ValueError("Expected bitfield but got None")
            if msg.ID != MessageID.MsgBitfield:
                raise ValueError(f"Expected bitfield message but got {msg.ID}")
            self.bitfield = Bitfield(msg.Payload)
            logging.debug("Received bitfield")
            
            # Gửi thông báo Interested
            self.send_interested()
        except socket.timeout:
            logging.error("Timeout while waiting for bitfield")

    def read(self):
        """Đọc một thông điệp từ kết nối."""
        try:
            msg, err = Message.read(self.conn)
            if err:
                logging.error(f"Error reading message: {err}")
            return msg
        except socket.timeout:
            logging.warning("Timeout while reading message, retrying...")
            return None
    def send_request(self, index, begin, length):
        """Gửi một thông điệp Request tới peer."""
        req = Message.format_request(index, begin, length)
        self.conn.send(req.serialize())

    def send_interested(self):
        """Gửi thông điệp Interested tới peer."""
        msg = Message(message_id=MessageID.MsgInterested)
        self.conn.send(msg.serialize())

    def send_not_interested(self):
        """Gửi thông điệp NotInterested tới peer."""
        msg = Message(message_id=MessageID.MsgNotInterested)
        self.conn.send(msg.serialize())

    def send_unchoke(self):
        """Gửi thông điệp Unchoke tới peer."""
        msg = Message(message_id=MessageID.MsgUnchoke)
        self.conn.send(msg.serialize())
    
    def send_choke(self):
        """Gửi thông điệp Choke tới peer."""
        msg = Message(message_id=MessageID.MsgChoke)
        self.conn.send(msg.serialize())
        
    def send_have(self, index):
        """Gửi thông điệp Have tới peer."""
        msg = Message.format_have(index)
        self.conn.send(msg.serialize())