/**
 * Canvas 2D HUD & Bounding Box Renderer for SmartVision AZS.
 * Renders telemetry overlays, zone boundaries, centroid vectors, and alarm indicators with layer toggles.
 */
class TelemetryCanvasRenderer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas ? this.canvas.getContext('2d') : null;
        this.virtualWidth = 1280;
        this.virtualHeight = 720;
        this.currentBoxes = [];
        this.isAlarm = false;
        this.alarmType = '';
        this.displacement = 0;
        this.flashCounter = 0;

        // Layer visibility toggles
        this.showPlates = true;
        this.showZones = true;
        this.showDisplacement = true;

        if (this.canvas) {
            this.resize();
            window.addEventListener('resize', () => this.resize());
        }
    }

    resize() {
        if (!this.canvas) return;
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width * (window.devicePixelRatio || 1);
        this.canvas.height = rect.height * (window.devicePixelRatio || 1);
        if (this.ctx) {
            this.ctx.scale(
                this.canvas.width / this.virtualWidth,
                this.canvas.height / this.virtualHeight
            );
        }
    }

    updateTelemetry(telemetry) {
        if (!telemetry) return;
        this.currentBoxes = telemetry.boxes || [];
        this.isAlarm = !!telemetry.is_alarm;
        this.alarmType = telemetry.alarm_type || '';
        this.displacement = telemetry.displacement_px || 0;
        this.render();
    }

    render() {
        if (!this.ctx) return;
        const ctx = this.ctx;
        ctx.clearRect(0, 0, this.virtualWidth, this.virtualHeight);

        // 1. Draw Bounding Boxes & Zones
        for (const box of this.currentBoxes) {
            if (box.type === 'zone' && !this.showZones) continue;
            if (box.type === 'plate' && !this.showPlates) continue;

            const [x1, y1, x2, y2] = box.bbox;
            const w = x2 - x1;
            const h = y2 - y1;
            const color = box.color || '#00843D';

            ctx.save();
            if (box.type === 'zone') {
                // Dashed boundary for control zone
                ctx.setLineDash([8, 6]);
                ctx.strokeStyle = color;
                ctx.lineWidth = 2.5;
                ctx.strokeRect(x1, y1, w, h);

                // Subtle semi-transparent fill
                ctx.fillStyle = 'rgba(0, 132, 61, 0.08)';
                ctx.fillRect(x1, y1, w, h);

                // Zone Label Badge
                ctx.setLineDash([]);
                ctx.fillStyle = 'rgba(24, 24, 27, 0.85)';
                ctx.fillRect(x1, y1 - 28, 260, 28);
                ctx.strokeStyle = color;
                ctx.strokeRect(x1, y1 - 28, 260, 28);

                ctx.fillStyle = '#00E676';
                ctx.font = 'bold 13px Inter, sans-serif';
                ctx.fillText(box.label, x1 + 8, y1 - 9);
            } else {
                // Solid bounding box with corner brackets
                ctx.strokeStyle = color;
                ctx.lineWidth = box.type === 'plate' ? 2.5 : 2;
                ctx.strokeRect(x1, y1, w, h);

                // Corner accents for high-tech HUD look
                const cornerLen = Math.min(16, w / 4);
                ctx.lineWidth = 4;
                ctx.beginPath();
                // Top-Left
                ctx.moveTo(x1, y1 + cornerLen); ctx.lineTo(x1, y1); ctx.lineTo(x1 + cornerLen, y1);
                // Top-Right
                ctx.moveTo(x2 - cornerLen, y1); ctx.lineTo(x2, y1); ctx.lineTo(x2, y1 + cornerLen);
                // Bottom-Left
                ctx.moveTo(x1, y2 - cornerLen); ctx.lineTo(x1, y2); ctx.lineTo(x1 + cornerLen, y2);
                // Bottom-Right
                ctx.moveTo(x2 - cornerLen, y2); ctx.lineTo(x2, y2); ctx.lineTo(x2, y2 - cornerLen);
                ctx.stroke();

                // Centroid & displacement marker for vehicle
                if (box.centroid && box.type === 'vehicle' && this.showDisplacement) {
                    const [cx, cy] = box.centroid;
                    ctx.fillStyle = color;
                    ctx.beginPath();
                    ctx.arc(cx, cy, 6, 0, Math.PI * 2);
                    ctx.fill();

                    ctx.strokeStyle = 'rgba(255, 255, 255, 0.8)';
                    ctx.lineWidth = 1.5;
                    ctx.beginPath();
                    ctx.arc(cx, cy, 14, 0, Math.PI * 2);
                    ctx.stroke();

                    // Displacement tag
                    const dispText = `ΔD: ${box.displacement || 0}px`;
                    ctx.fillStyle = (box.displacement || 0) > 15 ? '#EF4444' : '#10B981';
                    ctx.font = 'bold 12px monospace';
                    ctx.fillText(dispText, cx + 18, cy + 4);
                }

                // Label pill badge
                const labelText = box.label || '';
                ctx.font = 'bold 13px Inter, sans-serif';
                const textWidth = ctx.measureText(labelText).width;
                const badgeWidth = textWidth + 16;
                const badgeHeight = 24;
                const badgeY = Math.max(0, y1 - badgeHeight - 4);

                ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
                ctx.fillRect(x1, badgeY, badgeWidth, badgeHeight);
                ctx.strokeStyle = color;
                ctx.lineWidth = 1.5;
                ctx.strokeRect(x1, badgeY, badgeWidth, badgeHeight);

                ctx.fillStyle = '#FFFFFF';
                ctx.fillText(labelText, x1 + 8, badgeY + 16);
            }
            ctx.restore();
        }

        // 2. Emergency Alarm Overlay Banner
        if (this.isAlarm) {
            this.flashCounter++;
            const isFlashRed = Math.floor(this.flashCounter / 15) % 2 === 0;

            ctx.save();
            // Flashing border
            ctx.strokeStyle = isFlashRed ? '#EF4444' : '#F59E0B';
            ctx.lineWidth = 10;
            ctx.strokeRect(5, 5, this.virtualWidth - 10, this.virtualHeight - 10);

            // Top Warning HUD Banner
            ctx.fillStyle = isFlashRed ? 'rgba(239, 68, 68, 0.95)' : 'rgba(185, 28, 28, 0.95)';
            ctx.fillRect(0, 0, this.virtualWidth, 68);

            ctx.fillStyle = '#FFFFFF';
            ctx.font = '900 20px Inter, sans-serif';
            ctx.fillText('⚠ ТРЕВОГА: РИСК ОБРЫВА ШЛАНГА! НАСОСЫ ЗАБЛОКИРОВАНЫ', 40, 32);

            ctx.font = 'bold 14px monospace';
            ctx.fillStyle = '#FEF08A';
            ctx.fillText(`Смещение Т/С: ${this.displacement} px / 300мс (> 15 px) | Сигнал аварийного отключения E-STOP активен`, 40, 54);

            ctx.restore();
        }
    }
}

window.TelemetryCanvasRenderer = TelemetryCanvasRenderer;
