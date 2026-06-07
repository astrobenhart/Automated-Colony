GENERALIST = "Generalist"
FORAGER = "Forager"
BUILDER = "Builder"
SCOUT = "Scout"

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
        "Deposit wood": 4,
    },
    SCOUT: {
        "Explore": 40,
    },
    GENERALIST: {},
}


def role_for_index(index: int) -> str:
    return ROLE_ASSIGNMENT_CYCLE[index % len(ROLE_ASSIGNMENT_CYCLE)]


def role_goal_bonus(role: str, goal_name: str) -> int:
    return ROLE_GOAL_BONUSES.get(role, {}).get(goal_name, 0)


def is_valid_role(role: str) -> bool:
    return role in ROLES
