import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.agent import Agent
from src.carrying_capacity import (
    FOOD_STRAINED,
    SHELTER_STRAINED,
    STABLE,
    WATER_STRAINED,
    carrying_capacity_report,
)
from src.farming import FarmPlot
from src.renderer import PygameRenderer
from src.settlement import Settlement
from src.tile import Tile
from src.world import World


def make_world(width=12, height=12, population=6):
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    world.settlement = Settlement("Willowhold", width // 2, height // 2, 1, "Spring")
    world.agents = [Agent(f"A{index}", 1 + index, 1) for index in range(population)]
    world.update_settlement_population()
    return world


def add_shelters(world, count):
    for index in range(count):
        world.tile_at(index, 3).kind = "shelter"


def add_homes(world, count):
    for index in range(count):
        world.tile_at(index, 4).kind = "home"


def teardown_function():
    pygame.quit()


def test_stable_capacity_report_explains_supporting_factors():
    world = make_world(population=4)
    add_shelters(world, 2)
    world.colony_storage.deposit_food(20)
    world.settlement.local_food = {(1, 1), (2, 1)}
    world.settlement.local_water = {(3, 1), (4, 1)}

    report = carrying_capacity_report(world)

    assert report.status == STABLE
    assert report.population == 4
    assert report.capacity >= 4
    assert "support the living population" in report.reason
    assert any("Housing:" in line for line in report.reason_lines)
    assert any("Food:" in line for line in report.reason_lines)
    assert any("Water:" in line for line in report.reason_lines)


def test_food_strained_report_names_food_and_reason_lines():
    world = make_world(population=9)
    add_shelters(world, 3)
    world.colony_storage.deposit_food(8)
    world.settlement.local_food = {(1, 1), (2, 1)}
    world.settlement.local_water = {(3, 1), (4, 1), (5, 1)}

    report = carrying_capacity_report(world)

    assert report.population == 9
    assert report.capacity == 6
    assert report.status == FOOD_STRAINED
    assert report.reason == "Food is the limiting factor."
    assert report.reason_lines[0] == "Population: 9"
    assert "Food: 6 capacity" in report.reason_lines[2]


def test_shelter_strained_report_when_beds_are_limiting():
    world = make_world(population=7)
    add_shelters(world, 1)
    world.colony_storage.deposit_food(30)
    world.settlement.local_water = {(1, 1), (2, 1), (3, 1)}

    report = carrying_capacity_report(world)

    assert report.capacity == 5
    assert report.status == SHELTER_STRAINED
    assert report.reason == "Housing capacity is the limiting factor."


def test_home_tiles_count_toward_housing_capacity():
    world = make_world(population=7)
    add_homes(world, 2)
    world.colony_storage.deposit_food(30)
    world.settlement.local_water = {(1, 1), (2, 1), (3, 1)}

    report = carrying_capacity_report(world)

    assert report.shelter_capacity == 10
    assert report.reason_lines[1] == "Housing: 10 capacity from 2 houses (2 houses, 0 legacy shelters)"


def test_legacy_shelter_tiles_still_count_as_housing_capacity():
    world = make_world(population=4)
    add_shelters(world, 2)
    world.colony_storage.deposit_food(30)
    world.settlement.local_water = {(1, 1), (2, 1)}

    report = carrying_capacity_report(world)

    assert report.housing_capacity == 10
    assert "legacy shelters" in report.reason_lines[1]


def test_water_strained_report_when_water_access_is_limiting():
    world = make_world(population=6)
    add_shelters(world, 3)
    world.colony_storage.deposit_food(40)
    world.settlement.local_water = {(1, 1)}

    report = carrying_capacity_report(world)

    assert report.capacity == 4
    assert report.status == WATER_STRAINED
    assert report.reason == "Water access is the limiting factor."


def test_farms_raise_food_capacity_reasonably():
    world = make_world(population=6)
    add_shelters(world, 3)
    world.settlement.local_water = {(1, 1), (2, 1)}
    world.settlement.farm_plots.append(FarmPlot(4, 4, food=3))

    report = carrying_capacity_report(world)

    assert report.food_capacity == 5
    assert "3 farm-ready" in report.reason_lines[2]
    assert "Farms: 1 active plots" in report.reason_lines


def test_world_refreshes_settlement_carrying_capacity_report():
    world = make_world(population=4)
    add_shelters(world, 2)
    world.colony_storage.deposit_food(20)
    world.settlement.local_water = {(1, 1), (2, 1)}

    world.update_carrying_capacity()

    assert world.settlement.carrying_capacity_report is not None
    assert world.settlement.carrying_capacity_report.population == 4


def test_renderer_draws_colony_summary_without_crashing():
    world = make_world(population=9)
    add_shelters(world, 3)
    world.colony_storage.deposit_food(8)
    world.settlement.local_food = {(1, 1), (2, 1)}
    world.settlement.local_water = {(3, 1), (4, 1), (5, 1)}
    world.update_carrying_capacity()
    renderer = PygameRenderer(world)

    end_y = renderer.draw_colony_summary(10, 10, 260, 220)

    assert end_y > 10
