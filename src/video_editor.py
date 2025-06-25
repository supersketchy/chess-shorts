from typing import List, Optional, Any
from pathlib import Path
import random
import datetime
from moviepy import (
    ImageSequenceClip,
    VideoFileClip,
    CompositeVideoClip,
    AudioFileClip,
    concatenate_audioclips,
    concatenate_videoclips,
)
from moviepy.video.fx.Loop import Loop
from .gemini_analyzer import VideoAnalysis


def create_dynamic_video(png_files: List[str], analysis: VideoAnalysis, output_path: Path) -> VideoFileClip:
    """Create video with audio-synced timing based on Gemini analysis."""
    clips = []

    for i, move in enumerate(analysis.move_reactions):
        if i < len(png_files):
            clip = ImageSequenceClip([png_files[i]], durations=[move.duration])
            clips.append(clip)

    if clips:
        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile(str(output_path), codec="libx264", logger=None)
        result = VideoFileClip(str(output_path))
        final_clip.close()
        return result

    return create_base_video(png_files, output_path, 1)


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


def select_optimal_gif_from_analysis(gif_dir: Path, analysis: VideoAnalysis) -> Path:
    """Select GIF based on the longest/most impactful move."""
    available_gifs = list(gif_dir.glob("*.gif"))

    # Find the move with longest duration (most impactful)
    if analysis.move_reactions:
        longest_move = max(analysis.move_reactions, key=lambda m: m.duration)
        preferred_gif = longest_move.gif_choice
    else:
        preferred_gif = "vine-boom"

    # Look for exact match first
    for gif_file in available_gifs:
        if preferred_gif in gif_file.stem:
            return gif_file

    # Fallback to any available GIF
    return random.choice(available_gifs) if available_gifs else gif_dir / "default.gif"


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


def create_smart_audio_track(audio_dir: Path, analysis: VideoAnalysis) -> AudioFileClip:
    """Create audio track perfectly synced to move durations."""
    audio_files = {f.stem: f for f in audio_dir.glob("*.mp3")}
    selected_clips = []

    # Create audio sequence based on move-by-move analysis
    for move in analysis.move_reactions:
        audio_choice = move.audio_choice

        # Map audio choice to actual file
        matching_file = None
        for file_stem, file_path in audio_files.items():
            if audio_choice in file_stem or file_stem in audio_choice:
                matching_file = file_path
                break

        if matching_file:
            clip = AudioFileClip(str(matching_file))
            # The duration already matches the audio file, but ensure exact timing
            if clip.duration != move.duration:
                clip = clip.subclipped(0, min(move.duration, clip.duration))
            selected_clips.append(clip)

    # Final fallback
    if not selected_clips:
        fallback = random.choice(list(audio_files.values()))
        selected_clips = [AudioFileClip(str(fallback))]

    total_audio = concatenate_audioclips(selected_clips)
    return total_audio.subclipped(0, min(analysis.total_duration, total_audio.duration))


def create_composite_video(
    base_video_path: Path,
    gif_path: Path,
    audio_dir: Path,
    output_path: Path,
    target_width: int,
    target_height: int,
    analysis: Optional[VideoAnalysis] = None,
) -> None:
    """Create composite video with GIF overlay and smart audio."""
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

    if analysis:
        final_audio = create_smart_audio_track(audio_dir, analysis)
    else:
        audio_files = list(audio_dir.glob("*.mp3"))
        audio_segments = []
        total_duration = 0

        while total_duration < video_composite.duration:
            audio_clip = AudioFileClip(str(random.choice(audio_files)))
            audio_segments.append(audio_clip)
            total_duration += audio_clip.duration

        final_audio = concatenate_audioclips(audio_segments).subclipped(0, video_composite.duration)

    final_video: Any = video_composite.with_audio(final_audio)
    final_video.write_videofile(str(output_path), codec="libx264", audio_codec="aac", logger=None)

    for clip in [main_clip, gif_clip, main_resized, gif_resized, gif_looped, video_composite, final_audio, final_video]:
        if hasattr(clip, "close"):
            clip.close()


def generate_timestamped_path(base_dir: Path, prefix: str, suffix: str) -> Path:
    """Generate timestamped file path."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return base_dir / f"{prefix}_{timestamp}{suffix}"
