import pytest

from src.actions import HarvestFarmAction, SeekFarmAction
from src.agent import Agent
from src.environment_events import create_environment_event
from src.farming import (
    FarmPlot,
    choose_farm_target,
    daily_farm_growth,
    farm_border_edges,
    farm_tiles,
    harvest_farm,
    is_valid_farm_site,
    max_farm_plots_for_population,
    maybe_create_farm,
    settlement_food_pressure,
    update_farms,
)
from src.reservations import FARM
from src.roles import BUILDER, FORAGER, SCOUT
from src.settlement import FOOD, WOOD, Settlement, Stockpile, distance_to_settlement
from src.tile import Tile
from src.workshop import Workshop
from src.world import World, create_world
from src.worldgen_settings import default_worldgen_settings


def make_world(width=16, height=16, population=4):
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    world.settings = default_worldgen_settings().with_overrides(event_frequency=0)
    center_x = width // 2
    center_y = height // 2
    world.settlement = Settlement(
        "Willowhold",
        center_x,
        center_y,
        1,
        "Spring",
        radius=5,
        population=population,
        stockpiles=[
            Stockpile(center_x, center_y + 1, FOOD),
            Stockpile(center_x + 1, center_y, WOOD),
        ],
        workshops=[Workshop(center_x - 1, center_y)],
    )
    for index in range(population):
        world.agents.append(Agent(f"A{index}", 1 + index, 1))
    return world


def make_resource_poor_world(width=16, height=16, population=6):
    world = make_world(width, height, population)
    world.settings = default_worldgen_settings().with_overrides(
        event_frequency=0,
        resource_abundance=0,
    )
    for row in world.tiles:
        for tile in row:
            tile.food = 0
            tile.wood = 0
    world.colony_storage.food = 0
    world.settlement.local_food = set()
    world.settlement.local_resource_cache_day = world.day
    return world


def test_farm_plot_owns_exactly_four_2x2_tiles():
    farm = FarmPlot(3, 4)

    assert farm.tiles == [(3, 4), (4, 4), (3, 5), (4, 5)]
    assert len(farm.tiles) == 4


def test_farm_plot_rejects_non_2x2_tiles():
    with pytest.raises(ValueError):
        FarmPlot(3, 4, tiles=[(3, 4), (4, 4), (3, 5), (5, 5)])


def test_farms_are_not_created_immediately_without_food_pressure_day():
    world = make_world()
    world.day = 1

    assert maybe_create_farm(world) is None
    assert world.settlement.farm_plots == []


def test_food_pressure_can_trigger_farm_creation():
    world = make_world()
    world.day = 2
    world.settlement.local_food = set()
    world.settlement.local_resource_cache_day = world.day

    farm = maybe_create_farm(world)

    assert farm is not None
    assert farm in world.settlement.farm_plots


def test_farm_count_is_capped_by_population():
    assert max_farm_plots_for_population(5) == 1
    assert max_farm_plots_for_population(6) == 2
    assert max_farm_plots_for_population(11) == 4

    world = make_world(population=4)
    world.day = 2
    world.settlement.local_resource_cache_day = world.day
    world.settlement.local_food = set()

    assert maybe_create_farm(world) is not None
    assert maybe_create_farm(world) is None
    assert len(world.settlement.farm_plots) == 1


def test_every_farm_tile_is_valid_and_avoids_special_tiles():
    world = make_world()
    world.day = 2
    world.settlement.local_resource_cache_day = world.day
    world.settlement.local_food = set()

    farm = maybe_create_farm(world)
    special = {
        (world.settlement.x, world.settlement.y),
        *{(stockpile.x, stockpile.y) for stockpile in world.settlement.stockpiles},
        *{(workshop.x, workshop.y) for workshop in world.settlement.workshops},
    }

    assert farm is not None
    assert all(world.tile_at(x, y).walkable for x, y in farm.tiles)
    assert not any(pos in special for pos in farm.tiles)


def test_farm_site_rejects_water_mountain_shelter_and_overlap():
    world = make_world()
    world.tile_at(3, 3).kind = "water"
    world.tile_at(4, 3).kind = "mountain"
    world.tile_at(3, 4).kind = "shelter"
    world.settlement.farm_plots.append(FarmPlot(6, 6))

    assert not is_valid_farm_site(world, 3, 3)
    assert not is_valid_farm_site(world, 6, 6)


def test_farm_placement_is_deterministic_for_fixed_world():
    first = make_world()
    second = make_world()
    first.day = second.day = 2
    first.settlement.local_resource_cache_day = first.day
    second.settlement.local_resource_cache_day = second.day

    first_farm = maybe_create_farm(first)
    second_farm = maybe_create_farm(second)

    assert first_farm.origin == second_farm.origin


