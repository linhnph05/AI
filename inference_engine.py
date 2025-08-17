from const import DIRECTIONS, DX, DY

class InferenceEngine:
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.rules = [
            self.rule_safecombination,
            self.rule_eliminate_possible_pit_by_breeze_conflict,
            self.rule_eliminate_possible_wumpus_by_stench_conflict,
            self.rule_confirm_pit_from_breeze,
            self.rule_confirm_wumpus_from_stench,
        ]
    def rule_no_breeze(self, x, y):
        changed = False
        for nx, ny in self.kb.get_adjacent(x, y):
            if self.kb.add_fact("SafePit", nx, ny):
                changed = True
        return changed

    def rule_breeze_possible_pit(self, x, y):
        changed = False
        for nx, ny in self.kb.get_adjacent(x, y):
            if not self.kb.fact_exists("Safe", nx, ny):
                if self.kb.add_fact("PossiblePit", nx, ny):
                    changed = True
        return changed

    def rule_no_stench(self, x, y):
        changed = False
        for nx, ny in self.kb.get_adjacent(x, y):
            if self.kb.add_fact("SafeWumpus", nx, ny):
                changed = True
        return changed

    def rule_stench_possible_wumpus(self, x, y):
        changed = False
        for nx, ny in self.kb.get_adjacent(x, y):
            if not self.kb.fact_exists("Safe", nx, ny):
                if self.kb.add_fact("PossibleWumpus", nx, ny):
                    changed = True
        return changed

    def rule_safecombination(self):
        changed = False
        for x in range(self.kb.N):
            for y in range(self.kb.N):
                if self.kb.fact_exists("SafePit", x, y) and self.kb.fact_exists("SafeWumpus", x, y):
                    if self.kb.add_fact("Safe", x, y):
                        changed = True
                    if self.kb.remove_fact("PossiblePit", x, y):
                        changed = True
                    if self.kb.remove_fact("PossibleWumpus", x, y):
                        changed = True
        return changed

    def rule_eliminate_possible_pit_by_breeze_conflict(self):
        changed = False
        possible_pits = list(self.kb.iter_facts_of("PossiblePit"))
        for (px, py) in possible_pits:
            neighbors = self.kb.get_adjacent(px, py)
            visited_neighbors = [n for n in neighbors if (self.kb.fact_exists("Breeze", *n) or self.kb.fact_exists("NoBreeze", *n))]
            if not visited_neighbors:
                continue
            has_b = any(self.kb.fact_exists("Breeze", *n) for n in visited_neighbors)
            has_nb = any(self.kb.fact_exists("NoBreeze", *n) for n in visited_neighbors)
            if has_b and has_nb:
                if self.kb.add_fact("SafePit", px, py):
                    changed = True
                if self.kb.remove_fact("PossiblePit", px, py):
                    changed = True
        return changed

    def rule_eliminate_possible_wumpus_by_stench_conflict(self):
        changed = False
        possible_w = list(self.kb.iter_facts_of("PossibleWumpus"))
        for (px, py) in possible_w:
            neighbors = self.kb.get_adjacent(px, py)
            visited_neighbors = [n for n in neighbors if (self.kb.fact_exists("Stench", *n) or self.kb.fact_exists("NoStench", *n))]
            if not visited_neighbors:
                continue
            has_s = any(self.kb.fact_exists("Stench", *n) for n in visited_neighbors)
            has_ns = any(self.kb.fact_exists("NoStench", *n) for n in visited_neighbors)
            if has_s and has_ns:
                if self.kb.add_fact("SafeWumpus", px, py):
                    changed = True
                if self.kb.remove_fact("PossibleWumpus", px, py):
                    changed = True
        return changed

    def rule_confirm_pit_from_breeze(self):
        changed = False
        for (bx, by) in self.kb.iter_facts_of("Breeze"):
            neighbors = self.kb.get_adjacent(bx, by)

            unknown_neighbors = []
            for nx, ny in neighbors:
                if not self.kb.fact_exists("SafePit", nx, ny):
                    unknown_neighbors.append((nx, ny))

            if len(unknown_neighbors) == 1:
                px, py = unknown_neighbors[0]
                if self.kb.add_fact("Pit", px, py):
                    changed = True
                if self.kb.remove_fact("SafePit", px, py):
                    changed = True
                if self.kb.remove_fact("PossiblePit", px, py):
                    changed = True
        return changed

    def rule_confirm_wumpus_from_stench(self):
        changed = False
        for (sx, sy) in self.kb.iter_facts_of("Stench"):
            neighbors = self.kb.get_adjacent(sx, sy)

            unknown_neighbors = []
            for nx, ny in neighbors:
                if not self.kb.fact_exists("SafeWumpus", nx, ny):
                    unknown_neighbors.append((nx, ny))

            if len(unknown_neighbors) == 1:
                wx, wy = unknown_neighbors[0]
                if self.kb.add_fact("Wumpus", wx, wy):
                    changed = True
                if self.kb.remove_fact("SafeWumpus", wx, wy):
                    changed = True
                if self.kb.remove_fact("PossibleWumpus", wx, wy):
                    changed = True
        return changed

    def handle_shoot(self, agent_x, agent_y, agent_dir):
        dx, dy = DX[agent_dir], DY[agent_dir]
        x, y = agent_x + dx, agent_y + dy
        
        while 0 <= x < self.kb.N and 0 <= y < self.kb.N:
            if self.kb.fact_exists("Wumpus", x, y) or self.kb.fact_exists("PossibleWumpus", x, y):
                self.kb.remove_fact("Wumpus", x, y)
                self.kb.remove_fact("PossibleWumpus", x, y)
                self.kb.add_fact("SafeWumpus", x, y)
                
                for nx, ny in self.kb.get_adjacent(x, y):
                    if not self.kb.fact_exists("Wumpus", nx, ny) and not self.kb.fact_exists("PossibleWumpus", nx, ny):
                        self.kb.add_fact("SafeWumpus", nx, ny)
                
                break
            x += dx
            y += dy

    def logic_inference_forward_chaining(self):
        while True:
            new_fact_added = False
            for rule in self.rules:
                added = rule()
                if added:
                    new_fact_added = True
            if not new_fact_added:
                break
