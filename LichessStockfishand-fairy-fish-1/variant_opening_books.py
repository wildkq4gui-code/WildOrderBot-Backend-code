
"""
Chess Variant Opening Books
Contains opening knowledge for Crazyhouse, Chess960, King of the Hill, 
Three-check, Antichess, Atomic, Horde, and Racing Kings
"""

import random

# Crazyhouse Opening Book
CRAZYHOUSE_BOOK = {
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[] w KQkq - 0 1": ["e2e4", "d2d4", "g1f3"],
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR[] b KQkq e3 0 1": ["e7e5", "c7c5", "g8f6"],
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR[] w KQkq e6 0 2": ["g1f3", "b1c3", "f1c4"],
}

# King of the Hill Opening Book
KING_OF_THE_HILL_BOOK = {
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1": ["e2e4", "d2d4", "g1f3"],
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1": ["e7e5", "d7d5", "g8f6"],
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2": ["g1f3", "d2d4", "b1c3"],
}

# Three-check Opening Book
THREE_CHECK_BOOK = {
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 3+3 0 1": ["e2e4", "g1f3", "d2d4"],
    "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 3+3 0 1": ["e7e5", "g8f6", "d7d5"],
    "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 3+3 0 2": ["g1f3", "f1c4", "d2d4"],
}

# Antichess Opening Book
ANTICHESS_BOOK = {
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1": ["e2e3", "d2d3", "g1f3"],
    "rnbqkbnr/pppppppp/8/8/8/4P3/PPPP1PPP/RNBQKBNR b - - 0 1": ["b7b6", "g8f6", "e7e6"],
    "rnbqkbnr/p1pppppp/1p6/8/8/4P3/PPPP1PPP/RNBQKBNR w - - 0 2": ["f1a6", "d1h5", "f1b5"],
}

# Atomic Opening Book
ATOMIC_BOOK = {
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1": ["g1f3", "e2e3", "d2d4"],
    "rnbqkbnr/pppppppp/8/8/8/5N2/PPPPPPPP/RNBQKB1R b KQkq - 1 1": ["g8f6", "e7e6", "d7d5"],
    "rnbqkbnr/pppppppp/8/8/3P4/8/PPP1PPPP/RNBQKBNR b KQkq d3 0 1": ["g8f6", "e7e6", "d7d5"],
}

# Horde Opening Book
HORDE_BOOK = {
    "rnbqkbnr/pppppppp/8/1PP2PP1/PPPPPPPP/PPPPPPPP/PPPPPPPP/PPPPPPPP w kq - 0 1": ["e5e6", "a5a6", "h5h6"],
    "rnbqkbnr/pppppppp/4P3/1PP2PP1/PPPPPPPP/PPPPPPPP/PPPPPPPP/PPPPPPPP b kq - 0 1": ["d7e6", "f7e6"],
}

# Racing Kings Opening Book
RACING_KINGS_BOOK = {
    "8/8/8/8/8/8/krbnNBRK/qrbnNBRQ w - - 0 1": ["b2c3", "f2e3", "h2g3"],
    "8/8/8/8/8/2N5/krbn1BRK/qrbnNBRQ b - - 1 1": ["b1c2", "a1b2", "c1d2"],
}

# Chess960 uses standard opening principles
CHESS960_BOOK = {
    # Generic Chess960 principles - develop pieces, control center
}

def get_variant_opening_move(variant: str, fen: str) -> str:
    """Get a book move for the given variant and position"""
    if variant == 'crazyhouse':
        book = CRAZYHOUSE_BOOK
    elif variant == 'kingOfTheHill':
        book = KING_OF_THE_HILL_BOOK
    elif variant == 'threeCheck':
        book = THREE_CHECK_BOOK
    elif variant == 'antichess':
        book = ANTICHESS_BOOK
    elif variant == 'atomic':
        book = ATOMIC_BOOK
    elif variant == 'horde':
        book = HORDE_BOOK
    elif variant == 'racingKings':
        book = RACING_KINGS_BOOK
    elif variant == 'chess960':
        book = CHESS960_BOOK
    else:
        return None
    
    if fen in book:
        moves = book[fen]
        return random.choice(moves) if isinstance(moves, list) else moves
    return None
