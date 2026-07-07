from src.agent import Agent
from src.settlement import Home, Household, Settlement, Stockpile
from src.tile import Tile
from src.village_paths import is_path_like
from src.partnerships import partnership_candidates
from src.wanderers import (
    WANDERER_PROFILES,
    ARRIVING,
    DEPARTED,
    DEPARTING,
    SETTLED,
    VISITING,
    advance_wanderer,
    begin_departure,
    profile_destination_candidates,
    profile_for,
    settle_wanderer,
    spawn_wanderer,
)
from src.world import World
from src.world_history import LOCAL_STORY
from src.world_roads import seed_main_roads
from src.workshop import Workshop


def make_world(width: int = 24, height: int = 24) -> World:
    world = World(width, height, seed=4242)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    world.tiles[3][3].kind = "forest"
    world.tiles[3][4].kind = "forest"
    world.tiles[4][3].kind = "forest"
    world.settlement = Settlement("Oakvale", width // 2, height // 2, 1, "Spring", settlement_id="oakvale")
    world.settlement.homes = [Home(width // 2 - 2, height // 2, "home-0")]
    world.settlement.households = [Household("household-0", "Oak Hearth", member_ids=[])]
    world.settlement.stockpiles = [Stockpile(width // 2 + 1, height // 2, "food")]
    world.settlement.workshops = [Workshop(width // 2, height // 2 + 2)]
    seed_main_roads(world, world.settlement)
    return world


def walk_until_status(world: World, wanderer, status: str, limit: int = 40):
    for _ in range(limit):
        if wanderer.visitor_status == status:
            return
        advance_wanderer(world, wanderer)
        world.day += 1
    raise AssertionError(f"{wanderer.name} never reached {status}")


def test_main_roads_generate_from_village_to_map_edges():
    world = make_world()

    assert 2 <= len(world.main_roads) <= 3
    for road in world.main_roads:
        assert road.path[0] == (world.settlement.x, world.settlement.y)
        edge_x, edge_y = road.path[-1]
        assert edge_x in {0, world.width - 1} or edge_y in {0, world.height - 1}
        assert all(world.tile_at(x, y).walkable for x, y in road.path)
        assert any(is_path_like(world.tile_at(x, y).kind) for x, y in road.path[1:])


def test_wanderer_arrives_by_walking_along_a_road():
    world = make_world()
    road = world.main_roads[0]
    wanderer = spawn_wanderer(world, profile_id="storyteller", road_index=0)
    visited_positions = []

    assert wanderer.visitor_status == ARRIVING
    assert (wanderer.x, wanderer.y) == road.edge_anchor
    assert (wanderer.x, wanderer.y) != (world.settlement.x, world.settlement.y)

    while wanderer.visitor_status == ARRIVING:
        advance_wanderer(world, wanderer)
        visited_positions.append((wanderer.x, wanderer.y))
        world.day += 1

    road_positions = set(road.path)
    assert wanderer.visitor_status == VISITING
    assert (wanderer.x, wanderer.y) == road.village_anchor
    assert set(visited_positions).issubset(road_positions)
    assert wanderer.visitor_departure_day == wanderer.visitor_arrival_day + profile_for("storyteller").typical_stay_days


def test_every_wanderer_profile_arrives_with_shared_lifecycle_state():
    for profile_id, profile in WANDERER_PROFILES.items():
        world = make_world()
        wanderer = spawn_wanderer(world, profile_id=profile_id, road_index=0)

        assert wanderer.visitor_status == ARRIVING
        assert wanderer.visitor_profile == profile_id
        assert wanderer.role == profile.role
        assert wanderer.visitor_path[0] == world.main_roads[0].edge_anchor
        walk_until_status(world, wanderer, VISITING)
        assert wanderer.visitor_departure_day == wanderer.visitor_arrival_day + profile.typical_stay_days


def test_profile_definitions_influence_visit_destinations():
    expected_labels = {
        "travelling_merchant": "Storage",
        "hunter": "Forest",
        "scholar": "Workshop",
        "pilgrim": "Road",
        "refugee": "Home",
        "craftsman": "Workshop",
        "storyteller": "Gathering",
    }
    for profile_id, expected in expected_labels.items():
        world = make_world()
        world.agents.append(Agent("Ari", world.settlement.x, world.settlement.y, agent_id="ari", current_action="Idle"))
        world.agents.append(Agent("Bryn", world.settlement.x + 1, world.settlement.y, agent_id="bryn", current_action="Idle"))
        wanderer = spawn_wanderer(world, profile_id=profile_id, road_index=0)
        walk_until_status(world, wanderer, VISITING)

        labels = {label for label, _, _ in profile_destination_candidates(world, wanderer, profile_for(profile_id))}

        assert expected in labels


def test_profile_movement_uses_profile_destinations_without_new_ai_systems():
    world = make_world()
    hunter = spawn_wanderer(world, profile_id="hunter", road_index=0)
    walk_until_status(world, hunter, VISITING)
    previous_distance = abs(hunter.x - 3) + abs(hunter.y - 3)

    advance_wanderer(world, hunter)
    new_distance = abs(hunter.x - 3) + abs(hunter.y - 3)

    assert hunter.current_action == "Using nearby forest"
    assert new_distance < previous_distance


def test_wanderer_departure_uses_the_same_road_to_leave():
    world = make_world()
    road = world.main_roads[0]
    wanderer = spawn_wanderer(world, profile_id="hunter", road_index=0)
    walk_until_status(world, wanderer, VISITING)

    begin_departure(world, wanderer)
    assert wanderer.visitor_status == DEPARTING
    assert wanderer.visitor_path == road.path

    while wanderer.alive:
        advance_wanderer(world, wanderer)
        world.day += 1

    assert wanderer.visitor_status == DEPARTED
    assert (wanderer.x, wanderer.y) == road.edge_anchor
    assert any(entry.category == LOCAL_STORY and entry.title == "Wanderer Departed" for entry in world.history.entries)


def test_wanderer_settlement_reuses_household_and_family_systems():
    world = make_world()
    wanderer = spawn_wanderer(world, profile_id="craftsman", road_index=0)
    walk_until_status(world, wanderer, VISITING)

    household = settle_wanderer(world, wanderer)

    assert household is not None
    assert wanderer.visitor_status == SETTLED
    assert wanderer.household_id == household.household_id
    assert wanderer.home_settlement_id == world.settlement.settlement_id
    assert wanderer.family_id is not None
    assert household in world.settlement.households
    assert any(entry.title == "Wanderer Settled" for entry in world.history.entries)


def test_visitor_memories_track_arrivals_and_settlement():
    world = make_world()
    wanderer = spawn_wanderer(world, profile_id="refugee", road_index=0)
    walk_until_status(world, wanderer, VISITING)
    settle_wanderer(world, wanderer)

    memory = world.visitor_memories[wanderer.agent_id]
    events = [item["event"] for item in memory["events"]]

    assert memory["visits"] == 1
    assert "arrived" in events
    assert "reached the village" in events
    assert "settled" in events


def test_profile_chronicle_entries_are_specific_but_still_shared_framework():
    world = make_world()
    storyteller = spawn_wanderer(world, profile_id="storyteller", road_index=0)
    walk_until_status(world, storyteller, VISITING)

    titles = [entry.title for entry in world.history.entries if entry.category == LOCAL_STORY]

    assert "Wanderer Arrived" in titles
    assert "Storyteller Visit" in titles


def test_temporary_wanderers_do_not_auto_join_households_or_partnership_pool():
    world = make_world()
    wanderer = spawn_wanderer(world, profile_id="scholar", road_index=0)
    walk_until_status(world, wanderer, VISITING)

    world.ensure_household_membership()

    assert wanderer.household_id is None
    assert all(wanderer not in (candidate.first, candidate.second) for candidate in partnership_candidates(world))
