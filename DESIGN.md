# Automated Colony Simulation

## Core Concept

A world simulation where the player creates a world and watches autonomous agents survive, explore, build, cooperate, compete, and create history.

The player does not directly control units.

The goal is emergent storytelling through simulation.

## Core Loop

Need
→ Goal
→ Target
→ Movement
→ Action
→ World Change
→ Event

## Current Architecture

v0.4 Smarter World is complete.

Agents should:
- remember resources
- pathfind
- choose goals
- survive longer

World generation should:
- use centralized settings for reproducible and tunable worlds
- create deterministic worlds when given a seed
- generate elevation, moisture, and temperature maps
- trace simple downhill rivers from high elevation toward lower elevation
- assign water, mountain, hill, forest, wetland, dry, plain, and grass terrain from simple natural rules
- place food and wood based on terrain conditions
- apply terrain and season based resource growth, caps, and gradual die-off
- create rare visible environmental events such as drought and heavy rain
- record major environmental events in persistent world history
- spawn ambient wildlife from biome suitability without adding hunting or combat
- cycle simple seasons that influence terrain-based resource regrowth
- tint terrain by season in the renderer, blending during the final day, without changing gameplay tile kinds
- preserve existing simulation systems while preparing for biomes and environmental events

World generation settings should:
- keep defaults compatible with normal gameplay
- validate or clamp unsafe values
- expose seed, size, water level, forest density, and climate harshness
- support presets such as normal, wet, dry, forest, and harsh
- remain internal and preset-driven for now, without a player-facing setup screen

World identity should:
- be generated from actual terrain, resource, wildlife, and settings conditions
- give each world an evocative title, compact subtitle, and estimated survival outlook
- keep hidden tags for future history, settlement, and storytelling systems
- make the player feel they are discovering a world rather than configuring one

World history should:
- remain separate from the short-term event log
- store structured permanent entries for major events
- start with environmental history
- leave wildlife, settlement, migration, lineage, ruins, and myth history for later milestones

UI should:
- keep current simulation and colony status visible at a glance
- prefer compact grouped sections as more systems are added
- preserve selection, active events, history, legend, controls, and recent event visibility without changing simulation behavior

## Next Focus

v0.5 Settlement Simulation should focus on:
- roles as soft villager preferences
- settlement centers
- physical stockpiles
- clustered building placement
- local resource use around village hubs
- stronger long-term settlement behavior

Do not begin v0.5 by adding reproduction, migration, politics, warfare, or large-scale economy. The next step is making stable shelter clusters become recognizable early villages.

## Roles

Villagers are survivors with preferences, not workers with fixed assignments.

Implemented roles:
- Generalist: no specialty modifier
- Forager: modest preference for food gathering and food storage
- Builder: modest preference for wood gathering and shelter building
- Scout: modest preference for exploration

Role rules:
- roles modify goal utility only when immediate needs are reasonably satisfied
- thirst, hunger, and fatigue remain dominant
- no role is mandatory for colony function
- there is no player role assignment, job board, task claiming, or micromanagement

## Settlement Center v1

The settlement center is a conceptual village anchor, not a full building system.

Implemented behavior:
- each world has one settlement
- the settlement is automatically placed near the initial villager spawn centroid
- the center is placed on walkable terrain
- the settlement has a deterministic short name connected to the generated world identity
- it tracks founding day, founding season, living population, and radius
- the right panel and map marker make the settlement visible

Non-goals for v1:
- no player placement
- no physical stockpile tile
- no hauling jobs
- no task claiming
- no migration or multiple settlements
- no forced villager destination behavior

Future systems can use the center as the origin for local work radius, clustered building placement, physical storage, village identity, expansion, and settlement history.

## Settlement Arc

The long-term simulation arc is:

Survivors -> Colonists -> Villagers -> Settlements -> Historical Societies

Current behavior:
- Villagers naturally cluster near shelters.
- Exploration is mostly local.
- Colonies often suffer early population loss before stabilizing.
- Stable colonies tend to remain in a small area.

Desired future behavior:
- Shelter clusters become recognizable villages.
- Villages form around settlement centers.
- Storage, shelters, and production buildings cluster near local hubs.
- Villagers prefer nearby resources before ranging farther out.

Long-term behavior:
- Resource scarcity, population pressure, and social conditions can drive expansion.
- Some groups may migrate or form splinter settlements.
- Settlements can gain names, identities, founding dates, notable events, lineages, and ruins.
- Multiple settlements should emerge from simulation pressure rather than scripted history.

Non-goals for the current roadmap:
- Warfare
- Diplomacy
- Economy
- Politics
- Kingdoms

These may become future possibilities, but the next design step is village formation, not large-scale states.

## Design Priorities

1. Emergence over scripting
2. Simulation over graphics
3. Readability over realism
4. Small systems that interact
5. Observable behavior
