GENERALIST = "Generalist"
FORAGER = "Forager"
BUILDER = "Builder"
SCOUT = "Scout"

FOOD = "food"
WOOD = "wood"
WATER = "water"

ROLES = (GENERALIST, FORAGER, BUILDER, SCOUT)

ROLE_ASSIGNMENT_CYCLE = (
    GENERALIST,
    GENERALIST,
    GENERALIST,
    GENERALIST,
    FORAGER,
    FORAGER,
    BUILDER,
    BUILDER,
    SCOUT,
    FORAGER,
    GENERALIST,
    GENERALIST,
    GENERALIST,
    GENERALIST,
    FORAGER,
    FORAGER,
    BUILDER,
    BUILDER,
    BUILDER,
    SCOUT,
)

ROLE_GOAL_BONUSES = {
    FORAGER: {
        "Gather food": 18,
        "Deposit food": 4,
    },
    BUILDER: {
        "Gather wood": 20,
        "Build shelter": 12,
        "Workshop": 18,
        "Deposit wood": 4,
    },
    SCOUT: {
        "Explore": 40,
    },
    GENERALIST: {},
}

DISCOVERY_RADII = {
    SCOUT: {
        FOOD: 6,
        WOOD: 6,
        WATER: 6,
    },
    FORAGER: {
        FOOD: 5,
        WOOD: 4,
        WATER: 5,
    },
    GENERALIST: {
        FOOD: 4,
        WOOD: 4,
        WATER: 4,
    },
    BUILDER: {
        FOOD: 2,
        WOOD: 3,
        WATER: 2,
    },
}


def role_for_index(index: int) -> str:
    return ROLE_ASSIGNMENT_CYCLE[index % len(ROLE_ASSIGNMENT_CYCLE)]


def role_goal_bonus(role: str, goal_name: str) -> int:
    return ROLE_GOAL_BONUSES.get(role, {}).get(goal_name, 0)


def discovery_radius(role: str, resource_type: str) -> int:
    role_radii = DISCOVERY_RADII.get(role, DISCOVERY_RADII[GENERALIST])
    return role_radii.get(resource_type, DISCOVERY_RADII[GENERALIST].get(resource_type, 4))


def is_valid_role(role: str) -> bool:
    return role in ROLES
