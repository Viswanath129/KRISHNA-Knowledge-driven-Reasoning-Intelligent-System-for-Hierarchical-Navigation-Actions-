// ================================================================
//  KRISHNA GOD MODE — 100x ANIMATION ENGINE
//  Particle nebula, energy arcs, sacred geometry, task effects,
//  micro-interactions, aurora waves, and divine visual effects
// ================================================================

(function() {
'use strict';

// ====================== CONFIG ======================
const ANIM = {
    PARTICLE_COUNT: 120,
    CONNECTIONS_MAX_DIST: 140,
    SACRED_SYMBOLS: ['☸', 'ॐ', '🔱', '✦', '⚡', '◈', '❖', '⟡', '✧', '☯'],
    COLORS: {
        gold: [255, 215, 0],
        saffron: [255, 153, 51],
        cyan: [34, 211, 238],
        purple: [192, 132, 252],
        green: [74, 222, 128],
        red: [239, 68, 68],
        white: [240, 230, 211]
    }
};

// ====================== PARTICLE NEBULA ======================
const canvas = document.createElement('canvas');
canvas.id = 'nebula-canvas';
canvas.style.cssText = 'position:fixed;inset:0;z-index:0;pointer-events:none;opacity:0.7;';
document.body.insertBefore(canvas, document.body.firstChild);

const ctx = canvas.getContext('2d');
let W, H;
const particles = [];
let mouseX = -1000, mouseY = -1000;
let animFrame;

function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
}
resize();
window.addEventListener('resize', resize);

// Track mouse for interactive particles
document.addEventListener('mousemove', e => { mouseX = e.clientX; mouseY = e.clientY; });
document.addEventListener('mouseleave', () => { mouseX = -1000; mouseY = -1000; });

class Particle {
    constructor() { this.reset(); }
    reset() {
        this.x = Math.random() * W;
        this.y = Math.random() * H;
        this.vx = (Math.random() - 0.5) * 0.4;
        this.vy = (Math.random() - 0.5) * 0.4;
        this.life = Math.random() * 200 + 100;
        this.maxLife = this.life;
        this.radius = Math.random() * 2 + 0.5;
        const colorKeys = Object.keys(ANIM.COLORS);
        const pick = colorKeys[Math.floor(Math.random() * 3)]; // bias gold/saffron/cyan
        this.color = ANIM.COLORS[pick] || ANIM.COLORS.gold;
        this.pulse = Math.random() * Math.PI * 2;
        this.pulseSpeed = 0.02 + Math.random() * 0.03;
    }
    update() {
        // Mouse repulsion
        const dx = this.x - mouseX;
        const dy = this.y - mouseY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 120) {
            const force = (120 - dist) / 120 * 0.8;
            this.vx += (dx / dist) * force;
            this.vy += (dy / dist) * force;
        }
        // Friction
        this.vx *= 0.98;
        this.vy *= 0.98;
        this.x += this.vx;
        this.y += this.vy;
        this.life--;
        this.pulse += this.pulseSpeed;
        // Wrap
        if (this.x < -10) this.x = W + 10;
        if (this.x > W + 10) this.x = -10;
        if (this.y < -10) this.y = H + 10;
        if (this.y > H + 10) this.y = -10;
        if (this.life <= 0) this.reset();
    }
    draw() {
        const alpha = (this.life / this.maxLife) * (0.4 + 0.3 * Math.sin(this.pulse));
        const r = this.radius * (1 + 0.3 * Math.sin(this.pulse));
        ctx.beginPath();
        ctx.arc(this.x, this.y, r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${this.color[0]},${this.color[1]},${this.color[2]},${alpha})`;
        ctx.fill();
        // Glow
        ctx.beginPath();
        ctx.arc(this.x, this.y, r * 3, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${this.color[0]},${this.color[1]},${this.color[2]},${alpha * 0.15})`;
        ctx.fill();
    }
}

// Initialize particles
for (let i = 0; i < ANIM.PARTICLE_COUNT; i++) particles.push(new Particle());
window.particles = particles;

