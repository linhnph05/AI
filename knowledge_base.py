from const import DIRECTIONS, DX, DY

class KnowledgeBase:
    def __init__(self, N):
        self.N = N
        # Facts stored as strings in old format "Name(x,y)"
        self.facts = set()
        self.visited = set()

    def fact_str(self, name, x, y):
        return f"{name}({x},{y})"

    # --- helper thao tác facts ---
    # False if already exists, True if added or removed
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
        """Yield (x,y) for all facts with given name, e.g. all Breeze(x,y) in KB."""
        prefix = f"{name}("
        for f in list(self.facts):
            if f.startswith(prefix) and f.endswith(")"):
                inside = f[len(prefix):-1]
                try:
                    xs, ys = inside.split(",")
                    yield (int(xs), int(ys))
                except Exception:
                    continue

    def get_adjacent(self, x, y):
        """Get adjacent cells within the map boundaries."""
        neighbors = []
        for d in ['N', 'E', 'S', 'W']:
            nx, ny = x + DX[d], y + DY[d]
            if 0 <= nx < self.N and 0 <= ny < self.N:
                neighbors.append((nx, ny))
        return neighbors

    def get_map_status(self):
        """
        Return status list for each cell.
        Constraints:
        - If Safe then only Safe.
        - If Wumpus then no PossibleWumpus.
        - If Pit then no PossiblePit.
        """
        map_status = []
        for y in range(self.N):
            for x in range(self.N):
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
                
                glitter = self.fact_exists("glitter", x, y)
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
