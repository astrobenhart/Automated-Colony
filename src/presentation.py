from __future__ import annotations

from dataclasses import dataclass, field
import math

from src.intents import AgentIntent, IntentQueue, WALK_INTENT, intent_queue_for


ACTION_WAITING = "Waiting"
ACTION_STARTING = "Starting"
ACTION_PERFORMING = "Performing"
ACTION_FINISHING = "Finishing"
ACTION_COMPLETE = "Complete"


def presentation_id_for(agent) -> str:
    return getattr(agent, "agent_id", None) or getattr(agent, "name", "")


def presentation_key_for(agent) -> str:
    return getattr(agent, "agent_id", None) or f"object:{id(agent)}"


@dataclass(frozen=True)
class PresentationAgentSnapshot:
    agent_id: str
    name: str
    tile_x: int
    tile_y: int
    render_x: float
    render_y: float
    role: str
    current_action: str
    current_goal: str
    facing: tuple[int, int] = (0, 1)
    presentation_action: str = "Idle"
    presentation_action_state: str = ACTION_WAITING
    presentation_action_progress: float = 0.0
    presentation_route_remaining: int = 0
    route_recovery_reason: str | None = None


@dataclass(frozen=True)
class PresentationSnapshot:
    agents: tuple[PresentationAgentSnapshot, ...]
    camera: "ObserverCameraSnapshot | None" = None
    render_order: tuple[str, ...] = ("agents",)
    frame_index: int = 0
    elapsed_seconds: float = 0.0
    delta_seconds: float = 0.0
    interpolation_alpha: float = 0.0
    paused: bool = False


@dataclass
class PresentationTime:
    frame_index: int = 0
    elapsed_seconds: float = 0.0
    delta_seconds: float = 0.0
    interpolation_alpha: float = 0.0
    time_scale: float = 1.0
    paused: bool = False

    def advance(
        self,
        time_delta: float,
        *,
        paused: bool = False,
        time_scale: float | None = None,
        interpolation_alpha: float | None = None,
    ) -> "PresentationTime":
        scale = self.time_scale if time_scale is None else max(0.0, time_scale)
        scaled_delta = 0.0 if paused else max(0.0, time_delta) * scale
        self.frame_index += 1
        self.delta_seconds = scaled_delta
        self.elapsed_seconds += scaled_delta
        self.interpolation_alpha = max(0.0, min(1.0, interpolation_alpha if interpolation_alpha is not None else self.interpolation_alpha))
        self.time_scale = scale
        self.paused = paused
        return self


@dataclass(frozen=True)
class ObserverCameraSnapshot:
    world_x: float
    world_y: float
    target_x: float
    target_y: float
    viewport_width: int
    viewport_height: int
    world_width: int
    world_height: int


