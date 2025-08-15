import random
from const import DIRECTIONS, DX, DY

class RandomAgent:
    """
    Random Agent Baseline for Wumpus World.
    This agent makes completely random decisions for comparison purposes.
    """
    
    def __init__(self, N):
        self.N = N
        self.shoot = False
        self.has_gold = False
        
        # Track position and direction
        self.current_x = 0
        self.current_y = 0
        self.current_dir = 'E'
        
        # Score tracking (same as intelligent agent)
        self.score = 0
        
        # Track visited cells for basic memory
        self.visited = set()
        self.visited.add((0, 0))
        
        # Available actions
        self.actions = ["FORWARD", "LEFT", "RIGHT", "SHOOT", "GRAB", "CLIMB"]
        
    def update_position(self, x, y, direction):
        """Update agent's internal position and direction tracking."""
        self.current_x = x
        self.current_y = y
        self.current_dir = direction
        self.visited.add((x, y))
    
    def Agent_get_percepts(self, percept):
        """Process percepts from environment - minimal processing for random agent."""
        x, y = percept["position"]
        direction = percept["direction"]
        
        # Update position tracking
        self.update_position(x, y, direction)
        
        # Store percepts but don't act on them intelligently
        # Random agent ignores most percepts for true randomness
        self.last_percepts = percept
    
    def grab_gold_action(self):
        """Handle gold grabbing action - random agent attempts randomly."""
        # Random agent doesn't check for glitter intelligently
        # It just tries to grab and sees what happens
        x, y = self.current_x, self.current_y
        if hasattr(self, 'last_percepts') and self.last_percepts.get("glitter"):
            print("💰 Random agent randomly grabbed gold!")
            self.has_gold = True
            self.score += 10  # Grab gold +10
            return True
        else:
            print("🎲 Random agent tried to grab gold but nothing here")
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
        """Calculate current score."""
        return self.score
    
    def should_quit(self):
        """
        Random agent occasionally quits to prevent infinite loops.
        This makes it a more realistic baseline for comparison.
        """
        # 1% chance to quit each turn after visiting some cells
        if len(self.visited) > 10:
            return random.random() < 0.01
        return False

    def choose_action(self):
        """
        Pure random action selection for baseline comparison.
        This agent makes completely random decisions to serve as a control.
        """
        
        # Occasionally quit to prevent infinite exploration
        if self.should_quit():
            return "QUIT"
        
        # Build list of available actions
        available_actions = ["FORWARD", "LEFT", "RIGHT"]
        
        # Allow shooting once
        if not self.shoot:
            available_actions.append("SHOOT")
        
        # Always allow grabbing and climbing (agent doesn't know if valid)
        available_actions.extend(["GRAB", "CLIMB"])
        
        # Pure random selection - no intelligence or preferences
        action = random.choice(available_actions)
        
        # Print decision for debugging (with minimal logic explanation)
        print(f"🎲 Random agent chooses: {action}")
        
        return action
    
    def print_agent_map(self, width, height, agent_x, agent_y):
        """
        Print a simple map showing only visited cells and agent position.
        Random agent has no knowledge about dangers.
        """
        print("Random Agent Map (V=Visited, A=Agent, .=Unknown):")
        for y in reversed(range(height)):
            row = []
            for x in range(width):
                if (x, y) == (agent_x, agent_y):
                    cell_str = " A "
                elif (x, y) in self.visited:
                    cell_str = " V "
                else:
                    cell_str = " . "
                row.append(cell_str)
            print("".join(row))
        print(f"Visited: {len(self.visited)} cells")
