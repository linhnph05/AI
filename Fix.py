import random
import heapq
from collections import deque

DIRECTIONS = ['N', 'E', 'S', 'W']
DX = {'N': 0, 'E': 1, 'S': 0, 'W': -1}
DY = {'N': 1, 'E': 0, 'S': -1, 'W': 0}

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
        return {
            "position": (x, y),
            "stench": any(self.grid[ny][nx].wumpus for (nx, ny) in self.get_adjacent(x, y)),
            "breeze": any(self.grid[ny][nx].pit for (nx, ny) in self.get_adjacent(x, y)),
            "glitter": self.grid[y][x].gold,
            "bump": getattr(self, "_last_bump", False),
            "scream": self.scream,
            "direction": self.agent_dir   
        }

    def check_die(self):
        cell = self.grid[self.agent_y][self.agent_x]
        if cell.wumpus:
            print("YOU DIED! Reason: Eaten by Wumpus!")
            return True
        elif cell.pit:
            print("YOU DIED! Reason: Fell into a pit!")
            return True
        return False

    def move_forward(self):
        dx, dy = DX[self.agent_dir], DY[self.agent_dir]
        nx, ny = self.agent_x + dx, self.agent_y + dy
        if 0 <= nx < self.N and 0 <= ny < self.N:
            self.agent_x, self.agent_y = nx, ny
            return self.check_die()
        return True

    def turn_left(self):
        idx = DIRECTIONS.index(self.agent_dir)
        self.agent_dir = DIRECTIONS[(idx - 1) % 4]

    def turn_right(self):
        idx = DIRECTIONS.index(self.agent_dir)
        self.agent_dir = DIRECTIONS[(idx + 1) % 4]
   
    def shoot(self):
        x, y = self.agent_x, self.agent_y
        dx, dy = DX[self.agent_dir], DY[self.agent_dir]
        while 0 <= x < self.N and 0 <= y < self.N:
            if self.grid[y][x].wumpus:
                self.grid[y][x].wumpus = False
                self.scream = True
                return True
            x += dx
            y += dy
        self.scream = False
        return False

    def grab(self):
        if self.grid[self.agent_y][self.agent_x].gold:
            self.grid[self.agent_y][self.agent_x].gold = False
            return True
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

