from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.gatherings import active_gatherings
from src.social_memory import chebyshev_distance, villager_key
from src.world_history import LOCAL_STORY

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


COMMUNITY_GROUP_RECOGNITION_COUNT = 3
GATHERING_PLACE_RECOGNITION_COUNT = 3
TRADITION_RECOGNITION_COUNT = 2
COMMUNITY_CHRONICLE_LIMIT_PER_YEAR = 4


@dataclass(frozen=True)
class RecognizedCommunityGroup:
    group_id: str
    name: str
    member_ids: tuple[str, ...]
    first_seen_day: int
    last_seen_day: int
    sightings: int


@dataclass(frozen=True)
class RecognizedGatheringPlace:
    place_id: str
    name: str
    label: str
    center: tuple[int, int]
    first_seen_day: int
    last_seen_day: int
    visits: int


@dataclass(frozen=True)
class RecognizedTradition:
    tradition_id: str
    name: str
    first_seen_day: int
    last_seen_day: int
    occurrences: int


def update_community_recognition(world: World):
    ensure_community_state(world)
    observe_gathering_groups(world)
    observe_gathering_places(world)
    observe_traditions(world)


def ensure_community_state(world: World):
    if getattr(world, "community_group_counts", None) is None:
        world.community_group_counts = {}
    if getattr(world, "community_group_first_seen", None) is None:
        world.community_group_first_seen = {}
    if getattr(world, "recognized_community_groups", None) is None:
        world.recognized_community_groups = []
    if getattr(world, "gathering_place_counts", None) is None:
        world.gathering_place_counts = {}
    if getattr(world, "gathering_place_first_seen", None) is None:
        world.gathering_place_first_seen = {}
    if getattr(world, "recognized_gathering_places", None) is None:
        world.recognized_gathering_places = []
    if getattr(world, "recognized_traditions", None) is None:
        world.recognized_traditions = []
    if getattr(world, "community_chronicle_keys", None) is None:
        world.community_chronicle_keys = set()


def observe_gathering_groups(world: World):
    living_by_id = {villager_key(agent): agent for agent in world.living_agents()}
    for cluster in active_gatherings(world):
        members = [
            agent
            for agent in world.living_agents()
            if chebyshev_distance(agent.x, agent.y, cluster.center[0], cluster.center[1]) <= 2
        ]
        if len(members) < 3:
            continue
        member_ids = tuple(sorted(villager_key(agent) for agent in members))
        group_id = f"group:{'|'.join(member_ids)}"
        count = world.community_group_counts.get(group_id, 0) + 1
        world.community_group_counts[group_id] = count
        world.community_group_first_seen.setdefault(group_id, world.day)
        if count >= COMMUNITY_GROUP_RECOGNITION_COUNT and not recognized_group_exists(world, group_id):
            group = RecognizedCommunityGroup(
                group_id=group_id,
                name=community_group_name(members),
                member_ids=member_ids,
                first_seen_day=world.community_group_first_seen[group_id],
                last_seen_day=world.day,
                sightings=count,
            )
            world.recognized_community_groups.append(group)
            record_community_chronicle(
                world,
                f"group:{group.group_id}",
                "Community Group",
                f"{group.name} had become a familiar sight in {settlement_name(world)}.",
            )
        elif count >= COMMUNITY_GROUP_RECOGNITION_COUNT:
            refresh_recognized_group(world, group_id, living_by_id)


def observe_gathering_places(world: World):
    for cluster in active_gatherings(world):
        if cluster.size < 2:
            continue
        place_id = gathering_place_id(cluster.label, cluster.center)
        count = world.gathering_place_counts.get(place_id, 0) + 1
        world.gathering_place_counts[place_id] = count
        world.gathering_place_first_seen.setdefault(place_id, world.day)
        if count >= GATHERING_PLACE_RECOGNITION_COUNT and not recognized_place_exists(world, place_id):
            place = RecognizedGatheringPlace(
                place_id=place_id,
                name=gathering_place_name(cluster.label),
                label=cluster.label,
                center=cluster.center,
                first_seen_day=world.gathering_place_first_seen[place_id],
                last_seen_day=world.day,
                visits=count,
            )
            world.recognized_gathering_places.append(place)
            record_community_chronicle(
                world,
                f"place:{place.place_id}",
                "Gathering Place",
                f"{place.name} had become a regular gathering place in {settlement_name(world)}.",
            )
        elif count >= GATHERING_PLACE_RECOGNITION_COUNT:
            refresh_recognized_place(world, place_id)


