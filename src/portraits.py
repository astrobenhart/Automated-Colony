from __future__ import annotations

import pygame

from src.appearance import appearance_for_seed, stable_seed
from src.lifecycle import ELDER
from src.role_colors import color_for_role


SPRITE_SIZE = 32
SPRITE_SCALE = 3
DISPLAY_SIZE = SPRITE_SIZE * SPRITE_SCALE
CHIBI_PROPORTIONS = {
    "head": 16,
    "body": 12,
    "legs": 4,
}

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
    clothing = color_for_role(getattr(agent, "role", None))
    highlight, midtone, shadow = role_color_palette(clothing)
    hair = ELDER_HAIR if lifecycle_stage == ELDER else appearance.hair_color
    return {
        "skin": appearance.skin_tone,
        "hair": hair,
        "hair_highlight": shade_color(hair, 1.28),
        "hair_shadow": shade_color(hair, 0.58),
        "clothing": midtone,
        "clothing_highlight": highlight,
        "clothing_shadow": shadow,
        "accent": accent_color_for_seed(sprite_seed_for(agent)),
    }


def sprite_proportions() -> dict[str, int]:
    return dict(CHIBI_PROPORTIONS)


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
    pygame.draw.rect(surface, SHADOW, pygame.Rect(9, 31, 14, 1))


def draw_body_outline_layer(surface: pygame.Surface):
    # Chibi RPG proportions: a large rounded head over a compact body.
    pygame.draw.rect(surface, OUTLINE, pygame.Rect(10, 2, 12, 1))
    pygame.draw.rect(surface, OUTLINE, pygame.Rect(8, 3, 16, 3))
    pygame.draw.rect(surface, OUTLINE, pygame.Rect(7, 6, 18, 9))
    pygame.draw.rect(surface, OUTLINE, pygame.Rect(8, 15, 16, 3))
    pygame.draw.rect(surface, OUTLINE, pygame.Rect(10, 18, 12, 1))
    pygame.draw.rect(surface, OUTLINE, pygame.Rect(9, 19, 14, 7))
    pygame.draw.rect(surface, OUTLINE, pygame.Rect(8, 21, 3, 4))
    pygame.draw.rect(surface, OUTLINE, pygame.Rect(21, 21, 3, 4))
    pygame.draw.rect(surface, OUTLINE, pygame.Rect(11, 26, 4, 5))
    pygame.draw.rect(surface, OUTLINE, pygame.Rect(17, 26, 4, 5))


def draw_skin_layer(surface: pygame.Surface, appearance):
    skin = appearance.skin_tone
    if appearance.face_shape == "Narrow":
        face_blocks = (
            pygame.Rect(11, 6, 10, 2),
            pygame.Rect(10, 8, 12, 7),
            pygame.Rect(11, 15, 10, 2),
        )
    elif appearance.face_shape == "Angular":
        face_blocks = (
            pygame.Rect(10, 6, 12, 2),
            pygame.Rect(9, 8, 14, 7),
            pygame.Rect(11, 15, 10, 2),
        )
    else:
        face_blocks = (
            pygame.Rect(10, 5, 12, 2),
            pygame.Rect(9, 7, 14, 8),
            pygame.Rect(10, 15, 12, 2),
        )

    for block in face_blocks:
        pygame.draw.rect(surface, skin, block)
    pygame.draw.rect(surface, shade_color(skin, 1.14), pygame.Rect(11, 8, 3, 5))
    pygame.draw.rect(surface, shade_color(skin, 0.82), pygame.Rect(20, 9, 2, 6))
    pygame.draw.rect(surface, skin, pygame.Rect(8, 10, 1, 4))
    pygame.draw.rect(surface, skin, pygame.Rect(23, 10, 1, 4))
    pygame.draw.rect(surface, skin, pygame.Rect(8, 22, 2, 3))
    pygame.draw.rect(surface, skin, pygame.Rect(22, 22, 2, 3))


