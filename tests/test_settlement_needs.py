from src.actions import BuildShelterAction, DrinkAction, GatherWoodAction, UseWorkshopAction
from src.agent import Agent
from src.building_priorities import (
    MATERIALS,
    SHELTER,
    WOOD,
    stable_top_need,
    update_settlement_needs,
)
from src.config import DESIRED_BUILDING_MATERIALS
from src.roles import BUILDER
from src.settlement import Settlement
from src.tile import Tile
from src.workshop import Workshop
from src.world import World


def make_world(width=12, height=12):
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    world.settlement = Settlement(
        "Willowhold",
        width // 2,
        height // 2,
        1,
        "Spring",
        workshops=[Workshop(width // 2 - 1, height // 2)],
    )
    return world


def add_agents(world, count):
    for index in range(count):
        world.agents.append(Agent(f"Builder{index}", 1 + index, 1, role=BUILDER))


def add_shelters(world, count):
    for index in range(count):
        world.tile_at(2 + index, 4).kind = "shelter"


def test_settlement_has_need_scores():
    world = make_world()

    assert set(world.settlement.need_scores) == {SHELTER, WOOD, MATERIALS}
    assert world.settlement.top_need is None


def test_need_scores_update_centrally():
    world = make_world()
    add_agents(world, 4)

    world.update_settlement_needs(force=True)

    assert world.settlement.need_updated_day == world.day
    assert world.settlement.need_scores[SHELTER] > 0


def test_shelter_need_rises_when_capacity_is_insufficient():
    world = make_world()
    add_agents(world, 4)

    update_settlement_needs(world, force=True)

    assert world.settlement.need_scores[SHELTER] >= 50
    assert world.settlement.top_need == SHELTER


def test_shelter_need_falls_when_capacity_is_sufficient():
    world = make_world()
    add_agents(world, 4)
    add_shelters(world, 2)

    update_settlement_needs(world, force=True)

    assert world.settlement.need_scores[SHELTER] == 0


def test_wood_need_rises_when_construction_requires_wood():
    world = make_world()
    add_agents(world, 4)

    update_settlement_needs(world, force=True)

    assert world.settlement.need_scores[WOOD] >= 50


def test_materials_need_rises_when_buffer_low_and_workshop_has_wood():
    world = make_world()
    add_agents(world, 2)
    add_shelters(world, 1)
    world.colony_storage.deposit_wood(10)

    update_settlement_needs(world, force=True)

    assert world.settlement.need_scores[MATERIALS] >= 50
    assert world.settlement.top_need == MATERIALS


def test_materials_need_falls_when_material_buffer_is_sufficient():
    world = make_world()
    add_agents(world, 2)
    add_shelters(world, 1)
    world.colony_storage.deposit_wood(10)
    world.colony_storage.deposit_building_materials(DESIRED_BUILDING_MATERIALS)

    update_settlement_needs(world, force=True)

    assert world.settlement.need_scores[MATERIALS] == 0
    assert world.settlement.top_need != MATERIALS


def test_top_need_hysteresis_avoids_small_oscillation():
    scores = {SHELTER: 60, WOOD: 66, MATERIALS: 10}

    assert stable_top_need(SHELTER, scores) == SHELTER


def test_builder_gathers_wood_when_wood_need_is_high():
    world = make_world()
    add_agents(world, 1)
    builder = world.agents[0]
    builder.x = 3
    builder.y = 3
    world.tile_at(3, 3).kind = "forest"
    world.tile_at(3, 3).wood = 2
    world.settlement.need_scores = {SHELTER: 0, WOOD: 70, MATERIALS: 0}
    world.settlement.top_need = WOOD
    world.settlement.need_updated_day = world.day

    action = builder.choose_action(world)

    assert isinstance(action, GatherWoodAction)


def test_builder_uses_workshop_when_material_need_is_high_and_wood_exists():
    world = make_world()
    add_agents(world, 1)
    builder = world.agents[0]
    builder.x = world.settlement.x - 2
    builder.y = world.settlement.y
    world.colony_storage.deposit_wood(10)
    world.settlement.need_scores = {SHELTER: 0, WOOD: 0, MATERIALS: 70}
    world.settlement.top_need = MATERIALS
    world.settlement.need_updated_day = world.day

    action = builder.choose_action(world)

    assert isinstance(action, UseWorkshopAction)


def test_builder_does_not_use_workshop_when_materials_are_sufficient():
    world = make_world()
    add_agents(world, 1)
    builder = world.agents[0]
    builder.x = world.settlement.x - 2
    builder.y = world.settlement.y
    world.colony_storage.deposit_wood(10)
    world.colony_storage.deposit_building_materials(DESIRED_BUILDING_MATERIALS)
    update_settlement_needs(world, force=True)

    assert not isinstance(builder.choose_action(world), UseWorkshopAction)


def test_shelter_overbuilding_stops_when_capacity_is_sufficient():
    world = make_world()
    add_agents(world, 2)
    add_shelters(world, 1)
    builder = world.agents[0]
    builder.wood = 3
    update_settlement_needs(world, force=True)

    assert world.highest_building_priority() is None
    assert not isinstance(builder.choose_action(world), BuildShelterAction)


def test_urgent_thirst_overrides_settlement_needs():
    world = make_world()
    add_agents(world, 1)
    builder = world.agents[0]
    builder.thirst = 80
    world.tile_at(builder.x + 1, builder.y).kind = "water"
    world.colony_storage.deposit_wood(10)
    world.settlement.need_scores = {SHELTER: 0, WOOD: 0, MATERIALS: 70}
    world.settlement.top_need = MATERIALS
    world.settlement.need_updated_day = world.day

    action = builder.choose_action(world)

    assert isinstance(action, DrinkAction)


def test_settlement_need_scoring_does_not_call_pathfinding(monkeypatch):
    world = make_world()
    add_agents(world, 4)

    def fail_find_path(*args, **kwargs):
        raise AssertionError("settlement need scoring must not pathfind")

    monkeypatch.setattr("src.pathfinding.find_path", fail_find_path)

    update_settlement_needs(world, force=True)
