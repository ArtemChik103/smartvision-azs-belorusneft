/**
 * Interactive ROI Calculator Widget for SmartVision AZS.
 * Live recalculation of financial effect, payback horizon, scale presets, and Chart.js visualizations.
 */
class ROICalculatorWidget {
    constructor() {
        this.cashflowChart = null;
        this.structureChart = null;
        this.currentCapex = 380000.0;
        this.init();
    }

    init() {
        this.bindSliders();
        this.bindPresets();
        this.initCharts();
        this.recalculate();
    }

    bindPresets() {
        const btnPilot = document.getElementById('presetPilot');
        const btnRegion = document.getElementById('presetRegion');
        const btnNetwork = document.getElementById('presetNetwork');

        const presetBtns = [btnPilot, btnRegion, btnNetwork];

        const setPreset = (stations, traffic, incidents, capex, activeBtn) => {
            presetBtns.forEach((b) => {
                if (b) {
                    b.className = 'scale-preset-btn tactile-btn px-3.5 py-1.5 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-xs font-semibold text-zinc-300 border border-zinc-700';
                }
            });
            if (activeBtn) {
                activeBtn.className = 'scale-preset-btn active tactile-btn px-3.5 py-1.5 rounded-lg bg-[#00843D] text-white font-bold text-xs border border-[#00A84E] shadow-md';
            }

            const sStation = document.getElementById('slider_station_count');
            const sTraffic = document.getElementById('slider_daily_traffic');
            const sIncidents = document.getElementById('slider_hose_incidents');

            if (sStation) {
                sStation.value = stations;
                this.updateSliderLabel('station_count', stations);
            }
            if (sTraffic) {
                sTraffic.value = traffic;
                this.updateSliderLabel('daily_traffic', traffic);
            }
            if (sIncidents) {
                sIncidents.value = incidents;
                this.updateSliderLabel('hose_incidents', incidents);
            }

            this.currentCapex = capex;
            this.recalculate();
        };

        if (btnPilot) {
            btnPilot.addEventListener('click', () => setPreset(1, 750, 1, 6500.0, btnPilot));
        }
        if (btnRegion) {
            btnRegion.addEventListener('click', () => setPreset(60, 750, 25, 85000.0, btnRegion));
        }
        if (btnNetwork) {
            btnNetwork.addEventListener('click', () => setPreset(570, 750, 160, 380000.0, btnNetwork));
        }
    }

    bindSliders() {
        const sliders = [
            'station_count',
            'daily_traffic',
            'hose_incidents',
            'hose_cost',
            'retail_growth',
        ];

        sliders.forEach((id) => {
            const el = document.getElementById(`slider_${id}`);
            if (el) {
                el.addEventListener('input', () => {
                    this.updateSliderLabel(id, el.value);
                    this.recalculate();
                });
            }
        });
    }

    updateSliderLabel(id, value) {
        const label = document.getElementById(`val_${id}`);
        if (!label) return;

        if (id === 'retail_growth') {
            label.textContent = `+${parseFloat(value).toFixed(1)}%`;
        } else if (id === 'hose_cost') {
            label.textContent = `${parseInt(value).toLocaleString('ru-RU')} BYN`;
        } else {
            label.textContent = parseInt(value).toLocaleString('ru-RU');
        }
    }

    getParams() {
        return {
            station_count: parseInt(document.getElementById('slider_station_count')?.value || 570),
            daily_traffic: parseInt(document.getElementById('slider_daily_traffic')?.value || 750),
            hose_incidents_prevented: parseInt(document.getElementById('slider_hose_incidents')?.value || 160),
            hose_damage_cost: parseFloat(document.getElementById('slider_hose_cost')?.value || 1200),
            retail_growth_pct: parseFloat(document.getElementById('slider_retail_growth')?.value || 4.0),
            retail_avg_check: 12.50,
            retail_margin_pct: 28.0,
            system_capex: this.currentCapex,
            annual_opex_pct: 8.0,
        };
    }

