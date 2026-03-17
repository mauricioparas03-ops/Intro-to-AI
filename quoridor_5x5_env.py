#quoridor_5x5_env.py

from copy import deepcopy
from collections import deque

class GameState5x5:
    def __init__(self, p1_pos, p2_pos, p1_walls, p2_walls, h_walls, v_walls, turn):
        """
        State representation for a 5x5 Quoridor game.
        Coordinates are (col, row) from 0 to 4.
        """
        self.p1_pos = tuple(p1_pos)
        self.p2_pos = tuple(p2_pos)
        self.p1_walls = p1_walls
        self.p2_walls = p2_walls
        
        # Walls are stored as sets of tuples for fast O(1) lookup
        self.h_walls = set(tuple(w) for w in h_walls)
        self.v_walls = set(tuple(w) for w in v_walls)
        self.turn = turn

    def copy(self):
        return GameState5x5(
            self.p1_pos, self.p2_pos, 
            self.p1_walls, self.p2_walls, 
            self.h_walls.copy(), self.v_walls.copy(), 
            self.turn
        )

def is_passage_open(state, from_pos, to_pos):
    """Checks if there is a wall blocking the step between two adjacent cells."""
    fc, fr = from_pos    #From column, row
    tc, tr = to_pos      #To column, row
    dc, dr = tc - fc, tr - fr  #Direction of movement

    if dr == 1:    # moving down  / Checks if there i open passage below the current cell(no wall placements blocking it)
        return (fc, fr) not in state.h_walls and (fc - 1, fr) not in state.h_walls
    elif dr == -1: # moving up / Checks if there i open passage above the current cell(no wall placements blocking it)
        return (fc, tr) not in state.h_walls and (fc - 1, tr) not in state.h_walls
    elif dc == 1:  # moving right / Checks if there i open passage to the right of the current cell(no wall placements blocking it)
        return (fc, fr) not in state.v_walls and (fc, fr - 1) not in state.v_walls
    elif dc == -1: # moving left / Checks if there i open passage to the left of the current cell(no wall placements blocking it)
        return (tc, fr) not in state.v_walls and (tc, fr - 1) not in state.v_walls
    return False

def get_valid_pawn_moves(state, player_id):
    """Calculates all legal pawn moves for the given player, including jumps."""
    pos = state.p1_pos if player_id == 1 else state.p2_pos
    opp_pos = state.p2_pos if player_id == 1 else state.p1_pos
    
    pc, pr = pos     
    oc, or_ = opp_pos
    valid_moves = []

    # Orthogonal directions: Down, Up, Right, Left
    directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]

    for dc, dr in directions:
        nc, nr = pc + dc, pr + dr # next column, next row
        
        # Bounds check (5x5 grid -> 0 to 4)
        if not (0 <= nc <= 4 and 0 <= nr <= 4):
            continue
            
        if not is_passage_open(state, (pc, pr), (nc, nr)):
            continue

        if (nc, nr) != (oc, or_):
            # Normal step (unoccupied)
            valid_moves.append((nc, nr))
        else:
            # Jump mechanics (opponent is in the way)
            jc, jr = nc + dc, nr + dr # Cell behind opponent
            
            # Straight jump
            if 0 <= jc <= 4 and 0 <= jr <= 4 and is_passage_open(state, (nc, nr), (jc, jr)):
                valid_moves.append((jc, jr))
            else:
                # Diagonal/Lateral jump if straight jump is blocked or out of bounds
                for ldc, ldr in directions:
                    # Exclude forward and backward directions relative to the initial step
                    if (ldc, ldr) in [(dc, dr), (-dc, -dr)]:
                        continue
                    lc, lr = nc + ldc, nr + ldr
                    if 0 <= lc <= 4 and 0 <= lr <= 4 and is_passage_open(state, (nc, nr), (lc, lr)):
                        valid_moves.append((lc, lr))

    return list(set(valid_moves)) # Deduplicate

def has_path_to_goal(state, start_pos, goal_row):
    """BFS to verify if a player can still reach their goal row."""
    if start_pos[1] == goal_row: return True
    
    queue = deque([start_pos])
    visited = {start_pos}
    
    while queue:
        curr = queue.popleft()
        cc, cr = curr
        
        for dc, dr in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nc, nr = cc + dc, cr + dr
            if 0 <= nc <= 4 and 0 <= nr <= 4:
                if (nc, nr) not in visited and is_passage_open(state, curr, (nc, nr)):
                    if nr == goal_row:
                        return True
                    visited.add((nc, nr))
                    queue.append((nc, nr))
    return False


#----------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------
def get_next_states(current_state: GameState5x5):
    """
    Core Generator Function.
    Takes a GameState5x5 and returns a list of dictionaries containing:
    - 'action': The move or wall placement that created this state
    - 'state': The resulting GameState5x5 object
    """
    next_states = []
    p_id = current_state.turn
    next_turn = 2 if p_id == 1 else 1

    # 1. Generate Pawn Move States
    moves = get_valid_pawn_moves(current_state, p_id)
    for move in moves:
        new_state = current_state.copy()
        if p_id == 1: new_state.p1_pos = move
        else: new_state.p2_pos = move
        new_state.turn = next_turn
        
        next_states.append({
            "action": {"type": "move", "pos": move},
            "state": new_state
        })

    # 2. Generate Wall Placement States
    walls_left = current_state.p1_walls if p_id == 1 else current_state.p2_walls
    
    if walls_left > 0:
        # Wall anchors on a 5x5 board range from 0 to 3
        for r in range(4):
            for c in range(4):
                for w_type in ['h', 'v']:
                    # Check overlap/intersection
                    if w_type == 'h':
                        if (c, r) in current_state.h_walls: continue
                        if (c - 1, r) in current_state.h_walls or (c + 1, r) in current_state.h_walls: continue
                        if (c, r) in current_state.v_walls: continue # Crossing
                    else:
                        if (c, r) in current_state.v_walls: continue
                        if (c, r - 1) in current_state.v_walls or (c, r + 1) in current_state.v_walls: continue
                        if (c, r) in current_state.h_walls: continue # Crossing
                    
                    # Simulate wall placement for path validation
                    sim_state = current_state.copy()
                    if w_type == 'h': sim_state.h_walls.add((c, r))
                    else: sim_state.v_walls.add((c, r))
                    
                    # Check if both players can still reach their goals
                    # P1 goal row is 4, P2 goal row is 0
                    if has_path_to_goal(sim_state, sim_state.p1_pos, 4) and \
                       has_path_to_goal(sim_state, sim_state.p2_pos, 0):
                        
                        # Apply state changes permanently for the new branch
                        if p_id == 1: sim_state.p1_walls -= 1
                        else: sim_state.p2_walls -= 1
                        sim_state.turn = next_turn
                        
                        next_states.append({
                            "action": {"type": "wall", "pos": (c, r), "orientation": w_type},
                            "state": sim_state
                        })

    return next_states