def test_clustered_farms_appear_near_settlement_radius_under_pressure():
    world = make_world(width=20, height=20, population=8)
    world.day = 2
    world.settlement.local_resource_cache_day = world.day
    world.settlement.local_food = set()

    farm = maybe_create_farm(world)

    assert farm is not None
    assert all(distance_to_settlement(world, x, y) <= world.settlement.radius + 4 for x, y in farm.tiles)


def test_farms_are_not_created_when_local_food_is_sufficient():
    world = make_world(population=4)
    world.day = 2
    world.settlement.local_food = {(x, 2) for x in range(12)}
    world.settlement.local_resource_cache_day = world.day

    assert settlement_food_pressure(world) != "HIGH"
    assert maybe_create_farm(world) is None


def test_activation_scenario_a_healthy_small_colony_has_low_pressure_and_no_farm():
    world = make_world(population=4)
    world.day = 2
    world.colony_storage.deposit_food(20)
    world.settlement.local_food = set()
    world.settlement.local_resource_cache_day = world.day

    assert settlement_food_pressure(world) == "LOW"
    assert maybe_create_farm(world) is None
    assert world.settlement.farm_plots == []


def test_activation_scenario_b_low_storage_daily_update_creates_farm():
    world = make_resource_poor_world(population=6)

    assert settlement_food_pressure(world) == "HIGH"

    world.advance_day()

    assert len(world.settlement.farm_plots) == 1
    assert any("Food Pressure: HIGH" in event for event in world.events)
    assert any("Farm creation triggered" in event for event in world.events)


def test_activation_scenario_c_high_pressure_grows_farms_gradually_to_cap():
    world = make_resource_poor_world(population=8)
    cap = max_farm_plots_for_population(world.settlement.population)

    counts = []
    for _ in range(4):
        world.advance_day()
        counts.append(len(world.settlement.farm_plots))

    assert counts[0] == 1
    assert counts[1] == 2
    assert all(count <= cap for count in counts)
    assert counts[-1] == cap


def test_activation_scenario_d_no_additional_farms_after_cap():
    world = make_resource_poor_world(population=4)
    cap = max_farm_plots_for_population(world.settlement.population)
    world.settlement.farm_plots.extend(FarmPlot(3 + index * 3, 3) for index in range(cap))

    world.advance_day()

    assert len(world.settlement.farm_plots) == cap


def test_activation_scenario_e_every_created_farm_is_valid_2x2():
    world = make_resource_poor_world(population=8)

    for _ in range(2):
        world.advance_day()

    assert world.settlement.farm_plots
    for farm in world.settlement.farm_plots:
        assert farm.tiles == farm_tiles(farm.origin_x, farm.origin_y)
        assert len(farm.tiles) == 4
        assert is_valid_farm_site_without_self(world, farm)


def test_resource_poor_simulation_update_creates_farm_before_collapse():
    from src.config import TICKS_PER_DAY

    world = make_resource_poor_world(width=18, height=18, population=6)

    for _ in range(TICKS_PER_DAY):
        world.update()

    assert world.day == 2
    assert world.settlement.farm_food_pressure == "HIGH"
    assert len(world.settlement.farm_plots) >= 1
    assert len(world.living_agents()) == 6


def test_farm_growth_occurs_in_warm_seasons_and_slows_in_winter():
    world = make_world()
    farm = FarmPlot(3, 3)

    warm_growth = []
    for season_index in (0, 1, 2):
        world.season_index = season_index
        warm_growth.append(daily_farm_growth(world, farm))

    world.season_index = 3
    winter_growth = daily_farm_growth(world, farm)

    assert all(growth > 0 for growth in warm_growth)
    assert winter_growth < min(warm_growth)


def test_environment_events_affect_farm_growth():
    world = make_world()
    farm = FarmPlot(3, 3)
    normal = daily_farm_growth(world, farm)

    world.active_environment_events = [create_environment_event("drought", 3)]
    drought = daily_farm_growth(world, farm)
    world.active_environment_events = [create_environment_event("heavy_rain", 3)]
    rain = daily_farm_growth(world, farm)

    assert drought < normal
    assert rain > normal


def test_update_farms_produces_food_over_days():
    world = make_world()
    farm = FarmPlot(3, 3)
    world.settlement.farm_plots.append(farm)

    for _ in range(3):
        update_farms(world)

    assert farm.food > 0


