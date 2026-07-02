from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.config import SOCIAL_MEMORY_MAX_OBSERVATIONS_PER_AGENT
from src.social_memory import chebyshev_distance, nearby_agents, villager_key
from src.world_history import LOCAL_STORY

if TYPE_CHECKING:
    import random

    from src.agent import Agent
    from src.world import World


BEST_FRIEND_LIMIT = 3
KNOWN_FRIEND_LIMIT = 5
CLOSE_FRIEND_THRESHOLD = 30
BEST_FRIEND_THRESHOLD = 55
FRIENDSHIP_MAX_SCORE = 100
FRIENDSHIP_DECAY_AFTER_DAYS = 160
FRIENDSHIP_CHRONICLE_LIMIT_PER_YEAR = 6
FRIENDSHIP_LOSS_CHRONICLE_LIMIT_PER_YEAR = 4


@dataclass
class FriendshipEntry:
    friend_id: str
    display_name: str
    score: int = 0
    formed_day: int = 0
    last_interaction_day: int = 0
    close_recorded: bool = False


@dataclass(frozen=True)
class FriendshipDisplay:
    label: str
    name: str
    strength: int


def update_friendships(world: World):
    living = world.living_agents()
    if len(living) < 2:
        return

    living_by_id = {villager_key(agent): agent for agent in living}
    strengthen_household_friendships(world, living_by_id)
    strengthen_workplace_friendships(world, living_by_id)
    strengthen_nearby_friendships(world, living)
    strengthen_shared_activity_friendships(world, living)
    decay_stale_friendships(world, living_by_id)
    prune_all_friendships(living, living_by_id)


def strengthen_household_friendships(world: World, living_by_id: dict[str, Agent]):
    settlement = getattr(world, "settlement", None)
    if settlement is None:
        return

    for household in getattr(settlement, "households", []):
        members = [living_by_id[member_id] for member_id in household.member_ids if member_id in living_by_id]
        strengthen_group(world, members, amount=3)


def strengthen_workplace_friendships(world: World, living_by_id: dict[str, Agent]):
    settlement = getattr(world, "settlement", None)
    if settlement is None:
        return

    for workplace in getattr(settlement, "workplaces", []):
        workers = [
            living_by_id[worker_id]
            for worker_id in getattr(workplace, "assigned_workers", [])
            if worker_id in living_by_id
        ]
        strengthen_group(world, workers, amount=2)


def strengthen_nearby_friendships(world: World, living: list[Agent]):
    by_tile = {(agent.x, agent.y): [] for agent in living}
    for agent in living:
        by_tile[(agent.x, agent.y)].append(agent)

    seen_pairs: set[tuple[str, str]] = set()
    for observer in living:
        observed = 0
        for other in nearby_agents(observer, by_tile, radius=2):
            if other is observer:
                continue
            pair = pair_key(observer, other)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            record_friendship_interaction(world, observer, other, amount=1)
            observed += 1
            if observed >= SOCIAL_MEMORY_MAX_OBSERVATIONS_PER_AGENT:
                break


def strengthen_shared_activity_friendships(world: World, living: list[Agent]):
    buckets: dict[tuple[object, ...], list[Agent]] = {}
    for agent in living:
        action = getattr(agent, "current_action", None)
        if action in (None, "", "Idle", "Sleeping", "Recovering"):
            continue
        key = (
            action,
            getattr(agent, "current_goal", None),
            getattr(agent, "task_target", None) or getattr(agent, "current_target", None),
        )
        buckets.setdefault(key, []).append(agent)

    for group in buckets.values():
        if len(group) < 2:
            continue
        group.sort(key=villager_key)
        strengthen_group(world, group[:8], amount=1)


def strengthen_group(world: World, members: list[Agent], amount: int):
    if len(members) < 2:
        return
    members = sorted(members, key=villager_key)
    for index, agent in enumerate(members):
        for other in members[index + 1:]:
            record_friendship_interaction(world, agent, other, amount=amount)


def record_friendship_interaction(world: World, agent: Agent, other: Agent, amount: int = 1):
    if agent is other or amount <= 0:
        return
    if not getattr(agent, "alive", True) or not getattr(other, "alive", True):
        return

    before_a = friendship_score(agent, other)
    before_b = friendship_score(other, agent)
    entry_a = strengthen_one_direction(world, agent, other, amount)
    entry_b = strengthen_one_direction(world, other, agent, amount)

    if (
        max(before_a, before_b) < CLOSE_FRIEND_THRESHOLD
        and min(entry_a.score, entry_b.score) >= CLOSE_FRIEND_THRESHOLD
    ):
        record_friendship_formation(world, agent, other, entry_a, entry_b)


