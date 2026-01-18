from io import BytesIO
import chess
import chess.svg
import cairosvg
from PIL import Image
import numpy as np
from numpy.typing import NDArray


def render_board_sequence(fen: str, moves: list[str]) -> list[NDArray[np.uint8]]:
    """Generate numpy array sequence from chess position and moves.

    Args:
        fen (str): Starting position in FEN notation.
        moves (list[str]): List of UCI format moves.

    Returns:
        list[NDArray[np.uint8]]: List of RGB numpy arrays for each frame.
    """
    board = chess.Board(fen)
    frames = [_render_board(board)]

    for uci_move in moves:
        move = chess.Move.from_uci(uci_move)
        board.push(move)
        frames.append(_render_board(board, move))

    return frames


def _render_board(board: chess.Board, lastmove: chess.Move | None = None) -> NDArray[np.uint8]:
    """Render a single board state to numpy array.

    Args:
        board (chess.Board): Current board state.
        lastmove (chess.Move | None): Last move for highlighting.

    Returns:
        NDArray[np.uint8]: RGB numpy array of the board.
    """
    svg_data = chess.svg.board(board=board, lastmove=lastmove)
    png_bytes = cairosvg.svg2png(bytestring=svg_data.encode())
    image = Image.open(BytesIO(png_bytes)).convert("RGB")
    return np.array(image)
