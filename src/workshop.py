from __future__ import annotations

from dataclasses import dataclass

from src.config import WORKSHOP_PROGRESS_REQUIRED


@dataclass
class Workshop:
    x: int
    y: int
    kind: str = "basic"
    production: str = "building_materials"
    progress: int = 0
    active: bool = True
    total_items_produced: int = 0

    def work(self) -> bool:
        if not self.active:
            return False

        self.progress += 1
        return self.progress >= WORKSHOP_PROGRESS_REQUIRED

    def complete_item(self):
        self.progress = 0
        self.total_items_produced += 1


def create_workshops(world, settlement) -> list[Workshop]:
    pos = _nearest_workshop_tile(world, settlement)
    if pos is None:
        return []
    return [Workshop(pos[0], pos[1])]


def _nearest_workshop_tile(world, settlement) -> tuple[int, int] | None:
    blocked = {(settlement.x, settlement.y)}
    blocked.update((stockpile.x, stockpile.y) for stockpile in settlement.stockpiles)

    for radius in range(1, settlement.radius + 1):
        candidates = []
        for y in range(max(0, settlement.y - radius), min(world.height, settlement.y + radius + 1)):
            for x in range(max(0, settlement.x - radius), min(world.width, settlement.x + radius + 1)):
                if max(abs(x - settlement.x), abs(y - settlement.y)) != radius:
                    continue
                if (x, y) in blocked:
                    continue
                if not world.tile_at(x, y).walkable:
                    continue
                if world.agent_at(x, y) is not None:
                    continue
                candidates.append((x, y))

        if candidates:
            return min(candidates, key=lambda pos: (abs(pos[0] - settlement.x) + abs(pos[1] - settlement.y), pos[1], pos[0]))

    return None


def workshop_for(world) -> Workshop | None:
    settlement = world.settlement
    if settlement is None:
        return None
    for workshop in settlement.workshops:
        if workshop.active:
            return workshop
    return None


def is_workshop_tile(world, x: int, y: int) -> bool:
    settlement = world.settlement
    if settlement is None:
        return False
    return any(workshop.x == x and workshop.y == y for workshop in settlement.workshops)


def is_adjacent_to_workshop(world, x: int, y: int) -> bool:
    workshop = workshop_for(world)
    if workshop is None:
        return False
    return max(abs(x - workshop.x), abs(y - workshop.y)) <= 1


def workshop_access_tile(world, agent=None) -> tuple[int, int] | None:
    workshop = workshop_for(world)
    if workshop is None:
        return None

    candidates = []
    for y in range(max(0, workshop.y - 1), min(world.height, workshop.y + 2)):
        for x in range(max(0, workshop.x - 1), min(world.width, workshop.x + 2)):
            if (x, y) == (workshop.x, workshop.y):
                continue
            if not world.tile_at(x, y).walkable:
                continue
            if agent is not None and (x, y) == (agent.x, agent.y):
                occupied = False
            else:
                occupied = world.agent_at(x, y) is not None
            if not occupied:
                candidates.append((x, y))

    if not candidates:
        return None

    return min(candidates, key=lambda pos: (abs(pos[0] - workshop.x) + abs(pos[1] - workshop.y), pos[1], pos[0]))
