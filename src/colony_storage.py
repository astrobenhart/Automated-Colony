from __future__ import annotations

from src.config import FOOD_SPOILAGE_DAYS


class ColonyStorage:
    def __init__(
        self,
        food: int = 0,
        water: int = 0,
        wood: int = 0,
        building_materials: int = 0,
    ):
        self.food_batches: list[int] = [0] * max(0, food)
        self.water = max(0, water)
        self.wood = max(0, wood)
        self.building_materials = max(0, building_materials)

    @property
    def food(self) -> int:
        return len(self.food_batches)

    @food.setter
    def food(self, amount: int):
        self.food_batches = [0] * max(0, amount)

    def deposit_food(self, amount: int) -> int:
        deposited = max(0, amount)
        self.food_batches.extend([0] * deposited)
        return deposited

    def withdraw_food(self, amount: int) -> int:
        withdrawn = min(max(0, amount), self.food)
        if withdrawn <= 0:
            return 0
        self.food_batches.sort(reverse=True)
        del self.food_batches[:withdrawn]
        return withdrawn

    def age_food(self, max_age: int = FOOD_SPOILAGE_DAYS) -> int:
        if max_age <= 0:
            spoiled = self.food
            self.food_batches.clear()
            return spoiled

        spoiled = 0
        fresh_batches = []
        for age in self.food_batches:
            next_age = age + 1
            if next_age >= max_age:
                spoiled += 1
            else:
                fresh_batches.append(next_age)
        self.food_batches = fresh_batches
        return spoiled

    def deposit_water(self, amount: int) -> int:
        deposited = max(0, amount)
        self.water += deposited
        return deposited

    def withdraw_water(self, amount: int) -> int:
        withdrawn = min(max(0, amount), self.water)
        self.water -= withdrawn
        return withdrawn

    def deposit_wood(self, amount: int) -> int:
        deposited = max(0, amount)
        self.wood += deposited
        return deposited

    def withdraw_wood(self, amount: int) -> int:
        withdrawn = min(max(0, amount), self.wood)
        self.wood -= withdrawn
        return withdrawn

    def deposit_building_materials(self, amount: int) -> int:
        deposited = max(0, amount)
        self.building_materials += deposited
        return deposited

    def withdraw_building_materials(self, amount: int) -> int:
        withdrawn = min(max(0, amount), self.building_materials)
        self.building_materials -= withdrawn
        return withdrawn
