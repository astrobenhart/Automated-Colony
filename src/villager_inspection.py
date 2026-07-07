from __future__ import annotations

from src.affection import affection_label, partner_nearby_label, relationship_mood_label
from src.death_memory import active_remembrance_name
from src.celebrations import ceremony_status
from src.community import community_associations
from src.friendships import friendship_displays
from src.gatherings import social_state
from src.influence import influence_label
from src.shared_moments import current_shared_moment
from src.social_bonds import social_bonds
from src.social_memory import relationship_summary
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
        ("Household", household_rows(agent, world)),
        ("Partnership", partnership_rows(agent, world)),
        ("Status", status_rows(agent, world)),
        ("Community", community_rows(agent, world)),
        ("Friends", friendship_rows(agent)),
        ("Relationships", relationship_rows(agent)),
        ("Bonds", bond_rows(agent)),
        ("Memories", memory_rows(agent)),
    ]


def compact_villager_rows(agent, world=None) -> list[tuple[str, object]]:
    if agent is None:
        return [("Selected", "None")]

    return [
        ("Agent", getattr(agent, "name", "Villager")),
        ("Role", getattr(agent, "role", "Unknown")),
        ("Household", household_name_for_agent(agent, world)),
        ("State", safe_state_label(agent, world) or "Unknown"),
        ("Action", getattr(agent, "current_action", "Unknown")),
    ]


def identity_rows(agent, world=None) -> list[tuple[str, object]]:
    return present_rows([
        ("Name", getattr(agent, "name", None)),
        ("Age", getattr(agent, "age", None)),
        ("Stage", getattr(agent, "lifecycle_stage", None)),
        ("Role", getattr(agent, "role", None)),
        ("Experience", getattr(agent, "experience_level", None)),
        ("Role Years", getattr(agent, "years_in_role", None)),
        ("Trait", getattr(agent, "trait", None)),
        ("Family", family_name(agent, world)),
        ("Parents", parent_names(agent, world)),
        ("Home", getattr(agent, "home_settlement_name", None)),
    ])


def household_rows(agent, world=None) -> list[tuple[str, object]]:
    household = household_for_agent(agent, world)
    occupancy = None
    house_size = None
    if household is not None and world is not None:
        from src.residential import household_status

        status = household_status(world, household)
        occupancy = f"{status.occupants} / {status.capacity}"
        house_size = f"{status.house_tiles} Tile" if status.house_tiles == 1 else f"{status.house_tiles} Tiles"
    rows = [
        ("Household", household.household_name if household is not None else getattr(agent, "household_id", None)),
        ("Household Surname", getattr(household, "surname", None) if household is not None else None),
        ("Home", home_label(agent, world)),
        ("Occupants", occupancy),
        ("House Size", house_size),
        ("Members", household_member_names(household, world) if household is not None else None),
    ]
    return present_rows(rows) or [("", "None")]


def household_name_for_agent(agent, world=None) -> str:
    household = household_for_agent(agent, world)
    if household is not None:
        return household.household_name
    return getattr(agent, "household_id", None) or "Unknown"


def household_for_agent(agent, world=None):
    if world is None or getattr(world, "settlement", None) is None:
        return None
    return world.settlement.household_for(getattr(agent, "household_id", None))


def home_label(agent, world=None) -> str | None:
    home_id = getattr(agent, "home_id", None)
    if world is not None and getattr(world, "settlement", None) is not None:
        home = world.settlement.home_for_id(home_id)
        if home is not None:
            return f"{home.home_id} ({home.x}, {home.y})"
    home_x = getattr(agent, "home_x", None)
    home_y = getattr(agent, "home_y", None)
    if home_x is not None and home_y is not None:
        return f"({home_x}, {home_y})"
    return home_id


def household_member_names(household, world=None) -> str | None:
    if household is None or not household.member_ids:
        return None
    if world is None:
        return ", ".join(household.member_ids)
    names_by_id = {agent.agent_id or agent.name: agent.name for agent in world.agents}
    return ", ".join(names_by_id.get(member_id, member_id) for member_id in household.member_ids)


