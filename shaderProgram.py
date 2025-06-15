import sys
import glfw
from OpenGL.GL import *
import glm

class ShaderProgram:
    def __init__(self, vertex_shader_file, geometry_shader_file=None, fragment_shader_file=None):
        # Compile shaders
        self.vertex_shader = self._load_shader(GL_VERTEX_SHADER, vertex_shader_file)
        if geometry_shader_file:
            self.geometry_shader = self._load_shader(GL_GEOMETRY_SHADER, geometry_shader_file)
        else:
            self.geometry_shader = None
        self.fragment_shader = self._load_shader(GL_FRAGMENT_SHADER, fragment_shader_file)

        # Create program and attach shaders
        self.program = glCreateProgram()
        glAttachShader(self.program, self.vertex_shader)
        if self.geometry_shader:
            glAttachShader(self.program, self.geometry_shader)
        glAttachShader(self.program, self.fragment_shader)
        glLinkProgram(self.program)
        # Check link status
        status = glGetProgramiv(self.program, GL_LINK_STATUS)
        if status != GL_TRUE:
            log = glGetProgramInfoLog(self.program)
            print(f"Shader link error:\n{log.decode('utf-8')}", file=sys.stderr)
            sys.exit(1)
        # Optionally detach shaders
        glDetachShader(self.program, self.vertex_shader)
        if self.geometry_shader:
            glDetachShader(self.program, self.geometry_shader)
        glDetachShader(self.program, self.fragment_shader)

    def _read_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                return f.read()
        except Exception as e:
            print(f"Failed to read shader file '{file_path}': {e}", file=sys.stderr)
            sys.exit(1)

    def _load_shader(self, shader_type, file_path):
        # Read source
        source = self._read_file(file_path)
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)
        # Check compile status
        status = glGetShaderiv(shader, GL_COMPILE_STATUS)
        if status != GL_TRUE:
            log = glGetShaderInfoLog(shader)
            print(f"Shader compile error in {file_path}:\n{log.decode('utf-8')}", file=sys.stderr)
            sys.exit(1)
        return shader

    def use(self):
        glUseProgram(self.program)

    def u(self, name):
        return glGetUniformLocation(self.program, name)

    def a(self, name):
        return glGetAttribLocation(self.program, name)
    
    def set_int(self, name: str, value: int):
        loc = self.u(name)
        if loc == -1:
            print(f"Warning: uniform '{name}' not found")
        glUniform1i(loc, value)

    def set_mat4(self, name: str, mat):
        """Upload a 4×4 matrix (numpy array dtype=float32, shape=(4,4))."""
        loc = self.u(name)
        if loc == -1:
            print(f"Warning: uniform '{name}' not found")
        # GL_FALSE means “don’t transpose” — your array should already be column-major
        glUniformMatrix4fv(loc, 1, GL_FALSE, glm.value_ptr(mat))

    def set_vec3(self, name: str, vec):
        """Upload a vec3 (sequence or numpy array of length 3)."""
        loc = self.u(name)
        if loc == -1:
            print(f"Warning: uniform '{name}' not found")
        # If vec is a numpy array, you can also do glUniform3fv(loc, 1, vec)
        glUniform3f(loc, vec[0], vec[1], vec[2])

    def delete(self):
        if glIsProgram(self.program):
            glDeleteProgram(self.program)
        # Shaders can be deleted if needed
        if glIsShader(self.vertex_shader):
            glDeleteShader(self.vertex_shader)
        if self.geometry_shader and glIsShader(self.geometry_shader):
            glDeleteShader(self.geometry_shader)
        if glIsShader(self.fragment_shader):
            glDeleteShader(self.fragment_shader)