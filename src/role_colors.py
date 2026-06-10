from src.config import COLORS
from src.roles import BUILDER, FORAGER, GENERALIST, SCOUT


ROLE_COLOR_KEYS = {
    GENERALIST: "role_generalist",
    FORAGER: "role_forager",
    BUILDER: "role_builder",
    SCOUT: "role_scout",
}


def color_for_role(role: str | None) -> tuple[int, int, int]:
    return COLORS.get(ROLE_COLOR_KEYS.get(role, "agent"), COLORS["agent"])
