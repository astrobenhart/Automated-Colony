from __future__ import annotations
import random
from typing import TYPE_CHECKING

from src.settlement import (
    FOOD,
    WATER,
    WOOD,
    deposit_to_stockpile,
    is_adjacent_to_stockpile,
    is_near_settlement,
    random_tile_near_settlement,
    stockpile_access_tile,
    stockpile_for,
    valid_build_tile_near_settlement,
    withdraw_from_stockpile,
)
from src.building_placement import find_build_site_near_settlement
from src.building_priorities import SHELTER
from src.profiler import profiler
from src.workshop import is_adjacent_to_workshop, workshop_access_tile, workshop_for

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


class Action:
    name = "Action"

    def can_do(self, agent: Agent, world: World) -> bool:
        return True

    def score(self, agent: Agent, world: World) -> int:
        return 0

    def execute(self, agent: Agent, world: World):
        agent.current_action = self.name


class EatAction(Action):
    name = "Eating"

    def can_do(self, agent: Agent, world: World) -> bool:
        return agent.food > 0 and agent.hunger > 20

    def score(self, agent: Agent, world: World) -> int:
        return agent.hunger * 3

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        agent.reset_stuck()
        agent.food -= 1
        agent.hunger = max(0, agent.hunger - 60)
        world.log(f"{agent.name} eats carried food.")


class EatFromStorageAction(Action):
    name = "Eating from storage"

    def can_do(self, agent: Agent, world: World) -> bool:
        return agent.food == 0 and agent.hunger > 20 and world.colony_storage.food > 0

    def score(self, agent: Agent, world: World) -> int:
        return agent.hunger * 3

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        withdrawn = world.colony_storage.withdraw_food(1)

        if withdrawn > 0:
            agent.reset_stuck()
            agent.hunger = max(0, agent.hunger - 60)
            world.log(f"{agent.name} eats colony food.")


class DrinkAction(Action):
    name = "Drinking"

    def can_do(self, agent: Agent, world: World) -> bool:
        return world.nearby_tile_kind(agent.x, agent.y, "water") and agent.thirst > 10

    def score(self, agent: Agent, world: World) -> int:
        return agent.thirst * 4

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        agent.reset_stuck()
        agent.thirst = 0
        world.log(f"{agent.name} drinks water.")


class GatherFoodAction(Action):
    name = "Gathering food"

    def can_do(self, agent: Agent, world: World) -> bool:
        return world.tile_at(agent.x, agent.y).food > 0

    def score(self, agent: Agent, world: World) -> int:
        return 45 + agent.hunger

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        agent.reset_stuck()
        tile = world.tile_at(agent.x, agent.y)
        tile.food -= 1
        agent.food += 1
        world.log(f"{agent.name} gathers food.")


class DepositFoodAction(Action):
    name = "Depositing food"

    def can_do(self, agent: Agent, world: World) -> bool:
        if agent.food <= 1:
            return False
        if stockpile_for(world, FOOD) is None:
            return True
        return is_adjacent_to_stockpile(world, agent.x, agent.y, FOOD)

    def score(self, agent: Agent, world: World) -> int:
        return 15

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        agent.reset_stuck()
        amount = agent.food - 1
        deposited = world.colony_storage.deposit_food(amount)
        deposit_to_stockpile(world, FOOD, deposited)
        agent.food -= deposited
        world.log(f"{agent.name} stores {deposited} food.")


class SeekFoodStockpileAction(Action):
    name = "Seeking food stockpile"

    def can_do(self, agent: Agent, world: World) -> bool:
        return (
            agent.food > 1
            and stockpile_for(world, FOOD) is not None
            and not is_adjacent_to_stockpile(world, agent.x, agent.y, FOOD)
            and stockpile_access_tile(world, FOOD, agent) is not None
        )

    def score(self, agent: Agent, world: World) -> int:
        return 14

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        target = stockpile_access_tile(world, FOOD, agent)
        if target is None:
            agent.record_no_progress()
            return
        _step_along_path(agent, world, target)


class GatherWoodAction(Action):
    name = "Gathering wood"

    def can_do(self, agent: Agent, world: World) -> bool:
        return (
            world.should_gather_wood_for_construction(agent)
            and world.tile_at(agent.x, agent.y).wood > 0
        )

    def score(self, agent: Agent, world: World) -> int:
        if world.should_gather_wood_for_construction(agent):
            return 35
        return 0

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        agent.reset_stuck()
        tile = world.tile_at(agent.x, agent.y)
        tile.wood -= 1
        agent.wood += 1
        world.log(f"{agent.name} gathers wood.")


