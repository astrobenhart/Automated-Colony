from dataclasses import dataclass

@dataclass
class Tile:
    kind: str
    food: int = 0
    wood: int = 0
    foot_traffic: int = 0
    food_depleted_days: int = 0
    road_origin: str | None = None

    @property
    def walkable(self):
        return self.kind not in ("water", "mountain")
