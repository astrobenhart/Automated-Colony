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
- cycle simple seasons that influence terrain-based resource regrowth
- tint terrain by season in the renderer, blending during the final day, without changing gameplay tile kinds
- preserve existing simulation systems while preparing for biomes and environmental events

## Design Priorities

1. Emergence over scripting
2. Simulation over graphics
3. Readability over realism
4. Small systems that interact
5. Observable behavior
