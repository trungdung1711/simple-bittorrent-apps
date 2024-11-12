from tracker_util import Peer, TRACKER
from flask import Flask, request, jsonify
import threading

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello, World!'


#dictionary
#{
#   'info_hash': [list of peers (object)],
#   'info_hash': [list of peers (object)]
#}
peers_db = {}


@app.route('/announce', methods=['GET'])
def announce():
    # Step 1: Parse the announcement request parameters, create
    # Peer object
    peer = Peer()
    peer.__setattr__('info_hash', request.args.get('info_hash'))
    peer.__setattr__('peer_id', request.args.get('peer_id'))
    peer.__setattr__('peer_ip', request.args.get('peer_ip'))
    peer.__setattr__('peer_port', int(request.args.get('peer_port')))
    peer.__setattr__('uploaded', int(request.args.get('uploaded')))
    peer.__setattr__('downloaded', int(request.args.get('downloaded')))
    peer.__setattr__('left', int(request.args.get('left')))
    peer.__setattr__('event', request.args.get('event'))

    # Step 2: Validate required parameters
    if (not peer.info_hash) or (not peer.peer_id) or (peer.peer_port <= 0):
        app.logger.info('Announce unsuccessful')
        return "Announce unsuccessfully", 400

    # Step 3: Handle the event (e.g., started, stopped, completed)
    if peer.event == 'stopped':
        # Handle peer stopping (remove from peers list)
        peers_db[peer.info_hash] = [peer_mem for peer_mem in peers_db[peer.info_hash] if peer_mem.peer_id != peer.peer_id]
        app.logger.info(f'Peer {peer.peer_id} stopped')
        return "Peer stopped", 200

    if peer.event == 'started':
        # Handle a new peer starting (seeder or downloader)
        # If this is the first peer, case of seeder
        # Create an empty list
        if peer.info_hash not in peers_db:
            peers_db[peer.info_hash] = []

        # Add the peer to the list of active peers for this info_hash
        peers_db[peer.info_hash].append(peer)
        app.logger.info(f"Added new peer: {peer.peer_id} in the swarm {peer.info_hash}")

    if not peer.event :
        # Case periodically announcement
        # Update the peer
        for stored_peer in peers_db[peer.info_hash]:
            if stored_peer.peer_id == peer.peer_id:
                app.logger.info(f'Updated peer {peer.peer_id} in the swarm {peer.info_hash}')
                stored_peer.update(peer)

    # Step 4: Return the peer list for this info_hash
    # Here we return a list of peers that are currently
    # part of the swarm
    peers = peers_db.get(peer.info_hash)
    # Convert to a list of dictionary
    peers = [peer.to_dict() for peer in peers]

    # Step 5: Construct response
    response = {
        'interval': TRACKER.TIME_TO_ANNOUNCE,
        'peers': peers
    }

    return jsonify(response), 200


# @app.route('/api/v1/repo', methods=['POST'])
# def repo():
#     file = request.files['torrent']
#     file.save(f'./repo/{file.filename}')
#     return TRACKER.OK, 200


# Start the Flask server with threaded support
def run_server():
    app.run(host='0.0.0.0', port=80, threaded=True)

# Run the Flask server in a new thread
if __name__ == '__main__':
    server_thread = threading.Thread(target=run_server)
    server_thread.start()
