import random

from src.actions import (
    BuildShelterAction,
    DepositFoodAction,
    DepositWoodAction,
    SeekBuildSiteAction,
    SeekFoodStockpileAction,
    WanderAction,
)
from src.agent import Agent
from src.config import COLORS, SETTLEMENT_RADIUS, SYMBOL_LABELS
from src.roles import BUILDER, GENERALIST, SCOUT
from src.settlement import (
    FOOD,
    WOOD,
    Settlement,
    Stockpile,
    central_founding_site,
    distance_to_settlement,
    exploration_radius_for_role,
    is_valid_settlement_site,
    is_adjacent_to_stockpile,
    is_near_settlement,
    nearest_walkable_tile,
    random_tile_near_settlement,
    settlement_site_score,
    stockpile_access_tile,
    valid_build_tile_near_settlement,
)
from src.tile import Tile
from src.world import World, create_world


def make_world(width=8, height=8):
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def test_created_world_has_settlement():
    world = create_world(seed=25)

    assert world.settlement is not None
    assert world.settlement.name
    assert world.settlement.radius == SETTLEMENT_RADIUS


def test_settlement_center_is_walkable_and_not_water_or_mountain():
    world = create_world(seed=26)
    settlement = world.settlement

    tile = world.tile_at(settlement.x, settlement.y)

    assert tile.walkable
    assert tile.kind not in ("water", "mountain")


def test_settlement_center_is_deterministic_for_fixed_seed():
    first = create_world(seed=27)
    second = create_world(seed=27)

    assert (first.settlement.x, first.settlement.y) == (second.settlement.x, second.settlement.y)
    assert first.settlement.name == second.settlement.name


def test_settlement_center_is_near_map_center():
    world = create_world(seed=28)
    settlement = world.settlement
    center_x = world.width // 2
    center_y = world.height // 2

    distance = max(abs(settlement.x - center_x), abs(settlement.y - center_y))

    assert distance <= SETTLEMENT_RADIUS * 2


def test_central_founding_site_uses_nearby_valid_tile_when_center_is_blocked():
    world = make_world(width=9, height=9)
    world.tile_at(4, 4).kind = "water"
    world.tile_at(4, 3).kind = "mountain"

    x, y = central_founding_site(world)

    assert (x, y) != (4, 4)
    assert is_valid_settlement_site(world, x, y)
    assert max(abs(x - 4), abs(y - 4)) <= 1


def test_settlement_site_score_prefers_open_resource_rich_center():
    world = make_world(width=11, height=11)
    world.tile_at(5, 6).kind = "water"
    world.tile_at(6, 5).kind = "forest"
    world.tile_at(6, 5).wood = 2
    world.tile_at(5, 4).food = 1
    for x, y in [(0, 0), (0, 1), (1, 0)]:
        world.tile_at(x, y).kind = "mountain"

    center_score = settlement_site_score(world, 5, 5)
    corner_score = settlement_site_score(world, 1, 1)

    assert center_score < corner_score


def test_settlement_population_reflects_living_agents():
    world = make_world()
    world.agents = [
        Agent("Ari", 1, 1),
        Agent("Bryn", 2, 2),
        Agent("Cato", 3, 3, alive=False),
    ]
    world.establish_settlement()
    world.update_settlement_population()

    assert world.settlement.population == 2


def test_nearest_walkable_tile_skips_water_and_mountain():
    world = make_world(width=3, height=3)
    world.tile_at(1, 1).kind = "water"
    world.tile_at(1, 0).kind = "mountain"

    x, y = nearest_walkable_tile(world, 1, 1)

    assert world.tile_at(x, y).walkable


def test_settlement_marker_is_supported_by_config():
    assert "settlement" in COLORS
    assert SYMBOL_LABELS["+"] == "Settlement"


def test_settlement_distance_and_near_helpers_work():
    world = make_world(width=12, height=12)
    world.settlement = Settlement("Willowhold", 5, 5, 1, "Spring", radius=4)

    assert distance_to_settlement(world, 7, 8) == 3
    assert is_near_settlement(world, 7, 8)
    assert not is_near_settlement(world, 10, 10)


def test_random_tile_near_settlement_avoids_center_and_stays_in_radius():
    world = make_world(width=12, height=12)
    world.settlement = Settlement(
        "Willowhold",
        5,
        5,
        1,
        "Spring",
        radius=4,
        stockpiles=[Stockpile(5, 6, FOOD), Stockpile(6, 5, WOOD)],
    )

    x, y = random_tile_near_settlement(world, random.Random(1), GENERALIST)

    assert (x, y) != (5, 5)
    assert (x, y) not in [(5, 6), (6, 5)]
    assert is_near_settlement(world, x, y)


def test_scouts_have_larger_exploration_radius_than_generalists():
    assert exploration_radius_for_role(SCOUT, 10) > exploration_radius_for_role(GENERALIST, 10)


def test_wander_action_biases_calm_agent_toward_settlement_area():
    world = make_world(width=20, height=20)
    world.settlement = Settlement("Willowhold", 10, 10, 1, "Spring", radius=5)
    agent = Agent("Ari", 1, 1, role=BUILDER)
    world.agents.append(agent)

    WanderAction().execute(agent, world)

    assert agent.current_target is not None
    assert is_near_settlement(
        world,
        agent.current_target[0],
        agent.current_target[1],
        radius=exploration_radius_for_role(BUILDER, world.settlement.radius),
    )


