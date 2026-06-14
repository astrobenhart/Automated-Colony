from __future__ import annotations

from typing import Callable, Protocol


class Overlay(Protocol):
    key: str

    def close(self):
        ...

    def handle_event(self, event) -> bool:
        ...

    def update(self, time_delta: float):
        ...


OverlayFactory = Callable[[], Overlay]


class OverlayManager:
    def __init__(self):
        self.factories: dict[str, OverlayFactory] = {}
        self.active: dict[str, Overlay] = {}

    def register_overlay(self, key: str, factory: OverlayFactory):
        self.factories[key] = factory

    def is_open(self, key: str) -> bool:
        return key in self.active

    def toggle_overlay(self, key: str):
        if self.is_open(key):
            self.close_overlay(key)
            return None
        return self.open_overlay(key)

    def open_overlay(self, key: str):
        if key in self.active:
            return self.active[key]
        if key not in self.factories:
            raise KeyError(f"Unknown overlay: {key}")

        overlay = self.factories[key]()
        self.active[key] = overlay
        return overlay

    def close_overlay(self, key: str):
        overlay = self.active.pop(key, None)
        if overlay is not None:
            overlay.close()

    def close_all(self):
        for key in list(self.active):
            self.close_overlay(key)

    def handle_event(self, event) -> bool:
        consumed = False
        for key, overlay in list(self.active.items()):
            if overlay.handle_event(event):
                consumed = True
            if getattr(overlay, "closed", False):
                self.active.pop(key, None)
        return consumed

    def update(self, time_delta: float):
        for key, overlay in list(self.active.items()):
            overlay.update(time_delta)
            if getattr(overlay, "closed", False):
                self.active.pop(key, None)
