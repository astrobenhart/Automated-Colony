from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.config import (
    TASK_FATIGUE_INTERRUPT_THRESHOLD,
    TASK_HUNGER_INTERRUPT_THRESHOLD,
    TASK_THIRST_INTERRUPT_THRESHOLD,
)
from src.friendships import close_friend_ids
from src.lifecycle import CHILD
from src.social_memory import chebyshev_distance, villager_key

if TYPE_CHECKING:
    import random

    from src.agent import Agent
    from src.world import World


GATHERING_RADIUS = 2
COMFORTABLE_GATHERING_SIZE = 4


@dataclass(frozen=True)
class GatheringDestination:
    label: str
    anchor: tuple[int, int]
    score: float
    nearby_count: int


@dataclass(frozen=True)
class GatheringCluster:
    label: str
    center: tuple[int, int]
    size: int


def gathering_wander_target(agent: Agent, world: World, rng: random.Random) -> tuple[int, int] | None:
    if not can_participate_in_gathering(agent):
        return None

    destinations = gathering_destinations(agent, world, rng)
    if not destinations:
        return None

    chosen = weighted_choice(destinations, rng)
    return valid_tile_near_anchor(world, agent, chosen.anchor, rng)


def can_participate_in_gathering(agent: Agent) -> bool:
    if not getattr(agent, "alive", True):
        return False
    if getattr(agent, "hunger", 0) >= TASK_HUNGER_INTERRUPT_THRESHOLD:
        return False
    if getattr(agent, "thirst", 0) >= TASK_THIRST_INTERRUPT_THRESHOLD:
        return False
    if getattr(agent, "fatigue", 0) >= TASK_FATIGUE_INTERRUPT_THRESHOLD:
        return False
    action = getattr(agent, "current_action", "")
    if action in {"Eating", "Drinking", "Sleeping", "Building", "Harvesting", "Harvesting farm", "Planting", "Depositing"}:
        return False
    return True


def gathering_destinations(agent: Agent, world: World, rng: random.Random) -> list[GatheringDestination]:
    anchors = destination_anchors(agent, world)
    if not anchors:
        return []

    destinations = []
    for label, anchor in anchors.items():
        destinations.append(score_destination(agent, world, label, anchor, rng))

    destinations.sort(key=lambda destination: (-destination.score, destination.label, destination.anchor))
    return destinations[:8]


def destination_anchors(agent: Agent, world: World) -> dict[str, tuple[int, int]]:
    anchors: dict[str, tuple[int, int]] = {}
    settlement = getattr(world, "settlement", None)
    if settlement is not None:
        anchors["Village Centre"] = (settlement.x, settlement.y)

    from src.celebrations import celebration_destination

    ceremony = celebration_destination(world)
    if ceremony is not None:
        label, anchor = ceremony
        anchors[label] = anchor

    from src.mysteries import mystery_destination

    mystery = mystery_destination(world)
    if mystery is not None:
        label, anchor = mystery
        anchors[label] = anchor

    home = home_anchor(agent, world)
    if home is not None:
        anchors["Home"] = home

    if settlement is not None:
        for workplace in getattr(settlement, "workplaces", [])[:8]:
            anchors[f"{workplace.workplace_type.title()}"] = (workplace.x, workplace.y)

    for friend in close_friends(agent, world):
        anchors[f"Friend {friend.name}"] = (friend.x, friend.y)
        friend_home = home_anchor(friend, world)
        if friend_home is not None:
            anchors[f"{friend.name}'s Home"] = friend_home

    for related in household_or_family_members(agent, world):
        anchors[f"{related.name}"] = (related.x, related.y)

    water = nearest_known_water(agent, world)
    if water is not None:
        anchors["Water"] = water

    return anchors


def score_destination(
    agent: Agent,
    world: World,
    label: str,
    anchor: tuple[int, int],
    rng: random.Random,
) -> GatheringDestination:
    distance = chebyshev_distance(agent.x, agent.y, anchor[0], anchor[1])
    nearby = nearby_villagers(world, anchor, radius=GATHERING_RADIUS, exclude=agent)
    nearby_count = len(nearby)
    close_ids = close_friend_ids(agent)
    household_id = getattr(agent, "household_id", None)
    family_id = getattr(agent, "family_id", None)

    friend_count = sum(1 for other in nearby if villager_key(other) in close_ids)
    household_count = sum(1 for other in nearby if household_id and getattr(other, "household_id", None) == household_id)
    family_count = sum(1 for other in nearby if family_id and getattr(other, "family_id", None) == family_id)
    partner_nearby = partner_present_at_destination(agent, world, anchor)

    score = 12.0
    if label == "Village Centre":
        score += 8
    if label == "Home":
        score += 6
    if label.startswith("Friend ") or label.endswith("'s Home"):
        score += 22
    if label.startswith("Ceremony:"):
        from src.celebrations import celebration_attraction

        score += celebration_attraction(agent, world)
    if label.startswith("Mystery:"):
        from src.mysteries import mystery_attraction

        score += mystery_attraction(agent, world)
    if getattr(agent, "lifecycle_stage", None) == CHILD:
        score += child_safety_bonus(label, friend_count, household_count, family_count)

    score += gathering_size_attraction(nearby_count)
    score += friend_count * 10
    score += household_count * 7
    score += family_count * 6
    if partner_nearby:
        score += partner_attraction_bonus(agent)
    score -= distance * 1.5
    score += rng.random() * 6
    return GatheringDestination(label, anchor, max(1.0, score), nearby_count)


