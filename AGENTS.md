# Agent Rules

This is an autonomous colony simulation inspired by Dwarf Fortress, but v0.1 must stay simple.

## Priorities

1. Simulation logic must be understandable.
2. Agents should create emergent behavior through simple rules.
3. Pygame rendering should not control simulation behavior.
4. Every change should be small and testable.
5. Do not rewrite the whole project unless explicitly asked.

## Coding style

- Use plain Python.
- Prefer dataclasses.
- Keep modules small.
- Avoid global mutable state where possible.
- Keep simulation deterministic when a seed is provided.

## Current design direction

Move from reactive actions to goal-based agents:
Need → Goal → Target → Movement → Action → Event.