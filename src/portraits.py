from __future__ import annotations

import pygame

from src.appearance import appearance_for_seed, stable_seed
from src.lifecycle import ELDER
from src.role_colors import color_for_role


SPRITE_SIZE = 32
SPRITE_SCALE = 3
DISPLAY_SIZE = SPRITE_SIZE * SPRITE_SCALE

# Backward-compatible names for the first overlay consumer.
PORTRAIT_SIZE = SPRITE_SIZE
PORTRAIT_SCALE = SPRITE_SCALE

BACKGROUND = (34, 34, 40)
OUTLINE = (24, 22, 22)
EYE = (18, 18, 22)
ELDER_HAIR = (205, 205, 190)
BOOT = (48, 42, 42)
SHADOW = (20, 20, 24, 150)

_sprite_cache: dict[tuple, pygame.Surface] = {}


def portrait_seed_for(agent) -> int:
    return sprite_seed_for(agent)


def sprite_seed_for(agent) -> int:
    if getattr(agent, "appearance_seed", None) is not None:
        return agent.appearance_seed
    identity = getattr(agent, "agent_id", None) or getattr(agent, "name", "Villager")
    return stable_seed(str(identity))


def portrait_appearance_for(agent):
    return sprite_appearance_for(agent)


def sprite_appearance_for(agent):
    return appearance_for_seed(
        sprite_seed_for(agent),
        getattr(agent, "appearance_type", None),
    )


def portrait_cache_key(agent) -> tuple:
    return sprite_cache_key(agent)


def sprite_cache_key(agent) -> tuple:
    return (
        sprite_seed_for(agent),
        getattr(agent, "appearance_type", None),
        getattr(agent, "lifecycle_stage", None),
        getattr(agent, "role", None),
    )


def portrait_layer_metadata(agent) -> dict[str, tuple[int, int, int]]:
    return sprite_layer_metadata(agent)


def sprite_layer_metadata(agent) -> dict[str, tuple[int, int, int]]:
    appearance = sprite_appearance_for(agent)
    lifecycle_stage = getattr(agent, "lifecycle_stage", None)
    return {
        "skin": appearance.skin_tone,
        "hair": ELDER_HAIR if lifecycle_stage == ELDER else appearance.hair_color,
        "clothing": color_for_role(getattr(agent, "role", None)),
        "accent": accent_color_for_seed(sprite_seed_for(agent)),
    }


def generate_villager_portrait(agent) -> pygame.Surface:
    return generate_villager_sprite(agent)


def generate_villager_sprite(agent) -> pygame.Surface:
    key = sprite_cache_key(agent)
    if key not in _sprite_cache:
        base = draw_character_sprite_surface(agent)
        _sprite_cache[key] = pygame.transform.scale(
            base,
            (DISPLAY_SIZE, DISPLAY_SIZE),
        )
    return _sprite_cache[key]


def draw_portrait_surface(agent) -> pygame.Surface:
    return draw_character_sprite_surface(agent)


def draw_character_sprite_surface(agent) -> pygame.Surface:
    appearance = sprite_appearance_for(agent)
    surface = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
    surface.fill(BACKGROUND)

    draw_shadow_layer(surface)
    draw_body_outline_layer(surface)
    draw_skin_layer(surface, appearance)
    draw_hair_layer(surface, appearance, getattr(agent, "lifecycle_stage", None))
    draw_eye_layer(surface, appearance)
    draw_body_layer(surface, getattr(agent, "role", None), sprite_seed_for(agent))
    draw_accent_layer(surface, sprite_seed_for(agent))
    return surface


def draw_shadow_layer(surface: pygame.Surface):
    pygame.draw.rect(surface, SHADOW, pygame.Rect(9, 30, 14, 1))


def draw_body_outline_layer(surface: pygame.Surface):
    # Compact RPG proportions: large head, small torso, short legs, tiny arms.
    pygame.draw.rect(surface, OUTLINE, pygame.Rect(9, 4, 14, 13))
    pygame.draw.rect(surface, OUTLINE, pygame.Rect(10, 16, 12, 9))
    pygame.draw.rect(surface, OUTLINE, pygame.Rect(7, 18, 4, 7))
    pygame.draw.rect(surface, OUTLINE, pygame.Rect(21, 18, 4, 7))
    pygame.draw.rect(surface, OUTLINE, pygame.Rect(10, 24, 5, 6))
    pygame.draw.rect(surface, OUTLINE, pygame.Rect(17, 24, 5, 6))


