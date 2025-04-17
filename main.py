import pandas as pd
import os
from dotenv import load_dotenv
import chess
import chess.svg
import cairosvg
from moviepy import (
    ImageSequenceClip,
    VideoFileClip,
    CompositeVideoClip,
    AudioFileClip,
)
from moviepy.audio.AudioClip import concatenate_audioclips
from moviepy.video.fx.Loop import Loop
import shutil
import datetime
from pathlib import Path
from typing import Iterator, Tuple, List, Optional
import random
import concurrent.futures
from tqdm import tqdm
import google.genai as genai
from google.cloud import texttospeech
import re


load_dotenv()


def load_env_vars() -> tuple[str, str, str, int, str, str, str]:
    """Loads required environment variables.

    Returns:
        A tuple containing the CSV file path, temporary PNG directory name,
        output directory name, video FPS, reaction GIF directory name,
        Gemini API key, and reaction audio directory name.
    """
    csv_path: Optional[str] = os.getenv("CSV_FILE_PATH")
    temp_png_dir: str = os.getenv("TEMP_PNG_DIR_NAME", "temp_pngs")
    output_dir: str = os.getenv("OUTPUT_DIR_NAME", "outputs")
    video_fps_str: str = os.getenv("VIDEO_FPS", "1")
    video_fps: int = int(video_fps_str)
    reaction_gif_dir: str = os.getenv("REACTION_GIF_DIR", "reaction_gifs")
    gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY")
    reaction_audio_dir: str = os.getenv("REACTION_AUDIO_DIR", "reaction_audio")
    return (
        csv_path,
        temp_png_dir,
        output_dir,
        video_fps,
        reaction_gif_dir,
        gemini_api_key,
        reaction_audio_dir,
    )


def read_puzzles(file_path: str) -> pd.DataFrame:
    """Reads the puzzle CSV file into a pandas DataFrame.

    Args:
        file_path: The path to the CSV file.

    Returns:
        A pandas DataFrame containing the puzzle data.
    """
    column_names: List[str] = [
        "PuzzleId",
        "FEN",
        "Moves",
        "Rating",
        "RatingDeviation",
        "Popularity",
        "NbPlays",
        "Themes",
        "GameUrl",
        "OpeningTags",
    ]
    df: pd.DataFrame = pd.read_csv(file_path, names=column_names, header=0)
    return df


def prepare_directory(dir_path: Path) -> Path:
    """Prepares a directory by removing it if it exists and recreating it.

    Args:
        dir_path: The path to the directory to prepare.

    Returns:
        The path to the prepared directory.
    """
    shutil.rmtree(dir_path, ignore_errors=True)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def generate_board_states(
    fen: str, uci_moves: list[str]
) -> Iterator[Tuple[chess.Board, Optional[chess.Move]]]:
    """Generates chess board states for a given FEN and sequence of moves.

    Args:
        fen: The starting FEN string.
        uci_moves: A list of moves in UCI format.

    Yields:
        Tuples of (chess.Board, chess.Move | None), representing the board
        state and the last move made (or None for the initial state).
    """
    board: chess.Board = chess.Board(fen)
    yield board.copy(), None
    for uci_move in uci_moves:
        move: chess.Move = chess.Move.from_uci(uci_move)
        board.push(move)
        yield board.copy(), move


def generate_png_sequence(fen: str, uci_moves: list[str], temp_dir: Path) -> list[str]:
    """Generates a sequence of PNG images representing puzzle moves.

    Args:
        fen: The starting FEN string.
        uci_moves: A list of moves in UCI format.
        temp_dir: The directory to save temporary PNG files.

    Returns:
        A list of paths to the generated PNG files.
    """
    board_states: Iterator[Tuple[chess.Board, Optional[chess.Move]]] = (
        generate_board_states(fen, uci_moves)
    )
    png_files: List[str] = []
    for frame_num, (board, move) in enumerate(board_states):
        png_path: Path = temp_dir / f"frame_{frame_num:03d}.png"
        svg_data: str = chess.svg.board(board=board, lastmove=move)
        cairosvg.svg2png(bytestring=svg_data.encode("utf-8"), write_to=str(png_path))
        png_files.append(str(png_path))
    return png_files


