import pandas as pd
import os
from dotenv import load_dotenv
import chess
import chess.svg
import cairosvg
from moviepy import ImageSequenceClip, VideoFileClip, CompositeVideoClip
from moviepy.video.fx.Loop import Loop
import shutil
import datetime
from pathlib import Path
from typing import Iterator, Tuple, List, Optional
import random

load_dotenv()


def load_env_vars() -> tuple[str, str, str, int, str]:
    """Loads required environment variables.

    Returns:
        A tuple containing the CSV file path, temporary PNG directory name,
        output directory name, video FPS, and reaction GIF directory name.
    """
    csv_path: Optional[str] = os.getenv("CSV_FILE_PATH")
    temp_png_dir: str = os.getenv("TEMP_PNG_DIR_NAME", "temp_pngs")
    output_dir: str = os.getenv("OUTPUT_DIR_NAME", "outputs")
    video_fps_str: str = os.getenv("VIDEO_FPS", "1")
    video_fps: int = int(video_fps_str)
    reaction_gif_dir: str = os.getenv("REACTION_GIF_DIR", "reaction_gifs")
    return csv_path, temp_png_dir, output_dir, video_fps, reaction_gif_dir


def read_puzzles(file_path: str) -> pd.DataFrame:
    """Reads the puzzle CSV file into a pandas DataFrame.

    Args:
        file_path: The path to the CSV file.

    Returns:
        A pandas DataFrame containing the puzzle data.
    """
    column_names: List[str] = [
        "PuzzleId",
        "FEN",
        "Moves",
        "Rating",
        "RatingDeviation",
        "Popularity",
        "NbPlays",
        "Themes",
        "GameUrl",
        "OpeningTags",
    ]
    df: pd.DataFrame = pd.read_csv(file_path, names=column_names, header=0)
    return df


def prepare_directory(dir_path: Path) -> Path:
    """Prepares a directory by removing it if it exists and recreating it.

    Args:
        dir_path: The path to the directory to prepare.

    Returns:
        The path to the prepared directory.
    """
    shutil.rmtree(dir_path, ignore_errors=True)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def generate_board_states(
    fen: str, uci_moves: list[str]
) -> Iterator[Tuple[chess.Board, Optional[chess.Move]]]:
    """Generates chess board states for a given FEN and sequence of moves.

    Args:
        fen: The starting FEN string.
        uci_moves: A list of moves in UCI format.

    Yields:
        Tuples of (chess.Board, chess.Move | None), representing the board
        state and the last move made (or None for the initial state).
    """
    board: chess.Board = chess.Board(fen)
    yield board.copy(), None
    for uci_move in uci_moves:
        move: chess.Move = chess.Move.from_uci(uci_move)
        board.push(move)
        yield board.copy(), move


def generate_png_sequence(fen: str, uci_moves: list[str], temp_dir: Path) -> list[str]:
    """Generates a sequence of PNG images representing puzzle moves.

    Args:
        fen: The starting FEN string.
        uci_moves: A list of moves in UCI format.
        temp_dir: The directory to save temporary PNG files.

    Returns:
        A list of paths to the generated PNG files.
    """
    board_states: Iterator[Tuple[chess.Board, Optional[chess.Move]]] = (
        generate_board_states(fen, uci_moves)
    )
    png_files: List[str] = []
    for frame_num, (board, move) in enumerate(board_states):
        png_path: Path = temp_dir / f"frame_{frame_num:03d}.png"
        svg_data: str = chess.svg.board(board=board, lastmove=move)
        cairosvg.svg2png(bytestring=svg_data.encode("utf-8"), write_to=str(png_path))
        png_files.append(str(png_path))
    return png_files


def get_random_gif_path(gif_dir: Path) -> Path:
    """Gets the path to a randomly selected GIF file from a directory.

    Args:
        gif_dir: The directory containing the GIF files.

    Returns:
        A Path object to a random GIF file.
        Raises IndexError if no GIF files are found.
    """
    gif_files: List[Path] = list(gif_dir.glob("*.gif"))
    return random.choice(gif_files)