def test_shelter_building_seeks_settlement_build_site_before_building_far_away():
    world = make_world(width=12, height=12)
    world.settlement = Settlement("Willowhold", 6, 6, 1, "Spring", radius=3)
    agent = Agent("Builder", 0, 0, wood=3, role=BUILDER)
    world.agents.append(agent)

    assert valid_build_tile_near_settlement(world, agent) is not None
    assert not BuildShelterAction().can_do(agent, world)
    assert SeekBuildSiteAction().can_do(agent, world)


def test_shelter_building_is_allowed_near_settlement():
    world = make_world(width=12, height=12)
    world.settlement = Settlement("Willowhold", 6, 6, 1, "Spring", radius=3)
    agent = Agent("Builder", 7, 6, wood=3, role=BUILDER)
    world.agents.append(agent)

    assert BuildShelterAction().can_do(agent, world)


def test_survival_goal_overrides_settlement_bias():
    world = make_world(width=12, height=12)
    world.settlement = Settlement("Willowhold", 6, 6, 1, "Spring", radius=3)
    world.tile_at(11, 6).kind = "water"
    agent = Agent("Scout", 6, 6, thirst=80, role=SCOUT)
    agent.remembered_water.add((11, 6))
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Drink"
    assert action.name == "Seeking water"


def test_settlement_activity_tracking_updates():
    world = make_world(width=8, height=8)
    world.settlement = Settlement("Willowhold", 4, 4, 1, "Spring")
    world.agents.append(Agent("Ari", 2, 3))

    world.record_settlement_activity()

    assert world.settlement.activity_at(2, 3) == 1


def test_stockpiles_spawn_near_settlement():
    world = create_world(seed=29)
    settlement = world.settlement

    assert {stockpile.stockpile_type for stockpile in settlement.stockpiles} == {FOOD, WOOD}
    assert len(set((stockpile.x, stockpile.y) for stockpile in settlement.stockpiles)) == 2
    for stockpile in settlement.stockpiles:
        assert world.tile_at(stockpile.x, stockpile.y).walkable
        assert is_near_settlement(world, stockpile.x, stockpile.y)


def test_stockpile_locations_are_deterministic_for_fixed_seed():
    first = create_world(seed=30)
    second = create_world(seed=30)

    first_piles = [(pile.stockpile_type, pile.x, pile.y) for pile in first.settlement.stockpiles]
    second_piles = [(pile.stockpile_type, pile.x, pile.y) for pile in second.settlement.stockpiles]

    assert first_piles == second_piles


def test_food_deposit_updates_storage_and_food_stockpile_from_adjacent_tile():
    world = make_world(width=8, height=8)
    world.settlement = Settlement(
        "Willowhold",
        4,
        4,
        1,
        "Spring",
        stockpiles=[Stockpile(4, 5, FOOD), Stockpile(5, 4, WOOD)],
    )
    agent = Agent("Ari", 3, 5, food=3)
    world.agents.append(agent)

    DepositFoodAction().execute(agent, world)

    assert agent.food == 1
    assert world.colony_storage.food == 2
    assert world.settlement.stockpile_for(FOOD).stored_amount == 2


def test_wood_deposit_updates_storage_and_wood_stockpile_from_adjacent_tile():
    world = make_world(width=8, height=8)
    world.settlement = Settlement(
        "Willowhold",
        4,
        4,
        1,
        "Spring",
        stockpiles=[Stockpile(4, 5, FOOD), Stockpile(5, 4, WOOD)],
    )
    agent = Agent("Bryn", 5, 5, wood=2)
    world.agents.append(agent)

    DepositWoodAction().execute(agent, world)

    assert agent.wood == 0
    assert world.colony_storage.wood == 2
    assert world.settlement.stockpile_for(WOOD).stored_amount == 2


def test_food_carrier_seeks_stockpile_when_not_adjacent():
    world = make_world(width=12, height=12)
    world.settlement = Settlement(
        "Willowhold",
        6,
        6,
        1,
        "Spring",
        stockpiles=[Stockpile(6, 7, FOOD), Stockpile(7, 6, WOOD)],
    )
    agent = Agent("Cato", 1, 1, food=3)
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Deposit food"
    assert isinstance(action, SeekFoodStockpileAction)


def test_existing_deposit_behavior_still_works_without_stockpile():
    world = make_world(width=8, height=8)
    world.settlement = None
    agent = Agent("Dara", 3, 3, food=3)
    world.agents.append(agent)

    assert DepositFoodAction().can_do(agent, world)
    DepositFoodAction().execute(agent, world)

    assert agent.food == 1
    assert world.colony_storage.food == 2


def test_stockpile_access_tile_avoids_occupied_neighbors():
    world = make_world(width=8, height=8)
    world.settlement = Settlement(
        "Willowhold",
        4,
        4,
        1,
        "Spring",
        stockpiles=[Stockpile(4, 5, FOOD), Stockpile(5, 4, WOOD)],
    )
    blocked = Agent("Blocked", 3, 5)
    carrier = Agent("Carrier", 1, 1, food=3)
    world.agents.extend([blocked, carrier])

    target = stockpile_access_tile(world, FOOD, carrier)

    assert target != (blocked.x, blocked.y)
    assert is_adjacent_to_stockpile(world, target[0], target[1], FOOD)
