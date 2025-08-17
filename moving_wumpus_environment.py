import random
from const import DX, DY
from environment import Environment

class MovingWumpusEnvironment(Environment):
    
    def __init__(self, N=8, K=2, p=0.2):
        super().__init__(N, K, p)
        self.action_count = 0
        self.wumpus_locations = []
        
        self.update_wumpus_locations()
        
        print(f"- Moving Wumpus Environment Initialized:")
        print(f"+ Wumpuses move every 5 agent actions")
        print(f"+ Current Wumpus locations: {self.wumpus_locations}")
    
    def update_wumpus_locations(self):
        self.wumpus_locations = []
        for y in range(self.N):
            for x in range(self.N):
                if self.grid[y][x].wumpus:
                    self.wumpus_locations.append((x, y))
    
    def increment_action_count(self):
        self.action_count += 1
        print(f"Action count: {self.action_count}")
        
        if self.action_count % 5 == 0:
            print(f"\nWUMPUS MOVEMENT PHASE (after {self.action_count} actions)")
            self.move_all_wumpuses()
            return True  
        return False
    
    def get_valid_wumpus_moves(self, wx, wy):
        valid_moves = [] 
        
        for direction in ['N', 'E', 'S', 'W']:
            nx, ny = wx + DX[direction], wy + DY[direction]
            
            if not (0 <= nx < self.N and 0 <= ny < self.N):
                continue
            
            if self.grid[ny][nx].pit:
                continue
            
            if any((nx, ny) == (ox, oy) for (ox, oy) in self.wumpus_locations if (ox, oy) != (wx, wy)):
                continue
            
            valid_moves.append((nx, ny))
        
        return valid_moves
    
    def move_single_wumpus(self, wx, wy):
        valid_moves = self.get_valid_wumpus_moves(wx, wy)
        new_x, new_y = wx, wy
        if len(valid_moves) == 0:
            print(f"   Wumpus at ({wx},{wy}) stayed in place")
        else:
            new_x, new_y = random.choice(valid_moves)
            self.grid[wy][wx].wumpus = False
            self.grid[new_y][new_x].wumpus = True
            print(f"   Wumpus moved from ({wx},{wy}) to ({new_x},{new_y})")
        return new_x, new_y
    
    def move_all_wumpuses(self):
        old_locations = self.wumpus_locations.copy()
        new_locations = []
        
        for wx, wy in old_locations:
            new_x, new_y = self.move_single_wumpus(wx, wy)
            new_locations.append((new_x, new_y))
        
        self.wumpus_locations = new_locations
        
        agent_pos = (self.agent_x, self.agent_y)
        if agent_pos in self.wumpus_locations:
            print(f"COLLISION! Wumpus moved into agent's cell {agent_pos}")
            return True 
        
        print(f"   New Wumpus locations: {self.wumpus_locations}")
        return False  
    
    def move_forward(self):
        died, bump = super().move_forward()
        
        if died:
            return died, bump
        
        wumpus_moved = self.increment_action_count()
        
        if wumpus_moved:
            collision = self.check_wumpus_collision()
            if collision:
                return True, bump  
        
        return died, bump
    
    def turn_left(self):
        super().turn_left()
        wumpus_moved = self.increment_action_count()
        
        if wumpus_moved:
            collision = self.check_wumpus_collision()
            if collision:
                print("YOU DIED! Wumpus moved into your location!")
                return True  
        return False
    
    def turn_right(self):
        super().turn_right()
        wumpus_moved = self.increment_action_count()
        
        if wumpus_moved:
            collision = self.check_wumpus_collision()
            if collision:
                print("YOU DIED! Wumpus moved into your location!")
                return True  
        return False
    
    def shoot(self):
        super().shoot()
        wumpus_moved = self.increment_action_count()
        
        self.update_wumpus_locations()
        
        if wumpus_moved:
            collision = self.check_wumpus_collision()
            if collision:
                print("YOU DIED! Wumpus moved into your location!")
                return True  
        return False
    
    def grab_gold(self):
        result = super().grab_gold()
        wumpus_moved = self.increment_action_count()
        
        if wumpus_moved:
            collision = self.check_wumpus_collision()
            if collision:
                print("YOU DIED! Wumpus moved into your location!")
                return result  
        return result
    
    def climb(self):
        result = super().climb()
        if result:  
            self.action_count += 1
        return result
    
    def check_wumpus_collision(self):
        agent_pos = (self.agent_x, self.agent_y)
        return agent_pos in self.wumpus_locations
    
    def print_map(self):
        super().print_map()
        print(f"Actions: {self.action_count} | Next Wumpus movement in: {5 - (self.action_count % 5)} actions")
        print(f"Wumpus locations: {self.wumpus_locations}")
