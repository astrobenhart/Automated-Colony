from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.actions import DrinkAction, EatAction, SeekFoodAction, SeekShelterAction, SeekWaterAction, SleepAction, WanderAction

if TYPE_CHECKING:
    from src.actions import Action
    from src.agent import Agent
    from src.world import World


@dataclass(frozen=True)
class Goal:
    """High-level intent that selects a low-level action."""

    name: str = "Goal"

    def can_do(self, agent: Agent, world: World) -> bool:
        return True

    def score(self, agent: Agent, world: World) -> int:
        return 0

    def choose_action(self, agent: Agent, world: World) -> Action:
        return WanderAction()


@dataclass(frozen=True)
class DrinkGoal(Goal):
    name: str = "Drink"

    def can_do(self, agent: Agent, world: World) -> bool:
        return agent.thirst > 10 and (
            world.nearby_tile_kind(agent.x, agent.y, "water") or bool(agent.remembered_water)
        )

    def score(self, agent: Agent, world: World) -> int:
        if not self.can_do(agent, world):
            return -1
        return agent.thirst * 5

    def choose_action(self, agent: Agent, world: World) -> Action:
        if DrinkAction().can_do(agent, world):
            return DrinkAction()
        return SeekWaterAction()


@dataclass(frozen=True)
class EatGoal(Goal):
    name: str = "Eat"

    def can_do(self, agent: Agent, world: World) -> bool:
        return agent.hunger > 20 and (
            agent.food > 0 or world.tile_at(agent.x, agent.y).food > 0 or bool(agent.remembered_food)
        )

    def score(self, agent: Agent, world: World) -> int:
        if not self.can_do(agent, world):
            return -1
        if agent.food > 0:
            return agent.hunger * 4
        return 45 + agent.hunger * 2

    def choose_action(self, agent: Agent, world: World) -> Action:
        if EatAction().can_do(agent, world):
            return EatAction()
        if world.tile_at(agent.x, agent.y).food > 0:
            from src.actions import GatherFoodAction
            return GatherFoodAction()
        return SeekFoodAction()


@dataclass(frozen=True)
class SleepGoal(Goal):
    name: str = "Sleep"

    def can_do(self, agent: Agent, world: World) -> bool:
        return agent.fatigue > 40 and (
            world.tile_at(agent.x, agent.y).kind == "shelter" or bool(agent.remembered_shelters)
        )

    def score(self, agent: Agent, world: World) -> int:
        if not self.can_do(agent, world):
            return -1
        return agent.fatigue * 2

    def choose_action(self, agent: Agent, world: World) -> Action:
        if SleepAction().can_do(agent, world):
            return SleepAction()
        return SeekShelterAction()


@dataclass(frozen=True)
class ExploreGoal(Goal):
    name: str = "Explore"

    def score(self, agent: Agent, world: World) -> int:
        return 5

    def choose_action(self, agent: Agent, world: World) -> Action:
        return WanderAction()


def available_goals() -> list[Goal]:
    return [DrinkGoal(), EatGoal(), SleepGoal(), ExploreGoal()]


def choose_goal(agent: Agent, world: World) -> Goal:
    goals = [goal for goal in available_goals() if goal.can_do(agent, world)]
    return max(goals, key=lambda goal: goal.score(agent, world))
