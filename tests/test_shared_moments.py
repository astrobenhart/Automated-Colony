from src.agent import Agent
from src.diagnostics import diagnostics_sections, derived_mood_score, mood_modifiers
from src.gatherings import active_gatherings
from src.settlement import Settlement
from src.shared_moments import current_shared_moment, shared_moment_diagnostics, update_shared_moments
from src.tile import Tile
from src.villager_inspection import villager_detail_sections
from src.world import World


def make_world(width: int = 12, height: int = 12) -> World:
    world = World(width, height)
    world.tiles = [[Tile("grass") for _ in range(width)] for _ in range(height)]
    world.settlement = Settlement("Oakvale", 6, 6, 1, "Spring", settlement_id="oakvale")
    return world


def test_shared_moments_only_occur_during_gatherings():
    world = make_world()
    ari = Agent("Ari", 6, 6, agent_id="ari", current_action="Idle")
    bryn = Agent("Bryn", 7, 6, agent_id="bryn", current_action="Idle")
    loner = Agent("Cato", 1, 1, agent_id="cato", current_action="Idle")
    world.agents = [ari, bryn, loner]

    update_shared_moments(world)

    assert active_gatherings(world)
    assert current_shared_moment(ari, world) is not None
    assert current_shared_moment(bryn, world) is not None
    assert current_shared_moment(loner, world) is None


def test_survival_needs_override_shared_moments():
    world = make_world()
    ari = Agent("Ari", 6, 6, agent_id="ari", current_action="Idle", hunger=90)
    bryn = Agent("Bryn", 7, 6, agent_id="bryn", current_action="Idle")
    world.agents = [ari, bryn]

    update_shared_moments(world)

    assert current_shared_moment(ari, world) is None
    assert current_shared_moment(bryn, world) is None


def test_shared_moments_strengthen_friendships_without_chronicle_entries():
    world = make_world()
    ari = Agent("Ari", 6, 6, agent_id="ari", current_action="Idle")
    bryn = Agent("Bryn", 7, 6, agent_id="bryn", current_action="Idle")
    world.agents = [ari, bryn]

    update_shared_moments(world)

    assert ari.friendships["bryn"].score == 1
    assert bryn.friendships["ari"].score == 1
    assert world.history.entries == []


def test_shared_moment_mood_bonus_applies_lightly():
    world = make_world()
    ari = Agent("Ari", 6, 6, agent_id="ari", current_action="Idle")
    bryn = Agent("Bryn", 7, 6, agent_id="bryn", current_action="Idle")
    world.agents = [ari, bryn]

    baseline = derived_mood_score(ari, world)
    update_shared_moments(world)
    score = derived_mood_score(ari, world)
    positive, negative = mood_modifiers(ari, world)

    assert score == baseline + 2
    assert positive == "Shared moment"
    assert negative == "None"


def test_shared_moments_end_naturally_when_gathering_breaks():
    world = make_world()
    ari = Agent("Ari", 6, 6, agent_id="ari", current_action="Idle")
    bryn = Agent("Bryn", 7, 6, agent_id="bryn", current_action="Idle")
    world.agents = [ari, bryn]
    update_shared_moments(world)
    assert current_shared_moment(ari, world) is not None

    bryn.x = 1
    bryn.y = 1
    update_shared_moments(world)

    assert current_shared_moment(ari, world) is None
    assert current_shared_moment(bryn, world) is None


def test_villager_inspection_displays_current_shared_moment():
    world = make_world()
    ari = Agent("Ari", 6, 6, agent_id="ari", current_action="Idle")
    bryn = Agent("Bryn", 7, 6, agent_id="bryn", current_action="Idle")
    world.agents = [ari, bryn]
    update_shared_moments(world)

    sections = dict(villager_detail_sections(ari, world))

    assert ("Shared Moment", current_shared_moment(ari, world)) in sections["Status"]


def test_shared_moment_diagnostics_report_activity_duration_and_common_type():
    world = make_world()
    world.day = 5
    ari = Agent("Ari", 6, 6, agent_id="ari", current_action="Idle")
    bryn = Agent("Bryn", 7, 6, agent_id="bryn", current_action="Idle")
    world.agents = [ari, bryn]
    update_shared_moments(world)

    rows = dict(shared_moment_diagnostics(world))

    assert rows["Active Shared Moments"] == 2
    assert rows["Average Duration"] == "1.0 days"
    assert rows["Most Common Shared Moment"] == current_shared_moment(ari, world)


def test_diagnostics_include_shared_moments_section():
    world = make_world()
    world.agents = [
        Agent("Ari", 6, 6, agent_id="ari", current_action="Idle"),
        Agent("Bryn", 7, 6, agent_id="bryn", current_action="Idle"),
    ]
    update_shared_moments(world)

    sections = {section.title: dict(section.rows) for section in diagnostics_sections(world)}

    assert sections["Shared Moments"]["Active Shared Moments"] == 2
