#version 330 core

in vec4 posLightSpace;
in vec3 normal;
in vec2 texCoords;
in vec3 fragPos;

out vec4 FragColor;

uniform sampler2D textureMap0;
uniform sampler2DShadow shadowMap;

uniform vec3 lightPos;
uniform vec3 viewPos;

float ShadowCalculation(vec4 posLS) {
    vec3 proj = posLS.xyz/posLS.w;  
    proj = proj * 0.5 + 0.5;
    if(proj.z > 1.0) return 0.0;
    // hardware PCF compare: returns 1.0 if lit, 0.0 if in shadow
    float visibility = texture(shadowMap, vec3(proj.xy, proj.z - 0.005));
    // now convert to a classic “shadow factor” (1.0=in shadow, 0.0=lit):
    float shadow = 1.0 - visibility;
    return shadow;
}

void main() {
    vec3 color = texture(textureMap0, texCoords).rgb;
    vec3 n = normalize(normal);

    vec3 l = normalize(lightPos - fragPos);
    float diff = max(dot(n, l), 0.0);

    float shadow = ShadowCalculation(posLightSpace);

    vec3 ambient   = 0.15 * color;

	vec3 v = normalize(viewPos - fragPos);
    vec3 r = reflect(-l, n);
    float spec = pow(max(dot(v, r), 0.0), 32.0);

    vec3 lighting = ambient + (1.0 - shadow) * (diff + spec) * color;
    FragColor = vec4(lighting, 1.0);
}