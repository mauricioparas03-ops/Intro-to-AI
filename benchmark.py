# benchmark.py
import time
import matplotlib.pyplot as plt
from quoridor_5x5_env import GameState5x5
from abpruning import alpha_beta_search

def run_benchmark():
    # Setup a mid-game state (more branching factor = better test)
    # P1 is at C2, P2 is at C4. A few walls are placed.
    test_state = GameState5x5(
        p1_pos=(2, 1), p2_pos=(2, 3),
        p1_walls=2, p2_walls=2,
        h_walls=[(1, 2), (2, 2)], # A horizontal wall in the middle
        v_walls=[],
        turn=2 # AI's turn
    )

    depths = [1, 2, 3, 4]
    
    # Data storage for graphs
    ab_nodes, mm_nodes = [], []
    ab_times, mm_times = [], []
    ab_prunes = []

    print("Starting Benchmark...")
    
    for d in depths:
        print(f"\n--- Testing Depth {d} ---")
        
        # 1. Test Without Pruning (Standard Minimax)
        stats_mm = {'visited': 0, 'pruned': 0}
        start_time = time.time()
        alpha_beta_search(test_state, d, float('-inf'), float('inf'), True, 2, stats_mm, use_pruning=False)
        time_mm = time.time() - start_time
        
        mm_nodes.append(stats_mm['visited'])
        mm_times.append(time_mm)
        print(f"Minimax    -> Visited: {stats_mm['visited']:>6} | Time: {time_mm:.3f}s")

        # 2. Test With Alpha-Beta Pruning
        stats_ab = {'visited': 0, 'pruned': 0}
        start_time = time.time()
        alpha_beta_search(test_state, d, float('-inf'), float('inf'), True, 2, stats_ab, use_pruning=True)
        time_ab = time.time() - start_time
        
        ab_nodes.append(stats_ab['visited'])
        ab_times.append(time_ab)
        ab_prunes.append(stats_ab['pruned'])
        print(f"Alpha-Beta -> Visited: {stats_ab['visited']:>6} | Time: {time_ab:.3f}s | Pruned: {stats_ab['pruned']}")

    plot_graphs(depths, mm_nodes, ab_nodes, mm_times, ab_times, ab_prunes)

def plot_graphs(depths, mm_nodes, ab_nodes, mm_times, ab_times, ab_prunes):
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))

    # Graph 1: Nodes Visited (Log Scale)
    ax1.plot(depths, mm_nodes, label='Standard Minimax', marker='o', color='red')
    ax1.plot(depths, ab_nodes, label='Alpha-Beta Pruning', marker='o', color='green')
    ax1.set_yscale('log') # Log scale because game trees grow exponentially
    ax1.set_title('Total States Evaluated (Efficiency)')
    ax1.set_xlabel('Search Depth')
    ax1.set_ylabel('Nodes Visited (Log Scale)')
    ax1.legend()
    ax1.grid(True, which="both", ls="--", alpha=0.5)

    # Graph 2: Execution Time
    ax2.plot(depths, mm_times, label='Standard Minimax', marker='o', color='red')
    ax2.plot(depths, ab_times, label='Alpha-Beta Pruning', marker='o', color='green')
    ax2.set_title('Execution Time (Speed)')
    ax2.set_xlabel('Search Depth')
    ax2.set_ylabel('Time in Seconds')
    ax2.legend()
    ax2.grid(True, ls="--", alpha=0.5)

    # Graph 3: Pruning Events
    ax3.bar(depths, ab_prunes, color='purple', alpha=0.7)
    ax3.set_title('Number of Branches Pruned')
    ax3.set_xlabel('Search Depth')
    ax3.set_ylabel('Prune Count')
    ax3.set_xticks(depths)
    ax3.grid(axis='y', ls="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig('alphabeta_efficiency.png')
    print("\nGraphs saved as 'alphabeta_efficiency.png'. Open it to see the results!")

if __name__ == "__main__":
    run_benchmark()