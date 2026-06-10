from src.actions import GatherFoodAction
from src.agent import Agent
from src.death_memory import death_history_description, record_death
from src.overlays.history import active_remembrance_events, remembered_dead_card
from src.roles import BUILDER
from src.social_memory import SocialMemoryEntry, update_social_memory
from src.tile import Tile
from src.villager_inspection import villager_detail_sections
from src.world import World, create_world


def make_world(width: int = 8, height: int = 8) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def remember(observer: Agent, target: Agent, score: int, day: int):
    key = target.agent_id or target.name
    observer.social_memory[key] = SocialMemoryEntry(
        villager_id=key,
        display_name=target.name,
        familiarity_score=score,
        last_seen_day=day,
    )


def test_spawned_villagers_receive_home_settlement_identity():
    world = create_world(width=20, height=20, agent_count=4, seed=123)

    assert world.settlement is not None
    assert world.settlement.settlement_id is not None
    assert all(agent.home_settlement_id == world.settlement.settlement_id for agent in world.agents)
    assert all(agent.home_settlement_name == world.settlement.name for agent in world.agents)
    assert all(agent.birth_settlement_id == agent.home_settlement_id for agent in world.agents)
    assert all(agent.birth_settlement_name == agent.home_settlement_name for agent in world.agents)


def test_missing_settlement_identity_is_safe_in_character_card():
    agent = Agent("Ari", 1, 1)

    sections = dict(villager_detail_sections(agent))

    assert "Identity" in sections
    assert not any(label == "Home" for label, _ in sections["Identity"])


def test_character_card_formats_home_settlement():
    agent = Agent("Ari", 1, 1, home_settlement_name="Oakvale")

    sections = dict(villager_detail_sections(agent))

    assert ("Home", "Oakvale") in sections["Identity"]


def test_death_history_wording_includes_home_settlement_when_available():
    world = make_world()
    target = Agent(
        "Rowan",
        1,
        1,
        agent_id="rowan",
        role=BUILDER,
        home_settlement_id="oakvale-1",
        home_settlement_name="Oakvale",
    )
    world.agents = [target]

    record = record_death(world, target, "thirst")

    assert "Rowan of Oakvale" in death_history_description(record)
    assert "Rowan of Oakvale" in world.history.recent(1)[0].description


def test_death_history_wording_falls_back_without_settlement():
    world = make_world()
    target = Agent("Rowan", 1, 1, agent_id="rowan", role=BUILDER)
    world.agents = [target]

    record = record_death(world, target, "thirst")

    assert "Rowan, an Adult Builder, died of thirst." in death_history_description(record)


def test_chronicle_remembrance_uses_home_settlement_when_available():
    world = make_world()
    ari = Agent("Ari", 1, 1, home_settlement_name="Oakvale", remembering="Rowan", remembrance_expires_day=5)
    world.day = 2
    world.agents = [ari]

    assert active_remembrance_events(world) == ["Ari of Oakvale is remembering Rowan."]


def test_remembered_dead_card_uses_settlement_identity_when_available():
    world = make_world()
    target = Agent("Rowan", 1, 1, agent_id="rowan", role=BUILDER, home_settlement_name="Oakvale")
    world.agents = [target]

    record = record_death(world, target, "thirst")
    card = remembered_dead_card(record)

    assert card[0].text == "Rowan of Oakvale"


def test_settlement_identity_does_not_change_social_memory_growth():
    world = make_world()
    ari = Agent("Ari", 1, 1, agent_id="ari", home_settlement_name="Oakvale")
    bryn = Agent("Bryn", 2, 1, agent_id="bryn", home_settlement_name="Oakvale")
    world.agents = [ari, bryn]

    update_social_memory(world, radius=4)

    assert ari.social_memory["bryn"].familiarity_score == 1
    assert bryn.social_memory["ari"].familiarity_score == 1


def test_settlement_identity_does_not_change_remembrance_rules():
    world = make_world()
    target = Agent("Rowan", 1, 1, agent_id="rowan", home_settlement_name="Oakvale")
    seen_once = Agent("Ari", 2, 1, agent_id="ari", home_settlement_name="Oakvale")
    remember(seen_once, target, score=2, day=1)
    world.agents = [target, seen_once]

    record = record_death(world, target, "thirst")

    assert record.remembered_by == []
    assert seen_once.remembering is None


def test_settlement_identity_does_not_change_ai_behavior():
    baseline_world = make_world()
    baseline_world.tiles[2][2].food = 1
    baseline = Agent("Ari", 2, 2, hunger=55)
    baseline_world.agents = [baseline]

    identity_world = make_world()
    identity_world.tiles[2][2].food = 1
    with_identity = Agent("Ari", 2, 2, hunger=55, home_settlement_name="Oakvale")
    identity_world.agents = [with_identity]

    baseline_action = baseline.choose_action(baseline_world)
    identity_action = with_identity.choose_action(identity_world)

    assert isinstance(identity_action, GatherFoodAction)
    assert type(identity_action) is type(baseline_action)
    assert with_identity.current_goal == baseline.current_goal