def strengthen_one_direction(world: World, agent: Agent, other: Agent, amount: int) -> FriendshipEntry:
    key = villager_key(other)
    entry = agent.friendships.get(key)
    if entry is None:
        entry = FriendshipEntry(
            friend_id=key,
            display_name=other.name,
            formed_day=world.day,
            last_interaction_day=world.day,
        )
        agent.friendships[key] = entry

    entry.display_name = other.name
    entry.score = min(FRIENDSHIP_MAX_SCORE, entry.score + amount)
    entry.last_interaction_day = world.day
    return entry


def friendship_score(agent: Agent, other: Agent) -> int:
    entry = getattr(agent, "friendships", {}).get(villager_key(other))
    return entry.score if entry is not None else 0


def record_friendship_formation(
    world: World,
    agent: Agent,
    other: Agent,
    entry_a: FriendshipEntry,
    entry_b: FriendshipEntry,
):
    entry_a.close_recorded = True
    entry_b.close_recorded = True

    pair = pair_key(agent, other)
    recorded = getattr(world, "recorded_friendship_pairs", None)
    if recorded is None:
        world.recorded_friendship_pairs = set()
        recorded = world.recorded_friendship_pairs
    if pair in recorded:
        return
    recorded.add(pair)

    world.friendship_formations_by_year[world.year] = world.friendship_formations_by_year.get(world.year, 0) + 1
    if friendship_chronicle_count(world) >= FRIENDSHIP_CHRONICLE_LIMIT_PER_YEAR:
        return

    world.history.record(
        day=world.day,
        year=world.year,
        season=world.season,
        category=LOCAL_STORY,
        title="Close Friendship",
        description=f"{agent.name} and {other.name} became close friends.",
    )


def friendship_chronicle_count(world: World) -> int:
    return sum(
        1
        for entry in getattr(world.history, "entries", [])
        if entry.year == world.year and entry.category == LOCAL_STORY and entry.title == "Close Friendship"
    )


def decay_stale_friendships(world: World, living_by_id: dict[str, Agent]):
    for agent in living_by_id.values():
        for friend_id, entry in list(agent.friendships.items()):
            if friend_id not in living_by_id:
                continue
            if world.day - entry.last_interaction_day > FRIENDSHIP_DECAY_AFTER_DAYS:
                entry.score = max(1, entry.score - 1)


def prune_all_friendships(living: list[Agent], living_by_id: dict[str, Agent]):
    for agent in living:
        prune_friendships(agent, living_by_id)


def prune_friendships(agent: Agent, living_by_id: dict[str, Agent] | None = None):
    friendships = getattr(agent, "friendships", None)
    if not friendships:
        return

    entries = list(friendships.values())
    if living_by_id is not None:
        entries = [entry for entry in entries if entry.friend_id in living_by_id]
    entries.sort(key=lambda entry: (-entry.score, entry.display_name, entry.friend_id))
    agent.friendships = {entry.friend_id: entry for entry in entries[:KNOWN_FRIEND_LIMIT]}


def friendship_displays(agent: Agent, limit: int = KNOWN_FRIEND_LIMIT) -> list[FriendshipDisplay]:
    entries = list(getattr(agent, "friendships", {}).values())
    entries.sort(key=lambda entry: (-entry.score, entry.display_name, entry.friend_id))
    displays = []
    for index, entry in enumerate(entries[:limit]):
        if entry.score >= BEST_FRIEND_THRESHOLD and index < BEST_FRIEND_LIMIT:
            label = "Best Friend"
        elif entry.score >= CLOSE_FRIEND_THRESHOLD:
            label = "Close Friend"
        else:
            label = "Friend"
        displays.append(FriendshipDisplay(label=label, name=entry.display_name, strength=entry.score))
    return displays


def close_friend_ids(agent: Agent) -> set[str]:
    return {
        friend_id
        for friend_id, entry in getattr(agent, "friendships", {}).items()
        if entry.score >= CLOSE_FRIEND_THRESHOLD
    }


def has_nearby_close_friend(agent: Agent, world: World, radius: int = 2) -> bool:
    close_ids = close_friend_ids(agent)
    if not close_ids:
        return False
    for other in world.living_agents():
        if other is agent:
            continue
        if villager_key(other) not in close_ids:
            continue
        if chebyshev_distance(agent.x, agent.y, other.x, other.y) <= radius:
            return True
    return False


