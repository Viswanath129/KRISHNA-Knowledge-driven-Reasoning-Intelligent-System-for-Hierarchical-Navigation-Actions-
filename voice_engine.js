// ================================================================
//  KRISHNA GOD MODE — REAL-TIME GEMINI LIVE VOICE ENGINE
//  Google Gemini Multimodal Live API WS Client & Downsampler
//  Swirling 2D Canvas Orb Visualizer, Auto-interruption, and Jarvis Mode
// ================================================================

(function() {
'use strict';

// ====================== CONFIG ======================
const VOICE = {
    LANG: 'en-US',
    SPEAK_RESPONSES: true,   // TTS/speaker feedback volume toggle
    VOICE_NAME: 'Puck',
    BEEP_ON_LISTEN: true,
};

// ====================== STATE ======================
let ws = null;
let jarvisMode = false;  // always-on listening
let currentVoiceState = 'idle'; // 'idle', 'connecting', 'listening', 'processing', 'speaking', 'error'
let audioCtx = null;
let audioStream = null;
let audioInputNode = null;
let scriptNode = null;
let speakerAnalyser = null;
let speakerGain = null;
let activeSourceNodes = [];
let nextPlayTime = 0;

// Expose real-time volume amplitudes to the window for other UI items
window.voiceAmplitudes = { mic: 0, speaker: 0 };

// ====================== AUDIO BEEP FEEDBACK ======================
function playBeep(freq, duration, type) {
    try {
        if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.frequency.value = freq || 800;
        osc.type = type || 'sine';
        gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + (duration || 0.15));
        osc.start();
        osc.stop(audioCtx.currentTime + (duration || 0.15));
    } catch (e) {
        console.warn("Could not play feedback beep:", e);
    }
}

function playListenBeep() {
    playBeep(880, 0.1, 'sine');
    setTimeout(() => playBeep(1100, 0.12, 'sine'), 120);
}

function playSuccessBeep() {
    playBeep(523, 0.1, 'sine');
    setTimeout(() => playBeep(659, 0.1, 'sine'), 100);
    setTimeout(() => playBeep(784, 0.15, 'sine'), 200);
}

function playErrorBeep() {
    playBeep(300, 0.15, 'sawtooth');
    setTimeout(() => playBeep(200, 0.2, 'sawtooth'), 150);
}

// ====================== HELPER UTILITIES ======================
// Downsample float32 buffer to target rate (e.g. 16000Hz)
function downsampleBuffer(buffer, inputSampleRate, outputSampleRate) {
    if (inputSampleRate === outputSampleRate) {
        return buffer;
    }
    const sampleRateRatio = inputSampleRate / outputSampleRate;
    const newLength = Math.round(buffer.length / sampleRateRatio);
    const result = new Float32Array(newLength);
    let offsetResult = 0;
    let offsetBuffer = 0;
    while (offsetResult < result.length) {
        const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
        let accum = 0;
        let count = 0;
        for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
            accum += buffer[i];
            count++;
        }
        result[offsetResult] = count > 0 ? accum / count : 0;
        offsetResult++;
        offsetBuffer = nextOffsetBuffer;
    }
    return result;
}

