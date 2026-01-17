from pathlib import Path
import random
from moviepy import ImageSequenceClip, VideoFileClip, CompositeVideoClip, AudioFileClip, concatenate_audioclips
from moviepy.video.fx.Loop import Loop


def create_base_video(png_files: list[str], output_path: Path, fps: int) -> VideoFileClip:
    """Create video from PNG sequence.

    Args:
        png_files (list[str]): List of PNG file paths.
        output_path (Path): Output video path.
        fps (int): Frames per second.

    Returns:
        VideoFileClip: The created video clip.
    """
    clip = ImageSequenceClip(png_files, fps=fps)
    clip.write_videofile(str(output_path), codec="libx264", logger=None)
    result = VideoFileClip(str(output_path))
    clip.close()
    return result


def select_gif(gif_dir: Path) -> Path:
    """Select a random GIF from directory.

    Args:
        gif_dir (Path): Directory containing GIF files.

    Returns:
        Path: Path to selected GIF.
    """
    gifs = list(gif_dir.glob("*.gif"))
    return random.choice(gifs) if gifs else gif_dir / "default.gif"


def create_audio_track(audio_dir: Path, duration: float) -> AudioFileClip:
    """Create audio track by concatenating random audio files.

    Args:
        audio_dir (Path): Directory containing audio files.
        duration (float): Target duration in seconds.

    Returns:
        AudioFileClip: Combined audio clip.
    """
    audio_files = list(audio_dir.glob("*.mp3"))
    if not audio_files:
        return AudioFileClip(silence=duration)

    clips = []
    total = 0.0
    while total < duration:
        clip = AudioFileClip(str(random.choice(audio_files)))
        clips.append(clip)
        total += clip.duration

    return concatenate_audioclips(clips).subclipped(0, duration)


def create_composite_video(base_path: Path, gif_path: Path, audio_dir: Path, output_path: Path, width: int, height: int) -> None:
    """Create composite video with GIF overlay and audio.

    Args:
        base_path (Path): Path to base video.
        gif_path (Path): Path to GIF overlay.
        audio_dir (Path): Directory containing audio files.
        output_path (Path): Output video path.
        width (int): Target video width.
        height (int): Target video height.
    """
    main_clip = VideoFileClip(str(base_path))
    gif_clip = VideoFileClip(str(gif_path))

    main_resized = main_clip.resized(width=width)
    h_main = main_resized.size[1]
    h_gif_area = height - h_main

    if h_gif_area <= 0:
        main_resized.write_videofile(str(output_path), codec="libx264", logger=None)
        main_clip.close()
        gif_clip.close()
        main_resized.close()
        return

    gif_resized = gif_clip.resized(width=width)
    if gif_resized.size[1] > h_gif_area:
        gif_resized = gif_clip.resized(height=h_gif_area)

    w_gif, h_gif = gif_resized.size
    duration = float(main_resized.duration or 1.0)
    gif_looped = Loop(duration=duration).apply(gif_resized)

    gif_positioned = gif_looped.with_position(((width - w_gif) / 2, (h_gif_area - h_gif) / 2))
    main_positioned = main_resized.with_position(((width - main_resized.size[0]) / 2, h_gif_area))

    composite = CompositeVideoClip([main_positioned, gif_positioned], size=(width, height))
    audio = create_audio_track(audio_dir, composite.duration)
    final = composite.with_audio(audio)
    final.write_videofile(str(output_path), codec="libx264", audio_codec="aac", logger=None)

    for c in [main_clip, gif_clip, main_resized, gif_resized, gif_looped, composite, audio, final]:
        if hasattr(c, "close"):
            c.close()
