from __future__ import annotations

import pygame
import pygame_gui
from pygame_gui.elements import UIButton, UILabel, UIScrollingContainer, UIWindow

from src.villager_inspection import villager_detail_sections, villager_row_text


VILLAGERS_OVERLAY = "villagers"
REFRESH_INTERVAL_SECONDS = 1.0


def living_villagers(world) -> list:
    return [agent for agent in world.living_agents()]


class VillagersOverlay:
    key = VILLAGERS_OVERLAY

    def __init__(self, world, ui_manager, select_agent, get_selected_agent=None, rect: pygame.Rect | None = None):
        self.world = world
        self.ui_manager = ui_manager
        self.select_agent = select_agent
        self.get_selected_agent = get_selected_agent or (lambda: None)
        self.closed = False
        self.buttons: dict[UIButton, object] = {}
        self.detail_labels: list[UILabel] = []
        self.refresh_timer = 0.0

        window_rect = rect or pygame.Rect(24, 48, 760, 460)
        content_height = window_rect.height - 72
        list_width = 320
        detail_x = list_width + 20
        self.window = UIWindow(
            rect=window_rect,
            manager=ui_manager,
            window_display_title="Villagers",
            object_id="#villagers_overlay",
        )
        self.list_container = UIScrollingContainer(
            relative_rect=pygame.Rect(8, 8, list_width, content_height),
            manager=ui_manager,
            container=self.window,
        )
        self.details_container = UIScrollingContainer(
            relative_rect=pygame.Rect(detail_x, 8, window_rect.width - detail_x - 24, content_height),
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
                self.refresh_details()
            return True

        return False

    def update(self, time_delta: float):
        self.refresh_timer += time_delta
        if self.refresh_timer >= REFRESH_INTERVAL_SECONDS:
            self.refresh_timer = 0.0
            self.refresh()

    def refresh(self):
        self.refresh_list()
        self.refresh_details()

    def refresh_list(self):
        for button in list(self.buttons):
            button.kill()
        self.buttons.clear()

        row_height = 32
        padding = 4
        villagers = living_villagers(self.world)
        content_height = max(self.list_container.relative_rect.height, len(villagers) * row_height + padding)
        self.list_container.set_scrollable_area_dimensions((self.list_container.relative_rect.width, content_height))

        for index, agent in enumerate(villagers):
            button = UIButton(
                relative_rect=pygame.Rect(
                    padding,
                    padding + index * row_height,
                    self.list_container.relative_rect.width - padding * 4,
                    row_height - 4,
                ),
                text=villager_row_text(agent, self.world),
                manager=self.ui_manager,
                container=self.list_container,
            )
            self.buttons[button] = agent

    def refresh_details(self):
        for label in list(self.detail_labels):
            label.kill()
        self.detail_labels.clear()

        selected = self.selected_living_agent()
        sections = villager_detail_sections(selected, self.world)
        y = 4
        padding = 6
        row_height = 24
        content_width = self.details_container.relative_rect.width - padding * 4

        for section_title, rows in sections:
            title = UILabel(
                relative_rect=pygame.Rect(padding, y, content_width, row_height),
                text=section_title,
                manager=self.ui_manager,
                container=self.details_container,
            )
            self.detail_labels.append(title)
            y += row_height

            for label, value in rows:
                detail = UILabel(
                    relative_rect=pygame.Rect(padding + 8, y, content_width - 8, row_height),
                    text=f"{label}: {value}",
                    manager=self.ui_manager,
                    container=self.details_container,
                )
                self.detail_labels.append(detail)
                y += row_height

            y += 8

        self.details_container.set_scrollable_area_dimensions((
            self.details_container.relative_rect.width,
            max(self.details_container.relative_rect.height, y + padding),
        ))

    def selected_living_agent(self):
        selected = self.get_selected_agent()
        if selected is not None and getattr(selected, "alive", False) and selected in self.world.agents:
            return selected
        return None
