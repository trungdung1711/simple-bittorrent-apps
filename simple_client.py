import socket
import threading
import time
import click
import pprint
from constants import SBC
from threading import Thread
from client_util import create_torrent, get_torrent_dic, Peer, first_announce, get_piece_number, \
    accept_connections_from_peers, create_file, get_file_length, create_connections_to_server_peers, \
    is_download_completed
from io_util import progress_display



# Create a group of commands
@click.group()
def cli():
    pass  # This will serve as the entry point for all the commands


@cli.command()
@click.option('-f', '--file', required=True, type=str, help="Name of file")
@click.option('-ip', '--ip', required=True, type=str, help="IP address of tracker")
@click.option('-p', '--port', required=True, type=int, help="Port of tracker")
@click.option('-pl', '--piece-length', required=False, default = 512 * 1024, type=int, help="Length of piece (byte), default to be 512KB")
@click.option('-d', '--destination', required=True, type=str, help="Destination directory")
def torrent(file, ip, port, piece_length, destination):
    try:
        click.echo(f"Creating torrent from file {file}, saving torrent to {destination}")
        create_torrent(file, ip, port, piece_length, destination)
    except Exception as e:
        print(SBC.APP_NAME + ': ' + str(e))


@cli.command()
@click.option('-t', '--torrent', required=True, type=str, help="Name of torrent")
def meta(torrent):
    try:
        torrent_dic = get_torrent_dic(torrent)
        torrent_dic['info']['pieces'] = '***'
        pprint.pprint(torrent_dic)
    except Exception as e:
        print(SBC.APP_NAME + ': ' + str(e))


@cli.command()
@click.option('-t', '--torrent', required=True, type=str, help="Name of torrent")
@click.option('-f', '--file', required=True, type=str, help="Name of file saved")
@click.option('-ip', '--ip', required=True, type=str, help="IP address of peer")
@click.option('-p', '--port', required=True, type=int, help="Port of the peer")
def join(torrent, file, ip, port):
    try:
        # The dictionary for tracking piece number
        peer_pieces_tracking = {}
        peer_pieces_tracking_lock = threading.Lock()

        peer = Peer(torrent, file, ip, port)
        peer_lock = threading.Lock()

        # interval time to periodically announce
        # peers as list of dictionary of peer

        piece_number = get_piece_number(torrent)
        is_seeder = input('Are you a seeder (yes/no): ')
        if is_seeder == 'yes':
            # todo: announce
            peer.init_seeder()
            interval, peers = first_announce(peer)
            # print(interval)
            # pprint.pprint(peers)
            peer_pieces_tracking = {i : 'AVAILABLE' for i in range(piece_number)}
            # todo: update to the tracker periodically
        else:
            # todo: announce
            peer.init_leecher()
            interval, peers = first_announce(peer)
            # print(interval)
            # pprint.pprint(peers)
            # todo: create the file first
            peer_pieces_tracking = {i : 'UNAVAILABLE' for i in range(piece_number)}
            create_file(peer.file, get_file_length(peer.torrent))
            # todo: connect to other peer to download
            create_connections_to_server_peers(peer, peers, peer_pieces_tracking, peer_lock, peer_pieces_tracking_lock)
            # todo: update to the tracker periodically

        # todo: accept the connections from other peers, both for the
        # todo: seeder and the leecher
        accept_connections_from_peers_thread = threading.Thread(target=accept_connections_from_peers, args=(
        peer.peer_ip, peer.peer_port, peer, peer_pieces_tracking, peer_lock))
        # todo: ensure that the main thread will terminate the accept_connections_from_peers_thread
        accept_connections_from_peers_thread.daemon = True
        accept_connections_from_peers_thread.start()

        progress_display(peer)

        while True:
            if is_download_completed(peer):
                print('')
                is_continue_to_seed = input('Download successfully, continue to seed? (yes/no): ')
                # todo: still let the seeder to continue to seed, handle later
                if is_continue_to_seed == 'no':
                    # todo: announce to the tracker to remove the peer
                    # todo: stop the accept_connections_from_peers
                    print('Seeding')

                else:
                    # todo: still let the accept_connections_from_peers to run
                    print('Seeding')

        accept_connections_from_peers_thread.join()
    except Exception as e:
        print(SBC.APP_NAME + ': ' + str(e))

if __name__ == '__main__':
    cli()