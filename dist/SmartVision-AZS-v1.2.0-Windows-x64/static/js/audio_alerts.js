/**
 * Web Audio API Alert Synthesizer for SmartVision AZS.
 * Generates clear, hardware-independent industrial sound alerts.
 */
class SmartVisionAudio {
    constructor() {
        this.ctx = null;
        this.sirenOsc = null;
        this.sirenGain = null;
        this.isSirenPlaying = false;
        this.muted = false;
    }

    _initContext() {
        if (!this.ctx) {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            this.ctx = new AudioCtx();
        }
        if (this.ctx.state === 'suspended') {
            this.ctx.resume();
        }
    }

    toggleMute() {
        this.muted = !this.muted;
        if (this.muted && this.isSirenPlaying) {
            this.stopSiren();
        }
        return this.muted;
    }

    playPlateIdentified() {
        if (this.muted) return;
        this._initContext();
        
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(880, now); // A5
        osc.frequency.exponentialRampToValueAtTime(1318.5, now + 0.12); // E6

        gain.gain.setValueAtTime(0.01, now);
        gain.gain.linearRampToValueAtTime(0.18, now + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.35);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.36);
    }

    playFuelStart() {
        if (this.muted) return;
        this._initContext();

        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'triangle';
        osc.frequency.setValueAtTime(587.33, now); // D5
        osc.frequency.setValueAtTime(880.0, now + 0.08); // A5

        gain.gain.setValueAtTime(0.15, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.26);
    }

    playFuelComplete() {
        if (this.muted) return;
        this._initContext();

        const notes = [523.25, 659.25, 783.99]; // C5 - E5 - G5
        notes.forEach((freq, i) => {
            const now = this.ctx.currentTime + (i * 0.08);
            const osc = this.ctx.createOscillator();
            const gain = this.ctx.createGain();

            osc.type = 'sine';
            osc.frequency.setValueAtTime(freq, now);

            gain.gain.setValueAtTime(0.12, now);
            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.3);

            osc.connect(gain);
            gain.connect(this.ctx.destination);

            osc.start(now);
            osc.stop(now + 0.32);
        });
    }

    startEmergencySiren() {
        if (this.muted || this.isSirenPlaying) return;
        this._initContext();

        this.isSirenPlaying = true;
        const now = this.ctx.currentTime;

        this.sirenOsc = this.ctx.createOscillator();
        this.sirenGain = this.ctx.createGain();

        // High urgency two-tone square/sawtooth alarm
        this.sirenOsc.type = 'sawtooth';
        this.sirenOsc.frequency.setValueAtTime(650, now);

        // LFO for pitch oscillation (650Hz to 1100Hz at 4Hz rate)
        const lfo = this.ctx.createOscillator();
        const lfoGain = this.ctx.createGain();
        lfo.type = 'square';
        lfo.frequency.setValueAtTime(3.5, now); // 3.5 alternating cycles per sec
        lfoGain.gain.setValueAtTime(300, now);

        lfo.connect(this.sirenOsc.frequency);
        lfo.start(now);
        this.sirenLfo = lfo;

        this.sirenGain.gain.setValueAtTime(0.25, now);

        this.sirenOsc.connect(this.sirenGain);
        this.sirenGain.connect(this.ctx.destination);

        this.sirenOsc.start(now);
    }

    stopSiren() {
        if (this.isSirenPlaying && this.sirenGain && this.ctx) {
            const now = this.ctx.currentTime;
            this.sirenGain.gain.linearRampToValueAtTime(0.001, now + 0.05);
            setTimeout(() => {
                try {
                    if (this.sirenOsc) this.sirenOsc.stop();
                    if (this.sirenLfo) this.sirenLfo.stop();
                } catch (e) {}
                this.isSirenPlaying = false;
                this.sirenOsc = null;
                this.sirenGain = null;
            }, 60);
        }
    }

    playEmergencyAlarm() {
        this.startEmergencySiren();
    }

    stopEmergencyAlarm() {
        this.stopSiren();
    }
}

window.soundAlerts = new SmartVisionAudio();
