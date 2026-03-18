# game2.py

import time
from quoridor_5x5_env import GameState5x5, get_next_states
from abpruning import alpha_beta_search

# --- Coordinate Translators ---
COLS_TO_X = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4}
X_TO_COLS = {0: 'A', 1: 'B', 2: 'C', 3: 'D', 4: 'E'}
ROWS_TO_Y = {'1': 0, '2': 1, '3': 2, '4': 3, '5': 4}
Y_TO_ROWS = {0: '1', 1: '2', 2: '3', 3: '4', 4: '5'}

def format_coord(pos):
    """Converts internal (2, 0) to algebraic 'C1'"""
    return f"{X_TO_COLS[pos[0]]}{Y_TO_ROWS[pos[1]]}"

def draw_board(state: GameState5x5):
    """Renders the 5x5 board with A-E and 1-5 coordinates."""
    print("\n" + "="*34)
    print(f" P1 Walls: {state.p1_walls} | P2 (AI) Walls: {state.p2_walls}")
    print("="*34)
    
    # Column headers
    print("     A   B   C   D   E")
    
    for r in range(5):
        # 1. Print the row with pawns, vertical walls, and row number
        row_str = f" {Y_TO_ROWS[r]}  "
        for c in range(5):
            # Check pawns
            if (c, r) == state.p1_pos:
                row_str += " P1 "
            elif (c, r) == state.p2_pos:
                row_str += " P2 "
            else:
                row_str += "  . "
            
            # Check vertical walls to the right of this cell
            if c < 4:
                if (c, r) in state.v_walls or (c, r - 1) in state.v_walls:
                    row_str += "|"
                else:
                    row_str += " "
        print(row_str)
        
        # 2. Print the horizontal wall boundaries below this row
        if r < 4:
            wall_str = "    "
            for c in range(5):
                # Check horizontal walls below this cell
                if (c, r) in state.h_walls or (c - 1, r) in state.h_walls:
                    wall_str += "--- "
                else:
                    wall_str += "    "
                
                # Intersection '+'
                if c < 4:
                    wall_str += "+"
            print(wall_str)
    print("==================================\n")

def parse_human_command(cmd_str, current_state):
    """
    Translates human input (e.g., 'up', 'm c3', 'w b2 h') into 
    the engine's required action dictionary.
    """
    cmd = cmd_str.strip().lower().split()
    if not cmd:
        return None
        
    px, py = current_state.p1_pos

    # 1. Handle Directional Movement (up, down, left, right, w, a, s, d)
    dirs = {
        'up': (0, -1), 'w': (0, -1),
        'down': (0, 1), 's': (0, 1),
        'left': (-1, 0), 'a': (-1, 0),
        'right': (1, 0), 'd': (1, 0)
    }
    
    if cmd[0] in dirs:
        dx, dy = dirs[cmd[0]]
        target_pos = (px + dx, py + dy)
        
        # Auto-calculate straight jumps if the opponent is in the immediate target square
        if target_pos == current_state.p2_pos:
            target_pos = (target_pos[0] + dx, target_pos[1] + dy)
            
        return {"type": "move", "pos": target_pos}
        
    # 2. Handle Algebraic Movement (e.g., 'm c3')
    if cmd[0] == 'm' and len(cmd) == 2:
        pos_str = cmd[1]
        if len(pos_str) == 2 and pos_str[0] in COLS_TO_X and pos_str[1] in ROWS_TO_Y:
            c = COLS_TO_X[pos_str[0]]
            r = ROWS_TO_Y[pos_str[1]]
            return {"type": "move", "pos": (c, r)}

    # 3. Handle Algebraic Wall Placement (e.g., 'w b2 h')
    if cmd[0] == 'w' and len(cmd) == 3:
        pos_str = cmd[1]
        ori = cmd[2]
        if len(pos_str) == 2 and pos_str[0] in COLS_TO_X and pos_str[1] in ROWS_TO_Y and ori in ['h', 'v']:
            c = COLS_TO_X[pos_str[0]]
            r = ROWS_TO_Y[pos_str[1]]
            return {"type": "wall", "pos": (c, r), "orientation": ori}

    return None

def get_human_move(state: GameState5x5):
    """Loops until the human provides a legal move."""
    valid_states = get_next_states(state)
    
    while True:
        print("Commands:")
        print("  Move (Direction): up, down, left, right")
        print("  Move (Algebraic): m <coord>     (e.g., m c3)")
        print("  Place Wall:       w <coord> h/v (e.g., w b2 h)")
        
        user_input = input("Your Move (P1) > ")
        target_action = parse_human_command(user_input, state)
        
        if target_action is None:
            print(">>> INVALID FORMAT! Check your typing.\n")
            continue
            
        # Cross-reference the parsed command with the engine's legal moves
        for move_dict in valid_states:
            if move_dict["action"] == target_action:
                return move_dict["state"] 
        
        print(">>> ILLEGAL MOVE! (Blocked by wall, out of bounds, or traps a player)\n")

def main():
    current_state = GameState5x5(
        p1_pos=(2, 0), p2_pos=(2, 4), # Start at C1 and C5
        p1_walls=3, p2_walls=3,
        h_walls=[], v_walls=[],
        turn=1 # 1 = Human, 2 = AI
    )
    
    SEARCH_DEPTH = 4 
    
    print("\n--- NEW QUORIDOR GAME ---")
    print("You are P1 starting at the top (Row 1). Your goal is Row 5.")
    print("The AI is P2 starting at the bottom (Row 5). Its goal is Row 1.")
    print("NOTE: Walls anchor at their top-left coordinate. 'w c2 h' places a horizontal wall between C2/C3 and C3/C4.")
    
    while True:
        draw_board(current_state)
        
        # Check Win Conditions
        if current_state.p1_pos[1] == 4:
            print("🎉 YOU WIN! 🎉")
            break
        elif current_state.p2_pos[1] == 0:
            print("💀 AI WINS! 💀")
            break
            
        if current_state.turn == 1:
            current_state = get_human_move(current_state)
        else:
            print("🤖 AI is thinking...")
            start_time = time.time()
            
            best_score, best_action = alpha_beta_search(
                state=current_state,
                depth=SEARCH_DEPTH,
                alpha=float('-inf'),
                beta=float('inf'),
                is_maximizing=True,
                ai_player_id=2
            )
            
            for move_dict in get_next_states(current_state):
                if move_dict["action"] == best_action:
                    current_state = move_dict["state"]
                    break
                    
            elapsed = time.time() - start_time
            
            if best_action["type"] == "move":
                coord = format_coord(best_action['pos'])
                print(f"🤖 AI moved to {coord} (Took {elapsed:.2f}s)")
            else:
                coord = format_coord(best_action['pos'])
                w_dir = "Horizontal" if best_action["orientation"] == 'h' else "Vertical"
                print(f"🤖 AI placed a {w_dir} wall at {coord} (Took {elapsed:.2f}s)")

if __name__ == "__main__":
    main()