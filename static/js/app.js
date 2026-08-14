/**
 * Main Application Controller for SmartVision AZS.
 * Manages WebSocket telemetry stream, FSM lifecycle UI, Drive&Pay card, and Audit logs.
 */
document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Components
    const canvasRenderer = new TelemetryCanvasRenderer('telemetryCanvas');
    const roiWidget = new ROICalculatorWidget();
    let ws = null;
    let reconnectTimer = null;
    let lastKnownState = 'IDLE';
    let isAlarmActive = false;

    // 2. Tab Navigation
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanels = document.querySelectorAll('.tab-panel');

    tabBtns.forEach((btn) => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            tabBtns.forEach((b) => b.classList.remove('active'));
            tabPanels.forEach((p) => p.classList.add('hidden'));

            btn.classList.add('active');
            document.getElementById(targetTab)?.classList.remove('hidden');

            if (targetTab === 'tab-audit') {
                loadAuditLogs();
            } else if (targetTab === 'tab-roi') {
                roiWidget.recalculate();
            }
        });
    });

    // 3. Audio Mute Toggle
    const muteBtn = document.getElementById('muteToggleBtn');
    if (muteBtn) {
        muteBtn.addEventListener('click', () => {
            const isMuted = window.soundAlerts.toggleMute();
            muteBtn.innerHTML = isMuted
                ? `<svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" /><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2" /></svg> <span>Звук: Выкл</span>`
                : `<svg class="w-5 h-5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z" /></svg> <span>Звук: Вкл</span>`;
        });
    }

    // 4. WebSocket Client Setup
    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;

        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('Connected to SmartVision Telemetry Stream.');
            document.getElementById('wsStatusBadge')?.classList.remove('bg-red-500');
            document.getElementById('wsStatusBadge')?.classList.add('bg-green-500');
            document.getElementById('wsStatusText').textContent = 'ONLINE (WebSocket)';
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                handleTelemetryMessage(data);
            } catch (e) {
                console.error('Error handling WS packet:', e);
            }
        };

        ws.onclose = () => {
            console.warn('WebSocket disconnected. Retrying in 2s...');
            document.getElementById('wsStatusBadge')?.classList.remove('bg-green-500');
            document.getElementById('wsStatusBadge')?.classList.add('bg-red-500');
            document.getElementById('wsStatusText').textContent = 'RECONNECTING...';
            clearTimeout(reconnectTimer);
            reconnectTimer = setTimeout(connectWebSocket, 2000);
        };
    }

    // 5. Handle Live Telemetry Update
    function handleTelemetryMessage(msg) {
        // Update Canvas Overlays
        canvasRenderer.updateTelemetry(msg.telemetry);

        const fsm = msg.fsm || {};
        const state = fsm.state || 'IDLE';
        const session = fsm.session;
        const telemetry = msg.telemetry || {};

        // Audio Triggers on State Transition
        if (state !== lastKnownState) {
            if (state === 'PLATE_IDENTIFIED' && session?.is_drive_and_pay) {
                window.soundAlerts.playPlateIdentified();
            } else if (state === 'FUELING') {
                window.soundAlerts.playFuelStart();
            } else if (state === 'SESSION_COMPLETE') {
                window.soundAlerts.playFuelComplete();
            }
            lastKnownState = state;
        }

        // Safety Alarm Siren Handling
        if (telemetry.is_alarm || state === 'ALARM_LOCKDOWN') {
            if (!isAlarmActive) {
                isAlarmActive = true;
                window.soundAlerts.startEmergencySiren();
            }
        } else {
            if (isAlarmActive) {
                isAlarmActive = false;
                window.soundAlerts.stopSiren();
            }
        }

        // Update FSM State Badge
        updateStateBadge(state);

        // Update Drive&Pay Card
        updateDriveAndPayCard(session, state);

        // Update Fuel Dispense Progress Meter
        updateFuelMeter(session, state);

        // Update Safety Monitor
        updateSafetyPanel(telemetry, state);
    }

    function updateStateBadge(state) {
        const badge = document.getElementById('fsmStateBadge');
        if (!badge) return;

        const stateConfig = {
            IDLE: { text: 'ОЖИДАНИЕ Т/С', bg: 'bg-zinc-800', textCol: 'text-zinc-300', border: 'border-zinc-700' },
            CAR_ARRIVED: { text: 'АВТОМОБИЛЬ НА ТРК', bg: 'bg-blue-900/40', textCol: 'text-blue-400', border: 'border-blue-700' },
            PLATE_IDENTIFIED: { text: 'ГОСНОМЕР ОПРЕДЕЛЕН', bg: 'bg-amber-900/40', textCol: 'text-amber-300', border: 'border-amber-600' },
            NOZZLE_INSERTED: { text: 'ПИСТОЛЕТ В БАКЕ', bg: 'bg-emerald-900/40', textCol: 'text-emerald-300', border: 'border-emerald-600' },
            FUELING: { text: 'ИДЕТ НАЛИВ ТОПЛИВА', bg: 'bg-green-600/30', textCol: 'text-green-400', border: 'border-green-500' },
            NOZZLE_RETURNED: { text: 'ПИСТОЛЕТ ВЕРНУТ', bg: 'bg-teal-900/40', textCol: 'text-teal-300', border: 'border-teal-600' },
            SESSION_COMPLETE: { text: 'ЗАПРАВКА ЗАВЕРШЕНА', bg: 'bg-green-700/40', textCol: 'text-green-300', border: 'border-green-600' },
            ALARM_LOCKDOWN: { text: 'АВАРИЙНАЯ БЛОКИРОВКА (E-STOP)', bg: 'bg-red-600 animate-pulse', textCol: 'text-white', border: 'border-red-500' },
        };

        const cfg = stateConfig[state] || stateConfig.IDLE;
        badge.className = `px-3.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider border transition-all duration-300 ${cfg.bg} ${cfg.textCol} ${cfg.border}`;
        badge.textContent = cfg.text;
    }

    function updateDriveAndPayCard(session, state) {
        const cardDriver = document.getElementById('cardDriverName');
        const cardPlate = document.getElementById('cardPlate');
        const cardModel = document.getElementById('cardModel');
        const cardBalance = document.getElementById('cardBalance');
        const cardFuel = document.getElementById('cardFuelType');
        const cardDnpStatus = document.getElementById('cardDnpStatus');

        if (session) {
            if (cardDriver) cardDriver.textContent = session.driver_name;
            if (cardPlate) cardPlate.textContent = session.plate;
            if (cardModel) cardModel.textContent = session.model;
            if (cardBalance) cardBalance.textContent = `${session.balance.toFixed(2)} BYN`;
            if (cardFuel) cardFuel.textContent = `${session.fuel_type} (${session.price.toFixed(2)} BYN/л)`;

            if (cardDnpStatus) {
                if (session.is_drive_and_pay) {
                    cardDnpStatus.className = 'inline-flex items-center px-2.5 py-0.5 rounded text-xs font-bold bg-green-500/20 text-green-400 border border-green-500/40';
                    cardDnpStatus.textContent = 'Drive&Pay: Активен (Zero-Click)';
                } else {
                    cardDnpStatus.className = 'inline-flex items-center px-2.5 py-0.5 rounded text-xs font-bold bg-yellow-500/20 text-yellow-400 border border-yellow-500/40';
                    cardDnpStatus.textContent = 'Гостевой режим (Оплата на кассе)';
                }
            }
        } else {
            if (cardDriver) cardDriver.textContent = '—';
            if (cardPlate) cardPlate.textContent = '—';
            if (cardModel) cardModel.textContent = 'Ожидание автомобиля';
            if (cardBalance) cardBalance.textContent = '0.00 BYN';
            if (cardFuel) cardFuel.textContent = '—';
            if (cardDnpStatus) {
                cardDnpStatus.className = 'inline-flex items-center px-2.5 py-0.5 rounded text-xs font-bold bg-zinc-800 text-zinc-400 border border-zinc-700';
                cardDnpStatus.textContent = 'Режим ожидания';
            }
        }
    }

    function updateFuelMeter(session, state) {
        const elLiters = document.getElementById('dispensedLiters');
        const elCost = document.getElementById('dispensedCost');
        const elTarget = document.getElementById('targetLiters');
        const elBar = document.getElementById('fuelProgressBar');

        if (session) {
            const liters = session.dispensed_liters || 0.0;
            const cost = session.total_cost || 0.0;
            const target = session.target_liters || 30.0;
            const pct = Math.min(100, Math.round((liters / Math.max(target, 1)) * 100));

            if (elLiters) elLiters.textContent = liters.toFixed(2);
            if (elCost) elCost.textContent = `${cost.toFixed(2)} BYN`;
            if (elTarget) elTarget.textContent = `${target.toFixed(1)} л`;
            if (elBar) elBar.style.width = `${pct}%`;
        } else {
            if (elLiters) elLiters.textContent = '0.00';
            if (elCost) elCost.textContent = '0.00 BYN';
            if (elTarget) elTarget.textContent = '0.0 л';
            if (elBar) elBar.style.width = '0%';
        }
    }

    function updateSafetyPanel(telemetry, state) {
        const elDisp = document.getElementById('safetyDisplacementVal');
        const elPumpLock = document.getElementById('pumpLockStatus');
        const elMsg = document.getElementById('safetyStatusMsg');
        const elAlarmBanner = document.getElementById('emergencyAlarmBanner');

        const disp = telemetry.displacement_px || 0.0;
        const isAlarm = !!telemetry.is_alarm || state === 'ALARM_LOCKDOWN';
        const isLocked = !!telemetry.pump_locked || state === 'ALARM_LOCKDOWN';

        if (elDisp) {
            elDisp.textContent = `${disp.toFixed(1)} px / 300мс`;
            elDisp.className = disp > 15 ? 'text-red-400 font-bold' : 'text-emerald-400 font-bold';
        }

        if (elPumpLock) {
            if (isLocked) {
                elPumpLock.className = 'inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-red-600 text-white';
                elPumpLock.textContent = 'НАСОС: ЗАБЛОКИРОВАН (E-STOP)';
            } else {
                elPumpLock.className = 'inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-emerald-600/30 text-emerald-300 border border-emerald-500/50';
                elPumpLock.textContent = 'НАСОС: РАЗРЕШЕН';
            }
        }

        if (elMsg) {
            elMsg.textContent = telemetry.safety_message || 'Мониторинг риска обрыва шланга активен.';
        }

        if (elAlarmBanner) {
            if (isAlarm) {
                elAlarmBanner.classList.remove('hidden');
                document.getElementById('alarmDetailsText').textContent =
                    telemetry.safety_message || 'Критический риск обрыва шланга! Насосы ТРК №2 обесточены.';
            } else {
                elAlarmBanner.classList.add('hidden');
            }
        }
    }

    // 6. Simulator Controls & Action Buttons
    const videoEl = document.getElementById('stationVideo');
    const scenarioBtns = document.querySelectorAll('.scenario-btn');
    scenarioBtns.forEach((btn) => {
        btn.addEventListener('click', async () => {
            const action = btn.getAttribute('data-action');
            if (videoEl) {
                if (action === 'scenario_1' || action === 'restart') {
                    videoEl.currentTime = 0;
                    videoEl.play();
                } else if (action === 'scenario_2') {
                    videoEl.currentTime = 20.0;
                    videoEl.play();
                } else if (action === 'scenario_3') {
                    videoEl.currentTime = 35.0;
                    videoEl.play();
                }
            }
            try {
                await fetch(`/api/simulator/control?action=${action}`, { method: 'POST' });
            } catch (e) {
                console.error('Failed to switch scenario:', e);
            }
        });
    });

    const estopBtn = document.getElementById('estopButton');
    if (estopBtn) {
        estopBtn.addEventListener('click', async () => {
            try {
                await fetch('/api/emergency-stop', { method: 'POST' });
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ command: 'EMERGENCY_STOP' }));
                }
            } catch (e) {
                console.error('Failed to trigger E-STOP:', e);
            }
        });
    }

    const resetAlarmBtn = document.getElementById('resetAlarmBtn');
    if (resetAlarmBtn) {
        resetAlarmBtn.addEventListener('click', async () => {
            try {
                await fetch('/api/reset-alarm', { method: 'POST' });
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({ command: 'RESET_ALARM' }));
                }
            } catch (e) {
                console.error('Failed to reset alarm:', e);
            }
        });
    }

    // 7. Load Audit Logs (Sessions & Incidents)
    async function loadAuditLogs() {
        try {
            // Load Sessions
            const sessRes = await fetch('/api/sessions?limit=20');
            const sessions = await sessRes.json();
            const sessTbody = document.getElementById('sessionsTableBody');
            if (sessTbody) {
                sessTbody.innerHTML = sessions
                    .map(
                        (s) => `
                    <tr class="border-b border-zinc-800 hover:bg-zinc-800/40 transition-colors">
                        <td class="px-4 py-3 font-mono text-xs text-zinc-400">${s.session_uuid.slice(0, 8)}</td>
                        <td class="px-4 py-3 font-bold text-amber-300">${s.vehicle_plate}</td>
                        <td class="px-4 py-3 text-zinc-200">${s.fuel_type}</td>
                        <td class="px-4 py-3 text-zinc-200">${s.dispensed_liters.toFixed(2)} л</td>
                        <td class="px-4 py-3 font-bold text-emerald-400">${s.total_cost.toFixed(2)} BYN</td>
                        <td class="px-4 py-3">
                            <span class="px-2 py-0.5 text-xs rounded font-medium ${s.is_zero_click ? 'bg-green-500/20 text-green-300' : 'bg-zinc-700 text-zinc-300'}">
                                ${s.is_zero_click ? 'Drive&Pay Zero-Click' : 'Терминал / Касса'}
                            </span>
                        </td>
                        <td class="px-4 py-3 text-xs text-zinc-400">${s.created_at}</td>
                    </tr>
                `
                    )
                    .join('');
            }

            // Load Incidents
            const incRes = await fetch('/api/incidents?limit=20');
            const incidents = await incRes.json();
            const incTbody = document.getElementById('incidentsTableBody');
            if (incTbody) {
                incTbody.innerHTML = incidents
                    .map(
                        (inc) => `
                    <tr class="border-b border-zinc-800 hover:bg-zinc-800/40 transition-colors">
                        <td class="px-4 py-3">
                            <span class="px-2 py-0.5 text-xs rounded font-bold ${inc.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border border-red-500/40' : 'bg-yellow-500/20 text-yellow-300'}">
                                ${inc.incident_type}
                            </span>
                        </td>
                        <td class="px-4 py-3 text-xs text-zinc-200">${inc.description}</td>
                        <td class="px-4 py-3 font-mono text-xs ${inc.displacement_px > 15 ? 'text-red-400 font-bold' : 'text-zinc-300'}">
                            ${inc.displacement_px > 0 ? `${inc.displacement_px} px` : '—'}
                        </td>
                        <td class="px-4 py-3 text-xs text-zinc-400">${inc.created_at}</td>
                    </tr>
                `
                    )
                    .join('');
            }
        } catch (e) {
            console.error('Failed to load audit logs:', e);
        }
    }

    // Connect on load
    connectWebSocket();
});
