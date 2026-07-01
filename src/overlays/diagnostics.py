from __future__ import annotations

import pygame
import pygame_gui
from pygame_gui.elements import UILabel, UIScrollingContainer, UIWindow

from src.diagnostics import DiagnosticSection, diagnostics_sections


DIAGNOSTICS_OVERLAY = "diagnostics"
REFRESH_INTERVAL_SECONDS = 1.0


class DiagnosticsOverlay:
    key = DIAGNOSTICS_OVERLAY

    def __init__(self, world, ui_manager, metrics_provider=None, rect: pygame.Rect | None = None):
        self.world = world
        self.ui_manager = ui_manager
        self.metrics_provider = metrics_provider or (lambda: {})
        self.closed = False
        self.elements: list = []
        self.refresh_timer = 0.0

        window_rect = rect or pygame.Rect(72, 40, 680, 520)
        self.window = UIWindow(
            rect=window_rect,
            manager=ui_manager,
            window_display_title="Diagnostics",
            object_id="#diagnostics_overlay",
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
        return False

    def update(self, time_delta: float):
        self.refresh_timer += time_delta
        if self.refresh_timer >= REFRESH_INTERVAL_SECONDS:
            self.refresh_timer = 0.0
            self.refresh()

    def refresh(self):
        for element in list(self.elements):
            element.kill()
        self.elements.clear()

        padding = 8
        y = padding
        row_height = 24
        content_width = self.container.relative_rect.width - padding * 4

        for section in diagnostics_sections(self.world, self.metrics_provider()):
            y = self.add_section(section, y, content_width, row_height, padding)
            y += 10

        self.container.set_scrollable_area_dimensions((
            self.container.relative_rect.width,
            max(self.container.relative_rect.height, y + padding),
        ))

    def add_section(self, section: DiagnosticSection, y: int, width: int, row_height: int, padding: int) -> int:
        y = self.add_label(section.title, padding, y, width, row_height, "#diagnostics_section")
        y = self.add_label("-" * 24, padding, y, width, row_height, "#diagnostics_rule")
        for label, value in section.rows:
            y = self.add_label(f"{label:<32} {value}", padding + 8, y, width - 8, row_height, "#diagnostics_row")
        return y

    def add_label(self, text: str, x: int, y: int, width: int, row_height: int, object_id: str) -> int:
        label = UILabel(
            relative_rect=pygame.Rect(x, y, width, row_height),
            text=text,
            manager=self.ui_manager,
            container=self.container,
            object_id=object_id,
        )
        self.elements.append(label)
        return y + row_height
