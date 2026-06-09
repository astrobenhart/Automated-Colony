import pygame
import pygame_gui

from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    PANEL_WIDTH,
    VIEWPORT_WIDTH,
    VIEWPORT_HEIGHT,
    TILE_SIZE,
    CAMERA_STEP,
    DEBUG_DRAW_GRID,
    COLORS,
    TERRAIN_LABELS,
    SYMBOL_LABELS,
    FPS,
)
from src.environment_events import active_event_names, environmental_tile_color
from src.farming import farm_border_edges
from src.overlays.villagers import VILLAGERS_OVERLAY, VillagersOverlay
from src.resource_ecology import max_food, max_wood
from src.roles import BUILDER, FORAGER, GENERALIST, SCOUT
from src.seasons import seasonal_tile_color
from src.social_memory import familiarity_summary
from src.state import state_label
from src.agent import Agent
from src.profiler import profiler
from src.ui_overlays import OverlayManager
from src.world import World


ROLE_COLOR_KEYS = {
    GENERALIST: "role_generalist",
    FORAGER: "role_forager",
    BUILDER: "role_builder",
    SCOUT: "role_scout",
}


def color_for_role(role: str | None) -> tuple[int, int, int]:
    return COLORS.get(ROLE_COLOR_KEYS.get(role, "agent"), COLORS["agent"])


def is_food_visible_to_player(world: World, x: int, y: int) -> bool:
    return (x, y) in world.colony_memory.known_food


def is_wood_visible_to_player(world: World, x: int, y: int) -> bool:
    return (x, y) in world.colony_memory.known_wood


