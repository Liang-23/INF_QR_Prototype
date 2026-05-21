# CLAUDE.md

## Project
INF QR Environmental Monitor — IoT prototype for a course presentation.

## Architecture
```
Sensors ─┐
         ├─► Arduino UNO R3 ─► USB Serial JSON ─► Flask Server ─► QR Code ─► Phone
3W LED ◄─┘                                          │
                                                    ├─► Rule-based decision engine
                                                    ├─► ML Decision Tree (parallel)
                                                    └─► CSV history log
        ▲
        └─► I²C 8×8 LED Matrix (local icon feedback)
```

## Hardware
- Arduino UNO R3
- DHT11 temperature & humidity sensor (D2)
- TEMT6000 ambient light sensor (A0)
- I²C 8×8 LED matrix (SDA=A4, SCL=A5, address 0x70)
- 3 W LED module (D8) — auto on/off with hysteresis
- USB cable
- Laptop
- Phone

## Important Constraint
Arduino UNO R3 has no built-in Wi-Fi. The laptop acts as a temporary gateway
between the Arduino (via USB Serial) and the phone (via LAN HTTP). Do not redesign
the project around ESP32 or any Wi-Fi-capable board unless explicitly asked.

## Stack
- **Firmware**: Arduino C++ (Arduino IDE), targets UNO R3
- **Server**: Python 3, Flask, PySerial, qrcode, psutil
- **ML**: scikit-learn (DecisionTreeClassifier), pandas, joblib
- **Frontend**: Vanilla HTML/CSS/JS (no framework), mobile-first

## Development Rules
- Keep code beginner-friendly — avoid advanced patterns or abstractions.
- Explain each file clearly with short inline comments where helpful.
- Work in small steps; verify each stage before moving to the next.
- Keep Arduino code, server code, ML code, dashboard HTML, and documentation strictly separated.
- Use simple academic English in all documentation.
- Do not over-complicate the architecture — prefer a working prototype over a perfect but complex system.
- Treat the rule-based engine as the **main** control logic. The ML model is a parallel, supplementary prediction. Never let the ML output drive the 3 W LED or override `decision_engine.analyze_environment()`.

## Key Conventions
- **Serial format from Arduino**: JSON object with `device_id`, `temperature`, `humidity`, `light`.
- **Flask server**: runs on port 5000, binds to `0.0.0.0`.
- **Dashboard polling**: `/data` is fetched every **2 seconds** via `fetch`.
- **`/data` response shape** — full dict held in `latest_data`:
  ```
  device_id, temperature, humidity, light,
  status, main_issue, suggestion, led_action, comfort_level,   # rule-based
  ml_label, ml_status, ml_suggestion,                          # ML
  last_update, data_source_status
  ```
- **History CSV**: `server/data/sensor_log.csv` — append-only, 14 columns matching `data_logger.CSV_COLUMNS`. Header is auto-written on first save.

## Flask Routes
| Route          | Purpose |
|----------------|---------|
| `/`            | Main sensor dashboard (`dashboard.html`) |
| `/data`        | Live sensor JSON API, polled every 2 s |
| `/qr`          | Magic QR Refresh page (`qr.html`) — shows dynamic QR code |
| `/qr.png`      | QR code image generated in memory from the current best IPv4 |
| `/refresh-qr`  | Redirects to `/qr` — forces a re-detection of the network |
| `/trends`      | Data trends page (`trends.html`) — charts CSV history, mirrors the LED matrix icon, and shows ML prediction |
| `/history?limit=40` | Recent CSV history JSON API for the trends page |

## Magic QR Refresh Feature (permanent — do not remove)
The laptop IPv4 address changes each time a different Wi-Fi or hotspot is used.
The Flask app auto-detects the best LAN IP using `psutil` and generates a fresh
QR code on every `/qr` request.

