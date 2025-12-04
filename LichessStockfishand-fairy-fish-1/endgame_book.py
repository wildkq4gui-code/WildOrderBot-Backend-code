
"""
Chess Endgame Book
Contains endgame tablebase-like knowledge for common endgame positions
"""

ENDGAME_BOOK = {
    # King and Pawn endgames - these are position-specific examples
    # In practice, you'd want many more positions
    
    # Lucena position (winning)
    "8/8/8/8/1k6/8/1P6/1K6 w - - 0 1": ["b1c2"],
    
    # Philidor position (drawing technique)
    "8/8/8/8/4k3/8/4P3/4K3 b - - 0 1": ["e4d5"],
    
    # King opposition
    "8/8/8/3k4/8/3K4/8/8 w - - 0 1": ["d3d4"],
}

def is_endgame(board) -> bool:
    """Determine if position is an endgame based on material"""
    import chess
    
    # Count pieces (excluding kings and pawns)
    white_pieces = sum(1 for piece in board.piece_map().values() 
                      if piece.color == chess.WHITE and piece.piece_type not in [chess.KING, chess.PAWN])
    black_pieces = sum(1 for piece in board.piece_map().values() 
                      if piece.color == chess.BLACK and piece.piece_type not in [chess.KING, chess.PAWN])
    
    # Endgame if total pieces <= 6 or queens are off
    total_pieces = white_pieces + black_pieces
    has_queen = any(piece.piece_type == chess.QUEEN for piece in board.piece_map().values())
    
    return total_pieces <= 6 or (total_pieces <= 10 and not has_queen)

def get_endgame_move(fen: str) -> str:
    """Get a book move for endgame position"""
    import random
    if fen in ENDGAME_BOOK:
        return random.choice(ENDGAME_BOOK[fen]) if isinstance(ENDGAME_BOOK[fen], list) else ENDGAME_BOOK[fen]
    return None
