from typing import NamedTuple
import pandas as pd


class Puzzle(NamedTuple):
    """Chess puzzle data.

    Attributes:
        puzzle_id (str): Unique puzzle identifier.
        fen (str): Chess position in FEN notation.
        moves (list[str]): List of UCI moves.
    """

    puzzle_id: str
    fen: str
    moves: list[str]


def get_puzzle(csv_path: str, index: int) -> Puzzle:
    """Load puzzle from CSV at given index.

    Args:
        csv_path (str): Path to the CSV file.
        index (int): Zero-based index of the puzzle.

    Returns:
        Puzzle: Puzzle data at the specified index.
    """
    columns = ["PuzzleId", "FEN", "Moves", "Rating", "RatingDeviation", "Popularity", "NbPlays", "Themes", "GameUrl", "OpeningTags"]
    df = pd.read_csv(csv_path, names=columns, header=0)
    row = df.iloc[index]
    return Puzzle(puzzle_id=str(row["PuzzleId"]), fen=str(row["FEN"]), moves=str(row["Moves"]).split())