def get_random_gif_path(gif_dir: Path) -> Path:
    """Gets the path to a randomly selected GIF file from a directory.

    Args:
        gif_dir: The directory containing the GIF files.

    Returns:
        A Path object to a random GIF file.
        Raises IndexError if no GIF files are found.
    """
    gif_files: List[Path] = list(gif_dir.glob("*.gif"))
    if not gif_files:
        raise IndexError(f"No GIF files found in directory: {gif_dir}")
    return random.choice(gif_files)


def get_random_reaction_audio_path(audio_dir: Path) -> Optional[Path]:
    """Gets the path to a randomly selected audio file (e.g., MP3, WAV) from a directory.

    Args:
        audio_dir: The directory containing the audio files.

    Returns:
        A Path object to a random audio file, or None if no files are found
        or the directory doesn't exist.
    """
    audio_files: List[Path] = (
        list(audio_dir.glob("*.mp3"))
        + list(audio_dir.glob("*.wav"))
        + list(audio_dir.glob("*.ogg"))
    )
    return random.choice(audio_files)


def synthesize_text_to_speech(
    client: texttospeech.TextToSpeechClient, text: str, output_path: Path
) -> None:
    """Synthesizes speech from text and saves it as an MP3 file.

    Args:
        client: The initialized TextToSpeechClient.
        text: The text to synthesize.
        output_path: The path to save the output MP3 file.
    """
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    with open(output_path, "wb") as out:
        out.write(response.audio_content)


def generate_interleaved_audio(
    text: str,
    tts_client: texttospeech.TextToSpeechClient,
    reaction_audio_dir: Path,
    temp_dir: Path,
    prefix: str = "chunk",
) -> List[Path]:
    """Generates TTS audio chunks from text and interleaves them with random reaction sounds
       based on [REACTION] placeholders.

    Args:
        text: The input caption text containing [REACTION] placeholders.
        tts_client: Initialized Google TextToSpeechClient.
        reaction_audio_dir: Path to the directory with reaction audio files.
        temp_dir: Temporary directory to store generated audio chunks.
        prefix: Prefix for temporary audio chunk filenames.

    Returns:
        A list of Path objects for the audio files in the order they should be played
        (caption chunk, reaction sound, caption chunk, ...).
    """
    text_segments = [
        segment.strip()
        for segment in re.split(r"\[REACTION\]", text)
        if segment.strip()
    ]
    interleaved_paths: List[Path] = []
    chunk_num = 0

    for i, segment in enumerate(text_segments):
        chunk_path = temp_dir / f"{prefix}_{chunk_num}.mp3"
        print(f"Synthesizing TTS for segment {chunk_num}: '{segment[:50]}...'")
        synthesize_text_to_speech(tts_client, segment, chunk_path)
        interleaved_paths.append(chunk_path)
        chunk_num += 1

        if i < len(text_segments) - 1:
            reaction_path = get_random_reaction_audio_path(reaction_audio_dir)
            if reaction_path:
                print(f"Adding reaction audio: {reaction_path.name}")
                interleaved_paths.append(reaction_path)
            else:
                print("Warning: Could not find reaction audio to insert.")

    if not interleaved_paths and text.strip() and "[REACTION]" not in text:
        print("No [REACTION] found, synthesizing full text as one chunk.")
        chunk_path = temp_dir / f"{prefix}_full.mp4"
        synthesize_text_to_speech(tts_client, text.strip(), chunk_path)
        interleaved_paths.append(chunk_path)
    elif not interleaved_paths and text.strip():
        print("Warning: Text contained only [REACTION] or whitespace.")

    print(
        f"Generated {len(interleaved_paths)} audio segments (TTS chunks + reactions)."
    )
    return interleaved_paths


def create_base_video(
    fen: str,
    uci_moves: List[str],
    temp_dir: Path,
    fps: int,
) -> Path:
    """Generates PNGs and creates the base video inside the temp directory."""
    png_files = generate_png_sequence(fen, uci_moves, temp_dir)
    timestamp: str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    base_video_path = temp_dir / f"temp_base_video_{timestamp}.mp4"

    clip: ImageSequenceClip = ImageSequenceClip(png_files, fps=fps)
    clip.write_videofile(str(base_video_path), codec="libx264", logger=None)
    clip.close()
    return base_video_path


