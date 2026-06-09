from __future__ import annotations

from src.influence import influence_label
from src.social_memory import familiarity_summary
from src.state import state_label


def safe_state_label(agent, world=None) -> str | None:
    try:
        return state_label(agent, world)
    except AttributeError:
        return getattr(agent, "current_action", None)


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


def villager_detail_sections(agent, world=None) -> list[tuple[str, list[tuple[str, object]]]]:
    if agent is None:
        return [("Selection", [("Selected", "None")])]

    return [
        ("Identity", identity_rows(agent, world)),
        ("Needs", needs_rows(agent)),
        ("Activity", activity_rows(agent)),
        ("Inventory", inventory_rows(agent)),
        ("Social", social_rows(agent, world)),
    ]


def compact_villager_rows(agent, world=None) -> list[tuple[str, object]]:
    if agent is None:
        return [("Selected", "None")]

    return [
        ("Agent", getattr(agent, "name", "Villager")),
        ("Role", getattr(agent, "role", "Unknown")),
        ("State", safe_state_label(agent, world) or "Unknown"),
        ("Action", getattr(agent, "current_action", "Unknown")),
    ]


def identity_rows(agent, world=None) -> list[tuple[str, object]]:
    return present_rows([
        ("Name", getattr(agent, "name", None)),
        ("Role", getattr(agent, "role", None)),
        ("Life", getattr(agent, "lifecycle_stage", None)),
        ("Trait", getattr(agent, "trait", None)),
        ("State", safe_state_label(agent, world)),
    ])


def needs_rows(agent) -> list[tuple[str, object]]:
    return [
        ("Hunger", getattr(agent, "hunger", "Unknown")),
        ("Thirst", getattr(agent, "thirst", "Unknown")),
        ("Fatigue", getattr(agent, "fatigue", "Unknown")),
    ]


def activity_rows(agent) -> list[tuple[str, object]]:
    return [
        ("Action", getattr(agent, "current_action", "Unknown")),
        ("Goal", getattr(agent, "current_goal", "Unknown")),
    ]


def inventory_rows(agent) -> list[tuple[str, object]]:
    return [
        ("Food", getattr(agent, "food", 0)),
        ("Wood", getattr(agent, "wood", 0)),
    ]


def social_rows(agent, world=None) -> list[tuple[str, object]]:
    summary = ", ".join(familiarity_summary(agent)) if hasattr(agent, "social_memory") else ""
    return [
        ("Influence", influence_label(agent, world)),
        ("Knows", summary or "None"),
    ]


def present_rows(rows: list[tuple[str, object | None]]) -> list[tuple[str, object]]:
    return [(label, value) for label, value in rows if value not in (None, "")]
