from pygame.locals import *
import glm
from constants import WindowSize, windowSize

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

        self.move_speed = 10.0    # units per second
        self.mouse_sens = 5.0

    def get_view_matrix(self):
        return glm.lookAt(self.pos, self.pos + self.front, self.up)
    
    def process_mouse(self, x, y):
        if self.first_mouse_move:
            self.lastX, self.lastY = x, y
            self.first_mouse_move = False

        xoffset = (x - self.lastX) * self.mouse_sens
        yoffset = (self.lastY - y) * self.mouse_sens
        self.lastX, self.lastY = x, y

        self.yaw   += xoffset
        self.pitch = glm.clamp(self.pitch + yoffset, -89.0, 89.0)

        # recalc front & right
        yaw_rad   = glm.radians(self.yaw)
        pitch_rad = glm.radians(self.pitch)
        front = glm.vec3(
            glm.cos(yaw_rad) * glm.cos(pitch_rad),
            glm.sin(pitch_rad),
            glm.sin(yaw_rad) * glm.cos(pitch_rad)
        )
        self.front = glm.normalize(front)
        self.right = glm.normalize(glm.cross(self.front, self.up))

    def process_keyboard(self, keys, dt):
        velocity = self.move_speed * dt
        if keys[K_w]:
            self.pos += self.front * velocity
        if keys[K_s]:
            self.pos -= self.front * velocity
        if keys[K_a]:
            self.pos -= self.right * velocity
        if keys[K_d]:
            self.pos += self.right * velocity