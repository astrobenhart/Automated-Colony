from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.actions import (
    Action,
)
from src.config import (
    FATIGUE_RATE,
    HUNGER_DEATH_THRESHOLD,
    HUNGER_RATE,
    NO_PROGRESS_TICK_LIMIT,
    STUCK_TICK_LIMIT,
    THIRST_DEATH_THRESHOLD,
    THIRST_RATE,
)
from src.goals import (
    DrinkGoal,
    EatGoal,
    EatFromStorageGoal,
    SleepGoal,
    GatherFoodGoal,
    DepositFoodGoal,
    GatherWoodGoal,
    BuildShelterGoal,
    DepositWoodGoal,
    WorkshopGoal,
    ExploreGoal,
    Goal,
)
from src.profiler import profiler
from src.lifecycle import ADULT
from src.roles import FOOD, WATER, WOOD, GENERALIST, discovery_radius, role_goal_bonus
from src.social_memory import SocialMemoryEntry
from src.traits import CALM

if TYPE_CHECKING:
    from src.world import World


@dataclass
class Agent:
    name: str
    x: int
    y: int

    hunger: int = 0
    thirst: int = 0
    fatigue: int = 0

    food: int = 0
    wood: int = 0

    alive: bool = True
    current_action: str = "Idle"
    current_goal: str = "Explore"
    role: str = GENERALIST
    lifecycle_stage: str = ADULT
    trait: str = CALM
    agent_id: str | None = None
    peak_influence_score: int = 0
    appearance_seed: int | None = None
    appearance_type: str | None = None

    # Memory of coordinate locations
    remembered_food: set[tuple[int, int]] = field(default_factory=set, repr=False)
    remembered_water: set[tuple[int, int]] = field(default_factory=set, repr=False)
    remembered_wood: set[tuple[int, int]] = field(default_factory=set, repr=False)
    remembered_shelters: set[tuple[int, int]] = field(default_factory=set, repr=False)
    social_memory: dict[str, SocialMemoryEntry] = field(default_factory=dict, repr=False)

    # Active path being followed (list of (x,y) steps, nearest first)
    current_path: list[tuple[int, int]] = field(default_factory=list, repr=False)
    current_target: tuple[int, int] | None = field(default=None, repr=False)
    current_reservation_keys: set[tuple[str, tuple[int, int]]] = field(default_factory=set, repr=False)
    stuck_ticks: int = 0
    no_progress_ticks: int = 0

    def discovery_radius(self, resource_type: str) -> int:
        return discovery_radius(self.role, resource_type)

    def update_needs(self):
        self.hunger += HUNGER_RATE
        self.thirst += THIRST_RATE
        self.fatigue += FATIGUE_RATE

    def scan_surroundings(self, world: World):
        food_radius = self.discovery_radius(FOOD)
        wood_radius = self.discovery_radius(WOOD)
        water_radius = self.discovery_radius(WATER)
        shelter_radius = 5
        scan_radius = max(food_radius, wood_radius, water_radius, shelter_radius)

        for dy in range(-scan_radius, scan_radius + 1):
            for dx in range(-scan_radius, scan_radius + 1):
                nx = self.x + dx
                ny = self.y + dy

                if 0 <= nx < world.width and 0 <= ny < world.height:
                    tile = world.tile_at(nx, ny)
                    pos = (nx, ny)
                    distance = max(abs(dx), abs(dy))

                    # Food memory
                    if distance <= food_radius:
                        if tile.food > 0:
                            self.remembered_food.add(pos)
                            world.colony_memory.remember_food(pos)
                        else:
                            self.remembered_food.discard(pos)
                            world.colony_memory.forget_food(pos)

                    # Wood memory
                    if distance <= wood_radius:
                        if tile.kind == "forest" and tile.wood > 0:
                            self.remembered_wood.add(pos)
                            world.colony_memory.remember_wood(pos)
                        else:
                            self.remembered_wood.discard(pos)
                            world.colony_memory.forget_wood(pos)

                    # Water memory
                    if distance <= water_radius:
                        if tile.kind == "water":
                            self.remembered_water.add(pos)
                            world.colony_memory.remember_water(pos)
                        else:
                            self.remembered_water.discard(pos)
                            world.colony_memory.forget_water(pos)

                    # Shelter memory
                    if distance <= shelter_radius:
                        if tile.kind == "shelter":
                            self.remembered_shelters.add(pos)
                            world.colony_memory.remember_shelter(pos)
                        else:
                            self.remembered_shelters.discard(pos)
                            world.colony_memory.forget_shelter(pos)

    def choose_goal(self, world: World) -> Goal:
        with profiler.time("goal selection"):
            goals = [
                DrinkGoal(),
                EatGoal(),
                EatFromStorageGoal(),
                SleepGoal(),
                GatherFoodGoal(),
                DepositFoodGoal(),
                GatherWoodGoal(),
                BuildShelterGoal(),
                DepositWoodGoal(),
                WorkshopGoal(),
                ExploreGoal(),
            ]
            valid_goals = [goal for goal in goals if goal.can_do(self, world)]
            urgent_survival_goals = [
                goal
                for goal in valid_goals
                if (
                    (goal.name == "Drink" and self.thirst >= 50)
                    or (goal.name in ("Eat", "Eat from storage", "Gather food") and self.hunger >= 50)
                    or (goal.name == "Sleep" and self.fatigue >= 70)
                )
            ]
            if urgent_survival_goals:
                goal = max(urgent_survival_goals, key=lambda candidate: candidate.score(self, world))
            elif self.needs_emergency_exploration(valid_goals, world):
                goal = next(goal for goal in valid_goals if goal.name == "Explore")
            else:
                goal = max(valid_goals, key=lambda candidate: self.goal_score(candidate, world))
            self.current_goal = goal.name
            return goal

    def goal_score(self, goal: Goal, world: World) -> int:
        with profiler.time("goal scoring"):
            return goal.score(self, world) + role_goal_bonus(self.role, goal.name)

    def needs_emergency_exploration(self, valid_goals: list[Goal], world: World) -> bool:
        goal_names = {goal.name for goal in valid_goals}
        can_explore = "Explore" in goal_names

        hungry_without_food_plan = (
            self.hunger >= 50
            and self.food == 0
            and world.colony_storage.food == 0
            and "Gather food" not in goal_names
        )
        thirsty_without_water_plan = self.thirst >= 50 and "Drink" not in goal_names

        return can_explore and (hungry_without_food_plan or thirsty_without_water_plan)

    def choose_action(self, world: World) -> Action:
        goal = self.choose_goal(world)
        return goal.choose_action(self, world)

    def reset_stuck(self):
        self.stuck_ticks = 0
        self.no_progress_ticks = 0

    def record_path_blocked(self):
        self.stuck_ticks = min(self.stuck_ticks + 1, STUCK_TICK_LIMIT)
        self.current_path = []

        if self.stuck_ticks >= STUCK_TICK_LIMIT:
            self.current_target = None

    def progress_snapshot(self, world: World):
        return {
            "position": (self.x, self.y),
            "needs": (self.hunger, self.thirst, self.fatigue),
            "inventory": (self.food, self.wood),
            "storage": (world.colony_storage.food, world.colony_storage.wood),
            "shelters": world.count_tiles("shelter"),
            "target": self.current_target,
        }

    def update_progress_tracking(self, world: World, before):
        after = self.progress_snapshot(world)
        if self._made_progress(before, after):
            self.no_progress_ticks = 0
            return

        self.record_no_progress()
        if self.current_action == "Recovering":
            self.release_reservations(world)

    def record_no_progress(self):
        self.no_progress_ticks = min(self.no_progress_ticks + 1, NO_PROGRESS_TICK_LIMIT)

        if self.no_progress_ticks >= NO_PROGRESS_TICK_LIMIT:
            self.current_path = []
            self.current_target = None
            self.current_action = "Recovering"

    def release_reservations(self, world: World):
        world.reservations.release_agent(self)

    def _made_progress(self, before, after) -> bool:
        before_hunger, before_thirst, before_fatigue = before["needs"]
        after_hunger, after_thirst, after_fatigue = after["needs"]
        return (
            before["position"] != after["position"]
            or after_hunger < before_hunger
            or after_thirst < before_thirst
            or after_fatigue < before_fatigue
            or before["inventory"] != after["inventory"]
            or before["storage"] != after["storage"]
            or before["shelters"] != after["shelters"]
            or before["target"] != after["target"]
        )

    def die_if_needed(self, world: World):
        if self.hunger >= HUNGER_DEATH_THRESHOLD:
            self.alive = False
            self.current_action = "Dead"
            self.release_reservations(world)
            world.log(f"{self.name} died of starvation.")
        elif self.thirst >= THIRST_DEATH_THRESHOLD:
            self.alive = False
            self.current_action = "Dead"
            self.release_reservations(world)
            world.log(f"{self.name} died of thirst.")
