from pathlib import Path
from typing import Optional, List
import concurrent.futures
from tqdm import tqdm

from .config import Config
from .puzzle import get_puzzle
from .chess_renderer import render_board_sequence
from .video_editor import (
    create_base_video,
    create_composite_video,
    get_random_file,
    generate_timestamped_path,
)
from .utils import prepare_directory, ensure_directory


def generate_single_video(
    puzzle_index: int,
    config: Config,
    output_dir: Path,
    gif_dir: Path,
    audio_dir: Path,
) -> Optional[Path]:
    """Generate single puzzle video.

    Args:
        puzzle_index: int - Index of puzzle to process
        config: Config - Configuration settings
        output_dir: Path - Output directory for videos
        gif_dir: Path - Directory containing reaction GIFs
        audio_dir: Path - Directory containing audio files

    Returns:
        Optional[Path]: Path to generated video or None if failed
    """
    temp_dir = Path(f"{config.temp_png_dir}_{puzzle_index}")
    prepare_directory(temp_dir)

    puzzle = get_puzzle(config.csv_file_path, puzzle_index)
    png_files = render_board_sequence(puzzle.fen, puzzle.moves, temp_dir)

    base_video_path = generate_timestamped_path(temp_dir, "base", ".mp4")
    create_base_video(png_files, base_video_path, config.video_fps)

    gif_path = get_random_file(gif_dir, "*.gif")
    output_path = output_dir / f"{puzzle_index}.mp4"

    create_composite_video(
        base_video_path,
        gif_path,
        audio_dir,
        output_path,
        config.target_width,
        config.target_height,
    )

    prepare_directory(temp_dir)
    return output_path


def generate_videos_parallel(config: Config) -> List[Path]:
    """Generate multiple videos in parallel.

    Args:
        config: Config - Configuration settings

    Returns:
        List[Path]: List of generated video paths
    """
    output_dir = ensure_directory(Path(config.output_dir))
    gif_dir = Path(config.reaction_gif_dir)
    audio_dir = ensure_directory(Path(config.reaction_audio_dir))

    with concurrent.futures.ProcessPoolExecutor(max_workers=config.max_workers) as executor:
        futures = [executor.submit(generate_single_video, idx, config, output_dir, gif_dir, audio_dir) for idx in range(config.num_videos)]

        results = []
        for task in tqdm(
            concurrent.futures.as_completed(futures),
            total=len(futures),
            desc="Generating videos",
        ):
            result = task.result()
            if result:
                results.append(result)

    return results


def main() -> None:
    """Main entry point for video generation."""
    config = Config.from_env()
    results = generate_videos_parallel(config)
    print(f"Generated {len(results)} videos successfully.")


if __name__ == "__main__":
    main()
