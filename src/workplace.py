from __future__ import annotations

import random
from dataclasses import dataclass, field


STORAGE = "STORAGE"
FARM = "FARM"
WORKSHOP = "WORKSHOP"
VILLAGE_CENTER = "VILLAGE_CENTER"

WORKPLACE_TYPES = (STORAGE, FARM, WORKSHOP, VILLAGE_CENTER)
DEFAULT_CAPACITY = {
    STORAGE: 4,
    FARM: 6,
    WORKSHOP: 3,
    VILLAGE_CENTER: 12,
}


@dataclass
class Workplace:
    workplace_id: str
    workplace_type: str
    x: int
    y: int
    capacity: int
    assigned_workers: list[str] = field(default_factory=list)
    tiles: list[tuple[int, int]] = field(default_factory=list)

    @property
    def position(self) -> tuple[int, int]:
        return self.x, self.y

    def __post_init__(self):
        if self.workplace_type not in WORKPLACE_TYPES:
            raise ValueError(f"Unknown workplace type: {self.workplace_type}")
        if not self.tiles:
            self.tiles = [(self.x, self.y)]

    def assign_worker(self, worker_id: str | None) -> bool:
        if worker_id is None:
            return False
        if worker_id in self.assigned_workers:
            return True
        if len(self.assigned_workers) >= self.capacity:
            return False
        self.assigned_workers.append(worker_id)
        return True


def create_workplaces(world, settlement) -> list[Workplace]:
    workplaces: list[Workplace] = [
        Workplace(
            workplace_id="village-center",
            workplace_type=VILLAGE_CENTER,
            x=settlement.x,
            y=settlement.y,
            capacity=DEFAULT_CAPACITY[VILLAGE_CENTER],
        )
    ]

    storage_tiles = [(stockpile.x, stockpile.y) for stockpile in settlement.stockpiles]
    if storage_tiles:
        storage_x = round(sum(x for x, _ in storage_tiles) / len(storage_tiles))
        storage_y = round(sum(y for _, y in storage_tiles) / len(storage_tiles))
        workplaces.append(Workplace(
            workplace_id="storage-0",
            workplace_type=STORAGE,
            x=storage_x,
            y=storage_y,
            capacity=DEFAULT_CAPACITY[STORAGE],
            tiles=storage_tiles,
        ))

    for index, workshop in enumerate(settlement.workshops):
        workplaces.append(Workplace(
            workplace_id=f"workshop-{index}",
            workplace_type=WORKSHOP,
            x=workshop.x,
            y=workshop.y,
            capacity=DEFAULT_CAPACITY[WORKSHOP],
        ))

    farm_tiles = _find_farm_placeholder_tiles(world, settlement)
    if farm_tiles:
        origin_x = min(x for x, _ in farm_tiles)
        origin_y = min(y for _, y in farm_tiles)
        workplaces.append(Workplace(
            workplace_id="farm-0",
            workplace_type=FARM,
            x=origin_x,
            y=origin_y,
            capacity=DEFAULT_CAPACITY[FARM],
            tiles=farm_tiles,
        ))

    return workplaces


def _find_farm_placeholder_tiles(world, settlement) -> list[tuple[int, int]]:
    rng = random.Random(f"{world.seed}|{settlement.settlement_id}|workplace-farm")
    used = _blocked_positions(settlement)
    candidates = []

    for y in range(max(0, settlement.y - settlement.radius), min(world.height - 1, settlement.y + settlement.radius + 1)):
        for x in range(max(0, settlement.x - settlement.radius), min(world.width - 1, settlement.x + settlement.radius + 1)):
            tiles = [(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)]
            if any(pos in used for pos in tiles):
                continue
            if not all(_valid_placeholder_tile(world, px, py) for px, py in tiles):
                continue

            center_x = x + 0.5
            center_y = y + 0.5
            hub_distance = max(abs(center_x - settlement.x), abs(center_y - settlement.y))
            if hub_distance < 3 or hub_distance > settlement.radius:
                continue
            score = hub_distance + rng.random()
            candidates.append((score, y, x, tiles))

    if not candidates:
        return []
    _, _, _, tiles = min(candidates)
    return tiles


def _valid_placeholder_tile(world, x: int, y: int) -> bool:
    if not (0 <= x < world.width and 0 <= y < world.height):
        return False
    tile = world.tile_at(x, y)
    if not tile.walkable or tile.kind in ("water", "mountain", "home", "shelter"):
        return False
    if world.agent_at(x, y) is not None:
        return False
    return True


def _blocked_positions(settlement) -> set[tuple[int, int]]:
    blocked = {(settlement.x, settlement.y)}
    blocked.update((home.x, home.y) for home in settlement.homes)
    blocked.update((stockpile.x, stockpile.y) for stockpile in settlement.stockpiles)
    blocked.update((workshop.x, workshop.y) for workshop in settlement.workshops)
    blocked.update(tile for farm in settlement.farm_plots for tile in farm.tiles)
    return blocked
