import unittest
from tracker_server import TrackerServer
from client_list import ClientList

class TestTrackerServer(unittest.TestCase):
    def setUp(self):
        self.tracker_server = TrackerServer()
        self.client_list = self.tracker_server.client_list

    def test_announce(self):
        params = {'info_hash': ['some_info_hash'], 'peer_id': ['peer1'], 'port': ['6882']}
        self.tracker_server.handle_announce(params, '127.0.0.1')
        peers = self.client_list.get_peers('some_info_hash')
        self.assertEqual(len(peers), 1)
        self.assertEqual(peers[0]['peer_id'], 'peer1')

    def test_scrape(self):
        params = {'info_hash': ['some_info_hash'], 'peer_id': ['peer1'], 'port': ['6882']}
        self.tracker_server.handle_announce(params, '127.0.0.1')
        peers = self.tracker_server.handle_scrape('some_info_hash')
        self.assertEqual(len(peers), 1)
        self.assertEqual(peers[0]['peer_id'], 'peer1')

if __name__ == '__main__':
    unittest.main()
