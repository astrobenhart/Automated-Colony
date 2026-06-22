from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.social_memory import ACQUAINTED, FAMILIAR, SEEN, familiarity_level

if TYPE_CHECKING:
    from src.agent import Agent


FAMILIAR_BOND = "Familiar"
FRIEND_BOND = "Friend"
CLOSE_FRIEND = "Close Friend"
TRUSTED_COMPANION = "Trusted Companion"

OFTEN_SEEN_WITH = FAMILIAR_BOND
TRUSTED_NEIGHBOR = FRIEND_BOND
CLOSE_COMPANION = CLOSE_FRIEND

SOCIAL_BOND_LABELS = (
    FAMILIAR_BOND,
    FRIEND_BOND,
    CLOSE_FRIEND,
    TRUSTED_COMPANION,
)


@dataclass(frozen=True)
class SocialBond:
    label: str
    name: str


def social_bond_label_for_score(score: int) -> str | None:
    if score >= 45:
        return TRUSTED_COMPANION
    level = familiarity_level(score)
    if level == FAMILIAR:
        return CLOSE_FRIEND
    if level == ACQUAINTED:
        return FRIEND_BOND
    if level == SEEN:
        return FAMILIAR_BOND
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
    if label == TRUSTED_COMPANION:
        return 0
    if label == CLOSE_FRIEND:
        return 1
    if label == FRIEND_BOND:
        return 2
    if label == FAMILIAR_BOND:
        return 3
    return 3
