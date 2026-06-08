from __future__ import annotations
from typing import TYPE_CHECKING

from src.actions import (
    Action,
    DepositFoodAction,
    SeekFoodStockpileAction,
    DepositWoodAction,
    SeekWoodStockpileAction,
    DrinkAction,
    EatAction,
    EatFromStorageAction,
    GatherFoodAction,
    GatherWoodAction,
    BuildShelterAction,
    SeekBuildSiteAction,
    UseWorkshopAction,
    SeekWorkshopAction,
    SleepAction,
    WanderAction,
    SeekWaterAction,
    SeekFoodAction,
    SeekWoodAction,
    SeekShelterAction,
)
from src.profiler import profiler

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
        with profiler.time("goal scoring"):
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


class EatFromStorageGoal(Goal):
    name = "Eat from storage"
    action_types = (
        EatFromStorageAction,
    )


class GatherFoodGoal(Goal):
    name = "Gather food"
    action_types = (
        GatherFoodAction,
        SeekFoodAction,
    )


class DepositFoodGoal(Goal):
    name = "Deposit food"
    action_types = (
        DepositFoodAction,
        SeekFoodStockpileAction,
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
        return world.should_gather_wood_for_construction(agent) and super().can_do(agent, world)

    def score(self, agent: Agent, world: World) -> int:
        if not world.should_gather_wood_for_construction(agent):
            return 0
        return super().score(agent, world)


class BuildShelterGoal(Goal):
    name = "Build shelter"
    action_types = (
        BuildShelterAction,
        SeekBuildSiteAction,
    )

    def can_do(self, agent: Agent, world: World) -> bool:
        return world.should_build_shelter(agent) and super().can_do(agent, world)

    def score(self, agent: Agent, world: World) -> int:
        if not world.should_build_shelter(agent):
            return 0
        return super().score(agent, world)


class DepositWoodGoal(Goal):
    name = "Deposit wood"
    action_types = (
        DepositWoodAction,
        SeekWoodStockpileAction,
    )


class WorkshopGoal(Goal):
    name = "Workshop"
    action_types = (
        UseWorkshopAction,
        SeekWorkshopAction,
    )

    def score(self, agent: Agent, world: World) -> int:
        return super().score(agent, world)


class ExploreGoal(Goal):
    name = "Explore"
    action_types = (
        WanderAction,
    )

    def score(self, agent: Agent, world: World) -> int:
        return 10
