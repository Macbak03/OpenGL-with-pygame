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
uniform float lightRadius;
uniform int blockerSamples;
uniform int pcfSamples;

const float PI = 3.14159265358979323846;

float ShadowCalculation(vec4 posLS) {
    /*vec3 proj = posLS.xyz/posLS.w;  
    proj = proj * 0.5 + 0.5;
    if(proj.z > 1.0) return 0.0;
    // hardware PCF compare: returns 1.0 if lit, 0.0 if in shadow
    float visibility = texture(shadowMap, vec3(proj.xy, proj.z - 0.005));
    // now convert to a classic “shadow factor” (1.0=in shadow, 0.0=lit):
    float shadow = 1.0 - visibility;
    return shadow; */

    //przekształcenie do [0,1]
    vec3 proj = posLS.xyz / posLS.w;
    proj = proj * 0.5 + 0.5;
    if(proj.z > 1.0) 
        return 0.0;

    //obliczamy wielkość jednego texela w mapie głębokości
    vec2 texelSize = 1.0 / vec2(textureSize(shadowMap, 0));

    //parametry
    float bias = 0.005;
    float sum = 0.0;

    //pętla PCF 3×3
    for(int x = -1; x <= 1; ++x) {
        for(int y = -1; y <= 1; ++y) {
            vec2 offset = vec2(float(x), float(y)) * texelSize;
            // texture(sampler2DShadow, vec3(coord.xy, ref_depth)) → 1.0 = lit, 0.0 = in shadow
            sum += texture(shadowMap, vec3(proj.xy + offset, proj.z - bias));
        }
    }
    //uśredniamy widoczność i przeliczamy na klasyczny shadow factor
    float visibility = sum / 9.0;
    return 1.0 - visibility;
}


// PCSS: Percentage-Closer Soft Shadows
float ShadowPCSS(vec4 posLS) {
    // przekształcenie do [0,1]
    vec3 proj = posLS.xyz / posLS.w;
    proj = proj * 0.5 + 0.5;
    if (proj.z > 1.0) return 0.0;

    vec2 texelSize = 1.0 / vec2(textureSize(shadowMap, 0));
    float bias = 0.005;

    // Blocker Search
    float searchRadius = lightRadius * (texelSize.x); 
    float blockerSum = 0.0;
    int   blockerCount = 0;
    for (int i = 0; i < blockerSamples; ++i) {
        float angle = 2.0 * PI * float(i) / float(blockerSamples);
        vec2  offset = vec2(cos(angle), sin(angle)) * searchRadius;
        float sampleDepth = texture(shadowMap, vec3(proj.xy + offset, proj.z - bias));
        // hardware PCF: 1.0 = lit, 0.0 = shadow → blokery to te, gdzie sampleDepth < 1.0
        if (sampleDepth < 1.0) {
            blockerSum += proj.z;
            blockerCount++;
        }
    }
    // brak blokera → pełne oświetlenie
    if (blockerCount == 0) {
        return 0.0;
    }
    float avgBlockerDepth = blockerSum / float(blockerCount);

    // Obliczenie rozmiaru penumbry (w texelach)
    float zDiff = proj.z - avgBlockerDepth;
    float penumbra = (zDiff / avgBlockerDepth) * lightRadius;
    float filterRadius = penumbra * texelSize.x;

    // PCF z dynamicznym promieniem
    float sum = 0.0;
    for (int i = 0; i < pcfSamples; ++i) {
        float angle = 2.0 * PI * float(i) / float(pcfSamples);
        vec2  offset = vec2(cos(angle), sin(angle)) * filterRadius;
        sum += texture(shadowMap, vec3(proj.xy + offset, proj.z - bias));
    }
    float visibility = sum / float(pcfSamples);
    return 1.0 - visibility;
}

void main() {
    vec3 color = texture(textureMap0, texCoords).rgb;
    vec3 n = normalize(normal);

    vec3 l = normalize(lightPos - fragPos);
    float diff = max(dot(n, l), 0.0);

    //float shadow = ShadowCalculation(posLightSpace);
    float shadow = ShadowPCSS(posLightSpace);

    vec3 ambient   = 0.15 * color;

	vec3 v = normalize(viewPos - fragPos);
    vec3 r = reflect(-l, n);
    float spec = pow(max(dot(v, r), 0.0), 32.0);

    vec3 lighting = ambient + (1.0 - shadow) * (diff + spec) * color;
    FragColor = vec4(lighting, 1.0);
}