class Agent:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.shoot = False
        self.facts = set()
        self.visited = set()
        self.has_gold = False
        self.rules = [
            self.rule_safecombination,
            self.rule_eliminate_possible_pit_by_breeze_conflict,
            self.rule_eliminate_possible_wumpus_by_stench_conflict,
            self.rule_confirm_pit_from_breeze,
            self.rule_confirm_wumpus_from_stench,
        ]

    def fact_str(self, name, x, y):
        return f"{name}({x},{y})"

    def add_fact(self, name, x, y):
        f = self.fact_str(name, x, y)
        if f not in self.facts:
            self.facts.add(f)
            return True
        return False

    def remove_fact(self, name, x, y):
        f = self.fact_str(name, x, y)
        if f in self.facts:
            self.facts.remove(f)
            return True
        return False

    def fact_exists(self, name, x, y):
        return self.fact_str(name, x, y) in self.facts

    def iter_facts_of(self, name):
        prefix = f"{name}("
        for f in list(self.facts):
            if f.startswith(prefix) and f.endswith(")"):
                inside = f[len(prefix):-1]
                try:
                    xs, ys = inside.split(",")
                    yield (int(xs), int(ys))
                except Exception:
                    continue

    def Agent_get_percepts(self, percept, get_adjacent, agent_dir):
        x, y = percept["position"]
        self.visited.add((x, y))

        self.add_fact("Safe", x, y)
        self.add_fact("SafePit", x, y)
        self.add_fact("SafeWumpus", x, y)

        if percept.get("breeze"):
            self.add_fact("Breeze", x, y)
            self.rule_breeze_possible_pit(x, y, get_adjacent)
        else:
            self.add_fact("NoBreeze", x, y)
            self.rule_no_breeze(x, y, get_adjacent)

        if percept.get("stench"):
            self.add_fact("Stench", x, y)
            self.rule_stench_possible_wumpus(x, y, get_adjacent)
        else:
            self.add_fact("NoStench", x, y)
            self.rule_no_stench(x, y, get_adjacent)

        if percept.get("glitter"):
            self.add_fact("Glitter", x, y)

        if self.shoot:
            self.handle_shoot(x, y, agent_dir, get_adjacent)
            self.shoot = False

    def handle_shoot(self, agent_x, agent_y, agent_dir, get_adjacent):
        dx, dy = DX[agent_dir], DY[agent_dir]
        x, y = agent_x + dx, agent_y + dy
        while 0 <= x < self.width and 0 <= y < self.height:
            if self.fact_exists("Wumpus", x, y) or self.fact_exists("PossibleWumpus", x, y):
                self.remove_fact("Wumpus", x, y)
                self.remove_fact("PossibleWumpus", x, y)
                self.add_fact("SafeWumpus", x, y)
                break
            x += dx
            y += dy

    def rule_no_breeze(self, x, y, get_adjacent):
        changed = False
        for nx, ny in get_adjacent(x, y):
            if self.add_fact("SafePit", nx, ny):
                changed = True
        return changed

    def rule_breeze_possible_pit(self, x, y, get_adjacent):
        changed = False
        for nx, ny in get_adjacent(x, y):
            if not self.fact_exists("Safe", nx, ny):
                if self.add_fact("PossiblePit", nx, ny):
                    changed = True
        return changed

    def rule_no_stench(self, x, y, get_adjacent):
        changed = False
        for nx, ny in get_adjacent(x, y):
            if self.add_fact("SafeWumpus", nx, ny):
                changed = True
        return changed

    def rule_stench_possible_wumpus(self, x, y, get_adjacent):
        changed = False
        for nx, ny in get_adjacent(x, y):
            if not self.fact_exists("Safe", nx, ny):
                if self.add_fact("PossibleWumpus", nx, ny):
                    changed = True
        return changed

    def rule_safecombination(self, get_adjacent):
        changed = False
        for x in range(self.width):
            for y in range(self.height):
                if self.fact_exists("SafePit", x, y) and self.fact_exists("SafeWumpus", x, y):
                    if self.add_fact("Safe", x, y):
                        changed = True
                    if self.remove_fact("PossiblePit", x, y):
                        changed = True
                    if self.remove_fact("PossibleWumpus", x, y):
                        changed = True
        return changed

    def rule_eliminate_possible_pit_by_breeze_conflict(self, get_adjacent):
        changed = False
        possible_pits = list(self.iter_facts_of("PossiblePit"))
        for (px, py) in possible_pits:
            neighbors = get_adjacent(px, py)
            visited_neighbors = [n for n in neighbors if (self.fact_exists("Breeze", *n) or self.fact_exists("NoBreeze", *n))]
            if not visited_neighbors:
                continue
            has_b = any(self.fact_exists("Breeze", *n) for n in visited_neighbors)
            has_nb = any(self.fact_exists("NoBreeze", *n) for n in visited_neighbors)
            if has_b and has_nb:
                if self.add_fact("SafePit", px, py):
                    changed = True
                if self.remove_fact("PossiblePit", px, py):
                    changed = True
        return changed

    def rule_eliminate_possible_wumpus_by_stench_conflict(self, get_adjacent):
        changed = False
        possible_w = list(self.iter_facts_of("PossibleWumpus"))
        for (px, py) in possible_w:
            neighbors = get_adjacent(px, py)
            visited_neighbors = [n for n in neighbors if (self.fact_exists("Stench", *n) or self.fact_exists("NoStench", *n))]
            if not visited_neighbors:
                continue
            has_s = any(self.fact_exists("Stench", *n) for n in visited_neighbors)
            has_ns = any(self.fact_exists("NoStench", *n) for n in visited_neighbors)
            if has_s and has_ns:
                if self.add_fact("SafeWumpus", px, py):
                    changed = True
                if self.remove_fact("PossibleWumpus", px, py):
                    changed = True
        return changed

    def rule_confirm_pit_from_breeze(self, get_adjacent):
        changed = False
        for (bx, by) in self.iter_facts_of("Breeze"):
            neighbors = get_adjacent(bx, by)
            unknown_neighbors = []
            for nx, ny in neighbors:
                if not self.fact_exists("SafePit", nx, ny):
                    unknown_neighbors.append((nx, ny))
            if len(unknown_neighbors) == 1:
                px, py = unknown_neighbors[0]
                if self.add_fact("Pit", px, py):
                    changed = True
                if self.remove_fact("SafePit", px, py):
                    changed = True
                if self.remove_fact("PossiblePit", px, py):
                    changed = True
        return changed

    def rule_confirm_wumpus_from_stench(self, get_adjacent):
        changed = False
        for (sx, sy) in self.iter_facts_of("Stench"):
            neighbors = get_adjacent(sx, sy)
            unknown_neighbors = []
            for nx, ny in neighbors:
                if not self.fact_exists("SafeWumpus", nx, ny):
                    unknown_neighbors.append((nx, ny))
            if len(unknown_neighbors) == 1:
                wx, wy = unknown_neighbors[0]
                if self.add_fact("Wumpus", wx, wy):
                    changed = True
                if self.remove_fact("SafeWumpus", wx, wy):
                    changed = True
                if self.remove_fact("PossibleWumpus", wx, wy):
                    changed = True
        return changed

    def logic_inference_forward_chaining(self, x, y, get_adjacent):
        new_fact_added = True
        while new_fact_added:
            new_fact_added = False
            for rule in self.rules:
                added = rule(get_adjacent)
                if added:
                    new_fact_added = True

    def get_map_status(self):
        map_status = []
        for y in range(self.height):
            for x in range(self.width):
                status = []
                if self.fact_exists("Safe", x, y):
                    status = ["Safe"]
                else:
                    wumpus = self.fact_exists("Wumpus", x, y)
                    pit = self.fact_exists("Pit", x, y)
                    possible_pit = self.fact_exists("PossiblePit", x, y)
                    possible_wumpus = self.fact_exists("PossibleWumpus", x, y)
                    if wumpus:
                        status.append("Wumpus")
                    else:
                        if possible_wumpus:
                            status.append("PossibleWumpus")
                    if pit:
                        status.append("Pit")
                    else:
                        if possible_pit:
                            status.append("PossiblePit")
                glitter = self.fact_exists("Glitter", x, y)
                if glitter:
                    status.append("Gold")
                if not status:
                    status.append("Unknown")
                map_status.append({
                    "x": x,
                    "y": y,
                    "status": status
                })
        return map_status

    def print_agent_map(self, width, height, agent_x, agent_y, get_adjacent):
        for y in reversed(range(height)):
            row = []
            for x in range(width):
                cell_symbols = []
                if (x, y) == (agent_x, agent_y):
                    cell_symbols.append("A")
                if self.fact_exists("Safe", x, y):
                    cell_symbols.append("V")
                if self.fact_exists("Pit", x, y):
                    cell_symbols.append("P!")
                if self.fact_exists("Wumpus", x, y):
                    cell_symbols.append("W!")
                if self.fact_exists("PossiblePit", x, y):
                    cell_symbols.append("P?")
                if self.fact_exists("PossibleWumpus", x, y):
                    cell_symbols.append("W?")
                if not cell_symbols:
                    cell_symbols.append(".")
                cell_str = "".join(cell_symbols)
                cell_str = cell_str.ljust(3)
                row.append(cell_str)
            print("".join(row))

    def decide_action(self, percepts, env):
        x, y = percepts["position"]
        
        # If gold is present, grab it
        if percepts.get("glitter"):
            return "GRAB"
            
        # If we have gold and are at (0,0), climb out
        if self.has_gold and x == 0 and y == 0:
            return "CLIMB"
            
        # If we're facing a wumpus and have an arrow, shoot
        if self.fact_exists("Wumpus", x + DX[percepts["direction"]], y + DY[percepts["direction"]]) and not self.shoot:
            return "SHOOT"
            
        # Otherwise move to nearest safe unvisited cell
        safe_unvisited = []
        for (sx, sy) in self.iter_facts_of("Safe"):
            if (sx, sy) not in self.visited:
                safe_unvisited.append((sx, sy))
                
        if safe_unvisited:
            # Simple heuristic: go to closest safe unvisited cell
            target = min(safe_unvisited, key=lambda p: abs(p[0]-x) + abs(p[1]-y))
            return self.get_move_towards(x, y, percepts["direction"], target)
            
        # If no safe unvisited cells, try to return home
        if self.has_gold:
            return self.get_move_towards(x, y, percepts["direction"], (0, 0))
            
        # Default action if nothing else
        return "FORWARD"

    def get_move_towards(self, x, y, direction, target):
        tx, ty = target
        if x < tx and direction != 'E':
            return "RIGHT" if direction == 'N' else "LEFT"
        elif x > tx and direction != 'W':
            return "RIGHT" if direction == 'S' else "LEFT"
        elif y < ty and direction != 'N':
            return "RIGHT" if direction == 'W' else "LEFT"
        elif y > ty and direction != 'S':
            return "RIGHT" if direction == 'E' else "LEFT"
        else:
            return "FORWARD"

