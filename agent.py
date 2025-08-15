from const import DIRECTIONS, DX, DY
from collections import deque
from knowledge_base import KnowledgeBase
from inference_engine import InferenceEngine
from planning_module import PlanningModule

class Agent:
    def __init__(self, N):
        self.N = N
        self.shoot = False
        self.has_gold = False  

        # Agent's own tracking of position and direction
        self.current_x = 0
        self.current_y = 0
        self.current_dir = 'E'
        
        # Initialize knowledge base, inference engine, and planning module
        self.kb = KnowledgeBase(N)
        self.inference_engine = InferenceEngine(self.kb)
        self.planning_module = PlanningModule(self.kb, N)
        
        # Score tracking
        self.score = 0

    def update_position(self, x, y, direction):
        """Update agent's internal position and direction tracking."""
        self.current_x = x
        self.current_y = y
        self.current_dir = direction

    # === receive percepts ===
    def Agent_get_percepts(self, percept):
        x, y = percept["position"]
        direction = percept["direction"]
        
        # Update agent's own position tracking
        self.update_position(x, y, direction)
        
        self.kb.visited.add((x, y))

        # current cell is definitely safe
        self.kb.add_fact("Safe", x, y)
        self.kb.add_fact("SafePit", x, y)
        self.kb.add_fact("SafeWumpus", x, y)

        # breeze / nobreeze
        if percept.get("breeze"):
            self.kb.add_fact("Breeze", x, y)
            self.inference_engine.rule_breeze_possible_pit(x, y)
        else:
            self.kb.add_fact("NoBreeze", x, y)
            self.inference_engine.rule_no_breeze(x, y)

        # stench / nostench
        if percept.get("stench"):
            self.kb.add_fact("Stench", x, y)
            self.inference_engine.rule_stench_possible_wumpus(x, y)
        else:
            self.kb.add_fact("NoStench", x, y)
            self.inference_engine.rule_no_stench(x, y)

        # glitter
        if percept.get("glitter"):
            self.kb.add_fact("glitter", x, y)

        # scream
        if percept.get("scream"):
            self.kb.add_fact("Scream", x, y)
            self.inference_engine.handle_shoot(x, y, direction)

        # Bump - no score penalty here, handled in main loop
        if percept.get("bump"):
            pass
            
        # Run forward chaining inference after receiving new percepts
        self.inference_engine.logic_inference_forward_chaining()


    def handle_shoot(self, agent_x, agent_y, agent_dir):
        dx, dy = DX[agent_dir], DY[agent_dir]
        x, y = agent_x + dx, agent_y + dy
        
        while 0 <= x < self.N and 0 <= y < self.N:
            # if facts contain PossibleWumpus or Wumpus then remove it
            if self.kb.fact_exists("Wumpus", x, y) or self.kb.fact_exists("PossibleWumpus", x, y):
                # Remove wumpus facts
                self.kb.remove_fact("Wumpus", x, y)
                self.kb.remove_fact("PossibleWumpus", x, y)
                self.kb.add_fact("SafeWumpus", x, y)
                
                for nx, ny in self.kb.get_adjacent(x, y):
                    # Remove stench facts that might have been caused by this wumpus
                    # Note: This is a simplification - in reality we'd need to check if other wumpuses 
                    # are causing stench in these cells, but for now we'll let the agent re-discover
                    if self.kb.fact_exists("Stench", nx, ny):
                        self.kb.remove_fact("Stench", nx, ny)
                        # The agent will re-perceive the correct stench status when visiting these cells
                
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

                # Connect symbols, then pad to 3 characters (by adding spaces)
                cell_str = "".join(cell_symbols)
                cell_str = cell_str.ljust(3)  # left align, pad to 3 characters
                row.append(cell_str)
            print("".join(row))  # print entire row, each cell 3 characters

    def get_safe_unvisited_neighbors(self, x, y):
        """Get safe adjacent cells that haven't been visited yet."""
        safe_neighbors = []
        for nx, ny in self.kb.get_adjacent(x, y):
            if self.kb.fact_exists("Safe", nx, ny) and (nx, ny) not in self.kb.visited:
                safe_neighbors.append((nx, ny))
        return safe_neighbors

    def find_path_to_target(self, start_x, start_y, target_x, target_y):
        """Find path from start to target using only safe cells."""
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
        """Check if there's a confirmed wumpus in the shooting direction."""
        dx, dy = DX[agent_dir], DY[agent_dir]
        x, y = agent_x + dx, agent_y + dy
        
        while 0 <= x < self.N and 0 <= y < self.N:
            if self.kb.fact_exists("Wumpus", x, y):
                return True
            # Stop if we hit a wall or safe cell that blocks the shot
            if self.kb.fact_exists("Safe", x, y) and (x, y) in self.kb.visited:
                break
            x += dx
            y += dy
        return False

    def grab_gold_action(self):
        """Handle gold grabbing action."""
        x, y = self.current_x, self.current_y
        if self.kb.fact_exists("glitter", x, y):
            print("💰 Gold grabbed!")
            self.has_gold = True
            self.score += 10  # Grab gold +10
            return True
        else:
            print("❌ No gold to grab here!")
            return False

    def climb_action(self):
        """Handle climb action."""
        x, y = self.current_x, self.current_y
        if x == 0 and y == 0:
            if self.has_gold:
                self.score += 1000  # Climb out with gold +1000
                return True
            else:
                self.score += 0  # Climb out without gold +0
                return True
        return False
    
    def shoot_action(self):
        """Handle shooting action."""
        if not self.shoot:
            self.shoot = True
            self.score -= 10  # Shoot -10
            return True
        return False
    
    def move_forward_action(self):
        """Handle move forward action scoring."""
        self.score -= 1  # Move forward -1
    
    def turn_action(self):
        """Handle turn action scoring."""
        self.score -= 1  # Turn left/right -1
    
    def die_action(self):
        """Handle death action scoring."""
        self.score -= 1000  # Die -1000
    
    def calculate_current_score(self):
        """Calculate current score based on all scoring rules."""
        return self.score

    def choose_action(self):
        """
        Hybrid autonomous decision making combining logic inference and planning.
        Uses planning module for optimal path finding and utility-based decisions.
        """
        # Run inference first to update knowledge
        self.inference_engine.logic_inference_forward_chaining()
        
        # Print current knowledge state for debugging
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
        
        print(f"🧭 Adjacent cells: {' | '.join(adjacent_info)}")
        
        # Use planning module for optimal action selection
        current_score = self.calculate_current_score()
        action = self.planning_module.plan_optimal_action(
            self.current_x, self.current_y, self.current_dir, 
            self.has_gold, self.shoot, current_score
        )
        
        # Print decision rationale for debugging
        if action != "QUIT":
            current_score = self.calculate_current_score()
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
            
            print(f"🤖 Action: {action}{score_change} | Score: {current_score} | Gold: {self.has_gold} | Pos: ({self.current_x},{self.current_y})")
        
        return action
