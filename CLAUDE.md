# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

- **Run the application**: `python -m src.main`
- **Install dependencies**: `pixi install` (Pixi package manager is used)
- **Format code**: `ruff format` (configured with 200 char line length)
- **Lint code**: `ruff check`

## Environment Setup

Create a `.env` file with required environment variables:
- `CSV_FILE_PATH`: Path to the chess puzzle CSV file (e.g., `puzzles/lichess_db_puzzle.csv`)

Optional environment variables with defaults:
- `TEMP_DIR`: Directory for temporary files (default: "temp")
- `OUTPUT_DIR`: Directory for output videos (default: "outputs")
- `VIDEO_FPS`: Frame rate for videos (default: 1)
- `REACTION_GIF_DIR`: Directory containing reaction GIFs (default: "reaction_gifs")
- `REACTION_AUDIO_DIR`: Directory containing reaction audio files (default: "reaction_audios")
- `NUM_VIDEOS`: Number of videos to generate (default: 100)
- `MAX_WORKERS`: Parallel processing workers (default: half of CPU cores)

## Architecture Overview

This is a chess puzzle video generator that creates short-form videos (YouTube Shorts format) by:

1. **Puzzle Processing**: Loads chess puzzles from CSV files and converts FEN/moves to board states
2. **Visual Rendering**: Generates PNG sequences of chess board states using chess.svg and cairosvg
3. **Video Composition**: Combines board animations with reaction GIFs and audio using MoviePy
4. **Parallel Processing**: Generates multiple videos concurrently using ProcessPoolExecutor

### Key Components

- `src/main.py`: Entry point with parallel video generation orchestration
- `src/config.py`: Environment-based configuration management
- `src/puzzle.py`: Chess puzzle data structures and CSV parsing
- `src/chess_renderer.py`: Chess board visualization and PNG generation
- `src/video_editor.py`: Video composition and effects processing

### Data Flow

1. Load puzzles from CSV → Parse FEN and moves
2. Render chess board sequence → Generate PNG frames
3. Create base video from PNGs → Use simple timing
4. Select random reaction GIF and audio
5. Composite with reaction GIF and audio → Output final video

The system is designed for batch processing with configurable parallelism. All temporary files are stored in a single `temp/` directory and cleaned up after video generation completes.

IMPORTANT: All code generated should be short and concise, with absolutely no comments/try-except blocks and proper typing and docstrings (with the docstrings having types within them).
