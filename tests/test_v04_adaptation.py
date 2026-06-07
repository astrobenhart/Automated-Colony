from src.agent import Agent
from src.actions import SeekFoodAction, SeekWaterAction, SeekWoodAction
from src.resource_ecology import apply_resource_ecology
from src.tile import Tile
from src.world import create_world
from src.worldgen_settings import WORLD_PRESETS
from src.world_identity import SURVIVAL_OUTLOOKS


class SequenceRandom:
    def __init__(self, values):
        self.values = list(values)

    def random(self):
        return self.values.pop(0)


def count_tiles(world, kind: str) -> int:
    return sum(1 for row in world.tiles for tile in row if tile.kind == kind)


def total_food(world) -> int:
    return sum(tile.food for row in world.tiles for tile in row)


def total_wood(world) -> int:
    return sum(tile.wood for row in world.tiles for tile in row)


def far_walkable_tile(world, target: tuple[int, int]) -> tuple[int, int]:
    tx, ty = target
    candidates = [
        (x, y)
        for y, row in enumerate(world.tiles)
        for x, tile in enumerate(row)
        if tile.walkable and abs(x - tx) + abs(y - ty) > 8
    ]
    assert candidates
    return candidates[0]


def first_tile_with(world, predicate) -> tuple[int, int]:
    for y, row in enumerate(world.tiles):
        for x, tile in enumerate(row):
            if predicate(tile):
                return (x, y)
    raise AssertionError("No matching tile found")


def test_dry_world_has_less_water_and_food_than_wet_world():
    wet = create_world(settings=WORLD_PRESETS["wet"].with_overrides(seed=77), agent_count=0)
    dry = create_world(settings=WORLD_PRESETS["dry"].with_overrides(seed=77), agent_count=0)

    assert count_tiles(dry, "water") < count_tiles(wet, "water")
    assert total_food(dry) < total_food(wet)


def test_agent_in_dry_world_seeks_known_water():
    world = create_world(settings=WORLD_PRESETS["dry"].with_overrides(seed=77), agent_count=0)
    water = first_tile_with(world, lambda tile: tile.kind == "water")
    start = far_walkable_tile(world, water)
    agent = Agent("Ari", start[0], start[1], thirst=80)
    agent.remembered_water.add(water)
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Drink"
    assert isinstance(action, SeekWaterAction)


def test_hungry_agent_uses_remembered_food_in_resource_landscape():
    world = create_world(settings=WORLD_PRESETS["wet"].with_overrides(seed=77), agent_count=0)
    food = first_tile_with(world, lambda tile: tile.food > 0)
    start = far_walkable_tile(world, food)
    agent = Agent("Bryn", start[0], start[1], hunger=80)
    agent.remembered_food.add(food)
    world.agents.append(agent)

    action = agent.choose_action(world)

    assert agent.current_goal == "Gather food"
    assert isinstance(action, SeekFoodAction)


def test_forest_world_has_more_wood_and_supports_wood_seeking():
    normal = create_world(settings=WORLD_PRESETS["normal"].with_overrides(seed=77), agent_count=0)
    forest = create_world(settings=WORLD_PRESETS["forest"].with_overrides(seed=77), agent_count=0)

    assert total_wood(forest) > total_wood(normal)

    wood = first_tile_with(forest, lambda tile: tile.wood > 0)
    start = far_walkable_tile(forest, wood)
    agent = Agent("Cato", start[0], start[1])
    agent.remembered_wood.add(wood)
    forest.agents.append(agent)

    action = agent.choose_action(forest)

    assert agent.current_goal == "Gather wood"
    assert isinstance(action, SeekWoodAction)


def test_harsh_world_has_lower_resources_and_harsher_outlook_than_wet_world():
    wet = create_world(settings=WORLD_PRESETS["wet"].with_overrides(seed=77), agent_count=0)
    harsh = create_world(settings=WORLD_PRESETS["harsh"].with_overrides(seed=77), agent_count=0)

    assert total_food(harsh) < total_food(wet)
    assert total_wood(harsh) < total_wood(wet)
    assert SURVIVAL_OUTLOOKS.index(harsh.identity.survival_outlook) > SURVIVAL_OUTLOOKS.index(wet.identity.survival_outlook)


def test_winter_ecology_reduces_food_where_spring_can_restore_growth():
    winter_tile = Tile("plain", food=2)
    spring_tile = Tile("plain", food=0)

    apply_resource_ecology(winter_tile, "Winter", SequenceRandom([0.0, 1.0]))
    apply_resource_ecology(spring_tile, "Spring", SequenceRandom([0.0]))

    assert winter_tile.food == 1
    assert spring_tile.food == 1
