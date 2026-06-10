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
        ("Status", status_rows(agent, world)),
        ("Familiar With", familiarity_rows(agent)),
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
    role_life = " · ".join(
        str(value)
        for value in (
            getattr(agent, "role", None),
            getattr(agent, "lifecycle_stage", None),
        )
        if value
    )
    return present_rows([
        ("Name", getattr(agent, "name", None)),
        ("Role", role_life),
        ("Trait", getattr(agent, "trait", None)),
    ])


def status_rows(agent, world=None) -> list[tuple[str, object]]:
    return [
        ("State", safe_state_label(agent, world) or "Unknown"),
        ("Influence", influence_label(agent, world)),
    ]


def familiarity_rows(agent) -> list[tuple[str, object]]:
    if not hasattr(agent, "social_memory"):
        return [("", "None")]

    names = [
        item.split(" (", 1)[0]
        for item in familiarity_summary(agent)
    ]
    if not names:
        return [("", "None")]
    return [("", name) for name in names]


def present_rows(rows: list[tuple[str, object | None]]) -> list[tuple[str, object]]:
    return [(label, value) for label, value in rows if value not in (None, "")]
