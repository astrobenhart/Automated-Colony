DILIGENT = "Diligent"
CURIOUS = "Curious"
CALM = "Calm"
FRIENDLY = "Friendly"
CAUTIOUS = "Cautious"
BOLD = "Bold"
LAZY = "Lazy"
GRUMPY = "Grumpy"
STUBBORN = "Stubborn"
TIMID = "Timid"

TRAITS = (
    DILIGENT,
    CURIOUS,
    CALM,
    FRIENDLY,
    CAUTIOUS,
    BOLD,
    LAZY,
    GRUMPY,
    STUBBORN,
    TIMID,
)


def is_valid_trait(trait: str) -> bool:
    return trait in TRAITS


def trait_for_index(index: int) -> str:
    return TRAITS[index % len(TRAITS)]
