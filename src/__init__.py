"""Chess puzzle video generation package."""

from .main import main, generate_videos_parallel
from .config import Config

__all__ = ["main", "generate_videos_parallel", "Config"]
