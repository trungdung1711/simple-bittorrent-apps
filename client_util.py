import hashlib
import json
import os
import threading
import time
import random
import string
import socket
import requests
import bencodepy
import math
from constants import SBC


def create_pieces_hash(file_path, piece_length):
    hashes = []
    with open(file_path, 'rb') as f:
        piece = f.read(piece_length)
        while piece:
            hashes.append(hashlib.sha1(piece).digest())
            piece = f.read(piece_length)
    return b''.join(hashes)


def create_torrent(file_path, ip, port, piece_length, destination_directory):
    file_size = os.path.getsize(file_path)
    file_name = os.path.basename(file_path)
    piece_hashes = create_pieces_hash(file_path, piece_length)

    info = {
        'name': file_name,
        'length': file_size,
        'piece length': piece_length,
        'pieces': piece_hashes
    }

    torrent_dict = {
        'announce': f'http://{ip}:{port}/announce',
        'created by': SBC.APP_NAME,
        'creation date': int(time.time()),
        'version': SBC.VERSION,
        'info': info
    }

    torrent_data = bencodepy.encode(torrent_dict)

    torrent_file = file_name + '.torrent'
    torrent_file_path = os.path.join(destination_directory, torrent_file)
    with open(torrent_file_path, 'wb') as f:
        f.write(torrent_data)


def get_torrent_dic_from_torrent_dic_bytes(torrent_dict_bytes):
    torrent_dic = {
        'announce': torrent_dict_bytes[b'announce'].decode('utf-8'),
        'created by': torrent_dict_bytes[b'created by'].decode('utf-8'),
        'creation date': torrent_dict_bytes[b'creation date'],
        'version': torrent_dict_bytes[b'version'].decode('utf-8'),
        'info': {
            'name': torrent_dict_bytes[b'info'][b'name'].decode('utf-8'),
            'length': torrent_dict_bytes[b'info'][b'length'],
            'piece length': torrent_dict_bytes[b'info'][b'piece length'],
            'pieces': torrent_dict_bytes[b'info'][b'pieces']
        }
    }
    return torrent_dic


def generate_peer_id(client_prefix='PC000'):
    """
    Generates a valid peer_id for BitTorrent clients. The peer_id is 20 bytes long.
    The first 5 characters are the client's name prefix, and the next 15 are random characters.

    Args:
        client_prefix (str): The prefix that represents the client name (default is '-PC000').

    Returns:
        str: A 20-character peer_id string.
    """
    # Ensure the prefix is 5 characters long
    if len(client_prefix) != 5:
        raise ValueError("Prefix must be exactly 5 characters long")
    # Generate 15 random alphanumeric characters
    random_suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=15))
    # Combine the prefix and the random suffix
    return client_prefix + random_suffix


def create_file(file, length):
    """
    Create a file with a specific total size, initialized with zero bytes.
    This simulates the space allocated for the entire file.
    """
    with open(file, 'wb') as f:
        f.write(b'\0' * length)


def get_info_hash(file):
    """
    Generates the info hash from the torrent file.
    Used for identifying the torrent's swarm
    :param file: the torrent file
    :return: info_hash of the torrent
    """
    with open(file, 'rb') as f:
        data = f.read()
        torrent_dic_bytes = bencodepy.decode(data)
        torrent_dic = get_torrent_dic_from_torrent_dic_bytes(torrent_dic_bytes)
        info = torrent_dic['info']
        info_hash = hashlib.sha1(bencodepy.encode(info)).digest()
    return info_hash


def get_torrent_dic(torrent):
    """
    Decode the torrent raw file into the torrent dictionary
    :param torrent: torrent file of the file
    :return: torrent dictionary
    """
    with open(torrent, 'rb') as f:
        data = f.read()
        torrent_dic_bytes = bencodepy.decode(data)
        torrent_dic = get_torrent_dic_from_torrent_dic_bytes(torrent_dic_bytes)
        return torrent_dic


def get_piece_length(file):
    torrent_dic = get_torrent_dic(file)
    return torrent_dic['info']['piece length']


def get_file_length(torrent):
    """
    Calculate the length of the file in bytes
    :param torrent: the torrent of the file
    :return: length of the file extracted from the torrent
    """
    torrent_dic = get_torrent_dic(torrent)
    return torrent_dic['info']['length']


