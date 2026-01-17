from pathlib import Path
import chess
import chess.svg
import cairosvg


def render_board_sequence(fen: str, moves: list[str], output_dir: Path) -> list[str]:
    """Generate PNG sequence from chess position and moves.

    Args:
        fen (str): Starting position in FEN notation.
        moves (list[str]): List of UCI format moves.
        output_dir (Path): Directory to save PNG files.

    Returns:
        list[str]: Paths to generated PNG files.
    """
    board = chess.Board(fen)
    png_files = []

    svg_data = chess.svg.board(board=board)
    png_path = output_dir / "frame_000.png"
    cairosvg.svg2png(bytestring=svg_data.encode(), write_to=str(png_path))
    png_files.append(str(png_path))

    for i, uci_move in enumerate(moves, 1):
        move = chess.Move.from_uci(uci_move)
        board.push(move)
        svg_data = chess.svg.board(board=board, lastmove=move)
        png_path = output_dir / f"frame_{i:03d}.png"
        cairosvg.svg2png(bytestring=svg_data.encode(), write_to=str(png_path))
        png_files.append(str(png_path))

    return png_files
