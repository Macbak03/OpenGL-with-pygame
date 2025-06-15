from pygame.locals import *
import glm
from constants import WindowSize, windowSize
import pygame
from model import Model
from helper import clamp
import math
from shaderProgram import ShaderProgram

class Camera:
    """
    Camera class handles view transformations based on position, orientation, and input.
    """

    def __init__(self, window_size: WindowSize = windowSize):
        # Initial camera vectors
        self.pos = glm.vec3(0.0, 6.0, 15.0)
        self.front = glm.vec3(0.0, 0.0, 1.0)
        self.up = glm.vec3(0.0, 1.0, 0.0)
        self.right = glm.normalize(glm.cross(self.front, self.up))

        # Euler angles
        self.yaw = 270.0
        self.pitch = 0.0

        # Mouse tracking
        self.lastX = window_size.x
        self.lastY = window_size.y
        self.first_mouse_move = True

        self.move_speed = 10.0 
        self.mouse_sens = 5.0

        self.boundary_margin = 20
    
    def process_keyboard_input(self, dt):
        keys = pygame.key.get_pressed()
        camera_speed = self.move_speed * dt

        flat_front = glm.normalize(glm.vec3(self.front.x, 0.0, self.front.z))
        flat_right = glm.normalize(glm.cross(flat_front, self.up))
        displacement = glm.vec3(0.0, 0.0, 0.0)

        if keys[K_w]:
            displacement += flat_front * camera_speed
        if keys[K_s]:
            displacement -= flat_front * camera_speed
        if keys[K_a]:
            displacement -= flat_right * camera_speed
        if keys[K_d]:
            displacement += flat_right * camera_speed
        return displacement

    def check_for_collision(self, model: Model, displacement):
        new_pos = self.pos
        # X-axis collision test
        test_x = new_pos.x + displacement.x
        if not model.does_collide(glm.vec3(test_x, new_pos.y, new_pos.z)):
            new_pos.x = test_x
        # Z-axis collision test
        test_z = new_pos.z + displacement.z
        if not model.does_collide(glm.vec3(new_pos.x, new_pos.y, test_z)):
            new_pos.z = test_z
        # Update the camera poosition - if there was a collision then position is unchanged
        self.pos = new_pos

    def check_if_out_of_bounds(self, max_size):
        new_pos = self.pos
        min_bound = -max_size + self.boundary_margin
        max_bound = max_size - self.boundary_margin
        new_pos.x = clamp(new_pos.x, min_bound, max_bound)
        new_pos.z = clamp(new_pos.z, min_bound, max_bound)
        self.pos = new_pos

    def process_mouse_movement(self, dt):
        xrel, yrel = pygame.mouse.get_rel()

        if self.first_mouse_move:
            self.first_mouse_move = False
            return

        # Scale by time-based sensitivity
        sensitivity = self.mouse_sens * dt
        xoffset = xrel * sensitivity
        yoffset = -yrel * sensitivity  # invert y

        self.yaw += xoffset
        self.pitch += yoffset
        # 
        self.pitch = clamp(self.pitch, -89.0, 89.0)

        front = glm.vec3(
            math.cos(glm.radians(self.yaw)) * math.cos(glm.radians(self.pitch)),
            math.sin(glm.radians(self.pitch)),
            math.sin(glm.radians(self.yaw)) * math.cos(glm.radians(self.pitch))
        )
        self.front = glm.normalize(front)

    def set_up_in_scene(self, shader: ShaderProgram, aspect_ratio):
        view = glm.lookAt(self.pos, self.pos + self.front, self.up)
        projection = glm.perspective(glm.radians(50.0), aspect_ratio, 1.0, 50.0)
        shader.set_mat4("view", view)
        shader.set_mat4("projection", projection)