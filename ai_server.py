# ai_server.py
import argparse
import os
import random
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from quoridor_5x5_env import GameState5x5, get_next_states

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
    p1_walls_remaining: int
    p2_walls_remaining: int

#class GameState(BaseModel):
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

from ai_agent import choose_ai_move

def get_ai_move(state: GameState):
    print(f"AI Thinking... (Turn: {state.turn}, P1: {state.p1_pos}, P2: {state.p2_pos})")

    # construir el estado usando la clase de tu compañero
    game_state = GameState5x5(
        p1_pos=state.p1_pos,
        p2_pos=state.p2_pos,
        p1_walls=state.p1_walls,
        p2_walls=state.p2_walls,
        h_walls=state.h_walls,
        v_walls=state.v_walls,
        turn=state.turn
    )

    next_states = get_next_states(game_state)

    if not next_states:
        raise RuntimeError("No possible next states for AI.")

    # por ahora elegimos el primero
    chosen = next_states[0]["action"]

    if chosen["type"] == "move":
        return {
            "action_type": "move",
            "coordinates": list(chosen["pos"])
        }
    else:
        return {
            "action_type": "wall",
            "coordinates": list(chosen["pos"]),
            "orientation": "horizontal" if chosen["orientation"] == "h" else "vertical"
        }
#def get_ai_move(state: GameState):
    print(f"AI Thinking... (Turn: {state.turn}, P1: {state.p1_pos}, P2: {state.p2_pos})")
    
    # TODO 
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
