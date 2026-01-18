import json
from pathlib import Path
import concurrent.futures
import warnings
from tqdm import tqdm
from moviepy import VideoFileClip

warnings.filterwarnings("ignore", module="moviepy")

import config
from puzzle import get_puzzle
from chess_renderer import render_board_sequence
from video_editor import create_story_video
from story_generator import generate_story, AUDIO_DURATIONS


def _get_gif_duration(gif_dir: Path, gif_name: str) -> float:
    """Get duration of a GIF file.

    Args:
        gif_dir (Path): Directory containing GIF files.
        gif_name (str): Name of the GIF file.

    Returns:
        float: Duration in seconds.
    """
    gif_path = gif_dir / gif_name
    if not gif_path.exists():
        return 0.0
    clip = VideoFileClip(str(gif_path))
    duration = clip.duration
    clip.close()
    return duration


def _story_to_dict(story, gif_dir: Path) -> dict:
    """Convert Story to JSON-serializable dict.

    Args:
        story: Story namedtuple to convert.
        gif_dir (Path): Directory containing GIF files.

    Returns:
        dict: JSON-serializable representation.
    """
    return {
        "puzzle_id": story.puzzle_id,
        "title": story.title,
        "total_duration": story.total_duration,
        "beats": [
            {
                "character": beat.character.value,
                "emotion": beat.emotion.value,
                "gif_name": beat.gif_name,
                "gif_duration": _get_gif_duration(gif_dir, beat.gif_name),
                "audio_name": beat.audio_name,
                "audio_duration": AUDIO_DURATIONS.get(beat.audio_name, 0.0),
                "start_time": beat.start_time,
                "duration": beat.duration,
                "move_index": beat.move_index,
            }
            for beat in story.beats
        ],
    }


def generate_single_video(puzzle_index: int) -> Path | None:
    """Generate a single puzzle video with story-driven composition.

    Args:
        puzzle_index (int): Index of puzzle in CSV.

    Returns:
        Path | None: Output path if successful.
    """
    puzzle = get_puzzle(config.csv_file_path, puzzle_index)
    frames = render_board_sequence(puzzle.fen, puzzle.moves)
    story = generate_story(puzzle)

    gif_dir = Path(config.reaction_gif_dir)
    output_path = Path(config.output_dir) / f"{puzzle_index}.mp4"
    script_path = Path(config.output_dir) / f"{puzzle_index}_script.json"
    script_path.write_text(json.dumps(_story_to_dict(story, gif_dir), indent=2))

    create_story_video(
        frames,
        story,
        gif_dir,
        Path(config.reaction_audio_dir),
        output_path,
        config.target_width,
        config.target_height,
    )

    return output_path


def generate_videos_parallel() -> list[Path]:
    """Generate multiple videos in parallel.

    Returns:
        list[Path]: List of generated video paths.
    """
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)

    with concurrent.futures.ProcessPoolExecutor(max_workers=config.max_workers) as executor:
        futures = [executor.submit(generate_single_video, i) for i in range(config.num_videos)]
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
