import threading
import click
import pprint

from simple_peer.re_announcer import re_announcer
from simple_peer.talker import talker
from simple_peer.listener import listener
from simple_peer.util import create_torrent, create_file, get_torrent_dic, get_file_length,\
    started_announce, is_download_completed, SBC, progress_display, stop_announce, leecher_init, seeder_init


@click.group()
def cli():
    pass


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
@click.option('-f', '--file', required=True, type=str, help="Name of file")
@click.option('-ip', '--ip', required=True, type=str, help="IP address of peer")
@click.option('-p', '--port', required=True, type=int, help="Port of the peer")
def join(torrent, file, ip, port):
    try:
        (peer,
         peer_lock,
         peer_pieces_tracking,
         peer_pieces_tracking_lock) = leecher_init(torrent, file, ip, port)


        # todo: announce the leecher to the tracker
        # todo: connect to other peer to download
        # todo: create the file to save
        # todo: update to the tracker periodically
        create_file(peer.file, get_file_length(peer.torrent))

        # peers will be shared with the talker
        # re_announcer will update this peers
        # talker will loop, and check for new
        # peers in new list
        interval, peers = started_announce(peer)
        peers_lock = threading.Lock()
        pprint.pprint(peers)

        # re_announcer
        re_announcer_thread = threading.Thread(target=re_announcer, args=(interval, peer, peers, peers_lock), daemon=True)
        re_announcer_thread.start()


        # talker
        talker_thread = threading.Thread(target=talker, args=(peer, peers, peers_lock, peer_pieces_tracking, peer_lock, peer_pieces_tracking_lock), daemon=True)
        talker_thread.start()

        # listener
        listener_thread = threading.Thread(target=listener, args=(peer, peer_pieces_tracking, peer_lock), daemon=True)
        listener_thread.start()

        progress_display(peer)

        while True:
            if is_download_completed(peer):
                print('')
                is_continue_to_seed = input('Download successfully, continue to seed? (yes/no): ')
                # todo: still let the seeder to continue to seed, handle later
                if is_continue_to_seed == 'no':
                    # stop the main thread
                    # cause listener to terminate
                    stop_announce(peer)
                    return
                else:
                    click.echo('Seeding...')
    except Exception as e:
        click.echo(SBC.APP_NAME + ': ' + str(e))


@cli.command()
@click.option('-t', '--torrent', required=True, type=str, help="Name of torrent")
@click.option('-f', '--file', required=True, type=str, help="Name of file saved")
@click.option('-ip', '--ip', required=True, type=str, help="IP address of peer")
@click.option('-p', '--port', required=True, type=int, help="Port of the peer")
def seed(torrent, file, ip, port):
    try:
        (peer,
         peer_lock,
         peer_pieces_tracking,
         peer_pieces_tracking_lock) = seeder_init(torrent, file, ip, port)


        # peers will be shared with the talker,
        interval, peers = started_announce(peer)
        peers_lock = threading.Lock()
        pprint.pprint(peers)

        # re_announcer
        re_announcer_thread = threading.Thread(target=re_announcer, args=(interval, peer, peers, peers_lock), daemon=True)
        re_announcer_thread.start()

        # listener
        listener_thread = threading.Thread(target=listener, args=(
            peer, peer_pieces_tracking, peer_lock), daemon=True)
        listener_thread.start()

        while True:
            if is_download_completed(peer):
                print('')
                is_continue_to_seed = input('Continue to seed? (yes/no): ')
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
        click.echo(SBC.APP_NAME + ': ' + str(e))


if __name__ == '__main__':
    cli()