- `get_ipv4_candidates()` — scans every adapter via `psutil.net_if_addrs()`, filters out virtual interfaces (`vEthernet`, `WSL`, `VMware`, `VirtualBox`, `Bluetooth`, `Loopback`, `VPN`, `ZeroTier`, `Tailscale`, `Docker`) and bad IP prefixes (`127.`, `169.254.`, `198.18.`, `198.19.`).
- `get_best_local_ipv4()` — scores the remaining candidates (Wi-Fi adapter `+10`, private IP `+5`) and returns the top one (`127.0.0.1` if nothing qualifies).
- `build_dashboard_url()` — returns `http://<best-ip>:5000`.
- `/qr` renders `server/templates/qr.html` with the best IP, encoded URL, and a table of every adapter detected.
- `/qr.png` serves a QR PNG generated in memory (`io.BytesIO`, never written to disk).
- `/refresh-qr` redirects back to `/qr` so the user can re-trigger detection with one click.
- Dashboard has a **"📱 Show QR Code"** button linking to `/qr`.

**Do not revert to manual static QR generation unless explicitly asked.**
**Do not remove `get_ipv4_candidates()`, `get_best_local_ipv4()`, `build_dashboard_url()`, `/qr`, `/qr.png`, or `/refresh-qr`.**

## LED Matrix Icons (permanent — 4 icons only)
The matrix shows one icon at a time based on the current sensor reading.
Priority order: rain → moon → sun → smile.

| Icon  | Condition (firmware threshold) |
|-------|--------------------------------|
| Rain  | `humidity > 70 %` |
| Moon  | `light < 150` |
| Sun   | `light > 850` |
| Smile | all normal |

These firmware thresholds intentionally differ from the server-side `decision_engine` thresholds (which use `light < 250` and tighter comfort bands). The matrix is a quick local indicator; the dashboard gives the full numerical detail.

Keep the rendering logic in `updateMatrixIcon()` and the `MATRIX_ROTATION` constant (currently `3`). Do not add more icons unless explicitly asked.

## 3 W Auto-LED (permanent — owned by the Arduino)
The 3 W LED on `D8` is controlled **locally** by the Arduino with hysteresis:

- `light < LED_ON_THRESHOLD` (250) → ON
- `light > LED_OFF_THRESHOLD` (550) → OFF
- in between → previous state held (no flicker)

`LED_ACTIVE_HIGH = true` matches the current module. The Arduino prints a status line each loop: `LIGHT=…,LED=ON/OFF,STATUS=DARK/BRIGHT`.

The server's `decision_engine.led_action` is informational (shown on the dashboard) and does NOT drive `D8`. The Arduino owns the LED so it keeps working even if Flask is offline.

## Rule-Based Decision Engine (`server/decision_engine.py`)
`analyze_environment(temperature, humidity, light)` returns a dict with `status`, `main_issue`, `suggestion`, `led_action`, `comfort_level`.

| Reading | Threshold | Issue |
|---------|-----------|-------|
| temperature | `> 30` | "Temperature too high" |
| temperature | `< 18` | "Temperature too low" |
| humidity    | `> 70` | "Humidity too high" |
| humidity    | `< 35` | "Humidity too low" |
| light       | `< 250` | "Light too low" → `led_action="ON"` |
| light       | `> 850` | "Light too high" |

This is the **main** control logic for everything except the physical 3 W LED (which the Arduino owns).

## ML Model (`ml_model/`) — supplementary
A scikit-learn `DecisionTreeClassifier(max_depth=10)` trained on 1000 synthetic rows. Used in parallel with the rule engine — **never** as a replacement.

- `generate_dataset.py` — random samples within DHT11/TEMT6000 hardware ranges, labelled by the same priority rules used by `decision_engine` plus `too_dry` / `too_bright` / `comfortable`. 7 labels total: `too_hot, too_cold, too_humid, too_dry, too_dark, too_bright, comfortable`. Seed `42` (reproducible). Writes `sensor_dataset.csv`.
- `train_model.py` — 80/20 train/test split, saves `environment_model.joblib`, prints accuracy + classification report.
- `model_predict.py` — loads the model **once at import time** and exposes `predict_environment_condition(t, h, l)` returning `{ml_label, ml_status, ml_suggestion}`. Feature names match the training columns to avoid the sklearn warning.

