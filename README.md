# 🏠 PV-Battery-H₂ Hybrid Micro-Grid Simulator & Plotter

Hourly-resolution Python model that evaluates whether a **single family house** can achieve *net-zero* electricity balance by combining

* rooftop **PV**  
* a **Li-ion battery**, and  
* **green-hydrogen** storage (electrolyser + fuel-cell)  

The repository contains two main modules:

| File | Role |
|------|------|
| **`microgrid_simulation.py`** | Deterministic, modular simulator that follows a mermaid-documented flowchart and logs every power / energy flow |
| **`microgrid_plotter.py`**    | Convenience layer that runs the simulation and pops up seven diagnostic figures (surplus/deficit, storage levels, heat & electricity splits, unserved energy, …) |

---

## 👥 Attribution

This code base was created by Johan Hoppe Rauer **in collaboration with**

* **Nicolai Eiding** – Placeholder 1 – Placeholder 2  

as part of their university project in ** Design af Energianlæg **.

---

## 🎯 Project goal & purpose

1. **Analyse** whether a typical Danish dwelling can run as a *zero-energy* home under hourly weather and demand profiles.  
2. **Compare scenarios** – battery-only, hydrogen-only, and the full hybrid – by tweaking a single `SystemParameters` object.  
3. **Visualise** all key performance indicators (KPIs) so that design trade-offs are obvious to non-experts.

The model is intentionally **transparent & modular** (SOLID principles) so future students can:

* swap in different battery chemistries or fuel-cell stacks,
* read input from CSV/SQL instead of Excel,
* add new KPIs or optimisation loops – without touching the core loop.

---

## 📦 Quick start

```bash
pip install -r requirements.txt   # pandas, matplotlib, openpyxl, …
python microgrid_plotter.py       # uses EnergiData.xlsx by default
```

```python
from microgrid_plotter import run_and_plot, HeatPumpType

# Run with vertical ground-loop COP column and save all figures as PNGs
run_and_plot(
    excel_path="EnergiData.xlsx",
    heat_pump=HeatPumpType.JV,
    save_dir="figures"
)
```

---

## 🛠 Tech Stack & Skills Demonstrated

| Area | Stack / Library | Highlights in this project |
|------|------------------|-----------------------------|
| Core Simulation | Python 3.12, dataclasses, SOLID design | Battery & H₂ store encapsulated, dependency inversion via `SystemParameters` |
| Data Handling | pandas, openpyxl | One-line Excel loader, column validation, rolling & daily aggregations |
| Visualisation | matplotlib only (policy-compliant) | Layered stack-plots, twin y-axes, rolling-mean smoothing |
| Architecture | Enum-driven config, flowchart parity | Mermaid diagram → readable Python one-to-one |
| Numerical Robustness | EPS tolerance, explicit efficiencies | Eliminates floating-point pico-imports/exports |
| Extendability Hooks | Enum `HeatPumpType`, `ComponentLimits` | Swap COP column or device ratings without rewiring logic |
| Dev Experience | Type hints, 100 % docstrings | Straightforward for students to extend & refactor |
| Testing (planned) | pytest, property-based tests | Stubs already structured for deterministic runs |

---

## 📈 Figures Produced

| # | Figure | Insight |
|---|--------|---------|
| 1 | Hourly surplus / deficit (PV_AC − load) | When and how much the house over- or under-produces |
| 2 | Battery + H₂ levels (combined) | Interaction between the two storage media |
| 3 | Battery SoC only | Fine-grained SoC behaviour |
| 4 | Hydrogen store only | Seasonal H₂ swing & electrolyser sizing |
| 5 | Daily heat supply split | Heat-pump vs. fuel-cell waste heat |
| 6 | Daily electricity supply split | PV direct, battery discharge, fuel-cell, grid |
| 7 | Daily unserved energy | Should be 0 kWh in a true net-zero setup |

---

## 📜 Licence

MIT – feel free to fork, adapt, and cite in your own coursework.  
Please keep the attribution section intact when re-using.
