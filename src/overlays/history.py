from __future__ import annotations

from dataclasses import dataclass

import pygame
import pygame_gui
from pygame_gui.elements import UILabel, UIScrollingContainer, UIWindow

from src.death_memory import DeathRecord, active_remembrance_name, format_names, villager_history_name


HISTORY_OVERLAY = "history"
REFRESH_INTERVAL_SECONDS = 1.0


@dataclass(frozen=True)
class ChronicleLine:
    text: str
    style: str = "body"


def chronicle_date(season: str | None, year: int | None, day: int | None = None) -> str:
    if season and year:
        return f"{season}, Year {year}"
    if day is not None:
        return f"Day {day}"
    return "Unknown date"


def history_event_lines(world, limit: int = 12) -> list[ChronicleLine]:
    lines = []
    for description in active_remembrance_events(world):
        lines.append(ChronicleLine(description))

    entries = list(getattr(world.history, "entries", []))
    entries.sort(key=lambda entry: (entry.year, entry.day, entry.title), reverse=True)
    for entry in entries[:limit]:
        date = chronicle_date(entry.season, entry.year, entry.day)
        description = entry.description or entry.title
        lines.append(ChronicleLine(f"{date} - {description}"))

    if not lines:
        return [ChronicleLine("No notable history yet.", "muted")]
    return lines


def active_remembrance_events(world) -> list[str]:
    events = []
    for agent in world.living_agents():
        remembered = active_remembrance_name(agent, world)
        if remembered:
            events.append(f"{agent_chronicle_name(agent)} is remembering {remembered}.")
    return sorted(events)


def remembered_dead_cards(world) -> list[list[ChronicleLine]]:
    records = list(getattr(world, "death_records", []))
    records.sort(key=lambda record: (record.year, record.day, record.name), reverse=True)
    if not records:
        return [[ChronicleLine("No remembered dead yet.", "muted")]]
    return [remembered_dead_card(record) for record in records]


def remembered_dead_card(record: DeathRecord) -> list[ChronicleLine]:
    identity = " • ".join(
        str(value)
        for value in (record.role, record.lifecycle_stage)
        if value
    )
    lines = [ChronicleLine(villager_history_name(record), "title")]
    if identity:
        lines.append(ChronicleLine(identity, "muted"))
    if record.peak_influence_label:
        lines.append(ChronicleLine(record.peak_influence_label))
    lines.append(ChronicleLine(f"Died of {record.cause_of_death}"))
    lines.append(ChronicleLine(chronicle_date(record.season, record.year, record.day), "muted"))
    if record.remembered_by:
        lines.append(ChronicleLine(f"Remembered by: {format_names(record.remembered_by)}"))
    return lines


def agent_chronicle_name(agent) -> str:
    settlement_name = getattr(agent, "home_settlement_name", None)
    if settlement_name:
        return f"{agent.name} of {settlement_name}"
    return agent.name


class HistoryOverlay:
    key = HISTORY_OVERLAY

    def __init__(self, world, ui_manager, rect: pygame.Rect | None = None):
        self.world = world
        self.ui_manager = ui_manager
        self.closed = False
        self.elements: list = []
        self.refresh_timer = 0.0

        window_rect = rect or pygame.Rect(56, 56, 640, 460)
        self.window = UIWindow(
            rect=window_rect,
            manager=ui_manager,
            window_display_title="History",
            object_id="#history_overlay",
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
        content_width = self.container.relative_rect.width - padding * 4
        row_height = 24

        y = self.add_section("Recent Events", y, content_width, row_height, padding)
        for line in history_event_lines(self.world):
            y = self.add_line(line, y, content_width, row_height, padding + 8)
        y += 12

        y = self.add_section("People Remembered", y, content_width, row_height, padding)
        cards = remembered_dead_cards(self.world)
        for card in cards:
            for line in card:
                y = self.add_line(line, y, content_width, row_height, padding + 8)
            y += 10

        self.container.set_scrollable_area_dimensions((
            self.container.relative_rect.width,
            max(self.container.relative_rect.height, y + padding),
        ))

    def add_section(self, text: str, y: int, width: int, row_height: int, x: int) -> int:
        return self.add_label(ChronicleLine(text, "section"), x, y, width, row_height) + 4

    def add_line(self, line: ChronicleLine, y: int, width: int, row_height: int, x: int) -> int:
        return self.add_label(line, x, y, width, row_height)

    def add_label(self, line: ChronicleLine, x: int, y: int, width: int, row_height: int) -> int:
        label = UILabel(
            relative_rect=pygame.Rect(x, y, width, row_height),
            text=line.text,
            manager=self.ui_manager,
            container=self.container,
            object_id=f"#chronicle_{line.style}",
        )
        self.elements.append(label)
        return y + row_height
