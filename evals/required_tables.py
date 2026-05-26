"""
maps each golden question id -> the set of REAL chinook tables needed to answer it.
used to measure retrieval recall: did the retriever fetch the tables the question needs?

hand-labeled. this IS the ground truth for retrieval quality, so it's worth getting right.
"""

REQUIRED_TABLES = {
    1: {"Artist"},
    2: {"Artist"},
    3: {"Track"},
    4: {"Genre", "Track"},
    5: {"Customer", "Invoice"},
    6: {"Invoice"},
    7: {"Track"},
    8: {"Album", "Track"},
    9: {"Artist", "Album"},
    10: {"Invoice"},
    11: {"Invoice"},
    12: {"Invoice"},
    13: {"Customer"},
    14: {"Employee"},
    15: {"Genre", "Track", "InvoiceLine"},
    16: {"Playlist", "PlaylistTrack"},
    17: {"Customer", "Invoice"},
    18: {"Track"},
    19: {"Track"},
    20: {"Employee", "Customer"},
    21: {"Track", "Genre"},
    22: {"Customer"},
    23: {"Album", "Track", "InvoiceLine"},
    24: {"Track", "Genre"},
    25: {"Customer", "Invoice"},
    26: {"Track"},
    27: {"Artist", "Album"},
    28: {"Invoice"},
    29: {"Invoice", "Customer"},
    30: {"Track", "Genre"},
}