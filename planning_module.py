import heapq
from const import DIRECTIONS, DX, DY
from typing import List, Tuple, Optional, Set
class PlanningModule:
    def __init__(self, knowledge_base, N):
        self.kb = knowledge_base
        self.N = N
        
    def calculate_cell_risk(self, x: int, y: int) -> float:
        if (x, y) in self.kb.visited and self.kb.fact_exists("Safe", x, y):
            return 0.0
            
        if self.kb.fact_exists("Pit", x, y):
            return float('inf')
        if self.kb.fact_exists("Wumpus", x, y):
            return float('inf')
            
        risk = 0.0
        if self.kb.fact_exists("PossiblePit", x, y):
            return 1000.0
        
        if self.kb.fact_exists("PossibleWumpus", x, y):
            if self.kb.fact_exists("AllWumpusesKilled", x, y):
                risk += 0.0
            else:
                return 800.0
            
        if not self.kb.fact_exists("Safe", x, y) and (x, y) not in self.kb.visited:
            adjacent_to_danger = False
            for adj_x, adj_y in self.kb.get_adjacent(x, y):
                if self.kb.fact_exists("Breeze", adj_x, adj_y):
                    adjacent_to_danger = True
                    break
                elif (self.kb.fact_exists("Stench", adj_x, adj_y) and 
                      not self.kb.fact_exists("AllWumpusesKilled"), adj_x, adj_y):
                    adjacent_to_danger = True
                    break
                    adjacent_to_danger = True
                    break
            
            if adjacent_to_danger:
                risk += 100.0
            else:
                risk += 5.0
            
        return risk
    
    def calculate_cell_utility(self, x: int, y: int, has_gold: bool) -> float:
        utility = 0.0
        
        if not has_gold and self.kb.fact_exists("glitter", x, y):
            utility += 10.0
            
        if (x, y) not in self.kb.visited and self.kb.fact_exists("Safe", x, y):
            utility += 5.0
            
        if (x, y) not in self.kb.visited and not self.kb.fact_exists("Safe", x, y):
            utility += 2.0
            
        if x == 0 and y == 0 and has_gold:
            utility += 1000.0
            
        return utility
    
    def calculate_movement_cost(self, from_x: int, from_y: int, to_x: int, to_y: int, 
                              current_dir: str, target_dir: str) -> float:
        base_cost = 1.0
        
        if current_dir != target_dir:
            current_idx = DIRECTIONS.index(current_dir)
            target_idx = DIRECTIONS.index(target_dir)
            turns = min(abs(target_idx - current_idx), 4 - abs(target_idx - current_idx))
            base_cost += turns
            
        risk = self.calculate_cell_risk(to_x, to_y)
        if risk == float('inf'):
            return float('inf')
            
        if risk > 80:
            base_cost += 50
        elif risk > 30:
            base_cost += 10
            
        return base_cost
    
    def get_direction_to_move(self, from_x: int, from_y: int, to_x: int, to_y: int) -> str:
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
        return abs(x - goal_x) + abs(y - goal_y)
    
    def a_star_search(self, start_x: int, start_y: int, goal_x: int, goal_y: int, 
                     current_dir: str, avoid_dangerous: bool = True) -> Optional[List[Tuple[int, int, str]]]:
        open_set = [(0, 0, start_x, start_y, current_dir, [])]
        closed_set: Set[Tuple[int, int, str]] = set()
        
        g_scores = {(start_x, start_y, current_dir): 0}
        
        while open_set:
            f_score, g_score, x, y, direction, path = heapq.heappop(open_set)
            
            state = (x, y, direction)
            if state in closed_set:
                continue
            closed_set.add(state)
            
            if x == goal_x and y == goal_y:
                return path + [(x, y, direction)]
            
            for next_dir in DIRECTIONS:
                dx, dy = DX[next_dir], DY[next_dir]
                nx, ny = x + dx, y + dy
                
                if not (0 <= nx < self.N and 0 <= ny < self.N):
                    continue
                
                if avoid_dangerous:
                    risk = self.calculate_cell_risk(nx, ny)
                    if risk == float('inf'):
                        continue
                    if risk > 80:
                        continue
                
                move_cost = self.calculate_movement_cost(x, y, nx, ny, direction, next_dir)
                if move_cost == float('inf'):
                    continue
                
                tentative_g = g_score + move_cost
                next_state = (nx, ny, next_dir)
                
                if next_state in g_scores and tentative_g >= g_scores[next_state]:
                    continue
                
                g_scores[next_state] = tentative_g
                f_score = tentative_g + self.heuristic(nx, ny, goal_x, goal_y)
                
                new_path = path + [(x, y, direction)]
                heapq.heappush(open_set, (f_score, tentative_g, nx, ny, next_dir, new_path))
        
        return None
    
    def dijkstra_search(self, start_x: int, start_y: int, current_dir: str, 
                       has_gold: bool = False) -> Optional[Tuple[int, int, List[Tuple[int, int, str]]]]:
        open_set = [(0, 0, start_x, start_y, current_dir, [])]
        visited: Set[Tuple[int, int]] = set()
        
        best_cell = None
        best_ratio = float('-inf')
        best_path = None
        
        while open_set:
            neg_ratio, cost, x, y, direction, path = heapq.heappop(open_set)
            
            if (x, y) in visited:
                continue
            visited.add((x, y))
            
            utility = self.calculate_cell_utility(x, y, has_gold)
            ratio = utility / max(cost, 1)
            
            risk = self.calculate_cell_risk(x, y)
            if utility > 0 and risk < 500:
                if ratio > best_ratio:
                    best_ratio = ratio
                    best_cell = (x, y)
                    best_path = path + [(x, y, direction)]
            
            for next_dir in DIRECTIONS:
                dx, dy = DX[next_dir], DY[next_dir]
                nx, ny = x + dx, y + dy
                
                if not (0 <= nx < self.N and 0 <= ny < self.N):
                    continue
                
                if (nx, ny) in visited:
                    continue
                
                risk = self.calculate_cell_risk(nx, ny)
                if risk == float('inf'):
                    continue
                if risk > 500:
                    continue
                
                move_cost = self.calculate_movement_cost(x, y, nx, ny, direction, next_dir)
                if move_cost == float('inf'):
                    continue
                
                new_cost = cost + move_cost
                new_path = path + [(x, y, direction)]
                
                utility_estimate = self.calculate_cell_utility(nx, ny, has_gold)
                estimated_ratio = utility_estimate / max(new_cost, 1)
                
                heapq.heappush(open_set, (-estimated_ratio, new_cost, nx, ny, next_dir, new_path))
        
        if best_cell:
            return (best_cell[0], best_cell[1], best_path)
        return None
    
    def plan_optimal_action(self, agent_x: int, agent_y: int, agent_dir: str, 
                          has_gold: bool, has_shot: bool, current_score: int = 0) -> str:
        if agent_x == 0 and agent_y == 0 and has_gold:
            return "CLIMB"
        
        if has_gold and (agent_x != 0 or agent_y != 0):
            path = self.a_star_search(agent_x, agent_y, 0, 0, agent_dir, avoid_dangerous=True)
            if path and len(path) > 1:
                next_x, next_y, next_dir = path[1]
                required_dir = self.get_direction_to_move(agent_x, agent_y, next_x, next_y)
                
                if agent_dir != required_dir:
                    return self._get_turn_action(agent_dir, required_dir)
                else:
                    return "FORWARD"
        
        if not has_gold and self.kb.fact_exists("glitter", agent_x, agent_y):
            return "GRAB"
        
        if not has_shot and not self.kb.fact_exists("AllWumpusesKilled", agent_x, agent_y):
            dx, dy = DX[agent_dir], DY[agent_dir]
            x, y = agent_x + dx, agent_y + dy
            while 0 <= x < self.N and 0 <= y < self.N:
                if self.kb.fact_exists("Wumpus", x, y):
                    return "SHOOT"
                if self.kb.fact_exists("Safe", x, y) and (x, y) in self.kb.visited:
                    break
                x += dx
                y += dy
        
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
            nx, ny, required_dir = safe_adjacent[0]
            if agent_dir != required_dir:
                return self._get_turn_action(agent_dir, required_dir)
            else:
                return "FORWARD"
        
        result = self.dijkstra_search(agent_x, agent_y, agent_dir, has_gold)
        if result:
            target_x, target_y, path = result
            risk = self.calculate_cell_risk(target_x, target_y)
            if risk < 100:
                if len(path) > 1:
                    next_x, next_y, next_dir = path[1]
                    required_dir = self.get_direction_to_move(agent_x, agent_y, next_x, next_y)
                    
                    if agent_dir != required_dir:
                        return self._get_turn_action(agent_dir, required_dir)
                    else:
                        return "FORWARD"
        
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
                    
                    is_safe_unknown = True
                    for adj_x, adj_y in self.kb.get_adjacent(nx, ny):
                        if (self.kb.fact_exists("Breeze", adj_x, adj_y) or 
                            self.kb.fact_exists("Stench", adj_x, adj_y)):
                            is_safe_unknown = False
                            break
                    
                    if is_safe_unknown:
                        safe_unknown.append((nx, ny, next_dir))
        
        if safe_unknown:
            nx, ny, required_dir = safe_unknown[0]
            if agent_dir != required_dir:
                return self._get_turn_action(agent_dir, required_dir)
            else:
                return "FORWARD"
        
        risky_cells, all_dangerous = self.analyze_exploration_options(agent_x, agent_y)
        
        if all_dangerous and risky_cells:
            print(f"All unexplored cells are dangerous! Found {len(risky_cells)} risky options.")
            print(f"Current situation: Score={current_score}, Gold={'Yes' if has_gold else 'No'}")
            
            strategy = self.evaluate_risk_vs_reward(current_score, has_gold, risky_cells)
            
            if strategy == "RETREAT":
                print(f"Strategy: RETREAT - Returning to (0,0) to preserve score")
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
                    return "CLIMB"
                    
            elif strategy == "RISK_CLOSEST":
                print(f"Strategy: RISK_CLOSEST - Taking calculated risk on nearest cell")
                risky_action = self.find_closest_risky_cell(agent_x, agent_y, agent_dir, risky_cells)
                if risky_action:
                    return risky_action
        
        low_risk_adjacent = []
        for next_dir in DIRECTIONS:
            dx, dy = DX[next_dir], DY[next_dir]
            nx, ny = agent_x + dx, agent_y + dy
            
            if 0 <= nx < self.N and 0 <= ny < self.N:
                if (nx, ny) not in self.kb.visited:
                    risk = self.calculate_cell_risk(nx, ny)
                    if risk < float('inf'):
                        low_risk_adjacent.append((risk, nx, ny, next_dir))
        
        if low_risk_adjacent:
            low_risk_adjacent.sort()
            risk, nx, ny, required_dir = low_risk_adjacent[0]
            
            print(f"Taking calculated risk: cell ({nx},{ny}) with risk {risk:.1f}")
            
            if agent_dir != required_dir:
                return self._get_turn_action(agent_dir, required_dir)
            else:
                return "FORWARD"
        
        if (agent_x, agent_y) != (0, 0):
            print(f"No safe moves available, returning to start")
            path = self.a_star_search(agent_x, agent_y, 0, 0, agent_dir, avoid_dangerous=False)
            if path and len(path) > 1:
                next_x, next_y, next_dir = path[1]
                required_dir = self.get_direction_to_move(agent_x, agent_y, next_x, next_y)
                
                if agent_dir != required_dir:
                    return self._get_turn_action(agent_dir, required_dir)
                else:
                    return "FORWARD"
            else:
                return "CLIMB"
        else:
            return "CLIMB"
    
    def _get_turn_action(self, current_dir: str, required_dir: str) -> str:
        current_idx = DIRECTIONS.index(current_dir)
        required_idx = DIRECTIONS.index(required_dir)
        clockwise_turns = (required_idx - current_idx) % 4
        
        if clockwise_turns <= 2:
            return "RIGHT"
        else:
            return "LEFT"
    
    def analyze_exploration_options(self, agent_x: int, agent_y: int) -> Tuple[List[Tuple[int, int, float]], bool]:
        unexplored_cells = []
        
        for y in range(self.N):
            for x in range(self.N):
                if (x, y) not in self.kb.visited:
                    risk = self.calculate_cell_risk(x, y)
                    if risk < float('inf'):
                        steps_away = abs(x - agent_x) + abs(y - agent_y)
                        unexplored_cells.append((x, y, risk, steps_away))
        
        safe_unexplored = [cell for cell in unexplored_cells if cell[2] < 50]
        all_dangerous = len(safe_unexplored) == 0 and len(unexplored_cells) > 0
        
        risky_cells = [(x, y, risk) for x, y, risk, steps in unexplored_cells if risk >= 50]
        risky_cells_with_distance = [(x, y, risk, abs(x - agent_x) + abs(y - agent_y)) for x, y, risk in risky_cells]
        risky_cells_with_distance.sort(key=lambda cell: cell[3])
        
        return risky_cells_with_distance, all_dangerous
    
    def evaluate_risk_vs_reward(self, current_score: int, has_gold: bool, risky_cells: List[Tuple[int, int, float, int]]) -> str:
        if has_gold:
            if current_score > 500:
                return "RETREAT"
            elif current_score > 0 and len(risky_cells) > 0:
                closest_risk = risky_cells[0][2] if risky_cells else float('inf')
                if closest_risk > 500:
                    return "RETREAT"
                else:
                    return "RISK_CLOSEST"
            else:
                return "RISK_CLOSEST"
        
        if current_score <= -500:
            return "RISK_CLOSEST"
        elif current_score > 0:
            if risky_cells and risky_cells[0][2] < 300:
                return "RISK_CLOSEST"
            else:
                return "RETREAT"
        else:
            return "RISK_CLOSEST"
    
    def find_closest_risky_cell(self, agent_x: int, agent_y: int, agent_dir: str, risky_cells: List[Tuple[int, int, float, int]]) -> Optional[str]:
        if not risky_cells:
            return None
        
        target_x, target_y, risk, distance = risky_cells[0]
        
        print(f"Taking calculated risk: targeting ({target_x},{target_y}) with risk {risk:.1f}, {distance} steps away")
        
        path = self.a_star_search(agent_x, agent_y, target_x, target_y, agent_dir, avoid_dangerous=False)
        
        if path and len(path) > 1:
            next_x, next_y, next_dir = path[1]
            required_dir = self.get_direction_to_move(agent_x, agent_y, next_x, next_y)
            
            if agent_dir != required_dir:
                return self._get_turn_action(agent_dir, required_dir)
            else:
                return "FORWARD"
        
        for next_dir in DIRECTIONS:
            dx, dy = DX[next_dir], DY[next_dir]
            nx, ny = agent_x + dx, agent_y + dy
            
            if 0 <= nx < self.N and 0 <= ny < self.N and (nx, ny) not in self.kb.visited:
                risk = self.calculate_cell_risk(nx, ny)
                if risk < float('inf'):
                    if agent_dir != next_dir:
                        return self._get_turn_action(agent_dir, next_dir)
                    else:
                        return "FORWARD"
        
        return None
