from pathlib import Path
import shutil
import concurrent.futures
from tqdm import tqdm

from config import Config
from puzzle import get_puzzle
from chess_renderer import render_board_sequence
from video_editor import create_base_video, create_composite_video, select_gif


def prepare_dir(path: Path) -> Path:
    """Remove and recreate directory.

    Args:
        path (Path): Directory path.

    Returns:
        Path: The prepared directory path.
    """
    shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists.

    Args:
        path (Path): Directory path.

    Returns:
        Path: The directory path.
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def generate_single_video(puzzle_index: int, config: Config, temp_dir: Path, output_dir: Path, gif_dir: Path, audio_dir: Path) -> Path | None:
    """Generate a single puzzle video.

    Args:
        puzzle_index (int): Index of puzzle in CSV.
        config (Config): Configuration settings.
        temp_dir (Path): Base temp directory.
        output_dir (Path): Output directory.
        gif_dir (Path): GIF directory.
        audio_dir (Path): Audio directory.

    Returns:
        Path | None: Output path if successful.
    """
    worker_dir = prepare_dir(temp_dir / f"worker_{puzzle_index}")

    puzzle = get_puzzle(config.csv_file_path, puzzle_index)
    png_files = render_board_sequence(puzzle.fen, puzzle.moves, worker_dir)

    base_path = worker_dir / "base.mp4"
    create_base_video(png_files, base_path, config.video_fps)

    gif_path = select_gif(gif_dir)
    output_path = output_dir / f"{puzzle_index}.mp4"

    create_composite_video(base_path, gif_path, audio_dir, output_path, config.target_width, config.target_height)

    shutil.rmtree(worker_dir, ignore_errors=True)
    return output_path


def generate_videos_parallel(config: Config) -> list[Path]:
    """Generate multiple videos in parallel.

    Args:
        config (Config): Configuration settings.

    Returns:
        list[Path]: List of generated video paths.
    """
    temp_dir = prepare_dir(Path(config.temp_dir))
    output_dir = ensure_dir(Path(config.output_dir))
    gif_dir = Path(config.reaction_gif_dir)
    audio_dir = Path(config.reaction_audio_dir)

    with concurrent.futures.ProcessPoolExecutor(max_workers=config.max_workers) as executor:
        futures = [executor.submit(generate_single_video, i, config, temp_dir, output_dir, gif_dir, audio_dir) for i in range(config.num_videos)]
        results = []
        for task in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Generating videos"):
            result = task.result()
            if result:
                results.append(result)

    shutil.rmtree(temp_dir, ignore_errors=True)
    return results


def main() -> None:
    """Entry point for video generation."""
    config = Config.from_env()
    results = generate_videos_parallel(config)
    print(f"Generated {len(results)} videos successfully.")


if __name__ == "__main__":
    main()