@dataclass
class ObserverCamera:
    """Presentation-owned camera in continuous world coordinates."""

    world_x: float = 0.0
    world_y: float = 0.0
    target_x: float = 0.0
    target_y: float = 0.0
    viewport_width: int = 0
    viewport_height: int = 0
    world_width: int = 0
    world_height: int = 0
    smoothing: float = 12.0

    def configure_viewport(
        self,
        *,
        world_width: int,
        world_height: int,
        viewport_width: int,
        viewport_height: int,
    ) -> None:
        self.world_width = max(0, world_width)
        self.world_height = max(0, world_height)
        self.viewport_width = max(0, viewport_width)
        self.viewport_height = max(0, viewport_height)
        self.target_x, self.target_y = self.clamped_position(self.target_x, self.target_y)
        self.world_x, self.world_y = self.clamped_position(self.world_x, self.world_y)

    def set_position(
        self,
        world_x: float,
        world_y: float,
        *,
        snap: bool = False,
        clamp: bool = True,
    ) -> None:
        if clamp:
            self.target_x, self.target_y = self.clamped_position(world_x, world_y)
        else:
            self.target_x = float(world_x)
            self.target_y = float(world_y)
        if snap:
            self.world_x = self.target_x
            self.world_y = self.target_y

    def pan_by(self, dx: float, dy: float, *, snap: bool = False) -> None:
        self.set_position(self.target_x + dx, self.target_y + dy, snap=snap, clamp=True)

    def advance(self, time_delta: float) -> None:
        if time_delta <= 0:
            return

        blend = 1.0 - math.exp(-self.smoothing * time_delta)
        self.world_x += (self.target_x - self.world_x) * blend
        self.world_y += (self.target_y - self.world_y) * blend
        if abs(self.target_x - self.world_x) < 0.001:
            self.world_x = self.target_x
        if abs(self.target_y - self.world_y) < 0.001:
            self.world_y = self.target_y

    def clamped_position(self, world_x: float, world_y: float) -> tuple[float, float]:
        max_x = max(0.0, self.world_width - self.viewport_width)
        max_y = max(0.0, self.world_height - self.viewport_height)
        return (
            max(0.0, min(float(world_x), max_x)),
            max(0.0, min(float(world_y), max_y)),
        )

    def visible_tile_bounds(self) -> tuple[int, int, int, int]:
        start_x = int(math.floor(self.world_x))
        start_y = int(math.floor(self.world_y))
        end_x = min(self.world_width, start_x + self.viewport_width)
        end_y = min(self.world_height, start_y + self.viewport_height)
        return start_x, start_y, end_x, end_y

    def world_to_screen(self, world_x: float, world_y: float, tile_size: int) -> tuple[float, float]:
        return (
            (world_x - self.world_x) * tile_size,
            (world_y - self.world_y) * tile_size,
        )

    def screen_to_world(self, screen_x: float, screen_y: float, tile_size: int) -> tuple[float, float]:
        return (
            self.world_x + screen_x / tile_size,
            self.world_y + screen_y / tile_size,
        )

    def screen_to_tile(self, screen_x: float, screen_y: float, tile_size: int) -> tuple[int, int]:
        world_x, world_y = self.screen_to_world(screen_x, screen_y, tile_size)
        return int(math.floor(world_x)), int(math.floor(world_y))

    def snapshot(self) -> ObserverCameraSnapshot:
        return ObserverCameraSnapshot(
            world_x=self.world_x,
            world_y=self.world_y,
            target_x=self.target_x,
            target_y=self.target_y,
            viewport_width=self.viewport_width,
            viewport_height=self.viewport_height,
            world_width=self.world_width,
            world_height=self.world_height,
        )


@dataclass
class PresentationAction:
    intent_id: str = ""
    kind: str = "idle"
    label: str = "Idle"
    state: str = ACTION_WAITING
    progress: float = 0.0
    duration: float = 1.0

    @classmethod
    def from_intent(cls, intent: AgentIntent | None) -> "PresentationAction":
        if intent is None:
            return cls()
        return cls(
            intent_id=intent.intent_id,
            kind=intent.kind,
            label=intent.label,
            duration=action_duration(intent.kind),
        )

    def advance(self, time_delta: float) -> None:
        if self.kind == "idle":
            self.state = ACTION_WAITING
            self.progress = 0.0
            return

        if self.state == ACTION_COMPLETE:
            return

        self.progress = min(1.0, self.progress + max(0.0, time_delta) / max(0.001, self.duration))
        if self.progress <= 0.0:
            self.state = ACTION_WAITING
        elif self.progress < 0.15:
            self.state = ACTION_STARTING
        elif self.progress < 0.82:
            self.state = ACTION_PERFORMING
        elif self.progress < 1.0:
            self.state = ACTION_FINISHING
        else:
            self.state = ACTION_COMPLETE

    def complete(self) -> None:
        if self.kind == "idle":
            return
        self.progress = 1.0
        self.state = ACTION_COMPLETE


