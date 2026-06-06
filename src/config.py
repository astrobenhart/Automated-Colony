WIDTH = 80
HEIGHT = 45
VIEWPORT_WIDTH = 68
VIEWPORT_HEIGHT = 39
TILE_SIZE = 16
CAMERA_STEP = 3
DEBUG_DRAW_GRID = False
PANEL_WIDTH = 400
PANEL_HEIGHT = 160
PANEL_HEIGTH = PANEL_HEIGHT
STARTING_AGENTS = 10
WORLD_SEED = None
HUNGER_RATE = 1
THIRST_RATE = 1
FATIGUE_RATE = 1
HUNGER_DEATH_THRESHOLD = 100
THIRST_DEATH_THRESHOLD = 100
SHELTER_CAPACITY = 3
STUCK_TICK_LIMIT = 3

SCREEN_WIDTH = VIEWPORT_WIDTH * TILE_SIZE + PANEL_WIDTH
SCREEN_HEIGHT = VIEWPORT_HEIGHT * TILE_SIZE

FPS = 30
SIM_TICKS_PER_SECOND = 8

COLORS = {
    "grass": (75, 145, 75),
    "forest": (25, 95, 35),
    "water": (45, 95, 170),
    "mountain": (110, 110, 110),
    "shelter": (145, 95, 45),
    "food": (230, 80, 80),
    "wood": (130, 80, 35),
    "agent": (245, 245, 245),
    "dead": (90, 90, 90),
    "grid": (20, 20, 20),
    "panel": (24, 24, 28),
    "text": (230, 230, 230),
    "muted": (160, 160, 160),
    "warning": (240, 180, 80),
    "selection": (255, 235, 90),
    "selection_agent": (120, 215, 255),
}
