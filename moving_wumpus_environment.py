import random
from const import DIRECTIONS, DX, DY
from environment import Environment, Cell

class MovingWumpusEnvironment(Environment):
    """
    Extended Environment with Moving Wumpus capability.
    Wumpuses move every 5 agent actions according to specified rules.
    """
    
    def __init__(self, N=8, K=2, p=0.2):
        super().__init__(N, K, p)
        self.action_count = 0  # Track total agent actions
        self.wumpus_locations = []  # Track all wumpus positions
        
        # Initialize wumpus locations
        self.update_wumpus_locations()
        
        print(f"🐺 Moving Wumpus Environment Initialized:")
        print(f"   • Wumpuses move every 5 agent actions")
        print(f"   • Current Wumpus locations: {self.wumpus_locations}")
    
    def update_wumpus_locations(self):
        """Update the list of current wumpus locations."""
        self.wumpus_locations = []
        for y in range(self.N):
            for x in range(self.N):
                if self.grid[y][x].wumpus:
                    self.wumpus_locations.append((x, y))
    
    def increment_action_count(self):
        """Increment action count and trigger wumpus movement if needed."""
        self.action_count += 1
        print(f"📊 Action count: {self.action_count}")
        
        if self.action_count % 5 == 0:
            print(f"\n🚨 WUMPUS MOVEMENT PHASE (after {self.action_count} actions)")
            self.move_all_wumpuses()
            return True  # Indicate that wumpuses moved
        return False
    
    def get_valid_wumpus_moves(self, wx, wy):
        """Get valid adjacent cells for wumpus movement."""
        valid_moves = [(wx, wy)]  # Can stay in place if no valid moves
        
        for direction in ['N', 'E', 'S', 'W']:
            nx, ny = wx + DX[direction], wy + DY[direction]
            
            # Check bounds
            if not (0 <= nx < self.N and 0 <= ny < self.N):
                continue
            
            # Check for pit (wumpus can't enter pit)
            if self.grid[ny][nx].pit:
                continue
            
            # Check for other wumpus (can't overlap)
            if any((nx, ny) == (ox, oy) for (ox, oy) in self.wumpus_locations if (ox, oy) != (wx, wy)):
                continue
            
            valid_moves.append((nx, ny))
        
        return valid_moves
    
    def move_single_wumpus(self, wx, wy):
        """Move a single wumpus according to movement rules."""
        valid_moves = self.get_valid_wumpus_moves(wx, wy)
        new_x, new_y = random.choice(valid_moves)
        
        if (new_x, new_y) != (wx, wy):
            # Remove wumpus from old location
            self.grid[wy][wx].wumpus = False
            # Place wumpus in new location
            self.grid[new_y][new_x].wumpus = True
            print(f"   🐺 Wumpus moved from ({wx},{wy}) to ({new_x},{new_y})")
        else:
            print(f"   🐺 Wumpus at ({wx},{wy}) stayed in place")
        
        return new_x, new_y
    
    def move_all_wumpuses(self):
        """Move all wumpuses and check for agent collision."""
        old_locations = self.wumpus_locations.copy()
        new_locations = []
        
        for wx, wy in old_locations:
            new_x, new_y = self.move_single_wumpus(wx, wy)
            new_locations.append((new_x, new_y))
        
        # Update wumpus locations
        self.wumpus_locations = new_locations
        
        # Check for agent-wumpus collision
        agent_pos = (self.agent_x, self.agent_y)
        if agent_pos in self.wumpus_locations:
            print(f"💀 COLLISION! Wumpus moved into agent's cell {agent_pos}")
            return True  # Collision occurred
        
        print(f"   🗺️  New Wumpus locations: {self.wumpus_locations}")
        return False  # No collision
    
    def move_forward(self):
        """Override move_forward to include action counting and wumpus movement."""
        # Execute normal movement
        died, bump = super().move_forward()
        
        # Check for collision with existing wumpus first
        if died:
            return died, bump
        
        # Increment action count and potentially move wumpuses
        wumpus_moved = self.increment_action_count()
        
        # If wumpuses moved, check for collision
        if wumpus_moved:
            collision = self.check_wumpus_collision()
            if collision:
                return True, bump  # Agent died from wumpus collision
        
        return died, bump
    
    def turn_left(self):
        """Override turn_left to include action counting and wumpus movement."""
        super().turn_left()
        wumpus_moved = self.increment_action_count()
        
        if wumpus_moved:
            collision = self.check_wumpus_collision()
            if collision:
                print("💀 YOU DIED! Wumpus moved into your location!")
                return True  # Agent died
        return False
    
    def turn_right(self):
        """Override turn_right to include action counting and wumpus movement."""
        super().turn_right()
        wumpus_moved = self.increment_action_count()
        
        if wumpus_moved:
            collision = self.check_wumpus_collision()
            if collision:
                print("💀 YOU DIED! Wumpus moved into your location!")
                return True  # Agent died
        return False
    
    def shoot(self):
        """Override shoot to include action counting and wumpus movement."""
        super().shoot()
        wumpus_moved = self.increment_action_count()
        
        # Update wumpus locations after potential kill
        self.update_wumpus_locations()
        
        if wumpus_moved:
            collision = self.check_wumpus_collision()
            if collision:
                print("💀 YOU DIED! Wumpus moved into your location!")
                return True  # Agent died
        return False
    
    def grab_gold(self):
        """Override grab_gold to include action counting and wumpus movement."""
        result = super().grab_gold()
        wumpus_moved = self.increment_action_count()
        
        if wumpus_moved:
            collision = self.check_wumpus_collision()
            if collision:
                print("💀 YOU DIED! Wumpus moved into your location!")
                return result  # Return grab result, death will be handled in main loop
        return result
    
    def climb(self):
        """Override climb to include action counting (but no wumpus movement since game ends)."""
        result = super().climb()
        if result:  # Only count if climb was successful
            self.action_count += 1
        return result
    
    def check_wumpus_collision(self):
        """Check if agent collided with any wumpus."""
        agent_pos = (self.agent_x, self.agent_y)
        return agent_pos in self.wumpus_locations
    
    def print_map(self):
        """Override print_map to show action count and wumpus movement info."""
        super().print_map()
        print(f"Actions: {self.action_count} | Next Wumpus movement in: {5 - (self.action_count % 5)} actions")
        print(f"Wumpus locations: {self.wumpus_locations}")
