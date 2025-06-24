from pathlib import Path
import shutil


def prepare_directory(dir_path: Path) -> Path:
    """Prepare directory by removing and recreating it.

    Args:
        dir_path: Path - Directory path to prepare

    Returns:
        Path: The prepared directory path
    """
    shutil.rmtree(dir_path, ignore_errors=True)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def ensure_directory(dir_path: Path) -> Path:
    """Ensure directory exists without removing existing content.

    Args:
        dir_path: Path - Directory path to ensure

    Returns:
        Path: The directory path
    """
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path
