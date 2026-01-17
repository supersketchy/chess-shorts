import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    """Configuration settings for video generation.

    Attributes:
        csv_file_path (str): Path to chess puzzle CSV file.
        temp_dir (str): Directory for all temporary files.
        output_dir (str): Directory for output videos.
        video_fps (int): Frames per second for videos.
        reaction_gif_dir (str): Directory containing reaction GIFs.
        reaction_audio_dir (str): Directory containing reaction audio.
        num_videos (int): Number of videos to generate.
        target_width (int): Target video width in pixels.
        target_height (int): Target video height in pixels.
        max_workers (int): Number of parallel workers.
    """

    csv_file_path: str
    temp_dir: str = "temp"
    output_dir: str = "outputs"
    video_fps: int = 1
    reaction_gif_dir: str = "reaction_gifs"
    reaction_audio_dir: str = "reaction_audios"
    num_videos: int = 100
    target_width: int = 1080
    target_height: int = 1920
    max_workers: int = 1

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables.

        Returns:
            Config: Configuration instance with values from environment.

        Raises:
            ValueError: If CSV_FILE_PATH is not set.
        """
        csv_path = os.getenv("CSV_FILE_PATH")
        if not csv_path:
            raise ValueError("CSV_FILE_PATH environment variable is required")
        return cls(
            csv_file_path=csv_path,
            temp_dir=os.getenv("TEMP_DIR", "temp"),
            output_dir=os.getenv("OUTPUT_DIR", "outputs"),
            video_fps=int(os.getenv("VIDEO_FPS", "1")),
            reaction_gif_dir=os.getenv("REACTION_GIF_DIR", "reaction_gifs"),
            reaction_audio_dir=os.getenv("REACTION_AUDIO_DIR", "reaction_audios"),
            num_videos=int(os.getenv("NUM_VIDEOS", "100")),
            max_workers=int(os.getenv("MAX_WORKERS", str(1))),
        )