// Draw connections between nearby particles
function drawConnections() {
    for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
            const dx = particles[i].x - particles[j].x;
            const dy = particles[i].y - particles[j].y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < ANIM.CONNECTIONS_MAX_DIST) {
                const alpha = (1 - dist / ANIM.CONNECTIONS_MAX_DIST) * 0.12;
                ctx.beginPath();
                ctx.moveTo(particles[i].x, particles[i].y);
                ctx.lineTo(particles[j].x, particles[j].y);
                ctx.strokeStyle = `rgba(255,215,0,${alpha})`;
                ctx.lineWidth = 0.5;
                ctx.stroke();
            }
        }
    }
}

// ====================== ENERGY ARCS (Lightning) ======================
let arcs = [];
function spawnArc(x1, y1, x2, y2, color, segments) {
    segments = segments || 8;
    const points = [{x: x1, y: y1}];
    for (let i = 1; i < segments; i++) {
        const t = i / segments;
        points.push({
            x: x1 + (x2 - x1) * t + (Math.random() - 0.5) * 60,
            y: y1 + (y2 - y1) * t + (Math.random() - 0.5) * 60
        });
    }
    points.push({x: x2, y: y2});
    arcs.push({ points, color: color || ANIM.COLORS.gold, life: 20, maxLife: 20 });
}

function drawArcs() {
    arcs = arcs.filter(a => a.life > 0);
    arcs.forEach(a => {
        const alpha = a.life / a.maxLife;
        ctx.beginPath();
        ctx.moveTo(a.points[0].x, a.points[0].y);
        for (let i = 1; i < a.points.length; i++) {
            ctx.lineTo(a.points[i].x, a.points[i].y);
        }
        ctx.strokeStyle = `rgba(${a.color[0]},${a.color[1]},${a.color[2]},${alpha * 0.8})`;
        ctx.lineWidth = 2 * alpha;
        ctx.shadowColor = `rgba(${a.color[0]},${a.color[1]},${a.color[2]},${alpha})`;
        ctx.shadowBlur = 15;
        ctx.stroke();
        ctx.shadowBlur = 0;
        a.life--;
    });
}

// ====================== BURST EFFECTS (Task Complete/Fail) ======================
let bursts = [];
function spawnBurst(x, y, color, count) {
    count = count || 30;
    for (let i = 0; i < count; i++) {
        const angle = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.5;
        const speed = 2 + Math.random() * 5;
        bursts.push({
            x, y,
            vx: Math.cos(angle) * speed,
            vy: Math.sin(angle) * speed,
            life: 40 + Math.random() * 20,
            maxLife: 60,
            radius: 1 + Math.random() * 2.5,
            color: color || ANIM.COLORS.gold
        });
    }
}