def observe_traditions(world: World):
    history = getattr(world, "celebration_history", [])
    if not history:
        return
    counts = Counter(item.celebration_type for item in history)
    for celebration_type, count in counts.items():
        if count < TRADITION_RECOGNITION_COUNT:
            continue
        tradition_id = f"tradition:{celebration_type}"
        if recognized_tradition_exists(world, tradition_id):
            refresh_recognized_tradition(world, tradition_id, celebration_type, count)
            continue
        matching = [item for item in history if item.celebration_type == celebration_type]
        tradition = RecognizedTradition(
            tradition_id=tradition_id,
            name=tradition_name(celebration_type),
            first_seen_day=min(item.started_day for item in matching),
            last_seen_day=max(item.started_day for item in matching),
            occurrences=count,
        )
        world.recognized_traditions.append(tradition)
        record_community_chronicle(
            world,
            tradition.tradition_id,
            "Village Tradition",
            tradition_description(world, tradition),
        )


def community_group_name(members: list[Agent]) -> str:
    role_counts = Counter(getattr(agent, "role", None) for agent in members if getattr(agent, "role", None))
    if role_counts:
        role, count = role_counts.most_common(1)[0]
        if count >= 2:
            return f"{role} Circle"
    family_counts = Counter(getattr(agent, "family_id", None) for agent in members if getattr(agent, "family_id", None))
    if family_counts:
        family_id, count = family_counts.most_common(1)[0]
        if count >= 2:
            family = None
            for member in members:
                if getattr(member, "family_id", None) == family_id:
                    family = member
                    break
            return f"{getattr(family, 'name', 'Family')} Kin Circle"
    return "Village Circle"


def gathering_place_id(label: str, center: tuple[int, int]) -> str:
    return f"place:{label}:{center[0]}:{center[1]}"


def gathering_place_name(label: str) -> str:
    if label == "Village Centre":
        return "Village Centre"
    if label == "Home":
        return "Household Hearth"
    return f"{label} Gathering Spot"


def tradition_name(celebration_type: str) -> str:
    if celebration_type == "Open Cremation":
        return "Funeral Fires"
    return celebration_type


def tradition_description(world: World, tradition: RecognizedTradition) -> str:
    if tradition.name == "Funeral Fires":
        return f"Funeral fires had become a solemn tradition in {settlement_name(world)}."
    return f"{tradition.name} had become a village tradition in {settlement_name(world)}."


def recognized_group_exists(world: World, group_id: str) -> bool:
    return any(group.group_id == group_id for group in getattr(world, "recognized_community_groups", []))


def recognized_place_exists(world: World, place_id: str) -> bool:
    return any(place.place_id == place_id for place in getattr(world, "recognized_gathering_places", []))


def recognized_tradition_exists(world: World, tradition_id: str) -> bool:
    return any(tradition.tradition_id == tradition_id for tradition in getattr(world, "recognized_traditions", []))


def refresh_recognized_group(world: World, group_id: str, living_by_id: dict[str, Agent]):
    refreshed = []
    for group in getattr(world, "recognized_community_groups", []):
        if group.group_id != group_id:
            refreshed.append(group)
            continue
        members = [living_by_id[member_id] for member_id in group.member_ids if member_id in living_by_id]
        refreshed.append(RecognizedCommunityGroup(
            group_id=group.group_id,
            name=community_group_name(members) if members else group.name,
            member_ids=group.member_ids,
            first_seen_day=group.first_seen_day,
            last_seen_day=world.day,
            sightings=world.community_group_counts.get(group_id, group.sightings),
        ))
    world.recognized_community_groups = refreshed