def get_piece_number(file):
    length = get_file_length(file)
    piece_length = get_piece_length(file)
    return math.ceil(length / piece_length)


def get_announce(file):
    torrent_dic = get_torrent_dic(file)
    return torrent_dic['announce']


def get_piece_hash(piece_index, torrent):
    torrent_dic = get_torrent_dic(torrent)
    # byte object
    pieces_hash = torrent_dic['info']['pieces']
    # calculate the index (byte) of the piece hash
    start = 20 * piece_index
    return pieces_hash[start:start + 20]


def get_interest_piece_index(interest_request):
    return int(interest_request.split()[1])


def create_piece_hash(piece_data):
    """
    Calculates the piece hash of a piece_data.
    :param piece_data: piece_data to create piece hash
    :return: the hash of the piece data
    """
    return hashlib.sha1(piece_data).digest()


def verify_piece(piece_data, piece_index, torrent):
    calculated_piece_hash = create_piece_hash(piece_data)
    torrent_piece_hash = get_piece_hash(piece_index, torrent)
    return calculated_piece_hash == torrent_piece_hash


def write_piece(piece_data, piece_index, torrent, file):
    piece_length = get_piece_length(torrent)
    offset = piece_index * piece_length
    with open(file, 'r+b') as f:
        f.seek(offset)
        f.write(piece_data)


def first_announce(peer):
    """
    In the join function, first announce the tracker to tell
    the tracker that this peer will join the swarm.
    Also getting a list of other peers, who are in the swarm
    :param peer: the Peer object represent a peer
    :return: the interval to periodically announce, lists of dictionary Peer
    """
    response = requests.get(get_announce(peer.torrent), params=peer.get_params())
    if response.status_code == 200:
        interval = response.json()['interval']
        peers = response.json()['peers']
        return interval, peers
    else:
        raise Exception("Failed to first announce to tracker.")


def periodically_announce(peer):
    """
    Running by a thread, each interval, this function will send
    an announcement to the tracker to update its information and get a
    new list of peer and updating the list of peer
    :param peer: the Peer object represent a peer
    :return: nothing
    """
    # todo: periodically announce to the tracker
    value = 20


def is_download_completed(peer):
    return peer.left == 0


def update_peer_pieces_tracking_when_downloaded_one_piece(peer_pieces_tracking, peer_pieces_tracking_lock, piece_index):
    # todo, lock the peer_pieces_tracking and update the piece_index
    peer_pieces_tracking_lock.acquire()
    peer_pieces_tracking[piece_index] = 'AVAILABLE'
    peer_pieces_tracking_lock.release()


def update_peer_when_downloaded_one_piece(peer, peer_lock):
    peer_lock.acquire()
    peer.downloaded = peer.downloaded + 1
    peer.left = peer.left - 1
    peer.event = None
    peer_lock.release()


def update_peer_pieces_tracking_when_choose_to_download_one_piece(peer_pieces_tracking, peer_pieces_tracking_lock, piece_index):
    peer_pieces_tracking_lock.acquire()
    peer_pieces_tracking[piece_index] = 'DOWNLOADING'
    peer_pieces_tracking_lock.release()


def update_peer_pieces_tracking_when_verification_failed(peer_pieces_tracking, peer_pieces_tracking_lock, piece_index):
    peer_pieces_tracking_lock.acquire()
    peer_pieces_tracking[piece_index] = 'UNAVAILABLE'
    peer_pieces_tracking_lock.release()


def receive_full_server_peer_pieces_tracking(peer_client_socket):
    # Initialize an empty byte string to store the incoming data
    full_data = b''  # This will accumulate all the data we receive

    while True:
        # Receive data in chunks, let's assume 1024 bytes at a time
        chunk = peer_client_socket.recv(1024)

        if not chunk:
            # If chunk is empty, the connection has been closed
            raise ValueError("Connection closed unexpectedly")

        # Append the chunk to the full_data
        full_data += chunk

        try:
            # Attempt to decode and parse the data as JSON
            json_data = full_data.decode('utf-8')  # Decode bytes to string
            parsed_json = json.loads(json_data)  # Parse the string into a JSON object

            return parsed_json  # Return the parsed JSON object if successful

        except (UnicodeDecodeError, json.JSONDecodeError):
            # If decoding or JSON parsing fails, the message is not complete yet
            # So, continue to receive more data until it is complete
            continue