function drawBursts() {
    bursts = bursts.filter(b => b.life > 0);
    bursts.forEach(b => {
        b.x += b.vx;
        b.y += b.vy;
        b.vx *= 0.96;
        b.vy *= 0.96;
        b.vy += 0.05; // gravity
        b.life--;
        const alpha = b.life / b.maxLife;
        ctx.beginPath();
        ctx.arc(b.x, b.y, b.radius * alpha, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${b.color[0]},${b.color[1]},${b.color[2]},${alpha})`;
        ctx.fill();
    });
}

// ====================== FLOATING SACRED SYMBOLS ======================
let floatingSymbols = [];
function spawnFloatingSymbol(x, y) {
    const sym = ANIM.SACRED_SYMBOLS[Math.floor(Math.random() * ANIM.SACRED_SYMBOLS.length)];
    floatingSymbols.push({
        x, y, symbol: sym,
        vy: -1 - Math.random() * 1.5,
        vx: (Math.random() - 0.5) * 0.8,
        life: 80, maxLife: 80,
        size: 14 + Math.random() * 14,
        rotation: 0,
        rotSpeed: (Math.random() - 0.5) * 0.05
    });
}

function drawFloatingSymbols() {
    floatingSymbols = floatingSymbols.filter(s => s.life > 0);
    floatingSymbols.forEach(s => {
        s.x += s.vx;
        s.y += s.vy;
        s.rotation += s.rotSpeed;
        s.life--;
        const alpha = Math.min(1, s.life / s.maxLife * 2);
        ctx.save();
        ctx.translate(s.x, s.y);
        ctx.rotate(s.rotation);
        ctx.font = `${s.size}px serif`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.globalAlpha = alpha * 0.6;
        ctx.fillText(s.symbol, 0, 0);
        ctx.globalAlpha = 1;
        ctx.restore();
    });
}

// ====================== AURORA WAVES ======================
let auroraPhase = 0;
function drawAurora() {
    auroraPhase += 0.005;
    const gradient = ctx.createLinearGradient(0, H * 0.6, 0, H);
    gradient.addColorStop(0, 'transparent');
    gradient.addColorStop(0.5, `rgba(255,215,0,${0.015 + 0.01 * Math.sin(auroraPhase)})`);
    gradient.addColorStop(1, 'transparent');
    ctx.fillStyle = gradient;
    
    ctx.beginPath();
    ctx.moveTo(0, H);
    for (let x = 0; x <= W; x += 4) {
        const y = H * 0.75 + 
            Math.sin(x * 0.005 + auroraPhase * 2) * 30 +
            Math.sin(x * 0.01 + auroraPhase * 3) * 15 +
            Math.cos(x * 0.003 + auroraPhase) * 20;
        ctx.lineTo(x, y);
    }
    ctx.lineTo(W, H);
    ctx.fill();
    
    // Second wave layer
    const g2 = ctx.createLinearGradient(0, H * 0.5, 0, H);
    g2.addColorStop(0, 'transparent');
    g2.addColorStop(0.5, `rgba(255,153,51,${0.008 + 0.005 * Math.sin(auroraPhase + 1)})`);
    g2.addColorStop(1, 'transparent');
    ctx.fillStyle = g2;
    
    ctx.beginPath();
    ctx.moveTo(0, H);
    for (let x = 0; x <= W; x += 4) {
        const y = H * 0.8 + 
            Math.sin(x * 0.007 + auroraPhase * 1.5) * 25 +
            Math.cos(x * 0.004 + auroraPhase * 2) * 18;
        ctx.lineTo(x, y);
    }
    ctx.lineTo(W, H);
    ctx.fill();
}

// ====================== ENERGY RING PULSES ======================
let rings = [];
function spawnRing(x, y, color) {
    rings.push({ x, y, radius: 5, maxRadius: 100, life: 30, maxLife: 30, color: color || ANIM.COLORS.gold });
}

function drawRings() {
    rings = rings.filter(r => r.life > 0);
    rings.forEach(r => {
        const progress = 1 - r.life / r.maxLife;
        r.radius = 5 + (r.maxRadius - 5) * progress;
        r.life--;
        const alpha = r.life / r.maxLife * 0.5;
        ctx.beginPath();
        ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${r.color[0]},${r.color[1]},${r.color[2]},${alpha})`;
        ctx.lineWidth = 2 * (r.life / r.maxLife);
        ctx.stroke();
    });
}

// ====================== MAIN RENDER LOOP ======================
function renderLoop() {
    ctx.clearRect(0, 0, W, H);
    
    // Aurora background waves
    drawAurora();
    
    // Particles
    particles.forEach(p => { p.update(); p.draw(); });
    drawConnections();
    
    // Effects
    drawArcs();
    drawBursts();
    drawFloatingSymbols();
    drawRings();
    
    animFrame = requestAnimationFrame(renderLoop);
}
renderLoop();

