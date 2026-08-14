/**
 * Interactive ROI Calculator Widget for SmartVision AZS.
 * Live recalculation of financial effect, payback horizon, and Chart.js visualizations.
 */
class ROICalculatorWidget {
    constructor() {
        this.cashflowChart = null;
        this.structureChart = null;
        this.init();
    }

    init() {
        this.bindSliders();
        this.initCharts();
        this.recalculate();
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
            system_capex: 380000.0,
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
        const fmt = (v) => Math.round(v).toLocaleString('ru-RU');

        const elHose = document.getElementById('kpi_hose_savings');
        const elRetail = document.getElementById('kpi_retail_profit');
        const elTotal = document.getElementById('kpi_total_effect');
        const elPayback = document.getElementById('kpi_payback');
        const elRoi5 = document.getElementById('kpi_roi_5y');

        if (elHose) elHose.textContent = `${fmt(summary.annual_hose_savings)} BYN`;
        if (elRetail) elRetail.textContent = `${fmt(summary.annual_retail_extra_profit)} BYN`;
        if (elTotal) elTotal.textContent = `${fmt(summary.annual_net_benefit || summary.annual_gross_benefit)} BYN`;
        if (elPayback) elPayback.textContent = `${summary.payback_months} мес.`;
        if (elRoi5) elRoi5.textContent = `+${summary.roi_5_year_pct}%`;
    }

    initCharts() {
        // Chart 1: 5-Year Cumulative Cash Flow
        const ctx1 = document.getElementById('chart_cashflow')?.getContext('2d');
        if (ctx1 && window.Chart) {
            this.cashflowChart = new Chart(ctx1, {
                type: 'bar',
                data: {
                    labels: ['Старт', 'Год 1', 'Год 2', 'Год 3', 'Год 4', 'Год 5'],
                    datasets: [
                        {
                            label: 'Накопленный денежный поток (BYN)',
                            data: [0, 0, 0, 0, 0, 0],
                            backgroundColor: [
                                'rgba(239, 68, 68, 0.7)',
                                'rgba(0, 132, 61, 0.7)',
                                'rgba(0, 132, 61, 0.7)',
                                'rgba(0, 132, 61, 0.8)',
                                'rgba(0, 132, 61, 0.9)',
                                'rgba(0, 132, 61, 1.0)',
                            ],
                            borderColor: '#00843D',
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
                                label: (ctx) => `Накопленный эффект: ${Math.round(ctx.parsed.y).toLocaleString('ru-RU')} BYN`,
                            },
                        },
                    },
                    scales: {
                        y: {
                            grid: { color: 'rgba(255, 255, 255, 0.08)' },
                            ticks: {
                                color: '#94A3B8',
                                callback: (v) => `${(v / 1000).toFixed(0)}k`,
                            },
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#94A3B8' },
                        },
                    },
                },
            });
        }

        // Chart 2: Structure of Annual Economic Effect
        const ctx2 = document.getElementById('chart_structure')?.getContext('2d');
        if (ctx2 && window.Chart) {
            this.structureChart = new Chart(ctx2, {
                type: 'doughnut',
                data: {
                    labels: ['Предотвращение обрывов шлангов', 'Прирост чека ритейла (ликвидация очередей)'],
                    datasets: [
                        {
                            data: [192000, 436900],
                            backgroundColor: ['#FFCC00', '#00843D'],
                            borderColor: '#0F172A',
                            borderWidth: 3,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                color: '#E2E8F0',
                                font: { size: 12 },
                                padding: 15,
                            },
                        },
                    },
                },
            });
        }
    }

    updateCharts(summary) {
        if (this.cashflowChart && summary.cash_flow_years) {
            const dataPts = summary.cash_flow_years.map((y) => y.cumulative);
            this.cashflowChart.data.datasets[0].data = dataPts;
            this.cashflowChart.data.datasets[0].backgroundColor = dataPts.map((v) =>
                v < 0 ? 'rgba(239, 68, 68, 0.7)' : 'rgba(0, 132, 61, 0.85)'
            );
            this.cashflowChart.update();
        }

        if (this.structureChart) {
            this.structureChart.data.datasets[0].data = [
                summary.annual_hose_savings,
                summary.annual_retail_extra_profit,
            ];
            this.structureChart.update();
        }
    }
}

window.ROICalculatorWidget = ROICalculatorWidget;
