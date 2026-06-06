from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class ColonyMemory:
    known_food: set[tuple[int, int]] = field(default_factory=set)
    known_water: set[tuple[int, int]] = field(default_factory=set)
    known_wood: set[tuple[int, int]] = field(default_factory=set)
    known_shelters: set[tuple[int, int]] = field(default_factory=set)

    def remember_food(self, pos: tuple[int, int]):
        self.known_food.add(pos)

    def forget_food(self, pos: tuple[int, int]):
        self.known_food.discard(pos)

    def remember_water(self, pos: tuple[int, int]):
        self.known_water.add(pos)

    def forget_water(self, pos: tuple[int, int]):
        self.known_water.discard(pos)

    def remember_wood(self, pos: tuple[int, int]):
        self.known_wood.add(pos)

    def forget_wood(self, pos: tuple[int, int]):
        self.known_wood.discard(pos)

    def remember_shelter(self, pos: tuple[int, int]):
        self.known_shelters.add(pos)

    def forget_shelter(self, pos: tuple[int, int]):
        self.known_shelters.discard(pos)
