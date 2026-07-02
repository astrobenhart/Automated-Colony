import random

from src.agent import Agent
from src.celebrations import (
    OPEN_CREMATION,
    active_celebration,
    celebration_attendees,
    celebration_diagnostics,
)
from src.config import TASK_HUNGER_INTERRUPT_THRESHOLD
from src.death_memory import record_death
from src.diagnostics import diagnostics_sections
from src.gatherings import gathering_destinations, gathering_wander_target
from src.settlement import Household, Settlement
from src.shared_moments import current_shared_moment, update_shared_moments
from src.tile import Tile
from src.villager_inspection import villager_detail_sections
from src.world import World
from src.world_history import LOCAL_STORY


def make_world(width: int = 24, height: int = 24) -> World:
    world = World(width, height, seed=90210)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    world.settlement = Settlement("Oakvale", 12, 12, 1, "Spring", settlement_id="oakvale")
    return world


def test_respected_death_starts_open_cremation_and_chronicle_entry():
    world = make_world()
    rowan = Agent("Rowan", 12, 12, agent_id="rowan", peak_influence_score=24, lifecycle_stage="Elder")
    ari = Agent("Ari", 13, 12, agent_id="ari")
    world.agents = [rowan, ari]

    record_death(world, rowan, "old age")

    celebration = active_celebration(world)
    assert celebration is not None
    assert celebration.celebration_type == OPEN_CREMATION
    assert celebration.honoree_id == "rowan"
    assert celebration.honoree_name == "Rowan"
    assert len(world.celebration_history) == 1
    assert any(entry.category == LOCAL_STORY and entry.title == "Open Cremation" for entry in world.history.entries)


def test_non_respected_death_does_not_start_open_cremation():
    world = make_world()
    rowan = Agent("Rowan", 12, 12, agent_id="rowan", lifecycle_stage="Adult")
    ari = Agent("Ari", 13, 12, agent_id="ari")
    world.agents = [rowan, ari]

    record_death(world, rowan, "thirst")

    assert active_celebration(world) is None
    assert not any(entry.title == "Open Cremation" for entry in world.history.entries)


def test_celebration_location_becomes_attractive_without_special_movement():
    world = make_world()
    rowan = Agent("Rowan", 12, 12, agent_id="rowan", peak_influence_score=24, lifecycle_stage="Elder")
    partner = Agent("Ari", 3, 3, agent_id="ari", partner_id="rowan", current_action="Idle")
    world.agents = [rowan, partner]

    record_death(world, rowan, "old age")
    celebration = active_celebration(world)
    destinations = gathering_destinations(partner, world, random.Random(1))
    target = gathering_wander_target(partner, world, random.Random(1))

    assert celebration is not None
    assert destinations[0].label.startswith("Ceremony:")
    assert target is not None
    assert max(abs(target[0] - celebration.anchor[0]), abs(target[1] - celebration.anchor[1])) <= 1


def test_open_cremation_attendance_favours_relationships_but_never_forces_urgent_villagers():
    world = make_world()
    world.settlement.households = [
        Household("household-1", "Rowan House", member_ids=["rowan", "ari"], historical_member_ids=["rowan", "ari"])
    ]
    rowan = Agent("Rowan", 12, 12, agent_id="rowan", peak_influence_score=24, lifecycle_stage="Elder", household_id="household-1")
    ari = Agent("Ari", 3, 3, agent_id="ari", partner_id="rowan", current_action="Idle", household_id="household-1")
    bryn = Agent("Bryn", 4, 4, agent_id="bryn", current_action="Idle", hunger=TASK_HUNGER_INTERRUPT_THRESHOLD)
    cato = Agent("Cato", 5, 5, agent_id="cato", current_action="Idle")
    world.agents = [rowan, ari, bryn, cato]

    record_death(world, rowan, "old age")
    celebration = active_celebration(world)
    assert celebration is not None
    ari.x, ari.y = celebration.anchor
    bryn.x, bryn.y = celebration.anchor

    attendees = {agent.name for agent in celebration_attendees(world)}

    assert "Ari" in attendees
    assert "Bryn" not in attendees


def test_shared_moments_work_at_open_cremations():
    world = make_world()
    rowan = Agent("Rowan", 12, 12, agent_id="rowan", peak_influence_score=24, lifecycle_stage="Elder")
    ari = Agent("Ari", 3, 3, agent_id="ari", partner_id="rowan", current_action="Idle")
    bryn = Agent("Bryn", 4, 3, agent_id="bryn", current_action="Idle")
    world.agents = [rowan, ari, bryn]

    record_death(world, rowan, "old age")
    celebration = active_celebration(world)
    assert celebration is not None
    ari.x, ari.y = celebration.anchor
    bryn.x, bryn.y = celebration.anchor[0] + 1, celebration.anchor[1]

    update_shared_moments(world)

    assert current_shared_moment(ari, world) in {"Warming", "Watching", "Conversation", "Resting"}
    assert current_shared_moment(bryn, world) == current_shared_moment(ari, world)


def test_celebration_diagnostics_and_inspection_expose_ceremony_status():
    world = make_world()
    rowan = Agent("Rowan", 12, 12, agent_id="rowan", peak_influence_score=24, lifecycle_stage="Elder")
    ari = Agent("Ari", 3, 3, agent_id="ari", partner_id="rowan", current_action="Idle")
    world.agents = [rowan, ari]

    record_death(world, rowan, "old age")
    celebration = active_celebration(world)
    assert celebration is not None
    ari.x, ari.y = celebration.anchor

    rows = dict(celebration_diagnostics(world))
    sections = dict(villager_detail_sections(ari, world))
    diagnostics = {section.title: dict(section.rows) for section in diagnostics_sections(world)}

    assert rows["Active Celebration"] == celebration.title
    assert rows["Villagers Attending"] == 1
    assert rows["Celebration History"] == 1
    assert ("Current Ceremony", celebration.title) in sections["Status"]
    assert ("Ceremony Status", "Attending") in sections["Status"]
    assert diagnostics["Celebrations"]["Active Celebration"] == celebration.title


def test_celebrations_expire_without_leaving_active_state():
    world = make_world()
    rowan = Agent("Rowan", 12, 12, agent_id="rowan", peak_influence_score=24, lifecycle_stage="Elder")
    ari = Agent("Ari", 13, 12, agent_id="ari")
    world.agents = [rowan, ari]

    record_death(world, rowan, "old age")
    assert active_celebration(world) is not None
    world.day += 4
    world.run_daily_updates()

    assert active_celebration(world) is None
    assert world.active_celebration is None