class PathPlanner:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.safe_cells = set()
        self.unsafe_cells = set()
    
    def update_knowledge(self, agent):
        self.safe_cells = set()
        self.unsafe_cells = set()
        
        for y in range(self.height):
            for x in range(self.width):
                if agent.fact_exists("Safe", x, y):
                    self.safe_cells.add((x, y))
                elif agent.fact_exists("Pit", x, y) or agent.fact_exists("Wumpus", x, y):
                    self.unsafe_cells.add((x, y))

    def find_safest_path(self, start, goal):
        if start == goal:
            return [start]
        
        frontier = [(0, start, [start])]
        visited = set()
        
        while frontier:
            cost, current, path = heapq.heappop(frontier)
            
            if current in visited:
                continue
            visited.add(current)
            
            if current == goal:
                return path
            
            x, y = current
            for dx, dy in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nx, ny = x + dx, y + dy
                
                if (0 <= nx < self.width and 0 <= ny < self.height and 
                    (nx, ny) not in visited):
                    
                    if (nx, ny) in self.unsafe_cells:
                        continue
                    
                    new_path = path + [(nx, ny)]
                    move_cost = self.get_move_cost(nx, ny)
                    heuristic = abs(nx - goal[0]) + abs(ny - goal[1])
                    total_cost = cost + move_cost + heuristic
                    
                    heapq.heappush(frontier, (total_cost, (nx, ny), new_path))
        
        return None

    def get_move_cost(self, x, y):
        if (x, y) in self.safe_cells:
            return 1
        elif (x, y) in self.unsafe_cells:
            return float('inf')
        else:
            return 2

