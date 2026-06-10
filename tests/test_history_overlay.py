import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pygame_gui

from src.agent import Agent
from src.death_memory import DeathRecord
from src.overlays.history import (
    HISTORY_OVERLAY,
    HistoryOverlay,
    active_remembrance_events,
    chronicle_date,
    history_event_lines,
    remembered_dead_card,
    remembered_dead_cards,
)
from src.renderer import PygameRenderer
from src.tile import Tile
from src.world import World
from src.world_history import DEATH, SETTLEMENT


def make_world(width: int = 5, height: int = 5) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def death_record(**overrides) -> DeathRecord:
    values = {
        "name": "Rowan",
        "villager_id": "rowan",
        "role": "Builder",
        "lifecycle_stage": "Elder",
        "trait": "Calm",
        "appearance_seed": 42,
        "appearance_type": "Round",
        "influence_label": "Notable",
        "peak_influence_label": "Respected",
        "cause_of_death": "thirst",
        "day": 12,
        "season": "Summer",
        "year": 2,
        "remembered_by": ["Ari", "Bryn"],
    }
    values.update(overrides)
    return DeathRecord(**values)


def teardown_function():
    pygame.quit()


def test_chronicle_date_prefers_season_and_year():
    assert chronicle_date("Summer", 2, day=42) == "Summer, Year 2"
    assert chronicle_date(None, None, day=42) == "Day 42"
    assert chronicle_date(None, None, day=None) == "Unknown date"


def test_history_event_lines_use_newest_first_ordering():
    world = make_world()
    world.history.record(day=2, year=1, season="Spring", category=SETTLEMENT, title="Old", description="Old event.")
    world.history.record(day=8, year=1, season="Summer", category=DEATH, title="New", description="New event.")

    lines = history_event_lines(world)

    assert lines[0].text == "Summer, Year 1 - New event."
    assert lines[1].text == "Spring, Year 1 - Old event."


def test_empty_history_state_is_story_facing():
    world = make_world()

    assert history_event_lines(world)[0].text == "No notable history yet."


def test_remembrance_events_use_natural_language():
    world = make_world()
    world.day = 2
    ari = Agent("Ari", 1, 1, remembering="Rowan", remembrance_expires_day=5)
    bryn = Agent("Bryn", 2, 1)
    world.agents = [ari, bryn]

    assert active_remembrance_events(world) == ["Ari is remembering Rowan."]
    assert history_event_lines(world)[0].text == "Ari is remembering Rowan."


def test_remembered_dead_card_is_compact_and_story_oriented():
    card = remembered_dead_card(death_record())
    text = [line.text for line in card]

    assert text == [
        "Rowan",
        "Builder • Elder",
        "Respected",
        "Died of thirst",
        "Summer, Year 2",
        "Remembered by: Ari and Bryn",
    ]


def test_remembered_dead_card_handles_missing_optional_fields():
    card = remembered_dead_card(death_record(role=None, lifecycle_stage=None, peak_influence_label="", remembered_by=[]))
    text = [line.text for line in card]

    assert "Rowan" in text
    assert "Died of thirst" in text
    assert "Summer, Year 2" in text
    assert not any("Remembered by" in line for line in text)


def test_empty_remembered_dead_state_is_safe():
    world = make_world()

    cards = remembered_dead_cards(world)

    assert cards[0][0].text == "No remembered dead yet."


def test_remembered_dead_cards_are_newest_first():
    world = make_world()
    world.death_records = [
        death_record(name="Old", day=4, year=1),
        death_record(name="New", day=2, year=2),
    ]

    cards = remembered_dead_cards(world)

    assert cards[0][0].text == "New"
    assert cards[1][0].text == "Old"


def test_history_overlay_opens_with_empty_data_without_crashing():
    pygame.init()
    pygame.display.set_mode((640, 480))
    ui_manager = pygame_gui.UIManager((640, 480))
    world = make_world()

    overlay = HistoryOverlay(world, ui_manager, rect=pygame.Rect(20, 20, 520, 320))

    assert any(getattr(element, "text", "") == "Recent Events" for element in overlay.elements)
    assert any(getattr(element, "text", "") == "No notable history yet." for element in overlay.elements)
    assert any(getattr(element, "text", "") == "People Remembered" for element in overlay.elements)
    assert any(getattr(element, "text", "") == "No remembered dead yet." for element in overlay.elements)


def test_history_overlay_close_event_is_consumed():
    pygame.init()
    pygame.display.set_mode((640, 480))
    ui_manager = pygame_gui.UIManager((640, 480))
    overlay = HistoryOverlay(make_world(), ui_manager, rect=pygame.Rect(20, 20, 520, 320))
    event = pygame.event.Event(pygame_gui.UI_WINDOW_CLOSE, {"ui_element": overlay.window})

    assert overlay.handle_event(event)
    assert overlay.closed


def test_renderer_registers_history_overlay_toggle():
    pygame.init()
    world = make_world()
    renderer = PygameRenderer(world)

    renderer.toggle_history_overlay()

    assert renderer.overlay_manager.is_open(HISTORY_OVERLAY)

    renderer.toggle_history_overlay()

    assert not renderer.overlay_manager.is_open(HISTORY_OVERLAY)
