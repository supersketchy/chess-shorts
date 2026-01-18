from pathlib import Path
from contextlib import contextmanager
from typing import cast
import random
import sys
import os
import numpy as np
from numpy.typing import NDArray
from moviepy import ImageSequenceClip, VideoFileClip, VideoClip, CompositeVideoClip, AudioFileClip, concatenate_audioclips
from moviepy.video.fx.Loop import Loop


@contextmanager
def suppress_output():
    """Context manager to suppress stdout and stderr at file descriptor level."""
    sys.stdout.flush()
    sys.stderr.flush()
    devnull_fd = os.open(os.devnull, os.O_WRONLY)
    old_stdout_fd = os.dup(1)
    old_stderr_fd = os.dup(2)
    os.dup2(devnull_fd, 1)
    os.dup2(devnull_fd, 2)
    yield
    sys.stdout.flush()
    sys.stderr.flush()
    os.dup2(old_stdout_fd, 1)
    os.dup2(old_stderr_fd, 2)
    os.close(devnull_fd)
    os.close(old_stdout_fd)
    os.close(old_stderr_fd)


def create_base_clip(frames: list[NDArray[np.uint8]], fps: int) -> ImageSequenceClip:
    """Create video clip from numpy array sequence.

    Args:
        frames (list[NDArray[np.uint8]]): List of RGB numpy arrays.
        fps (int): Frames per second.

    Returns:
        ImageSequenceClip: The created video clip.
    """
    return ImageSequenceClip(frames, fps=fps)


def create_audio_track(audio_dir: Path, duration: float) -> AudioFileClip | None:
    """Create audio track by concatenating random audio files.

    Args:
        audio_dir (Path): Directory containing audio files.
        duration (float): Target duration in seconds.

    Returns:
        AudioFileClip | None: Combined audio clip or None if no audio files.
    """
    audio_files = list(audio_dir.glob("*.mp3"))
    if not audio_files:
        return None

    clips = []
    total = 0.0
    while total < duration:
        clip = AudioFileClip(str(random.choice(audio_files)))
        clips.append(clip)
        total += clip.duration

    return concatenate_audioclips(clips).subclipped(0, duration)


def create_composite_video(
    frames: list[NDArray[np.uint8]],
    fps: int,
    gif_clip: VideoFileClip,
    audio_dir: Path,
    output_path: Path,
    width: int,
    height: int,
) -> None:
    """Create composite video with GIF overlay and audio.

    Args:
        frames (list[NDArray[np.uint8]]): List of RGB numpy arrays for main video.
        fps (int): Frames per second.
        gif_clip (VideoFileClip): Pre-loaded GIF clip.
        audio_dir (Path): Directory containing audio files.
        output_path (Path): Output video path.
        width (int): Target video width.
        height (int): Target video height.
    """
    with suppress_output():
        main_clip = create_base_clip(frames, fps)
        main_resized = main_clip.resized(width=width)
        h_main = main_resized.size[1]
        h_gif_area = height - h_main

        if h_gif_area <= 0:
            audio = create_audio_track(audio_dir, main_resized.duration)
            final = main_resized.with_audio(audio) if audio else main_resized
            final.write_videofile(str(output_path), codec="libx264", audio_codec="aac", logger=None)
            main_clip.close()
            main_resized.close()
            return

        gif_resized = gif_clip.resized(width=width)
        if gif_resized.size[1] > h_gif_area:
            gif_resized = gif_clip.resized(height=h_gif_area)
        w_gif, h_gif = gif_resized.size
        duration = float(main_resized.duration or 1.0)
        gif_looped = cast(VideoClip, Loop(duration=duration).apply(gif_resized))

        gif_positioned = gif_looped.with_position(((width - w_gif) / 2, (h_gif_area - h_gif) / 2))
        main_positioned = main_resized.with_position(((width - main_resized.size[0]) / 2, h_gif_area))

        composite = CompositeVideoClip([main_positioned, gif_positioned], size=(width, height))
        audio = create_audio_track(audio_dir, composite.duration)
        final = composite.with_audio(audio) if audio else composite
        final.write_videofile(str(output_path), codec="libx264", audio_codec="aac", logger=None)

        for c in [main_clip, main_resized, gif_resized, gif_looped, composite, final]:
            if hasattr(c, "close"):
                c.close()
        if audio:
            audio.close()
