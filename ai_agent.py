from collections import deque
from quoridor_5x5_env import get_next_states, is_passage_open


def get_shortest_path_distance(state, start_pos, goal_row):
    """Returns the number of steps required to reach the goal row."""
    if start_pos[1] == goal_row:
        return 0

    queue = deque([(start_pos, 0)])  # (position, distance)
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

    return 999


def evaluate_state(state, ai_player_id):
    """
    Calculates a score for the board. Higher is better for the AI.
    """
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

    # Immediate win/loss
    if my_dist == 0:
        return 100000
    if opp_dist == 0:
        return -100000

    score = 0.0

    # Main heuristic: race to goal
    score += (opp_dist - my_dist) * 10

    # Small wall advantage
    score += (my_walls - opp_walls) * 0.1

    return score


def alpha_beta_search(state, depth, alpha, beta, ai_player_id):
    """
    Returns (best_score, best_action)
    """
    # terminal or depth limit
    if depth == 0 or state.p1_pos[1] == 4 or state.p2_pos[1] == 0:
        return evaluate_state(state, ai_player_id), None

    possible_moves = get_next_states(state)

    if not possible_moves:
        return evaluate_state(state, ai_player_id), None

    best_action = None

    # MAX node: AI turn
    if state.turn == ai_player_id:
        max_eval = float('-inf')

        for move_dict in possible_moves:
            eval_score, _ = alpha_beta_search(
                move_dict["state"],
                depth - 1,
                alpha,
                beta,
                ai_player_id
            )

            if eval_score > max_eval:
                max_eval = eval_score
                best_action = move_dict["action"]

            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break

        return max_eval, best_action

    # MIN node: opponent turn
    else:
        min_eval = float('inf')

        for move_dict in possible_moves:
            eval_score, _ = alpha_beta_search(
                move_dict["state"],
                depth - 1,
                alpha,
                beta,
                ai_player_id
            )

            if eval_score < min_eval:
                min_eval = eval_score
                best_action = move_dict["action"]

            beta = min(beta, min_eval)
            if beta <= alpha:
                break

        return min_eval, best_action


def choose_ai_move(state, depth=2):
    """
    state must already be a GameState5x5 object.
    Returns action in server format.
    """
    ai_player_id = state.turn

    _, best_action = alpha_beta_search(
        state=state,
        depth=depth,
        alpha=float('-inf'),
        beta=float('inf'),
        ai_player_id=ai_player_id
    )

    if best_action is None:
        possible_moves = get_next_states(state)
        if not possible_moves:
            raise RuntimeError("No legal moves available for AI.")
        best_action = possible_moves[0]["action"]

    if best_action["type"] == "move":
        return {
            "action_type": "move",
            "coordinates": [best_action["pos"][0], best_action["pos"][1]]
        }

    return {
        "action_type": "wall",
        "coordinates": [best_action["pos"][0], best_action["pos"][1]],
        "orientation": "horizontal" if best_action["orientation"] == "h" else "vertical"
    }