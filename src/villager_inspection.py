from __future__ import annotations

from src.death_memory import active_remembrance_name
from src.influence import influence_label
from src.social_bonds import social_bonds
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
        ("Bonds", bond_rows(agent)),
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
        ("Home", getattr(agent, "home_settlement_name", None)),
    ])


def status_rows(agent, world=None) -> list[tuple[str, object]]:
    rows = [
        ("State", safe_state_label(agent, world) or "Unknown"),
        ("Influence", influence_label(agent, world)),
    ]
    remembering = active_remembrance_name(agent, world)
    if remembering:
        rows.append(("Remembering", remembering))
    return rows


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


def bond_rows(agent) -> list[tuple[str, object]]:
    bonds = social_bonds(agent)
    if not bonds:
        return [("", "None")]
    return [(bond.label, bond.name) for bond in bonds]


def present_rows(rows: list[tuple[str, object | None]]) -> list[tuple[str, object]]:
    return [(label, value) for label, value in rows if value not in (None, "")]