def partnership_rows(agent, world=None) -> list[tuple[str, object]]:
    partner_id = getattr(agent, "partner_id", None)
    if not partner_id:
        return [("Partner", "None")]
    return [
        ("Partner", partner_name(partner_id, world)),
        ("Partnership", partnership_duration_label(agent)),
        ("Relationship", affection_label(agent)),
        ("Partner Nearby", partner_nearby_label(agent, world)),
    ]


def partner_name(partner_id: str, world=None) -> str:
    if world is None:
        return partner_id
    for agent in getattr(world, "agents", []):
        if (agent.agent_id or agent.name) == partner_id:
            return agent.name
    return partner_id


def partnership_duration_label(agent) -> str:
    years = getattr(agent, "partnership_duration", 0)
    if years == 1:
        return "1 year"
    return f"{years} years"


def parent_names(agent, world=None) -> str | None:
    parent_ids = list(getattr(agent, "parent_ids", []) or [])
    for parent_id in (getattr(agent, "parent_a_id", None), getattr(agent, "parent_b_id", None)):
        if parent_id and parent_id not in parent_ids:
            parent_ids.append(parent_id)
    if not parent_ids:
        return None
    if world is None:
        return ", ".join(parent_ids)
    names_by_id = {other.agent_id or other.name: other.name for other in getattr(world, "agents", [])}
    return ", ".join(names_by_id.get(parent_id, parent_id) for parent_id in parent_ids)


def family_name(agent, world=None) -> str | None:
    family_id = getattr(agent, "family_id", None)
    if not family_id:
        return None
    family = getattr(world, "families", {}).get(family_id) if world is not None else None
    if family is not None:
        return family.family_name
    return family_id


def status_rows(agent, world=None) -> list[tuple[str, object]]:
    ceremony, ceremony_attendance = ceremony_status(agent, world)
    rows = [
        ("State", safe_state_label(agent, world) or "Unknown"),
        ("Social", social_state(agent, world)),
        ("Shared Moment", current_shared_moment(agent, world) or "None"),
        ("Relationship Mood", relationship_mood_label(agent, world)),
        ("Current Ceremony", ceremony),
        ("Influence", influence_label(agent, world)),
    ]
    if ceremony != "None":
        rows.append(("Ceremony Status", ceremony_attendance))
    if getattr(agent, "visitor_status", None):
        rows.append(("Visitor Status", visitor_status_label(agent)))
    remembering = active_remembrance_name(agent, world)
    if remembering:
        rows.append(("Remembering", remembering))
    return rows


def visitor_status_label(agent) -> str:
    status = getattr(agent, "visitor_status", None)
    profile = getattr(agent, "visitor_profile", None)
    if not status:
        return "None"
    if profile:
        return f"{status} ({profile.replace('_', ' ').title()})"
    return status


def community_rows(agent, world=None) -> list[tuple[str, object]]:
    associations = community_associations(agent, world)
    if not associations:
        return [("Community Associations", "None")]
    return [("Community Associations", ", ".join(associations))]


def relationship_rows(agent) -> list[tuple[str, object]]:
    relationships = relationship_summary(agent)
    if not relationships:
        return [("", "None")]
    return relationships


def friendship_rows(agent) -> list[tuple[str, object]]:
    friends = friendship_displays(agent)
    if not friends:
        return [("", "None")]
    return [(friend.label, f"{friend.name} ({friend.strength})") for friend in friends]


def bond_rows(agent) -> list[tuple[str, object]]:
    bonds = social_bonds(agent)
    if not bonds:
        return [("", "None")]
    return [(bond.label, bond.name) for bond in bonds]


def memory_rows(agent) -> list[tuple[str, object]]:
    memories = getattr(agent, "personal_memories", None)
    if not memories:
        return [("", "None")]
    return [("Memory", memory) for memory in memories[:3]]


def present_rows(rows: list[tuple[str, object | None]]) -> list[tuple[str, object]]:
    return [(label, value) for label, value in rows if value not in (None, "")]
