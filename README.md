# Quoridor AI Project

## About the project
This project is a modification of the classic Quoridor board game, adapted for a 5x5 grid. It was created as an assignment for the 02180 Intro to Artificial Intelligence course. The primary goal of this project is to help students understand the practical implementation of an Artificial Intelligence agent (using Minimax and Alpha-Beta Pruning) into a functional board game environment.

## Requirements & Installation

To run the game and the benchmarking tools, you will need Python installed on your computer along with a few dependencies (like matplotlib for the graphs).

1. **Clone or download** this repository to your local machine.
2. **Open your terminal** or command prompt and navigate to the project folder.
3. **Install the required dependencies** by running the following command:
   ```bash
   pip install -r requirements.txt

## How to Play

1. Open your terminal in the project folder.
2. Start the game by running:
   ```bash
   python play_game.py
3. A graphical window will open where you can play against the AI using the following controls:
    1. To Move: Click the Move button on the screen, then select any of the green highlighted squares (allowed moves) to move your pawn.
    2. To Place a Horizontal Wall: Click the Horizontal Wall button, preview your placement on the board, and click to place it.
    3. To Place a Vertical Wall: Click the Vertical Wall button, preview your placement, and click to drop it onto the board.
**Note:** The game environment enforces the rules of Quoridor. You cannot place a wall that completely blocks a player from reaching their goal line.

## Project Structure & File Logic
Below is a breakdown of the core files and the logic driving the game and the AI:

* **`play_game.py`**: The main executable script. This handles the interactive graphical user interface (GUI) and the core game loop, allowing you to play against the AI using on-screen buttons.
* **`quoridor_5x5_env.py`**: The Game Environment. This acts as the referee. It contains all the strict rules of Quoridor, tracks where pawns and walls are, validates if a move is legal, and generates all possible future board states for the AI to analyze.
* **`abpruning.py`**: The AI Brain. This file contains the heuristic function (which mathematically calculates how "good" or "bad" a specific board layout is) and the Alpha-Beta Pruning algorithm, which allows the computer to look multiple turns into the future to pick the best move efficiently.
* **`benchmarking.py`**: A testing utility. Run `python benchmarking.py` to compare the performance of standard Minimax versus Alpha-Beta Pruning. It generates graphs showing how much time and processing power the pruning algorithm saves.





