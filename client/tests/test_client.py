import unittest
from unittest.mock import patch, MagicMock
import bencodepy
import sys
import os

# Add the parent directory of the client module to the sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from client_node import ClientNode

class TestClientNode(unittest.TestCase):
    def setUp(self):
        self.client = ClientNode()
        self.client._load_torrent_file = MagicMock(return_value=({'announce': 'http://localhost:6881/announce', 'info': {'length': 12345}}, {'length': 12345}))
        self.client.torrent_data = {'announce': 'http://localhost:6881/announce', 'info': {'length': 12345}}
        self.client.tracker_url = "http://localhost:6881/announce"

    @patch('requests.get')
    def test_announce_started(self, mock_get):
        bencode_response = bencodepy.encode({
            'interval': 1800,
            'peers': b'\x7f\x00\x00\x01\x1a\xe1'
        })
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = bencode_response

        peers = self.client.announce(info_hash=b'some_info_hash', peer_id=b'peer1', port=6882, event='started')
        expected_peers = [{'ip': '127.0.0.1', 'port': 6881}]
        self.assertEqual(peers, expected_peers)

    @patch('requests.get')
    def test_announce_stopped(self, mock_get):
        bencode_response = bencodepy.encode({
            'interval': 1800,
            'peers': b'\x7f\x00\x00\x01\x1a\xe1'
        })
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = bencode_response

        peers = self.client.announce(info_hash=b'some_info_hash', peer_id=b'peer1', port=6882, event='stopped')
        expected_peers = [{'ip': '127.0.0.1', 'port': 6881}]
        self.assertEqual(peers, expected_peers)

    @patch('requests.get')
    def test_announce_completed(self, mock_get):
        bencode_response = bencodepy.encode({
            'interval': 1800,
            'peers': b'\x7f\x00\x00\x01\x1a\xe1'
        })
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = bencode_response

        peers = self.client.announce(info_hash=b'some_info_hash', peer_id=b'peer1', port=6882, event='completed')
        expected_peers = [{'ip': '127.0.0.1', 'port': 6881}]
        self.assertEqual(peers, expected_peers)

    @patch('requests.get')
    def test_scrape(self, mock_get):
        bencode_response = bencodepy.encode({
            'files': {
                b'some_info_hash': {
                    b'complete': 5,
                    b'incomplete': 2,
                    b'downloaded': 10
                }
            }
        })
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = bencode_response

        stats = self.client.scrape(info_hash=b'some_info_hash')
        expected_stats = {
            'complete': 5,
            'incomplete': 2,
            'downloaded': 10
        }
        self.assertEqual(stats, expected_stats)


    @patch('requests.get')
    def test_show_peers(self, mock_get):
        bencode_response = bencodepy.encode({
            'interval': 1800,
            'peers': b'\x7f\x00\x00\x01\x1a\xe1'
        })
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = bencode_response

        self.client.announce = MagicMock()
        self.client.show_peers('dummy.torrent')
        self.client.announce.assert_called_once()

    @patch('requests.get')
    def test_stop_torrent(self, mock_get):
        bencode_response = bencodepy.encode({
            'interval': 1800,
            'peers': b'\x7f\x00\x00\x01\x1a\xe1'
        })
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = bencode_response

        self.client.announce = MagicMock()
        self.client.stop_torrent('dummy.torrent')
        self.client.announce.assert_called_once()


if __name__ == '__main__':
    unittest.main()