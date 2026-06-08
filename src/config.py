WIDTH = 80
HEIGHT = 45
VIEWPORT_WIDTH = 76
VIEWPORT_HEIGHT = 45
TILE_SIZE = 16
CAMERA_STEP = 3
DEBUG_DRAW_GRID = False
PANEL_WIDTH = 400
PANEL_HEIGHT = 160
PANEL_HEIGTH = PANEL_HEIGHT
STARTING_AGENTS = 10
INITIAL_SPAWN_RADIUS = 3
INITIAL_SPAWN_MAX_RADIUS = 10
WORLD_SEED = None
HUNGER_RATE = 1
THIRST_RATE = 1
FATIGUE_RATE = 1
HUNGER_DEATH_THRESHOLD = 100
THIRST_DEATH_THRESHOLD = 100
SHELTER_CAPACITY = 3
SETTLEMENT_RADIUS = 10
SETTLEMENT_RESOURCE_RADIUS = 12
SETTLEMENT_EXPANDED_RESOURCE_RADIUS = 24
STOCKPILE_CAPACITY = 99
WORKSHOP_PROGRESS_REQUIRED = 3
BUILDING_MATERIAL_SHELTER_WOOD_DISCOUNT = 1
DESIRED_BUILDING_MATERIALS = 4
DESIRED_WOOD_RESERVE = 8
SHELTER_CAPACITY_BUFFER = 1
FARM_START_FOOD_DAYS = 1.5
FARM_COMFORT_FOOD_DAYS = 3.0
FARM_CREATION_MIN_DAY = 2
FARM_PLACEMENT_RADIUS_MARGIN = 4
FARM_GROWTH_THRESHOLD = 100
FARM_FOOD_CAP = 6
FARM_SEASON_GROWTH = {
    "Spring": 42,
    "Summer": 30,
    "Autumn": 26,
    "Winter": 4,
}
FARM_MAX_PLOTS_SMALL = 1
FARM_MAX_PLOTS_MEDIUM = 2
FARM_MAX_PLOTS_LARGE = 4
NEED_SCORE_HIGH_THRESHOLD = 50
NEED_SCORE_LOW_THRESHOLD = 15
NEED_SCORE_SWITCH_MARGIN = 10
STUCK_TICK_LIMIT = 3
NO_PROGRESS_TICK_LIMIT = 5
RIVER_COUNT = 3
RIVER_MIN_LENGTH = 8
RIVER_SOURCE_ELEVATION = 0.70
RIVER_WIDEN_CHANCE = 0.06
DAYS_PER_SEASON = 20
TICKS_PER_DAY = 50
ENV_EVENT_CHANCE_PER_DAY = 0.06
ENV_EVENT_MIN_DURATION_DAYS = 3
ENV_EVENT_MAX_DURATION_DAYS = 6
MAX_ACTIVE_ENV_EVENTS = 2
WILDLIFE_DENSITY = 0.010
WILDLIFE_MAX_ANIMALS = 45
WILDLIFE_WANDER_CHANCE = 0.02
SEASONS = ["Spring", "Summer", "Autumn", "Winter"]
SEASON_FOOD_GROWTH_MODIFIERS = {
    "Spring": 1.45,
    "Summer": 0.95,
    "Autumn": 1.20,
    "Winter": 0.25,
}
SEASON_WOOD_GROWTH_MODIFIERS = {
    "Spring": 1.10,
    "Summer": 1.00,
    "Autumn": 0.90,
    "Winter": 0.65,
}
SEASON_MOISTURE_MODIFIERS = {
    "Spring": 1.10,
    "Summer": 0.85,
    "Autumn": 1.00,
    "Winter": 0.80,
}

SCREEN_WIDTH = VIEWPORT_WIDTH * TILE_SIZE + PANEL_WIDTH
SCREEN_HEIGHT = VIEWPORT_HEIGHT * TILE_SIZE

FPS = 30
SIM_TICKS_PER_SECOND = 8

COLORS = {
    "grass": (75, 145, 75),
    "forest": (25, 95, 35),
    "plain": (104, 156, 82),
    "hill": (126, 136, 86),
    "wetland": (55, 118, 104),
    "dry": (150, 132, 82),
    "water": (45, 95, 170),
    "mountain": (110, 110, 110),
    "shelter": (145, 95, 45),
    "food": (230, 80, 80),
    "wood": (130, 80, 35),
    "wildlife": (220, 205, 150),
    "settlement": (255, 220, 120),
    "stockpile_food": (240, 120, 100),
    "stockpile_wood": (170, 110, 55),
    "workshop": (200, 165, 95),
    "farm_border": (120, 74, 34),
    "farm_crop": (190, 175, 70),
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

SEASONAL_TERRAIN_COLORS = {
    "Spring": {
        "grass": (88, 165, 82),
        "forest": (32, 115, 45),
        "plain": (122, 174, 86),
        "hill": (138, 150, 92),
        "wetland": (60, 140, 116),
        "dry": (162, 146, 90),
        "water": (54, 116, 188),
        "mountain": (120, 124, 118),
        "shelter": (145, 95, 45),
    },
    "Summer": {
        "grass": (94, 142, 66),
        "forest": (30, 92, 37),
        "plain": (156, 151, 76),
        "hill": (142, 126, 78),
        "wetland": (74, 118, 86),
        "dry": (176, 140, 68),
        "water": (38, 82, 150),
        "mountain": (106, 104, 98),
        "shelter": (145, 95, 45),
    },
    "Autumn": {
        "grass": (112, 138, 66),
        "forest": (112, 82, 32),
        "plain": (150, 122, 64),
        "hill": (136, 108, 72),
        "wetland": (83, 110, 82),
        "dry": (150, 118, 72),
        "water": (44, 92, 158),
        "mountain": (112, 104, 96),
        "shelter": (145, 95, 45),
    },
    "Winter": {
        "grass": (142, 154, 138),
        "forest": (72, 92, 80),
        "plain": (160, 164, 142),
        "hill": (152, 152, 138),
        "wetland": (112, 140, 148),
        "dry": (156, 148, 126),
        "water": (74, 102, 150),
        "mountain": (172, 174, 168),
        "shelter": (135, 105, 76),
    },
}

TERRAIN_LABELS = {
    "water": "Water",
    "forest": "Forest",
    "mountain": "Mountain",
    "hill": "Hill",
    "plain": "Plain",
    "wetland": "Wetland",
    "dry": "Dry",
    "grass": "Grass",
    "shelter": "Shelter",
}

SYMBOL_LABELS = {
    "@": "Villager",
    "f": "Food",
    "w": "Wood",
    "r": "Rabbit",
    "d": "Deer",
    "b": "Boar",
    "v": "Waterfowl",
    "+": "Settlement",
    "F": "Food Pile",
    "W": "Wood Pile",
    "T": "Workshop",
    "#": "Farm Plot",
}
