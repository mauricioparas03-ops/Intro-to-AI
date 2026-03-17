"""
Quoridor Board Game Engine
==========================
A headless, pure-Python back-end engine for the Quoridor board game on a 9x9 grid.
Supports full move validation, wall placement with legality checking (including
BFS-based path-blocking detection), jump rules, and ASCII board rendering.

Coordinate system: (col, row) where (0,0) is top-left.
  - Player 1 starts at (4, 0), goal is row 8 (bottom).
  - Player 2 starts at (4, 8), goal is row 0 (top).

Wall encoding:
  - A HORIZONTAL wall at (c, r) blocks movement between row r and row r+1
    for columns c and c+1.  The wall "anchor" is the left-most gap.
  - A VERTICAL wall at (c, r) blocks movement between col c and col c+1
    for rows r and r+1.  The wall "anchor" is the top-most gap.
"""

from __future__ import annotations

import sys
from collections import deque
from enum import IntEnum
from typing import Optional


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class WallType(IntEnum):
    HORIZONTAL = 0
    VERTICAL = 1


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------

class Player:
    """Holds mutable state for a single Quoridor player.

    Attributes
    ----------
    player_id : int
        1 or 2.
    position : tuple[int, int]
        Current (col, row) position on the board.
    walls_remaining : int
        Number of walls still available to place (starts at 10).
    goal_row : int
        The row index the player must reach to win.
    """

    def __init__(self, player_id: int, start: tuple[int, int], goal_row: int) -> None:
        self.player_id = player_id
        self.position: tuple[int, int] = start
        self.walls_remaining: int = 10
        self.goal_row: int = goal_row

    def __repr__(self) -> str:
        return (
            f"Player(id={self.player_id}, pos={self.position}, "
            f"walls={self.walls_remaining}, goal_row={self.goal_row})"
        )


# ---------------------------------------------------------------------------
# Board / Wall state
# ---------------------------------------------------------------------------

class Board:
    """
    Stores wall state and exposes low-level adjacency queries.

    Wall sets
    ---------
    Each wall is stored as a frozenset anchor ``(col, row)`` in either
    ``h_walls`` (horizontal) or ``v_walls`` (vertical).

    Horizontal wall at (c, r):
        Blocks the edges  (c, r)↔(c, r+1)  and  (c+1, r)↔(c+1, r+1).

    Vertical wall at (c, r):
        Blocks the edges  (c, r)↔(c+1, r)  and  (c, r+1)↔(c+1, r+1).
    """

    SIZE = 9 # cells per side (0..8)

    def __init__(self) -> None:
        self.h_walls: set[tuple[int, int]] = set()  # horizontal wall anchors
        self.v_walls: set[tuple[int, int]] = set()  # vertical wall anchors

    # ------------------------------------------------------------------
    # Low-level edge queries
    # ------------------------------------------------------------------

    def _in_bounds(self, col: int, row: int) -> bool:
        return 0 <= col < self.SIZE and 0 <= row < self.SIZE

    def is_passage_open(
        self,
        from_pos: tuple[int, int],
        to_pos: tuple[int, int],
    ) -> bool:
        """Return True if no wall blocks the single-step passage between
        two orthogonally adjacent cells.

        Parameters
        ----------
        from_pos, to_pos:
            Must be orthogonally adjacent (differ by exactly 1 in one axis).

        Raises
        ------
        ValueError
            If the cells are not orthogonally adjacent.
        """
        fc, fr = from_pos
        tc, tr = to_pos
        dc, dr = tc - fc, tr - fr

        if abs(dc) + abs(dr) != 1:
            raise ValueError(f"Cells {from_pos} and {to_pos} are not adjacent.")

        if dr == 1:  # moving south (row increases)
            # Blocked by h_wall at (fc, fr) or (fc-1, fr)
            return (fc, fr) not in self.h_walls and (fc - 1, fr) not in self.h_walls

        if dr == -1:  # moving north
            return (fc, tr) not in self.h_walls and (fc - 1, tr) not in self.h_walls

        if dc == 1:  # moving east (col increases)
            # Blocked by v_wall at (fc, fr) or (fc, fr-1)
            return (fc, fr) not in self.v_walls and (fc, fr - 1) not in self.v_walls

        if dc == -1:  # moving west
            return (tc, fr) not in self.v_walls and (tc, fr - 1) not in self.v_walls

        return True  # unreachable

    def neighbors(self, pos: tuple[int, int]) -> list[tuple[int, int]]:
        """Return all cells reachable from *pos* in a single orthogonal
        step (no pawns considered; purely wall/boundary check).
        """
        col, row = pos
        result: list[tuple[int, int]] = []
        for dc, dr in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nc, nr = col + dc, row + dr
            if self._in_bounds(nc, nr) and self.is_passage_open(pos, (nc, nr)):
                result.append((nc, nr))
        return result


