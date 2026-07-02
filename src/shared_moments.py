from __future__ import annotations

import random
from collections import Counter
from typing import TYPE_CHECKING

from src.friendships import record_friendship_interaction
from src.gatherings import GATHERING_RADIUS, active_gatherings, can_participate_in_gathering, gathering_participant
from src.social_memory import chebyshev_distance, villager_key

if TYPE_CHECKING:
    from src.agent import Agent
    from src.world import World


CONVERSATION = "Conversation"
RESTING = "Resting"
MEAL = "Meal"
WATCHING = "Watching"
WARMING = "Warming"

SHARED_MOMENTS = (CONVERSATION, RESTING, MEAL, WATCHING, WARMING)
SHARED_MOMENT_FRIENDSHIP_GAIN = 1
SHARED_MOMENT_GROUP_LIMIT = 8


def update_shared_moments(world: World):
    clear_invalid_shared_moments(world)
    for cluster in active_gatherings(world):
        members = gathering_members(world, cluster.center)
        if len(members) < 2:
            continue
        moment = choose_shared_moment(world, cluster.center, len(members))
        for agent in members:
            if getattr(agent, "shared_moment", None) != moment:
                agent.shared_moment = moment
                agent.shared_moment_started_day = world.day
        strengthen_shared_moment_friendships(world, members)


def clear_invalid_shared_moments(world: World):
    participants = {
        villager_key(agent)
        for cluster in active_gatherings(world)
        for agent in gathering_members(world, cluster.center)
    }
    for agent in world.living_agents():
        if villager_key(agent) not in participants or not can_participate_in_gathering(agent):
            clear_shared_moment(agent)


def gathering_members(world: World, center: tuple[int, int]) -> list[Agent]:
    return [
        agent
        for agent in world.living_agents()
        if gathering_participant(agent)
        and chebyshev_distance(agent.x, agent.y, center[0], center[1]) <= GATHERING_RADIUS
    ]


def choose_shared_moment(world: World, center: tuple[int, int], size: int) -> str:
    rng = random.Random(f"{world.seed}|{world.day}|{center[0]}|{center[1]}|{size}|shared-moment")
    weighted = shared_moment_weights(world, center)
    total = sum(weight for _, weight in weighted)
    roll = rng.randint(1, total)
    running = 0
    for moment, weight in weighted:
        running += weight
        if roll <= running:
            return moment
    return CONVERSATION


def shared_moment_weights(world: World, center: tuple[int, int]) -> list[tuple[str, int]]:
    from src.celebrations import OPEN_CREMATION, active_celebration

    celebration = active_celebration(world)
    if celebration is not None and chebyshev_distance(center[0], center[1], celebration.anchor[0], celebration.anchor[1]) <= GATHERING_RADIUS:
        if celebration.celebration_type == OPEN_CREMATION:
            return [
                (WARMING, 42),
                (WATCHING, 28),
                (CONVERSATION, 20),
                (RESTING, 10),
            ]
        return [
            (WATCHING, 34),
            (CONVERSATION, 30),
            (MEAL, 18),
            (RESTING, 12),
            (WARMING, 6),
        ]

    return [
        (CONVERSATION, 38),
        (RESTING, 24),
        (WATCHING, 18),
        (MEAL, 14),
        (WARMING, 6),
    ]


def strengthen_shared_moment_friendships(world: World, members: list[Agent]):
    members = sorted(members, key=villager_key)[:SHARED_MOMENT_GROUP_LIMIT]
    for index, agent in enumerate(members):
        for other in members[index + 1:]:
            record_friendship_interaction(world, agent, other, amount=SHARED_MOMENT_FRIENDSHIP_GAIN)


def clear_shared_moment(agent: Agent):
    agent.shared_moment = None
    agent.shared_moment_started_day = 0


def current_shared_moment(agent: Agent, world: World | None = None) -> str | None:
    moment = getattr(agent, "shared_moment", None)
    if not moment:
        return None
    if world is not None and not can_participate_in_gathering(agent):
        return None
    return moment


def shared_moment_duration(agent: Agent, world: World) -> int:
    if current_shared_moment(agent, world) is None:
        return 0
    started = getattr(agent, "shared_moment_started_day", world.day) or world.day
    return max(1, world.day - started + 1)


def shared_moment_diagnostics(world: World) -> list[tuple[str, object]]:
    active = [agent for agent in world.living_agents() if current_shared_moment(agent, world)]
    durations = [shared_moment_duration(agent, world) for agent in active]
    counts = Counter(current_shared_moment(agent, world) for agent in active)
    counts.pop(None, None)
    most_common = counts.most_common(1)[0][0] if counts else "None"
    return [
        ("Active Shared Moments", len(active)),
        ("Average Duration", f"{(sum(durations) / len(durations)):.1f} days" if durations else "0.0 days"),
        ("Most Common Shared Moment", most_common),
    ]
