import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Configuration settings loaded from environment variables."""

    csv_file_path: str
    temp_png_dir: str = "temp_media/temp_pngs"
    output_dir: str = "temp_media/outputs"
    video_fps: int = 1
    reaction_gif_dir: str = "reaction_gifs"
    reaction_audio_dir: str = "reaction_audios"
    num_videos: int = 100
    target_width: int = 1080
    target_height: int = 1920
    max_workers: int = (os.cpu_count() or 8) // 2

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.

        Returns:
            Config: Configuration instance with values from environment.
        """
        csv_path = os.getenv("CSV_FILE_PATH")
        if not csv_path:
            raise ValueError("CSV_FILE_PATH environment variable is required")

        return cls(
            csv_file_path=csv_path,
            temp_png_dir=os.getenv("TEMP_PNG_DIR_NAME", "temp_media/temp_pngs"),
            output_dir=os.getenv("OUTPUT_DIR_NAME", "temp_media/outputs"),
            video_fps=int(os.getenv("VIDEO_FPS", "1")),
            reaction_gif_dir=os.getenv("REACTION_GIF_DIR", "reaction_gifs"),
            reaction_audio_dir=os.getenv("REACTION_AUDIO_DIR", "reaction_audios"),
            num_videos=int(os.getenv("NUM_VIDEOS", "100")),
            max_workers=int(os.getenv("MAX_WORKERS", str((os.cpu_count() or 8) // 2))),
        )