class PygameRenderer:
    def __init__(self, world: World):
        pygame.init()

        self.world = world
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Automated ASCII Colony v0.1")
        self.ui_manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.overlay_manager = OverlayManager()
        self.register_overlays()

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas", 13)
        self.big_font = pygame.font.SysFont("consolas", 17, bold=True)

        self.selected_agent: Agent | None = None
        self.selected_tile: tuple[int, int] | None = None
        self.panel_padding = 14
        self.panel_gap = 8
        self.camera_x = 0
        self.camera_y = 0

    def register_overlays(self):
        self.overlay_manager.register_overlay(
            VILLAGERS_OVERLAY,
            lambda: VillagersOverlay(self.world, self.ui_manager, self.select_agent),
        )

    def set_world(self, world: World):
        self.world = world
        self.clear_selection()
        self.overlay_manager.close_all()
        self.clamp_camera()

    def process_ui_event(self, event) -> bool:
        overlay_consumed = self.overlay_manager.handle_event(event)
        gui_consumed = self.ui_manager.process_events(event)
        return overlay_consumed or gui_consumed

    def update_ui(self, time_delta: float):
        self.overlay_manager.update(time_delta)
        self.ui_manager.update(time_delta)

    def toggle_villagers_overlay(self):
        self.overlay_manager.toggle_overlay(VILLAGERS_OVERLAY)

    def select_agent(self, agent: Agent):
        if agent not in self.world.agents:
            self.clear_selection()
            return
        self.selected_agent = agent
        self.selected_tile = None

    def select_tile_at_pixel(self, mouse_x: int, mouse_y: int):
        tile = self.screen_to_world_tile(mouse_x, mouse_y)
        if tile is None:
            self.clear_selection()
            return

        tile_x, tile_y = tile
        self.select_tile(tile_x, tile_y)

    def screen_to_world_tile(self, mouse_x: int, mouse_y: int) -> tuple[int, int] | None:
        map_width = VIEWPORT_WIDTH * TILE_SIZE
        map_height = VIEWPORT_HEIGHT * TILE_SIZE
        if not (0 <= mouse_x < map_width and 0 <= mouse_y < map_height):
            return None

        return (
            self.camera_x + mouse_x // TILE_SIZE,
            self.camera_y + mouse_y // TILE_SIZE,
        )

    def camera_step(self) -> int:
        return CAMERA_STEP

    def pan_camera(self, dx: int, dy: int):
        self.camera_x += dx
        self.camera_y += dy
        self.clamp_camera()

    def clamp_camera(self):
        max_x = max(0, self.world.width - VIEWPORT_WIDTH)
        max_y = max(0, self.world.height - VIEWPORT_HEIGHT)
        self.camera_x = max(0, min(self.camera_x, max_x))
        self.camera_y = max(0, min(self.camera_y, max_y))

    def visible_tile_bounds(self) -> tuple[int, int, int, int]:
        self.clamp_camera()
        start_x = self.camera_x
        start_y = self.camera_y
        end_x = min(self.world.width, start_x + VIEWPORT_WIDTH)
        end_y = min(self.world.height, start_y + VIEWPORT_HEIGHT)
        return start_x, start_y, end_x, end_y

    def select_tile(self, tile_x: int, tile_y: int):
        if not (0 <= tile_x < self.world.width and 0 <= tile_y < self.world.height):
            self.clear_selection()
            return

        agent = self.world.agent_at(tile_x, tile_y)
        if agent is not None:
            self.select_agent(agent)
            return

        self.selected_agent = None
        self.selected_tile = (tile_x, tile_y)

    def clear_selection(self):
        self.selected_agent = None
        self.selected_tile = None

    def validate_selection(self):
        if self.selected_agent is not None and self.selected_agent not in self.world.agents:
            self.clear_selection()

        if self.selected_tile is not None:
            x, y = self.selected_tile
            if not (0 <= x < self.world.width and 0 <= y < self.world.height):
                self.clear_selection()

    def draw(self, paused: bool, sim_speed: int):
        with profiler.time("renderer update"):
            self.validate_selection()
            self.clamp_camera()
            self.screen.fill((0, 0, 0))

            self.draw_world()
            self.draw_panel(paused, sim_speed)
            self.ui_manager.draw_ui(self.screen)

            pygame.display.flip()

    def draw_world(self):
        start_x, start_y, end_x, end_y = self.visible_tile_bounds()

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile = self.world.tile_at(x, y)
                screen_x = x - start_x
                screen_y = y - start_y

                rect = pygame.Rect(
                    screen_x * TILE_SIZE,
                    screen_y * TILE_SIZE,
                    TILE_SIZE,
                    TILE_SIZE,
                )

                pygame.draw.rect(self.screen, self.tile_color(tile.kind), rect)
                if DEBUG_DRAW_GRID:
                    pygame.draw.rect(self.screen, COLORS["grid"], rect, 1)

                farm = self.world.farm_at(x, y)
                if farm is not None:
                    self.draw_farm_border(farm, screen_x, screen_y, x, y)
                    if farm.food > 0:
                        self.draw_centered_symbol("#", screen_x, screen_y, COLORS["farm_crop"])

                if tile.food > 0 and is_food_visible_to_player(self.world, x, y):
                    self.draw_centered_symbol("f", screen_x, screen_y, self.resource_color("food", tile.food, max_food(tile)))

                if tile.wood > 0 and is_wood_visible_to_player(self.world, x, y):
                    self.draw_centered_symbol("w", screen_x, screen_y, self.resource_color("wood", tile.wood, max_wood(tile)))

                animal = self.world.animal_at(x, y)
                if animal:
                    self.draw_centered_symbol(animal.symbol, screen_x, screen_y, COLORS["wildlife"])

                if self.is_settlement_center(x, y):
                    self.draw_centered_symbol("+", screen_x, screen_y, COLORS["settlement"])

                stockpile = self.world.stockpile_at(x, y)
                if stockpile:
                    symbol = "F" if stockpile.stockpile_type == "food" else "W"
                    color = COLORS["stockpile_food"] if stockpile.stockpile_type == "food" else COLORS["stockpile_wood"]
                    self.draw_centered_symbol(symbol, screen_x, screen_y, color)

                workshop = self.world.workshop_at(x, y)
                if workshop:
                    self.draw_centered_symbol("T", screen_x, screen_y, COLORS["workshop"])

                agent = self.world.agent_at(x, y)
                if agent:
                    self.draw_centered_symbol("@", screen_x, screen_y, color_for_role(agent.role))

        self.draw_selection_highlight()

    def draw_selection_highlight(self):
        if self.selected_agent is not None:
            x = self.selected_agent.x
            y = self.selected_agent.y
            color = COLORS["selection_agent"]
        elif self.selected_tile is not None:
            x, y = self.selected_tile
            color = COLORS["selection"]
        else:
            return

        start_x, start_y, end_x, end_y = self.visible_tile_bounds()
        if not (start_x <= x < end_x and start_y <= y < end_y):
            return

        screen_x = x - start_x
        screen_y = y - start_y

        rect = pygame.Rect(
            screen_x * TILE_SIZE,
            screen_y * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        pygame.draw.rect(self.screen, color, rect, 2)

    def draw_centered_symbol(self, symbol: str, x: int, y: int, color: tuple):
        surface = self.font.render(symbol, True, color)
        rect = surface.get_rect(
            center=(
                x * TILE_SIZE + TILE_SIZE // 2,
                y * TILE_SIZE + TILE_SIZE // 2,
            )
        )
        self.screen.blit(surface, rect)

    def draw_farm_border(self, farm, screen_x: int, screen_y: int, tile_x: int, tile_y: int):
        rect = pygame.Rect(
            screen_x * TILE_SIZE,
            screen_y * TILE_SIZE,
            TILE_SIZE,
            TILE_SIZE,
        )
        color = COLORS["farm_border"]
        edges = farm_border_edges(farm, tile_x, tile_y)
        if edges["north"]:
            pygame.draw.line(self.screen, color, rect.topleft, rect.topright, 2)
        if edges["south"]:
            pygame.draw.line(self.screen, color, rect.bottomleft, rect.bottomright, 2)
        if edges["west"]:
            pygame.draw.line(self.screen, color, rect.topleft, rect.bottomleft, 2)
        if edges["east"]:
            pygame.draw.line(self.screen, color, rect.topright, rect.bottomright, 2)

    def draw_panel(self, paused: bool, sim_speed: int):
        panel_x = VIEWPORT_WIDTH * TILE_SIZE
        content_x = panel_x + self.panel_padding
        content_width = PANEL_WIDTH - self.panel_padding * 2
        bottom_y = SCREEN_HEIGHT - self.panel_padding

        pygame.draw.rect(
            self.screen,
            COLORS["panel"],
            pygame.Rect(panel_x, 0, PANEL_WIDTH, SCREEN_HEIGHT),
        )

        y = self.panel_padding

        y = self.draw_world_identity_header(content_x, y, content_width, bottom_y)
        y += self.panel_gap

        y = self.draw_time_grid(content_x, y, content_width, bottom_y, sim_speed)

        y += self.panel_gap
        y = self.draw_colony_summary(content_x, y, content_width, bottom_y)

        y += self.panel_gap
        y = self.draw_section_header("Active Events", content_x, y, content_width, bottom_y)
        y = self.draw_text_line(
            active_event_names(self.world.active_environment_events),
            content_x,
            y,
            content_width,
            bottom_y,
            color=COLORS["muted"],
        )

        y += self.panel_gap
        y = self.draw_history_summary(content_x, y, content_width, bottom_y)

        y += self.panel_gap
        y = self.draw_legend(content_x, y, content_width, bottom_y)

        y += self.panel_gap
        y = self.draw_section_header("Controls", content_x, y, content_width, bottom_y)
        controls = "WASD pan | V villagers | Space pause | Up/Down speed | R restart | Esc quit"
        y = self.draw_wrapped_text(controls, content_x, y, content_width, bottom_y, COLORS["muted"])

        y += self.panel_gap
        y = self.draw_selection_details(content_x, y, content_width, bottom_y)

        y += self.panel_gap
        y = self.draw_section_header("Recent Events", content_x, y, content_width, bottom_y)
        line_height = self.font.get_height() + 3
        max_events = max(0, (bottom_y - y) // line_height)
        if max_events > 0:
            for event in self.world.events[-max_events:]:
                y = self.draw_text_line(event, content_x, y, content_width, bottom_y, color=COLORS["muted"])

    def draw_world_identity_header(self, x: int, y: int, width: int, bottom_y: int):
        identity = self.world.identity
        if identity is None:
            y = self.draw_text_line("Automated Colony", x, y, width, bottom_y, self.big_font)
            return y

        y = self.draw_text_line(identity.title, x, y, width, bottom_y, self.big_font)
        y = self.draw_text_line(identity.subtitle, x, y, width, bottom_y, color=COLORS["muted"])
        y = self.draw_text_line(f"Survival: {identity.survival_outlook}", x, y, width, bottom_y, color=COLORS["warning"])
        return y

    def time_grid_rows(self, sim_speed: int) -> list[tuple[str, object]]:
        return [
            ("Day", self.world.day),
            ("Year", self.world.year),
            ("Season", self.world.season_label),
            ("Speed", f"{sim_speed}x"),
        ]

    def draw_time_grid(self, x: int, y: int, width: int, bottom_y: int, sim_speed: int):
        rows = self.time_grid_rows(sim_speed)
        left_x, column_width, right_x, right_width = self.panel_column_layout(x, width)
        first_y = y
        y = self.draw_compact_stat_row(rows[0][0], rows[0][1], left_x, first_y, column_width, bottom_y)
        right_y = self.draw_compact_stat_row(rows[1][0], rows[1][1], right_x, first_y, right_width, bottom_y)
        second_y = max(y, right_y)
        y = self.draw_compact_stat_row(rows[2][0], rows[2][1], left_x, second_y, column_width, bottom_y)
        right_y = self.draw_compact_stat_row(rows[3][0], rows[3][1], right_x, second_y, right_width, bottom_y)
        return max(y, right_y)

    def colony_summary_lines(self) -> list[str]:
        settlement = self.world.settlement
        report = settlement.carrying_capacity_report if settlement is not None else None
        status = report.status if report is not None else "Unknown"
        farm_count = len([farm for farm in settlement.farm_plots if farm.active]) if settlement is not None else 0

        lines = [
            f"{len(self.world.living_agents())} Villagers",
            status,
            f"Food {self.world.colony_storage.food} | Wood {self.world.colony_storage.wood}",
            f"Farms {farm_count} | Mats {self.world.colony_storage.building_materials}",
        ]
        reasons = self.colony_reason_lines(max_lines=3)
        if reasons:
            lines.append("Reason:")
            lines.extend(reasons)
        return lines

    def colony_reason_lines(self, max_lines: int = 3) -> list[str]:
        settlement = self.world.settlement
        if settlement is None or settlement.carrying_capacity_report is None:
            return []
        report = settlement.carrying_capacity_report
        if report.status == "Stable":
            return []

        reasons = []
        population = max(1, report.population)
        if report.status == "Food Strained":
            if self.world.colony_storage.food <= population * 2:
                reasons.append("Food stores low")
            if len(settlement.local_food) <= 2:
                reasons.append("Few local food sources")
            if not any(farm.active for farm in settlement.farm_plots):
                reasons.append("No active farms")
        elif report.status == "Water Strained":
            reasons.append("Limited local water")
        elif report.status == "Shelter Strained":
            reasons.append("Shelter space short")

        if not reasons:
            reasons.append(report.reason)
        return reasons[:max_lines]

    def draw_colony_summary(self, x: int, y: int, width: int, bottom_y: int):
        y = self.draw_section_header("Colony", x, y, width, bottom_y)
        lines = self.colony_summary_lines()
        for index, line in enumerate(lines):
            color = COLORS["warning"] if index == 1 and line != "Stable" else COLORS["text"]
            if line == "Reason:":
                color = COLORS["muted"]
            elif index > 4:
                color = COLORS["muted"]
            y = self.draw_text_line(line, x, y, width, bottom_y, color=color)
        return y

    def draw_selection_details(self, x: int, y: int, width: int, bottom_y: int):
        y = self.draw_section_header("Selection", x, y, width, bottom_y)

        if self.selected_agent is not None:
            agent = self.selected_agent
            target = agent.current_target if agent.current_target is not None else "None"
            known_water = len(agent.remembered_water | self.world.colony_memory.known_water)
            known_food = len(agent.remembered_food | self.world.colony_memory.known_food)
            details = [
                ("Agent", agent.name),
                ("Role", agent.role),
                ("Life", agent.lifecycle_stage),
                ("Trait", agent.trait),
                ("State", state_label(agent, self.world)),
                ("Knows", ", ".join(familiarity_summary(agent)) or "None"),
                ("Pos", f"({agent.x}, {agent.y})"),
                ("Needs", f"H{agent.hunger} T{agent.thirst} F{agent.fatigue}"),
                ("Carry", f"Food {agent.food}, Wood {agent.wood}"),
                ("Goal", agent.current_goal),
                ("Action", agent.current_action),
                ("Target", target),
                ("Path", len(agent.current_path)),
                ("Idle", agent.no_progress_ticks),
                ("Recover", agent.current_action == "Recovering"),
                ("Known W", known_water),
                ("Known F", known_food),
            ]
            color = COLORS["text"] if agent.alive else COLORS["dead"]

        elif self.selected_tile is not None:
            tile_x, tile_y = self.selected_tile
            tile = self.world.tile_at(tile_x, tile_y)
            details = [
                ("Tile", f"({tile_x}, {tile_y})"),
                ("Terrain", tile.kind),
                ("Food", tile.food if is_food_visible_to_player(self.world, tile_x, tile_y) else "Unknown"),
                ("Wood", tile.wood if is_wood_visible_to_player(self.world, tile_x, tile_y) else "Unknown"),
                ("Walkable", tile.walkable),
            ]
            if self.is_settlement_center(tile_x, tile_y) and self.world.settlement is not None:
                settlement = self.world.settlement
                details.extend([
                    ("Settlement", settlement.name),
                    ("Pop", settlement.population),
                    ("Center", f"{settlement.x},{settlement.y}"),
                    ("Radius", settlement.radius),
                    ("Founded", f"D{settlement.founded_day} {settlement.founded_season}"),
                    ("Claims", len(self.world.reservations.reservations)),
                ])
                report = settlement.carrying_capacity_report
                if report is not None:
                    details.extend([
                        ("Capacity", report.capacity),
                        ("Status", report.status),
                    ])
            stockpile = self.world.stockpile_at(tile_x, tile_y)
            if stockpile is not None:
                label = "Food" if stockpile.stockpile_type == "food" else "Wood"
                details.extend([
                    ("Stockpile", label),
                    ("Stored", stockpile.stored_amount),
                    ("Capacity", stockpile.capacity),
                ])
            workshop = self.world.workshop_at(tile_x, tile_y)
            if workshop is not None:
                details.extend([
                    ("Workshop", workshop.kind),
                    ("Makes", workshop.production),
                    ("Progress", workshop.progress),
                    ("Produced", workshop.total_items_produced),
                ])
            farm = self.world.farm_at(tile_x, tile_y)
            if farm is not None:
                details.extend([
                    ("Farm Plot", f"{farm.origin_x},{farm.origin_y}"),
                    ("Growth", farm.growth),
                    ("Farm Food", farm.food),
                    ("Fertility", round(farm.fertility, 2)),
                ])
            color = COLORS["text"]

        else:
            details = [("Selected", "None")]
            color = COLORS["muted"]

        for label, value in details:
            y = self.draw_stat_row(label, value, x, y, width, bottom_y, color=color)

        return y

    def draw_two_column_section(
        self,
        left_title: str,
        left_rows: list[tuple[str, object]],
        right_title: str,
        right_rows: list[tuple[str, object]],
        x: int,
        y: int,
        width: int,
        bottom_y: int,
    ):
        left_x, column_width, right_x, right_width = self.panel_column_layout(x, width)

        left_y = self.draw_section_header(left_title, left_x, y, column_width, bottom_y)
        right_y = self.draw_section_header(right_title, right_x, y, right_width, bottom_y)
        header_bottom = max(left_y, right_y)

        left_y = header_bottom
        right_y = header_bottom
        for label, value in left_rows:
            left_y = self.draw_compact_stat_row(label, value, left_x, left_y, column_width, bottom_y)
        for label, value in right_rows:
            right_y = self.draw_compact_stat_row(label, value, right_x, right_y, right_width, bottom_y)

        return max(left_y, right_y)

    def panel_column_layout(self, x: int, width: int):
        gap = self.panel_gap * 2
        column_width = (width - gap) // 2
        right_x = x + column_width + gap
        right_width = width - column_width - gap
        return x, column_width, right_x, right_width

    def draw_history_summary(self, x: int, y: int, width: int, bottom_y: int):
        y = self.draw_section_header("History", x, y, width, bottom_y)
        y = self.draw_stat_row("Entries", self.world.history.count(), x, y, width, bottom_y)
        recent = self.world.history.recent(1)
        if recent:
            entry = recent[0]
            y = self.draw_text_line(
                f"Last: D{entry.day} {entry.title}",
                x,
                y,
                width,
                bottom_y,
                color=COLORS["muted"],
            )
        return y

    def draw_legend(self, x: int, y: int, width: int, bottom_y: int):
        y = self.draw_section_header(f"Legend ({self.world.season_label})", x, y, width, bottom_y)
        column_width = width // 2
        row_height = self.font.get_height() + 3
        items = list(TERRAIN_LABELS.items())

        for index in range(0, len(items), 2):
            if y + row_height > bottom_y:
                return y

            for column, (kind, label) in enumerate(items[index:index + 2]):
                item_x = x + column * column_width
                self.draw_legend_item(kind, label, item_x, y, column_width - 8)

            y += row_height

        symbol_text = "  ".join(f"{symbol} {label}" for symbol, label in SYMBOL_LABELS.items())
        y = self.draw_wrapped_text(symbol_text, x, y, width, bottom_y, COLORS["muted"])
        return y

    def draw_legend_item(self, kind: str, label: str, x: int, y: int, width: int):
        swatch_size = 10
        swatch_y = y + max(0, (self.font.get_height() - swatch_size) // 2)
        pygame.draw.rect(
            self.screen,
            self.tile_color(kind),
            pygame.Rect(x, swatch_y, swatch_size, swatch_size),
        )

        text_x = x + swatch_size + 6
        text_width = max(0, width - swatch_size - 6)
        surface = self.font.render(self.fit_text(label, self.font, text_width), True, COLORS["text"])
        self.screen.blit(surface, (text_x, y))

    def tile_color(self, kind: str):
        season_color = seasonal_tile_color(
            kind,
            self.world.season,
            self.world.next_season,
            self.world.transition_progress,
        )
        return environmental_tile_color(season_color, kind, self.world.active_environment_events)

    def is_settlement_center(self, x: int, y: int) -> bool:
        settlement = self.world.settlement
        return settlement is not None and settlement.x == x and settlement.y == y

    def resource_color(self, resource: str, amount: int, cap: int):
        base = COLORS[resource]
        if cap <= 1:
            strength = 1.0
        else:
            strength = max(0.35, min(1.0, amount / cap))

        muted = tuple(max(40, round(channel * 0.45)) for channel in base)
        return tuple(
            round(muted_channel + (base_channel - muted_channel) * strength)
            for muted_channel, base_channel in zip(muted, base)
        )

    def draw_section_header(self, text: str, x: int, y: int, width: int, bottom_y: int):
        y = self.draw_text_line(text, x, y, width, bottom_y, self.big_font)
        return y + 2

    def draw_stat_row(
        self,
        label: str,
        value,
        x: int,
        y: int,
        width: int,
        bottom_y: int,
        color=None,
    ):
        label_text = f"{label}:"
        value_text = str(value)
        line = f"{label_text:<10} {value_text}"
        return self.draw_text_line(line, x, y, width, bottom_y, color=color)

    def draw_compact_stat_row(
        self,
        label: str,
        value,
        x: int,
        y: int,
        width: int,
        bottom_y: int,
        color=None,
    ):
        line = f"{label}: {value}"
        return self.draw_text_line(line, x, y, width, bottom_y, color=color)

    def draw_wrapped_text(self, text: str, x: int, y: int, width: int, bottom_y: int, color=None):
        words = text.split()
        line = ""

        for word in words:
            candidate = word if not line else f"{line} {word}"
            if self.font.size(candidate)[0] <= width:
                line = candidate
                continue

            if line:
                y = self.draw_text_line(line, x, y, width, bottom_y, color=color)
            line = word

        if line:
            y = self.draw_text_line(line, x, y, width, bottom_y, color=color)

        return y

    def draw_text_line(self, text: str, x: int, y: int, width: int, bottom_y: int, font=None, color=None):
        if font is None:
            font = self.font

        if color is None:
            color = COLORS["text"]

        if y + font.get_height() > bottom_y:
            return y

        surface = font.render(self.fit_text(str(text), font, width), True, color)
        self.screen.blit(surface, (x, y))

        return y + surface.get_height() + 3

    def fit_text(self, text: str, font, max_width: int):
        if font.size(text)[0] <= max_width:
            return text

        ellipsis = "..."
        available_width = max_width - font.size(ellipsis)[0]
        if available_width <= 0:
            return ellipsis

        fitted = ""
        for char in text:
            if font.size(fitted + char)[0] > available_width:
                break
            fitted += char

        return fitted + ellipsis

    def draw_line(self, text: str, x: int, y: int, font=None, color=None):
        if font is None:
            font = self.font

        if color is None:
            color = COLORS["text"]

        surface = font.render(text, True, color)
        self.screen.blit(surface, (x, y))

        return y + surface.get_height() + 4

    def limit_fps(self):
        self.clock.tick(FPS)