// ====================== CSS ANIMATIONS INJECTION ======================
const styleEl = document.createElement('style');
styleEl.textContent = `
/* ===== 100x ANIMATION SYSTEM ===== */

/* --- Ripple Click Effect --- */
.ripple-effect {
    position: absolute; border-radius: 50%; pointer-events: none;
    background: radial-gradient(circle, rgba(255,215,0,0.4) 0%, transparent 70%);
    animation: rippleExpand 0.6s ease-out forwards;
    z-index: 9999;
}
@keyframes rippleExpand {
    0% { width: 0; height: 0; opacity: 1; }
    100% { width: 200px; height: 200px; opacity: 0; margin-left: -100px; margin-top: -100px; }
}

/* --- Panel 3D Tilt Hover --- */
.panel {
    transition: transform 0.4s cubic-bezier(.25,.8,.25,1), border-color 0.3s, box-shadow 0.4s !important;
    transform-style: preserve-3d;
}
.panel:hover {
    border-color: rgba(255,215,0,0.25) !important;
    box-shadow: 0 8px 32px rgba(255,215,0,0.08), inset 0 0 30px rgba(255,215,0,0.02);
}

/* --- Brand Breathing Glow --- */
.brand-icon {
    animation: brandBreathe 3s ease-in-out infinite, brandRotateHue 8s linear infinite !important;
}
@keyframes brandBreathe {
    0%,100% { box-shadow: 0 0 20px rgba(255,215,0,0.3), 0 0 60px rgba(255,215,0,0.1); }
    50% { box-shadow: 0 0 30px rgba(255,215,0,0.5), 0 0 80px rgba(255,215,0,0.2), 0 0 120px rgba(255,153,51,0.1); }
}
@keyframes brandRotateHue {
    0% { filter: hue-rotate(0deg); }
    100% { filter: hue-rotate(360deg); }
}

/* --- God Badge Shimmer --- */
.god-badge {
    position: relative; overflow: hidden;
    animation: godShift 3s ease infinite !important;
}
.god-badge::after {
    content: ''; position: absolute; top: -50%; left: -100%; width: 60%; height: 200%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
    animation: shimmer 2.5s ease-in-out infinite;
}
@keyframes shimmer { 0%{left:-100%} 50%,100%{left:150%} }

/* --- Gauge Ring Glow Pulse --- */
.g-fill {
    filter: drop-shadow(0 0 6px rgba(255,215,0,0.5));
    animation: gaugeGlow 2s ease-in-out infinite;
}
@keyframes gaugeGlow {
    0%,100% { filter: drop-shadow(0 0 6px rgba(255,215,0,0.4)); }
    50% { filter: drop-shadow(0 0 14px rgba(255,215,0,0.7)) drop-shadow(0 0 30px rgba(255,153,51,0.3)); }
}

/* --- Score Number Pulse --- */
.g-score {
    animation: scorePulse 2s ease-in-out infinite;
}
@keyframes scorePulse {
    0%,100% { transform: scale(1); }
    50% { transform: scale(1.05); text-shadow: 0 0 20px rgba(255,215,0,0.5); }
}

/* --- Stat Value Count Up --- */
.sv {
    transition: all 0.5s cubic-bezier(.25,.8,.25,1);
}
.sv.bumped {
    animation: statBump 0.4s ease;
}
@keyframes statBump {
    0% { transform: scale(1); } 30% { transform: scale(1.4); } 100% { transform: scale(1); }
}

/* --- Button Execute Glow --- */
.btn {
    position: relative; overflow: hidden;
    transition: all 0.3s cubic-bezier(.25,.8,.25,1) !important;
}
.btn::before {
    content: ''; position: absolute; inset: 0;
    background: linear-gradient(45deg, transparent 40%, rgba(255,255,255,0.2) 50%, transparent 60%);
    background-size: 300% 300%; animation: btnShine 3s ease-in-out infinite;
}
@keyframes btnShine { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
.btn:hover {
    transform: translateY(-3px) scale(1.02) !important;
    box-shadow: 0 8px 30px rgba(255,215,0,0.4), 0 0 60px rgba(255,215,0,0.15) !important;
}
.btn:active {
    transform: translateY(0) scale(0.98) !important;
}

/* --- Task Item Slide In --- */
.task-item {
    animation: taskSlideIn 0.4s cubic-bezier(.25,.8,.25,1) !important;
}
@keyframes taskSlideIn {
    0% { opacity: 0; transform: translateX(-20px) scale(0.95); }
    60% { transform: translateX(3px) scale(1.01); }
    100% { opacity: 1; transform: translateX(0) scale(1); }
}

/* --- Task Status Glow --- */
.task-status-icon.done {
    animation: taskDoneGlow 1.5s ease-in-out !important;
}
@keyframes taskDoneGlow {
    0% { box-shadow: 0 0 0 rgba(74,222,128,0); }
    50% { box-shadow: 0 0 15px rgba(74,222,128,0.5), 0 0 30px rgba(74,222,128,0.2); }
    100% { box-shadow: 0 0 0 rgba(74,222,128,0); }
}

.task-status-icon.run {
    animation: spinIcon 1s linear infinite, taskRunPulse 1.5s ease-in-out infinite !important;
}
@keyframes taskRunPulse {
    0%,100% { box-shadow: 0 0 5px rgba(34,211,238,0.3); }
    50% { box-shadow: 0 0 15px rgba(34,211,238,0.6), 0 0 30px rgba(34,211,238,0.2); }
}

.task-status-icon.fail {
    animation: taskFailShake 0.5s ease !important;
}
@keyframes taskFailShake {
    0%,100% { transform: translateX(0); }
    15%,45%,75% { transform: translateX(-3px); }
    30%,60%,90% { transform: translateX(3px); }
}

.task-status-icon.blocked {
    animation: blockedFlash 0.8s ease infinite !important;
}
@keyframes blockedFlash {
    0%,100% { opacity: 1; } 50% { opacity: 0.5; box-shadow: 0 0 10px rgba(255,59,59,0.5); }
}

/* --- Ethics Audit Entry --- */
.ae {
    animation: auditSlide 0.35s cubic-bezier(.25,.8,.25,1) !important;
}
@keyframes auditSlide {
    0% { opacity: 0; transform: translateY(-10px); }
    100% { opacity: 1; transform: translateY(0); }
}
.ae.blocked {
    animation: auditSlide 0.35s ease, blockedPulse 2s ease-in-out infinite !important;
}
@keyframes blockedPulse {
    0%,100% { background: rgba(239,68,68,0.08); }
    50% { background: rgba(239,68,68,0.15); }
}

/* --- Log Entry Cascade --- */
.le {
    animation: logCascade 0.25s cubic-bezier(.25,.8,.25,1) forwards !important;
}
@keyframes logCascade {
    0% { opacity: 0; transform: translateY(6px) translateX(-4px); }
    100% { opacity: 1; transform: translateY(0) translateX(0); }
}

/* --- Terminal Dots Hover --- */
.d { transition: all 0.3s cubic-bezier(.25,.8,.25,1); cursor: pointer; }
.d:hover { transform: scale(1.4); filter: brightness(1.3); box-shadow: 0 0 8px currentColor; }
.d.r:hover { box-shadow: 0 0 8px #ff5f57; }
.d.y:hover { box-shadow: 0 0 8px #febc2e; }
.d.g:hover { box-shadow: 0 0 8px #28c840; }

/* --- Input Focus Aura --- */
textarea:focus {
    box-shadow: 0 0 0 3px rgba(255,215,0,0.1), 0 0 30px rgba(255,215,0,0.05), inset 0 0 20px rgba(255,215,0,0.02) !important;
    animation: inputAura 2s ease-in-out infinite;
}
@keyframes inputAura {
    0%,100% { box-shadow: 0 0 0 3px rgba(255,215,0,0.1), 0 0 30px rgba(255,215,0,0.05); }
    50% { box-shadow: 0 0 0 4px rgba(255,215,0,0.15), 0 0 40px rgba(255,215,0,0.08); }
}

/* --- Action Button Hover --- */
.action-btn {
    transition: all 0.25s cubic-bezier(.25,.8,.25,1) !important;
    position: relative; overflow: hidden;
}
.action-btn:hover {
    transform: translateY(-2px) scale(1.05) !important;
    box-shadow: 0 4px 15px rgba(255,215,0,0.15);
}
.action-btn:active { transform: translateY(0) scale(0.95) !important; }

/* --- Toast Entrance --- */
.toast {
    animation: toastEnter 0.4s cubic-bezier(.25,.8,.25,1) !important;
}
@keyframes toastEnter {
    0% { transform: translateX(100%) scale(0.8) rotate(3deg); opacity: 0; }
    60% { transform: translateX(-5%) scale(1.02) rotate(-0.5deg); }
    100% { transform: translateX(0) scale(1) rotate(0); opacity: 1; }
}

/* --- Scroll Bar Glow --- */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, rgba(255,215,0,0.3), rgba(255,153,51,0.3));
    border-radius: 10px;
}
::-webkit-scrollbar-thumb:hover { background: linear-gradient(180deg, rgba(255,215,0,0.5), rgba(255,153,51,0.5)); }

/* --- Connection Status Glow --- */
.conn-status {
    animation: connFloat 3s ease-in-out infinite;
}
@keyframes connFloat {
    0%,100% { transform: translateY(0); }
    50% { transform: translateY(-3px); }
}

/* --- God Mode Title Glow --- */
.brand-title {
    animation: titleGlow 4s ease-in-out infinite;
}
@keyframes titleGlow {
    0%,100% { filter: drop-shadow(0 0 5px rgba(255,215,0,0.3)); }
    50% { filter: drop-shadow(0 0 15px rgba(255,215,0,0.6)) drop-shadow(0 0 30px rgba(255,153,51,0.3)); }
}

/* --- Panel Header Underline Scan --- */
.ph {
    position: relative; overflow: hidden;
}
.ph::after {
    content: ''; position: absolute; bottom: 0; left: -100%; width: 60%; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,215,0,0.5), transparent);
    animation: scanLine 4s ease-in-out infinite;
}
@keyframes scanLine { 0%{left:-60%} 100%{left:100%} }

/* --- Status Dot Energy --- */
.dot {
    animation: blink 2s infinite, dotEnergy 3s ease-in-out infinite !important;
}
@keyframes dotEnergy {
    0%,100% { box-shadow: 0 0 4px rgba(74,222,128,0.4); }
    50% { box-shadow: 0 0 12px rgba(74,222,128,0.7), 0 0 24px rgba(74,222,128,0.3); }
}

/* --- Tool Count Badge Pulse --- */
.tool-count {
    animation: toolBadge 3s ease-in-out infinite;
}
@keyframes toolBadge {
    0%,100% { box-shadow: 0 0 0 rgba(34,211,238,0); }
    50% { box-shadow: 0 0 10px rgba(34,211,238,0.3), 0 0 20px rgba(34,211,238,0.1); }
}

/* --- Performance Monitor Glow --- */
.perf-monitor.active {
    animation: perfGlow 2s ease-in-out infinite;
}
@keyframes perfGlow {
    0%,100% { border-color: rgba(255,215,0,0.2); }
    50% { border-color: rgba(255,215,0,0.4); box-shadow: 0 0 15px rgba(255,215,0,0.1); }
}

/* --- Dharma Principle Hover --- */
.pi {
    transition: all 0.3s ease; padding-left: 4px; border-left: 2px solid transparent;
}
.pi:hover {
    padding-left: 12px; border-left-color: var(--gold-primary);
    background: rgba(255,215,0,0.03); border-radius: 0 6px 6px 0;
}

/* --- Clear/Export Button Hover --- */
.clr {
    transition: all 0.25s cubic-bezier(.25,.8,.25,1) !important;
}
.clr:hover {
    transform: translateY(-1px);
    box-shadow: 0 3px 10px rgba(255,215,0,0.15);
}

/* --- Textarea Typing Cursor Glow --- */
textarea {
    caret-color: var(--gold-primary);
}

/* --- Meta Label Shimmer --- */
.meta {
    background: linear-gradient(90deg, var(--text-muted) 40%, rgba(255,215,0,0.6) 50%, var(--text-muted) 60%);
    background-size: 200% 100%;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: metaShimmer 3s ease-in-out infinite;
}
@keyframes metaShimmer { 0%{background-position:100% 0} 100%{background-position:-100% 0} }

/* --- Spinner Power Up --- */
.spinner {
    animation: spin 0.6s linear infinite !important;
    border-color: rgba(10,10,10,0.3); border-top-color: #0a0a0a;
    filter: drop-shadow(0 0 3px rgba(255,215,0,0.5));
}

/* --- God Badge Rainbow Border --- */
.god-badge {
    box-shadow: 0 0 10px rgba(255,107,107,0.2), 0 0 20px rgba(255,107,107,0.1);
}

/* --- Empty State Float --- */
.empty-icon {
    animation: emptyFloat 2s ease-in-out infinite;
}
@keyframes emptyFloat {
    0%,100% { transform: translateY(0) scale(1); }
    50% { transform: translateY(-5px) scale(1.1); }
}

/* --- Page Load Fade --- */
.app {
    animation: appFadeIn 1s ease-out;
}
@keyframes appFadeIn {
    0% { opacity: 0; transform: translateY(20px); }
    100% { opacity: 1; transform: translateY(0); }
}

/* --- Header Slide Down --- */
.header {
    animation: headerSlide 0.6s cubic-bezier(.25,.8,.25,1);
}
@keyframes headerSlide {
    0% { opacity: 0; transform: translateY(-30px); }
    100% { opacity: 1; transform: translateY(0); }
}

/* --- Grid Stagger --- */
.grid > *:nth-child(1) { animation: gridStagger 0.8s ease 0.1s both; }
.grid > *:nth-child(2) { animation: gridStagger 0.8s ease 0.2s both; }
@keyframes gridStagger {
    0% { opacity: 0; transform: translateY(30px) scale(0.95); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}

/* --- Keyboard Shortcut Hint glow on focus --- */
.grid .panel:focus-within {
    border-color: rgba(255,215,0,0.3);
    box-shadow: 0 0 30px rgba(255,215,0,0.06);
}
`;
document.head.appendChild(styleEl);

