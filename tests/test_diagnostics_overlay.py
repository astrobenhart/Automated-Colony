import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pygame_gui

from src.diagnostics import diagnostics_sections
from src.overlays.diagnostics import DIAGNOSTICS_OVERLAY, DiagnosticsOverlay
from src.renderer import PygameRenderer
from src.world import create_world


def teardown_function():
    pygame.quit()


def section_map(world):
    return {section.title: dict(section.rows) for section in diagnostics_sections(world, {"last_render_ms": 1.2, "fps": 30})}


def test_diagnostics_sections_cover_generation_debug_categories():
    world = create_world(seed=1901, agent_count=20)
    sections = section_map(world)

    assert {
        "Population",
        "Households",
        "Housing",
        "Partnerships",
        "Births",
        "Resources",
        "Workforce",
        "Mood",
        "Performance",
    } <= set(sections)
    assert "Total Population" in sections["Population"]
    assert "Overcrowded Households" in sections["Households"]
    assert "Pending Expansions" in sections["Housing"]
    assert "Eligible Pairs" in sections["Births"]
    assert "Path Requests" in sections["Performance"]


def test_diagnostics_overlay_opens_with_scrollable_content():
    pygame.init()
    pygame.display.set_mode((800, 600))
    ui_manager = pygame_gui.UIManager((800, 600))
    world = create_world(seed=1902, agent_count=20)

    overlay = DiagnosticsOverlay(
        world,
        ui_manager,
        metrics_provider=lambda: {"last_render_ms": 2.5, "fps": 30},
        rect=pygame.Rect(20, 20, 620, 420),
    )

    texts = [getattr(element, "text", "") for element in overlay.elements]
    assert "Population" in texts
    assert "Households" in texts
    assert "Births" in texts
    assert any("Total Population" in text for text in texts)


def test_diagnostics_overlay_close_event_is_consumed():
    pygame.init()
    pygame.display.set_mode((800, 600))
    ui_manager = pygame_gui.UIManager((800, 600))
    world = create_world(seed=1903, agent_count=20)
    overlay = DiagnosticsOverlay(world, ui_manager, rect=pygame.Rect(20, 20, 620, 420))
    event = pygame.event.Event(pygame_gui.UI_WINDOW_CLOSE, {"ui_element": overlay.window})

    assert overlay.handle_event(event)
    assert overlay.closed


def test_renderer_registers_diagnostics_overlay_toggle():
    pygame.init()
    world = create_world(seed=1904, agent_count=20)
    renderer = PygameRenderer(world)

    renderer.toggle_diagnostics_overlay()

    assert renderer.overlay_manager.is_open(DIAGNOSTICS_OVERLAY)

    renderer.toggle_diagnostics_overlay()

    assert not renderer.overlay_manager.is_open(DIAGNOSTICS_OVERLAY)
