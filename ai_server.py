# ai_server.py
import argparse
import os
import random
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from quoridor_5x5_env import GameState5x5
from abpruning import alpha_beta_search

app = FastAPI()

# Enable CORS to allow the browser to communicate with this server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to track the operating mode ('ai' or 'manual')
SERVER_MODE = "ai"

class GameState(BaseModel):
    p1_pos: list[int]
    p2_pos: list[int]
    walls: list[list[int]]
    turn: int

def get_manual_move(state: GameState):
    """
    Blocks execution and asks the user to input a move via the terminal.
    Useful for debugging the game engine or playing as the 'bot'.
    """
    print("\n" + "="*40)
    print(">>> IT IS THE AI'S TURN (MANUAL CONTROL) <<<")
    print(f"Current State: Turn {state.turn} | P1: {state.p1_pos} | P2: {state.p2_pos}")
    print("Enter one of the following commands:")
    print("  Move Pawn:  m <x> <y>       (e.g., 'm 2 3')")
    print("  Place Wall: w <x> <y> <h/v> (e.g., 'w 1 1 h' for horizontal)")
    print("="*40)
    
    while True:
        try:
            # Read input from terminal
            user_input = input("Enter AI Move > ").strip().lower().split()
            if not user_input: continue
            
            cmd = user_input[0]
            
            if cmd == 'm' and len(user_input) == 3:
                # Move format: m x y
                return {
                    "action_type": "move", 
                    "coordinates": [int(user_input[1]), int(user_input[2])]
                }
            elif cmd == 'w' and len(user_input) == 4:
                # Wall format: w x y orientation
                orientation = "horizontal" if user_input[3].startswith('h') else "vertical"
                return {
                    "action_type": "wall", 
                    "coordinates": [int(user_input[1]), int(user_input[2])],
                    "orientation": orientation
                }
            else:
                print("Invalid command format. Please try again.")
        except ValueError:
            print("Invalid coordinates. Please enter numbers.")
        except Exception as e:
            print(f"Error: {e}")

def get_ai_move(state: GameState):
    print(f"AI Thinking... (Turn: {state.turn}, P1: {state.p1_pos}, P2: {state.p2_pos})")
        
    # 1. Translate the UI JSON into our high-speed environment state
    # Note: Ensure you track or extract the remaining walls correctly. 
    # Here we assume a static 3 for the example, but you should derive it from the UI state if possible.
    h_walls = [w[:2] for w in state.walls if w[2] == 0] # Assuming 0 is horizontal
    v_walls = [w[:2] for w in state.walls if w[2] == 1] # Assuming 1 is vertical
    
    current_state = GameState5x5(
        p1_pos=state.p1_pos,
        p2_pos=state.p2_pos,
        p1_walls=3 - (len(state.walls) // 2), # We need to find how to track the walls and update this correctly 
        p2_walls=3 - (len(state.walls) // 2), 
        h_walls=h_walls,
        v_walls=v_walls,
        turn=state.turn
    )
    
    # 2. Run Alpha-Beta Pruning
    # A depth of 3 or 4 is usually a good starting point for a 5x5 board
    SEARCH_DEPTH = 3 
    
    best_score, best_action = alpha_beta_search(
        state=current_state, 
        depth=SEARCH_DEPTH, 
        alpha=float('-inf'), 
        beta=float('inf'), 
        is_maximizing=True, 
        ai_player_id=state.turn
    )
    
    # 3. Translate the chosen action back to the UI's JSON format
    if best_action["type"] == "move":
        return {
            "action_type": "move",
            "coordinates": list(best_action["pos"])
        }
    elif best_action["type"] == "wall":
        return {
            "action_type": "wall",
            "coordinates": list(best_action["pos"]),
            # Format orientation string as expected by your UI
            "orientation": "horizontal" if best_action["orientation"] == 'h' else "vertical" 
        }

    # Add AI agent code or import from another python file (e.g. Alpha-beta, Monte Carlo Tree Search)
    
    # Placeholder code that does random moves, just to show function works:
    if random.random() > 0.6:
        # random Move
        current_pos = state.p1_pos if state.turn == 1 else state.p2_pos
        moves = [[0, 1], [0, -1], [1, 0], [-1, 0]]
        dx, dy = random.choice(moves)
        return {
            "action_type": "move",
            "coordinates": [current_pos[0] + dx, current_pos[1] + dy]
        }
    else:
        # random Wall
        return {
            "action_type": "wall",
            "coordinates": [random.randint(0, 4), random.randint(0, 4)],
            "orientation": "horizontal" if random.random() > 0.5 else "vertical"
        }

@app.post("/get_move")
def calculate_move(state: GameState):
    if SERVER_MODE == "manual":
        return get_manual_move(state)
    else:
        return get_ai_move(state)

if __name__ == "__main__":
    # Setup command line argument parsing
    parser = argparse.ArgumentParser(description="Quoridor AI Server")
    parser.add_argument("--mode", choices=["ai", "manual"], default="ai")
    parser.add_argument("--port", type=int, default=8000)
    
    args = parser.parse_args()
    SERVER_MODE = args.mode
    
    print(f"Starting server in {SERVER_MODE.upper()} mode on port {args.port}...")
    
    # Run the server directly (programmatic execution instead of using 'uvicorn' command in shell)
    uvicorn.run(app, host="127.0.0.1", port=args.port)
