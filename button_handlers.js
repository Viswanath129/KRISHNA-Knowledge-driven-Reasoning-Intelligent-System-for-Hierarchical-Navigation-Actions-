// ================================================================
//  KRISHNA GOD MODE - ALL BUTTON HANDLERS
//  Making Every Button Fully Functional
// ================================================================

// --- BUTTON EVENT HANDLERS ---
const ButtonHandlers = {
    _toggleLock: false,  // Mutex: prevents rapid-click race conditions on toggle buttons

    init() {
        // Clear logs button
        const clearBtn = document.getElementById('clr');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => LogManager.clear());
        }
        
        // Export logs button
        const exportBtn = document.getElementById('export-logs');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => LogManager.export());
        }
        
        // Clear tasks button
        const clearTasksBtn = document.getElementById('clear-tasks-btn');
        if (clearTasksBtn) {
            clearTasksBtn.addEventListener('click', () => this.clearTasks());
        }
        
        // Clear ethics button
        const clearEthicsBtn = document.getElementById('clear-ethics-btn');
        if (clearEthicsBtn) {
            clearEthicsBtn.addEventListener('click', () => this.clearEthics());
        }
        
        // Pause kernel button
        const pauseBtn = document.getElementById('pause-btn');
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => this.togglePause());
        }
        
        // Turbo mode button
        const turboBtn = document.getElementById('turbo-btn');
        if (turboBtn) {
            turboBtn.addEventListener('click', () => this.toggleTurbo());
        }
        
        // Performance monitor button
        const perfBtn = document.getElementById('perf-btn');
        if (perfBtn) {
            perfBtn.addEventListener('click', () => PerfMonitor.toggle());
        }
        
        // Terminal dots
        const dotRed = document.getElementById('dot-red');
        const dotYellow = document.getElementById('dot-yellow');
        const dotGreen = document.getElementById('dot-green');
        
        if (dotRed) {
            dotRed.addEventListener('click', () => this.minimizeTerminal());
        }
        
        if (dotYellow) {
            dotYellow.addEventListener('click', () => this.toggleAutoScroll());
        }
        
        if (dotGreen) {
            dotGreen.addEventListener('click', () => this.maximizeTerminal());
        }

        // Initialize UI from saved state
        this.applySavedState();
    },

    applySavedState() {
        if (PERF.PAUSED) {
            const pauseBtn = document.getElementById('pause-btn');
            if (pauseBtn) {
                pauseBtn.textContent = '▶️';
                pauseBtn.title = 'Resume Kernel';
                pauseBtn.style.background = 'rgba(239,68,68,0.15)';
                pauseBtn.style.borderColor = 'rgba(239,68,68,0.3)';
            }
        }

        if (PERF.TURBO_MODE) {
            PERF.THROTTLE_TASK_POLL = 200;
            PERF.THROTTLE_GOD_POLL = 400;
            PERF.THROTTLE_ETHICS_POLL = 1000;
            const turboBtn = document.getElementById('turbo-btn');
            if (turboBtn) {
                turboBtn.style.background = 'linear-gradient(135deg, #22d3ee, #c084fc)';
                turboBtn.style.borderColor = 'var(--cyan)';
                turboBtn.style.color = '#fff';
            }
        }

        const dotYellow = document.getElementById('dot-yellow');
        if (dotYellow) {
            if (PERF.AUTO_SCROLL) {
                dotYellow.style.boxShadow = '0 0 10px #febc2e';
            } else {
                dotYellow.style.boxShadow = '';
            }
        }

        if (window.PerfMonitor) {
            PerfMonitor.initUI();
        }
    },
    
    clearTasks() {
        window.lastTaskHash = '';
        const container = document.getElementById('tl-container');
        if (container) {
            container.innerHTML = '<div class="empty"><div class="empty-icon">⚡</div><div>Task history cleared.<br>Submit a new goal.</div></div>';
        }
        document.getElementById('tc').textContent = '0 tasks';
        showToast('Task history cleared', 'success', 2000);
    },
    
    clearEthics() {
        const auditWrap = document.getElementById('audit');
        if (auditWrap) {
            auditWrap.innerHTML = '<div class="empty" style="padding:16px;text-align:center;color:var(--text-muted);font-size:0.7rem;">Ethics audit cleared</div>';
        }
        document.getElementById('ac').textContent = '0 entries';
        showToast('Ethics audit cleared', 'success', 2000);
    },
    
    togglePause() {
        if (this._toggleLock) return;
        this._toggleLock = true;
        setTimeout(() => { this._toggleLock = false; }, 300);

        PERF.PAUSED = !PERF.PAUSED;
        if (window.savePerfSettings) window.savePerfSettings();

        const pauseBtn = document.getElementById('pause-btn');
        
        if (PERF.PAUSED) {
            pauseBtn.textContent = '▶️';
            pauseBtn.title = 'Resume Kernel';
            pauseBtn.style.background = 'rgba(239,68,68,0.15)';
            pauseBtn.style.borderColor = 'rgba(239,68,68,0.3)';
            showToast('Kernel paused - Polling stopped', 'warning', 3000);
        } else {
            pauseBtn.textContent = '⏸️';
            pauseBtn.title = 'Pause Kernel';
            pauseBtn.style.background = '';
            pauseBtn.style.borderColor = '';
            showToast('Kernel resumed - Polling active', 'success', 3000);
        }
    },
    
    toggleTurbo() {
        if (this._toggleLock) return;
        this._toggleLock = true;
        setTimeout(() => { this._toggleLock = false; }, 300);

        PERF.TURBO_MODE = !PERF.TURBO_MODE;
        if (window.savePerfSettings) window.savePerfSettings();

        const turboBtn = document.getElementById('turbo-btn');
        
        if (PERF.TURBO_MODE) {
            PERF.THROTTLE_TASK_POLL = 200;
            PERF.THROTTLE_GOD_POLL = 400;
            PERF.THROTTLE_ETHICS_POLL = 1000;
            turboBtn.style.background = 'linear-gradient(135deg, #22d3ee, #c084fc)';
            turboBtn.style.borderColor = 'var(--cyan)';
            turboBtn.style.color = '#fff';
            showToast('🚀 TURBO MODE ACTIVATED - Increased polling speed!', 'success', 3000);
            
            // Restart pollers with new intervals
            if (window.taskPollInterval) clearInterval(window.taskPollInterval);
            if (window.godPollInterval) clearInterval(window.godPollInterval);
            if (window.ethicsPollInterval) clearInterval(window.ethicsPollInterval);
            
            window.startPolling();
        } else {
            PERF.THROTTLE_TASK_POLL = 500;
            PERF.THROTTLE_GOD_POLL = 1000;
            PERF.THROTTLE_ETHICS_POLL = 2500;
            turboBtn.style.background = '';
            turboBtn.style.borderColor = '';
            turboBtn.style.color = '';
            showToast('Turbo mode disabled - Normal speed', 'info', 2000);
            
            // Restart pollers with normal intervals
            if (window.taskPollInterval) clearInterval(window.taskPollInterval);
            if (window.godPollInterval) clearInterval(window.godPollInterval);
            if (window.ethicsPollInterval) clearInterval(window.ethicsPollInterval);
            
            window.startPolling();
        }
    },
    
    minimizeTerminal() {
        const term = document.getElementById('term-panel');
        if (!term) return;
        
        if (term.style.display === 'none') {
            term.style.display = '';
            showToast('Terminal restored', 'info', 2000);
        } else {
            term.style.display = 'none';
            showToast('Terminal minimized', 'info', 2000);
        }
    },
    
    toggleAutoScroll() {
        PERF.AUTO_SCROLL = !PERF.AUTO_SCROLL;
        if (window.savePerfSettings) window.savePerfSettings();

        const dotYellow = document.getElementById('dot-yellow');
        
        if (PERF.AUTO_SCROLL) {
            dotYellow.style.boxShadow = '0 0 10px #febc2e';
            showToast('Auto-scroll enabled', 'success', 2000);
        } else {
            dotYellow.style.boxShadow = '';
            showToast('Auto-scroll disabled', 'info', 2000);
        }
    },
    
    maximizeTerminal() {
        const term = document.getElementById('term-panel');
        if (!term) return;
        
        if (term.classList.contains('maximized')) {
            term.classList.remove('maximized');
            term.style.position = '';
            term.style.inset = '';
            term.style.zIndex = '';
            term.style.maxHeight = '';
            showToast('Terminal restored', 'info', 2000);
        } else {
            term.classList.add('maximized');
            term.style.position = 'fixed';
            term.style.inset = '10px';
            term.style.zIndex = '10000';
            term.style.maxHeight = 'calc(100vh - 20px)';
            showToast('Terminal maximized - Click again to restore', 'info', 3000);
        }
    }
};

// Export for global use
window.ButtonHandlers = ButtonHandlers;