@dataclass
class PresentationAgent:
    agent_id: str
    name: str
    tile_x: int
    tile_y: int
    render_x: float
    render_y: float
    from_x: float
    from_y: float
    target_x: float
    target_y: float
    progress: float = 1.0
    facing: tuple[int, int] = (0, 1)
    role: str = ""
    current_action: str = "Idle"
    current_goal: str = "Explore"
    active_intent_id: str | None = None
    presentation_route: tuple[tuple[int, int], ...] = ()
    route_recovery_reason: str | None = None
    presentation_action: PresentationAction = field(default_factory=PresentationAction)

    @property
    def movement_queue(self) -> tuple[tuple[int, int], ...]:
        """Compatibility alias for older tests and tooling.

        The presentation layer now owns a persistent route; Intent updates
        reconcile into it instead of replacing it every simulation tick.
        """
        return self.presentation_route

    @movement_queue.setter
    def movement_queue(self, value: tuple[tuple[int, int], ...]) -> None:
        self.presentation_route = tuple(value)

    @classmethod
    def from_agent(cls, agent) -> "PresentationAgent":
        agent_id = presentation_id_for(agent)
        x = float(getattr(agent, "x", 0))
        y = float(getattr(agent, "y", 0))
        return cls(
            agent_id=agent_id,
            name=getattr(agent, "name", agent_id),
            tile_x=getattr(agent, "x", 0),
            tile_y=getattr(agent, "y", 0),
            render_x=x,
            render_y=y,
            from_x=x,
            from_y=y,
            target_x=x,
            target_y=y,
            role=getattr(agent, "role", ""),
            current_action=getattr(agent, "current_action", "Idle"),
            current_goal=getattr(agent, "current_goal", "Explore"),
        )

    def observe(self, agent, intent: AgentIntent | None = None) -> None:
        next_x = getattr(agent, "x", self.tile_x)
        next_y = getattr(agent, "y", self.tile_y)
        self.name = getattr(agent, "name", self.name)
        self.role = getattr(agent, "role", self.role)
        self.current_action = getattr(agent, "current_action", self.current_action)
        self.current_goal = getattr(agent, "current_goal", self.current_goal)
        self.observe_presentation_action(intent)
        if intent is not None and intent.kind == WALK_INTENT:
            self.observe_movement_intent(agent, intent)
            return

        self.active_intent_id = None
        self.presentation_route = ()

        if (next_x, next_y) == (self.tile_x, self.tile_y):
            return

        self.tile_x = next_x
        self.tile_y = next_y
        self.start_motion_to(next_x, next_y)

    def observe_presentation_action(self, intent: AgentIntent | None) -> None:
        intent_id = intent.intent_id if intent is not None else ""
        if self.presentation_action.intent_id == intent_id:
            return
        self.presentation_action = PresentationAction.from_intent(intent)

    def observe_movement_intent(self, agent, intent: AgentIntent) -> None:
        self.tile_x = getattr(agent, "x", self.tile_x)
        self.tile_y = getattr(agent, "y", self.tile_y)
        if self.active_intent_id == intent.intent_id and self.presentation_route:
            return

        self.active_intent_id = intent.intent_id
        self.reconcile_presentation_route(intent.path)

    def reconcile_presentation_route(self, intent_path: tuple[tuple[int, int], ...]) -> None:
        incoming_route = normalize_route(intent_path)
        if not incoming_route:
            return

        if not self.presentation_route:
            self.initialize_presentation_route(incoming_route)
            return

        merged_route = merge_route_update(self.presentation_route, incoming_route)
        if merged_route is None:
            self.recover_presentation_route(incoming_route, "intent_diverged")
            return

        self.route_recovery_reason = None
        self.presentation_route = merged_route
        if self.progress >= 1.0:
            self.advance_to_next_waypoint()

    def initialize_presentation_route(self, incoming_route: tuple[tuple[int, int], ...]) -> None:
        first_waypoint = incoming_route[0]
        if not self.can_reach_next_waypoint(first_waypoint):
            self.recover_presentation_route(incoming_route, "route_started_ahead_of_render")
            return

        self.route_recovery_reason = None
        self.presentation_route = incoming_route
        self.advance_to_next_waypoint()

    def recover_presentation_route(self, incoming_route: tuple[tuple[int, int], ...], reason: str) -> None:
        """Explicitly recover from a route that Presentation cannot faithfully play.

        Normal movement never rebuilds the route. Recovery is reserved for cases
        where Presentation did not receive enough adjacent simulation-approved
        waypoints to preserve a visually faithful path.
        """
        first_x, first_y = incoming_route[0]
        self.render_x = float(first_x)
        self.render_y = float(first_y)
        self.from_x = self.render_x
        self.from_y = self.render_y
        self.target_x = self.render_x
        self.target_y = self.render_y
        self.progress = 1.0
        self.route_recovery_reason = reason
        self.presentation_route = incoming_route[1:]
        self.advance_to_next_waypoint()

    def can_reach_next_waypoint(self, waypoint: tuple[int, int]) -> bool:
        rounded_x = int(round(self.render_x))
        rounded_y = int(round(self.render_y))
        return abs(waypoint[0] - rounded_x) + abs(waypoint[1] - rounded_y) <= 1

    def start_motion_to(self, next_x: int | float, next_y: int | float) -> None:
        if (float(next_x), float(next_y)) == (self.target_x, self.target_y) and self.progress < 1.0:
            return

        dx = float(next_x) - self.render_x
        dy = float(next_y) - self.render_y
        if dx or dy:
            self.facing = (sign(dx), sign(dy))

        self.from_x = self.render_x
        self.from_y = self.render_y
        self.target_x = float(next_x)
        self.target_y = float(next_y)
        self.progress = 0.0

    def advance_to_next_waypoint(self) -> None:
        remaining = list(self.presentation_route)
        while remaining and (
            abs(remaining[0][0] - self.render_x) < 0.001
            and abs(remaining[0][1] - self.render_y) < 0.001
        ):
            remaining.pop(0)

        self.presentation_route = tuple(remaining)
        if self.presentation_route:
            next_x, next_y = self.presentation_route[0]
            self.start_motion_to(next_x, next_y)

    def advance(self, time_delta: float, tiles_per_second: float) -> None:
        self.presentation_action.advance(time_delta)
        remaining_time = max(0.0, time_delta)
        while True:
            if self.progress >= 1.0:
                self.render_x = self.target_x
                self.render_y = self.target_y
                if self.presentation_route:
                    self.presentation_route = self.presentation_route[1:]
                    if self.presentation_route:
                        next_x, next_y = self.presentation_route[0]
                        self.start_motion_to(next_x, next_y)
                    else:
                        return
                else:
                    if self.presentation_action.kind == WALK_INTENT:
                        self.presentation_action.complete()
                    return

            if remaining_time <= 0:
                return

            distance = max(0.001, abs(self.target_x - self.from_x) + abs(self.target_y - self.from_y))
            progress_delta = remaining_time * tiles_per_second / distance
            if self.progress + progress_delta >= 1.0:
                time_to_target = (1.0 - self.progress) * distance / max(0.001, tiles_per_second)
                self.progress = 1.0
                self.render_x = self.target_x
                self.render_y = self.target_y
                remaining_time = max(0.0, remaining_time - time_to_target)
                continue

            self.progress += progress_delta
            eased = smoothstep(self.progress)
            self.render_x = self.from_x + (self.target_x - self.from_x) * eased
            self.render_y = self.from_y + (self.target_y - self.from_y) * eased
            return

    def snapshot(self) -> PresentationAgentSnapshot:
        return PresentationAgentSnapshot(
            agent_id=self.agent_id,
            name=self.name,
            tile_x=self.tile_x,
            tile_y=self.tile_y,
            render_x=self.render_x,
            render_y=self.render_y,
            role=self.role,
            current_action=self.current_action,
            current_goal=self.current_goal,
            facing=self.facing,
            presentation_action=self.presentation_action.label,
            presentation_action_state=self.presentation_action.state,
            presentation_action_progress=self.presentation_action.progress,
            presentation_route_remaining=len(self.presentation_route),
            route_recovery_reason=self.route_recovery_reason,
        )