class HybridWumpusAgent:
    def __init__(self, width, height):
        self.agent = Agent(width, height)
        self.planner = PathPlanner(width, height)
        self.score = 0
        self.actions_taken = []
        self.game_over = False
        self.path = []
    
    def act(self, percepts, env):
        if self.game_over:
            return None
        
        # Update knowledge base with percepts
        self.agent.Agent_get_percepts(percepts, env.get_adjacent, percepts["direction"])
        
        # Run inference engine
        self.agent.logic_inference_forward_chaining(
            percepts["position"][0], 
            percepts["position"][1], 
            env.get_adjacent
        )
        
        # Update path planner knowledge
        self.planner.update_knowledge(self.agent)
        
        # Decide action using integrated decision making
        action = self.agent.decide_action(percepts, env)
        
        # Update score based on action
        self.update_score(action, percepts)
        self.actions_taken.append(action)
        
        return action
    
    def update_score(self, action, percepts):
        if action in ["FORWARD", "LEFT", "RIGHT"]:
            self.score -= 1
        elif action == "SHOOT":
            self.score -= 10
        elif action == "GRAB" and percepts.get("glitter"):
            self.score += 10
            self.agent.has_gold = True
        elif action == "CLIMB" and percepts["position"] == (0, 0):
            if self.agent.has_gold:
                self.score += 1000
            self.game_over = True
    
    def get_performance_stats(self):
        return {
            "score": self.score,
            "actions_count": len(self.actions_taken),
            "visited_cells": len(self.agent.visited),
            "has_gold": self.agent.has_gold,
            "game_completed": self.game_over
        }

