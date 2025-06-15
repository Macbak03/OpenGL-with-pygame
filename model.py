import os
import numpy as np
from PIL import Image
from OpenGL.GL import *
from objLoader import Loader  # assumes the previous loader module
from shaderProgram import ShaderProgram
import glm

# Data structure to hold GPU buffers for a mesh
class MeshEntry:
    def __init__(self):
        self.VAO = glGenVertexArrays(1)
        self.VBO = glGenBuffers(3)
        self.EBO = glGenBuffers(1)
        self.texture_id = 0
        self.index_count = 0

# Main model class
class Model:
    def __init__(self, shadow_size=2048):
        self.loader = Loader()
        self.meshes = [] 
        self.box_min = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.box_max = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.loc_v = 0
        self.loc_n = 1
        self.loc_t = 2
        self.shadow_size = shadow_size
        self.depthFBO = glGenFramebuffers(1)
        self.depthTex = glGenTextures(1)

    def read_texture(self, filename):
        # Load image via Pillow
        img = Image.open(filename).convert("RGBA")
        img_data = np.array(img, dtype=np.uint8)

        tex = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.width, img.height,
                     0, GL_RGBA, GL_UNSIGNED_BYTE, img_data)
        glGenerateMipmap(GL_TEXTURE_2D)
        # Linear filtering
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)
        return tex
    
    def init_shadow_map(self):
        glBindTexture(GL_TEXTURE_2D, self.depthTex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT,
                     self.shadow_size, self.shadow_size, 0,
                     GL_DEPTH_COMPONENT, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        # zapobiega artefaktom poza obszarem:
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        borderColor = (1.0, 1.0, 1.0, 1.0)
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, borderColor)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_COMPARE_REF_TO_TEXTURE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_COMPARE_FUNC, GL_LEQUAL)

        glBindFramebuffer(GL_FRAMEBUFFER, self.depthFBO)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                               GL_TEXTURE_2D, self.depthTex, 0)
        # nie rysujemy koloru w tym FBO
        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def render_shadow(self, shadow_shader: ShaderProgram, light_space_matrix, model_matrix):
        # shadow_shader: ShaderProgram, ma tylko VS + pusty FS
        glViewport(0, 0, self.shadow_size, self.shadow_size)
        glBindFramebuffer(GL_FRAMEBUFFER, self.depthFBO)
        glClear(GL_DEPTH_BUFFER_BIT)

        shadow_shader.use()
        #lUniformMatrix4fv(shadow_shader.u("lightSpaceMatrix"), 1, GL_FALSE, glm.value_ptr(light_space_matrix))
        shadow_shader.set_mat4("lightSpaceMatrix", light_space_matrix)
        shadow_shader.set_mat4("model", model_matrix)

        # rysowanie modelu – tylko depth
        for mesh in self.meshes:
            glBindVertexArray(mesh.VAO)
            glDrawElements(GL_TRIANGLES, mesh.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def init_mesh(self, mesh_entry, vertices, normals, texcoords, indices):
        glBindVertexArray(mesh_entry.VAO)

        # Positions
        glBindBuffer(GL_ARRAY_BUFFER, mesh_entry.VBO[0])
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glEnableVertexAttribArray(self.loc_v)
        glVertexAttribPointer(self.loc_v, 4, GL_FLOAT, GL_FALSE, 0, None)
       

        # Normals
        glBindBuffer(GL_ARRAY_BUFFER, mesh_entry.VBO[1])
        glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
        glEnableVertexAttribArray(self.loc_n)
        glVertexAttribPointer(self.loc_n, 4, GL_FLOAT, GL_FALSE, 0, None)

        # TexCoords
        glBindBuffer(GL_ARRAY_BUFFER, mesh_entry.VBO[2])
        glBufferData(GL_ARRAY_BUFFER, texcoords.nbytes, texcoords, GL_STATIC_DRAW)
        glEnableVertexAttribArray(self.loc_t)
        glVertexAttribPointer(self.loc_t, 2, GL_FLOAT, GL_FALSE, 0, None)

        # Indices
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, mesh_entry.EBO)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        glBindVertexArray(0)
        mesh_entry.index_count = indices.size
        self.meshes.append(mesh_entry)

    def load_model(self, path):
        if not self.loader.load(path):
            print(f"Error loading model {path}")
            return False

        # Flatten and upload each mesh
        for mesh in self.loader.meshes:
            m = MeshEntry()
            # Texture
            #print(f"--------------{mesh.materials}-----------------")
            if mesh.materials and mesh.materials.map_Kd:
                tex_path = os.path.join(os.path.dirname(path), mesh.materials.map_Kd)
                m.texture_id = self.read_texture(tex_path)
            else:
                m.texture_id = 0

            # Build numpy arrays interleaved
            positions = []
            normals = []
            uvs = []
            for v in mesh.vertices:
                positions.extend([v.position.x, v.position.y, v.position.z, 1.0])
                normals.extend([v.normal.x, v.normal.y, v.normal.z, 0.0])
                uvs.extend([v.texcoord.x, v.texcoord.y])

            verts = np.array(positions, dtype=np.float32)
            norms = np.array(normals, dtype=np.float32)
            texc = np.array(uvs, dtype=np.float32)
            inds  = np.array(mesh.indices, dtype=np.uint32)

            self.init_mesh(m, verts, norms, texc, inds)

        self.create_collider()
        return True

    def create_collider(self):
        all_positions = [v.position for mesh in self.loader.meshes for v in mesh.vertices]
        coords = np.array([[p.x, p.y, p.z] for p in all_positions], dtype=np.float32)
        self.box_min = coords.min(axis=0)
        self.box_max = coords.max(axis=0)

    def does_collide(self, camera_pos, padding=1.0):
        x, y, z = camera_pos
        return (self.box_min[0]-padding <= x <= self.box_max[0]+padding and
                self.box_min[1]-padding <= y <= self.box_max[1]+padding and
                self.box_min[2]-padding <= z <= self.box_max[2]+padding)

    def draw(self, shader: ShaderProgram, model_matrix):

        shader.set_mat4("model", model_matrix)

        shader.set_int("textureMap0", 0)
        for mesh in self.meshes:
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, mesh.texture_id)
            glBindVertexArray(mesh.VAO)
            glDrawElements(GL_TRIANGLES, mesh.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