// ====================== CLICK RIPPLE EFFECT ======================
document.addEventListener('click', function(e) {
    const ripple = document.createElement('div');
    ripple.className = 'ripple-effect';
    ripple.style.left = e.clientX + 'px';
    ripple.style.top = e.clientY + 'px';
    document.body.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
});

// ====================== PANEL 3D TILT ON HOVER ======================
document.querySelectorAll('.panel').forEach(panel => {
    panel.addEventListener('mousemove', function(e) {
        const rect = this.getBoundingClientRect();
        const x = (e.clientX - rect.left) / rect.width - 0.5;
        const y = (e.clientY - rect.top) / rect.height - 0.5;
        this.style.transform = `perspective(800px) rotateY(${x * 4}deg) rotateX(${-y * 4}deg)`;
    });
    panel.addEventListener('mouseleave', function() {
        this.style.transform = '';
    });
});

// ====================== TASK EVENT HOOKS ======================
// Observe task container for new task items
const taskObserver = new MutationObserver(muts => {
    muts.forEach(m => {
        m.addedNodes.forEach(node => {
            if (node.classList && node.classList.contains('task-item')) {
                const icon = node.querySelector('.task-status-icon');
                if (!icon) return;
                const rect = node.getBoundingClientRect();
                const cx = rect.left + rect.width / 2;
                const cy = rect.top + rect.height / 2;
                
                if (icon.classList.contains('done')) {
                    // Success burst + ring
                    spawnBurst(cx, cy, ANIM.COLORS.green, 20);
                    spawnRing(cx, cy, ANIM.COLORS.green);
                    spawnFloatingSymbol(cx, cy);
                } else if (icon.classList.contains('fail')) {
                    // Error burst
                    spawnBurst(cx, cy, ANIM.COLORS.red, 15);
                    spawnRing(cx, cy, ANIM.COLORS.red);
                } else if (icon.classList.contains('blocked')) {
                    spawnBurst(cx, cy, ANIM.COLORS.red, 10);
                } else if (icon.classList.contains('run')) {
                    // Running arc
                    spawnArc(cx - 50, cy, cx + 50, cy, ANIM.COLORS.cyan, 6);
                }
            }
        });
    });
});
const tlContainer = document.getElementById('tl-container');
if (tlContainer) taskObserver.observe(tlContainer, { childList: true, subtree: true });

