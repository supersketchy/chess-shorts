import os
from dotenv import load_dotenv

load_dotenv()

csv_file_path = os.getenv("CSV_FILE_PATH", "puzzles/lichess_db_puzzle.csv")
temp_dir = os.getenv("TEMP_DIR", "temp")
output_dir = os.getenv("OUTPUT_DIR", "outputs")
video_fps = int(os.getenv("VIDEO_FPS", "1"))
reaction_gif_dir = os.getenv("REACTION_GIF_DIR", "reaction_gifs")
reaction_audio_dir = os.getenv("REACTION_AUDIO_DIR", "reaction_audios")
num_videos = int(os.getenv("NUM_VIDEOS", "100"))
target_width = 1080
target_height = 1920
max_workers = int(os.getenv("MAX_WORKERS", "16"))
