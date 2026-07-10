# Presentation State Ownership Audit

## Executive Summary

The Presentation architecture is directionally correct:

```text
Simulation
  -> Intent Layer
  -> Presentation Scene
  -> Observer Camera
  -> Renderer
```

However, state ownership is still mixed at the Simulation -> Intent -> Presentation boundary and again at the Presentation -> Renderer boundary.

The most important finding is that Presentation is not yet the only writer of Presentation state. `PresentationScene.update(...)` advances presentation state, but `PygameRenderer.draw_agents(...)` later calls `PresentationScene.snapshot_world(...)`, which calls `sync_world(...)` again during rendering. This means rendering can still mutate Presentation state.

The second important finding is that `PresentationAgent` stores some fields with ambiguous meaning. `tile_x` and `tile_y` are updated from the simulation during `observe_movement_intent(...)`, even while `render_x` and `render_y` may still be far behind. Later fallback movement compares the simulation position against those already-updated presentation fields and may decide there is nothing to do. This can explain agents visually failing to leave even though simulation continues.

The third important finding is that Intent still acts partly like a synchronization stream rather than only a behavioural contract. `IntentQueue.replace(...)` is called every sync, movement intent ids include the current simulation position and remaining path, and Presentation can reinitialize an empty route from still-active simulation intent. If Presentation finishes a visual route before simulation has consumed the same path, the next sync can cause the route to replay.

The reported symptoms likely share one root family:

- repeated paths: Presentation can finish a route, then rebuild it from still-active movement intent because there is no explicit intent execution ownership or completion contract
- popping: PresentationAgents are destroyed immediately when simulation membership changes and can be recreated at the current simulation tile with no presentation lifetime handoff
- failure to leave: simulation-position fields inside `PresentationAgent` can be updated ahead of rendered position, then later suppress fallback visual movement

The recommended architectural correction is not a small bug fix. Presentation needs a strict ownership boundary:

```text
Simulation owns facts.
Intent owns change descriptions.
Presentation owns execution state.
Renderer owns no world state mutation.
```

The single highest-priority change is to make Presentation update a one-way phase and make snapshots read-only. Rendering must never call `sync_world(...)`.

## Audit Basis

This audit reviewed the current working tree after the Persistent Presentation Routes work. The repo was already on `v0.9-development` and `git pull` reported up to date.

Files reviewed:

- `DESIGN.md`
- `ROADMAP.md`
- `TASKS.md`
- `PRESENTATION_AUDIT.md`
- `INTENT_PATH_FIDELITY_INVESTIGATION.md`
- `src/presentation.py`
- `src/intents.py`
- `src/renderer.py`
- `src/main.py`
- relevant presentation, intent, pathfinding and renderer tests

No implementation changes were made for this audit.

## Architecture Diagram

Intended long-term ownership:

```text
Simulation
  owns: world facts, tile positions, pathfinding, jobs, needs, relationships
  writes: Agent.x/y, Agent.current_target, Agent.current_path, Agent.current_action
  reads: nothing from Presentation

Intent Layer
  owns: derived behavioural contracts
  writes: immutable AgentIntent values
  reads: Simulation facts

Presentation Scene
  owns: visual object lifetime and execution state
  writes: PresentationAgent, PresentationRoute, PresentationAction, PresentationTime, ObserverCamera
  reads: Intent and selected simulation facts

Renderer
  owns: draw surfaces, caches, UI widgets, transient render metrics
  writes: pixels and renderer-local caches
  reads: PresentationSnapshot and remaining legacy World data
```

Current update flow:

```text
main loop
  -> World.update() zero or more times
  -> renderer.update_ui(dt)
       -> PresentationScene.update(world, dt)
            -> PresentationTime.advance(...)
            -> PresentationScene.sync_world(world)
            -> PresentationAgent.observe(...)
            -> ObserverCamera.advance(...)
            -> PresentationAgent.advance(...)
  -> renderer.draw(...)
       -> draw_agents(...)
            -> PresentationScene.snapshot_world(world)
                 -> PresentationScene.sync_world(world)   <-- mutation during draw
```

The last step is the primary architectural violation.

## Ownership Matrix

