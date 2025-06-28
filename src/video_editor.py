from typing import List, Any
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
    """Create base video from PNG sequence."""
    clip = ImageSequenceClip(png_files, fps=fps)
    clip.write_videofile(str(output_path), codec="libx264", logger=None)
    result = VideoFileClip(str(output_path))
    clip.close()
    return result


def get_random_file(directory: Path, extension: str) -> Path:
    """Get random file with given extension from directory."""
    files = list(directory.glob(extension))
    return random.choice(files) if files else directory / "default.gif"


def select_optimal_gif(gif_dir: Path, recommended_style: str) -> Path:
    """Legacy method - Select GIF based on recommended style."""
    style_mapping = {"shock": ["get-out", "why-are"], "excitement": ["anime-wow", "baby-laughing"], "celebration": ["baby-laughing"], "thinking": ["vine-boom"]}

    preferred_gifs = style_mapping.get(recommended_style, [])
    available_gifs = list(gif_dir.glob("*.gif"))

    for gif_name in preferred_gifs:
        matches = [g for g in available_gifs if gif_name in g.stem]
        if matches:
            return matches[0]

    return random.choice(available_gifs) if available_gifs else gif_dir / "default.gif"


def create_simple_audio_track(audio_dir: Path, duration: float) -> AudioFileClip:
    """Create audio track from random selection."""
    audio_files = list(audio_dir.glob("*.mp3"))
    if not audio_files:
        return AudioFileClip(silence=duration)

    selected_clips = []
    total_duration = 0

    while total_duration < duration:
        audio_file = random.choice(audio_files)
        clip = AudioFileClip(str(audio_file))
        selected_clips.append(clip)
        total_duration += clip.duration

    return concatenate_audioclips(selected_clips).subclipped(0, duration)


def create_composite_video(
    base_video_path: Path,
    gif_path: Path,
    audio_dir: Path,
    output_path: Path,
    target_width: int,
    target_height: int,
) -> None:
    """Create composite video with GIF overlay and random audio."""
    main_clip: Any = VideoFileClip(str(base_video_path))
    gif_clip: Any = VideoFileClip(str(gif_path))

    main_resized: Any = main_clip.resized(width=target_width)
    w_main, h_main = main_resized.size
    h_gif_area = target_height - h_main

    if h_gif_area <= 0:
        main_resized.write_videofile(str(output_path), codec="libx264", logger=None)
        for clip in [main_clip, gif_clip, main_resized]:
            clip.close()
        return

    gif_resized: Any = gif_clip.resized(width=target_width)
    w_gif, h_gif = gif_resized.size
    if h_gif > h_gif_area:
        gif_resized = gif_clip.resized(height=h_gif_area)
        w_gif, h_gif = gif_resized.size

    duration = float(main_resized.duration or 1.0)
    gif_looped: Any = Loop(duration=duration).apply(gif_resized)

    gif_positioned: Any = gif_looped.with_position(((target_width - w_gif) / 2, (h_gif_area - h_gif) / 2))
    main_positioned: Any = main_resized.with_position(((target_width - w_main) / 2, h_gif_area))

    video_composite: Any = CompositeVideoClip([main_positioned, gif_positioned], size=(target_width, target_height))

    final_audio = create_simple_audio_track(audio_dir, video_composite.duration)
    final_video: Any = video_composite.with_audio(final_audio)
    final_video.write_videofile(str(output_path), codec="libx264", audio_codec="aac", logger=None)

    for clip in [main_clip, gif_clip, main_resized, gif_resized, gif_looped, video_composite, final_audio, final_video]:
        if hasattr(clip, "close"):
            clip.close()


def generate_timestamped_path(base_dir: Path, prefix: str, suffix: str) -> Path:
    """Generate timestamped file path."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return base_dir / f"{prefix}_{timestamp}{suffix}"