def overlay_gif_on_video(
    base_video_path: Path,
    gif_path: Path,
    audio_paths: List[Path],
    output_path: Path,
) -> None:
    """Stack a reaction GIF on the chess video and add concatenated audio.

    Args:
        base_video_path: Path to the base MP4 without overlays.
        gif_path: Path to the reaction GIF to overlay.
        audio_paths: List of paths to audio files (TTS chunks, reactions) to concatenate.
        output_path: Path where the final MP4 will be saved.

    Returns:
        None
    """
    target_width = 1080
    target_height = 1920

    main_clip = None
    gif_clip_orig = None
    main_resized = None
    gif_resized = None
    gif_looped = None
    gif_positioned = None
    main_positioned = None
    video_only_clip = None
    audio_clips = []
    concatenated_audio = None
    final_audio = None
    final_clip_with_audio = None

    main_clip = VideoFileClip(str(base_video_path))
    gif_clip_orig = VideoFileClip(str(gif_path))
    main_resized = main_clip.resized(width=target_width)
    w_main_resized, h_main_resized = main_resized.size
    h_gif_area = target_height - h_main_resized
    if h_gif_area <= 0:
        print(
            "Warning: Not enough height for GIF. Outputting only main video without audio."
        )
        main_resized.write_videofile(str(output_path), codec="libx264", logger=None)
        return

    gif_resized = gif_clip_orig.resized(width=target_width)
    w_gif_resized, h_gif_resized = gif_resized.size
    if h_gif_resized > h_gif_area:
        gif_resized = gif_clip_orig.resized(height=h_gif_area)
        w_gif_resized, h_gif_resized = gif_resized.size

    looper = Loop(duration=main_resized.duration)
    gif_looped = looper.apply(gif_resized)

    gif_pos_x = (target_width - w_gif_resized) / 2
    gif_pos_y = (h_gif_area - h_gif_resized) / 2
    main_pos_x = (target_width - w_main_resized) / 2
    main_pos_y = h_gif_area

    gif_positioned = gif_looped.with_position((gif_pos_x, gif_pos_y))
    main_positioned = main_resized.with_position((main_pos_x, main_pos_y))

    video_only_clip = CompositeVideoClip(
        [main_positioned, gif_positioned], size=(target_width, target_height)
    )
    video_duration = video_only_clip.duration

    if audio_paths:
        print(f"Loading {len(audio_paths)} audio segments...")
        audio_clips = [AudioFileClip(str(p)) for p in audio_paths]
        print("Concatenating audio...")
        concatenated_audio = concatenate_audioclips(audio_clips)
        print("Setting final audio duration...")
        final_audio = concatenated_audio.with_duration(video_duration)
        print("Compositing audio onto video...")
        final_clip_with_audio = video_only_clip.with_audio(final_audio)
    else:
        print("Warning: No audio paths provided. Creating video without audio.")
        final_clip_with_audio = video_only_clip

    print("Writing final video file...")
    final_clip_with_audio.write_videofile(
        str(output_path),
        codec="libx264",
        audio_codec="aac" if final_audio else None,
        logger=None,
    )
    print("Video writing complete.")


def process_puzzle(csv_path: str, index: int) -> Tuple[str, List[str], str, str]:
    """Extract FEN, move list, ID, and themes for a puzzle at the given index.

    Args:
        csv_path: Path to the CSV file containing puzzles.
        index: Zero-based index of the puzzle to process.

    Returns:
        A tuple of (FEN string, list of UCI moves, PuzzleId, Themes string).
    """
    df = read_puzzles(csv_path)
    puzzle: pd.Series = df.iloc[index]
    fen: str = puzzle["FEN"]
    moves_str: str = puzzle["Moves"]
    uci_moves: List[str] = moves_str.split(" ")
    puzzle_id: str = puzzle["PuzzleId"]
    themes: str = puzzle["Themes"]
    return fen, uci_moves, puzzle_id, themes


def generate_timestamped_output_path(base_dir: Path, prefix: str, suffix: str) -> Path:
    """Create a timestamped filename within a directory.

    Args:
        base_dir: Directory in which to place the file.
        prefix: Filename prefix (e.g., 'puzzle').
        suffix: File extension including leading dot (e.g., '.mp4').

    Returns:
        A Path object for 'prefix_YYYYMMDD_HHMMSSsuffix'.
    """
    timestamp: str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path: Path = base_dir / f"{prefix}_{timestamp}{suffix}"
    return output_path


