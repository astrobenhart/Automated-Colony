from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.agent import Agent
from src.appearance import appearance_seed_for, appearance_type_for_seed
from src.families import ensure_family_registry
from src.renewal import ensure_expected_lifespan
from src.residential import next_household_id
from src.roles import BUILDER, FORAGER, GENERALIST, SCOUT
from src.settlement import Household
from src.social_memory import villager_key
from src.world_history import LOCAL_STORY
from src.pathfinding import find_path

if TYPE_CHECKING:
    from src.world import World


ARRIVING = "Arriving"
VISITING = "Visiting"
DEPARTING = "Departing"
SETTLED = "Settled"
DEPARTED = "Departed"

ACTIVE_WANDERER_STATES = {ARRIVING, VISITING, DEPARTING}
WANDERER_TRAVEL_STEPS_PER_DAY = 4
WANDERER_VISIT_STEPS_PER_DAY = 2
MAX_ACTIVE_WANDERERS = 2
WANDERER_DAILY_ARRIVAL_CHANCE = 0.018


@dataclass(frozen=True)
class WandererProfile:
    profile_id: str
    display_name: str
    role: str
    preferred_activities: tuple[str, ...]
    preferred_gathering_locations: tuple[str, ...]
    typical_stay_days: int
    settle_chance: float = 0.0

    @property
    def can_settle(self) -> bool:
        return self.settle_chance > 0.0


WANDERER_PROFILES: dict[str, WandererProfile] = {
    "travelling_merchant": WandererProfile(
        "travelling_merchant",
        "Travelling Merchant",
        GENERALIST,
        ("trade", "gathering", "rest"),
        ("Storage", "Village Centre", "Gathering"),
        typical_stay_days=4,
        settle_chance=0.03,
    ),
    "storyteller": WandererProfile(
        "storyteller",
        "Storyteller",
        GENERALIST,
        ("shared_moments", "celebration", "rest"),
        ("Gathering", "Village Centre", "Home"),
        typical_stay_days=5,
        settle_chance=0.04,
    ),
    "hunter": WandererProfile(
        "hunter",
        "Hunter",
        FORAGER,
        ("forage", "rest", "gathering"),
        ("Forest", "Water", "Village Centre"),
        typical_stay_days=3,
        settle_chance=0.05,
    ),
    "pilgrim": WandererProfile(
        "pilgrim",
        "Pilgrim",
        SCOUT,
        ("wandering", "ceremony", "rest"),
        ("Ceremony", "Road", "Village Centre"),
        typical_stay_days=4,
        settle_chance=0.04,
    ),
    "scholar": WandererProfile(
        "scholar",
        "Scholar",
        GENERALIST,
        ("observe", "shared_moments", "rest"),
        ("Workshop", "Skilled Villager", "Village Centre"),
        typical_stay_days=6,
        settle_chance=0.16,
    ),
    "refugee": WandererProfile(
        "refugee",
        "Refugee",
        GENERALIST,
        ("rest", "gathering", "work"),
        ("Home", "Gathering", "Village Centre"),
        typical_stay_days=7,
        settle_chance=0.42,
    ),
    "craftsman": WandererProfile(
        "craftsman",
        "Craftsman",
        BUILDER,
        ("workshop", "building", "gathering"),
        ("Construction", "Workshop", "Village Centre"),
        typical_stay_days=6,
        settle_chance=0.30,
    ),
}

WANDERER_NAMES = (
    "Mira",
    "Soren",
    "Talia",
    "Orin",
    "Vera",
    "Niko",
    "Sel",
    "Ilan",
    "Rhea",
    "Tovin",
)


def update_wanderers(world: World):
    maybe_spawn_wanderer(world)
    for agent in list(world.living_agents()):
        if is_active_wanderer(agent):
            advance_wanderer(world, agent)


