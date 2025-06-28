from typing import List, Dict, Tuple
from pathlib import Path
import random
from .puzzle import Puzzle


class ReactionSelector:
    """Rule-based reaction selector using file name analysis."""

    def __init__(self, gif_dir: Path, audio_dir: Path):
        self.gif_dir = gif_dir
        self.audio_dir = audio_dir
        self._categorize_media()

    def _categorize_media(self) -> None:
        """Categorize available media files by emotion/reaction type."""
        self.gif_categories: Dict[str, List[Path]] = {
            "excitement": [],
            "shock": [],
            "calculation": [],
            "anger": [],
        }

        self.audio_categories: Dict[str, List[Path]] = {
            "excitement": [],
            "shock": [],
            "meme": [],
        }

        for gif_file in self.gif_dir.glob("*.gif"):
            stem = gif_file.stem.lower()
            if "excitement" in stem:
                self.gif_categories["excitement"].append(gif_file)
            elif "shocked" in stem:
                self.gif_categories["shock"].append(gif_file)
            elif "calculation" in stem:
                self.gif_categories["calculation"].append(gif_file)
            elif "pissed" in stem:
                self.gif_categories["anger"].append(gif_file)

        for audio_file in self.audio_dir.glob("*.mp3"):
            stem = audio_file.stem.lower()
            if "anime-wow" in stem or "baby-laughing" in stem:
                self.audio_categories["excitement"].append(audio_file)
            elif "get-out" in stem or "why-are" in stem:
                self.audio_categories["shock"].append(audio_file)
            elif "vine-boom" in stem:
                self.audio_categories["meme"].append(audio_file)

    def select_reaction(self, puzzle: Puzzle, move_index: int) -> Tuple[Path, Path]:
        """Select optimal GIF and audio for a specific move."""
        is_last_move = move_index == len(puzzle.moves) - 1
        is_first_move = move_index == 0

        if is_last_move:
            gif_category = "excitement"
            audio_category = "excitement"
        elif is_first_move:
            gif_category = "calculation"
            audio_category = "meme"
        else:
            gif_category = "shock"
            audio_category = "shock"

        gif_file = self._select_from_category(self.gif_categories, gif_category)
        audio_file = self._select_from_category(self.audio_categories, audio_category)

        return gif_file, audio_file

    def _select_from_category(self, categories: Dict[str, List[Path]], category: str) -> Path:
        """Select random file from category with fallback."""
        if category in categories and categories[category]:
            return random.choice(categories[category])

        all_files = []
        for file_list in categories.values():
            all_files.extend(file_list)

        return random.choice(all_files) if all_files else self._get_fallback_file(categories)

    def _get_fallback_file(self, categories: Dict[str, List[Path]]) -> Path:
        """Get fallback file when no categorized files found."""
        if "gif" in str(self.gif_dir):
            return self.gif_dir / "default.gif"
        return self.audio_dir / "default.mp3"
