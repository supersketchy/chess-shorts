import pandas as pd
import os
from dotenv import load_dotenv
import chess
import chess.svg
import cairosvg
from moviepy import ImageSequenceClip
import shutil

load_dotenv()

csv_file_path = os.getenv("CSV_FILE_PATH")
temp_png_dir = "temp_pngs"
output_video_path = "puzzle_solution.mp4"

column_names = [
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

df = pd.read_csv(csv_file_path, names=column_names, header=0)
first_puzzle = df.iloc[0]
fen = first_puzzle["FEN"]
moves_str = first_puzzle["Moves"]
uci_moves = moves_str.split(' ')

board = chess.Board(fen)
png_files = []

if os.path.exists(temp_png_dir):
    shutil.rmtree(temp_png_dir)
os.makedirs(temp_png_dir)

# Initial board state
frame_num = 0
svg_initial = chess.svg.board(board=board)
png_path = os.path.join(temp_png_dir, f"frame_{frame_num:03d}.png")
cairosvg.svg2png(bytestring=svg_initial.encode('utf-8'), write_to=png_path)
png_files.append(png_path)

# Apply moves and generate frames
for uci_move in uci_moves:
    frame_num += 1
    move = chess.Move.from_uci(uci_move)
    board.push(move)
    boardsvg = chess.svg.board(board=board, lastmove=move)
    png_path = os.path.join(temp_png_dir, f"frame_{frame_num:03d}.png")
    cairosvg.svg2png(bytestring=boardsvg.encode('utf-8'), write_to=png_path)
    png_files.append(png_path)

# Create video from PNG frames
clip = ImageSequenceClip(png_files, fps=1) # 1 frame per second, will change later
clip.write_videofile(output_video_path, codec='libx264')

# Clean up temporary files
shutil.rmtree(temp_png_dir)

print(f"Generated video for the first puzzle solution and saved to {output_video_path}")
