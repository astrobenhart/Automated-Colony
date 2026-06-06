from __future__ import annotations
from dataclasses import dataclass


@dataclass
class ColonyStorage:
    food: int = 0
    wood: int = 0

    def deposit_food(self, amount: int) -> int:
        deposited = max(0, amount)
        self.food += deposited
        return deposited

    def withdraw_food(self, amount: int) -> int:
        withdrawn = min(max(0, amount), self.food)
        self.food -= withdrawn
        return withdrawn

    def deposit_wood(self, amount: int) -> int:
        deposited = max(0, amount)
        self.wood += deposited
        return deposited

    def withdraw_wood(self, amount: int) -> int:
        withdrawn = min(max(0, amount), self.wood)
        self.wood -= withdrawn
        return withdrawn
