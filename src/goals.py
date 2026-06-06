from __future__ import annotations
from typing import TYPE_CHECKING

from src.actions import (
    Action,
    DrinkAction,
    EatAction,
    GatherFoodAction,
    GatherWoodAction,
    BuildShelterAction,
    SleepAction,
    WanderAction,
    SeekWaterAction,
    SeekFoodAction,
    SeekWoodAction,
    SeekShelterAction,
)

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


class Goal:
    name = "Goal"
    action_types: tuple[type[Action], ...] = (WanderAction,)

    def valid_actions(self, agent: Agent, world: World) -> list[Action]:
        actions = [action_type() for action_type in self.action_types]
        return [action for action in actions if action.can_do(agent, world)]

    def can_do(self, agent: Agent, world: World) -> bool:
        return bool(self.valid_actions(agent, world))

    def score(self, agent: Agent, world: World) -> int:
        valid_actions = self.valid_actions(agent, world)

        if not valid_actions:
            return 0

        return max(action.score(agent, world) for action in valid_actions)

    def choose_action(self, agent: Agent, world: World) -> Action:
        valid_actions = self.valid_actions(agent, world)

        if not valid_actions:
            return WanderAction()

        return max(valid_actions, key=lambda action: action.score(agent, world))


class DrinkGoal(Goal):
    name = "Drink"
    action_types = (
        DrinkAction,
        SeekWaterAction,
    )

    def score(self, agent: Agent, world: World) -> int:
        return agent.thirst * 4


class EatGoal(Goal):
    name = "Eat"
    action_types = (
        EatAction,
    )


class GatherFoodGoal(Goal):
    name = "Gather food"
    action_types = (
        GatherFoodAction,
        SeekFoodAction,
    )


class SleepGoal(Goal):
    name = "Sleep"
    action_types = (
        SleepAction,
        SeekShelterAction,
    )

    def score(self, agent: Agent, world: World) -> int:
        return agent.fatigue * 2


class GatherWoodGoal(Goal):
    name = "Gather wood"
    action_types = (
        GatherWoodAction,
        SeekWoodAction,
    )

    def can_do(self, agent: Agent, world: World) -> bool:
        return world.needs_more_shelters() and super().can_do(agent, world)

    def score(self, agent: Agent, world: World) -> int:
        if not world.needs_more_shelters():
            return 0
        return super().score(agent, world)


class BuildShelterGoal(Goal):
    name = "Build shelter"
    action_types = (
        BuildShelterAction,
    )

    def can_do(self, agent: Agent, world: World) -> bool:
        return world.needs_more_shelters() and super().can_do(agent, world)

    def score(self, agent: Agent, world: World) -> int:
        if not world.needs_more_shelters():
            return 0
        return super().score(agent, world)


class ExploreGoal(Goal):
    name = "Explore"
    action_types = (
        WanderAction,
    )

    def score(self, agent: Agent, world: World) -> int:
        return 10