def draw_hair_layer(surface: pygame.Surface, appearance, lifecycle_stage: str | None):
    hair = ELDER_HAIR if lifecycle_stage == ELDER else appearance.hair_color
    hair_shadow = shade_color(hair, 0.58)
    hair_highlight = shade_color(hair, 1.28)

    if appearance.hair_style == "Short":
        pygame.draw.rect(surface, hair_shadow, pygame.Rect(8, 4, 16, 5))
        pygame.draw.rect(surface, hair, pygame.Rect(9, 3, 14, 5))
        pygame.draw.rect(surface, hair, pygame.Rect(8, 8, 4, 4))
        pygame.draw.rect(surface, hair_shadow, pygame.Rect(20, 8, 4, 5))
        pygame.draw.rect(surface, hair_highlight, pygame.Rect(12, 4, 5, 1))
        pygame.draw.rect(surface, hair, pygame.Rect(13, 8, 3, 2))
    elif appearance.hair_style == "Long":
        pygame.draw.rect(surface, hair_shadow, pygame.Rect(7, 5, 18, 15))
        pygame.draw.rect(surface, hair, pygame.Rect(8, 3, 16, 8))
        pygame.draw.rect(surface, hair, pygame.Rect(7, 9, 4, 10))
        pygame.draw.rect(surface, hair_shadow, pygame.Rect(21, 9, 4, 10))
        pygame.draw.rect(surface, hair_highlight, pygame.Rect(11, 5, 5, 1))
        pygame.draw.rect(surface, hair_shadow, pygame.Rect(9, 17, 14, 2))
    elif appearance.hair_style == "Messy":
        for rect in [
            pygame.Rect(8, 5, 16, 5),
            pygame.Rect(10, 3, 4, 4),
            pygame.Rect(15, 1, 4, 6),
            pygame.Rect(20, 4, 4, 5),
            pygame.Rect(6, 7, 4, 4),
            pygame.Rect(8, 9, 4, 6),
            pygame.Rect(21, 9, 3, 5),
        ]:
            pygame.draw.rect(surface, hair, rect)
        pygame.draw.rect(surface, hair_shadow, pygame.Rect(20, 10, 4, 5))
        pygame.draw.rect(surface, hair_highlight, pygame.Rect(11, 5, 4, 1))
    elif appearance.hair_style == "Parted":
        pygame.draw.rect(surface, hair, pygame.Rect(8, 4, 8, 6))
        pygame.draw.rect(surface, hair_shadow, pygame.Rect(16, 4, 8, 6))
        pygame.draw.rect(surface, hair, pygame.Rect(7, 9, 5, 7))
        pygame.draw.rect(surface, hair_shadow, pygame.Rect(20, 9, 5, 7))
        pygame.draw.rect(surface, hair_shadow, pygame.Rect(15, 4, 2, 11))
        pygame.draw.rect(surface, hair_highlight, pygame.Rect(11, 5, 3, 1))
    elif appearance.hair_style == "Straight":
        pygame.draw.rect(surface, hair, pygame.Rect(8, 3, 16, 7))
        pygame.draw.rect(surface, hair, pygame.Rect(8, 10, 3, 7))
        pygame.draw.rect(surface, hair_shadow, pygame.Rect(21, 10, 3, 7))
        pygame.draw.rect(surface, hair_shadow, pygame.Rect(10, 9, 12, 2))
        pygame.draw.rect(surface, hair_highlight, pygame.Rect(12, 5, 6, 1))
    else:
        for x, y in [(8, 5), (11, 3), (15, 3), (19, 4), (7, 9), (21, 9), (9, 12), (20, 12)]:
            pygame.draw.rect(surface, hair, pygame.Rect(x, y, 4, 4))
        pygame.draw.rect(surface, hair_shadow, pygame.Rect(21, 10, 4, 5))
        pygame.draw.rect(surface, hair_highlight, pygame.Rect(12, 5, 3, 1))


def draw_eye_layer(surface: pygame.Surface, appearance):
    y = 12 + appearance.eye_offset
    pygame.draw.rect(surface, EYE, pygame.Rect(12, y, 3, 3))
    pygame.draw.rect(surface, EYE, pygame.Rect(18, y, 3, 3))
    pygame.draw.rect(surface, (245, 245, 230), pygame.Rect(13, y, 1, 1))
    pygame.draw.rect(surface, (245, 245, 230), pygame.Rect(19, y, 1, 1))
    pygame.draw.rect(surface, (120, 65, 65), pygame.Rect(15, 16, 3, 1))


def draw_body_layer(surface: pygame.Surface, role: str | None, seed: int):
    highlight, clothing, shadow = role_color_palette(color_for_role(role))
    accent = accent_color_for_seed(seed)

    pygame.draw.rect(surface, shadow, pygame.Rect(10, 19, 12, 7))
    pygame.draw.rect(surface, clothing, pygame.Rect(11, 18, 10, 7))
    pygame.draw.rect(surface, clothing, pygame.Rect(12, 25, 8, 2))
    pygame.draw.rect(surface, highlight, pygame.Rect(12, 19, 6, 2))
    pygame.draw.rect(surface, shade_color(clothing, 1.08), pygame.Rect(13, 21, 3, 3))
    pygame.draw.rect(surface, shadow, pygame.Rect(18, 21, 3, 5))
    pygame.draw.rect(surface, shadow, pygame.Rect(12, 26, 8, 1))
    pygame.draw.rect(surface, accent, pygame.Rect(15, 20, 2, 6))
    pygame.draw.rect(surface, BOOT, pygame.Rect(11, 27, 4, 4))
    pygame.draw.rect(surface, BOOT, pygame.Rect(17, 27, 4, 4))
    pygame.draw.rect(surface, shade_color(BOOT, 1.25), pygame.Rect(12, 27, 2, 1))
    pygame.draw.rect(surface, shade_color(BOOT, 1.25), pygame.Rect(18, 27, 2, 1))


def draw_accent_layer(surface: pygame.Surface, seed: int):
    accent = accent_color_for_seed(seed)
    if seed % 3 == 0:
        pygame.draw.rect(surface, accent, pygame.Rect(20, 18, 2, 2))
    elif seed % 3 == 1:
        pygame.draw.rect(surface, accent, pygame.Rect(11, 23, 3, 1))
        pygame.draw.rect(surface, accent, pygame.Rect(18, 23, 3, 1))
    else:
        pygame.draw.rect(surface, accent, pygame.Rect(14, 24, 4, 1))


def accent_color_for_seed(seed: int) -> tuple[int, int, int]:
    palette = (
        (245, 225, 120),
        (130, 220, 205),
        (220, 140, 210),
        (230, 180, 95),
    )
    return palette[(seed // 17) % len(palette)]


def role_color_palette(base: tuple[int, int, int]) -> tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]:
    return (
        shade_color(base, 1.32),
        base,
        shade_color(base, 0.48),
    )


def shade_color(color: tuple[int, int, int], factor: float) -> tuple[int, int, int]:
    return tuple(max(0, min(255, int(channel * factor))) for channel in color)


def clear_portrait_cache():
    clear_sprite_cache()


def clear_sprite_cache():
    _sprite_cache.clear()