def maybe_spawn_wanderer(world: World) -> Agent | None:
    if getattr(world, "settlement", None) is None or not getattr(world, "main_roads", None):
        return None
    if len(active_wanderers(world)) >= MAX_ACTIVE_WANDERERS:
        return None
    rng = random.Random(f"{world.seed}|{world.day}|wanderer-arrival")
    if rng.random() >= WANDERER_DAILY_ARRIVAL_CHANCE:
        return None
    profile_id = rng.choice(tuple(WANDERER_PROFILES))
    road_index = rng.randrange(len(world.main_roads))
    return spawn_wanderer(world, profile_id=profile_id, road_index=road_index)


def spawn_wanderer(world: World, profile_id: str | None = None, road_index: int = 0) -> Agent:
    if not getattr(world, "main_roads", None):
        raise ValueError("Wanderers require main roads before arrival.")

    profile = profile_for(profile_id)
    road_index = road_index % len(world.main_roads)
    road = world.main_roads[road_index]
    path = list(reversed(road.path))
    start_x, start_y = path[0]
    sequence = next_wanderer_sequence(world)
    name = wanderer_name(world, profile, sequence)
    appearance_seed = appearance_seed_for(world.seed, sequence + 1000, name)
    agent = Agent(
        name,
        start_x,
        start_y,
        role=profile.role,
        age=28 + sequence % 23,
        agent_id=f"wanderer-{world.day}-{sequence}",
        appearance_seed=appearance_seed,
        appearance_type=appearance_type_for_seed(appearance_seed),
        birth_settlement_id=f"beyond-{road.edge}",
        birth_settlement_name=f"Beyond the {road.edge.title()} Road",
        birth_year=world.year - (28 + sequence % 23),
        birth_day=1,
        visitor_profile=profile.profile_id,
        visitor_status=ARRIVING,
        visitor_origin=road.edge,
        visitor_arrival_day=0,
        visitor_departure_day=0,
        visitor_road_index=road_index,
        visitor_path=path,
        visitor_path_index=0,
    )
    ensure_expected_lifespan(world, agent)
    world.agents.append(agent)
    world.wanderer_arrivals_by_year[world.year] = world.wanderer_arrivals_by_year.get(world.year, 0) + 1
    record_wanderer_history(world, "Wanderer Arrived", f"A {profile.display_name.lower()} arrived on the {road.edge} road.")
    remember_visitor(world, agent, "arrived")
    return agent


def advance_wanderer(world: World, agent: Agent):
    status = getattr(agent, "visitor_status", None)
    if status == ARRIVING:
        _walk_visitor_path(agent)
        if _visitor_reached_path_end(agent):
            agent.visitor_status = VISITING
            agent.current_action = "Idle"
            agent.current_goal = "Visit"
            agent.visitor_arrival_day = world.day
            agent.visitor_departure_day = world.day + profile_for(agent.visitor_profile).typical_stay_days
            remember_visitor(world, agent, "reached the village")
            record_profile_visit_history(world, agent)
        return

    if status == VISITING:
        drift_visiting_wanderer(world, agent)
        agent.current_goal = "Visit"
        if world.day >= getattr(agent, "visitor_departure_day", world.day):
            if should_settle(world, agent):
                settle_wanderer(world, agent)
            else:
                begin_departure(world, agent)
        return

    if status == DEPARTING:
        _walk_visitor_path(agent)
        if _visitor_reached_path_end(agent):
            depart_wanderer(world, agent)


def begin_departure(world: World, agent: Agent):
    road = world.main_roads[getattr(agent, "visitor_road_index", 0) % len(world.main_roads)]
    agent.visitor_status = DEPARTING
    agent.current_action = "Leaving"
    agent.current_goal = "Depart"
    agent.visitor_path = list(road.path)
    agent.visitor_path_index = nearest_path_index(agent, agent.visitor_path)
    remember_visitor(world, agent, "departed the village")


def depart_wanderer(world: World, agent: Agent):
    profile = profile_for(agent.visitor_profile)
    agent.visitor_status = DEPARTED
    agent.current_action = "Departed"
    agent.current_goal = "Departed"
    agent.alive = False
    remember_visitor(world, agent, "left")
    record_wanderer_history(world, "Wanderer Departed", f"The {profile.display_name.lower()} left by the {agent.visitor_origin} road.")