class DepositWoodAction(Action):
    name = "Depositing wood"

    def can_do(self, agent: Agent, world: World) -> bool:
        if agent.wood <= 0 or world.needs_more_shelters():
            return False
        if stockpile_for(world, WOOD) is None:
            return True
        return is_adjacent_to_stockpile(world, agent.x, agent.y, WOOD)

    def score(self, agent: Agent, world: World) -> int:
        return 12

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        agent.reset_stuck()
        deposited = world.colony_storage.deposit_wood(agent.wood)
        deposit_to_stockpile(world, WOOD, deposited)
        agent.wood -= deposited
        world.log(f"{agent.name} stores {deposited} wood.")


class SeekWoodStockpileAction(Action):
    name = "Seeking wood stockpile"

    def can_do(self, agent: Agent, world: World) -> bool:
        return (
            agent.wood > 0
            and not world.needs_more_shelters()
            and stockpile_for(world, WOOD) is not None
            and not is_adjacent_to_stockpile(world, agent.x, agent.y, WOOD)
            and stockpile_access_tile(world, WOOD, agent) is not None
        )

    def score(self, agent: Agent, world: World) -> int:
        return 11

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        target = stockpile_access_tile(world, WOOD, agent)
        if target is None:
            agent.record_no_progress()
            return
        _step_along_path(agent, world, target)


class BuildShelterAction(Action):
    name = "Building shelter"

    def can_do(self, agent: Agent, world: World) -> bool:
        tile = world.tile_at(agent.x, agent.y)
        if tile.kind != "grass" or not world.should_build_shelter(agent):
            return False
        if world.settlement is None:
            return True

        preferred_site = find_build_site_near_settlement(world, SHELTER, agent)
        if preferred_site is not None:
            return (agent.x, agent.y) == preferred_site or is_near_settlement(world, agent.x, agent.y)

        return is_near_settlement(world, agent.x, agent.y)

    def score(self, agent: Agent, world: World) -> int:
        if world.should_build_shelter(agent):
            preferred_site = find_build_site_near_settlement(world, SHELTER, agent)
            if preferred_site is not None and (agent.x, agent.y) != preferred_site:
                return 70
            return 80
        return 0

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        agent.reset_stuck()
        from src.building_priorities import shelter_wood_cost_for_agent

        wood_cost = shelter_wood_cost_for_agent(agent, world)
        tile = world.tile_at(agent.x, agent.y)
        tile.kind = "shelter"
        agent.wood -= wood_cost
        if world.colony_storage.building_materials > 0:
            world.colony_storage.withdraw_building_materials(1)
        world.log(f"{agent.name} builds a shelter.")


class SeekBuildSiteAction(Action):
    name = "Seeking build site"

    def can_do(self, agent: Agent, world: World) -> bool:
        if not world.should_build_shelter(agent):
            return False
        target = find_build_site_near_settlement(world, SHELTER, agent)
        if target is None:
            return False
        return (agent.x, agent.y) != target

    def score(self, agent: Agent, world: World) -> int:
        return 78

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        target = find_build_site_near_settlement(world, SHELTER, agent)
        if target is None:
            agent.record_no_progress()
            return
        _step_along_path(agent, world, target)


class SleepAction(Action):
    name = "Sleeping"

    def can_do(self, agent: Agent, world: World) -> bool:
        return agent.fatigue > 40 and world.tile_at(agent.x, agent.y).kind == "shelter"

    def score(self, agent: Agent, world: World) -> int:
        return agent.fatigue * 2

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        agent.reset_stuck()
        agent.fatigue = 0
        world.log(f"{agent.name} sleeps in a shelter.")


class UseWorkshopAction(Action):
    name = "Working workshop"

    def can_do(self, agent: Agent, world: World) -> bool:
        return (
            _can_use_workshop(agent)
            and world.colony_storage.wood > 0
            and workshop_for(world) is not None
            and is_adjacent_to_workshop(world, agent.x, agent.y)
        )

    def score(self, agent: Agent, world: World) -> int:
        return 6

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        workshop = workshop_for(world)
        if workshop is None or world.colony_storage.wood <= 0:
            agent.record_no_progress()
            return

        agent.reset_stuck()
        if workshop.work():
            withdrawn = world.colony_storage.withdraw_wood(1)
            withdraw_from_stockpile(world, WOOD, withdrawn)
            if withdrawn > 0:
                world.colony_storage.deposit_building_materials(1)
                workshop.complete_item()
                world.log(f"{agent.name} makes building materials.")
            else:
                workshop.progress = max(0, workshop.progress - 1)


class SeekWorkshopAction(Action):
    name = "Seeking workshop"

    def can_do(self, agent: Agent, world: World) -> bool:
        return (
            _can_use_workshop(agent)
            and world.colony_storage.wood > 0
            and workshop_for(world) is not None
            and not is_adjacent_to_workshop(world, agent.x, agent.y)
            and workshop_access_tile(world, agent) is not None
        )

    def score(self, agent: Agent, world: World) -> int:
        return 5

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        target = workshop_access_tile(world, agent)
        if target is None:
            agent.record_no_progress()
            return
        _step_along_path(agent, world, target)


