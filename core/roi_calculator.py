"""
Financial and Economic ROI Model for SmartVision AZS Deployment.
Calculates hose tear prevention savings, retail non-fuel turnover expansion,
cumulative 5-year cash flows, net present value (NPV), and payback horizon.
"""
from dataclasses import dataclass
from typing import Dict, List, Any
from pydantic import BaseModel, Field

from config import settings


class ROIParams(BaseModel):
    station_count: int = Field(default=settings.DEFAULT_STATION_COUNT, ge=1, le=2000, description="Количество АЗС в сети")
    daily_traffic: int = Field(default=settings.DEFAULT_DAILY_TRAFFIC, ge=50, le=5000, description="Среднесуточный трафик авто на 1 АЗС")
    hose_incidents_prevented: int = Field(
        default=settings.DEFAULT_HOSE_INCIDENTS_YEAR, ge=0, le=2000, description="Предотвращено обрывов шлангов на всю сеть в год"
    )
    hose_damage_cost: float = Field(
        default=settings.DEFAULT_HOSE_DAMAGE_COST, ge=100.0, le=10000.0, description="Средний прямой ущерб от одного обрыва (BYN)"
    )
    retail_growth_pct: float = Field(
        default=settings.DEFAULT_RETAIL_GROWTH_PCT, ge=0.0, le=30.0, description="Рост чека ритейла за счет ликвидации очередей (%)"
    )
    retail_avg_check: float = Field(
        default=settings.DEFAULT_RETAIL_AVERAGE_CHECK, ge=1.0, le=100.0, description="Средний чек сопутствующих товаров (BYN)"
    )
    retail_margin_pct: float = Field(
        default=settings.DEFAULT_RETAIL_MARGIN_PCT, ge=5.0, le=60.0, description="Торговая наценка / маржинальность ритейла (%)"
    )
    system_capex: float = Field(
        default=settings.DEFAULT_SYSTEM_CAPEX, ge=10000.0, le=5000000.0, description="Капитальные затраты на внедрение системы (BYN)"
    )
    annual_opex_pct: float = Field(
        default=8.0, ge=0.0, le=30.0, description="Ежегодные затраты на поддержку и серверы (% от Capex)"
    )


@dataclass
class ROIFinancialSummary:
    annual_hose_savings: float
    annual_retail_extra_profit: float
    annual_gross_benefit: float
    annual_opex: float
    annual_net_benefit: float
    payback_months: float
    roi_5_year_pct: float
    cash_flow_years: List[Dict[str, Any]]
    monthly_breakdown: Dict[str, float]


class ROICalculator:
    @staticmethod
    def calculate(params: ROIParams) -> ROIFinancialSummary:
        """
        Execute economic formulas for fuel network deployment.
        """
        # 1. Savings on equipment damage from hose tears (BYN/year)
        # S_tears = N_incidents * Cost_damage
        annual_hose_savings = params.hose_incidents_prevented * params.hose_damage_cost

        # 2. Non-fuel retail additional gross margin from zero-click line speedup (BYN/year)
        # Total annual vehicles across entire chain = Stations * DailyTraffic * 365
        total_annual_vehicles = params.station_count * params.daily_traffic * 365
        
        # Incremental retail spend per vehicle visit
        # Delta_spend = AvgCheck * (GrowthPct / 100)
        # Margin portion = Delta_spend * (MarginPct / 100)
        extra_margin_per_visit = (
            params.retail_avg_check * (params.retail_growth_pct / 100.0) * (params.retail_margin_pct / 100.0)
        )
        annual_retail_extra_profit = total_annual_vehicles * extra_margin_per_visit

        # 3. Total Annual Benefit
        annual_gross_benefit = annual_hose_savings + annual_retail_extra_profit
        annual_opex = params.system_capex * (params.annual_opex_pct / 100.0)
        annual_net_benefit = annual_gross_benefit - annual_opex

        # 4. Payback Horizon in Months
        if annual_net_benefit > 0:
            payback_months = round((params.system_capex / (annual_net_benefit / 12.0)), 1)
        else:
            payback_months = 999.0

        # 5. 5-Year Cumulative Cash Flow Projections
        cash_flow_years = []
        cumulative = -params.system_capex

        cash_flow_years.append({
            "year": 0,
            "label": "Старт (Capex)",
            "capex": params.system_capex,
            "benefit": 0.0,
            "opex": 0.0,
            "net": -params.system_capex,
            "cumulative": cumulative,
        })

        for year in range(1, 6):
            net_year = annual_net_benefit
            cumulative += net_year
            cash_flow_years.append({
                "year": year,
                "label": f"Год {year}",
                "capex": 0.0,
                "benefit": round(annual_gross_benefit, 2),
                "opex": round(annual_opex, 2),
                "net": round(net_year, 2),
                "cumulative": round(cumulative, 2),
            })

        # 5-Year ROI %
        five_year_total_net = (annual_net_benefit * 5) - params.system_capex
        roi_5_year_pct = round((five_year_total_net / params.system_capex) * 100.0, 1)

        monthly_breakdown = {
            "hose_savings_month": round(annual_hose_savings / 12.0, 2),
            "retail_profit_month": round(annual_retail_extra_profit / 12.0, 2),
            "gross_benefit_month": round(annual_gross_benefit / 12.0, 2),
            "net_benefit_month": round(annual_net_benefit / 12.0, 2),
        }

        return ROIFinancialSummary(
            annual_hose_savings=round(annual_hose_savings, 2),
            annual_retail_extra_profit=round(annual_retail_extra_profit, 2),
            annual_gross_benefit=round(annual_gross_benefit, 2),
            annual_opex=round(annual_opex, 2),
            annual_net_benefit=round(annual_net_benefit, 2),
            payback_months=payback_months,
            roi_5_year_pct=roi_5_year_pct,
            cash_flow_years=cash_flow_years,
            monthly_breakdown=monthly_breakdown,
        )
