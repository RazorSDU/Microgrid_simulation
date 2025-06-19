import enum
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

# ===== ENUMS ================================================================

class HeatPumpType(enum.Enum):
    LV = "COP_LV"   # Air-to-water
    JH = "COP_JH"   # Horizontal ground loop
    JV = "COP_JV"   # Vertical borehole


# ===== CONFIGURATION ========================================================

@dataclass(frozen=True)
class ComponentLimits:
    """Rated power / capacities for individual devices (kW, kWh)."""
    p_bat_charge: float = 20.0   # kW  (positive = charge, negative = discharge)
    p_bat_discharge: float = 20.0
    p_electrolyser: float = 10.0
    p_fuel_cell: float = 10.0


@dataclass
class SystemParameters:
    # -------- File & data -------------
    excel_path: str | Path = "EnergiData.xlsx"
    sheet_name: str | int | None = 0      # default: first sheet
    time_column: str = "Tid (nummer time på et år)"
    pv_column: str = "Solproduktion"
    plug_column: str = "Elforbrug"
    space_heat_column: str = "Varmeforbrug"
    dhw_column: str = "Forbrug varmt brugsvand"
    cop_columns: Tuple[str, str, str] = ("COP_LV", "COP_JH", "COP_JV")
    # -------- Efficiencies (0-1) -------
    eta_inv: float = 0.86
    eta_bat_roundtrip: float = 0.95
    eta_electrolyser: float = 0.55
    eta_fuel_cell: float = 0.55
    # -------- Capacities --------------
    battery_capacity_kwh: float = 82.0
    h2_capacity_kwh: float = 1_000.0
    # -------- Initial states ----------
    soc_bat_init: float = 0.5            # fraction of capacity
    h2_init_kwh: float = field(default=None)  # if None → 0.5 · cap
    # -------- Misc --------------------
    heat_pump_type: HeatPumpType = HeatPumpType.LV
    limits: ComponentLimits = ComponentLimits()

    # Derived ----------
    @property
    def charge_eff(self) -> float:       # assume symmetric half efficiencies
        return np.sqrt(self.eta_bat_roundtrip)

    @property
    def discharge_eff(self) -> float:
        return np.sqrt(self.eta_bat_roundtrip)

    def __post_init__(self):
        if self.h2_init_kwh is None:
            self.h2_init_kwh = 0.5 * self.h2_capacity_kwh


# ===== DATA LOADING =========================================================

class ExcelDataLoader:
    """Loads and validates the hourly time-series data."""
    def __init__(self, params: SystemParameters):
        self.params = params

    def load(self) -> pd.DataFrame:
        df = pd.read_excel(
            self.params.excel_path,
            sheet_name=self.params.sheet_name
        )
        expected_cols = {
            self.params.time_column,
            self.params.pv_column,
            self.params.plug_column,
            self.params.space_heat_column,
            self.params.dhw_column,
            *self.params.cop_columns,
        }
        missing = expected_cols.difference(df.columns)
        if missing:
            raise KeyError(f"Missing columns in Excel: {missing}")

        # Ensure correct ordering and set a proper datetime index if desired
        df = df.sort_values(self.params.time_column).reset_index(drop=True)
        return df


# ===== DEVICES ==============================================================

class Battery:
    def __init__(self, params: SystemParameters):
        self.cap = params.battery_capacity_kwh
        self.soc = params.soc_bat_init * self.cap
        self.eta_c = params.charge_eff
        self.eta_d = params.discharge_eff
        self.p_charge_max = params.limits.p_bat_charge
        self.p_discharge_max = params.limits.p_bat_discharge

    # All power quantities are **positive** here; sign is handled by caller
    def charge(self, p_requested_kw: float, dt_h: float = 1.0) -> float:
        p = min(p_requested_kw, self.p_charge_max)
        e_in = p * dt_h * self.eta_c
        space_left = self.cap - self.soc
        e_actual = min(e_in, space_left)
        self.soc += e_actual
        return e_actual / dt_h  # actual power absorbed (kW at AC side)

    def discharge(self, p_requested_kw: float, dt_h: float = 1.0) -> float:
        p = min(p_requested_kw, self.p_discharge_max)
        e_out_request = p * dt_h / self.eta_d
        e_available = min(e_out_request, self.soc)
        self.soc -= e_available
        return e_available * self.eta_d / dt_h  # kW delivered AC side


class HydrogenStore:
    def __init__(self, params: SystemParameters):
        self.cap = params.h2_capacity_kwh
        self.h2 = params.h2_init_kwh
        self.eta_elec = params.eta_electrolyser
        self.eta_fc = params.eta_fuel_cell
        self.p_elec_max = params.limits.p_electrolyser
        self.p_fc_max = params.limits.p_fuel_cell

    # Electrolyser: converts AC power → chemical energy (kWh in tank)
    def electrolyse(self, p_kw: float, dt_h: float = 1.0) -> float:
        p = min(p_kw, self.p_elec_max)
        e_h2 = p * dt_h * self.eta_elec
        space_left = self.cap - self.h2
        e_actual = min(e_h2, space_left)
        self.h2 += e_actual
        return e_actual / (self.eta_elec * dt_h)  # kW actually consumed

    # Fuel cell: converts chemical energy → AC power (kW) and waste heat (kW_th)
    def fuel_cell(self, p_kw: float, dt_h: float = 1.0) -> Tuple[float, float]:
        p = min(p_kw, self.p_fc_max)
        e_h2_needed = p * dt_h / self.eta_fc
        e_available = min(e_h2_needed, self.h2)
        self.h2 -= e_available
        p_ac = e_available * self.eta_fc / dt_h
        p_heat = (e_available - p_ac * dt_h) / dt_h  # waste heat kW
        return p_ac, p_heat