def partner_present_at_destination(agent: Agent, world: World, anchor: tuple[int, int]) -> bool:
    from src.affection import active_partner

    partner = active_partner(agent, world)
    if partner is None or not gathering_participant(partner):
        return False
    return chebyshev_distance(partner.x, partner.y, anchor[0], anchor[1]) <= GATHERING_RADIUS


def partner_attraction_bonus(agent: Agent) -> float:
    from src.affection import affection_label

    label = affection_label(agent)
    if label == "Lifelong":
        return 16.0
    if label == "Strong":
        return 14.0
    if label == "Established":
        return 12.0
    return 9.0


def gathering_size_attraction(count: int) -> float:
    if count <= 0:
        return 0.0
    if count <= COMFORTABLE_GATHERING_SIZE:
        return count * 5.0
    overflow = count - COMFORTABLE_GATHERING_SIZE
    return COMFORTABLE_GATHERING_SIZE * 5.0 - overflow * 3.0


def child_safety_bonus(label: str, friend_count: int, household_count: int, family_count: int) -> float:
    bonus = 0.0
    if label == "Home":
        bonus += 12
    bonus += household_count * 5
    bonus += family_count * 5
    bonus += friend_count * 3
    return bonus


def weighted_choice(destinations: list[GatheringDestination], rng: random.Random) -> GatheringDestination:
    weights = [max(1.0, destination.score) for destination in destinations]
    total = sum(weights)
    roll = rng.random() * total
    running = 0.0
    for destination, weight in zip(destinations, weights):
        running += weight
        if roll <= running:
            return destination
    return destinations[-1]


def valid_tile_near_anchor(
    world: World,
    agent: Agent,
    anchor: tuple[int, int],
    rng: random.Random,
    radius: int = 1,
) -> tuple[int, int] | None:
    candidates = []
    for y in range(max(0, anchor[1] - radius), min(world.height, anchor[1] + radius + 1)):
        for x in range(max(0, anchor[0] - radius), min(world.width, anchor[0] + radius + 1)):
            if (x, y) == (agent.x, agent.y):
                continue
            if not world.is_valid_spawn_tile(x, y):
                continue
            distance = chebyshev_distance(x, y, anchor[0], anchor[1])
            candidates.append((distance, rng.random(), (x, y)))
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][2]


def nearby_villagers(world: World, anchor: tuple[int, int], radius: int, exclude: Agent | None = None) -> list[Agent]:
    return [
        other
        for other in world.living_agents()
        if other is not exclude and chebyshev_distance(other.x, other.y, anchor[0], anchor[1]) <= radius
    ]


def close_friends(agent: Agent, world: World) -> list[Agent]:
    ids = close_friend_ids(agent)
    if not ids:
        return []
    return [other for other in world.living_agents() if other is not agent and villager_key(other) in ids]


def household_or_family_members(agent: Agent, world: World) -> list[Agent]:
    household_id = getattr(agent, "household_id", None)
    family_id = getattr(agent, "family_id", None)
    members = []
    for other in world.living_agents():
        if other is agent:
            continue
        if household_id and getattr(other, "household_id", None) == household_id:
            members.append(other)
            continue
        if family_id and getattr(other, "family_id", None) == family_id:
            members.append(other)
    return members[:8]


def nearest_known_water(agent: Agent, world: World) -> tuple[int, int] | None:
    known = list(getattr(world.colony_memory, "known_water", set()))
    if not known:
        return None
    known.sort(key=lambda pos: (chebyshev_distance(agent.x, agent.y, pos[0], pos[1]), pos[1], pos[0]))
    return known[0]


