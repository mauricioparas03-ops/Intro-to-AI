# ai_agent.py
from collections import deque
import math
from quoridor_5x5_env import get_next_states, is_passage_open

def get_shortest_path_distance(state, start_pos, goal_row):
    """Returns the number of steps required to reach the goal row."""
    if start_pos[1] == goal_row: return 0
    
    queue = deque([(start_pos, 0)]) # (position, distance)
    visited = {start_pos}
    
    while queue:
        curr, dist = queue.popleft()
        cc, cr = curr
        
        for dc, dr in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nc, nr = cc + dc, cr + dr
            if 0 <= nc <= 4 and 0 <= nr <= 4:
                if (nc, nr) not in visited and is_passage_open(state, curr, (nc, nr)):
                    if nr == goal_row:
                        return dist + 1
                    visited.add((nc, nr))
                    queue.append(((nc, nr), dist + 1))
    
    return float('inf') # Should theoretically never happen if get_next_states works correctly

def evaluate_state(state, ai_player_id):
    """
    Calculates a score for the board. Higher is better for the AI.
    """
    # Define goals based on who the AI is
    if ai_player_id == 1:
        my_pos, opp_pos = state.p1_pos, state.p2_pos
        my_goal, opp_goal = 4, 0
        my_walls, opp_walls = state.p1_walls, state.p2_walls
    else:
        my_pos, opp_pos = state.p2_pos, state.p1_pos
        my_goal, opp_goal = 0, 4
        my_walls, opp_walls = state.p2_walls, state.p1_walls

    my_dist = get_shortest_path_distance(state, my_pos, my_goal)
    opp_dist = get_shortest_path_distance(state, opp_pos, opp_goal)
    
    # Base score: Opponent's distance minus my distance
    # (If opp is 6 steps away and I am 2 steps away, score is +4)
    score = opp_dist - my_dist
    
    # Small tie-breaker: Having more walls in reserve is slightly better
    score += (my_walls - opp_walls) * 0.1 
    
    # Check for immediate win/loss conditions
    if my_dist == 0: return float('inf')
    if opp_dist == 0: return float('-inf')

    return score

def alpha_beta_search(state, depth, alpha, beta, is_maximizing, ai_player_id):
    """
    Returns (best_score, best_action)
    """
    # 1. Base Case: Reached maximum depth or the game is over
    if depth == 0 or state.p1_pos[1] == 4 or state.p2_pos[1] == 0:
        return evaluate_state(state, ai_player_id), None

    possible_moves = get_next_states(state)
    
    # If no moves are possible (edge case), evaluate current
    if not possible_moves:
        return evaluate_state(state, ai_player_id), None

    best_action = None

    if is_maximizing:
        max_eval = float('-inf')
        for move_dict in possible_moves:
            eval_score, _ = alpha_beta_search(
                move_dict["state"], 
                depth - 1, 
                alpha, 
                beta, 
                False, # Next turn is the opponent's (minimizing)
                ai_player_id
            )
            
            if eval_score > max_eval:
                max_eval = eval_score
                best_action = move_dict["action"]
                
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break # Prune! The opponent won't let us get this far.
                
        return max_eval, best_action

    else:
        min_eval = float('inf')
        for move_dict in possible_moves:
            eval_score, _ = alpha_beta_search(
                move_dict["state"], 
                depth - 1, 
                alpha, 
                beta, 
                True, # Next turn is the AI's (maximizing)
                ai_player_id
            )
            
            if eval_score < min_eval:
                min_eval = eval_score
                best_action = move_dict["action"]
                
            beta = min(beta, eval_score)
            if beta <= alpha:
                break # Prune! We wouldn't let the opponent get this far.
                
        return min_eval, best_action