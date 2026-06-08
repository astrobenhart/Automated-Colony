from __future__ import annotations

from dataclasses import dataclass

FOOD = "food"
WOOD = "wood"
BUILD_SITE = "build_site"
WORKSHOP = "workshop"
STOCKPILE_ACCESS = "stockpile_access"

DEFAULT_RESERVATION_TTL = 12


@dataclass(frozen=True)
class Reservation:
    reservation_type: str
    target: tuple[int, int]
    agent_name: str
    created_tick: int
    expires_tick: int

    @property
    def key(self) -> tuple[str, tuple[int, int]]:
        return self.reservation_type, self.target


class ReservationManager:
    def __init__(self):
        self.reservations: dict[tuple[str, tuple[int, int]], Reservation] = {}

    def reserve(
        self,
        reservation_type: str,
        target: tuple[int, int],
        agent,
        world,
        ttl: int = DEFAULT_RESERVATION_TTL,
    ) -> bool:
        self.cleanup(world)
        key = (reservation_type, target)
        existing = self.reservations.get(key)
        if existing is not None and existing.agent_name != agent.name:
            return False

        reservation = Reservation(
            reservation_type=reservation_type,
            target=target,
            agent_name=agent.name,
            created_tick=world.tick,
            expires_tick=world.tick + ttl,
        )
        self.reservations[key] = reservation
        agent.current_reservation_keys.add(key)
        return True

    def release(self, reservation_type: str, target: tuple[int, int], agent=None):
        key = (reservation_type, target)
        existing = self.reservations.get(key)
        if existing is None:
            return
        if agent is not None and existing.agent_name != agent.name:
            return

        del self.reservations[key]
        if agent is not None:
            agent.current_reservation_keys.discard(key)

    def release_agent(self, agent):
        for key in list(agent.current_reservation_keys):
            existing = self.reservations.get(key)
            if existing is not None and existing.agent_name == agent.name:
                del self.reservations[key]
            agent.current_reservation_keys.discard(key)

    def is_reserved(self, reservation_type: str, target: tuple[int, int], by_other_than=None) -> bool:
        reservation = self.reservations.get((reservation_type, target))
        if reservation is None:
            return False
        if by_other_than is None:
            return True
        name = by_other_than.name if hasattr(by_other_than, "name") else by_other_than
        return reservation.agent_name != name

    def reserved_by(self, reservation_type: str, target: tuple[int, int]) -> str | None:
        reservation = self.reservations.get((reservation_type, target))
        if reservation is None:
            return None
        return reservation.agent_name

    def cleanup(self, world):
        living_names = {agent.name for agent in world.living_agents()}
        stale = [
            key
            for key, reservation in self.reservations.items()
            if reservation.expires_tick <= world.tick
            or reservation.agent_name not in living_names
            or not _target_is_valid(world, reservation)
        ]
        for key in stale:
            reservation = self.reservations.pop(key)
            agent = _agent_named(world, reservation.agent_name)
            if agent is not None:
                agent.current_reservation_keys.discard(key)


def _target_is_valid(world, reservation: Reservation) -> bool:
    x, y = reservation.target
    if not (0 <= x < world.width and 0 <= y < world.height):
        return False
    if reservation.reservation_type == FOOD:
        return world.tile_at(x, y).food > 0
    if reservation.reservation_type == WOOD:
        return world.tile_at(x, y).wood > 0
    if reservation.reservation_type == BUILD_SITE:
        tile = world.tile_at(x, y)
        return tile.kind == "grass" and world.stockpile_at(x, y) is None and world.workshop_at(x, y) is None
    if reservation.reservation_type == WORKSHOP:
        workshop = world.workshop_at(x, y)
        return workshop is not None and workshop.active
    if reservation.reservation_type == STOCKPILE_ACCESS:
        return world.tile_at(x, y).walkable
    return True


def _agent_named(world, name: str):
    for agent in world.agents:
        if agent.name == name:
            return agent
    return None
