import pygame
import time

from src.config import (
    CAMERA_STEP,
    PERFORMANCE_LOGGING,
    PERFORMANCE_LOG_INTERVAL_FRAMES,
    SIMULATION_SPEED_SCALAR,
    SIM_TICKS_PER_SECOND,
)
from src.world import create_world
from src.renderer import PygameRenderer


def main():
    world = create_world()
    renderer = PygameRenderer(world)

    running = True
    paused = False
    sim_speed = SIM_TICKS_PER_SECOND
    simulation_speed_scalar = SIMULATION_SPEED_SCALAR

    accumulator = 0
    frame_count = 0
    last_sim_ms = 0.0
    sim_ticks_this_frame = 0

    while running:
        dt = renderer.clock.get_time() / 1000
        frame_start = time.perf_counter()
        if not paused:
            accumulator += dt * simulation_speed_scalar
        sim_ticks_this_frame = 0
        sim_start = time.perf_counter()

        for event in pygame.event.get():
            ui_consumed = renderer.process_ui_event(event)

            if event.type == pygame.QUIT:
                running = False

            if not ui_consumed and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                renderer.select_tile_at_pixel(*event.pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    paused = not paused

                elif event.key == pygame.K_w:
                    renderer.pan_camera(0, -CAMERA_STEP)

                elif event.key == pygame.K_s:
                    renderer.pan_camera(0, CAMERA_STEP)

                elif event.key == pygame.K_a:
                    renderer.pan_camera(-CAMERA_STEP, 0)

                elif event.key == pygame.K_d:
                    renderer.toggle_diagnostics_overlay()

                elif event.key == pygame.K_UP:
                    sim_speed = min(60, sim_speed + 1)

                elif event.key == pygame.K_DOWN:
                    sim_speed = max(1, sim_speed - 1)

                elif event.key == pygame.K_r:
                    world = create_world()
                    renderer.set_world(world)
                    accumulator = 0

                elif event.key == pygame.K_v:
                    renderer.toggle_villagers_overlay()

                elif event.key == pygame.K_h:
                    renderer.toggle_history_overlay()

        if not paused and len(world.living_agents()) > 0:
            step_time = 1 / sim_speed

            while accumulator >= step_time:
                world.update()
                accumulator -= step_time
                sim_ticks_this_frame += 1

        last_sim_ms = (time.perf_counter() - sim_start) * 1000

        renderer.update_ui(dt)
        renderer.draw(paused, sim_speed, last_sim_ms=last_sim_ms, sim_ticks=sim_ticks_this_frame)
        renderer.limit_fps()
        frame_count += 1

        if PERFORMANCE_LOGGING and frame_count % PERFORMANCE_LOG_INTERVAL_FRAMES == 0:
            frame_ms = (time.perf_counter() - frame_start) * 1000
            print(
                f"perf frame={frame_count} frame_ms={frame_ms:.2f} "
                f"sim_ms={last_sim_ms:.2f} sim_ticks={sim_ticks_this_frame} "
                f"sim_scalar={simulation_speed_scalar:.2f}"
            )

    pygame.quit()


if __name__ == "__main__":
    main()
