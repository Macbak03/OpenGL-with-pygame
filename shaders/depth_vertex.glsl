#version 330
layout(location = 0) in vec4 aPos;

uniform mat4 model;
uniform mat4 lightSpaceMatrix;

void main() {
    gl_Position = lightSpaceMatrix * model * aPos;
}