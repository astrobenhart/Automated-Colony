from __future__ import annotations

import random
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


FIRST_NAMES = (
    "Ada", "Alba", "Anya", "Bryn", "Cora", "Dara", "Ella", "Faye",
    "Galen", "Hale", "Iris", "Jora", "Kellan", "Lena", "Lily", "Mara",
    "Nia", "Oren", "Perrin", "Quinn", "Rowan", "Sera", "Tessa", "Theo",
    "Vera", "Wren",
)

SURNAMES = (
    "Ash", "Briar", "Brook", "Cairn", "Dale", "Fenn", "Field", "Hale",
    "Hart", "Miller", "Reed", "Rowan", "Stone", "Vale", "Weaver", "Wood",
)

PLACEHOLDER_NAME_RE = re.compile(r"^(?:(?:Child|Adult|Villager)\s+\d+|child-\d+|villager-\d+)$", re.IGNORECASE)
HOUSEHOLD_SUFFIXES = {"Hearth", "Home", "House", "Household"}


def is_placeholder_name(name: str | None) -> bool:
    if not name or not str(name).strip():
        return True
    return bool(PLACEHOLDER_NAME_RE.match(str(name).strip()))


def split_full_name(name: str | None) -> tuple[str | None, str | None]:
    parts = [part for part in str(name or "").strip().split() if part]
    if len(parts) >= 2 and not is_placeholder_name(name):
        return parts[0], parts[-1]
    if len(parts) == 1 and not is_placeholder_name(name):
        return parts[0], None
    return None, None


def full_name(first_name: str, surname: str) -> str:
    return f"{first_name} {surname}"


def surname_from_household_name(name: str | None) -> str:
    parts = [part for part in str(name or "").strip().split() if part]
    if not parts:
        return "House"
    if len(parts) >= 2 and parts[-1] in HOUSEHOLD_SUFFIXES:
        return parts[0]
    return parts[0]


def generated_name(seed: object, key: object, *, surname: str | None = None) -> tuple[str, str]:
    rng = random.Random(f"{seed}|persistent-name|{key}")
    first_name = rng.choice(FIRST_NAMES)
    return first_name, surname or rng.choice(SURNAMES)


def assign_persistent_name(
    agent: Agent,
    *,
    seed: object,
    key: object,
    surname: str | None = None,
) -> Agent:
    current_name_is_placeholder = is_placeholder_name(getattr(agent, "name", None))
    first_name = getattr(agent, "first_name", None)
    current_surname = getattr(agent, "surname", None)
    parsed_first, parsed_surname = split_full_name(getattr(agent, "name", None))

    if current_name_is_placeholder:
        first_name = None
        current_surname = surname

    if not first_name:
        first_name = parsed_first
    if not current_surname:
        current_surname = surname or parsed_surname

    if not first_name or not current_surname or current_name_is_placeholder:
        generated_first, generated_surname = generated_name(seed, key, surname=surname or current_surname)
        first_name = first_name if first_name and not current_name_is_placeholder else generated_first
        current_surname = current_surname or generated_surname

    agent.first_name = first_name
    agent.surname = current_surname
    agent.name = full_name(first_name, current_surname)
    return agent


def set_agent_surname(agent: Agent, surname: str | None) -> bool:
    if not surname:
        return False
    first_name = getattr(agent, "first_name", None)
    if not first_name:
        parsed_first, _parsed_surname = split_full_name(getattr(agent, "name", None))
        first_name = parsed_first
    if not first_name or is_placeholder_name(first_name):
        return False

    before = getattr(agent, "name", None)
    agent.first_name = first_name
    agent.surname = surname
    agent.name = full_name(first_name, surname)
    return getattr(agent, "name", None) != before


def household_surname(household) -> str | None:
    if household is None:
        return None
    surname = getattr(household, "surname", None)
    if not surname:
        surname = surname_from_household_name(getattr(household, "household_name", None))
        household.surname = surname
    return surname


def apply_household_surname(agent: Agent, household) -> bool:
    return set_agent_surname(agent, household_surname(household))


def inherited_child_surname(parent_a: Agent, parent_b: Agent, household=None) -> str | None:
    return household_surname(household) or getattr(parent_a, "surname", None) or getattr(parent_b, "surname", None)


def migrate_world_names(world: World) -> int:
    """Assign persistent names to old or placeholder villagers without changing gameplay state."""
    changed = 0
    for index, agent in enumerate(getattr(world, "agents", [])):
        before = getattr(agent, "name", None)
        key = getattr(agent, "agent_id", None) or f"agent-{index}"
        assign_persistent_name(agent, seed=getattr(world, "seed", None), key=key)
        if getattr(agent, "name", None) != before:
            changed += 1
    settlement = getattr(world, "settlement", None)
    if settlement is None:
        return changed
    agents_by_id = {
        getattr(agent, "agent_id", None) or getattr(agent, "name", None): agent
        for agent in getattr(world, "agents", [])
    }
    for household in getattr(settlement, "households", []):
        surname = household_surname(household)
        for member_id in getattr(household, "member_ids", []):
            agent = agents_by_id.get(member_id)
            if agent is not None and set_agent_surname(agent, surname):
                changed += 1
    return changed