class WanderAction(Action):
    name = "Wandering"

    def score(self, agent: Agent, world: World) -> int:
        return random.randint(1, 10)

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)

        if _can_use_settlement_bias(agent):
            target = random_tile_near_settlement(world, random, agent.role)
            if target is not None and target != (agent.x, agent.y):
                if _step_along_path(agent, world, target):
                    return

        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        random.shuffle(directions)

        for dx, dy in directions:
            nx = agent.x + dx
            ny = agent.y + dy

            if world.can_move_to(nx, ny):
                agent.x = nx
                agent.y = ny
                agent.reset_stuck()
                return


def _can_use_settlement_bias(agent: Agent) -> bool:
    return agent.hunger < 40 and agent.thirst < 40 and agent.fatigue < 50


def _can_use_workshop(agent: Agent) -> bool:
    return agent.hunger < 40 and agent.thirst < 40 and agent.fatigue < 50


# ---------------------------------------------------------------------------
# Seek actions — pathfinding-powered movement toward remembered resources
# ---------------------------------------------------------------------------

def _nearest(agent_x: int, agent_y: int, memory: set[tuple[int, int]]) -> tuple[int, int]:
    """Return the closest remembered coordinate by Chebyshev distance."""
    return min(memory, key=lambda pos: max(abs(pos[0] - agent_x), abs(pos[1] - agent_y)))


def _shared_memory(agent_memory: set[tuple[int, int]], colony_memory: set[tuple[int, int]]) -> set[tuple[int, int]]:
    """Use personal memory first, falling back to colony memory."""
    if agent_memory:
        return agent_memory
    return colony_memory


def _known_food(agent: Agent, world: World) -> set[tuple[int, int]]:
    with profiler.time("colony memory queries"):
        _forget_invalid_food(agent, world)
        return set(_shared_memory(agent.remembered_food, world.colony_memory.known_food))


def _known_wood(agent: Agent, world: World) -> set[tuple[int, int]]:
    with profiler.time("colony memory queries"):
        _forget_invalid_wood(agent, world)
        return set(_shared_memory(agent.remembered_wood, world.colony_memory.known_wood))


def _known_water(agent: Agent, world: World) -> set[tuple[int, int]]:
    with profiler.time("colony memory queries"):
        _forget_invalid_water(agent, world)
        return set(_shared_memory(agent.remembered_water, world.colony_memory.known_water))


def _has_food(world: World, pos: tuple[int, int]) -> bool:
    x, y = pos
    return 0 <= x < world.width and 0 <= y < world.height and world.tile_at(x, y).food > 0


def _has_wood(world: World, pos: tuple[int, int]) -> bool:
    x, y = pos
    return (
        0 <= x < world.width
        and 0 <= y < world.height
        and world.tile_at(x, y).wood > 0
    )


def _has_water(world: World, pos: tuple[int, int]) -> bool:
    x, y = pos
    return 0 <= x < world.width and 0 <= y < world.height and world.tile_at(x, y).kind == "water"


def _forget_invalid_food(agent: Agent, world: World):
    for pos in set(agent.remembered_food) | set(world.colony_memory.known_food):
        if not _has_food(world, pos):
            _forget_food_target(agent, world, pos)


def _forget_invalid_wood(agent: Agent, world: World):
    for pos in set(agent.remembered_wood) | set(world.colony_memory.known_wood):
        if not _has_wood(world, pos):
            _forget_wood_target(agent, world, pos)


def _forget_invalid_water(agent: Agent, world: World):
    for pos in set(agent.remembered_water) | set(world.colony_memory.known_water):
        if not _has_water(world, pos):
            _forget_water_target(agent, world, pos)


def _forget_food_target(agent: Agent, world: World, pos: tuple[int, int]):
    agent.remembered_food.discard(pos)
    world.colony_memory.forget_food(pos)
    if agent.current_target == pos:
        agent.current_target = None
        agent.current_path = []


def _forget_wood_target(agent: Agent, world: World, pos: tuple[int, int]):
    agent.remembered_wood.discard(pos)
    world.colony_memory.forget_wood(pos)
    if agent.current_target == pos:
        agent.current_target = None
        agent.current_path = []


def _forget_water_target(agent: Agent, world: World, pos: tuple[int, int]):
    agent.remembered_water.discard(pos)
    world.colony_memory.forget_water(pos)
    if agent.current_target == pos:
        agent.current_target = None
        agent.current_path = []


