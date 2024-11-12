def to_peer(peer):
    new_peer = Peer()
    new_peer.info_hash = peer['info_hash']
    new_peer.peer_id = peer['peer_id']
    new_peer.peer_ip = peer['peer_ip']
    new_peer.peer_port = peer['peer_port']
    new_peer.uploaded = peer['uploaded']
    new_peer.downloaded = peer['downloaded']
    new_peer.left = peer['left']
    new_peer.event = peer['event']
    return new_peer


class Peer:
    def __init__(self):
        self.info_hash = None
        self.peer_id = 'default'
        self.peer_ip = 'default'
        self.peer_port = 'default'
        self.uploaded = 0                       # The amount of data uploaded (can be set to 0 for initial announce)
        self.downloaded = 0                     # The amount of data downloaded (can be set to 0 for initial announce)
        self.left = 0                           # The amount of data left to download (0 for a seeder since it's already finished)
        self.event = 'started'                  # Event type; 'started' means the seeder has started sharing the file


    def update(self, peer):
        self.info_hash = peer.info_hash
        self.peer_id = peer.peer_id
        self.peer_ip = peer.peer_ip
        self.peer_port = peer.peer_port
        self.uploaded = peer.uploaded
        self.downloaded = peer.downloaded
        self.left = peer.left
        self.event = peer.event


    def to_dict(self):
        return {
            'info_hash': self.info_hash,
            'peer_id': self.peer_id,
            'peer_ip': self.peer_ip,
            'peer_port': self.peer_port,
            'uploaded': self.uploaded,
            'downloaded': self.downloaded,
            'left': self.left,
            'event': self.event
        }


class TRACKER:
    TIME_TO_ANNOUNCE=1800