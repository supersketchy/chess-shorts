from typing import List, Iterator, Tuple, Optional
from pathlib import Path
import chess
import chess.svg
import cairosvg


def generate_board_states(
    fen: str, moves: List[str]
) -> Iterator[Tuple[chess.Board, Optional[chess.Move]]]:
    """Generate chess board states for given FEN and moves.

    Args:
        fen: str - Starting FEN string
        moves: List[str] - List of moves in UCI format

    Yields:
        Tuple[chess.Board, Optional[chess.Move]]: Board state and last move
    """
    board = chess.Board(fen)
    yield board.copy(), None
    for uci_move in moves:
        move = chess.Move.from_uci(uci_move)
        board.push(move)
        yield board.copy(), move


def render_board_sequence(fen: str, moves: List[str], output_dir: Path) -> List[str]:
    """Generate PNG sequence from chess moves.

    Args:
        fen: str - Starting FEN string
        moves: List[str] - List of UCI moves
        output_dir: Path - Directory to save PNG files

    Returns:
        List[str]: List of PNG file paths
    """
    png_files = []
    for frame_num, (board, move) in enumerate(generate_board_states(fen, moves)):
        png_path = output_dir / f"frame_{frame_num:03d}.png"
        svg_data = chess.svg.board(board=board, lastmove=move)
        cairosvg.svg2png(bytestring=svg_data.encode("utf-8"), write_to=str(png_path))
        png_files.append(str(png_path))
    return png_files
