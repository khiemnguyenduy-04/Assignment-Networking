from client.metainfo_parse import MetainfoParser
import os

torrent_file = r"F:\Networking_Assignment1\torrent\Zulip-1.3.0-beta-mac.zip.torrent"
parser = MetainfoParser(torrent_file)
print(parser.get_pieces())