import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from client_list import ClientList
import bencodepy
import threading
import logging
import argparse
import socket

def decode_info_hash(url_encoded_string):
    decoded_string = bytearray()
    i = 0
    while i < len(url_encoded_string):
        if url_encoded_string[i] == '%':
            if i + 2 < len(url_encoded_string):
                hex_value = url_encoded_string[i + 1:i + 3]
                try:
                    decoded_byte = int(hex_value, 16)
                    decoded_string.append(decoded_byte)
                except ValueError:
                    raise ValueError(f"Invalid hex value: {hex_value}")
                i += 3
            else:
                break
        else:
            decoded_string.append(ord(url_encoded_string[i]))
            i += 1
    if len(decoded_string) != 20:
        raise ValueError(f"Decoded string is not a valid SHA1 hash length: {decoded_string.hex()}")
    return bytes(decoded_string).hex()

# Constants
DEFAULT_PORT = 8000
TRACKER_INTERVAL = 1800  # Time between tracker updates in seconds

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrackerServer(BaseHTTPRequestHandler):
    client_list = ClientList()
    lock = threading.Lock()

    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        info_hash = None
        for param in query.split('&'):
            if param.startswith('info_hash='):
                info_hash = param.split('=')[1]
                break
        params = urllib.parse.parse_qs(query)
        if info_hash is not None:
            params['info_hash'] = [info_hash]
        if self.path.startswith("/announce"):
            self.handle_announce(params)
        elif self.path.startswith("/scrape"):
            self.handle_scrape(params)
        else:
            self.send_error(404, "Unknown request path")

    def handle_announce(self, params):
        info_hash = params.get("info_hash", [None])[0]
        peer_id = params.get("peer_id", [None])[0]
        port = int(params.get("port", [None])[0]) if params.get("port") else None
        uploaded = int(params.get("uploaded", [0])[0])
        downloaded = int(params.get("downloaded", [0])[0])
        left = int(params.get("left", [0])[0])
        event = params.get("event", [None])[0]

        if peer_id is None or port is None:
            self.send_error(400, "Missing required parameters")
            return

        client_ip = self.client_address[0]
        logger.info(f"Client IP: {client_ip}")

        with self.lock:
            if event == "started":
                if info_hash:
                    try:
                        info_hash_hex = decode_info_hash(info_hash)
                        info_hash = bytes.fromhex(info_hash_hex)
                    except Exception as e:
                        self.send_error(400, "Invalid info_hash encoding")
                        logger.error(f"Encoding error: {e}")
                        return
                    self.client_list.update_peer(info_hash, peer_id, client_ip, port, uploaded, downloaded, left, event)
            elif event == "stopped":
                if info_hash:
                    try:
                        info_hash_hex = decode_info_hash(info_hash)
                        info_hash = bytes.fromhex(info_hash_hex)
                    except Exception as e:
                        self.send_error(400, "Invalid info_hash encoding")
                        logger.error(f"Encoding error: {e}")
                        return
                    self.client_list.remove_peer(info_hash, peer_id)
                    logger.info(f"Peer {peer_id} has been removed from {info_hash.hex()} list")
                else:
                    self.client_list.remove_peer_from_all(peer_id)
                    logger.info(f"Peer {peer_id} has been removed from all torrents")
            elif event == "completed":
                if info_hash:
                    try:
                        info_hash_hex = decode_info_hash(info_hash)
                        info_hash = bytes.fromhex(info_hash_hex)
                    except Exception as e:
                        self.send_error(400, "Invalid info_hash encoding")
                        logger.error(f"Encoding error: {e}")
                        return
                    self.client_list.update_peer(info_hash, peer_id, client_ip, port, uploaded, downloaded, left, event)

        if info_hash:
            # Get the list of peers and remove the client's peer
            peers = self.client_list.get_peers(info_hash, peer_id)
            response = {
                "interval": TRACKER_INTERVAL,
                "peers": peers,
                "complete": self.client_list.get_complete_count(info_hash),
                "incomplete": self.client_list.get_incomplete_count(info_hash),
                "client_ip": client_ip  # Include the client's IP address in the response
            }
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(bencodepy.encode(response))

    def handle_scrape(self, params):
        info_hash = params.get("info_hash", [None])[0]
        if info_hash is not None:
            try:
                info_hash_hex = decode_info_hash(info_hash)
                info_hash = bytes.fromhex(info_hash_hex)
            except Exception as e:
                self.send_error(400, "Invalid info_hash encoding")
                logger.error(f"Encoding error: {e}")
                return
        scrape_data = self.client_list.get_scrape_info(info_hash)
        response = {b'files': scrape_data}
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(bencodepy.encode(response))

    def handle_command(self, command):
        if command == "discover":
            self.discover_clients()
        elif command == "ping":
            self.ping_clients()
        else:
            logger.error(f"Unknown command: {command}")

    def discover_clients(self):
        # Implement the logic to discover connected clients
        logger.info("Discovering connected clients...")
        # Example: Print the list of connected clients
        for client_id, files in self.client_list.items():
            logger.info(f"Client ID: {client_id}, Files: {files}")

    def ping_clients(self):
        # Implement the logic to ping connected clients
        logger.info("Pinging connected clients...")
        # Example: Send a ping request to each client and log the response
        for client_id in self.client_list.keys():
            try:
                client_ip = self.client_list.get_client_ip(client_id)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1)
                    s.connect((client_ip, DEFAULT_PORT))
                    logger.info(f"Client {client_id} is online")
            except (socket.timeout, ConnectionRefusedError):
                logger.info(f"Client {client_id} is offline")

def run(server_class=ThreadingHTTPServer, handler_class=TrackerServer, port=DEFAULT_PORT):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    logger.info(f"Starting tracker server on port {port} with multi-threading support")
    httpd.serve_forever()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the tracker server.")
    parser.add_argument('--port', type=int, default=DEFAULT_PORT, help='Port to run the tracker server on')
    args = parser.parse_args()
    run(port=args.port)
#add new method 