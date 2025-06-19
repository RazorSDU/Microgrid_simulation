from __future__ import annotations

from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from Microgrid_simulation import (
    ExcelDataLoader,
    HeatPumpType,
    MicrogridSimulator,
    SystemParameters,
)

__all__: List[str] = ["run_and_plot"]

# ════════════════════════════════════════════════════════════════════════════
# ── Internal helpers ─────────────────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════════════════

def _daily_sum(series: pd.Series) -> pd.Series:
    """Return a new Series with one value per day (sum of 24 hours)."""
    return (
        series.reset_index(drop=True)
        .groupby(np.arange(len(series)) // 24)
        .sum()
    )


def _rolling_mean(series: pd.Series, window: int = 24) -> pd.Series:
    return series.rolling(window=window, center=True, min_periods=1).mean()


def _compute_electricity_split(res: pd.DataFrame) -> pd.DataFrame:
    """Compute *hourly* contributions whose *daily sums* will be stacked."""
    load = res["load"]
    batt = res["p_bat_discharge"].clip(lower=0)
    fc   = res["p_fc"].clip(lower=0)
    grid = res["p_grid_import"].clip(lower=0)

    # PV contribution is whatever remains to cover the load
    pv = (load - batt - fc - grid).clip(lower=0)

    split = pd.DataFrame(
        {
            "PV": pv,
            "Battery": batt,
            "Fuel‑cell": fc,
            "Grid import": grid,
        }
    )
    return split

# ════════════════════════════════════════════════════════════════════════════
# ── Plot functions  ──────────────────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════════════════

def _plot_surplus_deficit(res: pd.DataFrame) -> None:
    net = res["net_before"]
    net_smoothed = _rolling_mean(net)

    fig, ax = plt.subplots(num="Surplus‑Deficit Power", figsize=(8, 4))

    # Positive (surplus) and negative (deficit) areas separately
    ax.fill_between(
        net.index,
        0,
        net.where(net >= 0, 0),
        alpha=0.3,
        label="Surplus",
        step="mid",
    )
    ax.fill_between(
        net.index,
        0,
        net.where(net < 0, 0),
        alpha=0.3,
        label="Deficit",
        step="mid",
    )

    ax.plot(net_smoothed, linewidth=0.8, label="24 h mean")

    ax.set(title="Hourly Surplus and Deficit", xlabel="Hour of year", ylabel="Power [kW]")
    ax.axhline(0, linestyle="--", linewidth=0.7)
    ax.legend()
    fig.tight_layout()


def _plot_storage_combined(res: pd.DataFrame, p: SystemParameters) -> None:
    soc_pct = 100 * res["soc_bat"] / p.battery_capacity_kwh
    h2_kwh = res["h2_store"]
    fig, ax1 = plt.subplots(num="Storage Levels (Combined)", figsize=(9, 4))
    ax1.plot(soc_pct, label="Battery SoC [%]", linewidth=0.8)
    ax1.set_ylabel("Battery SoC [%]", color=ax1.lines[-1].get_color())
    ax1.tick_params(axis="y", labelcolor=ax1.lines[-1].get_color())
    ax2 = ax1.twinx()
    ax2.plot(h2_kwh, label="H₂ store [kWh]", linewidth=0.8, linestyle="--")
    ax2.set_ylabel("H₂ store [kWh]", color=ax2.lines[-1].get_color())
    ax2.tick_params(axis="y", labelcolor=ax2.lines[-1].get_color())
    ax1.set(title="Battery and Hydrogen Storage State", xlabel="Hour of year")
    fig.tight_layout()


def _plot_battery_only(res: pd.DataFrame, p: SystemParameters) -> None:
    soc_pct = 100 * res["soc_bat"] / p.battery_capacity_kwh
    fig, ax = plt.subplots(num="Battery SoC", figsize=(9, 3.5))
    ax.plot(soc_pct, linewidth=0.8)
    ax.set(title="Battery State of Charge", xlabel="Hour of year", ylabel="SoC [%]")
    ax.set_ylim(0, 100)
    fig.tight_layout()


def _plot_h2_only(res: pd.DataFrame) -> None:
    h2_kwh = res["h2_store"]
    fig, ax = plt.subplots(num="Hydrogen Storage", figsize=(9, 3.5))
    ax.plot(h2_kwh, linewidth=0.8)
    ax.set(title="Hydrogen Storage Level", xlabel="Hour of year", ylabel="Energy [kWh]")
    ax.set_ylim(0, h2_kwh.max() * 1.05)
    fig.tight_layout()


def _plot_heat_distribution(res: pd.DataFrame) -> None:
    hp_heat_daily = _daily_sum(res["heat_pump_heat"])
    fc_heat_daily = _daily_sum(res["heat_from_fc"])

    fig, ax = plt.subplots(num="Daily Heat Distribution", figsize=(8, 4))
    ax.stackplot(
        hp_heat_daily.index,
        hp_heat_daily,
        fc_heat_daily,
        labels=["Heat‑pump", "Fuel‑cell waste heat"],
        step="mid",
    )
    ax.set(
        title="Daily Heat Supply Distribution",
        xlabel="Day of year",
        ylabel="Heat [kWhₜₕ]",
    )
    ax.legend(loc="upper right")
    fig.tight_layout()


def _plot_electricity_distribution(res: pd.DataFrame) -> None:
    split_hourly = _compute_electricity_split(res)
    split_daily = split_hourly.apply(_daily_sum)

    fig, ax = plt.subplots(num="Daily Electricity Distribution", figsize=(8, 4))
    ax.stackplot(
        split_daily.index,
        *(split_daily[col] for col in split_daily.columns),
        labels=list(split_daily.columns),
        step="mid",
    )
    ax.set(
        title="Daily Electricity Supply Distribution",
        xlabel="Day of year",
        ylabel="Energy [kWhₑ]",
    )
    ax.legend(loc="upper right")
    fig.tight_layout()


def _plot_hp_vs_pv(res: pd.DataFrame) -> None:
    hp = res["hp_electricity"]
    pv = res["pv_ac"]

    hp_s = _rolling_mean(hp)
    pv_s = _rolling_mean(pv)

    fig, ax1 = plt.subplots(num="HP Electricity vs PV", figsize=(8, 4))

    ax1.plot(hp_s, label="HP electricity (24 h mean)")
    ax1.set_ylabel("HP electricity [kW]")

    ax2 = ax1.twinx()
    ax2.plot(pv_s, label="PV AC (24 h mean)", linestyle="--")
    ax2.set_ylabel("PV AC [kW]")

    ax1.set_xlabel("Hour of year")
    ax1.set_title("Heat‑pump Electricity Consumption vs. PV Production")

    # Combine legends from both axes
    lines, labels = [], []
    for ax_ in (ax1, ax2):
        line, label = ax_.get_legend_handles_labels()
        lines += line
        labels += label
    ax1.legend(lines, labels, loc="upper right")
    fig.tight_layout()

def _plot_unserved_energy(res: pd.DataFrame) -> None:
    """Figure 6 – daily energy imported from the grid (should ideally be 0)."""
    EPS_EN = 1e-6  # kWh‑per‑day tolerance: treat smaller values as numerical noise

    shortfall_daily = _daily_sum(res["p_grid_import"])
    shortfall_daily = shortfall_daily.where(shortfall_daily > EPS_EN, 0.0)

    fig, ax = plt.subplots(num="Daily Unserved Energy", figsize=(9, 3.5))
    ax.bar(shortfall_daily.index, shortfall_daily, width=1.0)
    ax.set(
        title="Daily Unserved Energy (Grid Import)",
        xlabel="Day of year",
        ylabel="Energy [kWh]",
    )
    ax.set_ylim(bottom=0)
    fig.tight_layout()

# ════════════════════════════════════════════════════════════════════════════
# ── Public API ───────────────────────────────────────────────────────────────
# ════════════════════════════════════════════════════════════════════════════

def run_and_plot(
    excel_path: str | Path | None = "EnergiData.xlsx",
    heat_pump: HeatPumpType = HeatPumpType.LV,
    save_dir: Path | None = None,
) -> pd.DataFrame:
    """Run the simulation and generate five improved figures.

    Parameters
    ----------
    excel_path
        Workbook containing the hourly time‑series.
    heat_pump
        Which COP column should be used by the heat‑pump model.
    save_dir
        If provided, figures are saved as PNG files into this folder **and**
        still shown on screen. Directory is created if missing.

    Returns
    -------
    pandas.DataFrame
        The hourly results table from the simulator.
    """
    params = SystemParameters(excel_path=excel_path, heat_pump_type=heat_pump)
    raw = ExcelDataLoader(params).load()
    sim = MicrogridSimulator(params, raw)
    results = sim.run()

    # ––– Plot –––
    _plot_surplus_deficit(results)
    _plot_storage_combined(results, params)
    _plot_battery_only(results, params)
    _plot_h2_only(results)
    _plot_heat_distribution(results)
    _plot_electricity_distribution(results)
    _plot_hp_vs_pv(results)
    _plot_unserved_energy(results)

    if save_dir is not None:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        for num in plt.get_fignums():
            fig = plt.figure(num)
            fig.savefig(save_dir / f"figure_{num}.png", dpi=150)

    plt.show()
    return results


if __name__ == "__main__":
    run_and_plot()
