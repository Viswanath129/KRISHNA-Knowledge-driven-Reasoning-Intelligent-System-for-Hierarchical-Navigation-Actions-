// ================================================================
//  KRISHNA GOD MODE - PERFORMANCE UPGRADE MODULE
//  100x Better Performance + All Buttons Functional
// ================================================================

// --- PERFORMANCE OPTIMIZATIONS & PERSISTENCE ---
const defaultPerf = {
    MAX_LOG_LINES: 500,
    MAX_TASKS_SHOWN: 50,
    USE_RAF: true,
    THROTTLE_TASK_POLL: 500,
    THROTTLE_GOD_POLL: 1000,
    THROTTLE_ETHICS_POLL: 2500,
    MAX_PARTICLES: 300,
    PARTICLE_QUALITY: 'high',
    AUTO_SCROLL: true,
    TURBO_MODE: false,
    PAUSED: false,
    MONITOR_ACTIVE: false
};

const savedPerf = JSON.parse(localStorage.getItem('krishnaGodModeSettings') || '{}');
const PERF = { ...defaultPerf, ...savedPerf };

function savePerfSettings() {
    localStorage.setItem('krishnaGodModeSettings', JSON.stringify({
        AUTO_SCROLL: PERF.AUTO_SCROLL,
        TURBO_MODE: PERF.TURBO_MODE,
        PAUSED: PERF.PAUSED,
        MONITOR_ACTIVE: PERF.MONITOR_ACTIVE
    }));
}