The dashboard's "Rule vs ML" comparison bar in `dashboard.html` maps each ML label to the matching `main_issue` keyword and shows `Matched` or `Different`.

If you regenerate the dataset or retrain the model, restart Flask so `model_predict.py` re-imports the new `.joblib`.

## CSV History Logger (`server/data_logger.py`)
`save_sensor_data(data)` is called from `read_serial()` on every valid JSON line. It appends one row to `server/data/sensor_log.csv` (creates the folder + header on first run). Column order must stay aligned with `CSV_COLUMNS` — do not reorder. Errors are caught so logging never crashes the serial thread.

## Data Trends Page (`server/templates/trends.html`)
The `/trends` page is a second frontend page for presentation evidence. It uses `/history?limit=40` to draw historical temperature, humidity, and light charts from the CSV log, mirrors the current 8×8 LED matrix icon visually, and shows the current ML label, status, suggestion, and rule-vs-ML comparison.

Tested status: `/trends` and `/history?limit=40` are confirmed working. The five-board trend dashboard shows temperature trend, humidity trend, light trend, LED matrix visual mirror, and ML prediction card.

## Demo (Achieved)
A user scans a QR code on their phone and opens a mobile dashboard with four sections:
- **A** Live readings — temperature, humidity, light
- **B** Rule-based decision — status, main issue, suggestion, LED action, comfort level
- **C** ML prediction — label, status, suggestion
- **D** System info — device ID, last update, data source

A comparison bar tells the user whether the rule engine and ML model agree.
The 8×8 LED matrix simultaneously shows a simple icon reflecting the current condition, and the 3 W LED auto-toggles based on ambient light.

## Current Status (as of 2026-05-21)
Full pipeline + rule engine + ML model + CSV log confirmed working.

- [x] DHT11 temperature + humidity working
- [x] TEMT6000 light working
- [x] Arduino UNO R3 sends JSON through COM4
- [x] 8×8 LED matrix shows 4 icons (rain, moon, sun, smile) at `MATRIX_ROTATION = 3`
- [x] 3 W LED on D8 auto on/off with hysteresis
- [x] Flask receives and parses JSON data
- [x] Rule-based `decision_engine.analyze_environment()` populates main status
- [x] ML `predict_environment_condition()` populates parallel prediction
- [x] CSV history written to `server/data/sensor_log.csv`
- [x] `/data` API returns full 14-key live dictionary
- [x] Dashboard shows four sections + Rule-vs-ML comparison bar
- [x] `/trends` data trend page tested
- [x] `/history?limit=40` CSV history API tested
- [x] Five-board trend dashboard tested: temperature, humidity, light, LED matrix visual mirror, ML prediction
- [x] Magic QR Refresh — psutil adapter scan + scoring
- [x] Clean `CTRL+C` shutdown closes the serial port

## Workflow Notes
- Test Arduino output first in Arduino IDE Serial Monitor before connecting Flask.
- Current Windows Arduino port: **COM4** (set as `SERIAL_PORT` in `server/app.py`).
- The COM port is different on every computer — check Arduino IDE → Tools → Port.
- Phone and laptop must be on the same Wi-Fi network for QR access to work.
- After editing `generate_dataset.py` or `train_model.py`, rerun both scripts to refresh `environment_model.joblib`, then restart Flask.
- `arduino/matrix_test/matrix_test.ino` is a standalone sketch for verifying the matrix alone (no sensors required).

## Out of Scope (for now)
- Cloud or remote access
- Data persistence beyond the local CSV log
- Authentication
- ESP32 or any Wi-Fi-capable microcontroller redesign
- Replacing the rule engine with the ML model (ML stays supplementary)