def get_request_type(request_message):
    if request_message == 'HAVING':
        return 'HAVING'
    elif request_message == 'DONE':
        return 'DONE'
    else:
        return 'INTEREST'


def update_peer_when_uploaded_one_piece(peer, peer_lock):
    peer_lock.acquire()
    peer.uploaded = peer.uploaded + 1
    peer.event = None
    peer_lock.release()


def accept_connections_from_peers(ip, port, peer, peer_pieces_tracking, peer_lock):
    # todo: a thread that accepts the connection from peers
    peer_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_server_socket.bind((ip, port))
    peer_server_socket.listen(10)
    while True:
        peer_client_socket, addr = peer_server_socket.accept()
        peer_client_handle_thread = threading.Thread(target=handle_connection_from_peer, args=(peer, peer_client_socket, peer_pieces_tracking, peer_lock))
        peer_client_handle_thread.daemon = True
        peer_client_handle_thread.start()


def handle_done_request(peer_client_socket):
    # todo: send back the acknowledgement and close the socket
    done_response = 'DONE_OK'
    peer_client_socket.send(done_response.encode('utf-8'))
    peer_client_socket.close()


def handle_interest_request(peer, peer_client_socket, interest_request, peer_lock):
    piece_index = get_interest_piece_index(interest_request)
    # todo: send the piece back to the peer client
    with open(peer.file, 'rb') as f:
        read_index = piece_index * get_piece_length(peer.torrent)
        f.seek(read_index)
        piece_data = f.read(get_piece_length(peer.torrent))
        peer_client_socket.send(piece_data)
    update_peer_when_uploaded_one_piece(peer, peer_lock)


def handle_having_request(peer_client_socket, peer_pieces_tracking):
    peer_client_socket.send(json.dumps(peer_pieces_tracking).encode('utf-8'))


##############################object
def handle_connection_from_peer(peer, peer_client_socket, peer_pieces_tracking, peer_lock):
    # todo: thread that instantly receive requests from a peer
    buffer = ""
    while True:
        # Receive data and append to buffer
        data = peer_client_socket.recv(1024).decode('utf-8')
        if not data:
            break  # Client closed connection

        buffer += data

        # Process all complete messages in the buffer
        while "\n" in buffer:
            # Split the buffer on the newline delimiter
            request_message, buffer = buffer.split("\n", 1)

            print('CHECK ' + request_message)

            request_type = get_request_type(request_message)
            if request_type == 'DONE':
                handle_done_request(peer_client_socket)
                return
            elif request_type == 'HAVING':
                handle_having_request(peer_client_socket, peer_pieces_tracking)
            elif request_type == 'INTEREST':
                handle_interest_request(peer, peer_client_socket, request_message, peer_lock)


def send_having_request(peer_client_socket):
    peer_client_socket.send('HAVING\n'.encode('utf-8'))
    server_peer_pieces_tracking = receive_full_server_peer_pieces_tracking(peer_client_socket)
    # todo: in the form as {'0': 'AVAILABLE'}
    # todo: convert back to indexable form
    server_peer_pieces_tracking = {int(k) : v for k, v in server_peer_pieces_tracking.items()}
    return server_peer_pieces_tracking


