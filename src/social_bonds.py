from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.social_memory import ACQUAINTED, FAMILIAR, SEEN, familiarity_level

if TYPE_CHECKING:
    from src.agent import Agent


OFTEN_SEEN_WITH = "Often Seen With"
TRUSTED_NEIGHBOR = "Trusted Neighbor"
CLOSE_COMPANION = "Close Companion"

SOCIAL_BOND_LABELS = (
    OFTEN_SEEN_WITH,
    TRUSTED_NEIGHBOR,
    CLOSE_COMPANION,
)


@dataclass(frozen=True)
class SocialBond:
    label: str
    name: str


def social_bond_label_for_score(score: int) -> str | None:
    level = familiarity_level(score)
    if level == FAMILIAR:
        return CLOSE_COMPANION
    if level == ACQUAINTED:
        return TRUSTED_NEIGHBOR
    if level == SEEN:
        return OFTEN_SEEN_WITH
    return None


def social_bonds(agent: Agent, limit: int = 3) -> list[SocialBond]:
    memory = getattr(agent, "social_memory", None)
    if not memory:
        return []

    bonds = []
    for entry in memory.values():
        label = social_bond_label_for_score(entry.familiarity_score)
        if label is None:
            continue
        bonds.append(SocialBond(label=label, name=entry.display_name))

    bonds.sort(key=lambda bond: (bond_priority(bond.label), bond.name))
    return bonds[:limit]


def bond_priority(label: str) -> int:
    if label == CLOSE_COMPANION:
        return 0
    if label == TRUSTED_NEIGHBOR:
        return 1
    if label == OFTEN_SEEN_WITH:
        return 2
    return 3
