import time

from simple_tracker.util import SimpleTracker


def is_over_threshold(peer):
    if int(time.time()) - peer.last_announce_time >= SimpleTracker.THRESHOLD:
        return True
    return False


def cleaner(peers_db, peers_db_lock):
    while True:
        # for every CHECKING_TIME
        time.sleep(SimpleTracker.CHECKING_TIME)
        # For each of the swarm
        with peers_db_lock:
            for info_hash, swarm in peers_db.items():
                # For each of the peer in the swarm
                for peer in swarm:
                    if is_over_threshold(peer):
                        # exclude that peer out of the swarm
                        peers_db[peer.info_hash] = [peer_mem for peer_mem in peers_db[peer.info_hash] if
                                                           peer_mem.peer_id != peer.peer_id]
                        # after excluding, if the swarm is empty
                        if not peers_db[peer.info_hash]:
                            # delete that entry of the swarm
                            del peers_db[peer.info_hash]