import sys
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import glm
import math
import numpy as np

from constants import windowSize
from shaderProgram import ShaderProgram
from camera import Camera
from model import Model
from ground import Ground
from shadowMap import ShadowMap
from light import Light

# Global state
aspect_ratio = 1.0
sp: ShaderProgram
depth_shader: ShaderProgram
camera: Camera
piano: Model
ground: Ground
shadow_map: ShadowMap
light: Light

def clamp(val, lo, hi):
    return max(lo, min(val, hi))


def init_pygame_opengl():
    global sp, camera, aspect_ratio, piano, depth_shader, ground, shadow_map, light

    # Initialize Pygame and OpenGL context
    pygame.init()
    screen = pygame.display.set_mode(
        (int(windowSize.x), int(windowSize.y)),
        DOUBLEBUF | OPENGL | RESIZABLE
    )
    pygame.display.set_caption("OpenGL with Pygame")

    # OpenGL setup
    glClearColor(0.1, 0.1, 0.1, 1.0)
    glEnable(GL_DEPTH_TEST)
    glDisable(GL_CULL_FACE)

    # Load shader program, shadow map and model
    shadow_map = ShadowMap()
    light = Light()
    sp = ShaderProgram("shaders/vertex_shader.glsl", None, "shaders/fragment_shader.glsl")
    depth_shader = ShaderProgram("shaders/depth_vertex.glsl", None, "shaders/depth_fragment.glsl")
    piano = Model()
    ground = Ground("textures/wood-floor-texture.png")
    if not piano.load_model("models/piano.obj"):
        print("Failed to load model", file=sys.stderr)
        sys.exit(1)
    # Camera after knowing window size
    width, height = pygame.display.get_surface().get_size()
    aspect_ratio = width / height
    camera = Camera(windowSize)

    # Mouse settings
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)
    camera.first_mouse_move = True


def process_input(dt):
    camera_displacement = camera.process_keyboard_input(dt)
    camera.check_for_collision(piano, camera_displacement)
    camera.check_if_out_of_bounds(ground.size)
    light.process_keyboard_input(dt)


def handle_mouse_motion(dt):
    camera.process_mouse_movement(dt)


def resize_viewport(event):
    global aspect_ratio
    width, height = event.size
    if height == 0:
        return
    aspect_ratio = width / height
    glViewport(0, 0, width, height)


def draw_scene():
    # build matrices
    M = glm.mat4(1.0)
    ground_M = glm.mat4(1.0)
    ground_M = glm.translate(ground_M, glm.vec3(0.0, -1.5, 0.0))

    light_space_matrix = light.calculate_light_space_matrix()
    
    # render
    shadow_map.render(ground, depth_shader, sp, light_space_matrix, model_matrix=ground_M)
    shadow_map.render(piano, depth_shader, sp, light_space_matrix, model_matrix=M)

    glViewport(0, 0, windowSize.x, windowSize.y)
    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    sp.use()
    # camera
    camera.set_up_in_scene(sp, aspect_ratio)
    # light
    light.set_up_in_scene(sp, camera.pos, light_space_matrix)
    shadow_map.set_up_in_scene(sp)
    piano.draw(sp, M)
    ground.draw(sp, ground_M)
    pygame.display.flip()


def main():
    init_pygame_opengl()
    clock = pygame.time.Clock()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0  # seconds

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == VIDEORESIZE:
                resize_viewport(event)
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False
            elif event.type == MOUSEMOTION:
                handle_mouse_motion(dt)

        process_input(dt)
        draw_scene()

    pygame.quit()
    sys.exit(0)


if __name__ == '__main__':
    main()
