from src.actions import BuildShelterAction, UseWorkshopAction
from src.agent import Agent
from src.config import COLORS, SYMBOL_LABELS, WORKSHOP_PROGRESS_REQUIRED
from src.roles import BUILDER, GENERALIST, SCOUT
from src.settlement import FOOD, WOOD, Settlement, Stockpile, is_stockpile_tile
from src.tile import Tile
from src.workshop import (
    Workshop,
    is_adjacent_to_workshop,
    is_workshop_tile,
    workshop_access_tile,
    workshop_for,
)
from src.world import World, create_world


def make_world(width=8, height=8):
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def make_settlement_with_workshop():
    return Settlement(
        "Willowhold",
        4,
        4,
        1,
        "Spring",
        stockpiles=[Stockpile(4, 5, FOOD), Stockpile(5, 4, WOOD, stored_amount=3)],
        workshops=[Workshop(3, 4)],
    )


def test_workshop_created_near_settlement_center():
    world = create_world(seed=41)
    workshop = workshop_for(world)

    assert workshop is not None
    assert max(abs(workshop.x - world.settlement.x), abs(workshop.y - world.settlement.y)) <= world.settlement.radius


def test_workshop_is_walkable_and_not_blocked_terrain():
    world = create_world(seed=42)
    workshop = workshop_for(world)
    tile = world.tile_at(workshop.x, workshop.y)

    assert tile.walkable
    assert tile.kind not in ("water", "mountain")


def test_workshop_location_is_deterministic_for_fixed_seed():
    first = create_world(seed=43)
    second = create_world(seed=43)

    assert (workshop_for(first).x, workshop_for(first).y) == (workshop_for(second).x, workshop_for(second).y)


def test_workshop_does_not_overlap_settlement_or_stockpile():
    world = create_world(seed=44)
    workshop = workshop_for(world)

    assert (workshop.x, workshop.y) != (world.settlement.x, world.settlement.y)
    assert not is_stockpile_tile(world, workshop.x, workshop.y)
    assert is_workshop_tile(world, workshop.x, workshop.y)


def test_building_materials_start_at_zero():
    world = create_world(seed=45)

    assert world.colony_storage.building_materials == 0


def test_workshop_production_consumes_wood_and_creates_building_materials():
    world = make_world()
    world.settlement = make_settlement_with_workshop()
    world.colony_storage.deposit_wood(3)
    agent = Agent("Builder", 3, 5, role=BUILDER)
    world.agents.append(agent)

    for _ in range(WORKSHOP_PROGRESS_REQUIRED):
        UseWorkshopAction().execute(agent, world)

    workshop = workshop_for(world)
    assert world.colony_storage.wood == 2
    assert world.colony_storage.building_materials == 1
    assert world.settlement.stockpile_for(WOOD).stored_amount == 2
    assert workshop.progress == 0
    assert workshop.total_items_produced == 1


def test_workshop_production_does_not_run_without_wood():
    world = make_world()
    world.settlement = make_settlement_with_workshop()
    world.settlement.stockpile_for(WOOD).stored_amount = 0
    agent = Agent("Builder", 3, 5, role=BUILDER)
    world.agents.append(agent)

    assert not UseWorkshopAction().can_do(agent, world)


def test_builder_prefers_workshop_more_than_generalist_when_needs_are_low():
    world = make_world()
    world.settlement = make_settlement_with_workshop()
    world.colony_storage.deposit_wood(1)

    builder = Agent("Builder", 3, 5, role=BUILDER)
    generalist = Agent("General", 3, 5, role=GENERALIST)

    world.agents.append(builder)
    builder_action = builder.choose_action(world)
    world.agents.remove(builder)

    world.agents.append(generalist)
    generalist_action = generalist.choose_action(world)

    assert builder.current_goal == "Workshop"
    assert builder_action.name == "Working workshop"
    assert generalist_action.name != "Working workshop"


def test_urgent_thirst_overrides_workshop_work():
    world = make_world(width=12, height=8)
    world.settlement = make_settlement_with_workshop()
    world.colony_storage.deposit_wood(1)
    world.tile_at(10, 4).kind = "water"
    agent = Agent("Builder", 3, 5, thirst=80, role=BUILDER)
    agent.remembered_water.add((10, 4))
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Drink"
    assert action.name == "Seeking water"


def test_building_material_reduces_shelter_wood_cost():
    world = make_world()
    world.settlement = make_settlement_with_workshop()
    world.colony_storage.deposit_building_materials(1)
    agent = Agent("Builder", 2, 2, wood=2, role=BUILDER)
    world.agents.append(agent)

    assert BuildShelterAction().can_do(agent, world)
    BuildShelterAction().execute(agent, world)

    assert world.tile_at(2, 2).kind == "shelter"
    assert agent.wood == 0
    assert world.colony_storage.building_materials == 0


def test_shelter_construction_still_works_without_building_materials():
    world = make_world()
    world.settlement = make_settlement_with_workshop()
    agent = Agent("Builder", 2, 2, wood=3, role=BUILDER)
    world.agents.append(agent)

    assert BuildShelterAction().can_do(agent, world)
    BuildShelterAction().execute(agent, world)

    assert world.tile_at(2, 2).kind == "shelter"
    assert agent.wood == 0


def test_workshop_access_tile_is_adjacent():
    world = make_world()
    world.settlement = make_settlement_with_workshop()
    agent = Agent("Builder", 1, 1, role=BUILDER)
    world.agents.append(agent)

    target = workshop_access_tile(world, agent)

    assert target is not None
    assert is_adjacent_to_workshop(world, target[0], target[1])


def test_workshop_symbols_are_supported_by_config():
    assert "workshop" in COLORS
    assert SYMBOL_LABELS["T"] == "Workshop"
