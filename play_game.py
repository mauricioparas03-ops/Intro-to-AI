import time
import tkinter as tk
from tkinter import messagebox

from quoridor_5x5_env import GameState5x5, get_next_states
from abpruning import alpha_beta_search


CELL_SIZE = 80
PAWN_RADIUS = 18
BOARD_SIZE = 5
SEARCH_DEPTH = 4


class QuoridorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Quoridor 5x5")

        self.current_state = GameState5x5(
            p1_pos=(2, 0),
            p2_pos=(2, 4),
            p1_walls=3,
            p2_walls=3,
            h_walls=[],
            v_walls=[],
            turn=1
        )

        self.selected_mode = tk.StringVar(value="move")
        self.valid_next_states = []

        self.info_label = tk.Label(
            root,
            text="You are P1. Goal: reach row 4. AI goal: row 0.",
            font=("Arial", 12)
        )
        self.info_label.pack(pady=8)

        top_frame = tk.Frame(root)
        top_frame.pack()

        tk.Label(top_frame, text="Action:").pack(side=tk.LEFT, padx=5)

        tk.Radiobutton(
            top_frame, text="Move", variable=self.selected_mode, value="move",
            command=self.refresh_valid_moves
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            top_frame, text="Horizontal Wall", variable=self.selected_mode, value="hwall",
            command=self.refresh_valid_moves
        ).pack(side=tk.LEFT)

        tk.Radiobutton(
            top_frame, text="Vertical Wall", variable=self.selected_mode, value="vwall",
            command=self.refresh_valid_moves
        ).pack(side=tk.LEFT)

        self.status_label = tk.Label(root, text="", font=("Arial", 11))
        self.status_label.pack(pady=6)

        canvas_w = BOARD_SIZE * CELL_SIZE
        canvas_h = BOARD_SIZE * CELL_SIZE
        self.canvas = tk.Canvas(root, width=canvas_w, height=canvas_h, bg="white")
        self.canvas.pack(padx=10, pady=10)

        self.canvas.bind("<Button-1>", self.on_canvas_click)

        self.draw_board()
        self.refresh_valid_moves()

    def refresh_valid_moves(self):
        self.valid_next_states = get_next_states(self.current_state)
        self.draw_board()

    def draw_board(self):
        self.canvas.delete("all")

        # Draw cells
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                x1 = c * CELL_SIZE
                y1 = r * CELL_SIZE
                x2 = x1 + CELL_SIZE
                y2 = y1 + CELL_SIZE

                fill = "#f5f5f5"
                self.canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline="black")

        # Highlight legal actions for current mode when it's human turn
        if self.current_state.turn == 1:
            mode = self.selected_mode.get()
            for move_dict in self.valid_next_states:
                action = move_dict["action"]

                if mode == "move" and action["type"] == "move":
                    c, r = action["pos"]
                    self.highlight_cell(c, r, "#c8f7c5")

                elif mode == "hwall" and action["type"] == "wall" and action["orientation"] == "h":
                    c, r = action["pos"]
                    self.highlight_hwall_slot(c, r, "#a5d8ff")

                elif mode == "vwall" and action["type"] == "wall" and action["orientation"] == "v":
                    c, r = action["pos"]
                    self.highlight_vwall_slot(c, r, "#a5d8ff")

        # Draw wall slots lightly
        for r in range(BOARD_SIZE - 1):
            for c in range(BOARD_SIZE - 1):
                self.draw_hwall_slot(c, r, "#dddddd")
                self.draw_vwall_slot(c, r, "#dddddd")

        # Draw placed horizontal walls
        for c, r in self.current_state.h_walls:
            x1 = c * CELL_SIZE
            y = (r + 1) * CELL_SIZE
            x2 = (c + 2) * CELL_SIZE
            self.canvas.create_line(x1, y, x2, y, width=8, fill="#1f4e79")

        # Draw placed vertical walls
        for c, r in self.current_state.v_walls:
            x = (c + 1) * CELL_SIZE
            y1 = r * CELL_SIZE
            y2 = (r + 2) * CELL_SIZE
            self.canvas.create_line(x, y1, x, y2, width=8, fill="#1f4e79")

        # Draw pawns
        self.draw_pawn(self.current_state.p1_pos, "red", "P1")
        self.draw_pawn(self.current_state.p2_pos, "black", "P2")

        # Grid coordinates
        for c in range(BOARD_SIZE):
            self.canvas.create_text(
                c * CELL_SIZE + CELL_SIZE / 2, 10, text=str(c), fill="gray20"
            )
        for r in range(BOARD_SIZE):
            self.canvas.create_text(
                10, r * CELL_SIZE + CELL_SIZE / 2, text=str(r), fill="gray20"
            )

        # Status text
        turn_text = "Your turn" if self.current_state.turn == 1 else "AI turn"
        self.status_label.config(
            text=f"P1 walls: {self.current_state.p1_walls}    "
                 f"P2 walls: {self.current_state.p2_walls}    "
                 f"{turn_text}"
        )

    def draw_pawn(self, pos, color, label):
        c, r = pos
        cx = c * CELL_SIZE + CELL_SIZE / 2
        cy = r * CELL_SIZE + CELL_SIZE / 2
        self.canvas.create_oval(
            cx - PAWN_RADIUS, cy - PAWN_RADIUS,
            cx + PAWN_RADIUS, cy + PAWN_RADIUS,
            fill=color, outline="white", width=2
        )
        self.canvas.create_text(cx, cy, text=label, fill="white", font=("Arial", 10, "bold"))

    def highlight_cell(self, c, r, color):
        pad = 8
        x1 = c * CELL_SIZE + pad
        y1 = r * CELL_SIZE + pad
        x2 = (c + 1) * CELL_SIZE - pad
        y2 = (r + 1) * CELL_SIZE - pad
        self.canvas.create_rectangle(x1, y1, x2, y2, outline=color, width=4)

    def draw_hwall_slot(self, c, r, color):
        x1 = c * CELL_SIZE + 8
        y = (r + 1) * CELL_SIZE
        x2 = (c + 2) * CELL_SIZE - 8
        self.canvas.create_line(x1, y, x2, y, width=2, fill=color)

    def draw_vwall_slot(self, c, r, color):
        x = (c + 1) * CELL_SIZE
        y1 = r * CELL_SIZE + 8
        y2 = (r + 2) * CELL_SIZE - 8
        self.canvas.create_line(x, y1, x, y2, width=2, fill=color)

    def highlight_hwall_slot(self, c, r, color):
        x1 = c * CELL_SIZE + 8
        y = (r + 1) * CELL_SIZE
        x2 = (c + 2) * CELL_SIZE - 8
        self.canvas.create_line(x1, y, x2, y, width=6, fill=color)

    def highlight_vwall_slot(self, c, r, color):
        x = (c + 1) * CELL_SIZE
        y1 = r * CELL_SIZE + 8
        y2 = (r + 2) * CELL_SIZE - 8
        self.canvas.create_line(x, y1, x, y2, width=6, fill=color)

    def on_canvas_click(self, event):
        if self.current_state.turn != 1:
            return

        mode = self.selected_mode.get()

        if mode == "move":
            c = event.x // CELL_SIZE
            r = event.y // CELL_SIZE
            self.try_apply_action({"type": "move", "pos": (c, r)})

        elif mode == "hwall":
            action = self.pick_horizontal_wall(event.x, event.y)
            if action is not None:
                self.try_apply_action(action)

        elif mode == "vwall":
            action = self.pick_vertical_wall(event.x, event.y)
            if action is not None:
                self.try_apply_action(action)

    def pick_horizontal_wall(self, x, y):
        tolerance = 12
        best = None
        best_dist = 999999

        for r in range(BOARD_SIZE - 1):
            wall_y = (r + 1) * CELL_SIZE
            if abs(y - wall_y) > tolerance:
                continue

            for c in range(BOARD_SIZE - 1):
                x1 = c * CELL_SIZE
                x2 = (c + 2) * CELL_SIZE
                if x1 <= x <= x2:
                    dist = abs(y - wall_y)
                    if dist < best_dist:
                        best_dist = dist
                        best = {"type": "wall", "pos": (c, r), "orientation": "h"}

        return best

    def pick_vertical_wall(self, x, y):
        tolerance = 12
        best = None
        best_dist = 999999

        for c in range(BOARD_SIZE - 1):
            wall_x = (c + 1) * CELL_SIZE
            if abs(x - wall_x) > tolerance:
                continue

            for r in range(BOARD_SIZE - 1):
                y1 = r * CELL_SIZE
                y2 = (r + 2) * CELL_SIZE
                if y1 <= y <= y2:
                    dist = abs(x - wall_x)
                    if dist < best_dist:
                        best_dist = dist
                        best = {"type": "wall", "pos": (c, r), "orientation": "v"}

        return best

    def try_apply_action(self, target_action):
        for move_dict in self.valid_next_states:
            if move_dict["action"] == target_action:
                self.current_state = move_dict["state"]
                self.draw_board()
                self.check_game_end()
                if self.current_state.turn == 2:
                    self.root.after(200, self.run_ai_turn)
                return

        messagebox.showwarning("Illegal move", "That action is not legal in this position.")

    def run_ai_turn(self):
        if self.current_state.turn != 2:
            return

        self.status_label.config(
            text=f"P1 walls: {self.current_state.p1_walls}    "
                 f"P2 walls: {self.current_state.p2_walls}    "
                 f"AI is thinking..."
        )
        self.root.update_idletasks()

        start_time = time.time()

        best_score, best_action = alpha_beta_search(
            state=self.current_state,
            depth=SEARCH_DEPTH,
            alpha=float('-inf'),
            beta=float('inf'),
            is_maximizing=True,
            ai_player_id=2
        )

        for move_dict in get_next_states(self.current_state):
            if move_dict["action"] == best_action:
                self.current_state = move_dict["state"]
                break

        elapsed = time.time() - start_time

        if best_action is not None:
            if best_action["type"] == "move":
                self.info_label.config(
                    text=f"AI moved to {best_action['pos']} "
                         f"(time: {elapsed:.2f}s, eval: {best_score})"
                )
            else:
                orientation = "Horizontal" if best_action["orientation"] == "h" else "Vertical"
                self.info_label.config(
                    text=f"AI placed {orientation} wall at {best_action['pos']} "
                         f"(time: {elapsed:.2f}s, eval: {best_score})"
                )

        self.refresh_valid_moves()
        self.check_game_end()

    def check_game_end(self):
        self.refresh_valid_moves()

        if self.current_state.p1_pos[1] == 4:
            self.draw_board()
            messagebox.showinfo("Game Over", "You win!")
        elif self.current_state.p2_pos[1] == 0:
            self.draw_board()
            messagebox.showinfo("Game Over", "AI wins!")


def main():
    root = tk.Tk()
    app = QuoridorGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()