def send_interest_request(client_peer, peer_client_socket, peer_pieces_tracking, server_peer_pieces_tracking, client_peer_lock, peer_pieces_tracking_lock, server_peer):
    for i in range(get_piece_number(client_peer.torrent)):
        if server_peer_pieces_tracking[i] == 'AVAILABLE' and peer_pieces_tracking[i] == 'UNAVAILABLE':
            update_peer_pieces_tracking_when_choose_to_download_one_piece(peer_pieces_tracking, peer_pieces_tracking_lock, i)
            interest_message = f'INTEREST {i}\n'
            peer_client_socket.send(interest_message.encode('utf-8'))
            piece_data = peer_client_socket.recv(get_piece_length(client_peer.torrent))
            if verify_piece(piece_data, i, client_peer.torrent):
                # todo: write piece_data to the file
                write_piece(piece_data, i, client_peer.torrent, client_peer.file)
                # todo: update the piece_pieces_tracking
                update_peer_when_downloaded_one_piece(client_peer, client_peer_lock)
                update_peer_pieces_tracking_when_downloaded_one_piece(peer_pieces_tracking, peer_pieces_tracking_lock, i)
                print(f'Getting piece {i} from {server_peer['peer_id']}')
            else:
                # todo: mark the piece as UNAVAILABLE and skip it
                print(f'PIECE {i} is wrong, skip this one')
                update_peer_pieces_tracking_when_verification_failed(peer_pieces_tracking, peer_pieces_tracking_lock, i)


def send_having_and_interest_request(client_peer, peer_client_socket, peer_pieces_tracking, client_peer_lock, peer_pieces_tracking_lock, server_peer):
    while not is_download_completed(client_peer):

        server_peer_pieces_tracking = send_having_request(peer_client_socket)

        send_interest_request(client_peer, peer_client_socket, peer_pieces_tracking, server_peer_pieces_tracking, client_peer_lock, peer_pieces_tracking_lock, server_peer)


def send_done_request(peer_client_socket):
    done_message = 'DONE\n'
    peer_client_socket.send(done_message.encode('utf-8'))
    done_message_received = peer_client_socket.recv(1024).decode('utf-8')
    if done_message_received == 'DONE_OK':
        peer_client_socket.close()


############################object########peer dictionary
def connect_to_server_peer(client_peer, server_peer, peer_pieces_tracking, peer_pieces_tracking_lock, client_peer_lock):
    # todo: connect to a server peer
    peer_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    peer_client_socket.connect((server_peer['peer_ip'], server_peer['peer_port']))

    # todo: starting downloading
    # todo: instantly send the HAVING, INTEREST message to the server
    send_having_and_interest_request(client_peer, peer_client_socket, peer_pieces_tracking, client_peer_lock, peer_pieces_tracking_lock, server_peer)
    # todo: downloading done, stop connect to the server
    send_done_request(peer_client_socket)


###############################obj####list of dictionary
def create_connections_to_server_peers(peer, peers, peer_pieces_tracking, peer_lock, peer_pieces_tracking_lock):
    for server_peer in peers:
        # todo: create the connection to each of the peer except yourself
        if server_peer['peer_id'] != peer.peer_id:
            connect_to_server_peer_thread = threading.Thread(target=connect_to_server_peer, args=(peer, server_peer, peer_pieces_tracking, peer_pieces_tracking_lock, peer_lock))
            connect_to_server_peer_thread.daemon = True
            print(f'Request pieces from {server_peer["peer_id"]}')
            connect_to_server_peer_thread.start()


class Peer:
    def __init__(self, torrent, file, ip, port):
        self.torrent = torrent
        self.file = file
        self.info_hash = get_info_hash(torrent)    # The hash of the torrent's "info" part (file's metadata)
        self.peer_id = generate_peer_id()       # A unique ID identifying this peer (can be generated randomly)
        self.peer_ip = ip                       # The ip address on the peer's machine
        self.peer_port = port                   # The port on which the peer is listening for connections
        self.uploaded = 0                       # The amount of data uploaded (can be set to 0 for initial announce)
        self.downloaded = 0                     # The amount of data downloaded (can be set to 0 for initial announce)
        self.left = 0                           # The amount of data left to download (0 for a seeder since it's already finished)
        self.event = 'started'                  # Event type; 'started' means the seeder has started sharing the file


    def get_params(self):
        params = {
            'info_hash': self.info_hash,
            'peer_id': self.peer_id,
            'peer_ip': self.peer_ip,
            'peer_port': self.peer_port,
            'uploaded': self.uploaded,
            'downloaded': self.downloaded,
            'left': self.left,
            'event': self.event
        }
        return params


    def init_seeder(self):
        self.uploaded = 0
        self.downloaded = 0
        self.left = 0
        self.event = 'started'


    def init_leecher(self):
        self.uploaded = 0
        self.downloaded = 0
        self.left = get_piece_number(self.torrent)
        self.event = 'started'