def home_anchor(agent: Agent, world: World) -> tuple[int, int] | None:
    if getattr(agent, "home_x", None) is not None and getattr(agent, "home_y", None) is not None:
        return agent.home_x, agent.home_y
    settlement = getattr(world, "settlement", None)
    if settlement is None:
        return None
    home_id = getattr(agent, "home_id", None)
    home = settlement.home_for_id(home_id)
    if home is not None:
        return home.x, home.y
    household = world.household_for_agent(agent) if hasattr(world, "household_for_agent") else None
    if household is not None:
        home = settlement.home_for_id(getattr(household, "home_id", None))
        if home is not None:
            return home.x, home.y
    return None


def social_state(agent: Agent, world: World | None = None) -> str:
    action = getattr(agent, "current_action", None) or "Idle"
    if action in {"Eating", "Drinking", "Sleeping"}:
        return "Resting"
    if action in {"Building", "Harvesting", "Harvesting farm", "Planting", "Depositing", "Seeking food", "Seeking water", "Gathering wood"}:
        return "Working"
    if action.startswith(("Gathering", "Seeking", "Moving", "Harvesting", "Planting", "Depositing", "Building")):
        return "Working"
    if world is None:
        return "Idle" if action == "Idle" else action
    if has_nearby_close_friend(agent, world):
        return "Visiting Friend"
    if gathering_cluster_for_agent(agent, world) is not None:
        return "Gathering"
    if action in {"Idle", "Wandering", "At village center", "At home", "Winding down"}:
        return "Idle"
    return action


def has_nearby_close_friend(agent: Agent, world: World) -> bool:
    close_ids = close_friend_ids(agent)
    if not close_ids:
        return False
    for other in world.living_agents():
        if other is agent:
            continue
        if villager_key(other) in close_ids and chebyshev_distance(agent.x, agent.y, other.x, other.y) <= GATHERING_RADIUS:
            return True
    return False


def gathering_cluster_for_agent(agent: Agent, world: World) -> GatheringCluster | None:
    for cluster in active_gatherings(world):
        if chebyshev_distance(agent.x, agent.y, cluster.center[0], cluster.center[1]) <= GATHERING_RADIUS:
            return cluster
    return None


def active_gatherings(world: World) -> list[GatheringCluster]:
    participants = [agent for agent in world.living_agents() if gathering_participant(agent)]
    remaining = set(range(len(participants)))
    clusters: list[GatheringCluster] = []
    while remaining:
        start = remaining.pop()
        group = {start}
        frontier = [start]
        while frontier:
            current = frontier.pop()
            current_agent = participants[current]
            connected = [
                index
                for index in list(remaining)
                if chebyshev_distance(current_agent.x, current_agent.y, participants[index].x, participants[index].y) <= GATHERING_RADIUS
            ]
            for index in connected:
                remaining.remove(index)
                group.add(index)
                frontier.append(index)
        if len(group) >= 2:
            members = [participants[index] for index in sorted(group)]
            center = cluster_center(members)
            clusters.append(GatheringCluster(gathering_label(world, center), center, len(members)))
    clusters.sort(key=lambda cluster: (-cluster.size, cluster.label, cluster.center))
    return clusters


def gathering_participant(agent: Agent) -> bool:
    if not can_participate_in_gathering(agent):
        return False
    return getattr(agent, "current_action", None) in {
        "Idle",
        "Wandering",
        "At village center",
        "At home",
        "Winding down",
    }


def cluster_center(members: list[Agent]) -> tuple[int, int]:
    x = round(sum(agent.x for agent in members) / len(members))
    y = round(sum(agent.y for agent in members) / len(members))
    return x, y


def gathering_label(world: World, center: tuple[int, int]) -> str:
    settlement = getattr(world, "settlement", None)
    if settlement is not None:
        if chebyshev_distance(center[0], center[1], settlement.x, settlement.y) <= 2:
            return "Village Centre"
        for home in getattr(settlement, "homes", []):
            if chebyshev_distance(center[0], center[1], home.x, home.y) <= 2:
                return "Home"
        for workplace in getattr(settlement, "workplaces", []):
            if chebyshev_distance(center[0], center[1], workplace.x, workplace.y) <= 2:
                return workplace.workplace_type.title()
    return f"{center[0]},{center[1]}"


def gathering_diagnostics(world: World) -> list[tuple[str, object]]:
    clusters = active_gatherings(world)
    sizes = [cluster.size for cluster in clusters]
    destinations = ", ".join(f"{cluster.label}:{cluster.size}" for cluster in clusters[:4]) or "None"
    return [
        ("Active Gatherings", len(clusters)),
        ("Average Gathering Size", f"{(sum(sizes) / len(sizes)):.1f}" if sizes else "0.0"),
        ("Largest Gathering", max(sizes) if sizes else 0),
        ("Idle Villagers Participating", sum(sizes)),
        ("Gathering Destinations", destinations),
    ]
