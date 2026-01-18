from pathlib import Path
from contextlib import contextmanager
from typing import cast
import random
import sys
import os
import numpy as np
from numpy.typing import NDArray
from moviepy import ImageSequenceClip, VideoFileClip, VideoClip, CompositeVideoClip, AudioFileClip, concatenate_audioclips, concatenate_videoclips
from moviepy.video.fx.Loop import Loop
from story import Story


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


def _create_board_clips(frames: list[NDArray[np.uint8]], story: Story, width: int) -> list[VideoClip]:
    """Create board clips with durations from story beats.

    Args:
        frames (list[NDArray[np.uint8]]): List of RGB numpy arrays.
        story (Story): Story with beat timings.
        width (int): Target width for resizing.

    Returns:
        list[VideoClip]: Board clips with correct durations.
    """
    clips = []
    for beat in story.beats:
        frame_idx = min(beat.move_index, len(frames) - 1)
        frame = frames[frame_idx]
        clip = ImageSequenceClip([frame], fps=1).with_duration(beat.duration)
        clips.append(clip.resized(width=width))
    return clips


def _create_gif_sequence(story: Story, gif_dir: Path, width: int, height: int) -> tuple[list[VideoClip], list[VideoFileClip]]:
    """Load GIFs per beat with correct duration.

    Args:
        story (Story): Story with beat timings.
        gif_dir (Path): Directory containing GIF files.
        width (int): Target width.
        height (int): Available height for GIF.

    Returns:
        tuple[list[VideoClip], list[VideoFileClip]]: GIF clips with correct durations and source clips to close later.
    """
    clips = []
    source_clips = []
    for beat in story.beats:
        gif_path = gif_dir / beat.gif_name
        if not gif_path.exists():
            gif_path = list(gif_dir.glob("*.gif"))[0]

        gif_clip = VideoFileClip(str(gif_path))
        source_clips.append(gif_clip)
        gif_resized = gif_clip.resized(width=width)
        if gif_resized.size[1] > height:
            gif_resized = gif_clip.resized(height=height)

        gif_looped = cast(VideoClip, Loop(duration=beat.duration).apply(gif_resized))
        clips.append(gif_looped)
    return clips, source_clips


def _create_audio_sequence(story: Story, audio_dir: Path) -> AudioFileClip:
    """Concatenate audio clips per beat.

    Args:
        story (Story): Story with beat timings.
        audio_dir (Path): Directory containing audio files.

    Returns:
        AudioFileClip: Combined audio track.
    """
    clips = []
    for beat in story.beats:
        audio_path = audio_dir / beat.audio_name
        if not audio_path.exists():
            audio_files = list(audio_dir.glob("*.mp3"))
            audio_path = audio_files[0] if audio_files else None

        if audio_path and audio_path.exists():
            audio_clip = AudioFileClip(str(audio_path))
            if audio_clip.duration > beat.duration:
                audio_clip = audio_clip.subclipped(0, beat.duration)
            elif audio_clip.duration < beat.duration:
                silence_duration = beat.duration - audio_clip.duration
                from moviepy.audio.AudioClip import AudioClip

                silence = AudioClip(lambda t: 0, duration=silence_duration, fps=44100)
                audio_clip = concatenate_audioclips([audio_clip, silence])
            clips.append(audio_clip)

    return concatenate_audioclips(clips) if clips else None


def create_story_video(
    frames: list[NDArray[np.uint8]],
    story: Story,
    gif_dir: Path,
    audio_dir: Path,
    output_path: Path,
    width: int,
    height: int,
) -> None:
    """Create video with story-driven GIF and audio timing.

    Args:
        frames (list[NDArray[np.uint8]]): List of RGB numpy arrays for chess boards.
        story (Story): Story with timed beats.
        gif_dir (Path): Directory containing GIF files.
        audio_dir (Path): Directory containing audio files.
        output_path (Path): Output video path.
        width (int): Target video width.
        height (int): Target video height.
    """
    with suppress_output():
        board_clips = _create_board_clips(frames, story, width)
        board_video = concatenate_videoclips(board_clips)
        h_board = board_clips[0].size[1] if board_clips else height // 2
        h_gif_area = height - h_board

        gif_clips, gif_source_clips = _create_gif_sequence(story, gif_dir, width, h_gif_area)
        gif_video = concatenate_videoclips(gif_clips)

        w_gif, h_gif = gif_video.size
        gif_positioned = gif_video.with_position(((width - w_gif) / 2, (h_gif_area - h_gif) / 2))
        board_positioned = board_video.with_position(((width - board_video.size[0]) / 2, h_gif_area))

        composite = CompositeVideoClip([board_positioned, gif_positioned], size=(width, height))

        audio = _create_audio_sequence(story, audio_dir)
        if audio:
            if audio.duration > composite.duration:
                audio = audio.subclipped(0, composite.duration)
            composite = composite.with_audio(audio)

        composite.write_videofile(str(output_path), codec="libx264", audio_codec="aac", logger=None)

        for clip in board_clips + gif_clips + gif_source_clips:
            if hasattr(clip, "close"):
                clip.close()
        if audio:
            audio.close()
        board_video.close()
        gif_video.close()
        composite.close()
