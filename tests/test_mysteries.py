import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from src.agent import Agent
from src.diagnostics import diagnostics_sections
from src.gatherings import gathering_destinations, gathering_wander_target
from src.mysteries import (
    STRANGE_LIGHTS,
    active_strange_lights,
    maybe_start_mystery,
    mystery_destination,
    update_mysteries,
)
from src.renderer import PygameRenderer
from src.settlement import Settlement
from src.shared_moments import current_shared_moment, update_shared_moments
from src.tile import Tile
from src.world import World
from src.world_history import MYSTERY


class SequenceRandom:
    def __init__(self, values, randint_value: int = 3):
        self.values = list(values)
        self.randint_value = randint_value

    def random(self):
        return self.values.pop(0) if self.values else 0.0

    def randint(self, _low, _high):
        return self.randint_value


def make_world(width: int = 14, height: int = 14) -> World:
    world = World(width, height, seed=909)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    world.settlement = Settlement("Oakvale", width // 2, height // 2, 1, "Spring", settlement_id="oakvale")
    for y in range(2, 5):
        for x in range(2, 5):
            world.tiles[y][x] = Tile("water")
    for y in range(8, 11):
        world.tiles[y][10] = Tile("forest")
    return world


def teardown_function():
    pygame.quit()


def test_strange_lights_generate_correctly_and_record_chronicle():
    world = make_world()
    witness = Agent("Ari Vale", 3, 5, agent_id="ari", current_action="Idle")
    world.agents = [witness]

    mystery = maybe_start_mystery(world, SequenceRandom([0.0, 0.0], randint_value=2))

    assert mystery is not None
    assert mystery.mystery_type == STRANGE_LIGHTS
    assert mystery in world.active_mysteries
    assert active_strange_lights(world) == mystery
    assert any(entry.category == MYSTERY and entry.title == "Strange Lights" for entry in world.history.entries)
    assert any("strange lights" in memory.lower() for memory in witness.personal_memories)


def test_strange_lights_use_environmental_overlay_without_terrain_cache_state():
    world = make_world()
    maybe_start_mystery(world, SequenceRandom([0.0, 0.0], randint_value=2))
    renderer = PygameRenderer(world)
    start_key = renderer.visual_transition_cache_state()
    overlay_state = renderer.environmental_overlay_state()
    calls = []

    renderer.draw_mystery_lights_overlay = lambda: calls.append("lights")
    renderer.draw_cloud_shadow_overlay = lambda: calls.append("clouds")
    renderer.draw_environmental_overlay_layer()

    assert renderer.visual_transition_cache_state() == start_key
    assert "strange_lights" in str(overlay_state)
    assert calls == ["clouds", "lights"]


def test_villagers_react_through_existing_gathering_and_shared_moment_systems():
    world = make_world()
    ari = Agent("Ari Vale", 7, 7, agent_id="ari", current_action="Idle")
    bryn = Agent("Bryn Vale", 8, 7, agent_id="bryn", current_action="Idle")
    world.agents = [ari, bryn]
    mystery = maybe_start_mystery(world, SequenceRandom([0.0, 0.0], randint_value=2))
    assert mystery is not None

    destinations = gathering_destinations(ari, world, random.Random(2))
    target = gathering_wander_target(ari, world, random.Random(2))
    ari.x, ari.y = mystery.anchor
    bryn.x, bryn.y = mystery.anchor[0] + 1, mystery.anchor[1]
    update_shared_moments(world)

    assert mystery_destination(world)[0] == "Mystery: Strange Lights"
    assert destinations[0].label == "Mystery: Strange Lights"
    assert target is not None
    assert current_shared_moment(ari, world) == "Watching"
    assert current_shared_moment(bryn, world) == "Watching"


def test_mystery_memories_are_recorded_once_per_witness():
    world = make_world()
    witness = Agent("Ari Vale", 3, 5, agent_id="ari", current_action="Idle")
    world.agents = [witness]

    update_mysteries(world, SequenceRandom([0.0, 0.0], randint_value=2))
    update_mysteries(world, SequenceRandom([1.0], randint_value=2))

    memories = [memory for memory in witness.personal_memories if "strange lights" in memory.lower()]
    assert len(memories) == 1


def test_mystery_diagnostics_report_active_lights():
    world = make_world()
    maybe_start_mystery(world, SequenceRandom([0.0, 0.0], randint_value=2))

    sections = {section.title: dict(section.rows) for section in diagnostics_sections(world)}

    assert sections["Mysteries"]["Active Mysteries"] == "Strange Lights"
    assert sections["Mysteries"]["Mystery Count"] == 1
