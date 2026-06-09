from __future__ import annotations

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UIScrollingContainer, UIWindow

from src.state import state_label


VILLAGERS_OVERLAY = "villagers"
REFRESH_INTERVAL_SECONDS = 1.0


def living_villagers(world) -> list:
    return [agent for agent in world.living_agents()]


def villager_row_text(agent, world=None) -> str:
    name = getattr(agent, "name", "Villager")
    parts = []
    for attr in ("role", "lifecycle_stage", "trait"):
        value = getattr(agent, attr, None)
        if value:
            parts.append(str(value))

    state = safe_state_label(agent, world)
    if state:
        parts.append(state)

    if not parts:
        return name
    return f"{name} - {' | '.join(parts)}"


def safe_state_label(agent, world=None) -> str | None:
    try:
        return state_label(agent, world)
    except AttributeError:
        return getattr(agent, "current_action", None)


class VillagersOverlay:
    key = VILLAGERS_OVERLAY

    def __init__(self, world, ui_manager, select_agent, rect: pygame.Rect | None = None):
        self.world = world
        self.ui_manager = ui_manager
        self.select_agent = select_agent
        self.closed = False
        self.buttons: dict[UIButton, object] = {}
        self.refresh_timer = 0.0

        window_rect = rect or pygame.Rect(24, 48, 540, 420)
        self.window = UIWindow(
            rect=window_rect,
            manager=ui_manager,
            window_display_title="Villagers",
            object_id="#villagers_overlay",
        )
        self.container = UIScrollingContainer(
            relative_rect=pygame.Rect(8, 8, window_rect.width - 32, window_rect.height - 72),
            manager=ui_manager,
            container=self.window,
        )
        self.refresh()

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.window.kill()

    def handle_event(self, event) -> bool:
        if event.type == pygame_gui.UI_WINDOW_CLOSE and event.ui_element == self.window:
            self.close()
            return True

        if event.type == pygame_gui.UI_BUTTON_PRESSED and event.ui_element in self.buttons:
            agent = self.buttons[event.ui_element]
            if getattr(agent, "alive", False) and agent in self.world.agents:
                self.select_agent(agent)
            return True

        return False

    def update(self, time_delta: float):
        self.refresh_timer += time_delta
        if self.refresh_timer >= REFRESH_INTERVAL_SECONDS:
            self.refresh_timer = 0.0
            self.refresh()

    def refresh(self):
        for button in list(self.buttons):
            button.kill()
        self.buttons.clear()

        row_height = 32
        padding = 4
        villagers = living_villagers(self.world)
        content_height = max(self.container.relative_rect.height, len(villagers) * row_height + padding)
        self.container.set_scrollable_area_dimensions((self.container.relative_rect.width, content_height))

        for index, agent in enumerate(villagers):
            button = UIButton(
                relative_rect=pygame.Rect(
                    padding,
                    padding + index * row_height,
                    self.container.relative_rect.width - padding * 4,
                    row_height - 4,
                ),
                text=villager_row_text(agent, self.world),
                manager=self.ui_manager,
                container=self.container,
            )
            self.buttons[button] = agent
