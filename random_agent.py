import random

class RandomAgent:
    
    def __init__(self, N, K=2):
        self.N = N
        self.K = K  # Number of wumpuses
        self.wumpuses_killed = 0  # Track killed wumpuses
        self.shoot = False
        self.has_gold = False
        
        self.current_x = 0
        self.current_y = 0
        self.current_dir = 'E'
        
        self.score = 0
        self.visited = set()
        self.visited.add((0, 0))
        
        self.actions = ["FORWARD", "LEFT", "RIGHT", "SHOOT", "GRAB", "CLIMB"]
        
    def update_position(self, x, y, direction):
        self.current_x = x
        self.current_y = y
        self.current_dir = direction
        self.visited.add((x, y))
    
    def Agent_get_percepts(self, percept):
        x, y = percept["position"]
        direction = percept["direction"]
        
        self.update_position(x, y, direction)
        self.last_percepts = percept
        
        if percept.get("scream"):
            self.wumpuses_killed += 1
            print(f"Random Agent: Wumpus killed! Total wumpuses killed: {self.wumpuses_killed}/{self.K}")
    
    def grab_gold_action(self):
        x, y = self.current_x, self.current_y
        if hasattr(self, 'last_percepts') and self.last_percepts.get("glitter"):
            print("Random agent randomly grabbed gold!")
            self.has_gold = True
            self.score += 10  
            return True
        else:
            print("Random agent tried to grab gold but nothing here")
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
        
        available_actions = ["FORWARD", "LEFT", "RIGHT"]
        
        if not self.shoot:
            available_actions.append("SHOOT")
        
        available_actions.extend(["GRAB", "CLIMB"])
        action = random.choice(available_actions)
        print(f"Random agent chooses: {action}")
        
        return action
    
    def print_agent_map(self, width, height, agent_x, agent_y):
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
