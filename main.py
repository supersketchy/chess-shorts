import pandas as pd
import os
from dotenv import load_dotenv
import chess
import chess.svg
import cairosvg
from moviepy import ImageSequenceClip
import shutil
import datetime
from pathlib import Path

TEMP_PNG_DIR_NAME = "temp_pngs"
OUTPUT_DIR_NAME = "outputs"
VIDEO_FPS = 1

def load_csv_path() -> str:
    load_dotenv()
    csv_path = os.getenv("CSV_FILE_PATH")
    if not csv_path:
        raise ValueError("CSV_FILE_PATH environment variable not set.")
    return csv_path

def read_puzzles(file_path: str) -> pd.DataFrame:
    column_names = [
        "PuzzleId", "FEN", "Moves", "Rating", "RatingDeviation",
        "Popularity", "NbPlays", "Themes", "GameUrl", "OpeningTags",
    ]
    return pd.read_csv(file_path, names=column_names, header=0)

def get_puzzle_data(df: pd.DataFrame, index: int) -> tuple[str, list[str]]:
    puzzle = df.iloc[index]
    fen = puzzle["FEN"]
    moves_str = puzzle["Moves"]
    uci_moves = moves_str.split(' ')
    return fen, uci_moves

def prepare_directory(dir_path: Path) -> Path:
    if dir_path.exists():
        shutil.rmtree(dir_path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def generate_board_states(fen: str, uci_moves: list[str]):
    board = chess.Board(fen)
    yield board.copy(), None
    for uci_move in uci_moves:
        move = chess.Move.from_uci(uci_move)
        if move in board.legal_moves:
            board.push(move)
            yield board.copy(), move

def save_board_as_png(board: chess.Board, last_move: chess.Move | None, file_path: Path):
    svg_data = chess.svg.board(board=board, lastmove=last_move)
    cairosvg.svg2png(bytestring=svg_data.encode('utf-8'), write_to=str(file_path))

def generate_png_sequence(fen: str, uci_moves: list[str], temp_dir: Path) -> list[str]:
    board_states = generate_board_states(fen, uci_moves)
    png_files = []
    for frame_num, (board, move) in enumerate(board_states):
        png_path = temp_dir / f"frame_{frame_num:03d}.png"
        save_board_as_png(board, move, png_path)
        png_files.append(str(png_path))
    return png_files

def create_video(image_paths: list[str], output_path: Path, fps: int):
    if not image_paths:
        return
    clip = ImageSequenceClip(image_paths, fps=fps)
    clip.write_videofile(str(output_path), codec='libx264', logger=None)
    clip.close()

def cleanup(dir_path: Path):
    if dir_path.exists():
        shutil.rmtree(dir_path)

def generate_timestamped_output_path(base_dir: Path, prefix: str, suffix: str) -> Path:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return base_dir / f"{prefix}_{timestamp}{suffix}"

def main():
    temp_dir_path = Path(TEMP_PNG_DIR_NAME)
    output_dir_path = Path(OUTPUT_DIR_NAME)
    puzzle_index_to_process = 0

    csv_path = load_csv_path()
    df = read_puzzles(csv_path)
    fen, uci_moves = get_puzzle_data(df, puzzle_index_to_process)

    prepare_directory(temp_dir_path)
    png_files = generate_png_sequence(fen, uci_moves, temp_dir_path)

    if png_files:
        output_video_path = generate_timestamped_output_path(
            output_dir_path, "youtube_short", ".mp4"
        )
        create_video(png_files, output_video_path, VIDEO_FPS)
        print(f"Generated video and saved to {output_video_path}")

    cleanup(temp_dir_path)

if __name__ == "__main__":
    main()
