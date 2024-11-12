import sys
import time

from client_util import get_piece_number


def progress_bar(left, total_pieces, bar_length=40):
    # Calculate the download progress
    downloaded_pieces = total_pieces - left
    progress = downloaded_pieces / total_pieces

    # Create the bar, percentage of bar
    block = int(round(bar_length * progress))
    bar = "#" * block + "-" * (bar_length - block)

    # Display the bar with the percentage
    sys.stdout.write(f"\rDownloading: [{bar}] {progress * 100:.2f}%")
    sys.stdout.flush()


def progress_display(peer):
    # skip by seeder because left = 0
    while peer.left > 0:
        time.sleep(0.5)
        # Display the progress bar
        progress_bar(peer.left, get_piece_number(peer.torrent))