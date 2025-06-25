from typing import List, NamedTuple
from pathlib import Path
from google import genai
import json
import os
import logging
import datetime
from .puzzle import Puzzle


class MoveReaction(NamedTuple):
    move_number: int
    move_notation: str
    tactical_type: str
    gif_choice: str
    audio_choice: str
    duration: float  # Will be set from audio file duration


class VideoAnalysis(NamedTuple):
    move_reactions: List[MoveReaction]
    total_duration: float


class GeminiAnalyzer:
    def __init__(self):
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        self._setup_logging()

    def analyze_puzzle(self, puzzle: Puzzle, available_gifs: List[Path], available_audio: List[Path]) -> VideoAnalysis:
        """Analyze chess puzzle for optimal video timing and reactions."""
        gif_info = self._get_media_info(available_gifs)
        audio_info = self._get_media_info(available_audio)

        prompt = self._create_analysis_prompt(puzzle, gif_info, audio_info)
        response = self.client.models.generate_content(model="gemini-2.0-flash-exp", contents=prompt)

        self._log_gemini_interaction(prompt, response.text or "")
        return self._parse_response(response.text or "")

    def _get_media_info(self, files: List[Path]) -> List[dict]:
        """Get basic info about media files."""
        return [{"name": f.stem, "path": str(f)} for f in files]

    def _create_analysis_prompt(self, puzzle: Puzzle, gif_info: List[dict], audio_info: List[dict]) -> str:
        """Create prompt for Gemini to analyze chess moves and recommend reactions."""
        return f"""
You are a chess expert analyzing moves for YouTube shorts. For each chess move, recommend the best reaction GIF and audio.

CHESS PUZZLE:
- Position: {puzzle.fen}
- Moves: {" ".join(puzzle.moves)}

AVAILABLE REACTIONS:
GIFs: {[g["name"] for g in gif_info]}
Audio: {[a["name"] for a in audio_info]}

REACTION GUIDE:
- **Sacrifices/Blunders**: get-out + get-out-sound (shocked reaction)
- **Brilliant Moves**: anime-wow + anime-wow-sound-effect (excitement)
- **Checkmate/Winning**: baby-laughing + baby-laughing-meme (celebration)
- **Quiet/Setup**: vine-boom + vine-boom (suspense)
- **Devastating**: why-are + why-are (disbelief)

RESPONSE FORMAT (JSON only):
{{
  "moves": [
    {{
      "move_number": 1,
      "move_notation": "Qh5+",
      "tactical_type": "sacrifice",
      "gif_choice": "get-out",
      "audio_choice": "get-out-sound"
    }},
    {{
      "move_number": 2,
      "move_notation": "Qxf7#",
      "tactical_type": "checkmate",
      "gif_choice": "baby-laughing",
      "audio_choice": "baby-laughing-meme"
    }}
  ]
}}

Analyze each move and pick the most fitting reaction. Keep it simple and impactful!
"""

    def _setup_logging(self) -> None:
        """Set up logging for Gemini interactions."""
        self.logger = logging.getLogger("gemini_analyzer")
        self.logger.setLevel(logging.INFO)

        if not self.logger.handlers:
            handler = logging.FileHandler("gemini.out", mode="a", encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _log_gemini_interaction(self, prompt: str, response: str) -> None:
        """Log Gemini prompt and response to file."""
        timestamp = datetime.datetime.now().isoformat()

        self.logger.info("=" * 80)
        self.logger.info(f"GEMINI INTERACTION - {timestamp}")
        self.logger.info("=" * 80)
        self.logger.info("PROMPT:")
        self.logger.info(prompt)
        self.logger.info("-" * 40)
        self.logger.info("RESPONSE:")
        self.logger.info(response)
        self.logger.info("=" * 80)

    def _parse_response(self, response_text: str) -> VideoAnalysis:
        """Parse Gemini response and add audio durations."""
        try:
            clean_response = response_text.strip().replace("```json", "").replace("```", "")
            data = json.loads(clean_response)

            # Get audio file durations
            audio_durations = self._get_audio_durations()

            move_reactions = []
            total_duration = 0.0

            for move_data in data["moves"]:
                # Get duration from audio file
                audio_choice = move_data["audio_choice"]
                duration = audio_durations.get(audio_choice, 2.0)  # Default 2 seconds

                move_reaction = MoveReaction(
                    move_number=move_data["move_number"],
                    move_notation=move_data["move_notation"],
                    tactical_type=move_data["tactical_type"],
                    gif_choice=move_data["gif_choice"],
                    audio_choice=audio_choice,
                    duration=duration,
                )
                move_reactions.append(move_reaction)
                total_duration += duration

            analysis = VideoAnalysis(move_reactions=move_reactions, total_duration=total_duration)

            self.logger.info(f"Successfully parsed {len(move_reactions)} moves with audio-synced durations")
            for move in move_reactions:
                self.logger.info(f"Move {move.move_number}: {move.move_notation} → {move.audio_choice} ({move.duration}s)")

            return analysis
        except Exception as e:
            self.logger.error(f"Failed to parse Gemini response: {e}")
            self.logger.error(f"Raw response: {response_text}")
            return self._create_fallback_analysis(4)

    def _get_audio_durations(self) -> dict:
        """Get actual audio file durations."""
        from moviepy import AudioFileClip
        from pathlib import Path

        audio_durations = {}
        audio_dir = Path("reaction_audios")

        if audio_dir.exists():
            for audio_file in audio_dir.glob("*.mp3"):
                clip = AudioFileClip(str(audio_file))
                audio_durations[audio_file.stem] = float(clip.duration)
                clip.close()

        self.logger.info(f"Audio durations: {audio_durations}")
        return audio_durations

    def _create_fallback_analysis(self, num_moves: int) -> VideoAnalysis:
        """Create fallback analysis with audio-synced durations."""
        audio_durations = self._get_audio_durations()
        vine_boom_duration = audio_durations.get("vine-boom", 2.0)

        fallback_moves = [
            MoveReaction(move_number=i + 1, move_notation=f"Move{i + 1}", tactical_type="quiet", gif_choice="vine-boom", audio_choice="vine-boom", duration=vine_boom_duration)
            for i in range(num_moves)
        ]

        total_duration = vine_boom_duration * num_moves

        analysis = VideoAnalysis(move_reactions=fallback_moves, total_duration=total_duration)

        self.logger.warning(f"Using fallback analysis for {num_moves} moves with audio duration {vine_boom_duration}s")
        return analysis
