import argparse
from client_node import ClientNode

def main():
    parser = argparse.ArgumentParser(description="Torrent Client CLI")
    subparsers = parser.add_subparsers(dest='command')

    # Command download
    download_parser = subparsers.add_parser('download')
    download_parser.add_argument('torrent_file', help='Path to the torrent file')
    download_parser.add_argument('--port', type=int, default=6881, help='Port to use for downloading')
    download_parser.add_argument('--download-dir', help='Directory to save downloaded files')

    # Command seed
    seed_parser = subparsers.add_parser('seed')
    seed_parser.add_argument('torrent_file', help='Path to the torrent file')
    seed_parser.add_argument('--port', type=int, default=6881, help='Port to use for seeding')
    seed_parser.add_argument('--upload-rate', type=int, help='Upload rate limit (KB/s)')

    # Command status
    status_parser = subparsers.add_parser('status')
    status_parser.add_argument('torrent_file', help='Path to the torrent file')

    # Command peers
    peers_parser = subparsers.add_parser('peers')
    peers_parser.add_argument('torrent_file', help='Path to the torrent file')
    peers_parser.add_argument('--scrape', action='store_true', help='Scrape tracker for peer information')

    # Command stop
    stop_parser = subparsers.add_parser('stop')
    stop_parser.add_argument('torrent_file', help='Path to the torrent file')

    # Command remove
    remove_parser = subparsers.add_parser('remove')
    remove_parser.add_argument('torrent_file', help='Path to the torrent file')

    args = parser.parse_args()

    # Handle each command
    client = ClientNode()

    if args.command == 'download':
        client.download_torrent(args.torrent_file, port=args.port, download_dir=args.download_dir)
    elif args.command == 'seed':
        client.seed_torrent(args.torrent_file, port=args.port, upload_rate=args.upload_rate)
    elif args.command == 'status':
        client.show_status(args.torrent_file)
    elif args.command == 'peers':
        if args.scrape:
            client.scrape_peers(args.torrent_file)  # Giả sử bạn đã định nghĩa phương thức này trong ClientNode
        else:
            client.show_peers(args.torrent_file)
    elif args.command == 'stop':
        client.stop_torrent(args.torrent_file)
    elif args.command == 'remove':
        client.remove_torrent(args.torrent_file)

if __name__ == '__main__':
    main()