| State | Owner | Readers | Writers | Lifetime | Update Frequency | Expected Synchronisation Behaviour |
|---|---|---|---|---|---|---|
| Simulation Position (`Agent.x/y`) | Simulation | Intent, renderer legacy selection/UI, Presentation sync | Simulation actions/path stepping | Agent lifetime | Simulation tick | Presentation observes; never writes |
| Simulation Path (`Agent.current_path`) | Simulation | Intent | Pathfinding and movement actions | Current gameplay target | Simulation tick/action execution | Intent may derive a route update; Presentation must not mutate it |
| Simulation Destination (`Agent.current_target`) | Simulation | Intent, diagnostics/tests | Simulation actions/task logic | Current task | Simulation tick/action execution | Intent observes target changes |
| Intent Queue | Presentation Scene currently; conceptually Intent Layer output | PresentationAgent | `PresentationScene.sync_world(...)` via `IntentQueue.replace(...)` | Presentation agent lifetime | Every sync, including draw-time sync | Should be updated once during presentation update, not during rendering |
| Intent Progress | Ambiguous / not represented | N/A | N/A | Missing state | N/A | Needs an explicit owner or deliberate absence; current absence allows route replay |
| Presentation Route | PresentationAgent | PresentationAgent, snapshots/tests | `observe_movement_intent`, reconciliation, recovery, `advance` | PresentationAgent lifetime | Presentation update and draw-time sync today | Should only change during Presentation update, never during rendering |
| Presentation Waypoints | PresentationAgent | PresentationAgent | Route reconciliation and `advance` | Current visual route | Presentation frame | Waypoints should be removed only when rendered position reaches them |
| Presentation Position (`render_x/y`) | PresentationAgent | Renderer agent layer, snapshots/tests | `PresentationAgent.advance`, recovery, initial creation | PresentationAgent lifetime | Presentation frame | Renderer reads immutable snapshot only |
| Presentation Segment (`from_x/y`, `target_x/y`, `progress`) | PresentationAgent | PresentationAgent, future animation | `start_motion_to`, `advance`, recovery | Current motion segment | Presentation frame | Must not be reset by draw-time sync |
| Presentation Action | PresentationAgent | Renderer snapshots, future animation | `observe_presentation_action` | Current intent/action | Presentation sync | Should be created from Intent, then advanced by Presentation |
| Presentation Action Progress | PresentationAction | Renderer snapshots, future animation | `PresentationAction.advance`, `complete` | Current action | Presentation frame | Should never be derived from simulation tick |
| Presentation Animation State | Not yet implemented | Future renderer | N/A | Missing state | N/A | Should be owned by PresentationAgent or animation object |
| Presentation Facing | PresentationAgent | Renderer snapshots/future animation | `start_motion_to` | PresentationAgent lifetime | Motion segment changes | Should become presentation-time interpolated; current value snaps |
| Presentation Timing | PresentationScene / PresentationTime | Presentation systems, snapshots | `PresentationTime.advance` | PresentationScene lifetime | Presentation frame | Simulation and renderer should not replace it |
| Presentation Camera / Observer Camera | PresentationScene owns; renderer commands it | Renderer transforms, picking | Renderer input methods call camera setters; camera advances itself | Renderer/session lifetime | Input events and presentation frame | Camera is presentation-owned but still controlled through renderer API |
| Presentation Snapshots | PresentationScene | Renderer | `snapshot()` and `snapshot_world()` | One frame / cached last snapshot | Presentation update and draw-time snapshot | Snapshot creation should be read-only; currently `snapshot_world` mutates via sync |
| Renderer State | PygameRenderer | Renderer | PygameRenderer | Renderer lifetime | Frame/input/cache invalidation | Should not modify Presentation except through update/input commands |
| Selection State | PygameRenderer / gameplay object references | Renderer UI, overlays | Renderer input, validation, overlay callbacks | Renderer/session lifetime | Input events and draw validation | Still references simulation agents directly; visual highlight uses simulation position |
| World Position | Ambiguous term | Simulation, Presentation, Renderer | Multiple depending on context | Varies | Varies | Should be split into simulation tile position and presentation world position |
| Render Position | PresentationAgent snapshot | Renderer | PresentationAgent only | PresentationAgent lifetime / snapshot frame | Presentation frame | Renderer should only read |

