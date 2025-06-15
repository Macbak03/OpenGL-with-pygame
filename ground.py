from model import *

class Ground(Model):
    def __init__(self, texure_path):
        super().__init__()
        self.size = 50.0   # half-extent of the ground
        self.ground_positions = np.array([
            -self.size, 0.0, -self.size, 1.0,
            self.size, 0.0, -self.size, 1.0,
            self.size, 0.0,  self.size, 1.0,
            -self.size, 0.0,  self.size, 1.0,
        ], dtype=np.float32)

        self.ground_normals = np.array([
            0.0, 1.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
        ], dtype=np.float32)

        # repeat UVs so the texture tiles across the plane
        self.repeat = 10.0
        self.ground_texcoords = np.array([
            0.0, 0.0,
            self.repeat, 0.0,
            self.repeat, self.repeat,
            0.0, self.repeat,
        ], dtype=np.float32)

        self.ground_indices = np.array([0,1,2,  2,3,0], dtype=np.uint32)

        # Upload into a new MeshEntry
        self.ground = MeshEntry()
        self.ground.texture_id = self.read_texture(texure_path)

        self.init_mesh(self.ground, self.ground_positions, self.ground_normals, self.ground_texcoords, self.ground_indices)