// Convert Float32Array to 16-bit Signed PCM
function convertFloat32ToInt16(buffer) {
    const l = buffer.length;
    const buf = new Int16Array(l);
    for (let i = 0; i < l; i++) {
        let s = Math.max(-1, Math.min(1, buffer[i]));
        buf[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return buf;
}

// Convert ArrayBuffer to Base64 String
function base64ArrayBuffer(arrayBuffer) {
    let binary = '';
    const bytes = new Uint8Array(arrayBuffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return window.btoa(binary);
}

// Convert Base64 String to ArrayBuffer
function base64ToArrayBuffer(base64) {
    const binaryString = window.atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
}

// ====================== WEB AUDIO SUBSYSTEM ======================
async function initAudio() {
    if (!audioCtx) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        audioCtx = new AudioCtx();
    }
    if (audioCtx.state === 'suspended') {
        await audioCtx.resume();
    }
    
    if (!speakerAnalyser) {
        speakerAnalyser = audioCtx.createAnalyser();
        speakerAnalyser.fftSize = 256;
        
        speakerGain = audioCtx.createGain();
        speakerGain.gain.value = VOICE.SPEAK_RESPONSES ? 1.0 : 0.0;
        
        speakerAnalyser.connect(speakerGain);
        speakerGain.connect(audioCtx.destination);
    }
}

// Start capturing and streaming mic audio
async function startMicCapture() {
    audioStream = await navigator.mediaDevices.getUserMedia({
        audio: {
            channelCount: 1,
            sampleRate: 16000,
            echoCancellation: true,
            noiseSuppression: true
        }
    });
    
    audioInputNode = audioCtx.createMediaStreamSource(audioStream);
    scriptNode = audioCtx.createScriptProcessor(4096, 1, 1);
    
    scriptNode.onaudioprocess = (e) => {
        // Stop capturing if not in listening mode
        if (currentVoiceState !== 'listening') {
            return;
        }
        
        const inputData = e.inputBuffer.getChannelData(0);
        
        // Calculate microphone RMS (volume)
        let sum = 0;
        for (let i = 0; i < inputData.length; i++) {
            sum += inputData[i] * inputData[i];
        }
        const rms = Math.sqrt(sum / inputData.length);
        window.voiceAmplitudes.mic = window.voiceAmplitudes.mic * 0.7 + rms * 0.3;
        
        // Auto-interruption logic:
        // If Gemini is speaking (active playbacks exist) and user starts talking (RMS > threshold)
        if (activeSourceNodes.length > 0 && rms > 0.05) {
            interruptGemini();
            return;
        }
        
        // Stream chunk to backend WebSocket
        const downsampled = downsampleBuffer(inputData, audioCtx.sampleRate, 16000);
        const pcm16 = convertFloat32ToInt16(downsampled);
        const base64 = base64ArrayBuffer(pcm16.buffer);
        
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                realtimeInput: {
                    mediaChunks: [
                        {
                            mimeType: "audio/pcm",
                            data: base64
                        }
                    ]
                }
            }));
        }
    };
    
    audioInputNode.connect(scriptNode);
    scriptNode.connect(audioCtx.destination);
}

// Queue and schedule PCM 24kHz audio chunk for seamless playback
function playPCM24kChunk(arrayBuffer) {
    if (!audioCtx) return;
    
    const int16Data = new Int16Array(arrayBuffer);
    const float32Data = new Float32Array(int16Data.length);
    let sum = 0;
    
    for (let i = 0; i < int16Data.length; i++) {
        const sample = int16Data[i] / 32768.0;
        float32Data[i] = sample;
        sum += sample * sample;
    }
    
    // Calculate speaker amplitude
    const rms = Math.sqrt(sum / int16Data.length);
    window.voiceAmplitudes.speaker = window.voiceAmplitudes.speaker * 0.5 + rms * 0.5;
    
    const audioBuffer = audioCtx.createBuffer(1, float32Data.length, 24000);
    audioBuffer.copyToChannel(float32Data, 0);
    
    const sourceNode = audioCtx.createBufferSource();
    sourceNode.buffer = audioBuffer;
    
    sourceNode.connect(speakerAnalyser);
    
    const currentTime = audioCtx.currentTime;
    if (nextPlayTime < currentTime) {
        nextPlayTime = currentTime + 0.03; // small buffer to avoid glitching
    }
    
    sourceNode.start(nextPlayTime);
    nextPlayTime += audioBuffer.duration;
    
    activeSourceNodes.push(sourceNode);
    sourceNode.onended = () => {
        const idx = activeSourceNodes.indexOf(sourceNode);
        if (idx > -1) activeSourceNodes.splice(idx, 1);
    };
}

// Interrupt Gemini response
function interruptGemini() {
    console.log("[Voice Engine] User interrupted Gemini.");
    activeSourceNodes.forEach(node => {
        try { node.stop(); } catch(e) {}
    });
    activeSourceNodes = [];
    nextPlayTime = 0;
    window.voiceAmplitudes.speaker = 0;
    
    if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "client_interrupted" }));
    }
    
    updateMicUI('listening');
    updateTranscriptUI('⚡ Interrupted...', true);
}