## Lifecycle Diagrams

### PresentationAgent Lifecycle

Current implementation:

```text
PresentationScene.sync_world(world)
  -> living_agents = alive agents from world.agents
  -> live_ids = presentation_key_for(agent)
  -> delete PresentationAgents whose ids are absent
  -> create PresentationAgent.from_agent(agent) for new ids
  -> observe agent and current intent
```

Creation:

- Created in `PresentationScene.sync_world(...)` when a living simulation agent has no matching presentation key.
- Initial render position is copied directly from the simulation tile.
- If an agent appears after being absent, it pops in at the current simulation tile.

Lifetime:

- Intended to persist for the simulation agent lifetime.
- Actually persists only while `presentation_key_for(agent)` remains stable and the simulation agent remains in `world.agents` with `alive=True`.

Destruction:

- Destroyed immediately when the agent is missing from `living_agents`.
- There is no Presentation exit state, departure action, fade, offscreen grace period or dead/departing visual lifecycle.

Recreation risk:

- Stable `agent_id` protects most villagers.
- Agents without stable `agent_id` fall back to `object:{id(agent)}` and can be recreated if simulation object identity changes.
- `PygameRenderer.set_world(...)` recreates the whole Presentation Scene.
- Any simulation removal/re-addition recreates the PresentationAgent at the current simulation tile.

### Movement Ownership Lifecycle

Current movement path:

```text
Simulation pathfinding
  -> Agent.current_path
  -> movement_intent_for(agent)
  -> IntentQueue.replace(...)
  -> PresentationAgent.observe_movement_intent(...)
  -> PresentationAgent.presentation_route
  -> PresentationAgent.advance(...)
  -> PresentationAgentSnapshot.render_x/y
  -> Renderer.draw_agents(...)
```

Where ownership is clean:

- Simulation owns pathfinding and tile movement.
- Presentation owns `presentation_route`, `render_x/y`, segment progress and easing.
- Renderer draws `render_x/y`.

Where ownership is ambiguous:

- `sync_world(...)` can run during rendering.
- `PresentationAgent.observe(...)` updates `tile_x/tile_y` from simulation while Presentation may not have visually reached that tile.
- `IntentQueue.replace(...)` refreshes intent every sync rather than representing a stable set of changes handed to Presentation.
- There is no explicit "Presentation accepted this intent update" or "Presentation completed this visual execution" state.

### Snapshot Lifecycle

Expected:

```text
PresentationScene.update(...)
  -> mutate Presentation
  -> produce last_snapshot

Renderer.draw(...)
  -> read last_snapshot
  -> draw pixels
```

Current:

```text
PresentationScene.update(...)
  -> sync and advance
  -> produce last_snapshot

Renderer.draw_agents(...)
  -> snapshot_world(world)
       -> sync again
       -> produce another snapshot
```

This means snapshot generation is not purely read-only.

## Answers to Specific Questions

### 1. Who owns the villager's current visual position?

Intended owner: `PresentationAgent`.

Current writers:

- `PresentationAgent.from_agent(...)` initializes `render_x/y` from simulation.
- `PresentationAgent.advance(...)` updates `render_x/y` during normal motion.
- `PresentationAgent.recover_presentation_route(...)` snaps `render_x/y` during explicit recovery.

Renderer reads `PresentationAgentSnapshot.render_x/y`.

Assessment: mostly clean, except recovery and creation can snap. The bigger issue is that render-time sync can trigger recovery or route changes during draw.

### 2. Who owns the current route?

Intended owner: `PresentationAgent.presentation_route`.

Current writers:

- `movement_queue` compatibility setter
- `observe(...)` clears the route when no walking intent exists
- `reconcile_presentation_route(...)`
- `initialize_presentation_route(...)`
- `recover_presentation_route(...)`
- `advance_to_next_waypoint(...)`
- `advance(...)`

Assessment: ownership is inside PresentationAgent, but too many methods can change it from both update-time and draw-time sync. The owner is right; the mutation phase is wrong.

### 3. Who removes completed waypoints?

Current owner: `PresentationAgent.advance(...)` and `advance_to_next_waypoint(...)`.