@dataclass
class PresentationScene:
    """Root of presentation-owned visual state.

    The scene observes simulation state and owns long-lived presentation objects.
    Gameplay systems should not depend on this class.
    """

    agents: dict[str, PresentationAgent] = field(default_factory=dict)
    intent_queues: dict[str, IntentQueue] = field(default_factory=dict)
    last_snapshot: PresentationSnapshot = field(default_factory=lambda: PresentationSnapshot(agents=()))
    render_order: tuple[str, ...] = ("agents",)
    presentation_time: PresentationTime = field(default_factory=PresentationTime)
    observer_camera: ObserverCamera = field(default_factory=ObserverCamera)

    @property
    def frame_state(self) -> PresentationTime:
        return self.presentation_time

    @property
    def camera(self) -> ObserverCamera:
        return self.observer_camera

    def configure_camera(
        self,
        *,
        world_width: int,
        world_height: int,
        viewport_width: int,
        viewport_height: int,
    ) -> None:
        self.observer_camera.configure_viewport(
            world_width=world_width,
            world_height=world_height,
            viewport_width=viewport_width,
            viewport_height=viewport_height,
        )

    def sync_world(self, world) -> None:
        living_agents = [agent for agent in getattr(world, "agents", ()) if getattr(agent, "alive", False)]
        live_ids = {presentation_key_for(agent) for agent in living_agents}
        for stale_id in set(self.agents) - live_ids:
            del self.agents[stale_id]
        for stale_id in set(self.intent_queues) - live_ids:
            del self.intent_queues[stale_id]

        for agent in living_agents:
            agent_key = presentation_key_for(agent)
            intent_queue = self.intent_queues.setdefault(agent_key, IntentQueue())
            derived_queue = intent_queue_for(agent)
            intent_queue.replace(derived_queue.items)
            presentation_agent = self.agents.get(agent_key)
            if presentation_agent is None:
                presentation_agent = PresentationAgent.from_agent(agent)
                self.agents[agent_key] = presentation_agent
                presentation_agent.observe(agent, intent_queue.peek())
            else:
                presentation_agent.observe(agent, intent_queue.peek())

        self.last_snapshot = self.snapshot()

    def update(
        self,
        world,
        time_delta: float,
        tiles_per_second: float,
        *,
        paused: bool = False,
        time_scale: float | None = None,
        interpolation_alpha: float | None = None,
    ) -> PresentationSnapshot:
        self.presentation_time.advance(
            time_delta,
            paused=paused,
            time_scale=time_scale,
            interpolation_alpha=interpolation_alpha,
        )
        self.sync_world(world)
        self.observer_camera.configure_viewport(
            world_width=getattr(world, "width", self.observer_camera.world_width),
            world_height=getattr(world, "height", self.observer_camera.world_height),
            viewport_width=self.observer_camera.viewport_width,
            viewport_height=self.observer_camera.viewport_height,
        )
        self.observer_camera.advance(self.presentation_time.delta_seconds)
        for agent in self.agents.values():
            agent.advance(self.presentation_time.delta_seconds, tiles_per_second)
        self.last_snapshot = self.snapshot()
        return self.last_snapshot

    def snapshot(self) -> PresentationSnapshot:
        return PresentationSnapshot(
            agents=tuple(agent.snapshot() for agent in self.agents.values()),
            camera=self.observer_camera.snapshot(),
            render_order=self.render_order,
            frame_index=self.presentation_time.frame_index,
            elapsed_seconds=self.presentation_time.elapsed_seconds,
            delta_seconds=self.presentation_time.delta_seconds,
            interpolation_alpha=self.presentation_time.interpolation_alpha,
            paused=self.presentation_time.paused,
        )

    def snapshot_world(self, world) -> PresentationSnapshot:
        self.sync_world(world)
        return self.last_snapshot


