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
    water: int = 0
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
    remembering: str | None = None
    remembrance_expires_day: int = 0
    home_settlement_id: str | None = None
    home_settlement_name: str | None = None
    household_id: str | None = None
    home_id: str | None = None
    home_x: int | None = None
    home_y: int | None = None
    birth_settlement_id: str | None = None
    birth_settlement_name: str | None = None
    parent_ids: list[str] = field(default_factory=list)
    child_ids: list[str] = field(default_factory=list)
    generation: int = 0
    render_from_x: float | None = field(default=None, repr=False)
    render_from_y: float | None = field(default=None, repr=False)
    render_target_x: float | None = field(default=None, repr=False)
    render_target_y: float | None = field(default=None, repr=False)
    render_progress: float = field(default=1.0, repr=False)
    render_path: list[tuple[float, float]] = field(default_factory=list, repr=False)
    render_path_index: int = field(default=0, repr=False)

    # Memory of coordinate locations
    remembered_food: set[tuple[int, int]] = field(default_factory=set, repr=False)
    remembered_water: set[tuple[int, int]] = field(default_factory=set, repr=False)
    remembered_wood: set[tuple[int, int]] = field(default_factory=set, repr=False)
    remembered_shelters: set[tuple[int, int]] = field(default_factory=set, repr=False)
    social_memory: dict[str, SocialMemoryEntry] = field(default_factory=dict, repr=False)

    # Active path being followed (list of (x,y) steps, nearest first)
    current_path: list[tuple[int, int]] = field(default_factory=list, repr=False)
    current_target: tuple[int, int] | None = field(default=None, repr=False)
    failed_path_target: tuple[int, int] | None = field(default=None, repr=False)
    current_reservation_keys: set[tuple[str, tuple[int, int]]] = field(default_factory=set, repr=False)
    active_action: Action | None = field(default=None, repr=False)
    last_decision_tick: int = -1
    idle_until_tick: int = 0
    home_wander_radius: int = 4
    daily_role: str | None = None
    task_state: str = "idle"
    task_target: tuple[int, int] | None = field(default=None, repr=False)
    task_timer: int = 0
    task_resume_state: str | None = field(default=None, repr=False)
    stuck_ticks: int = 0
    no_progress_ticks: int = 0

    def __post_init__(self):
        self.sync_render_position()

    def discovery_radius(self, resource_type: str) -> int:
        return discovery_radius(self.role, resource_type)

    def update_needs(self):
        self.hunger += HUNGER_RATE
        self.thirst += THIRST_RATE
        self.fatigue += FATIGUE_RATE

    def sync_render_position(self):
        self.render_from_x = float(self.x)
        self.render_from_y = float(self.y)
        self.render_target_x = float(self.x)
        self.render_target_y = float(self.y)
        self.render_progress = 1.0
        self.render_path = [(float(self.x), float(self.y))]
        self.render_path_index = 0

    def begin_render_move(self, from_x: int, from_y: int, to_x: int, to_y: int):
        self.begin_render_path([(from_x, from_y), (to_x, to_y)])

    def begin_render_path(self, path: list[tuple[int, int]]):
        if not path:
            self.sync_render_position()
            return

        self.render_path = [(float(x), float(y)) for x, y in path]
        self.render_path_index = 0
        self.render_from_x, self.render_from_y = self.render_path[0]
        if len(self.render_path) > 1:
            self.render_target_x, self.render_target_y = self.render_path[1]
        else:
            self.render_target_x, self.render_target_y = self.render_path[0]
        self.render_progress = 0.0

    def advance_render_motion(self, time_delta: float, tiles_per_second: float):
        if not self.render_path or self.render_path_index >= len(self.render_path) - 1:
            self.render_progress = 1.0
            return

        self.render_progress += max(0.0, time_delta) * tiles_per_second
        while self.render_progress >= 1.0 and self.render_path_index < len(self.render_path) - 1:
            self.render_progress -= 1.0
            self.render_path_index += 1
            self.render_from_x, self.render_from_y = self.render_path[self.render_path_index]
            if self.render_path_index < len(self.render_path) - 1:
                self.render_target_x, self.render_target_y = self.render_path[self.render_path_index + 1]
            else:
                self.render_target_x, self.render_target_y = self.render_path[self.render_path_index]
                self.render_progress = 1.0
                break

    def render_position(self) -> tuple[float, float]:
        if (
            self.render_from_x is None
            or self.render_from_y is None
            or self.render_target_x is None
            or self.render_target_y is None
        ):
            self.sync_render_position()

        if self.render_path and self.render_path_index >= len(self.render_path) - 1:
            return self.render_path[-1]

        progress = max(0.0, min(1.0, self.render_progress))
        x = self.render_from_x + (self.render_target_x - self.render_from_x) * progress
        y = self.render_from_y + (self.render_target_y - self.render_from_y) * progress
        return x, y

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

    def update_decision(self, world: World) -> Action:
        self.scan_surroundings(world)
        self.active_action = self.choose_action(world)
        self.last_decision_tick = world.tick
        return self.active_action

    def action_for_tick(self, world: World) -> Action:
        from src.config import DECISION_INTERVAL_TICKS

        if (
            self.active_action is None
            or self.last_decision_tick < 0
            or world.tick - self.last_decision_tick >= DECISION_INTERVAL_TICKS
            or not self.active_action.can_do(self, world)
        ):
            return self.update_decision(world)

        return self.active_action

    def reset_stuck(self):
        self.stuck_ticks = 0
        self.no_progress_ticks = 0

    def record_path_blocked(self):
        self.stuck_ticks = min(self.stuck_ticks + 1, STUCK_TICK_LIMIT)
        self.current_path = []

        if self.stuck_ticks >= STUCK_TICK_LIMIT:
            self.current_target = None
            self.failed_path_target = None

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
        if self.current_action == "Idle" and self.idle_until_tick > world.tick:
            self.no_progress_ticks = 0
            return

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
            self.failed_path_target = None
            self.active_action = None
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
            self.active_action = None
            self.release_reservations(world)
            from src.death_memory import record_death
            record_death(world, self, "starvation")
        elif self.thirst >= THIRST_DEATH_THRESHOLD:
            self.alive = False
            self.current_action = "Dead"
            self.active_action = None
            self.release_reservations(world)
            from src.death_memory import record_death
            record_death(world, self, "thirst")