Assessment: this is conceptually correct. Waypoints are removed when the rendered agent reaches them. However, `observe(...)` can clear the entire route when walking intent disappears, which bypasses per-waypoint completion.

### 4. Who decides when an Intent completes?

Current answer: ambiguous.

- Simulation completes gameplay actions by changing action/path/target state.
- Presentation completes `PresentationAction` when its visual progress reaches 1.0.
- IntentQueue itself has no progress or completion state.
- For walking, Presentation can finish a route while simulation still reports the same path intent, causing possible replay.

Assessment: Intent should not own execution, but the boundary needs an acknowledgement/version model so the same simulation intent does not repeatedly re-seed a completed presentation route.

### 5. Who creates PresentationAgents?

`PresentationScene.sync_world(...)`.

### 6. Who destroys PresentationAgents?

`PresentationScene.sync_world(...)` deletes agents whose presentation key is no longer in the current `living_agents` set.

### 7. Can PresentationAgents be recreated unnecessarily?

Yes.

Potential recreation paths:

- simulation object identity changes for agents without stable `agent_id`
- simulation temporarily removes and later re-adds an agent
- `alive` flips false before presentation has an exit lifecycle
- renderer `set_world(...)` replaces the whole PresentationScene

For normal villagers with stable `agent_id`, recreation should be uncommon. For wanderers, visitors, departures or any agent lifecycle that removes objects from `world.agents`, immediate presentation destruction is likely to look like popping.

### 8. Can Intent updates replace state that Presentation still owns?

Partially.

Persistent routes now reconcile instead of direct replacement, but:

- `IntentQueue.replace(...)` still replaces the queue every sync.
- `observe_presentation_action(...)` replaces the current PresentationAction whenever the intent id changes.
- `observe(...)` clears `presentation_route` when walking intent disappears.

Intent no longer fully replaces the movement route, but it still drives action replacement and route cancellation directly.

### 9. Can Simulation overwrite Presentation state before Presentation finishes executing it?

Simulation does not directly write Presentation fields. However, `sync_world(...)` copies simulation state into Presentation fields repeatedly:

- `name`
- `role`
- `current_action`
- `current_goal`
- `tile_x`
- `tile_y`
- current intent queue

Because this happens before Presentation finishes motion, simulation can indirectly overwrite presentation context. The most dangerous example is `tile_x/tile_y`, which are updated to the simulation position before `render_x/y` arrives.

### 10. Are there any remaining legacy synchronisation paths bypassing the Intent Layer?

Yes.

- Non-walking fallback in `PresentationAgent.observe(...)` starts motion directly from changed simulation tile coordinates.
- Renderer selection uses `world.agent_at(tile_x, tile_y)`.
- Selection highlight draws selected agents at `selected_agent.x/y`, not presentation render position.
- Terrain, vegetation, environment, structures, UI and overlays still query world state directly.
- `snapshot_world(world)` lets renderer ask Presentation to resync from simulation during draw.

## Synchronisation Paths

### Path A: Main Presentation Update

```text
renderer.update_ui(dt)
  -> update_presentation(dt)
  -> PresentationScene.update(world, dt)
  -> sync_world(world)
  -> PresentationAgent.observe(...)
  -> ObserverCamera.advance(...)
  -> PresentationAgent.advance(...)
```

This is the correct phase for Presentation mutation.

### Path B: Draw-Time Presentation Sync

```text
renderer.draw(...)
  -> compose_scene()
  -> draw_agent_layer()
  -> draw_agents(...)
  -> PresentationScene.snapshot_world(world)
  -> sync_world(world)
```

This is the critical ownership violation. Drawing should consume snapshots, not mutate Presentation objects.

### Path C: Renderer Selection Legacy Path

```text
mouse click
  -> screen_to_world_tile(...)
  -> world.agent_at(tile_x, tile_y)
  -> selected_agent = simulation Agent

draw_selection_highlight()
  -> selected_agent.x/y
  -> observer_camera.world_to_screen(...)
```

Selection truth may remain gameplay-owned for now, but visual selection should eventually consume a PresentationSelection snapshot so highlights track rendered position.

### Path D: Non-Intent Movement Fallback