def test_harvest_reduces_farm_food_and_increases_carried_food():
    world = make_world()
    farm = FarmPlot(3, 3, food=2)
    world.settlement.farm_plots.append(farm)
    agent = world.agents[0]
    agent.x, agent.y = 3, 3

    HarvestFarmAction().execute(agent, world)

    assert farm.food == 1
    assert agent.food == 1


def test_harvested_food_can_reach_storage():
    world = make_world()
    farm = FarmPlot(3, 3, food=2)
    world.settlement.farm_plots.append(farm)

    assert harvest_farm(world, farm) == 1
    assert world.colony_storage.deposit_food(1) == 1
    assert farm.food == 1
    assert world.colony_storage.food == 1


def test_foragers_are_more_likely_to_harvest_farms_than_builders_or_scouts():
    world = make_world()
    forager = Agent("Fenn", 3, 3, role=FORAGER)
    builder = Agent("Bryn", 3, 3, role=BUILDER)
    scout = Agent("Ira", 3, 3, role=SCOUT)

    action = HarvestFarmAction()

    assert action.score(forager, world) > action.score(builder, world)
    assert action.score(builder, world) > action.score(scout, world)


def test_survival_needs_override_farm_work():
    world = make_world()
    farm = FarmPlot(3, 3, food=2)
    world.settlement.farm_plots.append(farm)
    agent = Agent("Ari", 3, 3, hunger=10, thirst=80, role=FORAGER)
    world.agents = [agent]

    assert not HarvestFarmAction().can_do(agent, world)


def test_reservations_avoid_duplicate_farm_targeting():
    world = make_world()
    farm_a = FarmPlot(3, 3, food=1)
    farm_b = FarmPlot(7, 3, food=1)
    world.settlement.farm_plots.extend([farm_a, farm_b])
    ari = Agent("Ari", 2, 3, hunger=40)
    bryn = Agent("Bryn", 2, 4, hunger=40)
    world.agents = [ari, bryn]

    first = choose_farm_target(world, ari)
    world.reservations.reserve(FARM, first.origin, ari, world)
    second = choose_farm_target(world, bryn)

    assert second is farm_b


def test_critical_hunger_can_override_farm_reservation():
    world = make_world()
    farm = FarmPlot(3, 3, food=1)
    world.settlement.farm_plots.append(farm)
    ari = Agent("Ari", 2, 3)
    bryn = Agent("Bryn", 2, 4, hunger=80)
    world.agents = [ari, bryn]

    world.reservations.reserve(FARM, farm.origin, ari, world)

    assert choose_farm_target(world, bryn) is farm


def test_seek_farm_action_uses_reservation_and_sets_path_target():
    world = make_world()
    farm = FarmPlot(3, 3, food=1)
    world.settlement.farm_plots.append(farm)
    agent = Agent("Fenn", 1, 3, hunger=40, role=FORAGER)
    world.agents = [agent]

    SeekFarmAction().execute(agent, world)

    assert world.reservations.is_reserved(FARM, farm.origin, by_other_than=None)
    assert agent.current_target in farm.tiles


def test_farm_selection_does_not_call_pathfinding(monkeypatch):
    world = make_world()
    world.settlement.farm_plots.append(FarmPlot(3, 3, food=1))
    agent = Agent("Fenn", 1, 3, hunger=40, role=FORAGER)

    def fail_find_path(*args, **kwargs):
        raise AssertionError("farm target scoring must not pathfind")

    monkeypatch.setattr("src.pathfinding.find_path", fail_find_path)

    assert choose_farm_target(world, agent) is not None


def test_farm_border_edges_only_mark_outer_2x2_edges():
    farm = FarmPlot(3, 4)

    assert farm_border_edges(farm, 3, 4) == {"north": True, "south": False, "west": True, "east": False}
    assert farm_border_edges(farm, 4, 5) == {"north": False, "south": True, "west": False, "east": True}


def test_create_world_does_not_spawn_farms_at_founding():
    world = create_world(width=30, height=24, agent_count=4, seed=123)

    assert world.settlement is not None
    assert world.settlement.farm_plots == []


def test_farm_tiles_helper_returns_2x2_footprint():
    assert farm_tiles(5, 6) == [(5, 6), (6, 6), (5, 7), (6, 7)]


def is_valid_farm_site_without_self(world, farm):
    original = list(world.settlement.farm_plots)
    world.settlement.farm_plots = [other for other in original if other is not farm]
    try:
        return is_valid_farm_site(world, farm.origin_x, farm.origin_y)
    finally:
        world.settlement.farm_plots = original