def settle_wanderer(world: World, agent: Agent) -> Household | None:
    settlement = getattr(world, "settlement", None)
    if settlement is None:
        return None
    household_id = next_household_id(settlement)
    household = Household(
        household_id=household_id,
        household_name=wanderer_household_name(settlement, agent),
        member_ids=[],
        founder_ids=[villager_key(agent)],
        founded_year=world.year,
        household_head=villager_key(agent),
    )
    settlement.households.append(household)
    world.add_agent_to_household(agent, household)
    agent.home_settlement_id = settlement.settlement_id
    agent.home_settlement_name = settlement.name
    agent.visitor_status = SETTLED
    agent.current_action = "Idle"
    agent.current_goal = "Settle"
    ensure_family_registry(world)
    world.update_settlement_population()
    world.update_settlement_needs(force=True)
    world.wanderer_settlements_by_year[world.year] = world.wanderer_settlements_by_year.get(world.year, 0) + 1
    profile = profile_for(agent.visitor_profile)
    record_wanderer_history(world, "Wanderer Settled", f"The {profile.display_name.lower()} {agent.name} chose to remain in {settlement.name}.")
    remember_visitor(world, agent, "settled")
    return household


def should_settle(world: World, agent: Agent) -> bool:
    profile = profile_for(agent.visitor_profile)
    if not profile.can_settle:
        return False
    rng = random.Random(f"{world.seed}|{agent.agent_id}|{world.day}|settlement")
    return rng.random() < profile.settle_chance


def drift_visiting_wanderer(world: World, agent: Agent):
    profile = profile_for(agent.visitor_profile)
    agent.current_action = visitor_action_label(profile)
    destination = profile_visit_anchor(world, agent)
    if destination is None or destination == (agent.x, agent.y):
        return
    route = find_path(world, (agent.x, agent.y), destination, avoid_occupied=False)
    if not route:
        return
    _walk_route_segment(agent, route, WANDERER_VISIT_STEPS_PER_DAY)


def profile_visit_anchor(world: World, agent: Agent) -> tuple[int, int] | None:
    profile = profile_for(agent.visitor_profile)
    candidates = profile_destination_candidates(world, agent, profile)
    if not candidates:
        settlement = getattr(world, "settlement", None)
        return (settlement.x, settlement.y) if settlement is not None else None

    rng = random.Random(f"{world.seed}|{world.day}|{villager_key(agent)}|profile-drift")
    weighted = []
    for label, anchor, weight in candidates:
        distance = abs(anchor[0] - agent.x) + abs(anchor[1] - agent.y)
        score = max(1.0, weight - distance * 0.35 + rng.random() * 4)
        weighted.append((score, label, anchor))
    total = sum(score for score, _, _ in weighted)
    roll = rng.random() * total
    running = 0.0
    for score, _, anchor in weighted:
        running += score
        if roll <= running:
            return anchor
    return weighted[-1][2]


def profile_destination_candidates(
    world: World,
    agent: Agent,
    profile: WandererProfile,
) -> list[tuple[str, tuple[int, int], float]]:
    candidates: list[tuple[str, tuple[int, int], float]] = []
    for preference in profile.preferred_gathering_locations:
        candidates.extend(destination_candidates_for_preference(world, agent, preference))
    return candidates


def destination_candidates_for_preference(
    world: World,
    agent: Agent,
    preference: str,
) -> list[tuple[str, tuple[int, int], float]]:
    settlement = getattr(world, "settlement", None)
    if preference == "Village Centre" and settlement is not None:
        return [("Village Centre", (settlement.x, settlement.y), 20.0)]
    if preference == "Storage" and settlement is not None:
        return [("Storage", (stockpile.x, stockpile.y), 28.0) for stockpile in getattr(settlement, "stockpiles", [])]
    if preference == "Workshop" and settlement is not None:
        return [("Workshop", (workshop.x, workshop.y), 30.0) for workshop in getattr(settlement, "workshops", [])]
    if preference == "Construction" and settlement is not None:
        return construction_candidates(world)
    if preference == "Forest":
        return forest_candidates(world, agent)
    if preference == "Water":
        return water_candidates(world, agent)
    if preference == "Home" and settlement is not None:
        return [("Home", (home.x, home.y), 24.0) for home in getattr(settlement, "homes", [])[:6]]
    if preference == "Gathering":
        return gathering_candidates(world)
    if preference == "Ceremony":
        return ceremony_candidates(world)
    if preference == "Road":
        return road_candidates(world, agent)
    if preference == "Skilled Villager":
        return skilled_villager_candidates(world, agent)
    return []


