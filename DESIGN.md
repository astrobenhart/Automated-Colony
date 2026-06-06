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
- assign terrain from simple natural rules
- place food and wood based on terrain conditions
- preserve existing simulation systems while preparing for rivers, seasons, biomes, and environmental events

## Design Priorities

1. Emergence over scripting
2. Simulation over graphics
3. Readability over realism
4. Small systems that interact
5. Observable behavior
