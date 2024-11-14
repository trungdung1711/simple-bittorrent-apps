import threading
import click
import pprint
from simple_peer.talker import talker
from simple_peer.listener import listener
from simple_peer.util import create_torrent, create_file, get_torrent_dic, get_file_length, get_piece_number, \
    started_announce, is_download_completed, Peer, SBC, progress_display, stop_announce


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
        create_torrent(file, ip, port, piece_length, destination)
        click.echo(f'Creating torrent from file {file}')
        click.echo(f'Saving torrent to {destination}')
    except Exception as e:
        click.echo(SBC.APP_NAME + ': ' + str(e))


@cli.command()
@click.option('-t', '--torrent', required=True, type=str, help="Name of torrent")
def meta(torrent):
    try:
        torrent_dic = get_torrent_dic(torrent)
        torrent_dic['info']['pieces'] = '***'
        pprint.pprint(torrent_dic)
    except Exception as e:
        click.echo(SBC.APP_NAME + ': ' + str(e))


@cli.command()
@click.option('-t', '--torrent', required=True, type=str, help="Name of torrent")
@click.option('-f', '--file', required=True, type=str, help="Name of file saved")
@click.option('-ip', '--ip', required=True, type=str, help="IP address of peer")
@click.option('-p', '--port', required=True, type=int, help="Port of the peer")
def join(torrent, file, ip, port):
    try:
        # todo: protect the shared objects between client threads
        # todo: and the server threads
        peer = Peer(torrent, file, ip, port)
        # peer_pieces_tracking = {}
        peer_lock = threading.Lock()
        peer_pieces_tracking_lock = threading.Lock()

        is_seeder = input('Are you a seeder (yes/no): ')
        if is_seeder == 'yes':
            # todo: announce the seeder to the tracker
            peer.init_seeder()
            interval, peers = started_announce(peer)
            pprint.pprint(peers)
            peer_pieces_tracking = {i : 'AVAILABLE' for i in range(get_piece_number(peer.torrent))}
            # todo: update to the tracker periodically
        else:
            # todo: announce the leecher to the tracker
            # todo: connect to other peer to download
            # todo: create the file to save
            # todo: update to the tracker periodically
            peer.init_leecher()

            interval, peers = started_announce(peer)
            pprint.pprint(peers)
            peer_pieces_tracking = {i : 'UNAVAILABLE' for i in range(get_piece_number(peer.torrent))}
            create_file(peer.file, get_file_length(peer.torrent))
            talker_thread = threading.Thread(target=talker, args=(peer, peers, peer_pieces_tracking, peer_lock, peer_pieces_tracking_lock))
            talker_thread.daemon = True
            talker_thread.start()

        # todo: create the central server thread
        listener_thread = threading.Thread(target=listener, args=(
        peer, peer_pieces_tracking, peer_lock))
        # todo: ensure that the main thread will terminate the accept_connections_from_peers_thread
        listener_thread.daemon = True
        listener_thread.start()

        progress_display(peer)

        # todo: when finishing downloading, all the client peer thread
        # todo: should finish and close with the server handle peer thread
        # todo: as follow the DONE message in the protocol
        while True:
            if is_download_completed(peer):
                print('')
                is_continue_to_seed = input('Download successfully, continue to seed? (yes/no): ')
                # todo: still let the seeder to continue to seed, handle later
                if is_continue_to_seed == 'no':
                    # todo: announce to the tracker to remove the peer
                    # todo: stop the accept_connections_from_peers
                    stop_announce(peer)
                    return
                else:
                    # todo: still let the accept_connections_from_peers to run
                    print('Seeding...')
    except Exception as e:
        print(SBC.APP_NAME + ': ' + str(e))


if __name__ == '__main__':
    cli()