# ===== SIMULATOR ============================================================

class MicrogridSimulator:
    def __init__(self, params: SystemParameters, df: pd.DataFrame):
        self.p = params
        self.df = df
        self.battery = Battery(params)
        self.h2 = HydrogenStore(params)
        self.logs: Dict[str, List[float]] = {k: [] for k in [
            "pv_ac", "load", "net_before",
            "p_bat_charge", "p_bat_discharge", "soc_bat",
            "p_elec", "p_fc", "h2_store",
            "p_grid_export", "p_grid_import",
            "heat_pump_heat", "heat_from_fc",
            "heat_total_demand", "hp_electricity",
        ]}

    # ---- Helpers -----------------------------------------------------------

    def _log(self, **kwargs):
        for k, v in kwargs.items():
            self.logs[k].append(v)

    # ---- Main loop ---------------------------------------------------------

    def run(self) -> pd.DataFrame:
        cop_col = self.p.heat_pump_type.value
        dt = 1.0  # hours per time-step
        EPS = 1e-6  # kW tolerance (~1 Wh per hour)

        for _, row in self.df.iterrows():
            # 1) Basic demands & PV
            pv_ac = row[self.p.pv_column] * self.p.eta_inv
            q_space   = row[self.p.space_heat_column]
            q_dhw     = row[self.p.dhw_column]
            heat_req  = q_space + q_dhw                   # kWh_th
            cop_hp    = max(row[cop_col], 0.1)            # avoid div/0
            hp_el_kwh = heat_req / cop_hp
            hp_el_kw  = hp_el_kwh / dt

            plug_kw   = row[self.p.plug_column]
            load_kw   = plug_kw + hp_el_kw
            net_kw    = pv_ac - load_kw                   # + surplus / – deficit

            # 2) Surplus branch ------------------------------------------------
            p_bat_ch = p_bat_disch = 0.0
            p_elec = p_fc_kw = p_grid_exp = p_grid_imp = 0.0
            heat_from_fc_kw = 0.0

            if net_kw >= 0:
                # Charge battery
                p_bat_ch = self.battery.charge(net_kw)
                net_after_bat = net_kw - p_bat_ch
                if net_after_bat > 1e-6:
                    # Run electrolyser
                    p_elec = self.h2.electrolyse(net_after_bat)
                    net_after_bat -= p_elec
                p_grid_exp = net_after_bat if net_after_bat > EPS else 0.0

            # ---------- DEFICIT PATH --------------------------------------------
            else:
                deficit_kw = -net_kw                            # load exceeds PV
                # 2a) Discharge battery
                p_bat_disch = self.battery.discharge(deficit_kw)
                deficit_after_bat = deficit_kw - p_bat_disch
            
                # 2b) Fuel-cell if battery not enough and H₂ available
                if deficit_after_bat > EPS and self.h2.h2 > EPS:
                    p_fc_kw, heat_from_fc_kw = self.h2.fuel_cell(deficit_after_bat)
                    deficit_after_bat -= p_fc_kw
            
                # 2c) Whatever is still missing is imported from grid,
                #     but treat values < EPS as numerical noise.
                p_grid_imp = deficit_after_bat if deficit_after_bat > EPS else 0.0
            
                net_after_bat = 0.0  # kept for clarity; not used later


            # 4) Log everything -------------------------------------------------
            self._log(
                pv_ac=pv_ac,
                load=load_kw,
                net_before=net_kw,
                p_bat_charge=p_bat_ch,
                p_bat_discharge=p_bat_disch,
                soc_bat=self.battery.soc,
                p_elec=p_elec,
                p_fc=p_fc_kw,
                h2_store=self.h2.h2,
                p_grid_export=p_grid_exp,
                p_grid_import=p_grid_imp,
                heat_pump_heat=heat_req,
                heat_from_fc=heat_from_fc_kw * dt,  # convert back to kWh_th
                heat_total_demand=heat_req,
                hp_electricity=hp_el_kw,
            )

        # 5) Wrap-up & KPIs ----------------------------------------------------
        results = pd.DataFrame(self.logs)
        annual_balance = results.p_grid_export.sum() - results.p_grid_import.sum()
        print(
            f"Annual grid balance: {annual_balance:.1f} kWh "
            f"({'Zero-energy' if np.isclose(annual_balance, 0, atol=1e-2) else 'Surplus' if annual_balance>0 else 'Deficit'})"
        )
        return results

