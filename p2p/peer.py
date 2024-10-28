import struct
import socket
from typing import List

class Peer:
    def __init__(self, ip: str, port: int):
        self.ip = ip
        self.port = port

    @classmethod
    def unmarshal(cls, peers_bin: bytes) -> List['Peer']:
        peer_size = 6  # 4 bytes for IP, 2 bytes for port
        if len(peers_bin) % peer_size != 0:
            raise ValueError("Received malformed peers")

        num_peers = len(peers_bin) // peer_size
        peers = []
        
        for i in range(num_peers):
            offset = i * peer_size
            ip_bytes = peers_bin[offset:offset + 4]
            port_bytes = peers_bin[offset + 4:offset + 6]
            
            # Chuyển đổi IP từ bytes sang chuỗi
            ip = socket.inet_ntoa(ip_bytes)
            # Chuyển đổi port từ bytes sang số nguyên
            port = struct.unpack('>H', port_bytes)[0]
            peers.append(cls(ip, port))
        
        return peers

    def __str__(self):
        return f"{self.ip}:{self.port}"
