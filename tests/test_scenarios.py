from src.scenarios import (
    ANCIENT_HAMLET,
    DEFAULT_SCENARIO_KEY,
    GROWING_VILLAGE,
    MATURE_SETTLEMENT,
    PIONEER_CAMP,
)
from src.world import create_world
from src.world_history import MYSTERY
from src.worldgen_settings import WorldGenSettings, default_worldgen_settings


def world_for_scenario(scenario: str, seed: int = 701):
    settings = default_worldgen_settings().with_overrides(seed=seed, scenario=scenario)
    return create_world(settings=settings)


def average_household_age(world) -> float:
    households = world.settlement.households
    if not households:
        return 0.0
    return sum(household.established_years for household in households) / len(households)


def average_relationship_score(world) -> float:
    scores = [
        entry.familiarity_score
        for agent in world.living_agents()
        for entry in agent.social_memory.values()
    ]
    if not scores:
        return 0.0
    return sum(scores) / len(scores)


def test_default_scenario_preserves_growing_village_start_shape():
    world = create_world(seed=700)

    assert world.settings.scenario == DEFAULT_SCENARIO_KEY == GROWING_VILLAGE
    assert world.settlement.maturity_label == "Growing Village"
    assert 5 <= world.settlement.age_years <= 15
    assert 8 <= len(world.settlement.homes) <= 15
    assert 30 <= len(world.living_agents()) <= 60


def test_invalid_scenario_setting_falls_back_to_default():
    settings = WorldGenSettings(seed=700, scenario="not-a-scenario")

    assert settings.scenario == DEFAULT_SCENARIO_KEY


def test_pioneer_camp_generates_small_young_sparse_start():
    world = world_for_scenario(PIONEER_CAMP, seed=702)

    assert world.settlement.maturity_label == "Pioneer Camp"
    assert 0 <= world.settlement.age_years <= 2
    assert 4 <= len(world.settlement.homes) <= 7
    assert 12 <= len(world.living_agents()) <= 20
    assert max(household.established_years for household in world.settlement.households) <= 2


def test_mature_and_ancient_scenarios_generate_deeper_settlements():
    mature = world_for_scenario(MATURE_SETTLEMENT, seed=703)
    ancient = world_for_scenario(ANCIENT_HAMLET, seed=703)

    assert mature.settlement.maturity_label == "Mature Settlement"
    assert 20 <= mature.settlement.age_years <= 50
    assert 14 <= len(mature.settlement.homes) <= 20
    assert 45 <= len(mature.living_agents()) <= 60

    assert ancient.settlement.maturity_label == "Ancient Hamlet"
    assert 50 <= ancient.settlement.age_years <= 90
    assert 12 <= len(ancient.settlement.homes) <= 18
    assert 35 <= len(ancient.living_agents()) <= 55
    assert average_household_age(ancient) > average_household_age(mature)


def test_scenario_maturity_scales_chronicle_and_social_depth():
    pioneer = world_for_scenario(PIONEER_CAMP, seed=704)
    ancient = world_for_scenario(ANCIENT_HAMLET, seed=704)

    assert ancient.history.count() > pioneer.history.count()
    assert len(pioneer.history.by_category(MYSTERY)) == 0
    assert len(ancient.history.by_category(MYSTERY)) == 3
    assert average_relationship_score(ancient) > average_relationship_score(pioneer)


def test_non_default_scenarios_seed_matching_reserves():
    pioneer = world_for_scenario(PIONEER_CAMP, seed=705)
    mature = world_for_scenario(MATURE_SETTLEMENT, seed=705)

    assert pioneer.colony_storage.seed_reserve == 4
    assert mature.colony_storage.food == 18
    assert mature.colony_storage.water == 15
    assert mature.colony_storage.wood == 14
    assert mature.colony_storage.seed_reserve == 14
