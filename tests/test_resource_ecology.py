import random

from src.resource_ecology import (
    apply_resource_ecology,
    food_dieoff_chance,
    food_growth_chance,
    max_food,
    max_wood,
    wood_growth_chance,
)
from src.tile import Tile


class FixedRandom:
    def __init__(self, value: float):
        self.value = value

    def random(self):
        return self.value


class SequenceRandom:
    def __init__(self, values):
        self.values = list(values)

    def random(self):
        return self.values.pop(0)


def test_wetlands_grow_food_faster_than_dry_terrain():
    assert food_growth_chance("wetland", "Spring") > food_growth_chance("dry", "Spring")


def test_forests_grow_wood_faster_than_plain_or_dry_terrain():
    assert wood_growth_chance("forest", "Spring") > wood_growth_chance("plain", "Spring")
    assert wood_growth_chance("forest", "Spring") > wood_growth_chance("dry", "Spring")


def test_winter_growth_is_lower_than_spring_growth():
    assert food_growth_chance("plain", "Winter") < food_growth_chance("plain", "Spring")
    assert wood_growth_chance("forest", "Winter") < wood_growth_chance("forest", "Spring")


def test_winter_can_cause_food_dieoff():
    tile = Tile("plain", food=2)

    apply_resource_ecology(tile, "Winter", SequenceRandom([0.0, 1.0]))

    assert tile.food == 1


def test_dry_terrain_has_extra_summer_dieoff_pressure():
    assert food_dieoff_chance("dry", "Summer") > food_dieoff_chance("dry", "Spring")


def test_resource_caps_prevent_unbounded_growth():
    tile = Tile("wetland", food=max_food("wetland"), wood=0)

    apply_resource_ecology(tile, "Spring", FixedRandom(0.0))

    assert tile.food == max_food("wetland")


def test_forest_wood_cap_is_highest():
    assert max_wood("forest") > max_wood("hill")
    assert max_wood("forest") > max_wood("plain")


def test_mountains_and_water_remain_barren():
    for kind in ("mountain", "water"):
        tile = Tile(kind, food=5, wood=5)

        apply_resource_ecology(tile, "Spring", FixedRandom(0.0))

        assert tile.food == 0
        assert tile.wood == 0


def test_ecology_behavior_is_deterministic_with_seeded_rng():
    first = Tile("forest", food=1, wood=2)
    second = Tile("forest", food=1, wood=2)

    first_rng = random.Random(7)
    second_rng = random.Random(7)

    for _ in range(20):
        apply_resource_ecology(first, "Autumn", first_rng)
        apply_resource_ecology(second, "Autumn", second_rng)

    assert (first.food, first.wood) == (second.food, second.wood)
