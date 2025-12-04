
"""
Chess Middlegame Book
Contains common middlegame patterns and typical plans
"""

MIDDLEGAME_PATTERNS = {
    # Typical middlegame positions with thematic moves
    # These are examples - in practice you'd have many more
    
    # Isolated Queen's Pawn positions
    "r1bq1rk1/pp1nbppp/2p1pn2/3p4/2PP4/2N1PN2/PP2BPPP/R1BQ1RK1 w - - 0 9": ["d4d5"],
    
    # Minority attack in QGD Exchange
    "r1bq1rk1/pp1nbppp/2p1pn2/3p4/2PP4/2N1PN2/PP2BPPP/R1BQK2R w KQ - 0 9": ["b2b4"],
}

def get_middlegame_move(fen: str, moves_count: int) -> str:
    """Get a book move for middlegame position"""
    import random
    
    # Only use middlegame book between moves 10-30
    if 10 <= moves_count <= 30 and fen in MIDDLEGAME_PATTERNS:
        moves = MIDDLEGAME_PATTERNS[fen]
        return random.choice(moves) if isinstance(moves, list) else moves
    return None