def friend_wander_anchor(agent: Agent, world: World, rng: random.Random) -> tuple[int, int] | None:
    if getattr(agent, "hunger", 0) >= 50 or getattr(agent, "thirst", 0) >= 50 or getattr(agent, "fatigue", 0) >= 70:
        return None
    close_ids = close_friend_ids(agent)
    if not close_ids:
        return None
    candidates = [
        other
        for other in world.living_agents()
        if other is not agent and villager_key(other) in close_ids
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda other: (-friendship_score(agent, other), other.name))
    friend = candidates[0]
    options = []
    for y in range(max(0, friend.y - 2), min(world.height, friend.y + 3)):
        for x in range(max(0, friend.x - 2), min(world.width, friend.x + 3)):
            if (x, y) == (agent.x, agent.y):
                continue
            if world.is_valid_spawn_tile(x, y):
                options.append((x, y))
    if not options:
        return None
    return rng.choice(options)


def handle_friend_death(world: World, deceased: Agent):
    deceased_id = villager_key(deceased)
    mourners: list[Agent] = []
    for agent in world.living_agents():
        entry = getattr(agent, "friendships", {}).pop(deceased_id, None)
        if entry is None or entry.score < CLOSE_FRIEND_THRESHOLD:
            continue
        mourners.append(agent)
        memory = f"Mourned close friend {deceased.name}."
        if memory not in agent.personal_memories:
            agent.personal_memories.insert(0, memory)
        agent.remembering = deceased.name
        agent.remembrance_expires_day = max(getattr(agent, "remembrance_expires_day", 0), world.day + 4)

    if not mourners:
        return

    world.friendship_losses_by_year[world.year] = world.friendship_losses_by_year.get(world.year, 0) + len(mourners)
    if friendship_loss_chronicle_count(world) >= FRIENDSHIP_LOSS_CHRONICLE_LIMIT_PER_YEAR:
        return

    mourner = sorted(mourners, key=lambda agent: agent.name)[0]
    world.history.record(
        day=world.day,
        year=world.year,
        season=world.season,
        category=LOCAL_STORY,
        title="Friend Mourned",
        description=f"{mourner.name} mourned the loss of {deceased.name}.",
    )


def friendship_loss_chronicle_count(world: World) -> int:
    return sum(
        1
        for entry in getattr(world.history, "entries", [])
        if entry.year == world.year and entry.category == LOCAL_STORY and entry.title == "Friend Mourned"
    )


def friendship_diagnostics(world: World) -> list[tuple[str, object]]:
    living = world.living_agents()
    if not living:
        return [
            ("Average Friendships per Villager", "0.0"),
            ("Close Friendships", 0),
            ("Average Friendship Strength", "0.0"),
            ("Most Connected Villager", "None"),
            ("Friendship Formations This Year", 0),
            ("Friendship Losses This Year", 0),
        ]

    counts = [len(getattr(agent, "friendships", {})) for agent in living]
    strengths = [
        entry.score
        for agent in living
        for entry in getattr(agent, "friendships", {}).values()
    ]
    close_pairs = unique_close_friendship_count(living)
    connected = max(living, key=lambda agent: (len(getattr(agent, "friendships", {})), agent.name))
    return [
        ("Average Friendships per Villager", f"{(sum(counts) / len(counts)):.1f}"),
        ("Close Friendships", close_pairs),
        ("Average Friendship Strength", f"{(sum(strengths) / len(strengths)):.1f}" if strengths else "0.0"),
        ("Most Connected Villager", connected.name if counts and max(counts) > 0 else "None"),
        ("Friendship Formations This Year", getattr(world, "friendship_formations_by_year", {}).get(world.year, 0)),
        ("Friendship Losses This Year", getattr(world, "friendship_losses_by_year", {}).get(world.year, 0)),
    ]


def unique_close_friendship_count(living: list[Agent]) -> int:
    pairs = set()
    for agent in living:
        for friend_id, entry in getattr(agent, "friendships", {}).items():
            if entry.score >= CLOSE_FRIEND_THRESHOLD:
                pairs.add(tuple(sorted((villager_key(agent), friend_id))))
    return len(pairs)


def friendship_label_counts(agent: Agent) -> Counter[str]:
    return Counter(display.label for display in friendship_displays(agent))


def pair_key(agent: Agent, other: Agent) -> tuple[str, str]:
    return tuple(sorted((villager_key(agent), villager_key(other))))
