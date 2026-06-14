from src.actions import GatherFoodAction
from src.agent import Agent
from src.influence import (
    EMERGING,
    LOW,
    NOTABLE,
    RESPECTED,
    influence_label,
    influence_label_for_score,
    influence_score,
    peak_influence_label,
    update_agent_peak_influence,
)
from src.lifecycle import ADULT, ELDER
from src.roles import ROLES
from src.social_memory import SocialMemoryEntry
from src.tile import Tile
from src.world import World


def make_world(width: int = 8, height: int = 8) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    return world


def remember(observer: Agent, target: Agent, score: int, day: int):
    observer.social_memory[target.agent_id or target.name] = SocialMemoryEntry(
        villager_id=target.agent_id or target.name,
        display_name=target.name,
        familiarity_score=score,
        last_seen_day=day,
    )


def test_villager_with_no_social_memory_has_low_influence():
    world = make_world()
    ari = Agent("Ari", 1, 1, agent_id="ari")
    world.agents = [ari]

    assert influence_score(ari, world) == 0
    assert influence_label(ari, world) == LOW


def test_influence_increases_when_more_villagers_know_target():
    world = make_world()
    world.day = 12
    ari = Agent("Ari", 1, 1, agent_id="ari")
    bryn = Agent("Bryn", 2, 1, agent_id="bryn")
    cato = Agent("Cato", 3, 1, agent_id="cato")
    world.agents = [ari, bryn, cato]

    remember(bryn, ari, score=2, day=12)
    one_memory_score = influence_score(ari, world)
    remember(cato, ari, score=2, day=12)

    assert influence_score(ari, world) > one_memory_score


def test_familiar_contributes_more_than_acquainted_and_seen():
    world = make_world()
    world.day = 12
    target = Agent("Ari", 1, 1, agent_id="ari")
    seen = Agent("Seen", 2, 1, agent_id="seen")
    acquainted = Agent("Acq", 3, 1, agent_id="acq")
    familiar = Agent("Fam", 4, 1, agent_id="fam")
    world.agents = [target, seen, acquainted, familiar]

    remember(seen, target, score=2, day=12)
    seen_score = influence_score(target, world)
    seen.social_memory.clear()
    remember(acquainted, target, score=10, day=12)
    acquainted_score = influence_score(target, world)
    acquainted.social_memory.clear()
    remember(familiar, target, score=30, day=12)
    familiar_score = influence_score(target, world)

    assert acquainted_score > seen_score
    assert familiar_score > acquainted_score


def test_elder_bonus_works_but_does_not_automatically_create_top_influence():
    world = make_world()
    world.day = 20
    elder = Agent("Elder", 1, 1, agent_id="elder", lifecycle_stage=ELDER)
    adult = Agent("Adult", 2, 1, agent_id="adult", lifecycle_stage=ADULT)
    observer_a = Agent("Bryn", 3, 1, agent_id="bryn")
    observer_b = Agent("Cato", 4, 1, agent_id="cato")
    world.agents = [elder, adult, observer_a, observer_b]

    remember(observer_a, adult, score=10, day=20)
    remember(observer_b, adult, score=10, day=20)

    assert influence_score(elder, world) == 2
    assert influence_score(adult, world) > influence_score(elder, world)
    assert influence_label(elder, world) == LOW


def test_influence_labels_map_from_scores():
    assert influence_label_for_score(0) == LOW
    assert influence_label_for_score(4) == EMERGING
    assert influence_label_for_score(12) == NOTABLE
    assert influence_label_for_score(24) == RESPECTED


def test_peak_influence_updates_and_does_not_decrease():
    world = make_world()
    world.day = 30
    ari = Agent("Ari", 1, 1, agent_id="ari")
    bryn = Agent("Bryn", 2, 1, agent_id="bryn")
    cato = Agent("Cato", 3, 1, agent_id="cato")
    world.agents = [ari, bryn, cato]
    remember(bryn, ari, score=30, day=30)
    remember(cato, ari, score=30, day=30)

    update_agent_peak_influence(ari, world)
    peak = ari.peak_influence_score

    world.day = 100
    update_agent_peak_influence(ari, world)

    assert peak > influence_score(ari, world)
    assert ari.peak_influence_score == peak
    assert peak_influence_label(ari) == influence_label_for_score(peak)


def test_dead_or_missing_villagers_in_social_memory_do_not_crash():
    world = make_world()
    world.day = 5
    ari = Agent("Ari", 1, 1, agent_id="ari")
    bryn = Agent("Bryn", 2, 1, agent_id="bryn", alive=False)
    ari.social_memory["missing"] = SocialMemoryEntry("missing", "Gone", 30, 5)
    bryn.social_memory["ari"] = SocialMemoryEntry("ari", "Ari", 30, 5)
    world.agents = [ari, bryn]

    assert influence_label(ari, world) == LOW


def test_stale_social_memory_does_not_count_toward_current_influence():
    world = make_world()
    world.day = 100
    ari = Agent("Ari", 1, 1, agent_id="ari")
    bryn = Agent("Bryn", 2, 1, agent_id="bryn")
    world.agents = [ari, bryn]
    remember(bryn, ari, score=30, day=10)

    assert influence_score(ari, world) == 0


def test_influence_has_no_gameplay_behavior_effects():
    world = make_world()
    world.tiles[2][2].food = 1
    ari = Agent("Ari", 2, 2, agent_id="ari", hunger=55)
    bryn = Agent("Bryn", 1, 1, agent_id="bryn")
    remember(bryn, ari, score=30, day=1)
    world.agents = [ari, bryn]
    before = (ari.current_goal, ari.current_action, ari.hunger, ari.thirst, ari.fatigue)

    assert influence_label(ari, world) in (EMERGING, NOTABLE, RESPECTED)
    assert (ari.current_goal, ari.current_action, ari.hunger, ari.thirst, ari.fatigue) == before
    assert isinstance(ari.choose_action(world), GatherFoodAction)


def test_no_formal_leader_role_or_selection_exists():
    assert "Leader" not in ROLES
    assert "Leadership" not in ROLES
    assert not hasattr(World, "leader")
