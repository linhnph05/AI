import random
from const import DIRECTIONS, DX, DY
class Cell:
    def __init__(self):
        self.wumpus = False
        self.pit = False
        self.gold = False

class Environment:
    def __init__(self, N=8, K=2, p=0.2):
        self.N = N
        self.grid = [[Cell() for _ in range(N)] for _ in range(N)]  # grid[y][x]
        self.agent_x = 0  # column
        self.agent_y = 0  # row
        self.agent_dir = 'E'
        self.scream = False
        self.bump = False  # Track if agent bumped into a wall
        self.has_gold = False  # Track if agent has collected gold

        # Init
        self.place_pits(p)
        self.place_wumpus(K)
        self.place_gold()

    def place_pits(self, p):
        for y in range(self.N):
            for x in range(self.N):
                if (x, y) != (0, 0) and random.random() < p:
                    self.grid[y][x].pit = True

    def place_wumpus(self, K):
        count = 0
        while count < K:
            x = random.randint(0, self.N - 1)
            y = random.randint(0, self.N - 1)
            if not self.grid[y][x].pit and not self.grid[y][x].wumpus and (x, y) != (0, 0):
                self.grid[y][x].wumpus = True
                # self.wumpus_locations.append((x, y))
                count += 1

    def place_gold(self):
        while True:
            x = random.randint(0, self.N - 1)
            y = random.randint(0, self.N - 1)
            if not self.grid[y][x].pit and not self.grid[y][x].wumpus:
                self.grid[y][x].gold = True
                break

    def get_adjacent(self, x, y):
        neighbors = []
        for d in ['N', 'E', 'S', 'W']:
            nx, ny = x + DX[d], y + DY[d]
            if 0 <= nx < self.N and 0 <= ny < self.N:
                neighbors.append((nx, ny))
        return neighbors
    
    def env_get_percepts(self):
        x, y = self.agent_x, self.agent_y
        percept = {
            "position": (x, y),
            "direction": self.agent_dir ,
            "stench": any(self.grid[ny][nx].wumpus for (nx, ny) in self.get_adjacent(x, y)),
            "breeze": any(self.grid[ny][nx].pit for (nx, ny) in self.get_adjacent(x, y)),
            "glitter": self.grid[y][x].gold,
            "bump": self.bump,
            "scream": self.scream,
        }
        self.scream = False  # Reset scream after sending to agent
        self.bump = False  # Reset bump after sending to agent
        return percept

    def check_die(self):
        cell = self.grid[self.agent_y][self.agent_x]
        if cell.wumpus:
            print("💀 YOU DIED! Reason: Eaten by Wumpus!")
            return True
        elif cell.pit:
            print("💀 YOU DIED! Reason: Fell into a pit!")
            return True
        return False

    def move_forward(self):
        dx, dy = DX[self.agent_dir], DY[self.agent_dir]
        nx, ny = self.agent_x + dx, self.agent_y + dy
        if 0 <= nx < self.N and 0 <= ny < self.N:
            self.agent_x, self.agent_y = nx, ny
            died = self.check_die()  # Check for death after moving
            return died, False  # Return (died, bump)
        self.bump = True
        return False, True  # Return (died, bump)


    def turn_left(self):
        idx = DIRECTIONS.index(self.agent_dir)
        self.agent_dir = DIRECTIONS[(idx - 1) % 4]


    def turn_right(self):
        idx = DIRECTIONS.index(self.agent_dir)
        self.agent_dir = DIRECTIONS[(idx + 1) % 4]
   

    def shoot(self):
        dx, dy = DX[self.agent_dir], DY[self.agent_dir]
        # Start from the next cell in the direction agent is facing
        x, y = self.agent_x + dx, self.agent_y + dy
        
        # Travel in straight line until hitting boundary or wumpus
        while 0 <= x < self.N and 0 <= y < self.N:
            if self.grid[y][x].wumpus:
                self.grid[y][x].wumpus = False
                # self.wumpus_locations.remove((x, y))
                self.scream = True
                return
            x += dx
            y += dy
        
        # No wumpus hit
        self.scream = False

    def grab_gold(self):
        """Remove gold from current location in environment."""
        if self.grid[self.agent_y][self.agent_x].gold:
            self.grid[self.agent_y][self.agent_x].gold = False
            self.has_gold = True
            return True
        return False

    def climb(self):
        """Agent climbs out if at (0,0) with gold."""
        if self.agent_x == 0 and self.agent_y == 0 and self.has_gold:
            print("🎉 SUCCESS! Agent climbed out with the gold! Mission accomplished!")
            return True
        elif self.agent_x == 0 and self.agent_y == 0:
            print("❌ Cannot climb without gold!")
            return False
        else:
            print("❌ Can only climb at starting position (0,0)!")
            return False

    def print_map(self):
        for j in range(self.N - 1, -1, -1):  # j = y (row)
            for i in range(self.N):          # i = x (col)
                c = self.grid[j][i]
                symbol = '.'
                if self.agent_x == i and self.agent_y == j:
                    symbol = 'A'
                elif c.gold:
                    symbol = 'G'
                elif c.wumpus:
                    symbol = 'W'
                elif c.pit:
                    symbol = 'P'
                print(symbol, end='  ')
            print()
        print(f"Agent at ({self.agent_x},{self.agent_y}), facing {self.agent_dir}")