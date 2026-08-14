/**
 * Main Application Controller for SmartVision AZS — Belorusneft.
 * Manages WebSocket telemetry stream, FSM lifecycle UI, Drive&Pay card,
 * Scrubber Timeline, Glass HUD Toggles, Modals, and Audit logs.
 */
document.addEventListener('DOMContentLoaded', () => {
    // 1. Initialize Components
    const canvasRenderer = new TelemetryCanvasRenderer('telemetryCanvas');
    const roiWidget = new ROICalculatorWidget();
    let ws = null;
    let reconnectTimer = null;
    let lastKnownState = 'IDLE';
    let isAlarmActive = false;
    let currentFuelPrice = 2.46;
    let currentFuelType = 'АИ-95';
    let cachedSessions = [];
    let cachedIncidents = [];

    // Video Stream Watchdog & Reconnection
    const stationVideo = document.getElementById('stationVideo');
    function refreshVideoStream() {
        if (!stationVideo) return;
        stationVideo.src = `/api/video/feed?t=${Date.now()}`;
    }

    if (stationVideo) {
        stationVideo.onerror = () => {
            console.warn('Video stream interrupted. Reconnecting in 1s...');
            setTimeout(refreshVideoStream, 1000);
        };
        // Periodic stream sanity watchdog
        setInterval(() => {
            if (stationVideo && stationVideo.complete && stationVideo.naturalWidth === 0) {
                refreshVideoStream();
            }
        }, 10000);
    }

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

            if (targetTab === 'tab-operator') {
                refreshVideoStream();
            } else {
                if (stationVideo) stationVideo.src = '';
                if (targetTab === 'tab-audit') {
                    loadAuditLogs();
                } else if (targetTab === 'tab-roi') {
                    roiWidget.recalculate();
                }
            }
        });
    });

    // 3. Audio Mute Toggle
    const muteBtn = document.getElementById('muteToggleBtn');
    if (muteBtn) {
        muteBtn.addEventListener('click', () => {
            const isMuted = window.soundAlerts.toggleMute();
            document.getElementById('muteIcon').textContent = isMuted ? '🔇' : '🔊';
            document.getElementById('muteText').textContent = isMuted ? 'Звук: Выкл' : 'Звук: Вкл';
        });
    }

    // 4. Floating Glass HUD Controls
    const btnLayerPlate = document.getElementById('btnLayerPlate');
    const btnLayerZone = document.getElementById('btnLayerZone');
    const btnLayerDisp = document.getElementById('btnLayerDisp');
    const btnSnapshot = document.getElementById('btnSnapshot');
    const btnFullscreen = document.getElementById('btnFullscreen');

    if (btnLayerPlate) {
        btnLayerPlate.addEventListener('click', () => {
            canvasRenderer.showPlates = !canvasRenderer.showPlates;
            btnLayerPlate.classList.toggle('active', canvasRenderer.showPlates);
            btnLayerPlate.textContent = canvasRenderer.showPlates ? '✓ Номер' : '✕ Номер';
            canvasRenderer.render();
        });
    }
    if (btnLayerZone) {
        btnLayerZone.addEventListener('click', () => {
            canvasRenderer.showZones = !canvasRenderer.showZones;
            btnLayerZone.classList.toggle('active', canvasRenderer.showZones);
            btnLayerZone.textContent = canvasRenderer.showZones ? '✓ Зона' : '✕ Зона';
            canvasRenderer.render();
        });
    }
    if (btnLayerDisp) {
        btnLayerDisp.addEventListener('click', () => {
            canvasRenderer.showDisplacement = !canvasRenderer.showDisplacement;
            btnLayerDisp.classList.toggle('active', canvasRenderer.showDisplacement);
            btnLayerDisp.textContent = canvasRenderer.showDisplacement ? '✓ Смещение' : '✕ Смещение';
            canvasRenderer.render();
        });
    }

    // Snapshot Functionality
    if (btnSnapshot) {
        btnSnapshot.addEventListener('click', () => {
            const videoImg = document.getElementById('stationVideo');
            const hudCanvas = document.getElementById('telemetryCanvas');
            if (!videoImg || !hudCanvas) return;

            const tempCanvas = document.createElement('canvas');
            tempCanvas.width = 1280;
            tempCanvas.height = 720;
            const ctx = tempCanvas.getContext('2d');

            try {
                ctx.drawImage(videoImg, 0, 0, 1280, 720);
                ctx.drawImage(hudCanvas, 0, 0, 1280, 720);

                const link = document.createElement('a');
                link.download = `SmartVision_Snapshot_${new Date().toISOString().replace(/[:.]/g, '-')}.png`;
                link.href = tempCanvas.toDataURL('image/png');
                link.click();
            } catch (e) {
                console.error('Failed to capture snapshot:', e);
            }
        });
    }

    // Fullscreen Toggle
    if (btnFullscreen) {
        btnFullscreen.addEventListener('click', () => {
            const container = document.getElementById('videoContainer');
            if (!document.fullscreenElement) {
                container?.requestFullscreen().catch((err) => console.error(err));
                btnFullscreen.textContent = '⛶ Выход';
            } else {
                document.exitFullscreen();
                btnFullscreen.textContent = '⛶ Экран';
            }
        });
    }

    // 5. Interactive Scrubber Timeline
    const timelineEl = document.getElementById('scenarioTimeline');
    const timelineProgress = document.getElementById('timelineProgress');
    const timelineTimeText = document.getElementById('timelineCurrentTimeText');

    if (timelineEl) {
        timelineEl.addEventListener('click', async (e) => {
            const rect = timelineEl.getBoundingClientRect();
            const clickX = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
            const pct = clickX / rect.width;
            const targetSec = pct * 50.0;

            try {
                await fetch(`/api/simulator/control?action=seek&time=${targetSec.toFixed(1)}`, { method: 'POST' });
            } catch (err) {
                console.error('Timeline seek error:', err);
            }
        });
    }

    // 6. Fuel Grade Selector
    const fuelGradeBtns = document.querySelectorAll('.fuel-grade-btn');
    fuelGradeBtns.forEach((btn) => {
        btn.addEventListener('click', () => {
            fuelGradeBtns.forEach((b) => {
                b.className = 'fuel-grade-btn px-2.5 py-1 rounded bg-zinc-800 text-zinc-300 font-bold text-[11px] border border-zinc-700 hover:bg-zinc-700';
            });
            btn.className = 'fuel-grade-btn active px-2.5 py-1 rounded bg-[#00843D] text-white font-bold text-[11px] border border-[#00A84E]';
            currentFuelType = btn.getAttribute('data-fuel');
            currentFuelPrice = parseFloat(btn.getAttribute('data-price') || '2.46');
            const cardFuel = document.getElementById('cardFuelType');
            if (cardFuel) {
                cardFuel.textContent = `${currentFuelType} (${currentFuelPrice.toFixed(2)} BYN/л)`;
            }
        });
    });

    // 7. Electronic Fiscal Receipt Modal
    const receiptModal = document.getElementById('receiptModal');
    const openReceiptBtn = document.getElementById('openReceiptBtn');
    const closeReceiptBtn = document.getElementById('closeReceiptBtn');

    function drawReceiptQr(receiptId) {
        const qrCanvas = document.getElementById('receiptQrCanvas');
        if (!qrCanvas) return;
        const ctx = qrCanvas.getContext('2d');
        ctx.clearRect(0, 0, 112, 112);

        // Simple high-contrast geometric QR pattern for demo
        ctx.fillStyle = '#0F172A';
        ctx.fillRect(0, 0, 112, 112);
        ctx.fillStyle = '#FFFFFF';
        ctx.fillRect(4, 4, 104, 104);

        ctx.fillStyle = '#0F172A';
        // Corner squares
        ctx.fillRect(8, 8, 28, 28);
        ctx.clearRect(12, 12, 20, 20);
        ctx.fillRect(16, 16, 12, 12);

        ctx.fillRect(76, 8, 28, 28);
        ctx.clearRect(80, 12, 20, 20);
        ctx.fillRect(84, 16, 12, 12);

        ctx.fillRect(8, 76, 28, 28);
        ctx.clearRect(12, 80, 20, 20);
        ctx.fillRect(16, 84, 12, 12);

        // Pattern grid
        for (let i = 0; i < 7; i++) {
            for (let j = 0; j < 7; j++) {
                if ((i + j) % 2 === 0) {
                    ctx.fillRect(42 + i * 4, 42 + j * 4, 4, 4);
                }
            }
        }
    }

    window.openReceiptModal = (sessionData) => {
        let plate = '7777 AB-7';
        let driver = 'Иванов И. И.';
        let fuel = currentFuelType || 'АИ-95';
        let liters = 30.00;
        let unitPrice = currentFuelPrice || 2.46;
        let cost = 73.80;
        let dateStr = new Date().toLocaleDateString('ru-RU') + ' ' + new Date().toLocaleTimeString('ru-RU');

        if (sessionData) {
            plate = sessionData.plate_number || plate;
            fuel = sessionData.fuel_type || fuel;
            liters = sessionData.dispensed_liters > 0 ? sessionData.dispensed_liters : 30.0;
            cost = sessionData.total_cost > 0 ? sessionData.total_cost : (liters * unitPrice);
            driver = sessionData.driver_name || (sessionData.is_drive_and_pay ? 'Иванов И. И.' : 'Гостевой клиент');
            if (sessionData.created_at) {
                const d = new Date(sessionData.created_at);
                dateStr = d.toLocaleDateString('ru-RU') + ' ' + d.toLocaleTimeString('ru-RU');
            }
        } else {
            // Read from dashboard
            const curLiters = parseFloat(document.getElementById('dispensedLiters')?.textContent || '0');
            const curCost = parseFloat(document.getElementById('dispensedCost')?.textContent || '0');
            const curPlate = document.getElementById('cardPlate')?.textContent;
            const curDriver = document.getElementById('cardDriverName')?.textContent;

            if (curPlate && curPlate !== '—') plate = curPlate;
            if (curDriver) driver = curDriver;
            if (curLiters > 0) liters = curLiters;
            if (curCost > 0) cost = curCost;
            else cost = liters * unitPrice;
        }

        unitPrice = cost / Math.max(liters, 0.01);
        const receiptId = `REC-BN-${plate.replace(/[^A-Z0-9]/gi, '')}-${Math.floor(Date.now() / 1000)}`;

        document.getElementById('receiptNumber').textContent = receiptId;
        document.getElementById('receiptDate').textContent = dateStr;
        document.getElementById('receiptPlate').textContent = plate;
        document.getElementById('receiptDriver').textContent = driver;
        document.getElementById('receiptFuelItem').textContent = `Топливо ${fuel} (${liters.toFixed(2)} л × ${unitPrice.toFixed(2)} BYN):`;
        document.getElementById('receiptTotalVal').textContent = `${cost.toFixed(2)} BYN`;

        const bonusNum = (cost * 0.10).toFixed(2);
        document.getElementById('receiptBonus').textContent = `+${bonusNum} БОНУСОВ`;

        drawReceiptQr(receiptId);
        document.body.setAttribute('data-print-mode', 'receipt');
        receiptModal?.classList.add('open');
    };

    if (openReceiptBtn) {
        openReceiptBtn.addEventListener('click', () => window.openReceiptModal());
    }

    const btnPrintReceiptPdf = document.getElementById('btnPrintReceiptPdf');
    if (btnPrintReceiptPdf) {
        btnPrintReceiptPdf.addEventListener('click', () => {
            document.body.setAttribute('data-print-mode', 'receipt');
            window.print();
        });
    }

    if (closeReceiptBtn) {
        closeReceiptBtn.addEventListener('click', () => {
            document.body.removeAttribute('data-print-mode');
            receiptModal?.classList.remove('open');
        });
    }
    if (receiptModal) {
        receiptModal.addEventListener('click', (e) => {
            if (e.target === receiptModal) {
                document.body.removeAttribute('data-print-mode');
                receiptModal.classList.remove('open');
            }
        });
    }

    // 8. Snapshot Modal for Audit Log
    const snapshotModal = document.getElementById('snapshotModal');
    const closeSnapshotBtn = document.getElementById('closeSnapshotBtn');

    if (closeSnapshotBtn) {
        closeSnapshotBtn.addEventListener('click', () => {
            snapshotModal?.classList.remove('open');
        });
    }
    if (snapshotModal) {
        snapshotModal.addEventListener('click', (e) => {
            if (e.target === snapshotModal) snapshotModal.classList.remove('open');
        });
    }

    window.openIncidentSnapshot = (plate, disp, desc, timeStr) => {
        const modalImg = document.getElementById('snapshotModalImg');
        const modalDetails = document.getElementById('snapshotModalDetails');
        if (modalImg) {
            // Serve the static snapshot JPEG
            modalImg.src = '/api/snapshots/incident_hose_tear.jpg';
        }
        if (modalDetails) {
            modalDetails.innerHTML = `
                <div class="bg-zinc-900 p-3 rounded-xl border border-zinc-800">
                    <span class="text-zinc-400 block mb-1">Госномер Т/С</span>
                    <span class="font-mono font-bold text-amber-300 text-sm">${plate}</span>
                </div>
                <div class="bg-zinc-900 p-3 rounded-xl border border-zinc-800">
                    <span class="text-zinc-400 block mb-1">Критическое смещение</span>
                    <span class="font-bold text-red-400 text-sm">${disp} px / 300мс (&gt; 15 px)</span>
                </div>
                <div class="col-span-2 bg-zinc-900 p-3 rounded-xl border border-zinc-800">
                    <span class="text-zinc-400 block mb-1">Действие системы безопасности:</span>
                    <span class="text-zinc-200">${desc}. Сигнал E-STOP отправлен на контроллер насоса.</span>
                </div>
            `;
        }
        snapshotModal?.classList.add('open');
    };

    // 8.5. Executive TEO Feasibility Report Modal
    const teoModal = document.getElementById('teoModal');
    const exportReportBtn = document.getElementById('exportReportBtn');
    const closeTeoBtn = document.getElementById('closeTeoBtn');
    const btnPrintTeoPdf = document.getElementById('btnPrintTeoPdf');
    const btnDownloadTeoCsv = document.getElementById('btnDownloadTeoCsv');

    window.updateTeoValues = () => {
        const hoseKpi = document.getElementById('kpi_hose_savings')?.textContent || '192 000 BYN';
        const retailKpi = document.getElementById('kpi_retail_profit')?.textContent || '21 845 250 BYN';
        const netKpi = document.getElementById('kpi_total_effect')?.textContent || '22 006 850 BYN';
        const paybackKpi = document.getElementById('kpi_payback')?.textContent || '0.2 мес.';
        const roiKpi = document.getElementById('kpi_roi_5y')?.textContent || '+28 856%';
        const stationsVal = document.getElementById('slider_station_count')?.value || '570';

        const elScale = document.getElementById('teoScaleVal');
        const elNet = document.getElementById('teoAnnualNetVal');
        const elPayback = document.getElementById('teoPaybackVal');
        const elRoi = document.getElementById('teoRoiVal');
        const elHose = document.getElementById('teoHoseVal');
        const elRetail = document.getElementById('teoRetailVal');
        const elCapex = document.getElementById('teoCapexVal');

        if (elScale) elScale.textContent = `${stationsVal} АЗС`;
        if (elNet) elNet.textContent = netKpi;
        if (elPayback) elPayback.textContent = paybackKpi;
        if (elRoi) elRoi.textContent = roiKpi;
        if (elHose) elHose.textContent = `${hoseKpi} / год`;
        if (elRetail) elRetail.textContent = `${retailKpi} / год`;
        if (elCapex) {
            const stationsNum = parseInt(stationsVal) || 570;
            const capexNum = stationsNum === 570 ? 380000 : (stationsNum === 60 ? 85000 : (stationsNum === 1 ? 6500 : Math.round(stationsNum * 666.67)));
            elCapex.textContent = `${capexNum.toLocaleString('ru-RU')} BYN`;
        }
    };

    window.openTeoModal = () => {
        window.updateTeoValues();
        document.body.setAttribute('data-print-mode', 'teo');
        teoModal?.classList.add('open');
    };

    window.addEventListener('beforeprint', () => {
        if (document.body.getAttribute('data-print-mode') !== 'receipt') {
            window.updateTeoValues();
        }
    });

    if (exportReportBtn) {
        exportReportBtn.addEventListener('click', () => {
            window.openTeoModal();
        });
    }

    if (closeTeoBtn) {
        closeTeoBtn.addEventListener('click', () => {
            document.body.removeAttribute('data-print-mode');
            teoModal?.classList.remove('open');
        });
    }

    if (teoModal) {
        teoModal.addEventListener('click', (e) => {
            if (e.target === teoModal) {
                document.body.removeAttribute('data-print-mode');
                teoModal.classList.remove('open');
            }
        });
    }

    if (btnPrintTeoPdf) {
        btnPrintTeoPdf.addEventListener('click', () => {
            document.body.setAttribute('data-print-mode', 'teo');
            window.print();
        });
    }

    const btnDownloadTeoExcel = document.getElementById('btnDownloadTeoExcel');
    if (btnDownloadTeoExcel) {
        btnDownloadTeoExcel.addEventListener('click', async () => {
            const stationsCount = parseInt(document.getElementById('slider_station_count')?.value) || 570;
            const dailyTraffic = parseInt(document.getElementById('slider_daily_traffic')?.value) || 750;
            const hoseIncidents = parseInt(document.getElementById('slider_hose_incidents')?.value) || 160;
            const hoseCost = parseFloat(document.getElementById('slider_hose_cost')?.value) || 1200.0;
            const retailGrowth = parseFloat(document.getElementById('slider_retail_growth')?.value) || 4.0;

            const stationsNum = stationsCount;
            const capexNum = stationsNum === 570 ? 380000.0 : (stationsNum === 60 ? 85000.0 : (stationsNum === 1 ? 6500.0 : stationsNum * 666.67));

            const params = {
                station_count: stationsCount,
                daily_traffic: dailyTraffic,
                hose_incidents_prevented: hoseIncidents,
                hose_damage_cost: hoseCost,
                retail_growth_pct: retailGrowth,
                retail_avg_check: 25.0,
                retail_margin_pct: 35.0,
                system_capex: capexNum,
                annual_opex_pct: 8.0,
            };

            try {
                const response = await fetch('/api/roi/export-excel', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(params),
                });
                if (!response.ok) throw new Error('Ошибка генерации Excel');

                const blob = await response.blob();
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.setAttribute('href', url);
                link.setAttribute('download', `TEO_SmartVision_Belorusneft_${stationsCount}_AZS.xlsx`);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } catch (err) {
                console.error('Excel export error:', err);
                alert('Не удалось сформировать Excel файл. Проверьте соединение с сервером.');
            }
        });
    }

    if (btnDownloadTeoCsv) {
        btnDownloadTeoCsv.addEventListener('click', () => {
            const stationsVal = document.getElementById('slider_station_count')?.value || '570';
            const hoseKpi = document.getElementById('kpi_hose_savings')?.textContent || '192000 BYN';
            const retailKpi = document.getElementById('kpi_retail_profit')?.textContent || '21845250 BYN';
            const netKpi = document.getElementById('kpi_total_effect')?.textContent || '22006850 BYN';
            const paybackKpi = document.getElementById('kpi_payback')?.textContent || '0.2 мес.';
            const roiKpi = document.getElementById('kpi_roi_5y')?.textContent || '+28856%';

            const csvContent = "\uFEFF" + 
                "Параметр;Значение;Единица измерения\n" +
                `Масштаб внедрения;${stationsVal};АЗС сети ПО «Белоруснефть»\n` +
                `Экономия на обрывах шлангов;${hoseKpi.replace(/\s+BYN/g, '').replace(/\s+/g, '')};BYN/год\n` +
                `Маржинальная прибыль ритейла;${retailKpi.replace(/\s+BYN/g, '').replace(/\s+/g, '')};BYN/год\n` +
                `Совокупный годовой чистый эффект;${netKpi.replace(/\s+BYN/g, '').replace(/\s+/g, '')};BYN/год\n` +
                `Срок окупаемости;${paybackKpi};мес.\n` +
                `5-летний ROI;${roiKpi};%\n` +
                "Сокращение времени заправки;-78;% (с 210с до 45с)\n" +
                "Рост пропускной способности;+24;%\n";

            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.setAttribute('href', url);
            link.setAttribute('download', `TEO_SmartVision_Belorusneft_${Date.now()}.csv`);
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    }

    // 9. WebSocket Client Setup
    function connectWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/telemetry`;

        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('Connected to SmartVision Telemetry Stream.');
            refreshVideoStream();
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
            clearTimeout(reconnectTimer);
            reconnectTimer = setTimeout(connectWebSocket, 2000);
        };
    }

    // 10. Handle Live Telemetry Update
    function handleTelemetryMessage(msg) {
        // Update Canvas Overlays
        canvasRenderer.updateTelemetry(msg.telemetry);

        const fsm = msg.fsm || {};
        const state = fsm.state || 'IDLE';
        const session = fsm.session;
        const telemetry = msg.telemetry || {};
        const simTime = telemetry.sim_time !== undefined ? telemetry.sim_time : 0.0;

        // Update Timeline progress
        if (timelineProgress) {
            const pct = Math.min(100, Math.max(0, (simTime / 50.0) * 100));
            timelineProgress.style.width = `${pct}%`;
        }
        if (timelineTimeText) {
            const sec = Math.floor(simTime);
            timelineTimeText.textContent = `00:${sec < 10 ? '0' + sec : sec} / 00:50`;
        }

        // Audio Triggers & Real-Time Audit Log Refreshes on State Transition
        if (state !== lastKnownState) {
            if (state === 'PLATE_IDENTIFIED' && session?.is_drive_and_pay) {
                window.soundAlerts.playPlateIdentified();
            } else if (state === 'FUELING') {
                window.soundAlerts.playFuelStart();
            } else if (state === 'SESSION_COMPLETE') {
                window.soundAlerts.playFuelComplete();
                loadAuditLogs();
            } else if (state === 'ALARM_LOCKDOWN') {
                loadAuditLogs();
            } else if (state === 'IDLE' && lastKnownState === 'SESSION_COMPLETE') {
                loadAuditLogs();
            }
            lastKnownState = state;
        }

        if (telemetry.is_alarm && !isAlarmActive) {
            window.soundAlerts.playEmergencyAlarm();
            isAlarmActive = true;
            loadAuditLogs();
        } else if (!telemetry.is_alarm && isAlarmActive) {
            window.soundAlerts.stopEmergencyAlarm();
            isAlarmActive = false;
        }

        // Update Cockpit Badges & Panels
        updateFsmBadge(state);
        updateDriveAndPayCard(session, state, telemetry.plate_detected);
        updateFuelMeter(session, state, telemetry);
        updateSafetyPanel(telemetry, state);
    }

    function updateFsmBadge(state) {
        const badge = document.getElementById('fsmStateBadge');
        if (!badge) return;

        const stateConfig = {
            IDLE: { text: 'ОЖИДАНИЕ Т/С', class: 'bg-zinc-800 text-zinc-300 border-zinc-700' },
            VEHICLE_APPROACHING: { text: 'ЗАЕЗД Т/С', class: 'bg-blue-900/60 text-blue-300 border-blue-600' },
            PLATE_IDENTIFIED: { text: 'НОМЕР РАСПОЗНАН', class: 'bg-amber-900/60 text-amber-300 border-amber-500' },
            NOZZLE_INSERTED: { text: 'ПИСТОЛЕТ В БАКЕ', class: 'bg-teal-900/60 text-teal-300 border-teal-500' },
            FUELING: { text: 'ИДЕТ НАЛИВ ТОПЛИВА', class: 'bg-green-900/80 text-green-300 border-green-500' },
            NOZZLE_RETURNED: { text: 'ПИСТОЛЕТ ВОЗВРАЩЕН', class: 'bg-indigo-900/60 text-indigo-300 border-indigo-500' },
            SESSION_COMPLETE: { text: 'ЗАПРАВКА ЗАВЕРШЕНА', class: 'bg-emerald-900/80 text-emerald-300 border-emerald-400' },
            ALARM_LOCKDOWN: { text: 'ТРЕВОГА: НАСОС ЗАБЛОКИРОВАН', class: 'bg-red-700 text-white border-red-500 font-bold' },
        };

        const conf = stateConfig[state] || stateConfig['IDLE'];
        badge.className = `px-3.5 py-1 rounded-full text-xs font-bold uppercase tracking-wider border ${conf.class}`;
        badge.textContent = conf.text;
    }

    function updateDriveAndPayCard(session, state, detectedPlate) {
        const elName = document.getElementById('cardDriverName');
        const elPlate = document.getElementById('cardPlate');
        const elInitials = document.getElementById('cardInitials');
        const elModel = document.getElementById('cardModel');
        const elBalance = document.getElementById('cardBalance');
        const elFuel = document.getElementById('cardFuelType');
        const elDnpStatus = document.getElementById('cardDnpStatus');

        const driverPresets = {
            '7777 AB-7': {
                name: 'Иванов И. И.',
                initials: 'ИИ',
                model: 'Volkswagen Passat B8 (2.0 TSI)',
                balance: 150.00,
                dnp: true,
                fuel: 'АИ-95',
                price: 2.46,
            },
            '1234 IE-7': {
                name: 'Петров П. П.',
                initials: 'ПП',
                model: 'Geely Tugella 2.0T',
                balance: 95.50,
                dnp: true,
                fuel: 'АИ-95',
                price: 2.46,
            },
            '5678 MH-7': {
                name: 'Гостевой клиент',
                initials: 'ГК',
                model: 'Lada Vesta (1.6 MT)',
                balance: 0.00,
                dnp: false,
                fuel: 'АИ-92',
                price: 2.36,
            },
        };

        const activePlate = session?.plate || detectedPlate || '7777 AB-7';
        const preset = driverPresets[activePlate] || {
            name: session?.driver_name || 'Гостевой клиент',
            initials: 'ГК',
            model: session?.model || 'Легковой автомобиль',
            balance: session?.balance !== undefined ? session.balance : 0.00,
            dnp: !!session?.is_drive_and_pay,
            fuel: session?.fuel_type || currentFuelType || 'АИ-95',
            price: session?.price || currentFuelPrice || 2.46,
        };

        const driverName = session?.driver_name && session.driver_name !== 'Гостевой клиент' ? session.driver_name : preset.name;
        const carModel = session?.model && session.model !== '—' && session.model !== 'Легковой автомобиль' ? session.model : preset.model;
        const driverBalance = session?.balance !== undefined && session.balance > 0 ? session.balance : preset.balance;
        const isDnp = session ? session.is_drive_and_pay : preset.dnp;
        const fuelName = session?.fuel_type || preset.fuel;
        const fuelPrice = session?.price || preset.price;

        if (elPlate) elPlate.textContent = activePlate;
        if (elName) elName.textContent = driverName;
        if (elInitials) elInitials.textContent = preset.initials;
        if (elModel) elModel.textContent = carModel;
        if (elBalance) elBalance.textContent = `${driverBalance.toFixed(2)} BYN`;
        if (elFuel) elFuel.textContent = `${fuelName} (${fuelPrice.toFixed(2)} BYN/л)`;

        if (elDnpStatus) {
            if (isDnp) {
                elDnpStatus.className = 'inline-flex items-center px-2.5 py-0.5 rounded text-xs font-bold bg-green-500/20 text-green-400 border border-green-500/40';
                elDnpStatus.textContent = 'Drive&Pay: Активен (Zero-Click)';
            } else {
                elDnpStatus.className = 'inline-flex items-center px-2.5 py-0.5 rounded text-xs font-bold bg-amber-500/20 text-amber-400 border border-amber-500/40';
                elDnpStatus.textContent = 'Гостевой режим (Оплата на кассе)';
            }
        }
    }

    function updateFuelMeter(session, state, telemetry) {
        const elTitle = document.getElementById('fuelMeterHeaderTitle');
        const elCardBox = document.getElementById('fuelMeterCardBox');
        const elLiters = document.getElementById('dispensedLiters');
        const elCost = document.getElementById('dispensedCost');
        const elTarget = document.getElementById('targetLiters');
        const elBar = document.getElementById('fuelProgressBar');

        const isAlarm = state === 'ALARM_LOCKDOWN' || (telemetry && telemetry.is_alarm);

        if (isAlarm) {
            if (elTitle) elTitle.innerHTML = '<span class="text-red-400 font-bold uppercase tracking-wider animate-pulse">⛔ НАЛИВ ЗАБЛОКИРОВАН (E-STOP)</span>';
            if (elCardBox) elCardBox.className = 'bg-red-950/70 p-4 rounded-xl border-2 border-red-500 mb-3 text-center shadow-lg shadow-red-500/20';
            if (elCost) elCost.className = 'text-lg font-bold text-red-400 telemetry-val mt-1';
            if (elBar) elBar.className = 'bg-red-600 h-full transition-all duration-200 shadow-md shadow-red-500/50';
            if (session) {
                const liters = session.dispensed_liters || 0.0;
                const cost = session.total_cost || 0.0;
                if (elLiters) elLiters.textContent = liters.toFixed(2);
                if (elCost) elCost.textContent = `${cost.toFixed(2)} BYN [E-STOP]`;
            }
            return;
        }

        // Normal States
        if (elCardBox) elCardBox.className = 'bg-[#0F172A] p-4 rounded-xl border border-zinc-800 mb-3 text-center transition-colors duration-300';
        if (elCost) elCost.className = 'text-lg font-bold text-emerald-400 telemetry-val mt-1';
        if (elBar) elBar.className = 'bg-gradient-to-r from-[#00843D] to-[#00E676] h-full transition-all duration-200';

        if (state === 'FUELING') {
            if (elTitle) elTitle.innerHTML = '<span class="text-emerald-400 font-bold uppercase tracking-wider animate-pulse">⚡ ИДЕТ НАЛИВ ТОПЛИВА</span>';
        } else if (state === 'SESSION_COMPLETE') {
            if (elTitle) elTitle.innerHTML = '<span class="text-emerald-400 font-bold uppercase tracking-wider">✓ НАЛИВ ЗАВЕРШЕН</span>';
        } else {
            if (elTitle) elTitle.innerHTML = '<span class="text-zinc-400 font-bold uppercase tracking-wider">Налив топлива в реальном времени</span>';
        }

        if (session && state !== 'IDLE') {
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
            if (elTarget) elTarget.textContent = '30.0 л';
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
            elMsg.textContent = telemetry.safety_message || 'Мониторинг риска обрыва шланга активен. Порог срабатывания: > 15 px.';
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

    // 11. Simulator Controls & Action Buttons
    const scenarioBtns = document.querySelectorAll('.scenario-btn');
    scenarioBtns.forEach((btn) => {
        btn.addEventListener('click', async () => {
            const action = btn.getAttribute('data-action');
            try {
                await fetch(`/api/simulator/control?action=${action}`, { method: 'POST' });
            } catch (e) {
                console.error('Failed to switch scenario:', e);
            }
        });
    });



    // 12. Audit Logs Fetch & Filter
    async function loadAuditLogs() {
        try {
            const [sessRes, incRes] = await Promise.all([
                fetch('/api/sessions'),
                fetch('/api/incidents'),
            ]);

            if (sessRes.ok) {
                const sessData = await sessRes.json();
                const rawSessions = Array.isArray(sessData) ? sessData : (sessData.sessions || []);
                cachedSessions = rawSessions.map(s => ({
                    ...s,
                    plate_number: s.vehicle_plate || s.plate_number || '—',
                    is_drive_and_pay: s.is_zero_click !== undefined ? s.is_zero_click : (s.is_drive_and_pay || false),
                    dispensed_liters: typeof s.dispensed_liters === 'number' ? s.dispensed_liters : parseFloat(s.dispensed_liters || 0),
                    total_cost: typeof s.total_cost === 'number' ? s.total_cost : parseFloat(s.total_cost || 0),
                }));
            }
            if (incRes.ok) {
                const incData = await incRes.json();
                cachedIncidents = Array.isArray(incData) ? incData : (incData.incidents || []);
            }

            renderFilteredAuditLogs();
        } catch (e) {
            console.error('Failed to load audit logs:', e);
        }
    }

    // Auto-refresh audit logs every 3s when audit tab is visible
    setInterval(() => {
        const auditTab = document.getElementById('tab-audit');
        if (auditTab && !auditTab.classList.contains('hidden')) {
            loadAuditLogs();
        }
    }, 3000);

    function renderFilteredAuditLogs() {
        const searchVal = (document.getElementById('auditSearchInput')?.value || '').toLowerCase();
        const severityFilter = document.getElementById('auditSeverityFilter')?.value || 'ALL';

        // Render Sessions Table
        const sessionsTbody = document.getElementById('sessionsTableBody');
        if (sessionsTbody) {
            sessionsTbody.innerHTML = '';
            const filteredSessions = cachedSessions.filter((s) => {
                const matchesSearch = !searchVal || (s.plate_number || '').toLowerCase().includes(searchVal);
                let matchesSeverity = true;
                if (severityFilter === 'ZERO_CLICK') matchesSeverity = s.is_drive_and_pay;
                else if (severityFilter === 'GUEST') matchesSeverity = !s.is_drive_and_pay;
                return matchesSearch && matchesSeverity;
            });

            if (filteredSessions.length === 0) {
                sessionsTbody.innerHTML = `<tr><td colspan="8" class="px-4 py-8 text-center text-zinc-500 font-medium">Ожидание завершения транзакций (мониторинг ТРК №2 активен в реальном времени)...</td></tr>`;
            } else {
                filteredSessions.forEach((s, idx) => {
                    const row = document.createElement('tr');
                    row.className = s.created_at === 'Сейчас (Live)' ? 'bg-emerald-950/20 border-l-2 border-emerald-500 hover:bg-emerald-950/30 transition-colors' : 'hover:bg-zinc-800/50 transition-colors';
                    const timeStr = s.created_at === 'Сейчас (Live)' 
                        ? `<span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 animate-pulse">● LIVE</span>`
                        : (s.created_at || '—');
                    const dnpBadge = s.is_drive_and_pay
                        ? `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-green-500/20 text-green-400 border border-green-500/30">Zero-Click</span>`
                        : `<span class="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">Гость</span>`;

                    row.innerHTML = `
                        <td class="px-4 py-3 font-mono text-[11px] text-zinc-400">${(s.session_uuid || '').slice(0, 8)}...</td>
                        <td class="px-4 py-3 font-bold font-mono text-white">${s.plate_number}</td>
                        <td class="px-4 py-3 text-zinc-300">${s.fuel_type}</td>
                        <td class="px-4 py-3 font-mono text-zinc-200">${s.dispensed_liters.toFixed(2)} л</td>
                        <td class="px-4 py-3 font-bold text-emerald-400 font-mono">${s.total_cost.toFixed(2)} BYN</td>
                        <td class="px-4 py-3">${dnpBadge}</td>
                        <td class="px-4 py-3 font-mono text-zinc-300">${timeStr}</td>
                        <td class="px-4 py-3">
                            <button class="row-receipt-btn text-xs text-amber-400 font-bold hover:underline" data-idx="${idx}">Чек 🧾</button>
                        </td>
                    `;
                    sessionsTbody.appendChild(row);
                });

                document.querySelectorAll('.row-receipt-btn').forEach((btn) => {
                    btn.addEventListener('click', () => {
                        const idx = parseInt(btn.getAttribute('data-idx'));
                        window.openReceiptModal(filteredSessions[idx]);
                    });
                });
            }
        }

        // Render Incidents Table
        const incidentsTbody = document.getElementById('incidentsTableBody');
        if (incidentsTbody) {
            incidentsTbody.innerHTML = '';
            const filteredIncidents = cachedIncidents.filter((inc) => {
                const matchesSearch = !searchVal || (inc.description || '').toLowerCase().includes(searchVal);
                let matchesSeverity = true;
                if (severityFilter === 'CRITICAL') matchesSeverity = inc.severity === 'CRITICAL';
                return matchesSearch && matchesSeverity;
            });

            if (filteredIncidents.length === 0) {
                incidentsTbody.innerHTML = `<tr><td colspan="5" class="px-4 py-8 text-center text-zinc-500 font-medium">Инцидентов не зафиксировано. Комплекс безопасности ТРК №2 активен в штатном режиме.</td></tr>`;
            } else {
                filteredIncidents.forEach((inc, idx) => {
                    const row = document.createElement('tr');
                    row.className = 'hover:bg-red-950/30 transition-colors';
                    const timeStr = inc.created_at || '—';

                    row.innerHTML = `
                        <td class="px-4 py-3 font-bold text-red-400">${inc.incident_type}</td>
                        <td class="px-4 py-3 text-zinc-200 text-xs">${inc.description}</td>
                        <td class="px-4 py-3 font-bold font-mono text-red-300">${(inc.displacement_px || 0).toFixed(1)} px</td>
                        <td class="px-4 py-3 font-mono text-zinc-400">${timeStr}</td>
                        <td class="px-4 py-3">
                            <button class="row-snapshot-btn px-2 py-1 rounded bg-red-900/60 hover:bg-red-800 text-white font-bold text-[11px] border border-red-700" data-idx="${idx}">
                                📷 Просмотр
                            </button>
                        </td>
                    `;
                    incidentsTbody.appendChild(row);
                });

                document.querySelectorAll('.row-snapshot-btn').forEach((btn) => {
                    btn.addEventListener('click', () => {
                        const idx = parseInt(btn.getAttribute('data-idx'));
                        const inc = filteredIncidents[idx];
                        const timeStr = inc.created_at ? new Date(inc.created_at).toLocaleTimeString('ru-RU') : '—';
                        window.openIncidentSnapshot('1234 IE-7', inc.displacement_px, inc.description, timeStr);
                    });
                });
            }
        }
    }

    // Search and Filter Listeners
    const auditSearch = document.getElementById('auditSearchInput');
    const auditFilter = document.getElementById('auditSeverityFilter');
    const btnClearAuditLogs = document.getElementById('btnClearAuditLogs');

    if (auditSearch) auditSearch.addEventListener('input', renderFilteredAuditLogs);
    if (auditFilter) auditFilter.addEventListener('change', renderFilteredAuditLogs);
    if (btnClearAuditLogs) {
        btnClearAuditLogs.addEventListener('click', async () => {
            if (!confirm('Очистить все записи журнала сессий и инцидентов?')) return;
            try {
                const res = await fetch('/api/audit/clear', { method: 'POST' });
                if (res.ok) {
                    cachedSessions = [];
                    cachedIncidents = [];
                    renderFilteredAuditLogs();
                }
            } catch (err) {
                console.error('Failed to clear audit logs:', err);
            }
        });
    }

    // Initial WebSocket Connection
    connectWebSocket();
});
