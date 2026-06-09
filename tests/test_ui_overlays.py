import os
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pygame_gui

from src.agent import Agent
from src.overlays.villagers import VillagersOverlay, living_villagers, villager_row_text
from src.social_memory import SocialMemoryEntry
from src.tile import Tile
from src.ui_overlays import OverlayManager
from src.villager_inspection import compact_villager_rows, villager_detail_sections
from src.world import World


def make_world(width: int = 5, height: int = 5) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def teardown_function():
    pygame.quit()


def test_villager_row_format_includes_identity_fields():
    agent = Agent(
        "Ari",
        1,
        1,
        role="Forager",
        lifecycle_stage="Adult",
        trait="Curious",
        current_action="Idle",
    )

    row = villager_row_text(agent)

    assert row == "Ari - Forager | Adult | Curious | Content"


def test_villager_row_format_handles_missing_identity_fields():
    villager = SimpleNamespace(name="Mystery", current_action="Idle")

    assert villager_row_text(villager) == "Mystery - Idle"


def test_living_villager_list_excludes_dead_villagers():
    world = make_world()
    ari = Agent("Ari", 1, 1)
    bryn = Agent("Bryn", 2, 1, alive=False)
    world.agents = [ari, bryn]

    assert living_villagers(world) == [ari]


def test_overlay_manager_registers_and_toggles_overlay():
    manager = OverlayManager()
    created = []

    class DummyOverlay:
        key = "dummy"
        closed = False

        def close(self):
            self.closed = True

        def handle_event(self, event):
            return False

        def update(self, time_delta):
            pass

    manager.register_overlay("dummy", lambda: created.append(DummyOverlay()) or created[-1])

    overlay = manager.toggle_overlay("dummy")

    assert overlay is created[0]
    assert manager.is_open("dummy")

    manager.toggle_overlay("dummy")

    assert not manager.is_open("dummy")
    assert overlay.closed


def test_villagers_overlay_button_selects_existing_villager():
    pygame.init()
    pygame.display.set_mode((640, 480))
    ui_manager = pygame_gui.UIManager((640, 480))
    world = make_world()
    agent = Agent("Ari", 1, 1)
    world.agents = [agent]
    selected = {"agent": None}
    overlay = VillagersOverlay(
        world,
        ui_manager,
        lambda selected_agent: selected.update(agent=selected_agent),
        lambda: selected["agent"],
        rect=pygame.Rect(20, 20, 520, 260),
    )
    button = next(iter(overlay.buttons))
    event = pygame.event.Event(
        pygame_gui.UI_BUTTON_PRESSED,
        {"ui_element": button},
    )

    consumed = overlay.handle_event(event)

    assert consumed
    assert selected["agent"] is agent
    assert overlay.selected_living_agent() is agent


def test_villagers_overlay_refresh_removes_dead_villager():
    pygame.init()
    pygame.display.set_mode((640, 480))
    ui_manager = pygame_gui.UIManager((640, 480))
    world = make_world()
    ari = Agent("Ari", 1, 1)
    bryn = Agent("Bryn", 2, 1)
    world.agents = [ari, bryn]
    overlay = VillagersOverlay(
        world,
        ui_manager,
        lambda agent: None,
        rect=pygame.Rect(20, 20, 520, 260),
    )

    bryn.alive = False
    overlay.refresh()

    assert list(overlay.buttons.values()) == [ari]


def test_villager_detail_sections_include_player_facing_fields():
    agent = Agent(
        "Ari",
        1,
        1,
        role="Forager",
        lifecycle_stage="Adult",
        trait="Curious",
        hunger=12,
        thirst=8,
        fatigue=3,
        food=1,
        wood=2,
        current_action="Gathering food",
        current_goal="Gather food",
    )
    agent.social_memory["bryn"] = SocialMemoryEntry(
        villager_id="bryn",
        display_name="Bryn",
        familiarity_score=30,
        last_seen_day=30,
    )

    sections = dict(villager_detail_sections(agent))

    assert ("Name", "Ari") in sections["Identity"]
    assert ("Role", "Forager") in sections["Identity"]
    assert ("Life", "Adult") in sections["Identity"]
    assert ("Trait", "Curious") in sections["Identity"]
    assert ("State", "Working") in sections["Identity"]
    assert ("Hunger", 12) in sections["Needs"]
    assert ("Thirst", 8) in sections["Needs"]
    assert ("Fatigue", 3) in sections["Needs"]
    assert ("Action", "Gathering food") in sections["Activity"]
    assert ("Goal", "Gather food") in sections["Activity"]
    assert ("Food", 1) in sections["Inventory"]
    assert ("Wood", 2) in sections["Inventory"]
    assert ("Knows", "Bryn (Familiar)") in sections["Social"]


def test_villager_detail_sections_handle_missing_optional_fields():
    villager = SimpleNamespace(name="Mystery", current_action="Idle")

    sections = dict(villager_detail_sections(villager))

    assert ("Name", "Mystery") in sections["Identity"]
    assert ("Role", "Unknown") not in sections["Identity"]
    assert ("State", "Idle") in sections["Identity"]
    assert ("Food", 0) in sections["Inventory"]
    assert ("Wood", 0) in sections["Inventory"]
    assert ("Knows", "None") in sections["Social"]


def test_compact_villager_rows_keep_right_panel_short():
    agent = Agent("Ari", 1, 1, role="Scout", current_action="Wandering")

    rows = compact_villager_rows(agent)

    assert rows == [
        ("Agent", "Ari"),
        ("Role", "Scout"),
        ("State", "Exploring"),
        ("Action", "Wandering"),
    ]


def test_open_overlay_details_follow_map_selection():
    pygame.init()
    pygame.display.set_mode((640, 480))
    ui_manager = pygame_gui.UIManager((640, 480))
    world = make_world()
    ari = Agent("Ari", 1, 1)
    bryn = Agent("Bryn", 2, 1)
    world.agents = [ari, bryn]
    selected = {"agent": ari}
    overlay = VillagersOverlay(
        world,
        ui_manager,
        lambda agent: selected.update(agent=agent),
        lambda: selected["agent"],
        rect=pygame.Rect(20, 20, 640, 280),
    )

    selected["agent"] = bryn
    overlay.refresh_details()

    assert overlay.selected_living_agent() is bryn
    assert any(getattr(label, "text", "") == "Name: Bryn" for label in overlay.detail_labels)
