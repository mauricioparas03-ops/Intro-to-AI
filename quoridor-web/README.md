# Quoridor AI Project

This project is a modification of the original [quoridor-web](https://github.com/iliagrigorevdev/quoridor-web) game. The built-in ONNX-based AI has been completely removed and replaced with a bridge to an external Python server. This allows for the development and testing of a custom Quoridor AI, written from scratch in Python, as a separate entity from the game engine and UI.

## Setup and Installation

Follow these steps to set up the local environment and run the project.

### 1. Clone the Repository

First, clone this repository to your local machine using git.

```bash
git clone <YOUR_REPOSITORY_URL>
cd <repository-folder-name>
```

### 2. Set Up a Python Environment (Recommended)

Recommend using a virtual environment to manage project dependencies and avoid conflicts with other Python projects. You can use either `conda` or Python's built-in `venv`.

#### Option A: Using `conda`

Anaconda install link: https://docs.anaconda.com/anaconda/install/

```bash
# Create a new conda environment (can be call quoridor for example)
conda create --name quoridor python=3.10

# Activate the environment
conda activate quoridor
```

#### Option B: Using `venv`

```bash
# Create a new virtual environment in a folder named "venv"
python3 -m venv venv

# Activate the environment
# On macOS and Linux:
source venv/bin/activate

# On Windows (Command Prompt):
.\venv\Scripts\activate
```

### 3. Install Required Packages

This project's Python dependencies are listed in `requirements.txt`. 

Once conda environment or python venv is activated, install the dependencies using pip.

```bash
pip install -r requirements.txt
```
This will install the following packages:
- `fastapi`: For creating the API server.
- `uvicorn`: To run the FastAPI server.
- `pydantic`: For data validation.

## How to Run the Game

The system consists of two separate parts that must be running at the same time: the **AI Server** (Python backend) and the **Web Server** (JavaScript frontend). You will need to open two separate terminal windows.

---

### Terminal 1: Start the AI Server

Navigate to the project's root directory (`/quoridor`) and run the `ai_server.py` script. The AI server can be run in two modes.

#### AI Mode (Default)
This mode runs the AI player defined in the `get_ai_move` function.
```bash
python3 ai_server.py --mode ai
```

#### Manual Mode
This mode is for debugging. When it's the AI's turn, the server will pause and prompt you to enter a move directly into this terminal.
```bash
python3 ai_server.py --mode manual
```

---

### Terminal 2: Start the Web Server

Navigate into the `/quoridor/quoridor-web` directory and run the `serve.py` script. This will serve the game's user interface.

```bash
cd quoridor-web
python3 serve.py
```
This server will host the game on port 8080.

---

### 4. Play the Game

Once both servers are running, open your web browser and navigate to:

**http://localhost:8080**

Click on **"Player vs Bot"** to start a game. When you make a move, the browser will send the game state to your AI server, which will then respond with the AI's move. You can see the communication logs in the AI Server terminal.


### TODO
Add AI player (Minimax, Alpha beta pruning, Monte Carlo Tree Search) in the '`get_ai_move` function in the `ai_server.py` file or create a new file that is called there.