// ====================== FORM SUBMIT EFFECTS ======================
const form = document.getElementById('gf-form');
if (form) {
    form.addEventListener('submit', () => {
        const btn = document.getElementById('btn');
        if (!btn) return;
        const rect = btn.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2;
        // Big energy burst on submit
        spawnBurst(cx, cy, ANIM.COLORS.gold, 40);
        spawnRing(cx, cy, ANIM.COLORS.gold);
        spawnRing(cx, cy, ANIM.COLORS.saffron);
        // Lightning arcs from button
        for (let i = 0; i < 3; i++) {
            const tx = Math.random() * W;
            const ty = Math.random() * H * 0.5;
            setTimeout(() => spawnArc(cx, cy, tx, ty, ANIM.COLORS.gold, 10), i * 100);
        }
        // Floating symbols shower
        for (let i = 0; i < 5; i++) {
            setTimeout(() => spawnFloatingSymbol(
                cx + (Math.random() - 0.5) * 200,
                cy + (Math.random() - 0.5) * 50
            ), i * 80);
        }
    });
}

// ====================== PERIODIC AMBIENT EFFECTS ======================
// Random energy arcs every few seconds
setInterval(() => {
    if (Math.random() < 0.3) {
        const x1 = Math.random() * W;
        const y1 = Math.random() * H;
        const x2 = x1 + (Math.random() - 0.5) * 300;
        const y2 = y1 + (Math.random() - 0.5) * 300;
        spawnArc(x1, y1, x2, y2, ANIM.COLORS[['gold', 'saffron', 'cyan'][Math.floor(Math.random() * 3)]], 6);
    }
}, 3000);