def forest_candidates(world: World, agent: Agent) -> list[tuple[str, tuple[int, int], float]]:
    candidates = []
    for y, row in enumerate(world.tiles):
        for x, tile in enumerate(row):
            if tile.kind != "forest" or not tile.walkable:
                continue
            distance = abs(x - agent.x) + abs(y - agent.y)
            candidates.append((distance, ("Forest", (x, y), 34.0)))
    candidates.sort(key=lambda item: (item[0], item[1][1][1], item[1][1][0]))
    return [candidate for _, candidate in candidates[:5]]


def water_candidates(world: World, agent: Agent) -> list[tuple[str, tuple[int, int], float]]:
    known = list(getattr(world.colony_memory, "known_water", set()))
    candidates = []
    for x, y in known:
        access = nearest_walkable_access(world, x, y, agent)
        if access is not None:
            candidates.append(("Water", access, 18.0))
    return candidates[:4]


def construction_candidates(world: World) -> list[tuple[str, tuple[int, int], float]]:
    settlement = getattr(world, "settlement", None)
    if settlement is None:
        return []
    buildings = []
    for collection in ("homes", "workshops"):
        for building in getattr(settlement, collection, []):
            if getattr(building, "complete", True) is False:
                buildings.append(("Construction", (building.x, building.y), 34.0))
    if buildings:
        return buildings
    return [("Workshop", (workshop.x, workshop.y), 26.0) for workshop in getattr(settlement, "workshops", [])]


def gathering_candidates(world: World) -> list[tuple[str, tuple[int, int], float]]:
    from src.gatherings import active_gatherings

    gatherings = active_gatherings(world)
    return [("Gathering", cluster.center, 26.0 + cluster.size * 3.0) for cluster in gatherings[:5]]


def ceremony_candidates(world: World) -> list[tuple[str, tuple[int, int], float]]:
    from src.celebrations import active_celebration

    celebration = active_celebration(world)
    if celebration is None:
        return []
    return [("Ceremony", celebration.anchor, 36.0)]


