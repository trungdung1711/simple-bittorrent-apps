
# Simple BitTorrent Application

This is a simple implementation of a BitTorrent-like system consisting of a **Tracker** and **Peers** (Seeder/Leecher). The tracker manages file sharing metadata, while peers upload or download files.

---

## Features
- **Tracker**: Keeps track of files, peers, and availability.
- **Peer (Seeder/Leecher)**: Downloads or uploads pieces of files to/from other peers.
- **Provide**: multi-threaded application, each of peer can serer as a server and 

---

## Prerequisites
- Python 3.7 or above
- pip install -r requirements.txt
- Socket programming basics

---

## Components

### 1. **Tracker**
The tracker acts as the central server, managing peer information and file metadata.

#### Tracker Source Code
```python
# simple_bittorrent_tracker.py
from simple_tracker.cleaner import cleaner
from simple_tracker.util import SimpleTracker, announce_parse_request, announce_handler_lack_info, \
    announce_handler_stopped_event, announce_handler_started_event, announce_handler_re_announce_event, \
    announce_handler_swarm_response
from flask import Flask, jsonify
import threading
import logging

simple_bittorrent_tracker = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("announce")


# DICTIONARY
#   {
#       'info_hash': [list of peers (object)],
#       'info_hash': [list of peers (object)]
#   }
peers_db = {}
peers_db_lock = threading.Lock()

@simple_bittorrent_tracker.route('/', methods=['GET'])
def test():
    return 'Hello', 200


@simple_bittorrent_tracker.route('/announce', methods=['GET'])
def announce():
    peer = announce_parse_request()

    announce_handler_lack_info(peer)

    # STOPPED event
    if peer.event == SimpleTracker.EVENT_LIST[1]:
        announce_handler_stopped_event(peers_db, peers_db_lock, peer)
        return "Peer stopped", 200

    # STARTED event
    elif peer.event == SimpleTracker.EVENT_LIST[0]:
        announce_handler_started_event(peers_db, peers_db_lock, peer)

    # RE_ANNOUNCE event
    elif peer.event == SimpleTracker.EVENT_LIST[2]:
        announce_handler_re_announce_event(peers_db, peers_db_lock, peer)

    # response the swarms
    return jsonify(announce_handler_swarm_response(peer, peers_db, peers_db_lock)), 200


# Start the Flask server with threaded support
def run():
    simple_bittorrent_tracker.run(host='0.0.0.0', port=80, threaded=True)


# Run the Flask server in a new thread
if __name__ == '__main__':
    server_thread = threading.Thread(target=run)
    server_thread.start()
    cleaner_thread = threading.Thread(target=cleaner, args=(peers_db, peers_db_lock), daemon=True)
    cleaner_thread.start()
```

---

### 2. **Peer (Seeder/Leecher)**
Peers upload and download files by communicating with the tracker and other peers.

#### Peer Source Code
```python
# simple_bittorrent_client.py
from simple_tracker.cleaner import cleaner
from simple_tracker.util import SimpleTracker, announce_parse_request, announce_handler_lack_info, \
    announce_handler_stopped_event, announce_handler_started_event, announce_handler_re_announce_event, \
    announce_handler_swarm_response
from flask import Flask, jsonify
import threading
import logging

simple_bittorrent_tracker = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("announce")


# DICTIONARY
#   {
#       'info_hash': [list of peers (object)],
#       'info_hash': [list of peers (object)]
#   }
peers_db = {}
peers_db_lock = threading.Lock()

@simple_bittorrent_tracker.route('/', methods=['GET'])
def test():
    return 'Hello', 200


@simple_bittorrent_tracker.route('/announce', methods=['GET'])
def announce():
    peer = announce_parse_request()

    announce_handler_lack_info(peer)

    # STOPPED event
    if peer.event == SimpleTracker.EVENT_LIST[1]:
        announce_handler_stopped_event(peers_db, peers_db_lock, peer)
        return "Peer stopped", 200

    # STARTED event
    elif peer.event == SimpleTracker.EVENT_LIST[0]:
        announce_handler_started_event(peers_db, peers_db_lock, peer)

    # RE_ANNOUNCE event
    elif peer.event == SimpleTracker.EVENT_LIST[2]:
        announce_handler_re_announce_event(peers_db, peers_db_lock, peer)

    # response the swarms
    return jsonify(announce_handler_swarm_response(peer, peers_db, peers_db_lock)), 200


# Start the Flask server with threaded support
def run():
    simple_bittorrent_tracker.run(host='0.0.0.0', port=80, threaded=True)


# Run the Flask server in a new thread
if __name__ == '__main__':
    server_thread = threading.Thread(target=run)
    server_thread.start()
    cleaner_thread = threading.Thread(target=cleaner, args=(peers_db, peers_db_lock), daemon=True)
    cleaner_thread.start()
```

---

## How to Run

### Step 1: Run the Tracker
Start the tracker to listen for peer announcements.
```bash
python simple_bittorrent_tracker.py
```

### Step 2: Start Peers
Run multiple instances of the peer script. Some peers act as seeders, while others act as leechers with specific command like [torrent], [seed], [join]
```bash
python simple_bittorrent_peer.py
```


## Notes
- This implementation is a simplified model and does not handle:
  - Complex peer communication
  - Advanced error handling
  - Authentication and authorisation

---
