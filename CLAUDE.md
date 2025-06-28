# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

- **Run the application**: `python main.py`
- **Install dependencies**: `pixi install` (Pixi package manager is used)
- **Format code**: `ruff format` (configured with 200 char line length)
- **Lint code**: `ruff check`

## Environment Setup

Create a `.env` file with required environment variables:
- `CSV_FILE_PATH`: Path to the chess puzzle CSV file (e.g., `puzzles/lichess_db_puzzle.csv`)

Optional environment variables with defaults:
- `TEMP_PNG_DIR_NAME`: Directory for temporary PNG files (default: "temp_media/temp_pngs")
- `OUTPUT_DIR_NAME`: Directory for output videos (default: "temp_media/outputs")
- `VIDEO_FPS`: Frame rate for videos (default: 1)
- `REACTION_GIF_DIR`: Directory containing reaction GIFs (default: "reaction_gifs")
- `REACTION_AUDIO_DIR`: Directory containing reaction audio files (default: "reaction_audios")
- `NUM_VIDEOS`: Number of videos to generate (default: 100)
- `MAX_WORKERS`: Parallel processing workers (default: half of CPU cores)
- `VIDEO_TEMPLATE`: Template style ("engaging", "clean", "speed") (default: "engaging")
- `ENABLE_MULTI_REACTIONS`: Enable per-move reactions (default: true)
- `ENABLE_VISUAL_ENHANCEMENTS`: Enable visual overlays and effects (default: true)

## Architecture Overview

This is a chess puzzle video generator that creates short-form videos (YouTube Shorts format) by:

1. **Puzzle Processing**: Loads chess puzzles with themes, ratings, and metadata from CSV files
2. **Context-Aware Reactions**: Analyzes puzzle themes to select appropriate reactions for each move
3. **Visual Rendering**: Generates PNG sequences of chess board states using chess.svg and cairosvg
4. **Enhanced Video Composition**: Creates multi-reaction videos with visual overlays, gradients, and effects
5. **Audio Synchronization**: Applies crossfading, normalization, and energy-matched audio selection
6. **Parallel Processing**: Generates multiple videos concurrently using ProcessPoolExecutor

### Key Components

- `src/main.py`: Entry point with parallel video generation orchestration
- `src/config.py`: Environment-based configuration management with enhancement toggles
- `src/puzzle.py`: Enhanced puzzle data structures with themes, ratings, and metadata
- `src/chess_renderer.py`: Chess board visualization and PNG generation
- `src/enhanced_reaction_selector.py`: Context-aware reaction selection using puzzle themes and quality ranking
- `src/enhanced_video_editor.py`: Advanced video composition with multi-reactions, visual effects, and templates
- `src/video_editor.py`: Legacy video composition for backward compatibility
- `src/utils.py`: File system utilities and directory management

### Enhanced Features

- **Context-Aware Selection**: Reactions based on puzzle themes (mate, fork, sacrifice, etc.)
- **Dynamic Timing**: Move duration varies based on difficulty and importance
- **Multi-Reaction System**: Different reaction for each move instead of single reaction
- **Visual Enhancements**: Gradient backgrounds, difficulty badges, progress indicators
- **Audio Improvements**: Crossfading, normalization, energy-level matching
- **Engagement Hooks**: Opening text to increase viewer retention
- **Template System**: Multiple video styles (engaging, clean, speed)
- **Quality Ranking**: Prefer high-quality GIFs from known streamers

### Data Flow

1. Load puzzles from CSV → Parse FEN, moves, themes, and ratings
2. Render chess board sequence → Generate PNG frames for each move
3. Analyze puzzle context → Select appropriate reactions per move based on themes
4. Create enhanced video clips → Add visual effects, gradients, and overlays
5. Synchronize audio → Apply crossfading and energy-matched selection
6. Composite final video → Combine all elements with engagement hooks

The system is designed for batch processing with configurable parallelism and uses temporary directories that are cleaned up after each video generation.

IMPORTANT: All code generated should be short and concise, with absolutely no comments/try-except blocks and proper typing and docstrings (with the docstrings having types within them).
