#Piece length as Bytes
PIECE_LENGTH = 512 * 1024


class TRACKER:
    IP = '192.168.0.101'
    PORT = 80
    URL = f'http://{IP}:{PORT}'
    OK = 'TRACKER_OK'


class SBC:
    APP_NAME= 'Simple Bittorrent CLI'
    VERSION = '1.0.0'