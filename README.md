# VisGuithon — Data Visualization Dashboard

A multi-chart data visualization dashboard built with **pyimgui** (Dear ImGui) + GLFW + OpenGL.  
Architecture inspired by [ochisrj/VisGuithon](https://github.com/ochisrj/VisGuithon).

## Features

| Feature | Details |
|---|---|
| **Line / Area** | Animated line charts with filled area option |
| **Bar / Histogram** | Multi-series grouped bars with animated grow-in |
| **Scatter / Bubble** | Scatter plots with optional bubble sizing |
| **Pie / Donut** | Animated sweep-in with legend |
| **Gauges** | Radial CPU / RAM gauges with color thresholds |
| **Sparklines** | Compact inline history lines |
| **CSV / Excel** | Load any CSV or XLSX; pick X + Y columns interactively |
| **Live Stats** | Real-time CPU (total + per-core), RAM, Network, Disk I/O |
| **Dark Theme** | Cyberpunk/industrial dark palette |

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Layout

```
VisGuithon Dashboard
├── core/
│   ├── app.py            # Main GLFW + imgui loop
│   └── data_manager.py   # CSV/Excel + psutil live stats
├── ui/
│   ├── charts.py         # Line, Bar, Scatter, Pie, Gauge, Sparkline
│   ├── dashboard_panel.py # Dashboard / CSV / Live tabs
│   ├── menu_bar.py       # File / View / Help menus
│   └── file_dialog.py    # Path-input popup
├── themes/
│   └── theme_manager.py  # Cyberpunk dark theme colors
├── data/                 # Auto-generated sample.csv
└── main.py
```

## Usage

- **Dashboard tab** — auto-populated with live stats + first CSV columns
- **CSV Data tab** — pick X/Y columns and chart type via sidebar
- **Live Stats tab** — real-time system gauges, per-core bars, network/disk history
- **File → Load CSV/Excel** — type the file path in the dialog
- **File → Load Sample Data** — regenerates `data/sample.csv` (60 rows of business metrics)

## Keyboard Shortcuts

| Key | Action |
|---|---|
| Ctrl+O | Open file dialog |
| Ctrl+D | Load sample data |
| Ctrl+Q | Quit |
