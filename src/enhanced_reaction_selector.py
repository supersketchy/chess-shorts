from typing import List, Dict, Tuple, NamedTuple
from pathlib import Path
import random
from .puzzle import Puzzle


class ReactionTiming(NamedTuple):
    """Timing configuration for reactions."""

    duration: float
    energy_level: str
    priority: int


class EnhancedReactionSelector:
    """Advanced reaction selector with context awareness and quality ranking."""

    def __init__(self, gif_dir: Path, audio_dir: Path):
        self.gif_dir = gif_dir
        self.audio_dir = audio_dir
        self._categorize_media()
        self._rank_media_quality()

    def _categorize_media(self) -> None:
        """Categorize available media files by emotion/reaction type."""
        self.gif_categories: Dict[str, List[Path]] = {
            "excitement": [],
            "shock": [],
            "calculation": [],
            "anger": [],
            "celebration": [],
            "suspense": [],
        }

        self.audio_categories: Dict[str, List[Path]] = {
            "high_energy": [],
            "dramatic": [],
            "suspense": [],
            "celebration": [],
            "meme": [],
        }

        for gif_file in self.gif_dir.glob("*.gif"):
            stem = gif_file.stem.lower()
            if "excitement" in stem:
                self.gif_categories["excitement"].append(gif_file)
                self.gif_categories["celebration"].append(gif_file)
            elif "shocked" in stem:
                self.gif_categories["shock"].append(gif_file)
            elif "calculation" in stem:
                self.gif_categories["calculation"].append(gif_file)
                self.gif_categories["suspense"].append(gif_file)
            elif "pissed" in stem or "angry" in stem:
                self.gif_categories["anger"].append(gif_file)

        for audio_file in self.audio_dir.glob("*.mp3"):
            stem = audio_file.stem.lower()
            if "anime-wow" in stem or "baby-laughing" in stem:
                self.audio_categories["high_energy"].append(audio_file)
                self.audio_categories["celebration"].append(audio_file)
            elif "get-out" in stem or "why-are" in stem:
                self.audio_categories["dramatic"].append(audio_file)
            elif "vine-boom" in stem:
                self.audio_categories["suspense"].append(audio_file)
                self.audio_categories["meme"].append(audio_file)

    def _rank_media_quality(self) -> None:
        """Rank media files by quality indicators."""
        quality_streamers = ["magnus", "hikaru"]

        for category in self.gif_categories:
            self.gif_categories[category] = sorted(
                self.gif_categories[category],
                key=lambda g: (
                    any(streamer in g.stem.lower() for streamer in quality_streamers),
                    len(g.stem),
                ),
                reverse=True,
            )

    def select_reaction_by_context(self, puzzle: Puzzle, move_index: int) -> Tuple[Path, Path, ReactionTiming]:
        """Select reaction based on puzzle context and themes."""
        themes = puzzle.themes.lower() if puzzle.themes else ""
        move_count = len(puzzle.moves)
        is_final_move = move_index == move_count - 1
        is_setup_move = move_index == 0

        timing = self._calculate_move_timing(puzzle, move_index)

        if "mate" in themes or "crushing" in themes:
            gif_category, audio_category = "celebration", "celebration"
        elif "hangingpiece" in themes or "fork" in themes or "pin" in themes:
            gif_category, audio_category = "shock", "dramatic"
        elif "endgame" in themes or is_final_move:
            gif_category, audio_category = "excitement", "high_energy"
        elif "sacrifice" in themes or "deflection" in themes:
            gif_category, audio_category = "shock", "dramatic"
        elif is_setup_move or "quiet" in themes:
            gif_category, audio_category = "calculation", "suspense"
        else:
            gif_category, audio_category = "suspense", "meme"

        gif_file = self._select_quality_file(self.gif_categories, gif_category)
        audio_file = self._select_audio_by_energy(audio_category, timing.energy_level)

        return gif_file, audio_file, timing

    def _calculate_move_timing(self, puzzle: Puzzle, move_index: int) -> ReactionTiming:
        """Calculate dynamic timing based on move importance and puzzle difficulty."""
        base_duration = 1.8
        move_count = len(puzzle.moves)
        rating = puzzle.rating

        if move_index == move_count - 1:
            duration = base_duration * 2.5
            energy = "high"
            priority = 10
        elif move_index == 0:
            duration = base_duration * 1.8
            energy = "medium"
            priority = 7
        elif rating > 2000:
            duration = base_duration * 2.0
            energy = "high"
            priority = 8
        elif rating > 1600:
            duration = base_duration * 1.5
            energy = "medium"
            priority = 6
        else:
            duration = base_duration * 1.2
            energy = "low"
            priority = 5

        return ReactionTiming(duration, energy, priority)

    def _select_quality_file(self, categories: Dict[str, List[Path]], category: str) -> Path:
        """Select highest quality file from category."""
        if category in categories and categories[category]:
            return categories[category][0]

        all_files = []
        for file_list in categories.values():
            all_files.extend(file_list)

        return all_files[0] if all_files else self._get_fallback_file("gif")

    def _select_audio_by_energy(self, category: str, energy_level: str) -> Path:
        """Select audio file matching energy level."""
        if category in self.audio_categories and self.audio_categories[category]:
            candidates = self.audio_categories[category]

            if energy_level == "high" and "high_energy" in self.audio_categories:
                candidates = self.audio_categories["high_energy"]
            elif energy_level == "low" and "suspense" in self.audio_categories:
                candidates = self.audio_categories["suspense"]

            return random.choice(candidates)

        return self._get_fallback_file("audio")

    def _get_fallback_file(self, media_type: str) -> Path:
        """Get fallback file when no categorized files found."""
        if media_type == "gif":
            all_gifs = list(self.gif_dir.glob("*.gif"))
            return random.choice(all_gifs) if all_gifs else self.gif_dir / "default.gif"
        else:
            all_audio = list(self.audio_dir.glob("*.mp3"))
            return random.choice(all_audio) if all_audio else self.audio_dir / "default.mp3"