def _step_along_path(agent: Agent, world: World, target: tuple[int, int]) -> bool:
    """
    Move the agent one step along a BFS path toward target.

    Returns True if a step was taken, False if the path is empty or blocked.
    Recomputes the path whenever the stored target changes or the path runs out.
    """
    from src.pathfinding import find_path

    start = (agent.x, agent.y)

    # Recompute path if target changed or path is exhausted.
    if agent.current_target != target or not agent.current_path:
        agent.current_target = target
        agent.current_path = find_path(world, start, target, avoid_occupied=True)

    if not agent.current_path:
        agent.record_path_blocked()
        return False  # Unreachable.

    next_step = agent.current_path[0]
    nx, ny = next_step

    if world.can_move_to(nx, ny):
        agent.current_path.pop(0)
        agent.x = nx
        agent.y = ny
        agent.reset_stuck()
        return True

    # Path is blocked (another agent moved in); recover and recompute later.
    agent.record_path_blocked()
    return False


class SeekWaterAction(Action):
    """Move toward a remembered water tile so the agent can drink."""
    name = "Seeking water"

    def can_do(self, agent: Agent, world: World) -> bool:
        # Only seek if thirsty, knows water, and isn't already adjacent.
        if agent.thirst <= 15:
            return False
        memory = _known_water(agent, world)
        if world.choose_resource_target(agent, WATER, memory) is None:
            return False
        return not world.nearby_tile_kind(agent.x, agent.y, "water")

    def score(self, agent: Agent, world: World) -> int:
        return agent.thirst * 4  # Same urgency as DrinkAction.

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        memory = _known_water(agent, world)
        if not memory:
            agent.current_target = None
            agent.current_path = []
            agent.record_no_progress()
            return
        target = world.choose_resource_target(agent, WATER, memory)
        if target is None:
            agent.current_target = None
            agent.current_path = []
            agent.record_no_progress()
            return
        if not _step_along_path(agent, world, target):
            _forget_water_target(agent, world, target)
            fallback = world.choose_resource_target(agent, WATER, _known_water(agent, world))
            if fallback is not None:
                _step_along_path(agent, world, fallback)


class SeekFoodAction(Action):
    """Move toward a remembered food tile so the agent can gather."""
    name = "Seeking food"

    def can_do(self, agent: Agent, world: World) -> bool:
        if agent.hunger <= 20:
            return False
        memory = _known_food(agent, world)
        if world.choose_resource_target(agent, FOOD, memory) is None:
            return False
        return world.tile_at(agent.x, agent.y).food == 0

    def score(self, agent: Agent, world: World) -> int:
        return 45 + agent.hunger  # Same urgency as GatherFoodAction.

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        memory = _known_food(agent, world)
        if not memory:
            agent.current_target = None
            agent.current_path = []
            agent.record_no_progress()
            return
        target = world.choose_resource_target(agent, FOOD, memory)
        if target is None:
            agent.current_target = None
            agent.current_path = []
            agent.record_no_progress()
            return
        if not _step_along_path(agent, world, target):
            _forget_food_target(agent, world, target)
            fallback = world.choose_resource_target(agent, FOOD, _known_food(agent, world))
            if fallback is not None:
                _step_along_path(agent, world, fallback)


class SeekWoodAction(Action):
    """Move toward a remembered wood tile so the agent can gather timber."""
    name = "Seeking wood"

    def can_do(self, agent: Agent, world: World) -> bool:
        if not world.should_gather_wood_for_construction(agent):
            return False
        memory = _known_wood(agent, world)
        if world.choose_resource_target(agent, WOOD, memory) is None:
            return False
        return world.tile_at(agent.x, agent.y).wood == 0

    def score(self, agent: Agent, world: World) -> int:
        return 35  # Same as GatherWoodAction when wood < 3.

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        memory = _known_wood(agent, world)
        if not memory:
            agent.current_target = None
            agent.current_path = []
            agent.record_no_progress()
            return
        target = world.choose_resource_target(agent, WOOD, memory)
        if target is None:
            agent.current_target = None
            agent.current_path = []
            agent.record_no_progress()
            return
        if not _step_along_path(agent, world, target):
            _forget_wood_target(agent, world, target)
            fallback = world.choose_resource_target(agent, WOOD, _known_wood(agent, world))
            if fallback is not None:
                _step_along_path(agent, world, fallback)


class SeekShelterAction(Action):
    """Move toward a remembered shelter so the agent can sleep."""
    name = "Seeking shelter"

    def can_do(self, agent: Agent, world: World) -> bool:
        if agent.fatigue <= 40:
            return False
        memory = _shared_memory(agent.remembered_shelters, world.colony_memory.known_shelters)
        if not memory:
            return False
        return world.tile_at(agent.x, agent.y).kind != "shelter"

    def score(self, agent: Agent, world: World) -> int:
        return agent.fatigue * 2  # Same urgency as SleepAction.

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        memory = _shared_memory(agent.remembered_shelters, world.colony_memory.known_shelters)
        target = _nearest(agent.x, agent.y, memory)
        _step_along_path(agent, world, target)