// Check if all queued speaking chunks have finished playing
function checkPlaybackFinished() {
    const checkInterval = setInterval(() => {
        if (activeSourceNodes.length === 0) {
            clearInterval(checkInterval);
            if (currentVoiceState === 'speaking') {
                updateMicUI('listening');
                updateTranscriptUI('🎙️ Listening...', false);
                window.voiceAmplitudes.speaker = 0;
            }
        }
    }, 100);
}

// Release all audio nodes and mic streams
function cleanupAudioAndState() {
    if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
        audioStream = null;
    }
    if (audioInputNode) {
        try { audioInputNode.disconnect(); } catch(e) {}
        audioInputNode = null;
    }
    if (scriptNode) {
        try { scriptNode.disconnect(); } catch(e) {}
        scriptNode = null;
    }
    activeSourceNodes.forEach(node => {
        try { node.stop(); } catch(e) {}
    });
    activeSourceNodes = [];
    nextPlayTime = 0;
    
    window.voiceAmplitudes.mic = 0;
    window.voiceAmplitudes.speaker = 0;
}

// ====================== WEBSOCKET CONNECTION MANAGER ======================
async function startVoiceSession() {
    if (currentVoiceState !== 'idle' && currentVoiceState !== 'error') {
        stopVoiceSession();
        return;
    }
    
    updateMicUI('connecting');
    updateTranscriptUI('Establishing live secure connection...', true);
    
    try {
        await initAudio();
        
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/live`;
        
        ws = new WebSocket(wsUrl);
        
        ws.onopen = async () => {
            console.log("[Voice Engine] Connected to local FastAPI WebSocket Proxy.");
            playListenBeep();
            updateMicUI('listening');
            updateTranscriptUI('🎙️ Speak naturally. I am listening...', false);
            
            try {
                await startMicCapture();
            } catch (micErr) {
                console.error("[Voice Engine] Mic capture failed:", micErr);
                updateTranscriptUI('Microphone access denied. Grant permissions.', false);
                updateMicUI('error');
                playErrorBeep();
                ws.close();
            }
        };
        
        ws.onmessage = async (event) => {
            try {
                const msg = JSON.parse(event.data);
                
                if (msg.type === 'audio') {
                    updateMicUI('speaking');
                    const arrayBuffer = base64ToArrayBuffer(msg.data);
                    playPCM24kChunk(arrayBuffer);
                } 
                else if (msg.type === 'caption') {
                    updateTranscriptUI(msg.text, false);
                } 
                else if (msg.type === 'turn_complete') {
                    checkPlaybackFinished();
                } 
                else if (msg.type === 'interrupted') {
                    activeSourceNodes.forEach(node => {
                        try { node.stop(); } catch(e) {}
                    });
                    activeSourceNodes = [];
                    nextPlayTime = 0;
                    window.voiceAmplitudes.speaker = 0;
                    updateMicUI('listening');
                    updateTranscriptUI('🎙️ Listening...', false);
                }
            } catch (e) {
                console.error("[Voice Engine] Error handling socket message:", e);
            }
        };
        
        ws.onerror = (err) => {
            console.error("[Voice Engine] WebSocket error:", err);
            updateTranscriptUI('Voice service connection error.', false);
            updateMicUI('error');
            playErrorBeep();
        };
        
        ws.onclose = (event) => {
            console.log("[Voice Engine] Connection closed:", event.code, event.reason);
            cleanupAudioAndState();
            
            if (currentVoiceState === 'error') return;
            
            updateMicUI('idle');
            
            if (jarvisMode) {
                updateTranscriptUI('Reconnecting to Jarvis Voice Link...', true);
                setTimeout(() => {
                    if (jarvisMode) startVoiceSession();
                }, 2000);
            } else {
                updateTranscriptUI('Voice session closed.', false);
            }
        };
        
    } catch (err) {
        console.error("[Voice Engine] Live session error:", err);
        updateTranscriptUI('Failed to establish voice session.', false);
        updateMicUI('error');
        playErrorBeep();
    }
}

function stopVoiceSession() {
    jarvisMode = false;
    const jvBtn = document.getElementById('jarvis-toggle');
    if (jvBtn) jvBtn.classList.remove('active');
    
    if (ws) {
        try { ws.close(); } catch(e) {}
        ws = null;
    }
    cleanupAudioAndState();
    updateMicUI('idle');
    updateTranscriptUI('Voice control session stopped.', false);
}

function toggleVoice() {
    if (currentVoiceState === 'idle' || currentVoiceState === 'error') {
        startVoiceSession();
    } else {
        stopVoiceSession();
    }
}

function toggleJarvisMode() {
    jarvisMode = !jarvisMode;
    const btn = document.getElementById('jarvis-toggle');
    if (btn) btn.classList.toggle('active', jarvisMode);
    
    if (jarvisMode) {
        if (window.showToast) showToast('🤖 Jarvis Always-On Mode Active', 'success', 3000);
        if (currentVoiceState === 'idle' || currentVoiceState === 'error') {
            startVoiceSession();
        }
    } else {
        if (window.showToast) showToast('🤖 Jarvis Mode Deactivated', 'info', 2000);
        stopVoiceSession();
    }
}

// ====================== UI UPDATES ======================
function updateMicUI(state) {
    currentVoiceState = state;
    const micBtn = document.getElementById('voice-mic-btn');
    const micStatus = document.getElementById('voice-status');
    const voicePanel = document.getElementById('voice-panel');
    
    if (!micBtn) return;
    
    micBtn.className = 'voice-mic ' + state;
    
    const statusText = {
        idle: 'Click to speak',
        connecting: '⚡ Connecting...',
        listening: '🎤 Speak Now',
        processing: '⚡ Thinking...',
        speaking: '✨ Gemini Speaking...',
        error: '❌ Connection Error'
    };
    
    if (micStatus) {
        micStatus.textContent = statusText[state] || 'Click to speak';
    }
    
    if (voicePanel) {
        voicePanel.classList.toggle('active', state !== 'idle');
    }
}

function updateTranscriptUI(text, isInterim) {
    const el = document.getElementById('voice-transcript');
    if (!el) return;
    el.textContent = text;
    el.className = 'voice-transcript' + (isInterim ? ' interim' : ' final');
}

// ====================== CANVAS ORB VISUALIZER ======================
function startCanvasOrbAnimation() {
    const canvas = document.getElementById('voice-visualizer-canvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    let angle = 0;
    
    // Cache the wave bars for ultra-performance
    let waveBars = null;
    
    function drawOrb() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        angle += 0.03;
        
        const state = currentVoiceState;
        let glowRadius = 38;
        let colorStart = 'rgba(255, 215, 0, 0.25)';
        let colorEnd = 'rgba(255, 153, 51, 0)';
        
        if (state === 'listening') {
            const amp = window.voiceAmplitudes.mic * 150;
            glowRadius = 38 + amp;
            colorStart = `rgba(239, 68, 68, ${0.4 + window.voiceAmplitudes.mic * 2})`;
            colorEnd = 'rgba(239, 68, 68, 0)';
        } else if (state === 'speaking') {
            const amp = window.voiceAmplitudes.speaker * 120;
            glowRadius = 38 + amp;
            colorStart = `rgba(34, 211, 238, ${0.4 + window.voiceAmplitudes.speaker * 2})`;
            colorEnd = 'rgba(34, 211, 238, 0)';
        } else if (state === 'connecting' || state === 'processing') {
            glowRadius = 38 + Math.sin(Date.now() * 0.01) * 4;
            colorStart = 'rgba(192, 132, 252, 0.4)';
            colorEnd = 'rgba(192, 132, 252, 0)';
        } else {
            glowRadius = 38 + Math.sin(Date.now() * 0.003) * 3;
            colorStart = 'rgba(255, 215, 0, 0.2)';
            colorEnd = 'rgba(255, 153, 51, 0)';
        }
        
        // 1. Radial Glow
        const grad = ctx.createRadialGradient(cx, cy, 8, cx, cy, glowRadius);
        grad.addColorStop(0, colorStart);
        grad.addColorStop(1, colorEnd);
        ctx.beginPath();
        ctx.arc(cx, cy, glowRadius, 0, Math.PI * 2);
        ctx.fillStyle = grad;
        ctx.fill();
        
        // 2. Waveforms / Swirling Energy Lines
        if (state === 'listening') {
            // Neon red audio waves
            ctx.strokeStyle = '#ef4444';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            for (let a = 0; a < Math.PI * 2; a += 0.1) {
                const amp = window.voiceAmplitudes.mic * 30 * Math.sin(a * 4 + angle * 2);
                const r = 26 + amp;
                const x = cx + Math.cos(a) * r;
                const y = cy + Math.sin(a) * r;
                if (a === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.stroke();
        } else if (state === 'speaking') {
            // Swirling electric cyan energy field
            ctx.strokeStyle = '#22d3ee';
            ctx.lineWidth = 2;
            ctx.beginPath();
            for (let a = 0; a < Math.PI * 2; a += 0.05) {
                const noise = (Math.sin(a * 6 + angle * 3) + Math.cos(a * 3 - angle)) * 3;
                const r = 28 + window.voiceAmplitudes.speaker * 40 + noise;
                const x = cx + Math.cos(a) * r;
                const y = cy + Math.sin(a) * r;
                if (a === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.stroke();
            
            // Secondary orbiting line
            ctx.strokeStyle = 'rgba(34, 211, 238, 0.4)';
            ctx.lineWidth = 1;
            ctx.beginPath();
            for (let a = 0; a < Math.PI * 2; a += 0.05) {
                const r = 22 + window.voiceAmplitudes.speaker * 20 + Math.sin(a * 3 - angle * 2) * 2;
                const x = cx + Math.cos(a) * r;
                const y = cy + Math.sin(a) * r;
                if (a === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.stroke();
        } else if (state === 'connecting' || state === 'processing') {
            // Purple & Gold loading orbital rings
            ctx.strokeStyle = '#c084fc';
            ctx.lineWidth = 2.5;
            ctx.beginPath();
            ctx.arc(cx, cy, 26, angle, angle + Math.PI * 1.5);
            ctx.stroke();
            
            ctx.strokeStyle = '#ffd700';
            ctx.lineWidth = 1;
            ctx.beginPath();
            ctx.arc(cx, cy, 21, -angle, -angle + Math.PI);
            ctx.stroke();
        } else {
            // Idle breathing gold border
            ctx.strokeStyle = '#ffd700';
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.arc(cx, cy, 25 + Math.sin(angle * 0.5) * 1.5, 0, Math.PI * 2);
            ctx.stroke();
        }
        
        // 3. Central Core Sphere
        ctx.beginPath();
        ctx.arc(cx, cy, 10, 0, Math.PI * 2);
        if (state === 'listening') ctx.fillStyle = '#ef4444';
        else if (state === 'speaking') ctx.fillStyle = '#22d3ee';
        else if (state === 'connecting' || state === 'processing') ctx.fillStyle = '#c084fc';
        else ctx.fillStyle = '#ffd700';
        ctx.fill();
        
        // Highlights on the core sphere
        ctx.beginPath();
        ctx.arc(cx - 3, cy - 3, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = '#ffffff';
        ctx.fill();
        
        // 4. Dynamic Soundwave Frequency Bars
        if (!waveBars) {
            waveBars = document.querySelectorAll('.voice-wave-bar');
        }
        if (waveBars && waveBars.length > 0) {
            const currentAmp = state === 'listening' ? window.voiceAmplitudes.mic : (state === 'speaking' ? window.voiceAmplitudes.speaker : 0);
            waveBars.forEach((bar, idx) => {
                const baseHeight = 6;
                const factor = Math.sin(angle * 1.5 + idx * 0.7) * 0.5 + 0.5;
                const height = baseHeight + (currentAmp * 45 * factor);
                bar.style.height = `${height}px`;
                
                // Colors match state theme
                if (state === 'listening') {
                    bar.style.background = '#ef4444';
                } else if (state === 'speaking') {
                    bar.style.background = '#22d3ee';
                } else if (state === 'connecting' || state === 'processing') {
                    bar.style.background = '#c084fc';
                } else {
                    bar.style.background = 'var(--gold-primary)';
                }
            });
        }
        
        requestAnimationFrame(drawOrb);
    }
    
    drawOrb();
}

// ====================== INJECT UI ELEMENTS ======================
function injectVoiceUI() {
    const voiceStyle = document.createElement('style');
    voiceStyle.textContent = `
    /* ===== NEW GEMINI MULTIMODAL LIVE VOICE UI ===== */
    
    .voice-mic {
        position: fixed; bottom: 30px; right: 30px; z-index: 10000;
        width: 60px; height: 60px; border-radius: 50%;
        background: linear-gradient(135deg, var(--gold-primary), var(--saffron));
        border: none; cursor: pointer;
        display: flex; align-items: center; justify-content: center;
        font-size: 24px; color: #0a0a0a;
        box-shadow: 0 4px 25px rgba(255,215,0,0.3);
        transition: all 0.3s cubic-bezier(.25,.8,.25,1);
        animation: micFloat 3s ease-in-out infinite;
    }
    .voice-mic:hover {
        transform: scale(1.1) translateY(-3px);
        box-shadow: 0 8px 35px rgba(255,215,0,0.5);
    }
    .voice-mic:active { transform: scale(0.95); }
    @keyframes micFloat {
        0%,100% { transform: translateY(0); }
        50% { transform: translateY(-4px); }
    }
    
    .voice-mic.listening {
        background: linear-gradient(135deg, #ef4444, #dc2626);
        box-shadow: 0 0 30px rgba(239,68,68,0.5), 0 0 60px rgba(239,68,68,0.2);
        animation: micPulseRed 1s ease-in-out infinite;
    }
    @keyframes micPulseRed {
        0%,100% { box-shadow: 0 0 30px rgba(239,68,68,0.5); transform: scale(1); }
        50% { box-shadow: 0 0 50px rgba(239,68,68,0.7), 0 0 80px rgba(239,68,68,0.3); transform: scale(1.05); }
    }
    
    .voice-mic.connecting, .voice-mic.processing {
        background: linear-gradient(135deg, #c084fc, #8b5cf6);
        box-shadow: 0 0 30px rgba(192,132,252,0.5);
        animation: micSpin 1.5s linear infinite;
    }
    @keyframes micSpin {
        0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); }
    }
    
    .voice-mic.speaking {
        background: linear-gradient(135deg, #22d3ee, #06b6d4);
        box-shadow: 0 0 30px rgba(34,211,238,0.5), 0 0 60px rgba(34,211,238,0.2);
        animation: micPulseCyan 1.5s ease-in-out infinite;
    }
    @keyframes micPulseCyan {
        0%,100% { box-shadow: 0 0 20px rgba(34,211,238,0.4); }
        50% { box-shadow: 0 0 45px rgba(34,211,238,0.7); }
    }
    
    .voice-mic.error {
        background: linear-gradient(135deg, #f97316, #ea580c);
    }
    
    .voice-panel {
        position: fixed; bottom: 100px; right: 20px; z-index: 10000;
        width: 320px;
        background: rgba(12,15,28,0.95); backdrop-filter: blur(20px);
        border: 1px solid rgba(255,215,0,0.15); border-radius: 16px;
        padding: 20px 16px 16px 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.6);
        transform: translateY(20px) scale(0.9); opacity: 0;
        pointer-events: none;
        transition: all 0.35s cubic-bezier(.25,.8,.25,1);
    }
    .voice-panel.active {
        transform: translateY(0) scale(1); opacity: 1; pointer-events: auto;
    }
    
    .voice-orb {
        width: 48px; height: 48px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 20px;
    }
    
    .voice-waves {
        display: flex; align-items: center; justify-content: center;
        gap: 3px; height: 24px; margin-bottom: 12px;
    }
    .voice-wave-bar {
        width: 3px; border-radius: 3px;
        background: var(--gold-primary);
        height: 6px;
        transition: height 0.15s;
    }
    .voice-panel.active .voice-wave-bar {
        animation: waveBar 0.8s ease-in-out infinite;
    }
    .voice-wave-bar:nth-child(1) { animation-delay: 0s; }
    .voice-wave-bar:nth-child(2) { animation-delay: 0.1s; }
    .voice-wave-bar:nth-child(3) { animation-delay: 0.2s; }
    .voice-wave-bar:nth-child(4) { animation-delay: 0.3s; }
    .voice-wave-bar:nth-child(5) { animation-delay: 0.4s; }
    .voice-wave-bar:nth-child(6) { animation-delay: 0.3s; }
    .voice-wave-bar:nth-child(7) { animation-delay: 0.2s; }
    .voice-wave-bar:nth-child(8) { animation-delay: 0.1s; }
    .voice-wave-bar:nth-child(9) { animation-delay: 0s; }
    @keyframes waveBar {
        0%,100% { height: 6px; opacity: 0.4; }
        50% { height: 22px; opacity: 1; }
    }
    
    .voice-transcript {
        text-align: center;
        font-size: 0.82rem; font-weight: 500;
        color: var(--text-primary);
        min-height: 44px; max-height: 80px; overflow-y: auto;
        margin-bottom: 12px;
        line-height: 1.4;
        transition: all 0.2s;
    }
    .voice-transcript.interim {
        color: var(--text-secondary); font-style: italic;
    }
    .voice-transcript.final {
        color: var(--gold-primary); font-weight: 600;
    }
    
    .voice-status {
        text-align: center; font-size: 0.6rem;
        color: var(--text-muted); letter-spacing: 1.5px;
        text-transform: uppercase; margin-bottom: 12px;
        font-weight: 700;
    }
    
    .voice-controls {
        display: flex; gap: 8px; justify-content: center;
    }
    .voice-ctrl-btn {
        font-size: 0.65rem; padding: 6px 12px;
        background: rgba(255,215,0,0.08); color: var(--text-primary);
        border: 1px solid rgba(255,215,0,0.15); border-radius: 6px;
        cursor: pointer; font-family: 'Inter', sans-serif; font-weight: 700;
        transition: all 0.2s;
    }
    .voice-ctrl-btn:hover {
        background: rgba(255,215,0,0.15); border-color: var(--gold-primary);
        transform: translateY(-1px);
    }
    .voice-ctrl-btn.active {
        background: rgba(74,222,128,0.15); border-color: rgba(74,222,128,0.4);
        color: #4ade80;
    }
    .voice-ctrl-btn.danger {
        background: rgba(239,68,68,0.08); border-color: rgba(239,68,68,0.2);
    }
    .voice-ctrl-btn.danger:hover {
        background: rgba(239,68,68,0.15); border-color: rgba(239,68,68,0.4);
    }
    
    .voice-mic-label {
        position: fixed; bottom: 18px; right: 22px; z-index: 10001;
        font-size: 0.5rem; color: var(--text-muted);
        letter-spacing: 1px; text-transform: uppercase;
        text-align: center; width: 68px;
        pointer-events: none;
        font-weight: 800;
    }
    
    @media(max-width:900px) {
        .voice-mic { width: 50px; height: 50px; font-size: 20px; bottom: 20px; right: 20px; }
        .voice-panel { width: 280px; right: 10px; bottom: 80px; }
        .voice-mic-label { bottom: 8px; right: 14px; }
    }
    `;
    document.head.appendChild(voiceStyle);
    
    const voicePanel = document.createElement('div');
    voicePanel.className = 'voice-panel';
    voicePanel.id = 'voice-panel';
    voicePanel.innerHTML = `
        <div class="voice-orb-wrap" style="position: relative; width: 120px; height: 120px; margin: 0 auto 8px auto; display: flex; align-items: center; justify-content: center;">
            <canvas id="voice-visualizer-canvas" width="120" height="120" style="position: absolute; top: 0; left: 0; pointer-events: none;"></canvas>
            <div class="voice-orb" id="voice-orb" style="position: relative; z-index: 1; border: none; background: transparent; box-shadow: none;">🎤</div>
        </div>
        <div class="voice-waves">
            <div class="voice-wave-bar"></div>
            <div class="voice-wave-bar"></div>
            <div class="voice-wave-bar"></div>
            <div class="voice-wave-bar"></div>
            <div class="voice-wave-bar"></div>
            <div class="voice-wave-bar"></div>
            <div class="voice-wave-bar"></div>
            <div class="voice-wave-bar"></div>
            <div class="voice-wave-bar"></div>
        </div>
        <div class="voice-transcript" id="voice-transcript">Connecting voice link...</div>
        <div class="voice-status" id="voice-status">Connecting...</div>
        <div class="voice-controls">
            <button class="voice-ctrl-btn" id="jarvis-toggle" title="Toggle Jarvis (always-on) mode">🤖 Jarvis</button>
            <button class="voice-ctrl-btn" id="voice-mute-btn" title="Mute/unmute voice responses">🔊 Voice</button>
            <button class="voice-ctrl-btn danger" id="voice-stop-btn" title="Stop listening">⏹ Stop</button>
        </div>
    `;
    document.body.appendChild(voicePanel);
    
    // Floating mic button
    const micBtn = document.createElement('button');
    micBtn.className = 'voice-mic idle';
    micBtn.id = 'voice-mic-btn';
    micBtn.innerHTML = '🎤';
    micBtn.title = 'Voice Call Session (Ctrl+Shift+V)';
    micBtn.addEventListener('click', toggleVoice);
    document.body.appendChild(micBtn);
    
    // Mic label
    const micLabel = document.createElement('div');
    micLabel.className = 'voice-mic-label';
    micLabel.textContent = 'VOICE';
    document.body.appendChild(micLabel);
    
    // Bind buttons
    document.getElementById('jarvis-toggle').addEventListener('click', toggleJarvisMode);
    
    document.getElementById('voice-mute-btn').addEventListener('click', () => {
        VOICE.SPEAK_RESPONSES = !VOICE.SPEAK_RESPONSES;
        if (speakerGain) {
            speakerGain.gain.value = VOICE.SPEAK_RESPONSES ? 1.0 : 0.0;
        }
        const btn = document.getElementById('voice-mute-btn');
        btn.textContent = VOICE.SPEAK_RESPONSES ? '🔊 Voice' : '🔇 Muted';
        btn.classList.toggle('active', !VOICE.SPEAK_RESPONSES);
        if (window.showToast) showToast(VOICE.SPEAK_RESPONSES ? '🔊 Voice Feedback Enabled' : '🔇 Voice Feedback Muted', 'info', 2000);
    });
    
    document.getElementById('voice-stop-btn').addEventListener('click', stopVoiceSession);
    
    // Start drawing canvas visualizer orb
    startCanvasOrbAnimation();
    
    // Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'TEXTAREA' || e.target.tagName === 'INPUT') return;
        
        // Ctrl+Shift+V for voice toggle
        if (e.ctrlKey && e.shiftKey && e.key === 'V') {
            e.preventDefault();
            toggleVoice();
        }
        // Ctrl+J for Jarvis mode
        if (e.ctrlKey && e.key === 'j') {
            e.preventDefault();
            toggleJarvisMode();
        }
    });
}

// ====================== EXPORT ENGINE ======================
window.VoiceEngine = {
    start: startVoiceSession,
    stop: stopVoiceSession,
    toggle: toggleVoice,
    toggleJarvis: toggleJarvisMode,
    config: VOICE
};

// Inject UI on readiness
if (document.body) {
    injectVoiceUI();
} else {
    document.addEventListener('DOMContentLoaded', injectVoiceUI);
}

console.log('%c🎤 Gemini Multimodal Live Voice Engine Loaded', 'color: #22d3ee; font-size: 16px; font-weight: bold; text-shadow: 0 0 10px #22d3ee');
console.log('%c  Local secure WebSocket Proxy + 16kHz PCM downsampler + Swirling Canvas Orb Visualizer', 'color: #ffd700; font-size: 11px');

})();
