#version 330 core

in vec4 posLightSpace;
in vec3 normal;
in vec2 texCoords;
in vec3 fragPos;

out vec4 FragColor;

uniform sampler2D textureMap0;
uniform sampler2D shadowMap;

uniform vec3 lightPos;
uniform vec3 viewPos;

float ShadowCalculation(vec4 posLS) {
    // z NDC → [0,1]
    vec3 projCoords = posLS.xyz / posLS.w;
    projCoords = projCoords * 0.5 + 0.5;
    // odczytaj głębię z shadow mapy
    float closestDepth = texture(shadowMap, projCoords.xy).r;
    float currentDepth = projCoords.z;
    // proste porównanie
    float bias = 0.005;
    float shadow = currentDepth - bias > closestDepth ? 1.0 : 0.0;
    return shadow;
}

void main() {
    vec3 color = texture(textureMap0, texCoords).rgb;
    vec3 n = normalize(normal);

    vec3 l = normalize(lightPos - fragPos);
    float diff = max(dot(n, l), 0.0);

    float shadow = ShadowCalculation(posLightSpace);

	vec3 v = normalize(viewPos - fragPos);
    vec3 r = reflect(-l, n);
    float spec = pow(max(dot(v, r), 0.0), 32.0);

    vec3 lighting = (1.0 - shadow) * (diff + spec) * color;
    //vec3 lighting = (1.0 - shadow) * diff * color;
    FragColor = vec4(lighting, 1.0);
}