    async recalculate() {
        const params = this.getParams();

        try {
            const response = await fetch('/api/roi/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params),
            });

            if (!response.ok) throw new Error('ROI API error');
            const data = await response.json();
            this.updateUI(data.summary);
            this.updateCharts(data.summary);
        } catch (e) {
            // Client-side fallback calculation
            const sHose = params.hose_incidents_prevented * params.hose_damage_cost;
            const totalVehicles = params.station_count * params.daily_traffic * 365;
            const sRetail = totalVehicles * (params.retail_avg_check * (params.retail_growth_pct / 100) * (params.retail_margin_pct / 100));
            const gross = sHose + sRetail;
            const opex = params.system_capex * 0.08;
            const net = gross - opex;
            const payback = net > 0 ? (params.system_capex / (net / 12)).toFixed(1) : '999';

            this.updateUI({
                annual_hose_savings: sHose,
                annual_retail_extra_profit: sRetail,
                annual_gross_benefit: gross,
                annual_net_benefit: net,
                payback_months: parseFloat(payback),
                roi_5_year_pct: Math.round(((net * 5 - params.system_capex) / params.system_capex) * 100),
                cash_flow_years: [
                    { year: 0, cumulative: -params.system_capex },
                    { year: 1, cumulative: -params.system_capex + net },
                    { year: 2, cumulative: -params.system_capex + net * 2 },
                    { year: 3, cumulative: -params.system_capex + net * 3 },
                    { year: 4, cumulative: -params.system_capex + net * 4 },
                    { year: 5, cumulative: -params.system_capex + net * 5 },
                ],
            });
        }
    }

    updateUI(summary) {
        const setVal = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val;
        };

        const formatBYN = (num) => `${Math.round(num).toLocaleString('ru-RU')} BYN`;

        setVal('kpi_hose_savings', formatBYN(summary.annual_hose_savings));
        setVal('kpi_retail_profit', formatBYN(summary.annual_retail_extra_profit));
        setVal('kpi_total_effect', formatBYN(summary.annual_net_benefit));
        setVal('kpi_payback', `${summary.payback_months.toFixed(1)} мес.`);
        setVal('kpi_roi_5y', `+${Math.round(summary.roi_5_year_pct)}%`);
    }

    initCharts() {
        // Chart 1: Cash Flow
        const ctx1 = document.getElementById('chart_cashflow');
        if (ctx1) {
            this.cashflowChart = new Chart(ctx1, {
                type: 'bar',
                data: {
                    labels: ['Год 0 (Capex)', 'Год 1', 'Год 2', 'Год 3', 'Год 4', 'Год 5'],
                    datasets: [
                        {
                            label: 'Накопленный денежный поток (BYN)',
                            data: [-380000, 218505, 817010, 1415515, 2014020, 2612525],
                            backgroundColor: [
                                'rgba(239, 68, 68, 0.75)',
                                'rgba(52, 211, 153, 0.75)',
                                'rgba(16, 185, 129, 0.85)',
                                'rgba(5, 150, 105, 0.9)',
                                'rgba(4, 120, 87, 0.95)',
                                'rgba(6, 95, 70, 1)',
                            ],
                            borderColor: [
                                '#EF4444',
                                '#34D399',
                                '#10B981',
                                '#059669',
                                '#047857',
                                '#065F46',
                            ],
                            borderWidth: 1.5,
                            borderRadius: 6,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            callbacks: {
                                label: (item) => ` ${Math.round(item.raw).toLocaleString('ru-RU')} BYN`,
                            },
                        },
                    },
                    scales: {
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.06)' },
                            ticks: {
                                color: '#94A3B8',
                                font: { family: 'monospace' },
                                callback: (v) => `${(v / 1000).toFixed(0)}k BYN`,
                            },
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#CBD5E1', font: { weight: 'bold' } },
                        },
                    },
                },
            });
        }

        // Chart 2: Structure
        const ctx2 = document.getElementById('chart_structure');
        if (ctx2) {
            this.structureChart = new Chart(ctx2, {
                type: 'doughnut',
                data: {
                    labels: ['Экономия на обрывах шлангов', 'Дополнительная маржа ритейла', 'Операционные расходы (Opex)'],
                    datasets: [
                        {
                            data: [192000, 436905, 30400],
                            backgroundColor: ['#FFCC00', '#00843D', '#EF4444'],
                            borderWidth: 2,
                            borderColor: '#18181B',
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: { color: '#E2E8F0', boxWidth: 12, font: { size: 11 } },
                        },
                        tooltip: {
                            callbacks: {
                                label: (item) => ` ${item.label}: ${Math.round(item.raw).toLocaleString('ru-RU')} BYN`,
                            },
                        },
                    },
                    cutout: '65%',
                },
            });
        }
    }

    updateCharts(summary) {
        if (this.cashflowChart && summary.cash_flow_years) {
            const dataVals = summary.cash_flow_years.map((y) => Math.round(y.cumulative));
            this.cashflowChart.data.datasets[0].data = dataVals;
            this.cashflowChart.update();
        }

        if (this.structureChart) {
            const opexVal = summary.system_capex ? summary.system_capex * 0.08 : 30400;
            this.structureChart.data.datasets[0].data = [
                Math.round(summary.annual_hose_savings),
                Math.round(summary.annual_retail_extra_profit),
                Math.round(opexVal),
            ];
            this.structureChart.update();
        }
    }
}

window.ROICalculatorWidget = ROICalculatorWidget;
