import pygame

from src.config import SIM_TICKS_PER_SECOND
from src.world import create_world
from src.renderer import PygameRenderer


def main():
    world = create_world()
    renderer = PygameRenderer(world)

    running = True
    paused = False
    sim_speed = SIM_TICKS_PER_SECOND

    accumulator = 0

    while running:
        dt = renderer.clock.get_time() / 1000
        accumulator += dt

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                renderer.select_tile_at_pixel(*event.pos)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False

                elif event.key == pygame.K_SPACE:
                    paused = not paused

                elif event.key == pygame.K_UP:
                    sim_speed = min(60, sim_speed + 1)

                elif event.key == pygame.K_DOWN:
                    sim_speed = max(1, sim_speed - 1)

                elif event.key == pygame.K_r:
                    world = create_world()
                    renderer.world = world
                    renderer.clear_selection()
                    accumulator = 0

        if not paused and len(world.living_agents()) > 0:
            step_time = 1 / sim_speed

            while accumulator >= step_time:
                world.update()
                accumulator -= step_time

        renderer.draw(paused, sim_speed)
        renderer.limit_fps()

    pygame.quit()


if __name__ == "__main__":
    main()
