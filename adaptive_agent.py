from const import DIRECTIONS, DX, DY
from collections import deque
from agent import Agent
from knowledge_base import KnowledgeBase
from inference_engine import InferenceEngine
from planning_module import PlanningModule

class AdaptiveAgent(Agent):
    """
    Enhanced agent designed specifically for Moving Wumpus environments.
    Features dynamic knowledge management and cautious planning.
    """
    
    def __init__(self, N):
        super().__init__(N)
        
        # Additional tracking for dynamic environment
        self.last_action_count = 0  # Track when wumpuses last moved
        self.wumpus_movement_history = []  # Track wumpus movement events
        self.outdated_wumpus_knowledge = set()  # Cells with potentially outdated wumpus info
        self.confidence_decay_factor = 0.8  # How much to reduce confidence after movement
        self.movement_phases = 0  # Number of wumpus movement phases experienced
        
        # Enhanced caution parameters
        self.safety_margin = 2  # Extra safety distance from suspected dangers
        self.exploration_threshold = 0.7  # Confidence threshold for exploration
        
        print("🧠 Adaptive Agent initialized for Moving Wumpus environment")
        print("   • Enhanced knowledge management for dynamic threats")
        print("   • Increased caution and safety margins")
        print("   • Continuous belief updating capabilities")
    
    def handle_wumpus_movement_phase(self, current_action_count):
        """Handle the aftermath of a wumpus movement phase."""
        if current_action_count > self.last_action_count and current_action_count % 5 == 0:
            self.movement_phases += 1
            self.last_action_count = current_action_count
            
            print(f"🚨 ADAPTIVE AGENT: Detected Wumpus movement phase #{self.movement_phases}")
            
            # Mark all previous wumpus knowledge as potentially outdated
            self.mark_wumpus_knowledge_outdated()
            
            # Increase caution level
            self.adjust_caution_level()
            
            # Clear outdated possible wumpus locations
            self.clear_outdated_wumpus_facts()
            
            # Re-evaluate all cells based on fresh percepts
            self.reevaluate_environment_knowledge()
            
            return True
        return False
    
    def mark_wumpus_knowledge_outdated(self):
        """Mark all existing wumpus knowledge as potentially outdated."""
        # Find all cells with wumpus-related knowledge
        for x in range(self.N):
            for y in range(self.N):
                if (self.kb.fact_exists("Wumpus", x, y) or 
                    self.kb.fact_exists("PossibleWumpus", x, y)):
                    self.outdated_wumpus_knowledge.add((x, y))
        
        print(f"   📝 Marked {len(self.outdated_wumpus_knowledge)} cells with outdated wumpus knowledge")
    
    def adjust_caution_level(self):
        """Increase caution level after wumpus movement."""
        # Reduce confidence in existing knowledge
        self.exploration_threshold = min(0.9, self.exploration_threshold + 0.05)
        self.safety_margin = min(3, self.safety_margin + 0.2)
        
        print(f"   ⚠️  Increased caution: threshold={self.exploration_threshold:.2f}, margin={self.safety_margin:.1f}")
    
    def clear_outdated_wumpus_facts(self):
        """Remove potentially outdated wumpus facts that aren't confirmed by recent percepts."""
        cleared_count = 0
        
        # Remove PossibleWumpus facts from cells not recently confirmed
        for x, y in list(self.outdated_wumpus_knowledge):
            # Only keep wumpus knowledge if we have recent confirming evidence
            if not self.has_recent_wumpus_evidence(x, y):
                if self.kb.remove_fact("PossibleWumpus", x, y):
                    cleared_count += 1
                # Don't remove confirmed Wumpus facts, but mark them as uncertain
                
        print(f"   🗑️  Cleared {cleared_count} outdated possible wumpus facts")
    
    def has_recent_wumpus_evidence(self, x, y):
        """Check if we have recent evidence for wumpus at this location."""
        # Check if any adjacent cell has recent stench
        for nx, ny in self.kb.get_adjacent(x, y):
            if (nx, ny) in self.kb.visited:
                # If we've been to adjacent cell recently and detected stench
                if self.kb.fact_exists("Stench", nx, ny):
                    return True
        return False
    
    def reevaluate_environment_knowledge(self):
        """Re-evaluate environment knowledge after wumpus movement."""
        print("   🔄 Re-evaluating environment knowledge...")
        
        # Run enhanced inference to update beliefs
        self.inference_engine.logic_inference_forward_chaining()
        
        # Apply dynamic knowledge decay
        self.apply_knowledge_decay()
        
        # Update exploration priorities
        self.update_exploration_priorities()
    
    def apply_knowledge_decay(self):
        """Apply confidence decay to knowledge that may be outdated."""
        # This is a conceptual implementation - in practice you might use
        # probability weights or certainty factors
        decay_applied = 0
        
        for x, y in self.outdated_wumpus_knowledge:
            # Don't decay knowledge of visited safe cells
            if (x, y) not in self.kb.visited:
                # For now, we'll keep the binary logic but mark uncertainty
                if self.kb.fact_exists("PossibleWumpus", x, y):
                    # Could implement probabilistic reasoning here
                    decay_applied += 1
        
        if decay_applied > 0:
            print(f"   📉 Applied uncertainty decay to {decay_applied} cells")
    
    def update_exploration_priorities(self):
        """Update exploration priorities based on current knowledge confidence."""
        # Prioritize cells with fresh, confident knowledge
        # Avoid cells with uncertain or outdated threat information
        safe_cells = 0
        uncertain_cells = 0
        
        for x in range(self.N):
            for y in range(self.N):
                if (x, y) not in self.kb.visited:
                    if self.kb.fact_exists("Safe", x, y):
                        safe_cells += 1
                    elif (x, y) in self.outdated_wumpus_knowledge:
                        uncertain_cells += 1
        
        print(f"   🎯 Exploration update: {safe_cells} safe cells, {uncertain_cells} uncertain cells")
    
    def Agent_get_percepts(self, percept):
        """Enhanced percept processing for dynamic environment."""
        x, y = percept["position"]
        
        # Call parent method for basic processing
        super().Agent_get_percepts(percept)
        
        # Check if we're getting contradictory information
        self.check_for_contradictions(x, y, percept)
        
        # If we detect fresh percepts that contradict old knowledge, update accordingly
        self.resolve_knowledge_conflicts(x, y, percept)
        
        # Clear outdated knowledge for this cell
        if (x, y) in self.outdated_wumpus_knowledge:
            self.outdated_wumpus_knowledge.remove((x, y))
            print(f"   ✅ Updated knowledge for cell ({x},{y}) with fresh percepts")
    
    def check_for_contradictions(self, x, y, percept):
        """Check for contradictions between new percepts and existing knowledge."""
        contradictions = []
        
        # Check stench vs wumpus knowledge
        if percept.get("stench"):
            # We smell stench, but do we have SafeWumpus facts for adjacent cells?
            adjacent_safe_wumpus = 0
            for nx, ny in self.kb.get_adjacent(x, y):
                if self.kb.fact_exists("SafeWumpus", nx, ny):
                    adjacent_safe_wumpus += 1
            
            if adjacent_safe_wumpus == len(self.kb.get_adjacent(x, y)):
                contradictions.append("stench_vs_safe_wumpus")
        
        if contradictions:
            print(f"   ⚠️  Detected contradictions at ({x},{y}): {contradictions}")
            self.resolve_contradictions(x, y, contradictions)
    
    def resolve_contradictions(self, x, y, contradictions):
        """Resolve knowledge contradictions by favoring fresh percepts."""
        for contradiction in contradictions:
            if contradiction == "stench_vs_safe_wumpus":
                print(f"   🔧 Resolving stench contradiction - wumpus may have moved")
                # Remove SafeWumpus facts for adjacent cells (wumpus may have moved here)
                for nx, ny in self.kb.get_adjacent(x, y):
                    if self.kb.remove_fact("SafeWumpus", nx, ny):
                        self.kb.add_fact("PossibleWumpus", nx, ny)
                        print(f"      📝 Updated ({nx},{ny}) from SafeWumpus to PossibleWumpus")
    
    def resolve_knowledge_conflicts(self, x, y, percept):
        """Resolve conflicts between new percepts and existing knowledge."""
        # Trust fresh percepts over potentially outdated knowledge
        
        if not percept.get("stench"):
            # No stench means adjacent cells are safe from wumpus
            for nx, ny in self.kb.get_adjacent(x, y):
                if self.kb.fact_exists("PossibleWumpus", nx, ny):
                    if (nx, ny) in self.outdated_wumpus_knowledge:
                        self.kb.remove_fact("PossibleWumpus", nx, ny)
                        self.kb.add_fact("SafeWumpus", nx, ny)
                        print(f"   ✅ Fresh no-stench confirms ({nx},{ny}) is SafeWumpus")
    
    def choose_action(self):
        """Enhanced action selection with dynamic environment awareness."""
        # Run inference first to update knowledge
        self.inference_engine.logic_inference_forward_chaining()
        
        # Check for wumpus movement (if we have access to action count)
        # This would be called from the main loop with action count info
        
        # Print enhanced knowledge state
        agent_x, agent_y = self.current_x, self.current_y
        self.print_enhanced_status(agent_x, agent_y)
        
        # Use planning module with enhanced caution
        current_score = self.calculate_current_score()
        action = self.planning_module.plan_optimal_action(
            self.current_x, self.current_y, self.current_dir, 
            self.has_gold, self.shoot, current_score
        )
        
        # Apply additional caution for dynamic environment
        action = self.apply_dynamic_caution(action, agent_x, agent_y)
        
        # Print decision rationale
        self.print_action_rationale(action, agent_x, agent_y)
        
        return action
    
    def print_enhanced_status(self, agent_x, agent_y):
        """Print enhanced status information for dynamic environment."""
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
        
        print(f"🧭 Adjacent: {' | '.join(adjacent_info)}")
        print(f"🕐 Movement phases: {self.movement_phases} | Uncertain cells: {uncertain_cells}")
        print(f"⚠️  Caution level: {self.exploration_threshold:.2f} | Safety margin: {self.safety_margin:.1f}")
    
    def apply_dynamic_caution(self, action, agent_x, agent_y):
        """Apply additional caution for dynamic environment."""
        if action == "FORWARD":
            dx, dy = DX[self.current_dir], DY[self.current_dir]
            next_x, next_y = agent_x + dx, agent_y + dy
            
            # Check if target cell has uncertain wumpus knowledge
            if (0 <= next_x < self.N and 0 <= next_y < self.N and 
                (next_x, next_y) in self.outdated_wumpus_knowledge):
                
                print(f"   ⚠️  CAUTION: Target cell ({next_x},{next_y}) has uncertain wumpus knowledge")
                
                # If we have safe alternatives, prefer them
                safe_alternatives = self.get_safe_movement_alternatives(agent_x, agent_y)
                if safe_alternatives:
                    print(f"   🔄 Switching to safer alternative action")
                    return safe_alternatives[0]  # Take first safe alternative
        
        return action
    
    def get_safe_movement_alternatives(self, agent_x, agent_y):
        """Get safe movement alternatives when forward movement is uncertain."""
        alternatives = []
        
        # Check turning as safe alternatives
        alternatives.extend(["LEFT", "RIGHT"])
        
        # Check if we can move in other directions after turning
        for direction in DIRECTIONS:
            if direction != self.current_dir:
                dx, dy = DX[direction], DY[direction]
                nx, ny = agent_x + dx, agent_y + dy
                if (0 <= nx < self.N and 0 <= ny < self.N and 
                    self.kb.fact_exists("Safe", nx, ny) and
                    (nx, ny) not in self.outdated_wumpus_knowledge):
                    # This is a safe direction - we'd need to turn to go there
                    alternatives.insert(0, "LEFT" if self.get_turn_direction(direction) == "LEFT" else "RIGHT")
                    break
        
        return alternatives
    
    def get_turn_direction(self, target_direction):
        """Get which way to turn to face target direction."""
        current_idx = DIRECTIONS.index(self.current_dir)
        target_idx = DIRECTIONS.index(target_direction)
        
        # Calculate turn direction
        diff = (target_idx - current_idx) % 4
        return "LEFT" if diff == 3 or diff == -1 else "RIGHT"
    
    def print_action_rationale(self, action, agent_x, agent_y):
        """Print reasoning behind action choice in dynamic environment."""
        current_score = self.calculate_current_score()
        uncertainty_level = len(self.outdated_wumpus_knowledge)
        
        rationale = []
        if uncertainty_level > 0:
            rationale.append(f"uncertainty:{uncertainty_level}")
        if self.movement_phases > 0:
            rationale.append(f"movements:{self.movement_phases}")
        
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
            score_change = " (+1000)"
        
        rationale_str = f" [{','.join(rationale)}]" if rationale else ""
        print(f"🤖 ADAPTIVE: {action}{score_change} | Score: {current_score} | Gold: {self.has_gold}{rationale_str}")
    
    def print_agent_map(self, width, height, agent_x, agent_y):
        """Enhanced map printing with uncertainty indicators."""
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
                        cell_symbols.append("w?")  # Uncertain wumpus
                    else:
                        cell_symbols.append("w")
                else:
                    cell_symbols.append(".")

                # Add gold indicator
                if self.kb.fact_exists("glitter", x, y):
                    cell_symbols.append("G")

                # Format cell display
                cell_str = "".join(cell_symbols)
                cell_str = cell_str.ljust(3)  # Pad to 3 characters
                row.append(cell_str)
            print("".join(row))
        
        print(f"Legend: A=Agent, S=Safe, P=Pit, W=Wumpus, p=?Pit, w=?Wumpus, w?=Uncertain Wumpus, G=Gold")
        print(f"Visited: {len(self.kb.visited)}, Uncertain: {len(self.outdated_wumpus_knowledge)}, Movements: {self.movement_phases}")
