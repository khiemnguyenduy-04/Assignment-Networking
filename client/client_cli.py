import argparse
from client_node import ClientNode

def main():
    # Initialize client
    client = ClientNode()

    parser = argparse.ArgumentParser(description="Torrent Client CLI")
    subparsers = parser.add_subparsers(dest='command')

    # Command download
    download_parser = subparsers.add_parser('download')
    download_parser.add_argument('torrent_file', help='Path to the torrent file')
    download_parser.add_argument('--port', type=int, default=6881, help='Port to use for downloading')
    download_parser.add_argument('--download-dir', help='Directory to save the downloaded file')

    # Command seed
    seed_parser = subparsers.add_parser('seed')
    seed_parser.add_argument('torrent_file', help='Path to the torrent file')
    seed_parser.add_argument('complete_file', help='Path to the complete file to seed')
    seed_parser.add_argument('--port', type=int, default=6882, help='Port to use for seeding')
    seed_parser.add_argument('--upload-rate', type=int, help='Upload rate limit in KB/s')

    # Command status
    status_parser = subparsers.add_parser('status')
    

    # Command peers
    peers_parser = subparsers.add_parser('peers')
    peers_parser.add_argument('torrent_file', help='Path to the torrent file')
    peers_parser.add_argument('--scrape', action='store_true', help='Scrape the tracker for peer information')
    peers_parser.add_argument('--get', action='store_true', help='Get the list of peers from the tracker')

    # Command stop
    stop_parser = subparsers.add_parser('stop')
    stop_parser.add_argument('torrent_file', help='Path to the torrent file')

    # Command remove
    remove_parser = subparsers.add_parser('remove')
    remove_parser.add_argument('torrent_file', help='Path to the torrent file')

    # Parse initial arguments
    args = parser.parse_args()

    # If a command is provided, execute it
    if args.command:
        try:
            if args.command == 'download':
                client.download_torrent(args.torrent_file, port=args.port, download_dir=args.download_dir)
            elif args.command == 'seed':
                client.seed_torrent(args.torrent_file, args.complete_file, port=args.port, upload_rate=args.upload_rate)
            elif args.command == 'status':
                client.show_status()
            elif args.command == 'peers':
                if args.scrape:
                    client.scrape_peers(args.torrent_file)
                elif args.get:
                    client.show_peers(args.torrent_file)
                else:
                    print("Unknown peers command")
            elif args.command == 'stop':
                client.stop_torrent(args.torrent_file)
            elif args.command == 'remove':
                client.remove_torrent(args.torrent_file)
            else:
                print("Unknown command")
        except Exception as e:
            print(f"Error executing command: {e}")

    # Enter interactive mode
    try:
        while True:
            command = input(">>> ").split()
            if not command:
                continue
            if command[0] == 'exit':
                break
            try:
                args = parser.parse_args(command)
            except SystemExit:
                print("Invalid command. Please try again.")
                continue

            if args.command == 'download':
                client.download_torrent(args.torrent_file, port=args.port, download_dir=args.download_dir)
            elif args.command == 'seed':
                client.seed_torrent(args.torrent_file, args.complete_file, port=args.port, upload_rate=args.upload_rate)
            elif args.command == 'status':
                client.show_status()
            elif args.command == 'peers':
                if args.scrape:
                    client.scrape_peers(args.torrent_file)
                elif args.get:
                    client.show_peers(args.torrent_file)
                else:
                    print("Unknown peers command")
            elif args.command == 'stop':
                client.stop_torrent(args.torrent_file)
            elif args.command == 'remove':
                client.remove_torrent(args.torrent_file)
            else:
                print("Unknown command")
    finally:
        # Sign out when exiting if an event was announced
        client.sign_out()

if __name__ == '__main__':
    main()