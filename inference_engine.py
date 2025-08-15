from const import DIRECTIONS, DX, DY

class InferenceEngine:
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        # List of rules: each rule is a general function (not hardcoded coordinates)
        self.rules = [
            self.rule_safecombination,
            self.rule_eliminate_possible_pit_by_breeze_conflict,
            self.rule_eliminate_possible_wumpus_by_stench_conflict,
            self.rule_confirm_pit_from_breeze,
            self.rule_confirm_wumpus_from_stench,
        ]

    # === RULES (general) ===
    # Each rule returns True if it has added (or removed) at least 1 fact, for forward chaining to repeat.
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
        # If cell has SafePit and SafeWumpus then mark Safe
        changed = False
        # iterate whole grid
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
        """
        If a cell p has PossiblePit and among the neighbors of p there is
        at least 1 neighbor known to have Breeze and 1 neighbor known to have NoBreeze
        then p cannot be a pit => add SafePit(p) and remove PossiblePit(p).
        """
        changed = False
        # collect current possible pits to avoid modifying set during iteration
        possible_pits = list(self.kb.iter_facts_of("PossiblePit"))
        for (px, py) in possible_pits:
            neighbors = self.kb.get_adjacent(px, py)
            # only consider neighbors that already have Breeze/NoBreeze information
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
        """
        Similar for Wumpus: if a cell p has PossibleWumpus and among neighbors
        there is at least 1 Stench and 1 NoStench then p is SafeWumpus.
        """
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
        """
        If a cell has Breeze and all adjacent cells are SafePit except exactly 1 undetermined cell,
        then that cell is definitely a Pit.
        """
        changed = False
        for (bx, by) in self.kb.iter_facts_of("Breeze"):
            neighbors = self.kb.get_adjacent(bx, by)

            unknown_neighbors = []
            for nx, ny in neighbors:
                # Undetermined pit if not SafePit and not Pit yet
                if not self.kb.fact_exists("SafePit", nx, ny):
                    unknown_neighbors.append((nx, ny))

            # If only 1 neighbor is undetermined → it is a Pit
            if len(unknown_neighbors) == 1:
                px, py = unknown_neighbors[0]
                if self.kb.add_fact("Pit", px, py):
                    changed = True
                # Also remove old SafePit/PossiblePit possibilities
                if self.kb.remove_fact("SafePit", px, py):
                    changed = True
                if self.kb.remove_fact("PossiblePit", px, py):
                    changed = True
        return changed

    def rule_confirm_wumpus_from_stench(self):
        """
        If a cell has Stench and all adjacent cells are SafeWumpus except exactly 1 undetermined cell,
        then that cell is definitely a Wumpus.
        """
        changed = False
        for (sx, sy) in self.kb.iter_facts_of("Stench"):
            neighbors = self.kb.get_adjacent(sx, sy)

            unknown_neighbors = []
            for nx, ny in neighbors:
                # Undetermined wumpus if not SafeWumpus and not Wumpus yet
                if not self.kb.fact_exists("SafeWumpus", nx, ny):
                    unknown_neighbors.append((nx, ny))

            # If only 1 neighbor is undetermined → it is a Wumpus
            if len(unknown_neighbors) == 1:
                wx, wy = unknown_neighbors[0]
                if self.kb.add_fact("Wumpus", wx, wy):
                    changed = True
                # Remove old SafeWumpus/PossibleWumpus possibilities
                if self.kb.remove_fact("SafeWumpus", wx, wy):
                    changed = True
                if self.kb.remove_fact("PossibleWumpus", wx, wy):
                    changed = True
        return changed

    def handle_shoot(self, agent_x, agent_y, agent_dir):
        """Handle the aftermath of shooting an arrow (when scream is heard)."""
        dx, dy = DX[agent_dir], DY[agent_dir]
        x, y = agent_x + dx, agent_y + dy
        
        while 0 <= x < self.kb.N and 0 <= y < self.kb.N:
            # if facts contain PossibleWumpus or Wumpus then remove it
            if self.kb.fact_exists("Wumpus", x, y) or self.kb.fact_exists("PossibleWumpus", x, y):
                # Remove wumpus facts
                self.kb.remove_fact("Wumpus", x, y)
                self.kb.remove_fact("PossibleWumpus", x, y)
                self.kb.add_fact("SafeWumpus", x, y)
                
                # Update adjacent cells that might now be safe from wumpus
                for nx, ny in self.kb.get_adjacent(x, y):
                    # Only update if we don't have confirmed wumpus info for adjacent cells
                    if not self.kb.fact_exists("Wumpus", nx, ny) and not self.kb.fact_exists("PossibleWumpus", nx, ny):
                        self.kb.add_fact("SafeWumpus", nx, ny)
                
                break
            x += dx
            y += dy

    # === forward chaining general ===
    def logic_inference_forward_chaining(self):
        """
        Run forward chaining: call each general rule (not hardcoded for each cell).
        new_fact_added True if there are changes.
        """
        while True:
            new_fact_added = False
            for rule in self.rules:
                # each rule uses knowledge base methods
                added = rule()
                if added:
                    new_fact_added = True
            if not new_fact_added:
                break
