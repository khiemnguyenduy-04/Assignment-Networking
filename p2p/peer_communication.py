import socket
import time
import os
import sys

# Thêm thư mục gốc của dự án vào sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from p2p.bitfield import Bitfield  
from p2p.peer import Peer 
from p2p.message import Message, MessageID
from p2p.handshake import Handshake

import logging

class Communicator:
    def __init__(self, peer: Peer, peer_id: bytes, info_hash: bytes, bitfield: Bitfield = None):
        self.conn = None
        self.choked = True
        self.bitfield = bitfield
        self.peer = peer
        self.info_hash = info_hash
        self.peer_id = peer_id
        
        self.connect(peer)
        self.complete_handshake()
        self.recv_bitfield()

    def connect(self, peer: Peer):
        """Connect to a peer."""
        self.conn = socket.create_connection((peer.ip, peer.port), timeout=1.5)
        logging.debug(f"Connected to peer {peer}")

    def complete_handshake(self):
        """Complete handshake with peer."""
        req = Handshake(info_hash=self.info_hash, peer_id=self.peer_id)
        self.conn.settimeout(7)
        self.conn.send(req.serialize())
        logging.debug("Sent handshake")

        res = Handshake.read(self.conn)
        if res.info_hash != self.info_hash:
            raise ValueError(f"Expected infohash {self.info_hash.hex()} but got {res.info_hash.hex()}")
        logging.debug("Received valid handshake response")

        # Send bitfield after handshake if available
        # Để thực hiện seeding, client cần gửi bitfield cho peer
        if self.bitfield:
            bitfield_msg = Message(message_id=MessageID.MsgBitfield, payload=self.bitfield.to_bytes())
            self.conn.send(bitfield_msg.serialize())
            logging.debug("Sent bitfield")

    def recv_bitfield(self):
        """Receive bitfield from peer."""
        self.conn.settimeout(10)
        msg, err = Message.read(self.conn)
        if err:
            raise ValueError(f"Error reading message: {err}")
        if msg is None:
            raise ValueError("Expected bitfield but got None")
        if msg.ID != MessageID.MsgBitfield:
            raise ValueError(f"Expected bitfield message but got {msg.ID}")

        self.bitfield = Bitfield(msg.Payload)
        logging.debug("Received bitfield")

    def read(self):
        """Đọc và tiêu thụ một thông điệp từ kết nối."""
        msg, err = Message.read(self.conn)
        if err:
            raise ValueError(f"Error reading message: {err}")
        return msg

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

    def send_have(self, index):
        """Gửi thông điệp Have tới peer."""
        msg = Message.format_have(index)
        self.conn.send(msg.serialize())