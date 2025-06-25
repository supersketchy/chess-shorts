from typing import List
from pathlib import Path
import random
import datetime
from moviepy import (
    ImageSequenceClip,
    VideoFileClip,
    CompositeVideoClip,
    AudioFileClip,
    concatenate_audioclips,
)
from moviepy.video.fx.Loop import Loop


def create_base_video(png_files: List[str], output_path: Path, fps: int) -> VideoFileClip:
    """Create base video from PNG sequence.

    Args:
        png_files: List[str] - List of PNG file paths
        output_path: Path - Output video path
        fps: int - Frames per second

    Returns:
        VideoFileClip: Created video clip
    """
    clip = ImageSequenceClip(png_files, fps=fps)
    clip.write_videofile(str(output_path), codec="libx264", logger=None)
    result = VideoFileClip(str(output_path))
    clip.close()
    return result


def get_random_file(directory: Path, extension: str) -> Path:
    """Get random file with given extension from directory.

    Args:
        directory: Path - Directory to search
        extension: str - File extension (e.g., '*.gif')

    Returns:
        Path: Random file path
    """
    files = list(directory.glob(extension))
    return random.choice(files)


def create_composite_video(
    base_video_path: Path,
    gif_path: Path,
    audio_dir: Path,
    output_path: Path,
    target_width: int,
    target_height: int,
) -> None:
    """Create composite video with GIF overlay and audio.

    Args:
        base_video_path: Path - Base chess video
        gif_path: Path - Reaction GIF to overlay
        audio_dir: Path - Directory with audio files
        output_path: Path - Final video output path
        target_width: int - Target video width
        target_height: int - Target video height
    """
    main_clip = VideoFileClip(str(base_video_path))
    gif_clip = VideoFileClip(str(gif_path))

    main_resized = main_clip.resized(width=target_width)
    w_main, h_main = main_resized.size
    h_gif_area = target_height - h_main

    if h_gif_area <= 0:
        main_resized.write_videofile(str(output_path), codec="libx264", logger=None)
        main_clip.close()
        gif_clip.close()
        main_resized.close()
        return

    gif_resized = gif_clip.resized(width=target_width)
    w_gif, h_gif = gif_resized.size
    if h_gif > h_gif_area:
        gif_resized = gif_clip.resized(height=h_gif_area)
        w_gif, h_gif = gif_resized.size

    duration = float(main_resized.duration or 1.0)
    gif_looped = Loop(duration=duration).apply(gif_resized)

    gif_positioned = gif_looped.with_position(((target_width - w_gif) / 2, (h_gif_area - h_gif) / 2))
    main_positioned = main_resized.with_position(((target_width - w_main) / 2, h_gif_area))

    video_composite = CompositeVideoClip([main_positioned, gif_positioned], size=(target_width, target_height))

    audio_files = list(audio_dir.glob("*.mp3"))
    audio_segments = []
    total_duration = 0

    while total_duration < video_composite.duration:
        audio_clip = AudioFileClip(str(random.choice(audio_files)))
        audio_segments.append(audio_clip)
        total_duration += audio_clip.duration

    final_audio = concatenate_audioclips(audio_segments).subclipped(0, video_composite.duration)
    final_video = video_composite.with_audio(final_audio)

    final_video.write_videofile(str(output_path), codec="libx264", audio_codec="aac", logger=None)

    for clip in [
        main_clip,
        gif_clip,
        main_resized,
        gif_resized,
        gif_looped,
        video_composite,
        final_audio,
        final_video,
    ] + audio_segments:
        clip.close()


def generate_timestamped_path(base_dir: Path, prefix: str, suffix: str) -> Path:
    """Generate timestamped file path.

    Args:
        base_dir: Path - Base directory
        prefix: str - Filename prefix
        suffix: str - File extension

    Returns:
        Path: Timestamped file path
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return base_dir / f"{prefix}_{timestamp}{suffix}"
