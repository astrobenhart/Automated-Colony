from __future__ import annotations
import random
from typing import TYPE_CHECKING

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
        return agent.food > 1

    def score(self, agent: Agent, world: World) -> int:
        return 15

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        agent.reset_stuck()
        amount = agent.food - 1
        deposited = world.colony_storage.deposit_food(amount)
        agent.food -= deposited
        world.log(f"{agent.name} stores {deposited} food.")


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
        return agent.wood > 0 and not world.needs_more_shelters()

    def score(self, agent: Agent, world: World) -> int:
        return 12

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        agent.reset_stuck()
        deposited = world.colony_storage.deposit_wood(agent.wood)
        agent.wood -= deposited
        world.log(f"{agent.name} stores {deposited} wood.")


class BuildShelterAction(Action):
    name = "Building shelter"

    def can_do(self, agent: Agent, world: World) -> bool:
        tile = world.tile_at(agent.x, agent.y)
        return tile.kind == "grass" and world.should_build_shelter(agent)

    def score(self, agent: Agent, world: World) -> int:
        if world.should_build_shelter(agent):
            return 80
        return 0

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        agent.reset_stuck()
        tile = world.tile_at(agent.x, agent.y)
        tile.kind = "shelter"
        agent.wood -= 3
        world.log(f"{agent.name} builds a shelter.")


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


class WanderAction(Action):
    name = "Wandering"

    def score(self, agent: Agent, world: World) -> int:
        return random.randint(1, 10)

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)

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
        memory = _shared_memory(agent.remembered_water, world.colony_memory.known_water)
        if not memory:
            return False
        return not world.nearby_tile_kind(agent.x, agent.y, "water")

    def score(self, agent: Agent, world: World) -> int:
        return agent.thirst * 4  # Same urgency as DrinkAction.

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        memory = _shared_memory(agent.remembered_water, world.colony_memory.known_water)
        target = _nearest(agent.x, agent.y, memory)
        _step_along_path(agent, world, target)


class SeekFoodAction(Action):
    """Move toward a remembered food tile so the agent can gather."""
    name = "Seeking food"

    def can_do(self, agent: Agent, world: World) -> bool:
        if agent.hunger <= 20:
            return False
        memory = _shared_memory(agent.remembered_food, world.colony_memory.known_food)
        if not memory:
            return False
        return world.tile_at(agent.x, agent.y).food == 0

    def score(self, agent: Agent, world: World) -> int:
        return 45 + agent.hunger  # Same urgency as GatherFoodAction.

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        memory = _shared_memory(agent.remembered_food, world.colony_memory.known_food)
        target = _nearest(agent.x, agent.y, memory)
        _step_along_path(agent, world, target)


class SeekWoodAction(Action):
    """Move toward a remembered wood tile so the agent can gather timber."""
    name = "Seeking wood"

    def can_do(self, agent: Agent, world: World) -> bool:
        if not world.should_gather_wood_for_construction(agent):
            return False
        memory = _shared_memory(agent.remembered_wood, world.colony_memory.known_wood)
        if not memory:
            return False
        return world.tile_at(agent.x, agent.y).wood == 0

    def score(self, agent: Agent, world: World) -> int:
        return 35  # Same as GatherWoodAction when wood < 3.

    def execute(self, agent: Agent, world: World):
        super().execute(agent, world)
        memory = _shared_memory(agent.remembered_wood, world.colony_memory.known_wood)
        target = _nearest(agent.x, agent.y, memory)
        _step_along_path(agent, world, target)


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
