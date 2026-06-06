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

## Current Focus

v0.4 Smarter World

Agents should:
- remember resources
- pathfind
- choose goals
- survive longer

World generation should:
- create deterministic worlds when given a seed
- generate elevation, moisture, and temperature maps
- trace simple downhill rivers from high elevation toward lower elevation
- assign water, mountain, hill, forest, wetland, dry, plain, and grass terrain from simple natural rules
- place food and wood based on terrain conditions
- apply terrain and season based resource growth, caps, and gradual die-off
- create rare visible environmental events such as drought and heavy rain
- cycle simple seasons that influence terrain-based resource regrowth
- tint terrain by season in the renderer, blending during the final day, without changing gameplay tile kinds
- preserve existing simulation systems while preparing for biomes and environmental events

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