# ---------------------------------------------------------------------------
# BFS pathfinding
# ---------------------------------------------------------------------------

def bfs_has_path(board: Board, start: tuple[int, int], goal_row: int) -> bool:
    """Return True if *start* can reach any cell in *goal_row* through the
    current wall configuration (pawn positions ignored for goal-blocking check).

    Parameters
    ----------
    board : Board
        Current wall state.
    start : tuple[int, int]
        Starting cell (col, row).
    goal_row : int
        Target row index (0 or 8).
    """
    if start[1] == goal_row:
        return True

    visited: set[tuple[int, int]] = {start}
    queue: deque[tuple[int, int]] = deque([start])

    while queue:
        current = queue.popleft()
        for nxt in board.neighbors(current):
            if nxt in visited:
                continue
            if nxt[1] == goal_row:
                return True
            visited.add(nxt)
            queue.append(nxt)

    return False


# ---------------------------------------------------------------------------
# Game
# ---------------------------------------------------------------------------

class Game:
    """
    Manages the full game state for a two-player Quoridor match.

    Public interface
    ----------------
    get_valid_moves(player_id)        -> list of valid (col, row) targets
    is_wall_legal(wall_type, anchor)  -> bool
    place_wall(player_id, wall_type, anchor)
    move_pawn(player_id, new_position)
    check_winner()                    -> Optional[int]  (1, 2, or None)
    render()                          -> str  (ASCII board)
    """

    def __init__(self) -> None:
        self.board = Board()
        self.players: dict[int, Player] = {
            1: Player(player_id=1, start=(4, 0), goal_row=8),
            2: Player(player_id=2, start=(4, 8), goal_row=0),
        }
        self.current_turn: int = 1   # player whose turn it is
        self.winner: Optional[int] = None
        self.move_history: list[str] = []

    # ------------------------------------------------------------------
    # Turn management
    # ------------------------------------------------------------------

    def _next_turn(self) -> None:
        self.current_turn = 2 if self.current_turn == 1 else 1

    def _opponent_id(self, player_id: int) -> int:
        return 2 if player_id == 1 else 1

    # ------------------------------------------------------------------
    # Move validation
    # ------------------------------------------------------------------

    def get_valid_moves(self, player_id: int) -> list[tuple[int, int]]:
        """Return all valid destination cells for the given player's pawn.

        Rules implemented
        -----------------
        1. **Normal move**: Step one cell orthogonally if the passage is
           open and the target is within bounds.
        2. **Straight jump**: If the opponent occupies the adjacent cell and
           the passage between them is open AND the passage from opponent
           to the cell behind them is also open, the player may jump
           straight over to land on the far side.
        3. **Diagonal (side) jump**: If a straight jump is blocked by a wall
           (or the board edge) behind the opponent, the player may instead
           move to either open lateral cell adjacent to the opponent.

        Parameters
        ----------
        player_id : int
            The player (1 or 2) whose moves are being enumerated.

        Returns
        -------
        list[tuple[int, int]]
            Unique list of reachable cells.
        """
        board = self.board
        player = self.players[player_id]
        opponent = self.players[self._opponent_id(player_id)]

        pc, pr = player.position
        oc, or_ = opponent.position
        valid: list[tuple[int, int]] = []

        for dc, dr in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nc, nr = pc + dc, pr + dr
            if not board._in_bounds(nc, nr):
                continue
            if not board.is_passage_open((pc, pr), (nc, nr)):
                continue

            if (nc, nr) != (oc, or_):
                # Normal (unoccupied) step
                valid.append((nc, nr))
            else:
                # Opponent is on (nc, nr) → apply jump rules
                jc, jr = nc + dc, nr + dr  # straight-jump landing

                straight_ok = (
                    board._in_bounds(jc, jr)
                    and board.is_passage_open((nc, nr), (jc, jr))
                )

                if straight_ok:
                    valid.append((jc, jr))
                else:
                    # Try lateral (diagonal) jumps
                    for ldc, ldr in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                        if (ldc, ldr) == (dc, dr) or (ldc, ldr) == (-dc, -dr):
                            continue  # skip forward/backward directions
                        lc, lr = nc + ldc, nr + ldr
                        if (
                            board._in_bounds(lc, lr)
                            and board.is_passage_open((nc, nr), (lc, lr))
                        ):
                            valid.append((lc, lr))

        # Deduplicate while preserving order
        seen: set[tuple[int, int]] = set()
        result: list[tuple[int, int]] = []
        for cell in valid:
            if cell not in seen:
                seen.add(cell)
                result.append(cell)
        return result

    # ------------------------------------------------------------------
    # Wall validation
    # ------------------------------------------------------------------

    def is_wall_legal(self, wall_type: WallType, anchor: tuple[int, int]) -> bool:
        """Check whether placing a wall of *wall_type* at *anchor* is legal.

        Legality criteria
        -----------------
        1. **Bounds**: The wall anchor must satisfy ``0 <= col <= 7`` and
           ``0 <= row <= 7`` (walls span two cells, so they cannot start at
           index 8).
        2. **No overlap**: The exact same wall must not already exist.
        3. **No crossing**: A horizontal wall cannot cross an existing
           horizontal wall; a vertical wall cannot cross a vertical wall.
           A horizontal and vertical wall of the same anchor position
           intersect and are therefore also illegal.
        4. **Path not blocked**: After simulating the placement, both players
           must still have at least one path to their respective goal rows
           (verified via BFS).

        Parameters
        ----------
        wall_type : WallType
            HORIZONTAL or VERTICAL.
        anchor : tuple[int, int]
            (col, row) of the wall's anchor cell.

        Returns
        -------
        bool
            True if the wall may legally be placed.
        """
        c, r = anchor

        # 1. Bounds check (walls occupy two cells, anchor 0-7)
        if not (0 <= c <= 7 and 0 <= r <= 7):
            return False

        h_walls = self.board.h_walls
        v_walls = self.board.v_walls

        if wall_type == WallType.HORIZONTAL:
            # 2. No identical wall
            if (c, r) in h_walls:
                return False
            # 3a. No overlap with adjacent horizontal wall sharing a cell
            if (c - 1, r) in h_walls or (c + 1, r) in h_walls:
                return False
            # 3b. No crossing with vertical wall at the same anchor
            if (c, r) in v_walls:
                return False

        else:  # VERTICAL
            if (c, r) in v_walls:
                return False
            if (c, r - 1) in v_walls or (c, r + 1) in v_walls:
                return False
            if (c, r) in h_walls:
                return False

        # 4. Simulate placement and BFS-check both players
        if wall_type == WallType.HORIZONTAL:
            h_walls.add((c, r))
        else:
            v_walls.add((c, r))

        p1_ok = bfs_has_path(self.board, self.players[1].position, self.players[1].goal_row)
        p2_ok = bfs_has_path(self.board, self.players[2].position, self.players[2].goal_row)

        # Roll back simulation
        if wall_type == WallType.HORIZONTAL:
            h_walls.discard((c, r))
        else:
            v_walls.discard((c, r))

        return p1_ok and p2_ok

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def place_wall(
        self,
        player_id: int,
        wall_type: WallType,
        anchor: tuple[int, int],
    ) -> bool:
        """Place a wall on behalf of *player_id*.

        Parameters
        ----------
        player_id : int
            Must equal ``self.current_turn``.
        wall_type : WallType
            HORIZONTAL or VERTICAL.
        anchor : tuple[int, int]
            Wall anchor (col, row).

        Returns
        -------
        bool
            True if the wall was placed successfully; False otherwise
            (wrong turn, no walls remaining, or illegal placement).
        """
        if self.winner is not None:
            return False
        if player_id != self.current_turn:
            return False

        player = self.players[player_id]
        if player.walls_remaining <= 0:
            return False

        if not self.is_wall_legal(wall_type, anchor):
            return False

        if wall_type == WallType.HORIZONTAL:
            self.board.h_walls.add(anchor)
        else:
            self.board.v_walls.add(anchor)

        player.walls_remaining -= 1
        label = "H" if wall_type == WallType.HORIZONTAL else "V"
        self.move_history.append(f"P{player_id} wall {label}{anchor}")
        self._next_turn()
        return True

    def move_pawn(self, player_id: int, new_position: tuple[int, int]) -> bool:
        """Move the pawn of *player_id* to *new_position*.

        Parameters
        ----------
        player_id : int
            Must equal ``self.current_turn``.
        new_position : tuple[int, int]
            Destination cell; must be in ``get_valid_moves(player_id)``.

        Returns
        -------
        bool
            True if the move was applied; False otherwise.
        """
        if self.winner is not None:
            return False
        if player_id != self.current_turn:
            return False
        if new_position not in self.get_valid_moves(player_id):
            return False

        self.players[player_id].position = new_position
        self.move_history.append(f"P{player_id} move {new_position}")

        # Check win condition
        player = self.players[player_id]
        if new_position[1] == player.goal_row:
            self.winner = player_id

        self._next_turn()
        return True

    # ------------------------------------------------------------------
    # Win check
    # ------------------------------------------------------------------

    def check_winner(self) -> Optional[int]:
        """Return the winning player id (1 or 2), or None if the game is ongoing."""
        return self.winner

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def render(self) -> str:
        """Return a multi-line ASCII string representing the current board.

        Legend
        ------
        P1 / P2  – player pawns
        .        – empty cell
        ---      – horizontal wall segment between rows
        |        – vertical wall segment between columns
        +        – corner / intersection marker
        """
        SIZE = Board.SIZE
        board = self.board
        p1_pos = self.players[1].position
        p2_pos = self.players[2].position

        lines: list[str] = []

        # Column header
        col_header = "   " + "  ".join(str(c) for c in range(SIZE))
        lines.append(col_header)

        for row in range(SIZE):
            # --- Cell row ---
            cell_parts: list[str] = [f"{row} "]
            for col in range(SIZE):
                pos = (col, row)
                if pos == p1_pos:
                    cell_parts.append("P1")
                elif pos == p2_pos:
                    cell_parts.append("P2")
                else:
                    cell_parts.append(" .")

                # Vertical wall to the right of this cell?
                if col < SIZE - 1:
                    # v_wall at (col, row) or (col, row-1) blocks (col,row)↔(col+1,row)
                    blocked = (
                        (col, row) in board.v_walls
                        or (col, row - 1) in board.v_walls
                    )
                    cell_parts.append(" |" if blocked else "  ")

            lines.append("".join(cell_parts))

            # --- Horizontal wall row (between this row and next) ---
            if row < SIZE - 1:
                hw_parts: list[str] = ["  "]
                for col in range(SIZE):
                    # h_wall at (col, row) or (col-1, row) blocks (col,row)↔(col,row+1)
                    blocked = (
                        (col, row) in board.h_walls
                        or (col - 1, row) in board.h_walls
                    )
                    hw_parts.append("--" if blocked else "  ")
                    if col < SIZE - 1:
                        hw_parts.append("+")
                lines.append("".join(hw_parts))

        # Footer: wall counts
        p1 = self.players[1]
        p2 = self.players[2]
        lines.append("")
        lines.append(
            f"  P1 walls left: {p1.walls_remaining}   "
            f"P2 walls left: {p2.walls_remaining}"
        )
        turn_label = f"P{self.current_turn}" if self.winner is None else f"P{self.winner} wins!"
        lines.append(f"  Turn: {turn_label}")
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render()


