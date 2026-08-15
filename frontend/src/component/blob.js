import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';

export default function App({
    color = '#0084ff',
    sensitivity = 1.0,
    smoothing = 0.1
}) {
    const mountRef = useRef(null);
    const [isListening, setIsListening] = useState(false);
    const [permissionError, setPermissionError] = useState('');

    const audioContextRef = useRef(null);
    const analyserRef = useRef(null);
    const dataArrayRef = useRef(null);
    const sourceRef = useRef(null);

    const params = {
        timeScale: 0.78,
        rotationSpeedX: 0.002,
        rotationSpeedY: 0.005,
        plasmaScale: 0.1404,
        plasmaBrightness: 1.31,
        voidThreshold: 0.072,
        colorDeep: new THREE.Color(color).clone().multiplyScalar(0.2).getHex(),
        colorMid: new THREE.Color(color).getHex(),
        colorBright: new THREE.Color('#ffffff').lerp(new THREE.Color(color), 0.2).getHex(),
        shellColor: new THREE.Color(color).getHex(),
        shellOpacity: 0.41
    };

    const startMicrophone = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const audioContext = new (window.AudioContext || window.webkitAudioContext)();
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;
            analyser.smoothingTimeConstant = 0.9;
            const source = audioContext.createMediaStreamSource(stream);
            source.connect(analyser);
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            audioContextRef.current = audioContext;
            analyserRef.current = analyser;
            dataArrayRef.current = dataArray;
            sourceRef.current = source;
            if (audioContext.state === 'suspended') {
                setPermissionError('Audio suspended. Click to activate.');
                setIsListening(false);
            } else {
                setIsListening(true);
                setPermissionError('');
            }
        } catch (err) {
            setPermissionError('Microphone access denied. Please allow microphone permissions.');
            setIsListening(false);
        }
    };

    const handleInteraction = async () => {
        if (audioContextRef.current && audioContextRef.current.state === 'suspended') {
            await audioContextRef.current.resume();
            setIsListening(true);
            setPermissionError('');
        } else if (!isListening && !audioContextRef.current) {
            await startMicrophone();
        }
    };

    useEffect(() => { startMicrophone(); }, []);

    useEffect(() => {
        const currentMount = mountRef.current;
        if (!currentMount) return;

        const scene = new THREE.Scene();
        scene.background = null;

        const width = currentMount.offsetWidth;
        const height = currentMount.offsetHeight;
        const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 100);
        camera.position.z = 2.4;

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 0.9;
        currentMount.appendChild(renderer.domElement);

        const controls = new OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.enablePan = false;
        controls.minDistance = 1.5;
        controls.maxDistance = 20;

        const mainGroup = new THREE.Group();
        scene.add(mainGroup);

        const noiseFunctions = `
      vec3 mod289(vec3 x){return x-floor(x*(1.0/289.0))*289.0;}
      vec4 mod289(vec4 x){return x-floor(x*(1.0/289.0))*289.0;}
      vec4 permute(vec4 x){return mod289(((x*34.0)+1.0)*x);}
      vec4 taylorInvSqrt(vec4 r){return 1.79284291400159-0.85373472095314*r;}
      float snoise(vec3 v){
        const vec2 C=vec2(1.0/6.0,1.0/3.0);
        const vec4 D=vec4(0.0,0.5,1.0,2.0);
        vec3 i=floor(v+dot(v,C.yyy));
        vec3 x0=v-i+dot(i,C.xxx);
        vec3 g=step(x0.yzx,x0.xyz);
        vec3 l=1.0-g;
        vec3 i1=min(g.xyz,l.zxy);
        vec3 i2=max(g.xyz,l.zxy);
        vec3 x1=x0-i1+C.xxx;
        vec3 x2=x0-i2+C.yyy;
        vec3 x3=x0-D.yyy;
        i=mod289(i);
        vec4 p=permute(permute(permute(i.z+vec4(0.0,i1.z,i2.z,1.0))+i.y+vec4(0.0,i1.y,i2.y,1.0))+i.x+vec4(0.0,i1.x,i2.x,1.0));
        float n_=0.142857142857;
        vec3 ns=n_*D.wyz-D.xzx;
        vec4 j=p-49.0*floor(p*ns.z*ns.z);
        vec4 x_=floor(j*ns.z);
        vec4 y_=floor(j-7.0*x_);
        vec4 x=x_*ns.x+ns.yyyy;
        vec4 y=y_*ns.x+ns.yyyy;
        vec4 h=1.0-abs(x)-abs(y);
        vec4 b0=vec4(x.xy,y.xy);
        vec4 b1=vec4(x.zw,y.zw);
        vec4 s0=floor(b0)*2.0+1.0;
        vec4 s1=floor(b1)*2.0+1.0;
        vec4 sh=-step(h,vec4(0.0));
        vec4 a0=b0.xzyw+s0.xzyw*sh.xxyy;
        vec4 a1=b1.xzyw+s1.xzyw*sh.zzww;
        vec3 p0=vec3(a0.xy,h.x);
        vec3 p1=vec3(a0.zw,h.y);
        vec3 p2=vec3(a1.xy,h.z);
        vec3 p3=vec3(a1.zw,h.w);
        vec4 norm=taylorInvSqrt(vec4(dot(p0,p0),dot(p1,p1),dot(p2,p2),dot(p3,p3)));
        p0*=norm.x;p1*=norm.y;p2*=norm.z;p3*=norm.w;
        vec4 m=max(0.6-vec4(dot(x0,x0),dot(x1,x1),dot(x2,x2),dot(x3,x3)),0.0);
        m=m*m;
        return 42.0*dot(m*m,vec4(dot(p0,x0),dot(p1,x1),dot(p2,x2),dot(p3,x3)));
      }
      float fbm(vec3 p){
        float total=0.0;float amplitude=0.5;float frequency=1.0;
        for(int i=0;i<3;i++){total+=snoise(p*frequency)*amplitude;amplitude*=0.5;frequency*=2.0;}
        return total;
      }
    `;

        // --- Shell ---
        const pointLight = new THREE.PointLight(params.shellColor, 2.0, 10);
        mainGroup.add(pointLight);

        const shellGeo = new THREE.SphereGeometry(1.0, 64, 64);
        const shellShader = {
            vertexShader: `varying vec3 vNormal;varying vec3 vViewPosition;void main(){vNormal=normalize(normalMatrix*normal);vec4 mvPosition=modelViewMatrix*vec4(position,1.0);vViewPosition=-mvPosition.xyz;gl_Position=projectionMatrix*mvPosition;}`,
            fragmentShader: `varying vec3 vNormal;varying vec3 vViewPosition;uniform vec3 uColor;uniform float uOpacity;void main(){float fresnel=pow(1.0-dot(normalize(vNormal),normalize(vViewPosition)),2.5);gl_FragColor=vec4(uColor,fresnel*uOpacity);}`
        };
        mainGroup.add(new THREE.Mesh(shellGeo, new THREE.ShaderMaterial({ vertexShader: shellShader.vertexShader, fragmentShader: shellShader.fragmentShader, uniforms: { uColor: { value: new THREE.Color(params.colorDeep) }, uOpacity: { value: 0.3 } }, transparent: true, blending: THREE.AdditiveBlending, side: THREE.BackSide, depthWrite: false })));
        mainGroup.add(new THREE.Mesh(shellGeo, new THREE.ShaderMaterial({ vertexShader: shellShader.vertexShader, fragmentShader: shellShader.fragmentShader, uniforms: { uColor: { value: new THREE.Color(params.shellColor) }, uOpacity: { value: params.shellOpacity } }, transparent: true, blending: THREE.AdditiveBlending, side: THREE.FrontSide, depthWrite: false })));

        // --- Plasma Core ---
        const plasmaGeo = new THREE.SphereGeometry(0.998, 128, 128);
        const plasmaMat = new THREE.ShaderMaterial({
            uniforms: { uTime: { value: 0 }, uScale: { value: params.plasmaScale }, uBrightness: { value: params.plasmaBrightness }, uThreshold: { value: params.voidThreshold }, uColorDeep: { value: new THREE.Color(params.colorDeep) }, uColorMid: { value: new THREE.Color(params.colorMid) }, uColorBright: { value: new THREE.Color(params.colorBright) } },
            vertexShader: `varying vec3 vPosition;varying vec3 vNormal;varying vec3 vViewPosition;void main(){vPosition=position;vNormal=normalize(normalMatrix*normal);vec4 mvPosition=modelViewMatrix*vec4(position,1.0);vViewPosition=-mvPosition.xyz;gl_Position=projectionMatrix*mvPosition;}`,
            fragmentShader: `uniform float uTime;uniform float uScale;uniform float uBrightness;uniform float uThreshold;uniform vec3 uColorDeep;uniform vec3 uColorMid;uniform vec3 uColorBright;varying vec3 vPosition;varying vec3 vNormal;varying vec3 vViewPosition;${noiseFunctions}void main(){vec3 p=vPosition*uScale;vec3 q=vec3(fbm(p+vec3(0.0,uTime*0.05,0.0)),fbm(p+vec3(5.2,1.3,2.8)+uTime*0.05),fbm(p+vec3(2.2,8.4,0.5)-uTime*0.02));float density=fbm(p+2.0*q);float t=(density+0.4)*0.8;float alpha=smoothstep(uThreshold,0.7,t);vec3 cWhite=vec3(1.0);vec3 color=mix(uColorDeep,uColorMid,smoothstep(uThreshold,0.5,t));color=mix(color,uColorBright,smoothstep(0.5,0.8,t));color=mix(color,cWhite,smoothstep(0.8,1.0,t));float facing=dot(normalize(vNormal),normalize(vViewPosition));float depthFactor=(facing+1.0)*0.5;float finalAlpha=alpha*(0.02+0.98*depthFactor);gl_FragColor=vec4(color*uBrightness,finalAlpha);}`,
            transparent: true, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, depthWrite: false
        });
        const plasmaMesh = new THREE.Mesh(plasmaGeo, plasmaMat);
        mainGroup.add(plasmaMesh);

        // ============================================================
        // UPGRADED PARTICLE SYSTEM — multiple layers
        // ============================================================

        const baseColor = new THREE.Color(color);
        const brightColor = new THREE.Color('#ffffff').lerp(baseColor, 0.3);
        const accentColor = new THREE.Color(color).offsetHSL(0.15, 0, 0.2);

        // --- Layer 1: Core orbiters (medium count, physics-driven elliptical orbits) ---
        const ORBIT_COUNT = 300;
        const orbitPos = new Float32Array(ORBIT_COUNT * 3);
        const orbitLife = new Float32Array(ORBIT_COUNT);
        const orbitPhase = new Float32Array(ORBIT_COUNT);
        const orbitTilt = new Float32Array(ORBIT_COUNT * 3);
        const orbitSize = new Float32Array(ORBIT_COUNT);
        const orbitSpeed = new Float32Array(ORBIT_COUNT);

        for (let i = 0; i < ORBIT_COUNT; i++) {
            const r = 0.3 + Math.random() * 0.7;
            orbitLife[i] = r;
            orbitPhase[i] = Math.random() * Math.PI * 2;
            orbitSpeed[i] = (0.3 + Math.random() * 0.7) * (Math.random() < 0.5 ? 1 : -1);
            orbitSize[i] = Math.random();

            const tx = Math.random() * 2 - 1;
            const ty = Math.random() * 2 - 1;
            const tz = Math.random() * 2 - 1;
            const tl = Math.sqrt(tx * tx + ty * ty + tz * tz);
            orbitTilt[i * 3] = tx / tl;
            orbitTilt[i * 3 + 1] = ty / tl;
            orbitTilt[i * 3 + 2] = tz / tl;

            orbitPos[i * 3] = r;
            orbitPos[i * 3 + 1] = 0;
            orbitPos[i * 3 + 2] = 0;
        }

        const tiltX = new Float32Array(ORBIT_COUNT);
        const tiltY = new Float32Array(ORBIT_COUNT);
        const tiltZ = new Float32Array(ORBIT_COUNT);
        for (let i = 0; i < ORBIT_COUNT; i++) {
            tiltX[i] = orbitTilt[i * 3];
            tiltY[i] = orbitTilt[i * 3 + 1];
            tiltZ[i] = orbitTilt[i * 3 + 2];
        }

        const orbitGeo = new THREE.BufferGeometry();
        orbitGeo.setAttribute('position', new THREE.BufferAttribute(orbitPos, 3));
        orbitGeo.setAttribute('aSize', new THREE.BufferAttribute(orbitSize, 1));
        orbitGeo.setAttribute('aOrbitR', new THREE.BufferAttribute(orbitLife, 1));
        orbitGeo.setAttribute('aPhase', new THREE.BufferAttribute(orbitPhase, 1));
        orbitGeo.setAttribute('aSpeed', new THREE.BufferAttribute(orbitSpeed, 1));
        orbitGeo.setAttribute('aTiltX', new THREE.BufferAttribute(tiltX, 1));
        orbitGeo.setAttribute('aTiltY', new THREE.BufferAttribute(tiltY, 1));
        orbitGeo.setAttribute('aTiltZ', new THREE.BufferAttribute(tiltZ, 1));

        const orbitMat = new THREE.ShaderMaterial({
            uniforms: {
                uTime: { value: 0 },
                uColor: { value: baseColor.clone() },
                uPulse: { value: 0.0 },
                uAudioIntensity: { value: 0.0 }
            },
            vertexShader: `
        uniform float uTime;
        uniform float uPulse;
        uniform float uAudioIntensity;
        attribute float aSize;
        attribute float aOrbitR;
        attribute float aPhase;
        attribute float aSpeed;
        attribute float aTiltX;
        attribute float aTiltY;
        attribute float aTiltZ;
        varying float vAlpha;
        varying float vGlow;

        vec3 rotateAround(vec3 p, vec3 axis, float angle) {
          float c = cos(angle); float s = sin(angle);
          return p * c + cross(axis, p) * s + axis * dot(axis, p) * (1.0 - c);
        }

        void main() {
          float angle = aPhase + uTime * aSpeed * (1.0 + uAudioIntensity * 2.0);
          float ellipseA = aOrbitR * (1.0 + uPulse * 0.4);
          float ellipseB = aOrbitR * 0.6;

          vec3 localPos = vec3(cos(angle) * ellipseA, sin(angle) * ellipseB, 0.0);
          vec3 axis = normalize(vec3(aTiltX, aTiltY, aTiltZ));
          vec3 worldPos = rotateAround(localPos, axis, uTime * 0.1);

          vec4 mvPosition = modelViewMatrix * vec4(worldPos, 1.0);
          gl_Position = projectionMatrix * mvPosition;

          float baseSize = 6.0 * aSize + 3.0;
          float audioBoost = 1.0 + uAudioIntensity * 3.0;
          gl_PointSize = baseSize * audioBoost * (1.0 / -mvPosition.z);

          vAlpha = 0.6 + 0.4 * sin(uTime * 1.5 + aPhase);
          vGlow = uAudioIntensity;
        }
      `,
            fragmentShader: `
        uniform vec3 uColor;
        varying float vAlpha;
        varying float vGlow;
        void main() {
          vec2 uv = gl_PointCoord - 0.5;
          float dist = length(uv);
          if (dist > 0.5) discard;
          float core = 1.0 - dist * 2.0;
          float glow = pow(core, 1.2 + (1.0 - vGlow) * 1.5);
          float halo = pow(max(0.0, 1.0 - dist * 2.5), 0.4) * 0.3;
          vec3 c = mix(uColor, vec3(1.0), vGlow * 0.5);
          gl_FragColor = vec4(c, (glow + halo) * vAlpha);
        }
      `,
            transparent: true, blending: THREE.AdditiveBlending, depthWrite: false
        });

        const orbitParticles = new THREE.Points(orbitGeo, orbitMat);
        mainGroup.add(orbitParticles);

        // --- Layer 2: Burst particles (ejected on audio peaks, with lifetime + velocity) ---
        const BURST_COUNT = 800;
        const burstPos = new Float32Array(BURST_COUNT * 3);
        const burstVelArr = new Float32Array(BURST_COUNT * 3);
        const burstLifetime = new Float32Array(BURST_COUNT);
        const burstMaxLife = new Float32Array(BURST_COUNT);
        const burstSizeArr = new Float32Array(BURST_COUNT);

        for (let i = 0; i < BURST_COUNT; i++) {
            burstLifetime[i] = -1;
            burstMaxLife[i] = 1;
            burstSizeArr[i] = Math.random();
            burstPos[i * 3] = 0; burstPos[i * 3 + 1] = 0; burstPos[i * 3 + 2] = 0;
        }

        const burstGeo = new THREE.BufferGeometry();
        const burstPosAttr = new THREE.BufferAttribute(burstPos, 3);
        burstPosAttr.setUsage(THREE.DynamicDrawUsage);
        burstGeo.setAttribute('position', burstPosAttr);
        const burstLifeAttr = new THREE.BufferAttribute(burstLifetime, 1);
        burstLifeAttr.setUsage(THREE.DynamicDrawUsage);
        burstGeo.setAttribute('aLife', burstLifeAttr);
        const burstMaxLifeAttr = new THREE.BufferAttribute(burstMaxLife, 1);
        burstGeo.setAttribute('aMaxLife', burstMaxLifeAttr);
        burstGeo.setAttribute('aSize', new THREE.BufferAttribute(burstSizeArr, 1));

        const burstMat = new THREE.ShaderMaterial({
            uniforms: {
                uColor: { value: brightColor.clone() },
                uAccentColor: { value: accentColor.clone() }
            },
            vertexShader: `
        attribute float aLife;
        attribute float aMaxLife;
        attribute float aSize;
        varying float vAlpha;
        varying float vT;
        void main() {
          vT = clamp(aLife / aMaxLife, 0.0, 1.0);
          if (aLife < 0.0) { gl_Position = vec4(9999.0); gl_PointSize = 0.0; vAlpha = 0.0; return; }
          vAlpha = smoothstep(0.0, 0.15, vT) * smoothstep(1.0, 0.6, vT);
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_Position = projectionMatrix * mvPosition;
          float sz = (8.0 * aSize + 4.0) * (1.0 - vT * 0.7);
          gl_PointSize = sz * (1.0 / -mvPosition.z);
        }
      `,
            fragmentShader: `
        uniform vec3 uColor;
        uniform vec3 uAccentColor;
        varying float vAlpha;
        varying float vT;
        void main() {
          if (vAlpha <= 0.0) discard;
          vec2 uv = gl_PointCoord - 0.5;
          float dist = length(uv);
          if (dist > 0.5) discard;
          float core = pow(1.0 - dist * 2.0, 1.5);
          float spark = pow(max(0.0, 0.5 - dist) * 2.0, 0.3) * 0.5;
          vec3 c = mix(uColor, uAccentColor, vT);
          c = mix(c, vec3(1.0), (1.0 - vT) * 0.4);
          gl_FragColor = vec4(c, (core + spark) * vAlpha);
        }
      `,
            transparent: true, blending: THREE.AdditiveBlending, depthWrite: false
        });

        const burstParticles = new THREE.Points(burstGeo, burstMat);
        mainGroup.add(burstParticles);

        // --- Layer 3: Ambient dust (large count, slow drift, noise-field driven) ---
        const DUST_COUNT = 1200;
        const dustPos = new Float32Array(DUST_COUNT * 3);
        const dustSeed = new Float32Array(DUST_COUNT);
        const dustLayer = new Float32Array(DUST_COUNT);

        for (let i = 0; i < DUST_COUNT; i++) {
            const r = 0.2 + Math.random() * 0.85;
            const theta = Math.random() * Math.PI * 2;
            const phi = Math.acos(2 * Math.random() - 1);
            dustPos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
            dustPos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
            dustPos[i * 3 + 2] = r * Math.cos(phi);
            dustSeed[i] = Math.random() * 100;
            dustLayer[i] = Math.floor(Math.random() * 3);
        }

        const dustGeo = new THREE.BufferGeometry();
        dustGeo.setAttribute('position', new THREE.BufferAttribute(dustPos, 3));
        dustGeo.setAttribute('aSeed', new THREE.BufferAttribute(dustSeed, 1));
        dustGeo.setAttribute('aLayer', new THREE.BufferAttribute(dustLayer, 1));

        const dustMat = new THREE.ShaderMaterial({
            uniforms: {
                uTime: { value: 0 },
                uColor: { value: baseColor.clone() },
                uAudioIntensity: { value: 0.0 }
            },
            vertexShader: `
        uniform float uTime;
        uniform float uAudioIntensity;
        attribute float aSeed;
        attribute float aLayer;
        varying float vAlpha;
        varying vec3 vColor;
        uniform vec3 uColor;

        void main() {
          vec3 pos = position;
          float t = uTime * 0.08 + aSeed;

          // Swirling drift
          pos.x += sin(t * 1.1 + pos.y * 3.0) * 0.04;
          pos.y += cos(t * 0.9 + pos.z * 2.5) * 0.04;
          pos.z += sin(t * 1.3 + pos.x * 2.8) * 0.04;

          // Audio breathing
          float breathe = 1.0 + sin(uTime * 2.0 + aSeed) * 0.02 * uAudioIntensity;
          pos *= breathe;

          vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
          gl_Position = projectionMatrix * mvPosition;

          // Tiny dust points
          float sz = 2.0 + aLayer * 1.5;
          gl_PointSize = sz * (1.0 / -mvPosition.z);

          vAlpha = (0.2 + 0.3 * sin(uTime * 0.7 + aSeed)) * (1.0 - length(pos));
          vAlpha = max(0.0, vAlpha);

          // Color varies by layer
          if (aLayer < 0.5) vColor = uColor;
          else if (aLayer < 1.5) vColor = mix(uColor, vec3(1.0), 0.5);
          else vColor = mix(uColor, vec3(0.5, 0.8, 1.0), 0.3);
        }
      `,
            fragmentShader: `
        varying float vAlpha;
        varying vec3 vColor;
        void main() {
          vec2 uv = gl_PointCoord - 0.5;
          float dist = length(uv);
          if (dist > 0.5) discard;
          float soft = 1.0 - dist * 2.0;
          gl_FragColor = vec4(vColor, soft * vAlpha);
        }
      `,
            transparent: true, blending: THREE.AdditiveBlending, depthWrite: false
        });

        const dustParticles = new THREE.Points(dustGeo, dustMat);
        mainGroup.add(dustParticles);

        // --- Layer 4: Ring sparks — corona ring around equator ---
        const RING_COUNT = 150;
        const ringPos = new Float32Array(RING_COUNT * 3);
        const ringAngle = new Float32Array(RING_COUNT);
        const ringR = new Float32Array(RING_COUNT);
        const ringPhaseArr = new Float32Array(RING_COUNT);

        for (let i = 0; i < RING_COUNT; i++) {
            ringAngle[i] = (i / RING_COUNT) * Math.PI * 2;
            ringR[i] = 0.95 + Math.random() * 0.1;
            ringPhaseArr[i] = Math.random() * Math.PI * 2;
            ringPos[i * 3] = Math.cos(ringAngle[i]) * ringR[i];
            ringPos[i * 3 + 1] = 0;
            ringPos[i * 3 + 2] = Math.sin(ringAngle[i]) * ringR[i];
        }

        const ringGeo = new THREE.BufferGeometry();
        ringGeo.setAttribute('position', new THREE.BufferAttribute(ringPos, 3));
        ringGeo.setAttribute('aAngle', new THREE.BufferAttribute(ringAngle, 1));
        ringGeo.setAttribute('aR', new THREE.BufferAttribute(ringR, 1));
        ringGeo.setAttribute('aPhase', new THREE.BufferAttribute(ringPhaseArr, 1));

        const ringMat = new THREE.ShaderMaterial({
            uniforms: {
                uTime: { value: 0 },
                uColor: { value: new THREE.Color(color).offsetHSL(0, 0, 0.3) },
                uAudioIntensity: { value: 0.0 }
            },
            vertexShader: `
        uniform float uTime;
        uniform float uAudioIntensity;
        attribute float aAngle;
        attribute float aR;
        attribute float aPhase;
        varying float vAlpha;
        void main() {
          float a = aAngle + uTime * 0.3;
          float pulse = 1.0 + uAudioIntensity * 0.3 * sin(aPhase + uTime * 5.0);
          float r = aR * pulse;
          float yWave = sin(aAngle * 8.0 + uTime * 3.0) * 0.04 * (1.0 + uAudioIntensity);
          vec3 pos = vec3(cos(a) * r, yWave, sin(a) * r);
          vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
          gl_Position = projectionMatrix * mvPosition;
          float sz = (4.0 + uAudioIntensity * 8.0);
          gl_PointSize = sz * (1.0 / -mvPosition.z);
          vAlpha = 0.5 + 0.5 * sin(aPhase + uTime * 4.0);
          vAlpha *= (0.4 + uAudioIntensity * 0.8);
        }
      `,
            fragmentShader: `
        uniform vec3 uColor;
        varying float vAlpha;
        void main() {
          vec2 uv = gl_PointCoord - 0.5;
          float dist = length(uv);
          if (dist > 0.5) discard;
          float g = pow(1.0 - dist * 2.0, 2.0);
          gl_FragColor = vec4(uColor + 0.5, g * vAlpha);
        }
      `,
            transparent: true, blending: THREE.AdditiveBlending, depthWrite: false
        });

        const ringParticles = new THREE.Points(ringGeo, ringMat);
        mainGroup.add(ringParticles);

        // --- Burst emitter state ---
        let burstHead = 0;
        let lastAudioIntensity = 0;
        let burstCooldown = 0;

        function emitBurst(count, intensity) {
            for (let i = 0; i < count; i++) {
                const idx = burstHead % BURST_COUNT;
                burstHead++;

                const theta = Math.random() * Math.PI * 2;
                const phi = Math.acos(2 * Math.random() - 1);
                const r = 0.9 + Math.random() * 0.15;

                burstPos[idx * 3] = r * Math.sin(phi) * Math.cos(theta);
                burstPos[idx * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
                burstPos[idx * 3 + 2] = r * Math.cos(phi);

                const speed = 0.008 + Math.random() * 0.015 * intensity;
                burstVelArr[idx * 3] = Math.sin(phi) * Math.cos(theta) * speed;
                burstVelArr[idx * 3 + 1] = Math.sin(phi) * Math.sin(theta) * speed;
                burstVelArr[idx * 3 + 2] = Math.cos(phi) * speed;

                burstLifetime[idx] = 0.001;
                burstMaxLife[idx] = 0.5 + Math.random() * 0.8;
            }

            burstPosAttr.needsUpdate = true;
            burstLifeAttr.needsUpdate = true;
        }

        const clock = new THREE.Clock();
        let animationFrameId;
        let currentScale = 1.0;

        function animate() {
            animationFrameId = requestAnimationFrame(animate);
            const t = clock.getElapsedTime();

            let targetScale = 0.8;
            let targetBrightness = params.plasmaBrightness;
            let audioIntensity = 0.0;

            if (analyserRef.current && dataArrayRef.current) {
                analyserRef.current.getByteFrequencyData(dataArrayRef.current);
                let sum = 0;
                const activeBins = Math.floor(dataArrayRef.current.length / 2);
                for (let i = 0; i < activeBins; i++) sum += dataArrayRef.current[i];
                const avgVolume = sum / activeBins;
                audioIntensity = Math.min(avgVolume / (45.0 / sensitivity), 1.5);
                targetScale = 0.8 + audioIntensity * 0.35;
                targetBrightness = params.plasmaBrightness + audioIntensity * 1.2;
            }

            currentScale += (targetScale - currentScale) * smoothing;
            mainGroup.scale.set(currentScale, currentScale, currentScale);

            // Burst emission on audio transients
            burstCooldown -= 0.016;
            const intensityDelta = audioIntensity - lastAudioIntensity;
            if (intensityDelta > 0.15 && burstCooldown <= 0) {
                const burstCount = Math.floor(intensityDelta * 40 + 5);
                emitBurst(Math.min(burstCount, 30), audioIntensity);
                burstCooldown = 0.05;
            }
            lastAudioIntensity = audioIntensity * 0.9 + lastAudioIntensity * 0.1;

            // Update burst particle positions (CPU physics)
            let burstChanged = false;
            for (let i = 0; i < BURST_COUNT; i++) {
                if (burstLifetime[i] > 0) {
                    burstLifetime[i] += 0.016;
                    const drag = 0.97;
                    burstPos[i * 3] += burstVelArr[i * 3];
                    burstPos[i * 3 + 1] += burstVelArr[i * 3 + 1];
                    burstPos[i * 3 + 2] += burstVelArr[i * 3 + 2];
                    burstVelArr[i * 3] *= drag;
                    burstVelArr[i * 3 + 1] *= drag;
                    burstVelArr[i * 3 + 2] *= drag;
                    if (burstLifetime[i] >= burstMaxLife[i]) burstLifetime[i] = -1;
                    burstChanged = true;
                }
            }
            if (burstChanged) {
                burstPosAttr.needsUpdate = true;
                burstLifeAttr.needsUpdate = true;
            }

            // Update uniforms
            const elapsed = clock.getElapsedTime();
            plasmaMat.uniforms.uTime.value = elapsed * params.timeScale;
            plasmaMat.uniforms.uBrightness.value += (targetBrightness - plasmaMat.uniforms.uBrightness.value) * smoothing;

            orbitMat.uniforms.uTime.value = elapsed;
            orbitMat.uniforms.uPulse.value += (currentScale - 1.0 - orbitMat.uniforms.uPulse.value) * 0.1;
            orbitMat.uniforms.uAudioIntensity.value += (audioIntensity - orbitMat.uniforms.uAudioIntensity.value) * 0.15;

            dustMat.uniforms.uTime.value = elapsed;
            dustMat.uniforms.uAudioIntensity.value += (audioIntensity - dustMat.uniforms.uAudioIntensity.value) * 0.1;

            ringMat.uniforms.uTime.value = elapsed;
            ringMat.uniforms.uAudioIntensity.value += (audioIntensity - ringMat.uniforms.uAudioIntensity.value) * 0.2;

            // Rotation
            plasmaMesh.rotation.y = elapsed * 0.08;
            mainGroup.rotation.x += params.rotationSpeedX;
            mainGroup.rotation.y += params.rotationSpeedY;

            controls.update();
            renderer.render(scene, camera);
        }

        const handleResize = () => {
            const w = currentMount.offsetWidth;
            const h = currentMount.offsetHeight;
            camera.aspect = w / h;
            camera.updateProjectionMatrix();
            renderer.setSize(w, h);
        };
        window.addEventListener('resize', handleResize);
        animate();

        return () => {
            window.removeEventListener('resize', handleResize);
            cancelAnimationFrame(animationFrameId);
            currentMount.removeChild(renderer.domElement);
            renderer.dispose();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [color, sensitivity, smoothing]);

    return (
        <div
            onClick={handleInteraction}
            style={{
                position: 'relative',
                width: '100%',
                height: '100%',
                backgroundColor: 'transparent',
                overflow: 'hidden',
                cursor: !isListening ? 'pointer' : 'default'
            }}
        >
            <div ref={mountRef} style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }} />
            {!isListening && permissionError && (
                <div style={{
                    position: 'absolute', top: '20px', left: 0, width: '100%',
                    textAlign: 'center', color: '#ff4444', fontFamily: 'sans-serif', zIndex: 10
                }}>
                    {permissionError} — Click to try again
                </div>
            )}
        </div>
    );
}