from const import DIRECTIONS, DX, DY
from agent import Agent

class AdaptiveAgent(Agent):
    
    def __init__(self, N, K=2):
        super().__init__(N, K)
        
        self.last_action_count = 0
        self.outdated_wumpus_knowledge = set()
        self.movement_phases = 0
        
        print("- Adaptive Agent initialized for Moving Wumpus environment")
        print("+ Enhanced knowledge management for dynamic threats")
        print("+ Increased caution and safety margins")
        print("+ Continuous belief updating capabilities")
    
    def handle_wumpus_movement_phase(self, current_action_count):
        if current_action_count > self.last_action_count and current_action_count % 5 == 0:
            self.movement_phases += 1
            self.last_action_count = current_action_count
            
            print(f"ADAPTIVE AGENT: Detected Wumpus movement phase #{self.movement_phases}")
            
            self.mark_wumpus_knowledge_outdated()

            self.clear_outdated_wumpus_facts()
            
            self.reevaluate_environment_knowledge()
            
            return True
        return False
    
    def mark_wumpus_knowledge_outdated(self):
        for x in range(self.N):
            for y in range(self.N):
                if (self.kb.fact_exists("Wumpus", x, y) or 
                    self.kb.fact_exists("PossibleWumpus", x, y)):
                    self.outdated_wumpus_knowledge.add((x, y))
        
        print(f"Marked {len(self.outdated_wumpus_knowledge)} cells with outdated wumpus knowledge")

    def clear_outdated_wumpus_facts(self):
        cleared_count = 0
        
        for x, y in list(self.outdated_wumpus_knowledge):
            if not self.has_recent_wumpus_evidence(x, y):
                if self.kb.remove_fact("PossibleWumpus", x, y):
                    cleared_count += 1
                
        print(f"Cleared {cleared_count} outdated possible wumpus facts")
    
    def has_recent_wumpus_evidence(self, x, y):
        for nx, ny in self.kb.get_adjacent(x, y):
            if (nx, ny) in self.kb.visited:
                if self.kb.fact_exists("Stench", nx, ny):
                    return True
        return False
    
    def reevaluate_environment_knowledge(self):
        print("Re-evaluating environment knowledge...")
        
        self.inference_engine.logic_inference_forward_chaining()
        
    
    def Agent_get_percepts(self, percept):
        x, y = percept["position"]
        
        super().Agent_get_percepts(percept)
        
        self.check_for_contradictions(x, y, percept)
        
        self.resolve_knowledge_conflicts(x, y, percept)
        
        if (x, y) in self.outdated_wumpus_knowledge:
            self.outdated_wumpus_knowledge.remove((x, y))
            print(f"Updated knowledge for cell ({x},{y}) with fresh percepts")
    
    def check_for_contradictions(self, x, y, percept):
        contradictions = []
        
        if percept.get("stench"):
            adjacent_safe_wumpus = 0
            for nx, ny in self.kb.get_adjacent(x, y):
                if self.kb.fact_exists("SafeWumpus", nx, ny):
                    adjacent_safe_wumpus += 1
            
            if adjacent_safe_wumpus == len(self.kb.get_adjacent(x, y)):
                contradictions.append("stench_vs_safe_wumpus")
        
        if contradictions:
            print(f"Detected contradictions at ({x},{y}): {contradictions}")
            self.resolve_contradictions(x, y, contradictions)
    
    def resolve_contradictions(self, x, y, contradictions):
        for contradiction in contradictions:
            if contradiction == "stench_vs_safe_wumpus":
                print(f"Resolving stench contradiction - wumpus may have moved")
                for nx, ny in self.kb.get_adjacent(x, y):
                    if self.kb.remove_fact("SafeWumpus", nx, ny):
                        self.kb.add_fact("PossibleWumpus", nx, ny)
                        print(f"Updated ({nx},{ny}) from SafeWumpus to PossibleWumpus")
    
    def resolve_knowledge_conflicts(self, x, y, percept):
        if not percept.get("stench"):
            for nx, ny in self.kb.get_adjacent(x, y):
                if self.kb.fact_exists("PossibleWumpus", nx, ny):
                    if (nx, ny) in self.outdated_wumpus_knowledge:
                        self.kb.remove_fact("PossibleWumpus", nx, ny)
                        self.kb.add_fact("SafeWumpus", nx, ny)
                        print(f"   Fresh no-stench confirms ({nx},{ny}) is SafeWumpus")
    
    def choose_action(self):
        self.inference_engine.logic_inference_forward_chaining()
        
        agent_x, agent_y = self.current_x, self.current_y
        self.print_enhanced_status(agent_x, agent_y)
        
        current_score = self.currentScore()
        action = self.planning_module.plan_optimal_action(
            self.current_x, self.current_y, self.current_dir, 
            self.has_gold, self.shoot, current_score
        )
        
        action = self.apply_dynamic_caution(action, agent_x, agent_y)
        
        return action
    
    def print_enhanced_status(self, agent_x, agent_y):
        adjacent_info = []
        uncertain_cells = 0
        
        for direction in DIRECTIONS:
            dx, dy = DX[direction], DY[direction]
            nx, ny = agent_x + dx, agent_y + dy
            if 0 <= nx < self.N and 0 <= ny < self.N:
                status = []
                if self.kb.fact_exists("Safe", nx, ny):
                    status.append("Safe")
                if self.kb.fact_exists("PossiblePit", nx, ny):
                    status.append("?Pit")
                if self.kb.fact_exists("PossibleWumpus", nx, ny):
                    status.append("?Wumpus")
                    if (nx, ny) in self.outdated_wumpus_knowledge:
                        status.append("(Outdated)")
                        uncertain_cells += 1
                
                if not status:
                    status.append("Unknown")
                
                adjacent_info.append(f"{direction}:{','.join(status)}")
        
        print(f"Adjacent: {' | '.join(adjacent_info)}")
        print(f"Movement phases: {self.movement_phases} | Uncertain cells: {uncertain_cells}")
    
    def apply_dynamic_caution(self, action, agent_x, agent_y):
        if action == "FORWARD":
            dx, dy = DX[self.current_dir], DY[self.current_dir]
            next_x, next_y = agent_x + dx, agent_y + dy
            
            if (0 <= next_x < self.N and 0 <= next_y < self.N and 
                (next_x, next_y) in self.outdated_wumpus_knowledge):
                
                print(f"   CAUTION: Target cell ({next_x},{next_y}) has uncertain wumpus knowledge")
                
                safe_alternatives = self.get_safe_movement_alternatives(agent_x, agent_y)
                if safe_alternatives:
                    print(f"   Switching to safer alternative action")
                    return safe_alternatives[0]
        
        return action
    
    def get_safe_movement_alternatives(self, agent_x, agent_y):
        alternatives = []
        
        alternatives.extend(["LEFT", "RIGHT"])
        
        for direction in DIRECTIONS:
            if direction != self.current_dir:
                dx, dy = DX[direction], DY[direction]
                nx, ny = agent_x + dx, agent_y + dy
                if (0 <= nx < self.N and 0 <= ny < self.N and 
                    self.kb.fact_exists("Safe", nx, ny) and
                    (nx, ny) not in self.outdated_wumpus_knowledge):
                    alternatives.insert(0, "LEFT" if self.get_turn_direction(direction) == "LEFT" else "RIGHT")
                    break
        
        return alternatives
    
    def get_turn_direction(self, target_direction):
        current_idx = DIRECTIONS.index(self.current_dir)
        target_idx = DIRECTIONS.index(target_direction)
        
        diff = (target_idx - current_idx) % 4
        return "LEFT" if diff == 3 or diff == -1 else "RIGHT"
    
    def print_agent_map(self, width, height, agent_x, agent_y):
        print("Adaptive Agent Knowledge Map:")
        for y in reversed(range(height)):
            row = []
            for x in range(width):
                cell_symbols = []

                if (x, y) == (agent_x, agent_y):
                    cell_symbols.append("A")
                elif self.kb.fact_exists("Safe", x, y):
                    cell_symbols.append("S")
                elif self.kb.fact_exists("Pit", x, y):
                    cell_symbols.append("P")
                elif self.kb.fact_exists("Wumpus", x, y):
                    cell_symbols.append("W")
                elif self.kb.fact_exists("PossiblePit", x, y):
                    cell_symbols.append("p")
                elif self.kb.fact_exists("PossibleWumpus", x, y):
                    if (x, y) in self.outdated_wumpus_knowledge:
                        cell_symbols.append("w?")
                    else:
                        cell_symbols.append("w")
                else:
                    cell_symbols.append(".")

                if self.kb.fact_exists("glitter", x, y):
                    cell_symbols.append("G")

                cell_str = "".join(cell_symbols)
                cell_str = cell_str.ljust(3)
                row.append(cell_str)
            print("".join(row))
        
        print(f"Remember: A=Agent, S=Safe, P=Pit, W=Wumpus, p=?Pit, w=?Wumpus, w?=Uncertain Wumpus, G=Gold")
        print(f"Visited: {len(self.kb.visited)}, Uncertain: {len(self.outdated_wumpus_knowledge)}, Movements: {self.movement_phases}")