# ---------------------------------------------------------------------------
# CLI demo / smoke test
# ---------------------------------------------------------------------------

def _demo() -> None:
    """Quick smoke-test demonstrating basic engine capabilities."""
    game = Game()
    print("=== Initial board ===")
    print(game)

    # A few pawn moves
    moves_p1 = [(4, 1), (4, 2), (4, 3)]
    moves_p2 = [(4, 7), (4, 6), (4, 5)]

    for m1, m2 in zip(moves_p1, moves_p2):
        ok = game.move_pawn(1, m1)
        assert ok, f"P1 move to {m1} failed"
        ok = game.move_pawn(2, m2)
        assert ok, f"P2 move to {m2} failed"

    print("\n=== After 3 moves each ===")
    print(game)

    # Place a horizontal wall: P1's turn
    ok = game.place_wall(1, WallType.HORIZONTAL, (3, 4))
    assert ok, "Wall placement failed!"
    print("\n=== After P1 places H-wall at (3,4) ===")
    print(game)

    # Place a vertical wall: P2's turn
    ok = game.place_wall(2, WallType.VERTICAL, (4, 3))
    assert ok, "Wall placement failed!"
    print("\n=== After P2 places V-wall at (4,3) ===")
    print(game)

    # Show P1's valid moves
    print(f"\nP1 valid moves: {game.get_valid_moves(1)}")

    # Try an illegal wall (would block a player completely – unlikely here,
    # but demonstrates the API)
    bad = game.is_wall_legal(WallType.HORIZONTAL, (100, 0))
    print(f"\nWall at (100, 0) legal? {bad}  (expected False)")

    print("\n✓ Smoke test passed.")


if __name__ == "__main__":
    _demo()