def refresh_recognized_place(world: World, place_id: str):
    world.recognized_gathering_places = [
        RecognizedGatheringPlace(
            place_id=place.place_id,
            name=place.name,
            label=place.label,
            center=place.center,
            first_seen_day=place.first_seen_day,
            last_seen_day=world.day if place.place_id == place_id else place.last_seen_day,
            visits=world.gathering_place_counts.get(place_id, place.visits) if place.place_id == place_id else place.visits,
        )
        for place in getattr(world, "recognized_gathering_places", [])
    ]


def refresh_recognized_tradition(world: World, tradition_id: str, celebration_type: str, count: int):
    matching = [item for item in getattr(world, "celebration_history", []) if item.celebration_type == celebration_type]
    if not matching:
        return
    world.recognized_traditions = [
        RecognizedTradition(
            tradition_id=tradition.tradition_id,
            name=tradition.name,
            first_seen_day=tradition.first_seen_day,
            last_seen_day=max(item.started_day for item in matching) if tradition.tradition_id == tradition_id else tradition.last_seen_day,
            occurrences=count if tradition.tradition_id == tradition_id else tradition.occurrences,
        )
        for tradition in getattr(world, "recognized_traditions", [])
    ]


def record_community_chronicle(world: World, key: str, title: str, description: str):
    if key in world.community_chronicle_keys:
        return
    if community_chronicle_count_this_year(world) >= COMMUNITY_CHRONICLE_LIMIT_PER_YEAR:
        return
    world.community_chronicle_keys.add(key)
    world.history.record(
        day=world.day,
        year=world.year,
        season=world.season,
        category=LOCAL_STORY,
        title=title,
        description=description,
    )


def community_chronicle_count_this_year(world: World) -> int:
    return sum(
        1
        for entry in getattr(world.history, "entries", [])
        if entry.year == world.year and entry.category == LOCAL_STORY and entry.title in {"Community Group", "Gathering Place", "Village Tradition"}
    )


def settlement_name(world: World) -> str:
    settlement = getattr(world, "settlement", None)
    return getattr(settlement, "name", "the village")


def community_associations(agent: Agent, world: World | None = None) -> list[str]:
    if world is None:
        return []
    agent_id = villager_key(agent)
    associations: list[str] = []
    for group in sorted(getattr(world, "recognized_community_groups", []), key=lambda item: (-item.sightings, item.name)):
        if agent_id in group.member_ids and group.name not in associations:
            associations.append(group.name)
    family_label = family_association(agent, world)
    if family_label and family_label not in associations:
        associations.append(family_label)
    for place in sorted(getattr(world, "recognized_gathering_places", []), key=lambda item: (-item.visits, item.name)):
        if chebyshev_distance(agent.x, agent.y, place.center[0], place.center[1]) <= 2:
            label = f"{place.name} Regular"
            if label not in associations:
                associations.append(label)
    return associations[:3]


def family_association(agent: Agent, world: World) -> str | None:
    family_id = getattr(agent, "family_id", None)
    if not family_id:
        return None
    family = getattr(world, "families", {}).get(family_id)
    if family is None:
        return None
    if getattr(family, "generation_count", 1) >= 2 or len(getattr(family, "member_ids", [])) >= 3:
        return family.family_name
    return None


def community_diagnostics(world: World) -> list[tuple[str, object]]:
    groups = getattr(world, "recognized_community_groups", [])
    places = getattr(world, "recognized_gathering_places", [])
    traditions = getattr(world, "recognized_traditions", [])
    oldest_group = min(groups, key=lambda group: group.first_seen_day, default=None)
    return [
        ("Recognised Community Groups", len(groups)),
        ("Recognised Traditions", len(traditions)),
        ("Recognised Gathering Places", len(places)),
        ("Oldest Continuing Community Group", oldest_group.name if oldest_group else "None"),
    ]