def road_candidates(world: World, agent: Agent) -> list[tuple[str, tuple[int, int], float]]:
    candidates = []
    for road in getattr(world, "main_roads", []):
        if not road.path:
            continue
        index = min(len(road.path) - 1, max(0, len(road.path) // 2))
        candidates.append(("Road", road.path[index], 20.0))
    return candidates


def skilled_villager_candidates(world: World, agent: Agent) -> list[tuple[str, tuple[int, int], float]]:
    candidates = []
    for other in world.living_agents():
        if other is agent:
            continue
        if getattr(other, "visitor_status", None):
            continue
        score = getattr(other, "peak_influence_score", 0) + getattr(other, "years_in_role", 0)
        if score <= 0:
            continue
        candidates.append((score, ("Skilled Villager", (other.x, other.y), 18.0 + min(16.0, score))))
    candidates.sort(key=lambda item: (-item[0], item[1][1][1], item[1][1][0]))
    return [candidate for _, candidate in candidates[:4]]


def nearest_walkable_access(world: World, x: int, y: int, agent: Agent) -> tuple[int, int] | None:
    options = []
    for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        nx, ny = x + dx, y + dy
        if not (0 <= nx < world.width and 0 <= ny < world.height):
            continue
        if world.tile_at(nx, ny).walkable:
            options.append((abs(nx - agent.x) + abs(ny - agent.y), (nx, ny)))
    if not options:
        return None
    return min(options, key=lambda item: item[0])[1]


def visitor_action_label(profile: WandererProfile) -> str:
    labels = {
        "travelling_merchant": "Visiting storage",
        "hunter": "Using nearby forest",
        "scholar": "Observing village work",
        "pilgrim": "Passing through",
        "refugee": "Seeking safety",
        "craftsman": "Assisting village work",
        "storyteller": "Sharing stories",
    }
    return labels.get(profile.profile_id, "Visiting")


def _walk_route_segment(agent: Agent, route: list[tuple[int, int]], steps: int):
    if not route:
        return
    steps = min(max(1, steps), len(route))
    segment = route[:steps]
    agent.x, agent.y = segment[-1]


def _walk_visitor_path(agent: Agent):
    path = getattr(agent, "visitor_path", [])
    if not path:
        return
    start_index = min(getattr(agent, "visitor_path_index", 0), len(path) - 1)
    end_index = min(start_index + WANDERER_TRAVEL_STEPS_PER_DAY, len(path) - 1)
    if end_index == start_index:
        return
    agent.visitor_path_index = end_index
    agent.x, agent.y = path[end_index]


def _visitor_reached_path_end(agent: Agent) -> bool:
    path = getattr(agent, "visitor_path", [])
    return bool(path) and getattr(agent, "visitor_path_index", 0) >= len(path) - 1


def nearest_path_index(agent: Agent, path: list[tuple[int, int]]) -> int:
    if not path:
        return 0
    return min(range(len(path)), key=lambda index: abs(path[index][0] - agent.x) + abs(path[index][1] - agent.y))


def is_active_wanderer(agent: Agent) -> bool:
    return getattr(agent, "visitor_status", None) in ACTIVE_WANDERER_STATES


def active_wanderers(world: World) -> list[Agent]:
    return [agent for agent in world.living_agents() if is_active_wanderer(agent)]


def profile_for(profile_id: str | None) -> WandererProfile:
    if profile_id in WANDERER_PROFILES:
        return WANDERER_PROFILES[profile_id]
    return WANDERER_PROFILES["storyteller"]


def next_wanderer_sequence(world: World) -> int:
    world.wanderer_sequence += 1
    return world.wanderer_sequence


def wanderer_name(world: World, profile: WandererProfile, sequence: int) -> str:
    base = WANDERER_NAMES[sequence % len(WANDERER_NAMES)]
    return f"{base} the {profile.display_name.split()[-1]}"


def wanderer_household_name(settlement, agent: Agent) -> str:
    base = f"{agent.name.split()[0]} Hearth"
    existing = {household.household_name for household in settlement.households}
    if base not in existing:
        return base
    index = 2
    while f"{base} {index}" in existing:
        index += 1
    return f"{base} {index}"


def record_wanderer_history(world: World, title: str, description: str):
    world.history.record(
        day=world.day,
        year=world.year,
        season=world.season,
        category=LOCAL_STORY,
        title=title,
        description=description,
    )


def record_profile_visit_history(world: World, agent: Agent):
    profile = profile_for(agent.visitor_profile)
    settlement_name = getattr(getattr(world, "settlement", None), "name", "the village")
    descriptions = {
        "travelling_merchant": f"A travelling merchant spent several days around {settlement_name}'s stores and gathering places.",
        "storyteller": f"A storyteller shared quiet evenings with the people of {settlement_name}.",
        "hunter": f"A hunter rested near {settlement_name} after using the surrounding forests.",
        "pilgrim": f"A pilgrim passed through {settlement_name} on a longer road.",
        "scholar": f"A scholar lingered near {settlement_name}'s workshops to watch village life.",
        "refugee": f"A refugee sought safety among the households of {settlement_name}.",
        "craftsman": f"A craftsman looked for useful work among {settlement_name}'s builders.",
    }
    description = descriptions.get(profile.profile_id)
    if description is None:
        return
    record_wanderer_history(world, f"{profile.display_name} Visit", description)


def remember_visitor(world: World, agent: Agent, event: str):
    key = villager_key(agent)
    memory = world.visitor_memories.setdefault(
        key,
        {
            "name": agent.name,
            "profile": getattr(agent, "visitor_profile", None),
            "visits": 0,
            "events": [],
        },
    )
    if event == "arrived":
        memory["visits"] = int(memory.get("visits", 0)) + 1
    events = memory.setdefault("events", [])
    events.insert(0, {"day": world.day, "year": world.year, "event": event})
    del events[8:]