def run_hybrid_simulation():
    env = Environment(N=8, K=2, p=0.1)
    hybrid_agent = HybridWumpusAgent(env.N, env.N)
    
    print("=== Hybrid Wumpus World Agent Simulation ===")
    step = 0
    max_steps = 100
    
    while step < max_steps and not hybrid_agent.game_over:
        step += 1
        print(f"\n--- Step {step} ---")
        
        # Get percepts
        percepts = env.env_get_percepts()
        print(f"Position: {percepts['position']}, Direction: {percepts['direction']}")
        print(f"Percepts: Stench={percepts['stench']}, Breeze={percepts['breeze']}, "
              f"Glitter={percepts['glitter']}, Bump={percepts['bump']}")
        
        # Agent decides action
        action = hybrid_agent.act(percepts, env)
        if action is None:
            break
            
        print(f"Agent Action: {action}")
        
        # Execute action in environment
        if action == "FORWARD":
            if env.move_forward():
                print("Agent died!")
                hybrid_agent.score -= 1000
                break
        elif action == "LEFT":
            env.turn_left()
        elif action == "RIGHT":
            env.turn_right()
        elif action == "GRAB":
            if env.grab():
                print("Gold grabbed!")
        elif action == "SHOOT":
            if env.shoot():
                print("Wumpus killed!")
            hybrid_agent.agent.shoot = True
        elif action == "CLIMB":
            if percepts["position"] == (0, 0):
                print("Agent climbed out!")
                break
        
        # Display maps
        print("\nEnvironment Map:")
        env.print_map()
        print("\nAgent's Knowledge Map:")
        hybrid_agent.agent.print_agent_map(env.N, env.N, env.agent_x, env.agent_y, env.get_adjacent)
        
        # Show performance
        stats = hybrid_agent.get_performance_stats()
        print(f"Current Score: {stats['score']}, Visited: {stats['visited_cells']} cells")
    
    # Final results
    final_stats = hybrid_agent.get_performance_stats()
    print("\n=== Final Results ===")
    print(f"Final Score: {final_stats['score']}")
    print(f"Total Actions: {final_stats['actions_count']}")
    print(f"Cells Visited: {final_stats['visited_cells']}")
    print(f"Gold Retrieved: {final_stats['has_gold']}")
    print(f"Game Completed: {final_stats['game_completed']}")

def manual_play():
    env = Environment(N=8, K=2, p=0.1) 
    agent = Agent(env.N, env.N)
    
    while True:
        env.print_map()
        percepts = env.env_get_percepts()
        agent.Agent_get_percepts(percepts, env.get_adjacent, percepts["direction"])
        agent.logic_inference_forward_chaining(env.agent_x, env.agent_y, env.get_adjacent)
        agent.print_agent_map(env.N, env.N, env.agent_x, env.agent_y, env.get_adjacent)

        action = input("\n\nAction [F,L,R,S,Q]: ").upper()
        if action == 'F':
            if env.move_forward():
                break
        elif action == 'L':
            env.turn_left()
        elif action == 'R':
            env.turn_right()
        elif action == 'S':
            env.shoot()
            agent.shoot = True
            env.scream = False
        elif action == 'Q':
            break

if __name__ == "__main__":
    print("Choose mode:")
    print("1. Automatic simulation")
    print("2. Manual play")
    choice = input("Enter choice (1 or 2): ")
    if choice == "1":
        run_hybrid_simulation()
    else:
        manual_play()