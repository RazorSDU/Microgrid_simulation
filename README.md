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

This code base was created by RazorSDU **in collaboration with Students**  

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

## 📈 FlowChart Diagram for the simulation

[📈 View the Flowchart Diagram](https://mermaid.live/view#pako:eNqFVdty2kgQ_ZUuVSVFyuAANhdTm2wJIRvFBGQQxrcUNYYBVKvbSiPbxLgqlTzt8z7sF-zW_oHfs-_7Ef6S7RkhCYzZ6EWIOX05fXq676WRO6ZSTZpY7u1oRnwGRuPKAXxevYJc8oDW1gxNbmk92dA67ZWTCCxnLnuG3DUgMO3QIsx0nU9vlkcIfg_1yyup5ZIxqHcjagEzbZoLqG_S4PvfES5-9NMMe_PsLyucviXhHVjoIdg47nlkRHMzShiMqU2c8Qai0RysHEmfotO6yEzBzHqUgUd8YlNG_WDdNrf--e-j6dxk8XVNGH9Ri474ezJaxykdfdjUn_Fwb6kPb4E61J_OwTJtkwVJOopIp4HpaI7JTGJBwAijz7i6yhAjwzvI75a-P6o2uePf66BmcRgw16cclbhvCPfqPdfB9YC7KMDTl7-gWikj6iFCvaS92lIVo6spcgvqcktuK-qG_qpwfoi566dDWUHfQkb454-oYEkWhwJ4hMAm18unv4amT8docBJwGdFo5wTlWtXpSNg0lzY5L7Q94GVnvjky2RzerbPHkmTWnT99-R1OhofK8JYEjGYhj4k9xgrFUZoiioZR1KVv0W6cCrYfJ7MDafxfBrPEUhOWH9CyTZmgzkvAg_KOT2AvlbbX7-qtfg902WhuFPUD97vgPp9--xPyCzhG8eqEYY_OYRJa1s-JbMcR1F1AC9NQ8CJPKVxH0PXqZHwaeMgPdN5Gr3lDpZVuCSYf0UXfG2Pvxe2WAD4KQDui-vT1K7IV-SFXfcjcYRwyxrdjChz7nnPoIIde6HtWGIBFJyzl0BHYcxosQMcA3dBZquxacxwV22gMOSiloIsMT1IK8WVIECcC0eVC33muz_vEJqYzxqvJXJj6ZipZJylrd7uGDfVQUzTjRxr-xNn3VhSktsfmKf1eEsvA1BpmMPofFX-opCFI9rcr2ReA01jJb0sld7CgE9-1N5Q8TZX8FnEZIJcm15XcENMi1xZNyQxSLc-WWk5CnPs4-62tQk5WZDwT6Z1vyohEyXgM4iYDn_mJybkwueDz036mK2e0ruwgqfbFdmVbnSMM11bPDDA05XhD3K6IKMtit02B3oiLiZsUraLZHYe7WCKXKzHaier2yIOurOf6-stzdsHwKvGpvYA636uKa3shVoM4Tohb41jX0qVSXy45JXOptht8J0tZiVdCqjE_pFnJpj5WCT-le25xJbEZtTHxGv4c0wkJLazwlfOAZh5xLlzXji19N5zOpNqEWAF-hUKmhkmmuEYTCOXlV9zQYVKtsCdcSLV76U6qFavF3VK5fFAuVg8O8tVKJSvNpVpuf6-6WymVynvF_f2Dg0Kl_JCVPougxd1CoVra28_nS6VKvlQuPPwHzoN6dw)

---

## 📜 Licence

MIT – feel free to fork, adapt, and cite in your own coursework.  
Please keep the attribution section intact when re-using.
