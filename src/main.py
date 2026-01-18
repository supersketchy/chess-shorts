from pathlib import Path
import random
import concurrent.futures
import warnings
from tqdm import tqdm
from moviepy import VideoFileClip

warnings.filterwarnings("ignore", module="moviepy")

import config
from puzzle import get_puzzle
from chess_renderer import render_board_sequence
from video_editor import create_composite_video, suppress_output


def generate_single_video(puzzle_index: int, gif_path: Path) -> Path | None:
    """Generate a single puzzle video.

    Args:
        puzzle_index (int): Index of puzzle in CSV.
        gif_path (Path): Path to GIF file.

    Returns:
        Path | None: Output path if successful.
    """
    puzzle = get_puzzle(config.csv_file_path, puzzle_index)
    frames = render_board_sequence(puzzle.fen, puzzle.moves)

    with suppress_output():
        gif_clip = VideoFileClip(str(gif_path))

    output_path = Path(config.output_dir) / f"{puzzle_index}.mp4"
    create_composite_video(
        frames,
        config.video_fps,
        gif_clip,
        Path(config.reaction_audio_dir),
        output_path,
        config.target_width,
        config.target_height,
    )

    gif_clip.close()
    return output_path


def generate_videos_parallel() -> list[Path]:
    """Generate multiple videos in parallel.

    Returns:
        list[Path]: List of generated video paths.
    """
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)
    gif_paths = list(Path(config.reaction_gif_dir).glob("*.gif"))

    with concurrent.futures.ProcessPoolExecutor(max_workers=config.max_workers) as executor:
        futures = [
            executor.submit(generate_single_video, i, random.choice(gif_paths))
            for i in range(config.num_videos)
        ]
        results = []
        for task in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Generating videos"):
            result = task.result()
            if result:
                results.append(result)

    return results


def main() -> None:
    """Entry point for video generation."""
    results = generate_videos_parallel()
    print(f"Generated {len(results)} videos successfully.")


if __name__ == "__main__":
    main()
