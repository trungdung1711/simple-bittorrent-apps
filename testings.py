def get_piece_hash(pieces_bytes, piece_index):
    """Get the SHA-1 hash for a specific piece."""
    start = piece_index * 20
    end = start + 20
    return pieces_bytes[start:end]

file = 'C:/Users/Maxsys/OneDrive/Desktop/test.txt.torrent'

dictionary_test = {
    5 : 'five',
    6 : 'seven'
}
print(dictionary_test.items())