def create_base_video(
    fen: str, uci_moves: List[str], temp_dir: Path, output_dir: Path, fps: int
) -> Path:
    """Generates PNGs and creates the base video."""
    png_files = generate_png_sequence(fen, uci_moves, temp_dir)
    base_video_path = generate_timestamped_output_path(
        output_dir, "temp_base_video", ".mp4"
    )
    clip: ImageSequenceClip = ImageSequenceClip(png_files, fps=fps)
    clip.write_videofile(str(base_video_path), codec="libx264", logger=None)
    clip.close()
    return base_video_path


def overlay_gif_on_video(base_video_path: Path, gif_path: Path, output_path: Path):
    """Stacks a reaction GIF on top of the base chess video to fit 1080x1920."""
    target_width = 1080
    target_height = 1920

    main_clip = VideoFileClip(str(base_video_path))
    gif_clip_orig = VideoFileClip(str(gif_path))

    main_resized = main_clip.resized(width=target_width)
    w_main_resized, h_main_resized = main_resized.size
    h_gif_area = target_height - h_main_resized
    if h_gif_area <= 0:
        print("Warning: Not enough height for GIF. Outputting only main video.")
        main_resized.write_videofile(str(output_path), codec="libx264", logger=None)
        main_clip.close()
        gif_clip_orig.close()
        main_resized.close()
        return
    gif_resized = gif_clip_orig.resized(width=target_width)
    w_gif_resized, h_gif_resized = gif_resized.size
    if h_gif_resized > h_gif_area:
        gif_resized = gif_clip_orig.resized(height=h_gif_area)
        w_gif_resized, h_gif_resized = gif_resized.size
    looper = Loop(duration=main_resized.duration)
    gif_looped = looper.apply(gif_resized)
    gif_pos_x = (target_width - w_gif_resized) / 2
    gif_pos_y = (h_gif_area - h_gif_resized) / 2
    main_pos_x = (target_width - w_main_resized) / 2
    main_pos_y = h_gif_area

    gif_positioned = gif_looped.with_position((gif_pos_x, gif_pos_y))
    main_positioned = main_resized.with_position((main_pos_x, main_pos_y))
    final_clip = CompositeVideoClip(
        [main_positioned, gif_positioned], size=(target_width, target_height)
    )

    final_clip.write_videofile(str(output_path), codec="libx264", logger=None)

    gif_clip_orig.close()
    main_clip.close()
    gif_resized.close()
    main_resized.close()
    final_clip.close()


def process_puzzle(csv_path: str, index: int) -> Tuple[str, List[str]]:
    """Reads puzzles and extracts data for a specific index."""
    df = read_puzzles(csv_path)
    puzzle: pd.Series = df.iloc[index]
    fen: str = puzzle["FEN"]
    moves_str: str = puzzle["Moves"]
    uci_moves: List[str] = moves_str.split(" ")
    return fen, uci_moves


def generate_timestamped_output_path(base_dir: Path, prefix: str, suffix: str) -> Path:
    """Generates a timestamped file path within a base directory.

    Args:
        base_dir: The base directory for the output file.
        prefix: The prefix for the filename.
        suffix: The suffix (extension) for the filename.

    Returns:
        A Path object representing the full timestamped output path.
    """
    timestamp: str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path: Path = base_dir / f"{prefix}_{timestamp}{suffix}"
    return output_path


def main():
    """
    Main function to generate a chess puzzle video with a reaction GIF overlay.
    """
    csv_path, temp_png_dir_name, output_dir_name, video_fps, reaction_gif_dir_name = (
        load_env_vars()
    )

    temp_dir_path = Path(temp_png_dir_name)
    output_dir_path = Path(output_dir_name)
    gif_dir_path = Path(reaction_gif_dir_name)

    prepare_directory(temp_dir_path)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    puzzle_index_to_process = 0
    fen, uci_moves = process_puzzle(csv_path, puzzle_index_to_process)

    base_video_path = create_base_video(
        fen, uci_moves, temp_dir_path, output_dir_path, video_fps
    )
    random_gif_path = get_random_gif_path(gif_dir_path)
    final_output_video_path = generate_timestamped_output_path(
        output_dir_path, "youtube_short", ".mp4"
    )

    overlay_gif_on_video(base_video_path, random_gif_path, final_output_video_path)

    os.remove(base_video_path)
    shutil.rmtree(temp_dir_path)

    print(f"Generated video with GIF overlay and saved to {final_output_video_path}")


if __name__ == "__main__":
    main()