class PresentationEngine(PresentationScene):
    """Compatibility name for the first presentation root."""


def smoothstep(progress: float) -> float:
    progress = max(0.0, min(1.0, progress))
    return progress * progress * (3.0 - 2.0 * progress)


def sign(value: int | float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def normalize_route(route: tuple[tuple[int, int], ...]) -> tuple[tuple[int, int], ...]:
    normalized: list[tuple[int, int]] = []
    for waypoint in route:
        point = (int(waypoint[0]), int(waypoint[1]))
        if not normalized or normalized[-1] != point:
            normalized.append(point)
    return tuple(normalized)


def merge_route_update(
    existing_route: tuple[tuple[int, int], ...],
    incoming_route: tuple[tuple[int, int], ...],
) -> tuple[tuple[int, int], ...] | None:
    existing = list(existing_route)
    incoming = list(incoming_route)

    for existing_position, point in enumerate(existing):
        if point in incoming:
            incoming_position = incoming.index(point)
            return normalize_route(tuple(existing[: existing_position + 1] + incoming[incoming_position + 1 :]))

    if existing and incoming and existing[-1] == incoming[0]:
        return normalize_route(tuple(existing + incoming[1:]))

    return None


def action_duration(kind: str) -> float:
    return {
        WALK_INTENT: 1.0,
        "harvest": 1.4,
        "deposit": 0.9,
        "eat": 1.2,
        "sleep": 2.0,
    }.get(kind, 1.0)
