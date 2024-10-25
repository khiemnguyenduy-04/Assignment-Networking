class ClientList:
    def __init__(self):
        self.peers = {}

    def add_peer(self, info_hash, peer_id, ip, port):
        """Thêm peer mới vào danh sách peers cho file info_hash."""
        if info_hash not in self.peers:
            self.peers[info_hash] = []
        self.peers[info_hash].append({'peer_id': peer_id, 'ip': ip, 'port': port})

    def remove_peer(self, info_hash, peer_id):
        """Xóa một peer khỏi danh sách khi họ dừng chia sẻ."""
        if info_hash in self.peers:
            self.peers[info_hash] = [peer for peer in self.peers[info_hash] if peer['peer_id'] != peer_id]

    def get_peers(self, info_hash):
        """Trả về danh sách các peers đang chia sẻ tệp với info_hash."""
        return self.peers.get(info_hash, [])
