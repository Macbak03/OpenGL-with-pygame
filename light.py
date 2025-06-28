from OpenGL.GL import *
import glm
from shaderProgram import ShaderProgram
import pygame
from helper import clamp

class Light:
    def __init__(self, distance = 10.0):
        self.distance = distance
        self.ortho_size = 10.0
        # coming from above and behind the camera
        self.light_dir = glm.vec3(0.0, -1.0, 0.0)
        # place the “light camera” 10 units back along that direction
        self.light_pos = -self.light_dir * 10.0 
        self.pitch = glm.degrees(glm.asin(self.light_dir.y))              # elevation
        self.yaw = glm.degrees(glm.atan(self.light_dir.x, self.light_dir.z))      # azimuth

        self.min_pitch = -89.0
        self.max_pitch =  -40.0

        self.rotate_speed = 400.0

        self.update_from_angles()

    def update_from_angles(self):
        # clamp pitch
        self.pitch = clamp(self.pitch, self.min_pitch, self.max_pitch)

        # spherical → cartesian
        r_pitch = glm.radians(self.pitch)
        r_yaw   = glm.radians(self.yaw)
        x = glm.cos(r_pitch) * glm.sin(r_yaw)
        y = glm.sin(r_pitch)
        z = glm.cos(r_pitch) * glm.cos(r_yaw)
        self.light_dir = glm.normalize(glm.vec3(x, y, z))

        # place the virtual “light camera” at distance along −dir
        self.light_pos = -self.light_dir * self.distance

    def process_keyboard_input(self, dt):
        keys = pygame.key.get_pressed()
        speed = self.rotate_speed * dt

        # left/right: change azimuth
        if keys[pygame.K_LEFT]:
            self.yaw -= speed
        if keys[pygame.K_RIGHT]:
            self.yaw += speed

        # up/down: change elevation
        if keys[pygame.K_UP]:
            self.pitch += speed
        if keys[pygame.K_DOWN]:
            self.pitch -= speed

        # now recompute dir & pos
        self.update_from_angles()

    def calculate_light_space_matrix(self):
        ortho = self.ortho_size
        lightProj = glm.ortho(-ortho, ortho, -ortho, ortho, 1.0, 50.0)
        lightView = glm.lookAt(self.light_pos, glm.vec3(0.0), glm.vec3(0.0, 1.0, 0.0))
        light_space_matrix = lightProj * lightView
        return light_space_matrix
    
    def set_up_in_scene(self, shader: ShaderProgram, camera_pos, light_space_matrix):
        shader.set_vec3("lightPos", self.light_pos)
        shader.set_vec3("viewPos", camera_pos)
        shader.set_mat4("lightSpaceMatrix", light_space_matrix)
        shader.set_float("lightRadius", 64.0)      # np. 1.0 jednostki
        shader.set_int("blockerSamples", 32)    # 16 próbek na blocker search
        shader.set_int("pcfSamples", 32)    # 32 próbek końcowego PCF