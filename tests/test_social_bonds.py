from src.actions import GatherFoodAction
from src.agent import Agent
from src.social_bonds import (
    CLOSE_COMPANION,
    OFTEN_SEEN_WITH,
    SOCIAL_BOND_LABELS,
    TRUSTED_NEIGHBOR,
    social_bond_label_for_score,
    social_bonds,
)
from src.social_memory import SocialMemoryEntry
from src.tile import Tile
from src.villager_inspection import villager_detail_sections
from src.world import World


FORBIDDEN_BOND_WORDS = {
    "Partner",
    "Spouse",
    "Mate",
    "Parent",
    "Child",
    "Sibling",
    "Family",
    "Household",
    "Couple",
    "Romantic",
}


def make_world(width: int = 5, height: int = 5) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def remember(agent: Agent, villager_id: str, name: str, score: int):
    agent.social_memory[villager_id] = SocialMemoryEntry(
        villager_id=villager_id,
        display_name=name,
        familiarity_score=score,
        last_seen_day=10,
    )


def test_social_bond_labels_derive_from_existing_familiarity_levels():
    assert social_bond_label_for_score(1) is None
    assert social_bond_label_for_score(2) == OFTEN_SEEN_WITH
    assert social_bond_label_for_score(10) == TRUSTED_NEIGHBOR
    assert social_bond_label_for_score(30) == CLOSE_COMPANION


def test_social_bonds_do_not_appear_for_strangers():
    agent = Agent("Ari", 1, 1)
    remember(agent, "bryn", "Bryn", 1)

    assert social_bonds(agent) == []


def test_social_bonds_are_capped_to_top_three():
    agent = Agent("Ari", 1, 1)
    remember(agent, "bryn", "Bryn", 30)
    remember(agent, "cato", "Cato", 30)
    remember(agent, "dara", "Dara", 10)
    remember(agent, "eli", "Eli", 2)

    bonds = social_bonds(agent)

    assert [(bond.label, bond.name) for bond in bonds] == [
        (CLOSE_COMPANION, "Bryn"),
        (CLOSE_COMPANION, "Cato"),
        (TRUSTED_NEIGHBOR, "Dara"),
    ]


def test_social_bond_labels_avoid_family_and_romance_wording():
    for label in SOCIAL_BOND_LABELS:
        assert not any(word.lower() in label.lower() for word in FORBIDDEN_BOND_WORDS)


def test_missing_social_memory_is_safe():
    class Mystery:
        name = "Mystery"

    assert social_bonds(Mystery()) == []


def test_character_card_formats_social_bonds_without_raw_scores():
    agent = Agent("Ari", 1, 1)
    remember(agent, "bryn", "Bryn", 30)
    remember(agent, "cato", "Cato", 10)

    sections = dict(villager_detail_sections(agent))
    rendered = "\n".join(f"{label}: {value}" for label, value in sections["Bonds"])

    assert ("Close Companion", "Bryn") in sections["Bonds"]
    assert ("Trusted Neighbor", "Cato") in sections["Bonds"]
    assert "30" not in rendered
    assert "10" not in rendered


def test_social_bonds_have_no_behavior_effects():
    world = make_world()
    world.tiles[2][2].food = 1
    baseline = Agent("Ari", 2, 2, hunger=55)
    with_bonds = Agent("Ari", 2, 2, hunger=55)
    remember(with_bonds, "bryn", "Bryn", 30)

    world.agents = [baseline]
    baseline_action = baseline.choose_action(world)

    world.agents = [with_bonds]
    bond_action = with_bonds.choose_action(world)

    assert isinstance(bond_action, GatherFoodAction)
    assert type(bond_action) is type(baseline_action)
    assert with_bonds.current_goal == baseline.current_goal
