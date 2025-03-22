from typing import List, Tuple, Dict, Set
import heapq

class Pathfinder:
    def __init__(self, world):
        self.world = world

    def find_path(self, start_x: int, start_y: int, target_x: int, target_y: int) -> List[Tuple[int, int]]:
        """Find a path from start to target using A* algorithm."""
        if not self.world.is_valid_move(target_x, target_y):
            return []

        # Priority queue for open nodes
        open_set = []
        # Dictionary to store g_scores (cost from start to node)
        g_score = {}
        # Dictionary to store f_scores (g_score + heuristic)
        f_score = {}
        # Dictionary to store path parents
        came_from = {}
        
        start = (start_x, start_y)
        target = (target_x, target_y)
        
        # Initialize start node
        heapq.heappush(open_set, (0, start))
        g_score[start] = 0
        f_score[start] = self._heuristic(start, target)
        
        while open_set:
            current = heapq.heappop(open_set)[1]
            
            if current == target:
                return self._reconstruct_path(came_from, current)
            
            # Check all adjacent tiles (including diagonals)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                        
                    next_x = current[0] + dx
                    next_y = current[1] + dy
                    neighbor = (next_x, next_y)
                    
                    # Skip if not a valid move
                    if not self.world.is_valid_move(next_x, next_y):
                        continue
                    
                    # Calculate tentative g_score
                    # Use 1.4 for diagonal movement, 1 for cardinal directions
                    move_cost = 1.4 if dx != 0 and dy != 0 else 1
                    tentative_g_score = g_score[current] + move_cost
                    
                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = g_score[neighbor] + self._heuristic(neighbor, target)
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        
        return []  # No path found

    def _heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """Calculate heuristic distance between two points using diagonal distance."""
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return max(dx, dy) + 0.4 * min(dx, dy)

    def _reconstruct_path(self, came_from: Dict[Tuple[int, int], Tuple[int, int]], 
                         current: Tuple[int, int]) -> List[Tuple[int, int]]:
        """Reconstruct the path from the came_from dictionary."""
        path = [current]
        while current in came_from:
            current = came_from[current]
            path.append(current)
        path.reverse()
        return path 