// Random floating symbols
setInterval(() => {
    if (Math.random() < 0.4) {
        spawnFloatingSymbol(
            Math.random() * W,
            H * 0.5 + Math.random() * H * 0.4
        );
    }
}, 4000);

// ====================== GAUGE UPDATE EFFECTS ======================
// Override gauge update to add visual effects
const origUpGauge = window.upGauge;
if (origUpGauge) {
    window.upGauge = function(s) {
        origUpGauge(s);
        const gs = document.getElementById('gs');
        if (gs) {
            gs.style.transform = 'scale(1.15)';
            setTimeout(() => { gs.style.transform = ''; }, 300);
        }
    };
}

// ====================== STAT BUMP ON CHANGE ======================
['sa', 'sw', 'sb'].forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    let lastVal = el.textContent;
    const obs = new MutationObserver(() => {
        if (el.textContent !== lastVal) {
            lastVal = el.textContent;
            el.classList.remove('bumped');
            void el.offsetWidth; // force reflow
            el.classList.add('bumped');
        }
    });
    obs.observe(el, { childList: true, characterData: true, subtree: true });
});

// ====================== SSE LOG FLASH EFFECT ======================
const origSrc = window.EventSource;
// Add flash to log entries as they appear
const logsEl = document.getElementById('logs');
if (logsEl) {
    const logObs = new MutationObserver(muts => {
        muts.forEach(m => {
            m.addedNodes.forEach(node => {
                if (node.nodeType === 1 && node.classList.contains('le')) {
                    // Detect special log types and add glow
                    const text = node.textContent || '';
                    if (text.includes('BLOCKED') || text.includes('🚫')) {
                        node.style.background = 'rgba(239,68,68,0.08)';
                        node.style.borderLeft = '2px solid rgba(239,68,68,0.5)';
                        node.style.paddingLeft = '8px';
                        node.style.borderRadius = '3px';
                    } else if (text.includes('✅')) {
                        node.style.background = 'rgba(74,222,128,0.04)';
                        node.style.borderLeft = '2px solid rgba(74,222,128,0.3)';
                        node.style.paddingLeft = '8px';
                    } else if (text.includes('[GOD MODE]') || text.includes('⚡')) {
                        node.style.background = 'rgba(255,215,0,0.04)';
                        node.style.borderLeft = '2px solid rgba(255,215,0,0.3)';
                        node.style.paddingLeft = '8px';
                    }
                }
            });
        });
    });
    logObs.observe(logsEl, { childList: true });
}

