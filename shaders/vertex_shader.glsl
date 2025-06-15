#version 330 core
layout(location = 0) in vec4 aPos;
layout(location = 1) in vec4 aNormal;
layout(location = 2) in vec2 aTexCoords;

out vec4 posLightSpace;
out vec3 normal;
out vec2 texCoords;
out vec3 fragPos;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;
uniform mat4 lightSpaceMatrix;

void main() {
    fragPos = vec3(model * aPos);
    normal = mat3(transpose(inverse(model))) * aNormal.xyz;
    texCoords = aTexCoords;
    posLightSpace = lightSpaceMatrix * model * aPos;
    gl_Position = projection * view * model * aPos;
}