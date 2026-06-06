from dataclasses import dataclass

@dataclass
class Tile:
    kind: str
    food: int = 0
    wood: int = 0

    @property
    def walkable(self):
        return self.kind not in ("water", "mountain")
