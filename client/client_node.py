import requests
import bencodepy
import random
import string
import struct
import os
import hashlib
from tabulate import tabulate

def _generate_peer_id(length=20):
    """Generate a random peer ID."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

class ClientNode:
    def __init__(self):
        self.tracker_url = None
        self.tracker_id = None
        self.torrent_file = None
        self.torrent_data = None
        self.has_announced = False  # Track if the client has announced to the tracker
        self.peer_id = _generate_peer_id()
        self.port = 6881

    def _load_torrent_file(self, torrent_file):
        """Load and parse the .torrent file."""
        with open(torrent_file, 'rb') as f:
            torrent_data = bencodepy.decode(f.read())
        self.torrent_file = torrent_file
        torrent_data = {k.decode('utf-8'): v for k, v in torrent_data.items()}
        torrent_data['info'] = {k.decode('utf-8'): v for k, v in torrent_data['info'].items()}  # Decode info keys
        self.tracker_url = torrent_data['announce'].decode('utf-8')
        self.torrent_data = torrent_data
        return torrent_data, torrent_data['info']

    def announce(self, info_hash, port, event='started'):
        """Send announce request to tracker and update client state."""
        info = self.torrent_data['info']
        if 'length' in info:
            file_length = info['length']
        elif 'files' in info:
            file_length = sum(file['length'] for file in info['files'])
        else:
            raise KeyError("Neither 'length' nor 'files' key found in torrent info dictionary.")

        params = {
            'info_hash': info_hash,
            'peer_id': self.peer_id,
            'port': port,
            'uploaded': 0,
            'downloaded': 0,
            'left': file_length,  # Set the length of the file from the torrent data
            'event': event,
            'compact': 1
        }
        if self.tracker_id:
            params['trackerid'] = self.tracker_id

        try:
            response = requests.get(self.tracker_url, params=params)
            response.raise_for_status()
            response_data = bencodepy.decode(response.content)
            self.has_announced = True  # Confirm that the client has announced to the tracker
            if b'failure reason' in response_data:
                print(f"Tracker error: {response_data[b'failure reason'].decode()}")
                return []
            if b'warning message' in response_data:
                print(f"Tracker warning: {response_data[b'warning message'].decode()}")
            if b'tracker id' in response_data:
                self.tracker_id = response_data[b'tracker id'].decode()
            peers = response_data.get(b'peers', [])
            if isinstance(peers, bytes):
                # Handle compact format
                peers = self._parse_compact_peers(peers)
            return peers
        except requests.RequestException as e:
            print(f"Error during announce request: {e}")
            return []

    def download_torrent(self, torrent_file, port, download_dir=None):
        """Handle the download process of a torrent."""
        torrent_data, info = self._load_torrent_file(torrent_file)
        info_hash = hashlib.sha1(bencodepy.encode(info)).digest()
        print(f"Starting download from {self.tracker_url} on port {port}...")

        peers = self.announce(info_hash, port)
        print(f"Found peers: {peers}")

        # Simulate download process
        print(f"Downloading files to {download_dir if download_dir else os.getcwd()}...")
        # Implement actual download logic here

    def seed_torrent(self, torrent_file, port, upload_rate=None):
        """Handle the seeding process of a torrent."""
        torrent_data, info = self._load_torrent_file(torrent_file)
        info_hash = hashlib.sha1(bencodepy.encode(info)).digest()
        print(f"Starting seeding to {self.tracker_url} on port {port} with upload rate {upload_rate}...")

        peers = self.announce(info_hash, port, event='completed')
        print(f"Seeding to peers: {peers}")
        # Simulate seeding process
        print("Seeding...")

    def show_status(self, torrent_file):
        """Show the status of a torrent."""
        torrent_data, _ = self._load_torrent_file(torrent_file)
        print("Torrent status:")
        print(f"Tracker: {self.tracker_url}")
        # Simulate fetching and showing status

    def show_peers(self, torrent_file):
        """Show the list of peers for a torrent."""
        torrent_data, info = self._load_torrent_file(torrent_file)
        info_hash = hashlib.sha1(bencodepy.encode(info)).digest()
        print(f"Fetching peers from {self.tracker_url}...")

        peers = self.announce(info_hash, port=6881)  # Use default port
        table = [[peer['ip'], peer['port']] for peer in peers]
        print(f"Peers for {torrent_file}:\n")
        print(tabulate(table, headers=["IP Address", "Port"], tablefmt="grid"))

    def stop_torrent(self, torrent_file):
        """Stop the torrent download or seeding."""
        torrent_data, info = self._load_torrent_file(torrent_file)
        info_hash = hashlib.sha1(bencodepy.encode(info)).digest()
        print(f"Stopping torrent {torrent_file}...")

        # Notify tracker that we're stopping
        self.announce(info_hash, port=6881, event='stopped')
        print("Torrent stopped.")

    def remove_torrent(self, torrent_file):
        """Remove the torrent from the client."""
        print(f"Removing torrent {torrent_file} from the client...")
        # Simulate removing torrent (e.g., remove from a list or database)

    def _parse_compact_peers(self, peers):
        """Parse compact peer format."""
        peer_list = []
        for i in range(0, len(peers), 6):
            ip = struct.unpack("!I", peers[i:i+4])[0]
            ip_str = f"{(ip >> 24) & 0xFF}.{(ip >> 16) & 0xFF}.{(ip >> 8) & 0xFF}.{ip & 0xFF}"
            port = struct.unpack("!H", peers[i+4:i+6])[0]
            peer_list.append({'ip': ip_str, 'port': port})
        return peer_list

    def scrape(self, info_hash):
        """Gửi yêu cầu scrape tới tracker để lấy thông tin về số lượng peers của torrent với info_hash."""
        # Tạo URL scrape
        if 'announce' in self.tracker_url:
            scrape_url = self.tracker_url.replace('announce', 'scrape')
        else:
            raise ValueError("Tracker does not support scrape convention.")

        # Thực hiện yêu cầu scrape
        params = {'info_hash': info_hash}
        try:
            response = requests.get(scrape_url, params=params)
            response.raise_for_status()  # Kiểm tra xem yêu cầu có thành công không
            self.has_announced = True  # Đánh dấu rằng đã thông báo sự kiện
            # Giải mã phản hồi
            response_data = bencodepy.decode(response.content)

            # Lấy thông tin về torrents
            files_info = response_data.get(b'files', {})
            if info_hash in files_info:
                torrent_info = files_info[info_hash]
                complete = torrent_info.get(b'complete', 0)
                incomplete = torrent_info.get(b'incomplete', 0)
                downloaded = torrent_info.get(b'downloaded', 0)
                return {
                    'complete': complete,
                    'incomplete': incomplete,
                    'downloaded': downloaded
                }
            else:
                print("No information found for the given info_hash.")
                return None

        except requests.RequestException as e:
            print(f"Error during scrape request: {e}")
            return None

    def scrape_peers(self, torrent_file):
        """Scrape the tracker for peer information."""
        torrent_data, info = self._load_torrent_file(torrent_file)
        info_hash = hashlib.sha1(bencodepy.encode(info)).digest()
        print(f"Scraping tracker for peer information...")
        stats = self.scrape(info_hash)
        if stats:
            table = [
                ["Seeders (complete)", stats['complete']],
                ["Leechers (incomplete)", stats['incomplete']],
                ["Total downloaded", stats['downloaded']]
            ]
            print(f"Scrape info for {torrent_file}:\n")
            print(tabulate(table, headers=["Description", "Count"], tablefmt="grid"))

    def sign_out(self):
        """Notify tracker that the client is offline if an event was announced."""
        if not self.has_announced:
            print("No event announced, skipping sign out.")
            return

        params = {
            'peer_id': self.peer_id,
            'port': self.port,
            'event': 'stopped'
        }
        try:
            response = requests.get(self.tracker_url, params=params)
            response.raise_for_status()
            print("Signed out successfully.")
        except requests.RequestException as e:
            print(f"Error during sign out request: {e}")