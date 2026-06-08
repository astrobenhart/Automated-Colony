from src.actions import UseWorkshopAction
from src.agent import Agent
from src.building_placement import find_build_site_near_settlement
from src.building_priorities import MATERIALS, SHELTER
from src.reservations import BUILD_SITE, FOOD, WOOD, WORKSHOP
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


def test_reservation_can_be_created_and_released():
    world = make_world()
    agent = Agent("Ari", 1, 1)
    world.agents.append(agent)

    assert world.reservations.reserve(FOOD, (2, 2), agent, world)
    assert world.reservations.is_reserved(FOOD, (2, 2))

    world.reservations.release(FOOD, (2, 2), agent)

    assert not world.reservations.is_reserved(FOOD, (2, 2))


def test_reservation_expires_after_timeout():
    world = make_world()
    agent = Agent("Ari", 1, 1)
    world.agents.append(agent)
    world.tile_at(2, 2).food = 1

    assert world.reservations.reserve(FOOD, (2, 2), agent, world, ttl=1)
    world.tick += 1
    world.reservations.cleanup(world)

    assert not world.reservations.is_reserved(FOOD, (2, 2))


def test_reservation_releases_when_agent_dies():
    world = make_world()
    agent = Agent("Ari", 1, 1)
    world.agents.append(agent)
    world.tile_at(2, 2).food = 1
    world.reservations.reserve(FOOD, (2, 2), agent, world)

    agent.alive = False
    world.reservations.cleanup(world)

    assert not world.reservations.is_reserved(FOOD, (2, 2))


def test_reservation_releases_when_target_is_depleted():
    world = make_world()
    agent = Agent("Ari", 1, 1)
    world.agents.append(agent)
    world.tile_at(2, 2).food = 1
    world.reservations.reserve(FOOD, (2, 2), agent, world)

    world.tile_at(2, 2).food = 0
    world.reservations.cleanup(world)

    assert not world.reservations.is_reserved(FOOD, (2, 2))


def test_another_agent_sees_target_as_reserved():
    world = make_world()
    ari = Agent("Ari", 1, 1)
    bryn = Agent("Bryn", 1, 2)
    world.agents.extend([ari, bryn])
    world.tile_at(2, 2).food = 1

    world.reservations.reserve(FOOD, (2, 2), ari, world)

    assert world.reservations.is_reserved(FOOD, (2, 2), by_other_than=bryn)
    assert not world.reservations.is_reserved(FOOD, (2, 2), by_other_than=ari)


def test_two_agents_prefer_different_food_targets_when_alternatives_exist():
    world = make_world()
    ari = Agent("Ari", 1, 1, hunger=40)
    bryn = Agent("Bryn", 1, 2, hunger=40)
    world.agents.extend([ari, bryn])
    world.tile_at(2, 2).food = 1
    world.tile_at(3, 2).food = 1
    candidates = {(2, 2), (3, 2)}

    first = world.choose_resource_target(ari, "food", candidates)
    world.reservations.reserve(FOOD, first, ari, world)
    second = world.choose_resource_target(bryn, "food", candidates)

    assert second != first


def test_two_agents_prefer_different_wood_targets_when_alternatives_exist():
    world = make_world()
    ari = Agent("Ari", 1, 1)
    bryn = Agent("Bryn", 1, 2)
    world.agents.extend([ari, bryn])
    for pos in [(2, 2), (3, 2)]:
        world.tile_at(*pos).kind = "forest"
        world.tile_at(*pos).wood = 1
    candidates = {(2, 2), (3, 2)}

    first = world.choose_resource_target(ari, "wood", candidates)
    world.reservations.reserve(WOOD, first, ari, world)
    second = world.choose_resource_target(bryn, "wood", candidates)

    assert second != first


def test_build_site_reservation_prevents_duplicate_builder_targeting():
    world = make_world(width=15, height=15)
    ari = Agent("Ari", 1, 1, wood=3)
    bryn = Agent("Bryn", 1, 2, wood=3)
    world.agents.extend([ari, bryn])

    first = find_build_site_near_settlement(world, SHELTER, ari)
    world.reservations.reserve(BUILD_SITE, first, ari, world)
    second = find_build_site_near_settlement(world, SHELTER, bryn)

    assert second != first


def test_workshop_reservation_limits_crowding():
    world = make_world()
    ari = Agent("Ari", world.settlement.x - 2, world.settlement.y)
    bryn = Agent("Bryn", world.settlement.x - 2, world.settlement.y + 1)
    world.agents.extend([ari, bryn])
    world.colony_storage.deposit_wood(10)
    world.settlement.need_scores = {SHELTER: 0, WOOD: 0, MATERIALS: 80}
    world.settlement.top_need = MATERIALS
    world.settlement.need_updated_day = world.day
    workshop = world.settlement.workshops[0]

    assert world.reservations.reserve(WORKSHOP, (workshop.x, workshop.y), ari, world)

    assert not UseWorkshopAction().can_do(bryn, world)


def test_critical_hunger_can_override_food_reservation_when_no_alternatives_exist():
    world = make_world()
    ari = Agent("Ari", 1, 1)
    bryn = Agent("Bryn", 1, 2, hunger=80)
    world.agents.extend([ari, bryn])
    world.tile_at(2, 2).food = 1
    world.reservations.reserve(FOOD, (2, 2), ari, world)

    assert world.choose_resource_target(bryn, "food", {(2, 2)}) == (2, 2)


def test_no_progress_recovery_releases_reservations():
    world = make_world()
    agent = Agent("Ari", 1, 1)
    world.agents.append(agent)
    world.tile_at(2, 2).food = 1
    world.reservations.reserve(FOOD, (2, 2), agent, world)
    before = agent.progress_snapshot(world)

    for _ in range(5):
        agent.update_progress_tracking(world, before)

    assert agent.current_action == "Recovering"
    assert not world.reservations.is_reserved(FOOD, (2, 2))


def test_reservation_checks_do_not_call_pathfinding(monkeypatch):
    world = make_world()
    ari = Agent("Ari", 1, 1)
    bryn = Agent("Bryn", 1, 2)
    world.agents.extend([ari, bryn])
    world.tile_at(2, 2).food = 1

    def fail_find_path(*args, **kwargs):
        raise AssertionError("reservation checks must not pathfind")

    monkeypatch.setattr("src.pathfinding.find_path", fail_find_path)

    world.reservations.reserve(FOOD, (2, 2), ari, world)
    assert world.choose_resource_target(bryn, "food", {(2, 2)}) is None