// ====================== KEYBOARD SHORTCUT VISUAL FEEDBACK ======================
document.addEventListener('keydown', e => {
    if (e.ctrlKey && ['m', 'p', 't'].includes(e.key)) {
        // Flash screen border
        document.body.style.boxShadow = '0 0 40px rgba(255,215,0,0.15) inset';
        setTimeout(() => { document.body.style.boxShadow = ''; }, 300);
    }
});

// ====================== WELCOME SEQUENCE ======================
setTimeout(() => {
    // Spawn initial burst at center
    spawnBurst(W / 2, H / 2, ANIM.COLORS.gold, 50);
    spawnRing(W / 2, H / 2, ANIM.COLORS.gold);
    spawnRing(W / 2, H / 2, ANIM.COLORS.saffron);
    // Multiple symbol rain
    for (let i = 0; i < 8; i++) {
        setTimeout(() => spawnFloatingSymbol(
            W * 0.2 + Math.random() * W * 0.6,
            H * 0.3 + Math.random() * H * 0.4
        ), i * 150);
    }
    // Lightning arcs
    for (let i = 0; i < 4; i++) {
        setTimeout(() => spawnArc(
            W / 2, H / 2,
            Math.random() * W, Math.random() * H,
            ANIM.COLORS.gold, 12
        ), i * 200);
    }
}, 800);

// Export for external use
window.ANIM = ANIM;
window.spawnBurst = spawnBurst;
window.spawnArc = spawnArc;
window.spawnRing = spawnRing;
window.spawnFloatingSymbol = spawnFloatingSymbol;

console.log('%c✨ 100x Animation Engine Active', 'color: #FFD700; font-size: 16px; font-weight: bold; text-shadow: 0 0 10px #FFD700');
console.log('%c🌌 Particle Nebula + Energy Arcs + Aurora Waves + Sacred Geometry', 'color: #22d3ee; font-size: 12px');

})();
