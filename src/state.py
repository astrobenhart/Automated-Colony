CONTENT = "Content"
HUNGRY = "Hungry"
THIRSTY = "Thirsty"
TIRED = "Tired"
RECOVERING = "Recovering"
WORKING = "Working"
EXPLORING = "Exploring"
RESTING = "Resting"
IDLE = "Idle"
DEAD = "Dead"

STATE_LABELS = (
    CONTENT,
    HUNGRY,
    THIRSTY,
    TIRED,
    RECOVERING,
    WORKING,
    EXPLORING,
    RESTING,
    IDLE,
    DEAD,
)

THIRSTY_THRESHOLD = 50
HUNGRY_THRESHOLD = 50
TIRED_THRESHOLD = 70

RESTING_ACTIONS = {"Sleeping"}
EXPLORING_ACTIONS = {"Wandering"}
WORKING_ACTION_PREFIXES = (
    "Building",
    "Depositing",
    "Gathering",
    "Harvesting",
    "Seeking",
    "Working",
)


def state_label(agent, world=None) -> str:
    if not agent.alive or agent.current_action == DEAD:
        return DEAD
    if agent.current_action == RECOVERING:
        return RECOVERING
    if agent.thirst >= THIRSTY_THRESHOLD:
        return THIRSTY
    if agent.hunger >= HUNGRY_THRESHOLD:
        return HUNGRY
    if agent.fatigue >= TIRED_THRESHOLD:
        return TIRED
    if agent.current_action in RESTING_ACTIONS:
        return RESTING
    if agent.current_action.startswith(WORKING_ACTION_PREFIXES):
        return WORKING
    if agent.current_action in EXPLORING_ACTIONS:
        return EXPLORING
    if agent.current_action == IDLE and (agent.hunger > 0 or agent.thirst > 0 or agent.fatigue > 0):
        return IDLE
    return CONTENT
