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

# Global state
aspect_ratio = 1.0
boundary_margin = 20
sp: ShaderProgram
depth_shader: ShaderProgram
camera: Camera
piano: Model
ground: Ground

def clamp(val, lo, hi):
    return max(lo, min(val, hi))


def init_pygame_opengl():
    global sp, camera, aspect_ratio, piano, depth_shader, ground

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

    # Load shader program and model
    sp = ShaderProgram("shaders/vertex_shader.glsl", None, "shaders/fragment_shader.glsl")
    depth_shader = ShaderProgram("shaders/depth_vertex.glsl", None, "shaders/depth_fragment.glsl")
    piano = Model()
    ground = Ground()
    if not piano.load_model("models/piano.obj"):
        print("Failed to load model", file=sys.stderr)
        sys.exit(1)
    piano.init_shadow_map()
    ground.init_ground()

    # Camera after knowing window size
    width, height = pygame.display.get_surface().get_size()
    aspect_ratio = width / height
    camera = Camera(windowSize)

    # Mouse settings
    pygame.event.set_grab(True)
    pygame.mouse.set_visible(False)
    camera.first_mouse_move = True

    return screen


def process_input(dt):
    global camera, piano, ground, boundary_margin
    keys = pygame.key.get_pressed()
    camera_speed = 8.0 * dt

    flat_front = glm.normalize(glm.vec3(camera.front.x, 0.0, camera.front.z))
    flat_right = glm.normalize(glm.cross(flat_front, camera.up))
    displacement = glm.vec3(0.0, 0.0, 0.0)

    if keys[K_w]:
        displacement += flat_front * camera_speed
    if keys[K_s]:
        displacement -= flat_front * camera_speed
    if keys[K_a]:
        displacement -= flat_right * camera_speed
    if keys[K_d]:
        displacement += flat_right * camera_speed

    new_pos = camera.pos
    # X-axis collision test
    test_x = new_pos.x + displacement.x
    if not piano.does_collide(glm.vec3(test_x, new_pos.y, new_pos.z)):
        new_pos.x = test_x
    # Z-axis collision test
    test_z = new_pos.z + displacement.z
    if not piano.does_collide(glm.vec3(new_pos.x, new_pos.y, test_z)):
        new_pos.z = test_z

    min_bound = -ground.size + boundary_margin
    max_bound =  ground.size - boundary_margin
    new_pos.x = clamp(new_pos.x, min_bound, max_bound)
    new_pos.z = clamp(new_pos.z, min_bound, max_bound)

    camera.pos = new_pos


def handle_mouse_motion(dt):
    global camera
    xrel, yrel = pygame.mouse.get_rel()

    if camera.first_mouse_move:
        camera.first_mouse_move = False
        return

    # Scale by time-based sensitivity
    sensitivity = 5.0 * dt
    xoffset = xrel * sensitivity
    yoffset = -yrel * sensitivity  # invert y

    camera.yaw += xoffset
    camera.pitch += yoffset
    camera.pitch = max(min(camera.pitch, 89.0), -89.0)

    front = glm.vec3(
        math.cos(glm.radians(camera.yaw)) * math.cos(glm.radians(camera.pitch)),
        math.sin(glm.radians(camera.pitch)),
        math.sin(glm.radians(camera.yaw)) * math.cos(glm.radians(camera.pitch))
    )
    camera.front = glm.normalize(front)


def resize_viewport(event):
    global aspect_ratio
    width, height = event.size
    if height == 0:
        return
    aspect_ratio = width / height
    glViewport(0, 0, width, height)


def draw_scene():
    global depth_shader, sp, ground, piano
    # build matrices
    M = glm.mat4(1.0)
    ground_M = glm.mat4(1.0)
    ground_M = glm.translate(ground_M, glm.vec3(0.0, -1.5, 0.0))
    V = glm.lookAt(camera.pos, camera.pos + camera.front, camera.up)
    P = glm.perspective(glm.radians(50.0), aspect_ratio, 1.0, 50.0)

    ortho_size = 10.0
    # coming from above and behind the camera
    light_dir = glm.vec3(-0.5, -1.0, -0.3)
    # place the “light camera” 10 units back along that direction
    light_pos = -light_dir * 10.0  
    lightProj = glm.ortho(-ortho_size, ortho_size, -ortho_size, ortho_size, 1.0, 50.0)
    lightView = glm.lookAt(light_pos, glm.vec3(0.0), glm.vec3(0.0, 1.0, 0.0))
    lightSpaceMatrix = lightProj * lightView
    # render
    piano.render_shadow(depth_shader, lightSpaceMatrix)

    glViewport(0, 0, windowSize.x, windowSize.y)
    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    sp.use()
    # camera
    sp.set_mat4("view", V)
    sp.set_mat4("projection", P)
    # light
    sp.set_vec3("lightPos", light_pos)
    sp.set_vec3("viewPos", camera.pos)
    sp.set_mat4("lightSpaceMatrix", lightSpaceMatrix)
    glActiveTexture(GL_TEXTURE1)
    glBindTexture(GL_TEXTURE_2D, piano.depthTex)
    sp.set_int("shadowMap", 1)
    piano.draw(sp, M)
    ground.draw(sp, ground_M)
    pygame.display.flip()


def main():
    screen = init_pygame_opengl()
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
    sp.delete()
    sys.exit(0)


if __name__ == '__main__':
    main()