def generate_puzzle_caption(
    client: genai.Client, fen: str, uci_moves: List[str], themes: str
) -> str:
    """Generates a text caption/script for a chess puzzle video using the Gemini API.

    Args:
        client: The initialized Gemini Client.
        fen: The starting FEN string of the puzzle.
        uci_moves: The list of moves in UCI format.
        themes: A string describing the puzzle themes.

    Returns:
        The generated text script, designed for ~50 seconds, with [REACTION] placeholders.
    """
    moves_str = " ".join(uci_moves)
    prompt = f"""Generate an engaging script for a ~50-second social media video about a chess puzzle.
The script should commentate on the puzzle moves. Interleave the commentary with placeholders marked exactly as '[REACTION]' where a reaction sound effect or GIF could be inserted to add humor or emphasis. Aim for roughly 150-200 words total.

Puzzle details:
Starting Position (FEN): {fen}
Moves: {moves_str}
Themes: {themes}

Example structure:
"White starts with a surprising move... [REACTION] Black seems to fall for the trap! [REACTION] And now, the checkmate!"

Generate the script now:"""

    print("Generating caption with Gemini...")
    response = client.models.generate_content(
        model="gemini-2.0-flash-lite", contents=prompt
    )
    print("Caption generation complete.")

    cleaned_text = re.sub(r"```(python|text)?\n?|\n?```", "", response.text).strip()
    return cleaned_text


def generate_single_video(
    puzzle_index_to_process: int,
    csv_path: str,
    base_temp_dir_name: str,
    output_dir_path: Path,
    gif_dir_path: Path,
    reaction_audio_dir_path: Path,
    video_fps: int,
    gemini_api_key: str,
) -> Optional[Path]:
    """Generate one puzzle video end-to-end, including interleaved audio."""
    print(f"Starting processing for puzzle index: {puzzle_index_to_process}")
    gemini_client = genai.Client(api_key=gemini_api_key)
    tts_client = texttospeech.TextToSpeechClient()

    temp_dir_path = Path(f"{base_temp_dir_name}_{puzzle_index_to_process}")
    prepare_directory(temp_dir_path)
    base_video_path = None

    fen, uci_moves, puzzle_id, themes = process_puzzle(
        csv_path, puzzle_index_to_process
    )
    caption = generate_puzzle_caption(gemini_client, fen, uci_moves, themes)
    print(
        f"Puzzle {puzzle_index_to_process} (ID: {puzzle_id}) Caption: {caption[:100]}..."
    )
    audio_file_paths = generate_interleaved_audio(
        caption, tts_client, reaction_audio_dir_path, temp_dir_path
    )

    base_video_path = create_base_video(fen, uci_moves, temp_dir_path, video_fps)
    random_gif_path = get_random_gif_path(gif_dir_path)
    final_output_video_path: Path = (
        output_dir_path / f"puzzle_{puzzle_index_to_process}.mp4"
    )
    overlay_gif_on_video(
        base_video_path, random_gif_path, audio_file_paths, final_output_video_path
    )

    print(
        f"Finished processing puzzle index: {puzzle_index_to_process}, saved to {final_output_video_path}"
    )
    return final_output_video_path


def main() -> None:
    """Main entry point: generate multiple puzzle videos in parallel."""
    (
        csv_path,
        temp_png_dir_name,
        output_dir_name,
        video_fps,
        reaction_gif_dir_name,
        gemini_api_key,
        reaction_audio_dir_name,
    ) = load_env_vars()

    output_dir_path = Path(output_dir_name)
    gif_dir_path = Path(reaction_gif_dir_name)
    reaction_audio_dir_path = Path(reaction_audio_dir_name)

    output_dir_path.mkdir(parents=True, exist_ok=True)

    num_videos_to_generate = 10
    puzzle_indices = range(num_videos_to_generate)
    print(f"Starting parallel generation of {num_videos_to_generate} videos...")
    base_temp_dir = Path(temp_png_dir_name)

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(
                generate_single_video,
                idx,
                csv_path,
                str(base_temp_dir),  # Pass the base name as string
                output_dir_path,
                gif_dir_path,
                reaction_audio_dir_path,
                video_fps,
                gemini_api_key,
            )
            for idx in puzzle_indices
        ]
        results: List[Optional[Path]] = []  # Allow for None results on failure
        for task in tqdm(
            concurrent.futures.as_completed(futures),
            total=len(futures),
            desc="Generating videos",
        ):
            outcome = task.result()
            results.append(outcome)

    successful_videos = [res for res in results if res is not None]
    print(
        f"\nFinished parallel generation. {len(successful_videos)} videos successfully generated."
    )


if __name__ == "__main__":
    main()
