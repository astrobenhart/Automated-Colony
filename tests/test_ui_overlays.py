import os
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pygame_gui

from src.agent import Agent
from src.overlays.villagers import VillagersOverlay, living_villagers, villager_row_text
from src.tile import Tile
from src.ui_overlays import OverlayManager
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
    selected = []
    overlay = VillagersOverlay(
        world,
        ui_manager,
        selected.append,
        rect=pygame.Rect(20, 20, 360, 240),
    )
    button = next(iter(overlay.buttons))
    event = pygame.event.Event(
        pygame_gui.UI_BUTTON_PRESSED,
        {"ui_element": button},
    )

    consumed = overlay.handle_event(event)

    assert consumed
    assert selected == [agent]


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
        rect=pygame.Rect(20, 20, 360, 240),
    )

    bryn.alive = False
    overlay.refresh()

    assert list(overlay.buttons.values()) == [ari]
