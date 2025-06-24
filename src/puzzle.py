from typing import List, NamedTuple
import pandas as pd


class Puzzle(NamedTuple):
    """Chess puzzle data structure.

    Attributes:
        puzzle_id: str - Unique puzzle identifier
        fen: str - Chess position in FEN notation
        moves: List[str] - List of UCI moves
    """

    puzzle_id: str
    fen: str
    moves: List[str]


def load_puzzles(csv_path: str) -> pd.DataFrame:
    """Load puzzles from CSV file.

    Args:
        csv_path: str - Path to the CSV file containing puzzles

    Returns:
        pd.DataFrame: DataFrame containing puzzle data
    """
    columns = [
        "PuzzleId",
        "FEN",
        "Moves",
        "Rating",
        "RatingDeviation",
        "Popularity",
        "NbPlays",
        "Themes",
        "GameUrl",
        "OpeningTags",
    ]
    return pd.read_csv(csv_path, names=columns, header=0)


def get_puzzle(csv_path: str, index: int) -> Puzzle:
    """Extract puzzle data at given index.

    Args:
        csv_path: str - Path to the CSV file
        index: int - Zero-based index of the puzzle

    Returns:
        Puzzle: Puzzle data structure
    """
    df = load_puzzles(csv_path)
    row = df.iloc[index]
    return Puzzle(
        puzzle_id=str(row["PuzzleId"]),
        fen=str(row["FEN"]),
        moves=str(row["Moves"]).split(" "),
    )