```text
PresentationAgent.observe(agent, intent=None)
  -> compare agent.x/y with PresentationAgent.tile_x/y
  -> start_motion_to(...) if different
```

This bypasses Intent. It is useful compatibility scaffolding, but it becomes unsafe when `tile_x/y` were already updated by previous movement intent observation.

## Legacy Paths

Legacy renderer paths still querying simulation directly:

- Terrain layer reads `world` and `tile` state.
- Vegetation overlay reads `world.tile_at(...)` and `world.tick`.
- Environmental overlay uses `world.tick` for weather, cloud shadows and mysteries.
- Structure and workplace rendering read settlement/building data directly.
- UI panels and overlays read `world`, selected simulation agents and selected tiles.
- Selection highlight uses simulation position for agents.
- Mouse picking uses tile-space simulation lookup.

These are not all urgent ownership bugs. Many are expected during gradual renderer migration. The urgent issue is not that legacy paths exist; it is that the agent renderer path, which is supposed to be Presentation-owned, still mutates Presentation during draw.

## Conflicting Ownership

### Critical: Snapshot Generation Mutates Presentation

Owner conflict:

- PresentationScene owns Presentation state.
- Renderer should read snapshots.
- Renderer currently calls `snapshot_world(world)`, which calls `sync_world(world)` and mutates Presentation state.

Why it matters:

- route reconciliation can occur during draw
- action replacement can occur during draw
- agent creation/destruction can occur during draw
- a read operation is no longer safe or deterministic

Recommended ownership correction:

- `PresentationScene.update(...)` should be the only routine that calls `sync_world(...)`.
- `PresentationScene.snapshot_world(...)` should either be removed or made read-only.
- Renderer should draw `presentation_scene.last_snapshot` or `presentation_scene.snapshot()` without passing `world`.

### Critical: `PresentationAgent.tile_x/y` Has Two Meanings

Owner conflict:

- As snapshot data, `tile_x/y` means authoritative simulation tile.
- As fallback movement state, it is used to decide whether Presentation needs to move.

Why it matters:

- `observe_movement_intent(...)` sets `tile_x/y` to the simulation position before visual motion catches up.
- Later, if walking intent disappears, `observe(...)` compares the simulation position with already-updated `tile_x/y` and may return without moving `render_x/y`.

Recommended ownership correction:

- Split the fields:
  - `simulation_tile_x/y`: latest observed simulation tile
  - `visual_tile_x/y` or route/segment-derived visual tile: presentation execution state
- Fallback sync should compare simulation position against render/target state, not an already-synchronized simulation mirror.

### High: Intent Queue Replacement Still Looks Like State Sync

Owner conflict:

- Intent is intended to communicate behaviour changes.
- `IntentQueue.replace(...)` replaces the queue every sync from current simulation state.

Why it matters:

- Intent does not carry update semantics such as append, continue, replace, cancel or invalidate.
- Presentation must infer whether a movement intent is new, ongoing, stale, replayed or a correction.
- Presentation can finish a route faster than simulation consumes it, then accept the same simulation path again as new visual work.

Recommended ownership correction:

- Introduce explicit Intent Update records with stable sequence/version fields.
- Make movement intent represent a route update event, not a continuously replaced current-state mirror.
- Track which intent update has been accepted by Presentation.

### High: Presentation Route Cancellation Is Too Broad

Owner conflict:

- Presentation owns route execution.
- `observe(...)` clears `presentation_route` whenever no walking intent exists.

Why it matters:

- A temporary absence of walking intent can destroy visual work that Presentation has not completed.
- It turns absence of intent into an implicit route cancel.

Recommended ownership correction:

- Route cancellation should be an explicit Intent Update or recovery state.
- Absence of new movement intent should mean "no new route update", not "clear the visual route", unless simulation explicitly invalidates movement.

### High: PresentationAction Replacement Is Intent-Id Driven

Owner conflict:

- Presentation owns action lifecycle and progress.
- Intent id changes replace the whole PresentationAction immediately.

Why it matters:

- Action progress can reset due to simulation label/position changes even when the visible action should continue or transition.
- This can make action state stutter or replay.

Recommended ownership correction:

- Presentation Actions need transition rules, not direct replacement on any intent id change.
- Intent should specify action kind and continuity identity separately from incidental state like current position.

### Medium: Selection Visuals Bypass Presentation

Owner conflict:

- Gameplay selection truth lives in renderer as selected simulation object/tile.
- Visual selection highlight draws from simulation tile position.
- Agent sprites draw from Presentation render position.

Why it matters:

- Selection highlight can lag/snap separately from the rendered villager.
- It reinforces the tick-based feel.

Recommended ownership correction:

- Keep selection truth gameplay/read-only if desired.
- Add PresentationSelection that resolves selected agent id to current presentation render position.

### Medium: PresentationAgent Lifetime Has No Exit State

Owner conflict:

- Simulation owns agent existence.
- Presentation owns visual object lifetime.
- Current sync deletes PresentationAgents immediately when simulation no longer reports them alive/present.

Why it matters:

- Death, departure, settlement change or world removal can cause popping.
- Wanderers may appear not to leave if their visual lifecycle is destroyed before completing an exit route, or may vanish before the player sees departure.

Recommended ownership correction:

- Add lifecycle phases:
  - Active
  - Departing
  - Dead/Exit Presentation
  - Retired
- Simulation removal should produce a presentation lifecycle update, not immediate deletion where visual continuity matters.

## Root Cause Analysis

The three symptoms are probably not three independent renderer bugs.

### Repeated Movement

Likely cause:

```text
Presentation finishes route
  -> simulation still exposes current path/target intent
  -> draw-time or next update sync sees empty presentation route
  -> route initializes again from simulation intent
  -> villager visually repeats path
```

Architectural source:

- no explicit owner for intent progress/completion
- IntentQueue replacement every sync
- Presentation route accepts current simulation state as new work after it finishes
- draw-time sync gives this more opportunities to happen

### Popping In And Out

Likely cause:

```text
sync_world sees agent absent/not alive
  -> deletes PresentationAgent immediately
later agent appears / object changes / scene resets
  -> creates PresentationAgent.from_agent(...)
  -> render position starts at current simulation tile
```

Architectural source:

- Presentation object lifetime is tied directly to simulation membership
- no visual lifecycle for exits
- no stable presentation identity contract for every visible actor type

### Failing To Visually Leave

Likely cause:

```text
movement intent sync updates PresentationAgent.tile_x/y to simulation position
render_x/y remains behind
walking intent disappears
fallback observe compares next simulation x/y to tile_x/y
values already match
fallback returns without starting motion
rendered villager remains behind
```

Architectural source:

- `tile_x/y` is both a simulation mirror and fallback presentation sync marker
- absence of intent is interpreted as route clearing rather than "no update"
- Presentation does not own a complete execution contract for leaving/departure

## Recommended Architectural Changes

These are ownership corrections, not small bug fixes.

### 1. Make Presentation Updates Single-Phase

Rule:

```text
Only PresentationScene.update(...) may mutate Presentation state.
Renderer draw calls must never call sync_world(...).
```

Expected changes in a future implementation task:

- remove or redefine `snapshot_world(world)` so it is read-only
- renderer agent layer reads `presentation_scene.last_snapshot`
- test that drawing does not mutate `PresentationScene.presentation_time`, routes, actions or agent dictionaries

Expected impact:

- eliminates draw-time route/action/agent mutation
- makes snapshots reliable
- makes ownership easier to reason about

Priority: Critical.

### 2. Split Simulation Mirror State From Presentation Execution State

Rule:

```text
Simulation position mirrors are not presentation progress markers.
```

Expected changes:

- replace ambiguous `tile_x/y` use inside `PresentationAgent`
- preserve simulation tile in snapshots for diagnostics/readability
- base visual movement completion on route/segment/render state
- never decide "no visual movement needed" from a field already synchronized from simulation

Expected impact:

- reduces stuck visuals
- clarifies world position vs render position
- prepares future animation and selection systems

Priority: Critical.

### 3. Convert Intent Queue Replacement Into Intent Updates

Rule:

```text
Intent communicates changes; it does not synchronize Presentation state.
```

Expected changes:

- introduce movement update types such as Continue, Append, Replace, Cancel and Invalidate
- give updates stable sequence/version identity
- keep accepted update state in Presentation
- absence of a new movement update does not clear current Presentation execution

