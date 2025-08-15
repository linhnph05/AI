import heapq
from const import DIRECTIONS, DX, DY
from typing import List, Tuple, Optional, Set
import math

class PlanningModule:
    def __init__(self, knowledge_base, N):
        self.kb = knowledge_base
        self.N = N
        
    def calculate_cell_risk(self, x: int, y: int) -> float:
        """
        Calculate risk score for a cell based on knowledge base.
        Higher score = more dangerous
        """
        # If already visited and safe, no risk
        if (x, y) in self.kb.visited and self.kb.fact_exists("Safe", x, y):
            return 0.0
            
        # Confirmed dangers - absolutely avoid
        if self.kb.fact_exists("Pit", x, y):
            return float('inf')  # Deadly
        if self.kb.fact_exists("Wumpus", x, y):
            return float('inf')  # Deadly (avoid unless we can shoot)
            
        # Possible dangers - strongly avoid
        risk = 0.0
        if self.kb.fact_exists("PossiblePit", x, y):
            return 1000.0  # Very high risk - avoid unless absolutely necessary
        if self.kb.fact_exists("PossibleWumpus", x, y):
            return 800.0  # High risk - avoid unless absolutely necessary
            
        # Unknown cells have some risk but are explorable
        if not self.kb.fact_exists("Safe", x, y) and (x, y) not in self.kb.visited:
            # Check if this unknown cell is adjacent to any breeze/stench
            adjacent_to_danger = False
            for adj_x, adj_y in self.kb.get_adjacent(x, y):
                if (self.kb.fact_exists("Breeze", adj_x, adj_y) or 
                    self.kb.fact_exists("Stench", adj_x, adj_y)):
                    adjacent_to_danger = True
                    break
            
            if adjacent_to_danger:
                risk += 100.0  # Higher risk for unknown cells near danger
            else:
                risk += 5.0  # Lower risk for unknown cells far from danger
            
        return risk
    
    def calculate_cell_utility(self, x: int, y: int, has_gold: bool) -> float:
        """
        Calculate utility/reward for visiting a cell using correct scoring.
        Higher score = more valuable
        """
        utility = 0.0
        
        # Gold is valuable if we don't have it yet (+10 points)
        if not has_gold and self.kb.fact_exists("glitter", x, y):
            utility += 10.0
            
        # Unvisited safe cells have exploration value
        if (x, y) not in self.kb.visited and self.kb.fact_exists("Safe", x, y):
            utility += 5.0
            
        # Unknown cells have some exploration value but less
        if (x, y) not in self.kb.visited and not self.kb.fact_exists("Safe", x, y):
            utility += 2.0
            
        # Being at start position (0,0) with gold is the ultimate goal (+1000)
        if x == 0 and y == 0 and has_gold:
            utility += 1000.0
            
        return utility
    
    def calculate_movement_cost(self, from_x: int, from_y: int, to_x: int, to_y: int, 
                              current_dir: str, target_dir: str) -> float:
        """
        Calculate cost of moving from one cell to another using actual scoring rules.
        """
        # Movement cost (forward = -1)
        base_cost = 1.0
        
        # Turning cost (each turn = -1)
        if current_dir != target_dir:
            current_idx = DIRECTIONS.index(current_dir)
            target_idx = DIRECTIONS.index(target_dir)
            turns = min(abs(target_idx - current_idx), 4 - abs(target_idx - current_idx))
            base_cost += turns  # Each turn costs 1 point
            
        # Risk-based cost modifier
        risk = self.calculate_cell_risk(to_x, to_y)
        if risk == float('inf'):
            return float('inf')  # Cannot move to deadly cells
            
        # Add risk as additional cost (death = -1000)
        if risk > 80:  # High risk areas
            base_cost += 50  # Significant penalty for risky moves
        elif risk > 30:  # Medium risk areas
            base_cost += 10  # Moderate penalty
            
        return base_cost
    
    def get_direction_to_move(self, from_x: int, from_y: int, to_x: int, to_y: int) -> str:
        """Get the direction needed to move from one cell to another."""
        dx = to_x - from_x
        dy = to_y - from_y
        
        if dx == 1:
            return 'E'
        elif dx == -1:
            return 'W'
        elif dy == 1:
            return 'N'
        elif dy == -1:
            return 'S'
        else:
            raise ValueError(f"Invalid movement from ({from_x},{from_y}) to ({to_x},{to_y})")
    
    def heuristic(self, x: int, y: int, goal_x: int, goal_y: int) -> float:
        """Manhattan distance heuristic for A*."""
        return abs(x - goal_x) + abs(y - goal_y)
    
    def a_star_search(self, start_x: int, start_y: int, goal_x: int, goal_y: int, 
                     current_dir: str, avoid_dangerous: bool = True) -> Optional[List[Tuple[int, int, str]]]:
        """
        A* search algorithm to find optimal path from start to goal.
        Returns list of (x, y, direction) tuples or None if no path found.
        """
        # Priority queue: (f_score, g_score, x, y, direction, path)
        open_set = [(0, 0, start_x, start_y, current_dir, [])]
        closed_set: Set[Tuple[int, int, str]] = set()
        
        # Best g_scores for each state (x, y, direction)
        g_scores = {(start_x, start_y, current_dir): 0}
        
        while open_set:
            f_score, g_score, x, y, direction, path = heapq.heappop(open_set)
            
            # Skip if already processed this state
            state = (x, y, direction)
            if state in closed_set:
                continue
            closed_set.add(state)
            
            # Goal reached
            if x == goal_x and y == goal_y:
                return path + [(x, y, direction)]
            
            # Explore neighbors
            for next_dir in DIRECTIONS:
                dx, dy = DX[next_dir], DY[next_dir]
                nx, ny = x + dx, y + dy
                
                # Check bounds
                if not (0 <= nx < self.N and 0 <= ny < self.N):
                    continue
                
                # Skip dangerous cells if avoiding them
                if avoid_dangerous:
                    risk = self.calculate_cell_risk(nx, ny)
                    if risk == float('inf'):  # Confirmed pit
                        continue
                    if risk > 80:  # Very high risk (confirmed wumpus)
                        continue
                
                # Calculate costs
                move_cost = self.calculate_movement_cost(x, y, nx, ny, direction, next_dir)
                if move_cost == float('inf'):
                    continue
                
                tentative_g = g_score + move_cost
                next_state = (nx, ny, next_dir)
                
                # Skip if we've found a better path to this state
                if next_state in g_scores and tentative_g >= g_scores[next_state]:
                    continue
                
                g_scores[next_state] = tentative_g
                f_score = tentative_g + self.heuristic(nx, ny, goal_x, goal_y)
                
                new_path = path + [(x, y, direction)]
                heapq.heappush(open_set, (f_score, tentative_g, nx, ny, next_dir, new_path))
        
        return None  # No path found
    
    def dijkstra_search(self, start_x: int, start_y: int, current_dir: str, 
                       has_gold: bool = False) -> Optional[Tuple[int, int, List[Tuple[int, int, str]]]]:
        """
        Dijkstra's algorithm to find the most valuable reachable cell considering risk and utility.
        Prioritizes safe cells and avoids possible dangers.
        Returns (best_x, best_y, path) or None.
        """
        # Priority queue: (negative_utility_to_cost_ratio, cost, x, y, direction, path)
        open_set = [(0, 0, start_x, start_y, current_dir, [])]
        visited: Set[Tuple[int, int]] = set()
        
        best_cell = None
        best_ratio = float('-inf')
        best_path = None
        
        while open_set:
            neg_ratio, cost, x, y, direction, path = heapq.heappop(open_set)
            
            # Skip if already visited this cell
            if (x, y) in visited:
                continue
            visited.add((x, y))
            
            # Calculate utility for this cell
            utility = self.calculate_cell_utility(x, y, has_gold)
            ratio = utility / max(cost, 1)  # Utility to cost ratio
            
            # Only consider cells that are actually worth visiting and not dangerous
            risk = self.calculate_cell_risk(x, y)
            if utility > 0 and risk < 500:  # Avoid high-risk cells
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_cell = (x, y)
                    best_path = path + [(x, y, direction)]
            
            # Explore neighbors
            for next_dir in DIRECTIONS:
                dx, dy = DX[next_dir], DY[next_dir]
                nx, ny = x + dx, y + dy
                
                # Check bounds
                if not (0 <= nx < self.N and 0 <= ny < self.N):
                    continue
                
                # Skip if already visited
                if (nx, ny) in visited:
                    continue
                
                # Skip very dangerous cells - be more strict
                risk = self.calculate_cell_risk(nx, ny)
                if risk == float('inf'):
                    continue
                if risk > 500:  # Skip possible pits/wumpuses
                    continue
                
                # Calculate cost to reach this neighbor
                move_cost = self.calculate_movement_cost(x, y, nx, ny, direction, next_dir)
                if move_cost == float('inf'):
                    continue
                
                new_cost = cost + move_cost
                new_path = path + [(x, y, direction)]
                
                # Use negative ratio for min-heap (we want max ratio)
                utility_estimate = self.calculate_cell_utility(nx, ny, has_gold)
                estimated_ratio = utility_estimate / max(new_cost, 1)
                
                heapq.heappush(open_set, (-estimated_ratio, new_cost, nx, ny, next_dir, new_path))
        
        if best_cell:
            return (best_cell[0], best_cell[1], best_path)
        return None
    
    def plan_optimal_action(self, agent_x: int, agent_y: int, agent_dir: str, 
                          has_gold: bool, has_shot: bool, current_score: int = 0) -> str:
        """
        Plan the optimal action using search algorithms and utility calculations.
        Prioritizes safe exploration over risky moves.
        """
        # Priority 1: Climb if at (0,0) with gold
        if agent_x == 0 and agent_y == 0 and has_gold:
            return "CLIMB"
        
        # Priority 2: Return to (0,0) if we have gold
        if has_gold and (agent_x != 0 or agent_y != 0):
            path = self.a_star_search(agent_x, agent_y, 0, 0, agent_dir, avoid_dangerous=True)
            if path and len(path) > 1:
                next_x, next_y, next_dir = path[1]  # Skip current position
                required_dir = self.get_direction_to_move(agent_x, agent_y, next_x, next_y)
                
                if agent_dir != required_dir:
                    return self._get_turn_action(agent_dir, required_dir)
                else:
                    return "FORWARD"
        
        # Priority 3: Grab gold if available
        if not has_gold and self.kb.fact_exists("glitter", agent_x, agent_y):
            return "GRAB"
        
        # Priority 4: Shoot wumpus if there's a confirmed one in front and haven't shot
        if not has_shot:
            dx, dy = DX[agent_dir], DY[agent_dir]
            x, y = agent_x + dx, agent_y + dy
            while 0 <= x < self.N and 0 <= y < self.N:
                if self.kb.fact_exists("Wumpus", x, y):
                    return "SHOOT"
                if self.kb.fact_exists("Safe", x, y) and (x, y) in self.kb.visited:
                    break  # Can't shoot through visited safe cells
                x += dx
                y += dy
        
        # Priority 5: Move to confirmed safe adjacent cells first
        safe_adjacent = []
        for next_dir in DIRECTIONS:
            dx, dy = DX[next_dir], DY[next_dir]
            nx, ny = agent_x + dx, agent_y + dy
            
            if 0 <= nx < self.N and 0 <= ny < self.N:
                if ((nx, ny) not in self.kb.visited and 
                    self.kb.fact_exists("Safe", nx, ny) and
                    not self.kb.fact_exists("PossiblePit", nx, ny) and
                    not self.kb.fact_exists("PossibleWumpus", nx, ny)):
                    safe_adjacent.append((nx, ny, next_dir))
        
        if safe_adjacent:
            # Choose the first confirmed safe adjacent cell
            nx, ny, required_dir = safe_adjacent[0]
            if agent_dir != required_dir:
                return self._get_turn_action(agent_dir, required_dir)
            else:
                return "FORWARD"
        
        # Priority 6: Use Dijkstra to find most valuable reachable SAFE cell
        result = self.dijkstra_search(agent_x, agent_y, agent_dir, has_gold)
        if result:
            target_x, target_y, path = result
            # Double-check the target is actually safe
            risk = self.calculate_cell_risk(target_x, target_y)
            if risk < 100:  # Only go to low-risk targets
                if len(path) > 1:
                    next_x, next_y, next_dir = path[1]  # Skip current position
                    required_dir = self.get_direction_to_move(agent_x, agent_y, next_x, next_y)
                    
                    if agent_dir != required_dir:
                        return self._get_turn_action(agent_dir, required_dir)
                    else:
                        return "FORWARD"
        
        # Priority 7: Explore unknown cells that are NOT adjacent to breeze/stench
        safe_unknown = []
        for next_dir in DIRECTIONS:
            dx, dy = DX[next_dir], DY[next_dir]
            nx, ny = agent_x + dx, agent_y + dy
            
            if 0 <= nx < self.N and 0 <= ny < self.N:
                if ((nx, ny) not in self.kb.visited and
                    not self.kb.fact_exists("PossiblePit", nx, ny) and
                    not self.kb.fact_exists("PossibleWumpus", nx, ny) and
                    not self.kb.fact_exists("Pit", nx, ny) and
                    not self.kb.fact_exists("Wumpus", nx, ny)):
                    
                    # Check if this unknown cell is far from danger signals
                    is_safe_unknown = True
                    for adj_x, adj_y in self.kb.get_adjacent(nx, ny):
                        if (self.kb.fact_exists("Breeze", adj_x, adj_y) or 
                            self.kb.fact_exists("Stench", adj_x, adj_y)):
                            is_safe_unknown = False
                            break
                    
                    if is_safe_unknown:
                        safe_unknown.append((nx, ny, next_dir))
        
        if safe_unknown:
            # Choose the first safe unknown cell
            nx, ny, required_dir = safe_unknown[0]
            if agent_dir != required_dir:
                return self._get_turn_action(agent_dir, required_dir)
            else:
                return "FORWARD"
        
        # Priority 8: Strategic decision when all unexplored cells are dangerous
        risky_cells, all_dangerous = self.analyze_exploration_options(agent_x, agent_y)
        
        if all_dangerous and risky_cells:
            print(f"⚠️  All unexplored cells are dangerous! Found {len(risky_cells)} risky options.")
            print(f"💰 Current situation: Score={current_score}, Gold={'Yes' if has_gold else 'No'}")
            
            # Make strategic decision using the risk vs reward evaluation
            strategy = self.evaluate_risk_vs_reward(current_score, has_gold, risky_cells)
            
            if strategy == "RETREAT":
                print(f"🛡️  Strategy: RETREAT - Returning to (0,0) to preserve score")
                # Return to start to climb and preserve points
                if (agent_x, agent_y) != (0, 0):
                    path = self.a_star_search(agent_x, agent_y, 0, 0, agent_dir, avoid_dangerous=False)
                    if path and len(path) > 1:
                        next_x, next_y, next_dir = path[1]
                        required_dir = self.get_direction_to_move(agent_x, agent_y, next_x, next_y)
                        
                        if agent_dir != required_dir:
                            return self._get_turn_action(agent_dir, required_dir)
                        else:
                            return "FORWARD"
                else:
                    return "CLIMB"  # Already at start, climb out
                    
            elif strategy == "RISK_CLOSEST":
                print(f"🎲 Strategy: RISK_CLOSEST - Taking calculated risk on nearest cell")
                risky_action = self.find_closest_risky_cell(agent_x, agent_y, agent_dir, risky_cells)
                if risky_action:
                    return risky_action
        
        # Priority 9: Take calculated risks with lower-risk adjacent cells
        low_risk_adjacent = []
        for next_dir in DIRECTIONS:
            dx, dy = DX[next_dir], DY[next_dir]
            nx, ny = agent_x + dx, agent_y + dy
            
            if 0 <= nx < self.N and 0 <= ny < self.N:
                if (nx, ny) not in self.kb.visited:
                    risk = self.calculate_cell_risk(nx, ny)
                    if risk < float('inf'):  # Not deadly
                        low_risk_adjacent.append((risk, nx, ny, next_dir))
        
        if low_risk_adjacent:
            # Sort by risk (lowest first)
            low_risk_adjacent.sort()
            risk, nx, ny, required_dir = low_risk_adjacent[0]
            
            print(f"⚠️  Taking calculated risk: cell ({nx},{ny}) with risk {risk:.1f}")
            
            if agent_dir != required_dir:
                return self._get_turn_action(agent_dir, required_dir)
            else:
                return "FORWARD"
        
        # Priority 10: Return to start if no other options
        if (agent_x, agent_y) != (0, 0):
            print(f"🏠 No safe moves available, returning to start")
            path = self.a_star_search(agent_x, agent_y, 0, 0, agent_dir, avoid_dangerous=False)
            if path and len(path) > 1:
                next_x, next_y, next_dir = path[1]
                required_dir = self.get_direction_to_move(agent_x, agent_y, next_x, next_y)
                
                if agent_dir != required_dir:
                    return self._get_turn_action(agent_dir, required_dir)
                else:
                    return "FORWARD"
            else:
                return "CLIMB"  # Can't find path, try to climb
        else:
            # At start position, climb out to preserve any points
            return "CLIMB"
        
        # Last resort
        print(f"❌ No viable actions available")
        return "QUIT"
    
    def _get_turn_action(self, current_dir: str, required_dir: str) -> str:
        """Calculate whether to turn left or right to reach required direction."""
        current_idx = DIRECTIONS.index(current_dir)
        required_idx = DIRECTIONS.index(required_dir)
        clockwise_turns = (required_idx - current_idx) % 4
        
        if clockwise_turns <= 2:
            return "RIGHT"
        else:
            return "LEFT"
    
    def analyze_exploration_options(self, agent_x: int, agent_y: int) -> Tuple[List[Tuple[int, int, float]], bool]:
        """
        Analyze all unexplored cells and categorize them by risk.
        Returns (risky_unexplored_cells, all_unexplored_are_dangerous)
        """
        unexplored_cells = []
        
        # Find all unexplored cells in the map
        for y in range(self.N):
            for x in range(self.N):
                if (x, y) not in self.kb.visited:
                    risk = self.calculate_cell_risk(x, y)
                    if risk < float('inf'):  # Not completely deadly
                        steps_away = abs(x - agent_x) + abs(y - agent_y)  # Manhattan distance
                        unexplored_cells.append((x, y, risk, steps_away))
        
        # Check if any unexplored cells are actually safe
        safe_unexplored = [cell for cell in unexplored_cells if cell[2] < 50]  # Risk < 50 is considered safe
        all_dangerous = len(safe_unexplored) == 0 and len(unexplored_cells) > 0
        
        # Sort by steps away (distance) for risky cells
        risky_cells = [(x, y, risk) for x, y, risk, steps in unexplored_cells if risk >= 50]
        risky_cells_with_distance = [(x, y, risk, abs(x - agent_x) + abs(y - agent_y)) for x, y, risk in risky_cells]
        risky_cells_with_distance.sort(key=lambda cell: cell[3])  # Sort by distance
        
        return risky_cells_with_distance, all_dangerous
    
    def evaluate_risk_vs_reward(self, current_score: int, has_gold: bool, risky_cells: List[Tuple[int, int, float, int]]) -> str:
        """
        Evaluate whether to take risks or retreat based on current situation.
        Returns strategy: "RETREAT", "RISK_CLOSEST", or "CONTINUE"
        """
        # If we have gold, retreat is often the safer choice
        if has_gold:
            if current_score > 500:  # Good score with gold, retreat
                return "RETREAT"
            elif current_score > 0 and len(risky_cells) > 0:
                # Consider risk vs potential loss
                closest_risk = risky_cells[0][2] if risky_cells else float('inf')
                if closest_risk > 500:  # Very high risk
                    return "RETREAT"
                else:
                    return "RISK_CLOSEST"  # Moderate risk, worth trying
            else:
                return "RISK_CLOSEST"  # Low score, need to try
        
        # No gold yet
        if current_score <= -500:  # Already low score, might as well try
            return "RISK_CLOSEST"
        elif current_score > 0:  # Positive score, be more cautious
            if risky_cells and risky_cells[0][2] < 300:  # Moderate risk
                return "RISK_CLOSEST"
            else:
                return "RETREAT"  # Too risky
        else:  # Slightly negative score
            return "RISK_CLOSEST"
    
    def find_closest_risky_cell(self, agent_x: int, agent_y: int, agent_dir: str, risky_cells: List[Tuple[int, int, float, int]]) -> Optional[str]:
        """
        Find the closest risky unexplored cell and return the action to move towards it.
        """
        if not risky_cells:
            return None
        
        # Take the closest risky cell
        target_x, target_y, risk, distance = risky_cells[0]
        
        print(f"🎲 Taking calculated risk: targeting ({target_x},{target_y}) with risk {risk:.1f}, {distance} steps away")
        
        # Try to find a path to the risky cell
        path = self.a_star_search(agent_x, agent_y, target_x, target_y, agent_dir, avoid_dangerous=False)
        
        if path and len(path) > 1:
            next_x, next_y, next_dir = path[1]  # Skip current position
            required_dir = self.get_direction_to_move(agent_x, agent_y, next_x, next_y)
            
            if agent_dir != required_dir:
                return self._get_turn_action(agent_dir, required_dir)
            else:
                return "FORWARD"
        
        # If no path found, try adjacent risky cells
        for next_dir in DIRECTIONS:
            dx, dy = DX[next_dir], DY[next_dir]
            nx, ny = agent_x + dx, agent_y + dy
            
            if 0 <= nx < self.N and 0 <= ny < self.N and (nx, ny) not in self.kb.visited:
                risk = self.calculate_cell_risk(nx, ny)
                if risk < float('inf'):  # Not deadly
                    if agent_dir != next_dir:
                        return self._get_turn_action(agent_dir, next_dir)
                    else:
                        return "FORWARD"
        
        return None