def draw_skin_layer(surface: pygame.Surface, appearance):
    skin = appearance.skin_tone
    if appearance.face_shape == "Narrow":
        face_rect = pygame.Rect(11, 6, 10, 10)
    elif appearance.face_shape == "Angular":
        face_rect = pygame.Rect(10, 6, 12, 10)
    else:
        face_rect = pygame.Rect(10, 5, 12, 11)

    pygame.draw.rect(surface, skin, face_rect)
    pygame.draw.rect(surface, skin, pygame.Rect(8, 20, 2, 4))
    pygame.draw.rect(surface, skin, pygame.Rect(22, 20, 2, 4))


def draw_hair_layer(surface: pygame.Surface, appearance, lifecycle_stage: str | None):
    hair = ELDER_HAIR if lifecycle_stage == ELDER else appearance.hair_color
    if appearance.hair_style == "Crop":
        pygame.draw.rect(surface, hair, pygame.Rect(9, 4, 14, 4))
        pygame.draw.rect(surface, hair, pygame.Rect(9, 8, 3, 5))
        pygame.draw.rect(surface, hair, pygame.Rect(20, 8, 3, 5))
    elif appearance.hair_style == "Sweep":
        pygame.draw.rect(surface, hair, pygame.Rect(9, 4, 14, 4))
        pygame.draw.rect(surface, hair, pygame.Rect(9, 8, 9, 3))
        pygame.draw.rect(surface, hair, pygame.Rect(8, 7, 4, 7))
    elif appearance.hair_style == "Parted":
        pygame.draw.rect(surface, hair, pygame.Rect(9, 4, 6, 4))
        pygame.draw.rect(surface, hair, pygame.Rect(17, 4, 6, 4))
        pygame.draw.rect(surface, hair, pygame.Rect(8, 8, 4, 5))
        pygame.draw.rect(surface, hair, pygame.Rect(20, 8, 4, 5))
    else:
        for x, y in [(9, 5), (12, 4), (16, 4), (20, 5), (8, 9), (21, 9)]:
            pygame.draw.rect(surface, hair, pygame.Rect(x, y, 4, 4))


def draw_eye_layer(surface: pygame.Surface, appearance):
    y = 11 + appearance.eye_offset
    pygame.draw.rect(surface, EYE, pygame.Rect(13, y, 2, 2))
    pygame.draw.rect(surface, EYE, pygame.Rect(18, y, 2, 2))
    pygame.draw.rect(surface, (120, 65, 65), pygame.Rect(15, 15, 3, 1))


def draw_body_layer(surface: pygame.Surface, role: str | None, seed: int):
    clothing = color_for_role(role)
    muted = tuple(max(20, int(channel * 0.58)) for channel in clothing)
    accent = accent_color_for_seed(seed)

    pygame.draw.rect(surface, muted, pygame.Rect(11, 17, 10, 8))
    pygame.draw.rect(surface, clothing, pygame.Rect(12, 17, 8, 5))
    pygame.draw.rect(surface, accent, pygame.Rect(15, 17, 2, 8))
    pygame.draw.rect(surface, BOOT, pygame.Rect(11, 25, 4, 5))
    pygame.draw.rect(surface, BOOT, pygame.Rect(17, 25, 4, 5))


def draw_accent_layer(surface: pygame.Surface, seed: int):
    accent = accent_color_for_seed(seed)
    if seed % 3 == 0:
        pygame.draw.rect(surface, accent, pygame.Rect(21, 17, 2, 2))
    elif seed % 3 == 1:
        pygame.draw.rect(surface, accent, pygame.Rect(10, 22, 3, 1))
        pygame.draw.rect(surface, accent, pygame.Rect(19, 22, 3, 1))
    else:
        pygame.draw.rect(surface, accent, pygame.Rect(14, 23, 4, 1))


def accent_color_for_seed(seed: int) -> tuple[int, int, int]:
    palette = (
        (245, 225, 120),
        (130, 220, 205),
        (220, 140, 210),
        (230, 180, 95),
    )
    return palette[(seed // 17) % len(palette)]


def clear_portrait_cache():
    clear_sprite_cache()


def clear_sprite_cache():
    _sprite_cache.clear()
