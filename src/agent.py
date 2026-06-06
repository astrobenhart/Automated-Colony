from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from src.actions import (
    Action,
)
from src.goals import (
    DrinkGoal,
    EatGoal,
    SleepGoal,
    GatherFoodGoal,
    GatherWoodGoal,
    BuildShelterGoal,
    ExploreGoal,
    Goal,
)

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

    # Memory of coordinate locations
    remembered_food: set[tuple[int, int]] = field(default_factory=set, repr=False)
    remembered_water: set[tuple[int, int]] = field(default_factory=set, repr=False)
    remembered_wood: set[tuple[int, int]] = field(default_factory=set, repr=False)
    remembered_shelters: set[tuple[int, int]] = field(default_factory=set, repr=False)

    # Active path being followed (list of (x,y) steps, nearest first)
    current_path: list[tuple[int, int]] = field(default_factory=list, repr=False)
    current_target: tuple[int, int] | None = field(default=None, repr=False)

    def update_needs(self):
        self.hunger += 1
        self.thirst += 2
        self.fatigue += 1

    def scan_surroundings(self, world: World):
        for dy in range(-5, 6):
            for dx in range(-5, 6):
                nx = self.x + dx
                ny = self.y + dy

                if 0 <= nx < world.width and 0 <= ny < world.height:
                    tile = world.tile_at(nx, ny)

                    # Food memory
                    if tile.food > 0:
                        self.remembered_food.add((nx, ny))
                    elif (nx, ny) in self.remembered_food:
                        self.remembered_food.remove((nx, ny))

                    # Wood memory
                    if tile.kind == "forest" and tile.wood > 0:
                        self.remembered_wood.add((nx, ny))
                    elif (nx, ny) in self.remembered_wood:
                        self.remembered_wood.remove((nx, ny))

                    # Water memory
                    if tile.kind == "water":
                        self.remembered_water.add((nx, ny))
                    elif (nx, ny) in self.remembered_water:
                        self.remembered_water.remove((nx, ny))

                    # Shelter memory
                    if tile.kind == "shelter":
                        self.remembered_shelters.add((nx, ny))
                    elif (nx, ny) in self.remembered_shelters:
                        self.remembered_shelters.remove((nx, ny))

    def choose_goal(self, world: World) -> Goal:
        goals = [
            DrinkGoal(),
            EatGoal(),
            SleepGoal(),
            GatherFoodGoal(),
            GatherWoodGoal(),
            BuildShelterGoal(),
            ExploreGoal(),
        ]
        valid_goals = [goal for goal in goals if goal.can_do(self, world)]
        goal = max(valid_goals, key=lambda candidate: candidate.score(self, world))
        self.current_goal = goal.name
        return goal

    def choose_action(self, world: World) -> Action:
        goal = self.choose_goal(world)
        return goal.choose_action(self, world)

    def die_if_needed(self, world: World):
        if self.hunger >= 100:
            self.alive = False
            self.current_action = "Dead"
            world.log(f"{self.name} died of starvation.")
        elif self.thirst >= 100:
            self.alive = False
            self.current_action = "Dead"
            world.log(f"{self.name} died of thirst.")
