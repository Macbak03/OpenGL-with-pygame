from OpenGL.GL import *
from shaderProgram import ShaderProgram
from model import Model

class ShadowMap:
    def __init__(self, size=2048):
        self.size = size
        self.depthFBO = glGenFramebuffers(1)
        self.depthTex = glGenTextures(1)
        self._init_buffers()

    def _init_buffers(self):
        glBindTexture(GL_TEXTURE_2D, self.depthTex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT,
                     self.size, self.size, 0,
                     GL_DEPTH_COMPONENT, GL_FLOAT, None)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_BORDER)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_BORDER)
        borderColor = (1.0, 1.0, 1.0, 1.0)
        glTexParameterfv(GL_TEXTURE_2D, GL_TEXTURE_BORDER_COLOR, borderColor)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_COMPARE_MODE, GL_COMPARE_REF_TO_TEXTURE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_COMPARE_FUNC, GL_LEQUAL)
        glBindFramebuffer(GL_FRAMEBUFFER, self.depthFBO)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT,
                               GL_TEXTURE_2D, self.depthTex, 0)
        glDrawBuffer(GL_NONE)
        glReadBuffer(GL_NONE)
        assert glCheckFramebufferStatus(GL_FRAMEBUFFER) == GL_FRAMEBUFFER_COMPLETE
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def render(self, model: Model, shader: ShaderProgram,
               light_space_matrix, model_matrix):
        glViewport(0, 0, self.size, self.size)
        glBindFramebuffer(GL_FRAMEBUFFER, self.depthFBO)
        glClear(GL_DEPTH_BUFFER_BIT)

        shader.use()
        shader.set_mat4("lightSpaceMatrix", light_space_matrix)
        shader.set_mat4("model", model_matrix)
        for mesh in model.meshes:
            glBindVertexArray(mesh.VAO)
            glDrawElements(GL_TRIANGLES, mesh.index_count, GL_UNSIGNED_INT, None)
        glBindVertexArray(0)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def bind_depth_texture(self, unit=1):
        glActiveTexture(GL_TEXTURE0 + unit)
        glBindTexture(GL_TEXTURE_2D, self.depthTex)

    def set_up_in_scene(self, shader):
        shader.set_int("shadowMap", 1)
        self.bind_depth_texture(1)