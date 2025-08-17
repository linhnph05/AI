from const import DIRECTIONS, DX, DY
from collections import deque
from knowledge_base import KnowledgeBase
from inference_engine import InferenceEngine
from planning_module import PlanningModule

class Agent:
    def __init__(self, N, K=2):
        self.N = N
        self.K = K  # Number of wumpuses
        self.wumpuses_killed = 0  # Track killed wumpuses
        self.shoot = False
        self.has_gold = False  

        self.current_x = 0
        self.current_y = 0
        self.current_dir = 'E'
        
        self.kb = KnowledgeBase(N)
        self.inference_engine = InferenceEngine(self.kb)
        self.planning_module = PlanningModule(self.kb, N)
        
        self.score = 0

    def update_position(self, x, y, direction):
        self.current_x = x
        self.current_y = y
        self.current_dir = direction

    def Agent_get_percepts(self, percept):
        x, y = percept["position"]
        direction = percept["direction"]
        
        self.update_position(x, y, direction)
        
        self.kb.visited.add((x, y))

        self.kb.add_fact("Safe", x, y)
        self.kb.add_fact("SafePit", x, y)
        self.kb.add_fact("SafeWumpus", x, y)

        if percept.get("breeze"):
            self.kb.add_fact("Breeze", x, y)
            self.inference_engine.rule_breeze_possible_pit(x, y)
        else:
            self.kb.add_fact("NoBreeze", x, y)
            self.inference_engine.rule_no_breeze(x, y)

        if percept.get("stench"):
            self.kb.add_fact("Stench", x, y)
            self.inference_engine.rule_stench_possible_wumpus(x, y)
        else:
            self.kb.add_fact("NoStench", x, y)
            self.inference_engine.rule_no_stench(x, y)

        if percept.get("glitter"):
            self.kb.add_fact("glitter", x, y)

        if percept.get("scream"):
            self.kb.add_fact("Scream", x, y)
            self.wumpuses_killed += 1
            print(f"Wumpus killed! Total wumpuses killed: {self.wumpuses_killed}/{self.K}")
            
            if self.wumpuses_killed >= self.K:
                print("All wumpuses have been killed! No more wumpus threats.")
                self.kb.add_fact("AllWumpusesKilled")
                self.inference_engine.handle_all_wumpuses_killed()
            
            self.inference_engine.handle_shoot(x, y, direction)

        if percept.get("bump"):
            pass
            
        self.inference_engine.logic_inference_forward_chaining()


    def handle_shoot(self, agent_x, agent_y, agent_dir):
        dx, dy = DX[agent_dir], DY[agent_dir]
        x, y = agent_x + dx, agent_y + dy
        
        while 0 <= x < self.N and 0 <= y < self.N:
            if self.kb.fact_exists("Wumpus", x, y) or self.kb.fact_exists("PossibleWumpus", x, y):
                self.kb.remove_fact("Wumpus", x, y)
                self.kb.remove_fact("PossibleWumpus", x, y)
                self.kb.add_fact("SafeWumpus", x, y)
                
                for nx, ny in self.kb.get_adjacent(x, y):
                    if self.kb.fact_exists("Stench", nx, ny):
                        self.kb.remove_fact("Stench", nx, ny)
                
                break
            x += dx
            y += dy

    def print_agent_map(self, width, height, agent_x, agent_y):
        for y in reversed(range(height)):
            row = []
            for x in range(width):
                cell_symbols = []

                if (x, y) == (agent_x, agent_y):
                    cell_symbols.append("A")
                if self.kb.fact_exists("Safe", x, y):
                    cell_symbols.append("V")
                if self.kb.fact_exists("Pit", x, y):
                    cell_symbols.append("P!")
                if self.kb.fact_exists("Wumpus", x, y):
                    cell_symbols.append("W!")
                if self.kb.fact_exists("PossiblePit", x, y):
                    cell_symbols.append("P?")
                if self.kb.fact_exists("PossibleWumpus", x, y):
                    cell_symbols.append("W?")
                if not cell_symbols:
                    cell_symbols.append(".")

                cell_str = "".join(cell_symbols)
                cell_str = cell_str.ljust(3)
                row.append(cell_str)
            print("".join(row))

    def get_safe_unvisited_neighbors(self, x, y):
        safe_neighbors = []
        for nx, ny in self.kb.get_adjacent(x, y):
            if self.kb.fact_exists("Safe", nx, ny) and (nx, ny) not in self.kb.visited:
                safe_neighbors.append((nx, ny))
        return safe_neighbors

    def find_path_to_target(self, start_x, start_y, target_x, target_y):
        if (target_x, target_y) not in self.kb.visited and not self.kb.fact_exists("Safe", target_x, target_y):
            return None
            
        queue = deque([(start_x, start_y, [])])
        visited = set()
        
        while queue:
            x, y, path = queue.popleft()
            
            if (x, y) in visited:
                continue
            visited.add((x, y))
            
            if x == target_x and y == target_y:
                return path
                
            for nx, ny in self.kb.get_adjacent(x, y):
                if (nx, ny) not in visited and (self.kb.fact_exists("Safe", nx, ny) or (nx, ny) in self.kb.visited):
                    queue.append((nx, ny, path + [(nx, ny)]))
        
        return None

    def should_shoot_wumpus(self, agent_x, agent_y, agent_dir):
        dx, dy = DX[agent_dir], DY[agent_dir]
        x, y = agent_x + dx, agent_y + dy
        
        while 0 <= x < self.N and 0 <= y < self.N:
            if self.kb.fact_exists("Wumpus", x, y):
                return True
            
            if self.kb.fact_exists("Safe", x, y) and (x, y) in self.kb.visited:
                break
            x += dx
            y += dy
        return False

    def grab_gold_action(self):
        x, y = self.current_x, self.current_y
        if self.kb.fact_exists("glitter", x, y):
            print("Gold grabbed!")
            self.has_gold = True
            self.score += 10  
            return True
        else:
            print("No gold to grab here!")
            return False

    def climb_action(self):
        x, y = self.current_x, self.current_y
        if x == 0 and y == 0:
            if self.has_gold:
                self.score += 1000  
                return True
            else:
                self.score += 0  
                return True
        return False
    
    def shoot_action(self):
        if not self.shoot:
            self.shoot = True
            self.score -= 10  
            return True
        return False
    
    def move_forward_action(self):
        self.score -= 1  
    
    def turn_action(self):
        self.score -= 1  
    
    def die_action(self):
        self.score -= 1000  
    
    def currentScore(self):
        return self.score

    def choose_action(self):
        self.inference_engine.logic_inference_forward_chaining()
        
        agent_x, agent_y = self.current_x, self.current_y
        adjacent_info = []
        for direction in DIRECTIONS:
            dx, dy = DX[direction], DY[direction]
            nx, ny = agent_x + dx, agent_y + dy
            if 0 <= nx < self.N and 0 <= ny < self.N:
                status = []
                if self.kb.fact_exists("Safe", nx, ny):
                    status.append("Safe")
                if self.kb.fact_exists("PossiblePit", nx, ny):
                    status.append("P?")
                if self.kb.fact_exists("PossibleWumpus", nx, ny):
                    status.append("W?")
                if self.kb.fact_exists("Pit", nx, ny):
                    status.append("PIT!")
                if self.kb.fact_exists("Wumpus", nx, ny):
                    status.append("WUMPUS!")
                if (nx, ny) in self.kb.visited:
                    status.append("Visited")
                if not status:
                    status.append("Unknown")
                
                adjacent_info.append(f"{direction}:({nx},{ny})={'/'.join(status)}")
        
        print(f"Adjacent cells: {' | '.join(adjacent_info)}")
        
        current_score = self.currentScore()
        action = self.planning_module.plan_optimal_action(
            self.current_x, self.current_y, self.current_dir, 
            self.has_gold, self.shoot, current_score
        )
        
        current_score = self.currentScore()
        score_change = ""
        if action == "FORWARD":
            score_change = " (-1)"
        elif action in ["LEFT", "RIGHT"]:
            score_change = " (-1)"
        elif action == "SHOOT":
            score_change = " (-10)"
        elif action == "GRAB":
            score_change = " (+10)"
        elif action == "CLIMB":
            score_change = f" ({'+1000' if self.has_gold else '+0'})"
        
        print(f"Action: {action}{score_change} | Score: {current_score} | Gold: {self.has_gold} | Pos: ({self.current_x},{self.current_y})")
        
        return action
