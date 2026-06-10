from __future__ import annotations

import hashlib
from dataclasses import dataclass


ROUND = "Round"
ANGULAR = "Angular"
SOFT = "Soft"
NARROW = "Narrow"

APPEARANCE_TYPES = (ROUND, ANGULAR, SOFT, NARROW)


@dataclass(frozen=True)
class Appearance:
    seed: int
    appearance_type: str
    skin_tone: tuple[int, int, int]
    hair_color: tuple[int, int, int]
    hair_style: str
    face_shape: str
    eye_offset: int


SKIN_TONES = (
    (236, 188, 150),
    (198, 134, 88),
    (141, 85, 55),
    (224, 172, 105),
)

HAIR_COLORS = (
    (40, 28, 20),
    (95, 55, 28),
    (166, 108, 45),
    (207, 168, 95),
)

HAIR_STYLES = ("Short", "Long", "Messy", "Parted", "Curly", "Straight")


def appearance_seed_for(world_seed, index: int, name: str) -> int:
    basis = f"{world_seed if world_seed is not None else 'no-seed'}:{index}:{name}"
    return stable_seed(basis)


def appearance_type_for_seed(seed: int) -> str:
    return APPEARANCE_TYPES[seed % len(APPEARANCE_TYPES)]


def appearance_for_seed(seed: int, appearance_type: str | None = None) -> Appearance:
    chosen_type = appearance_type if appearance_type in APPEARANCE_TYPES else appearance_type_for_seed(seed)
    return Appearance(
        seed=seed,
        appearance_type=chosen_type,
        skin_tone=SKIN_TONES[(seed // 3) % len(SKIN_TONES)],
        hair_color=HAIR_COLORS[(seed // 7) % len(HAIR_COLORS)],
        hair_style=HAIR_STYLES[(seed // 11) % len(HAIR_STYLES)],
        face_shape=chosen_type,
        eye_offset=(seed // 13) % 2,
    )


def stable_seed(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
    return int(digest[:12], 16)