// --- TOAST NOTIFICATION SYSTEM ---
let _toastCount = 0; // Limit concurrent toasts
function showToast(message, type = 'info', duration = 3000) {
    if (_toastCount >= 5) return; // Drop excess during flood
    _toastCount++;
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
    };

    // Escape message to prevent XSS via crafted log or reaction text
    const safeMsg = String(message).replace(/</g, '&lt;').replace(/>/g, '&gt;');
    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || 'ℹ️'}</div>
        <div class="toast-content">
            <div class="toast-title">${type.toUpperCase()}</div>
            <div class="toast-msg">${safeMsg}</div>
        </div>
        <div class="toast-close">×</div>
    `;
    
    document.body.appendChild(toast);
    
    const close = () => {
        toast.style.animation = 'toastSlide 0.3s ease-out reverse';
        setTimeout(() => { toast.remove(); _toastCount = Math.max(0, _toastCount - 1); }, 300);
    };
    
    toast.querySelector('.toast-close').onclick = close;
    if (duration > 0) setTimeout(close, duration);
    
    return toast;
}

// --- CONNECTION STATUS MANAGER ---
const ConnectionManager = {
    status: 'connected',
    reconnectAttempts: 0,
    maxAttempts: 5,
    
    updateStatus(status) {
        this.status = status;
        const connStatus = document.getElementById('conn-status');
        const connDot = document.getElementById('conn-dot');
        const connText = document.getElementById('conn-text');
        
        if (!connStatus) return;
        
        connStatus.style.display = 'flex';
        connDot.className = 'conn-dot ' + status;
        
        const texts = {
            connected: 'Connected',
            disconnected: 'Disconnected',
            reconnecting: 'Reconnecting...'
        };
        connText.textContent = texts[status] || 'Unknown';
        
        if (status === 'disconnected') {
            showToast('Connection lost. Retrying...', 'warning', 0);
        } else if (status === 'connected' && this.reconnectAttempts > 0) {
            showToast('Connection restored!', 'success');
            this.reconnectAttempts = 0;
        }
    },
    
    async testConnection() {
        try {
            const response = await fetch('/api/godmode', { method: 'GET', signal: AbortSignal.timeout(3000) });
            if (response.ok) {
                this.updateStatus('connected');
                return true;
            }
        } catch (e) {
            this.updateStatus('disconnected');
            return false;
        }
        return false;
    },
    
    async reconnect() {
        if (this.reconnectAttempts >= this.maxAttempts) {
            // Instead of giving up permanently, auto-schedule retry after 30s
            showToast('Connection failed. Auto-retrying in 30s...', 'warning', 8000);
            setTimeout(() => {
                this.reconnectAttempts = 0;
                this.reconnect();
            }, 30000);
            return;
        }
        
        this.reconnectAttempts++;
        this.updateStatus('reconnecting');
        
        // Exponential backoff: 2s, 4s, 8s, 16s, 30s (capped)
        const delay = Math.min(2000 * Math.pow(2, this.reconnectAttempts - 1), 30000);
        await new Promise(resolve => setTimeout(resolve, delay));
        const ok = await this.testConnection();
        if (!ok) await this.reconnect();
    }
};

// --- PERFORMANCE MONITOR ---
const PerfMonitor = {
    fps: 0,
    frameCount: 0,
    lastTime: performance.now(),
    enabled: PERF.MONITOR_ACTIVE,
    
    update() {
        this.frameCount++;
        const now = performance.now();
        
        if (now >= this.lastTime + 1000) {
            this.fps = Math.round((this.frameCount * 1000) / (now - this.lastTime));
            this.frameCount = 0;
            this.lastTime = now;
            
            if (this.enabled) this.render();
        }
    },
    
    render() {
        const fpsEl = document.getElementById('fps');
        const particleEl = document.getElementById('particle-count');
        const taskEl = document.getElementById('task-count-perf');
        
        if (!fpsEl) return;
        
        fpsEl.textContent = this.fps;
        fpsEl.className = 'perf-value ' + (this.fps >= 50 ? 'perf-good' : this.fps >= 30 ? 'perf-warn' : 'perf-bad');
        
        if (particleEl && window.particles) {
            particleEl.textContent = window.particles.length;
        }
        
        if (taskEl && window.lastTaskCount) {
            taskEl.textContent = window.lastTaskCount;
        }
    },
    
    toggle() {
        this.enabled = !this.enabled;
        PERF.MONITOR_ACTIVE = this.enabled;
        savePerfSettings();
        const monitor = document.getElementById('perf-monitor');
        if (monitor) {
            monitor.classList.toggle('active', this.enabled);
        }
        showToast(`Performance monitor ${this.enabled ? 'enabled' : 'disabled'}`, 'info', 2000);
    },

    initUI() {
        const monitor = document.getElementById('perf-monitor');
        if (monitor) {
            monitor.classList.toggle('active', this.enabled);
        }
    }
};

// --- OPTIMIZED FETCH WITH RETRY ---
async function fetchWithRetry(url, options = {}, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const response = await fetch(url, { ...options, signal: AbortSignal.timeout(5000) });
            if (response.ok) {
                ConnectionManager.updateStatus('connected');
                return await response.json();
            }
        } catch (e) {
            if (i === retries - 1) {
                ConnectionManager.reconnect();
                throw e;
            }
            await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        }
    }
}

// --- THROTTLE UTILITY ---
function throttle(func, wait) {
    let timeout = null;
    let previous = 0;
    
    return function(...args) {
        const now = Date.now();
        const remaining = wait - (now - previous);
        
        if (remaining <= 0 || remaining > wait) {
            if (timeout) {
                clearTimeout(timeout);
                timeout = null;
            }
            previous = now;
            func.apply(this, args);
        } else if (!timeout) {
            timeout = setTimeout(() => {
                previous = Date.now();
                timeout = null;
                func.apply(this, args);
            }, remaining);
        }
    };
}

// --- DEBOUNCE UTILITY ---
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// --- LOG MANAGER WITH LIMIT ---
const LogManager = {
    maxLines: PERF.MAX_LOG_LINES,
    
    addLog(text) {
        const logsEl = document.getElementById('logs');
        if (!logsEl) return;
        
        const lines = logsEl.children;
        if (lines.length >= this.maxLines) {
            logsEl.removeChild(lines[0]);
        }
        
        const div = document.createElement('div');
        div.className = 'le';
        div.innerHTML = '<span class="lt">[' + this.timeStr() + ']</span> ' + this.fmtLog(text);
        logsEl.appendChild(div);
        
        if (PERF.AUTO_SCROLL) {
            logsEl.scrollTop = logsEl.scrollHeight;
        }
    },
    
    timeStr() {
        const n = new Date();
        return n.getHours().toString().padStart(2, '0') + ':' + 
               n.getMinutes().toString().padStart(2, '0') + ':' + 
               n.getSeconds().toString().padStart(2, '0');
    },
    
    fmtLog(t) {
        const esc = (s) => s ? s.replace(/</g, '&lt;').replace(/>/g, '&gt;') : '';
        let c = '';
        if (t.indexOf('[GOD MODE]') !== -1) c = 'lgod';
        else if (t.indexOf('BLOCKED') !== -1) c = 'le-bl';
        else if (t.indexOf('[Ethics]') !== -1 && t.indexOf('⚠️') !== -1) c = 'le-wr';
        else if (t.indexOf('[Ethics]') !== -1 && t.indexOf('✅') !== -1) c = 'le-ok';
        else if (t.indexOf('[Kernel]') !== -1) c = 'lk';
        else if (t.indexOf('[Handler]') !== -1) c = 'lh';
        else if (t.indexOf('Error') !== -1) c = 'lerr';
        return '<span class="' + c + '">' + esc(t) + '</span>';
    },
    
    clear() {
        const logsEl = document.getElementById('logs');
        if (logsEl) {
            logsEl.innerHTML = '<div style="color:var(--text-muted);font-style:italic;font-size:0.72rem">// Logs cleared. Awaiting events...</div>';
        }
        showToast('Logs cleared', 'success', 2000);
    },
    
    export() {
        const logsEl = document.getElementById('logs');
        if (!logsEl) return;
        
        const text = Array.from(logsEl.children).map(el => el.textContent).join('\n');
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `krishna_logs_${Date.now()}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        showToast('Logs exported successfully', 'success');
    }
};

// Export for global use
window.PERF = PERF;
window.savePerfSettings = savePerfSettings;
window.showToast = showToast;
window.ConnectionManager = ConnectionManager;
window.PerfMonitor = PerfMonitor;
window.fetchWithRetry = fetchWithRetry;
window.throttle = throttle;
window.debounce = debounce;
window.LogManager = LogManager;