Expected impact:

- prevents repeated routes
- makes cancellation explicit
- makes route recovery auditable

Priority: High.

### 4. Add PresentationAgent Lifecycle Phases

Rule:

```text
Simulation existence and visual existence are related, but not identical.
```

Expected changes:

- keep PresentationAgent alive long enough to complete departure/death/exit presentation when appropriate
- remove immediately only for hard world reset or explicit nonvisual cleanup
- create a stable identity requirement for wanderers and future visible entities

Expected impact:

- reduces popping
- supports departures, funerals, wanderers and mysteries

Priority: High.

### 5. Move Selection Visuals Into Presentation

Rule:

```text
Selection truth may be gameplay-owned; selection presentation should be presentation-owned.
```

Expected changes:

- keep selected agent id or selected tile as UI state
- derive selection highlight position from PresentationSnapshot when selecting an agent
- keep tile selection as tile-based until tile presentation exists

Expected impact:

- highlight follows visible villager instead of simulation tile
- reduces tick-based perception

Priority: Medium.

## Recommended DESIGN.md Additions

Recommended permanent rules:

```text
Every state has exactly one authoritative owner.
Readers may observe state, but only the owner may modify it.
Presentation objects are persistent visual entities.
Intent communicates behaviour changes; it does not synchronize Presentation state.
Simulation never directly modifies Presentation state after creation.
Presentation never modifies Simulation state.
Renderer draw calls are read-only with respect to Presentation.
Snapshots are immutable outputs of the Presentation update phase.
Absence of new Intent is not cancellation; cancellation must be explicit.
Simulation tile position and presentation world position are separate concepts.
```

Recommended ownership diagram:

```text
World.update()
  writes Simulation state

Intent derivation
  reads Simulation state
  emits Intent updates

PresentationScene.update()
  consumes Intent updates
  writes Presentation state
  emits PresentationSnapshot

Renderer.draw()
  reads PresentationSnapshot
  writes pixels only
```

## Suggested Future Roadmap

### TASK-115 - Read-Only Presentation Snapshots

Purpose:

Ensure renderer draw calls cannot mutate Presentation state.

Completion criteria:

- `draw_agents(...)` no longer calls `snapshot_world(world)` if it mutates.
- `snapshot_world(...)` is removed, renamed or made read-only.
- Rendering the same snapshot twice does not change routes, action progress, agent lifetime or intent queues.

### TASK-116 - Presentation Position Ownership Split

Purpose:

Separate latest simulation tile mirrors from presentation execution state.

Completion criteria:

- `PresentationAgent` has explicit simulation position fields and explicit visual position/route fields.
- fallback movement no longer relies on ambiguous `tile_x/y`.
- disappearing movement intent cannot strand render position behind simulation truth.

### TASK-117 - Intent Update Semantics

Purpose:

Replace queue synchronization with explicit update semantics.

Completion criteria:

- movement intent can express continue, append, replace, cancel and invalidate.
- Presentation tracks accepted updates.
- repeated current simulation state does not replay completed visual routes.

### TASK-118 - PresentationAgent Lifecycle

Purpose:

Make visual entity lifetime persistent enough for departures, deaths and exits.

Completion criteria:

- PresentationAgents have lifecycle phases.
- simulation removal can become visual departure where appropriate.
- hard deletion is reserved for cleanup/reset/nonvisible entities.

### TASK-119 - Presentation Selection

Purpose:

Make selected-agent highlights follow presentation state.

Completion criteria:

- selected-agent visual highlight uses Presentation snapshot position.
- selection truth remains read-only and does not affect simulation.

## Final Assessment

The architecture is close, but it is crossing a classic boundary problem: the project has introduced Presentation as an executor, while some surrounding code still treats Presentation as a synchronized cache of simulation state.

The fix direction is clear:

```text
Do not make synchronization smarter.
Make ownership stricter.
```

Once Presentation update becomes the only mutation phase, snapshots become read-only, simulation mirrors are separated from visual execution state, and Intent becomes explicit updates rather than replaced queues, the repeated movement, popping and failure-to-leave symptoms should become much easier to resolve without further renderer drift.
