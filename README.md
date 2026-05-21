# INF QR Environmental Monitor

A prototype IoT system that streams sensor data from an Arduino to a phone browser via a QR code — no app required. The current build adds a rule-based decision engine, a parallel machine-learning prediction, an automatic 3 W LED, and a CSV history logger.

## Architecture
```
Sensors ─┐
         ├─► Arduino UNO R3 ─► USB Serial JSON ─► Flask Server ─► QR Code ─► Phone Browser
3W LED ◄─┘                                          │
                                                    ├─► Rule-based decision engine
                                                    ├─► ML Decision Tree (parallel)
                                                    └─► CSV history log
        ▲
        └─► I²C 8x8 LED Matrix (local icon feedback)
```

## Quick Start

### 1. Flash the Arduino
Open `arduino/sensor_reader/sensor_reader.ino` in the Arduino IDE and upload to the UNO R3.

### 2. Install Python dependencies
```bash
cd server
pip install -r requirements.txt
pip install pandas scikit-learn joblib   # required by the ML model
```

### 3. Train the ML model (one-time setup)
```bash
cd ml_model
python generate_dataset.py    # creates sensor_dataset.csv
python train_model.py         # creates environment_model.joblib
```
Re-run these only if you change the labels or thresholds in `generate_dataset.py`.

### 4. Check the COM port
Open `server/app.py` and set `SERIAL_PORT` to the port shown in **Arduino IDE → Tools → Port**.
The correct port is different on every computer (`"COM4"` on Windows, `"/dev/ttyUSB0"` on Linux/Mac).

### 5. Run the server
```bash
cd server
python app.py
```
The Flask server starts at `http://0.0.0.0:5000` and starts logging every reading to `server/data/sensor_log.csv`. Press `CTRL+C` to stop — the serial port closes cleanly.

## Open the Dashboard on Your Phone

### 1. Connect to the same Wi-Fi
The laptop and phone must be on the **same Wi-Fi network or hotspot**.

### 2. Start the Flask server
```bash
cd server
python app.py
```

### 3. Find your laptop's IPv4 (or just use Magic QR Refresh — see below)
On Windows:
```bash
ipconfig
```
Look for the **Wi-Fi** section and note the **IPv4 Address**, e.g. `192.168.1.25`.

### 4. Open the dashboard on the phone
```
http://192.168.1.25:5000
```

### 5. Troubleshooting
- **Page does not load** — check that Windows Firewall is not blocking port 5000.
  Go to **Windows Defender Firewall → Allow an app** and allow Python, or temporarily
  disable the firewall for private networks during testing.
- **Flask not reachable** — confirm the server started with `host="0.0.0.0"` (already set in `app.py`).
- **Wrong IP** — run `ipconfig` again; your IP may change each time you reconnect to Wi-Fi.

## Magic QR Refresh

When you switch hotspots, the laptop's IPv4 changes and any static QR stops working. The Magic QR Refresh page solves this automatically — no manual IP entry.

**How it works**
`server/app.py` uses `psutil.net_if_addrs()` to scan every adapter on the laptop, filters out virtual interfaces (VPN, VMware, WSL, Bluetooth, Loopback, ZeroTier, Tailscale, Docker) and unreachable IP ranges (`127.`, `169.254.`, `198.18.`, `198.19.`), then scores the remaining candidates:

- `+10` if the adapter name contains **Wi-Fi**, **WLAN**, or **Wireless**
- `+5` if the IP is in a phone-reachable private range (`10.x`, `192.168.x`, `172.16–31.x`)

The top-scoring IP is used for the QR.

**How to use it**

1. Connect laptop and phone to the **same Wi-Fi or hotspot**.
2. Start the Flask server.
3. On the laptop browser, open:
   ```
   http://127.0.0.1:5000/qr
   ```
4. The page shows the best-detected IPv4, the encoded URL, the QR image, and a table of every adapter discovered (best one highlighted).
5. Scan the QR with your phone to open the dashboard.
6. If you switch hotspots, click **"↻ Refresh QR Code"** — the server re-scans the adapters and serves a fresh QR.

The **"📱 Show QR Code"** button on the main dashboard also opens this page.

## Project Structure
```
INF_QR_Prototype/
├── arduino/
│   ├── sensor_reader/
│   │   └── sensor_reader.ino     # Main firmware: sensors + matrix + 3W LED
│   └── matrix_test/
│       └── matrix_test.ino       # Standalone LED-matrix sanity check
├── server/
│   ├── app.py                    # Flask server + serial reader thread
│   ├── decision_engine.py        # Rule-based environmental analyzer
│   ├── data_logger.py            # Appends every reading to sensor_log.csv
│   ├── generate_qr.py            # Static QR generator (manual fallback)
│   ├── requirements.txt
│   ├── data/
│   │   └── sensor_log.csv        # Auto-created on first reading
│   └── templates/
│       ├── dashboard.html        # Mobile dashboard
│       ├── qr.html               # Magic QR Refresh page
│       └── trends.html           # Historical trend charts page
├── ml_model/
│   ├── generate_dataset.py       # Synthesizes 1000-row labelled CSV
│   ├── train_model.py            # Trains Decision Tree → environment_model.joblib
│   ├── model_predict.py          # Loads model and exposes predict_environment_condition()
│   ├── sensor_dataset.csv        # Generated dataset (created by step above)
│   └── environment_model.joblib  # Saved trained model
├── docs/
│   ├── system_architecture.md
│   ├── demo_checklist.md
│   ├── demo_evidence.md
│   ├── presentation_script.md
│   ├── testing_log.md
│   └── dashboard_qr.png
├── generate_presentation.py      # One-off course-presentation deck generator
├── presentation.pptx
├── README.md
└── CLAUDE.md
```

## Hardware
- Arduino UNO R3
- DHT11 temperature & humidity sensor — `D2`
- TEMT6000 ambient light sensor — `A0`
- I²C 8×8 LED matrix — `SDA=A4`, `SCL=A5`, address `0x70`
- 3 W LED module — `D8` (auto on/off based on light, with hysteresis)
- USB-A to USB-B cable
- Laptop with Python 3.x
- Phone with a QR scanner

## Software Components

### Arduino firmware — `arduino/sensor_reader/sensor_reader.ino`
- Reads DHT11 (temperature, humidity) and TEMT6000 (light, 0–1023 raw ADC) every ~3 s.
- Drives the 8×8 LED matrix icon based on local sensor values (rain → moon → sun → smile priority).
- Drives the 3 W LED on `D8` with hysteresis:
  - `light < 250` → LED ON
  - `light > 550` → LED OFF
  - between → keep previous state (no flicker)
- Emits one JSON line per reading: `{"device_id","temperature","humidity","light"}`.
- `TEST_ICON_MODE = true` cycles all four icons every 2 s for matrix-orientation testing.
- `MATRIX_ROTATION = 3` matches the current physical board (icons render upright).

### Flask server — `server/app.py`
- Reads serial JSON in a background thread; caches the latest dictionary in `latest_data`.
- Runs the rule engine and the ML model on every reading.
- Appends every reading to `server/data/sensor_log.csv`.
- Auto-detects the best LAN IP via `psutil` and serves a fresh QR per request.
- Clean `CTRL+C` shutdown — releases the COM port.

### Rule-based decision engine — `server/decision_engine.py`
Plain `if/elif` logic. **This is the main control logic** for `led_action` and the rule-based status.

| Reading | Range | Result |
|---------|-------|--------|
| temperature | `> 30 °C` | "Temperature too high" |
| temperature | `< 18 °C` | "Temperature too low" |
| humidity    | `> 70 %`  | "Humidity too high" |
| humidity    | `< 35 %`  | "Humidity too low" |
| light       | `< 250`   | "Light too low" → `led_action = "ON"` |
| light       | `> 850`   | "Light too high" |

When no issue is found, status is `Normal` and comfort level is `Comfortable`.

### Machine-learning prediction — `ml_model/`
A Decision Tree classifier trained on a 1000-row synthetic dataset. **Shown alongside the rule engine, not in place of it** — it does not control the LED.

- Labels: `comfortable`, `too_hot`, `too_cold`, `too_humid`, `too_dry`, `too_dark`, `too_bright`.
- `predict_environment_condition(t, h, l)` returns `{ml_label, ml_status, ml_suggestion}`.
- Model is loaded once at import time and reused for every call.
- Dashboard Section C shows the ML output and a comparison bar tells you whether rule and ML agree.

### CSV history logger — `server/data_logger.py`
Every live reading appends one row to `server/data/sensor_log.csv` with 14 columns (timestamp, sensors, rule results, ML results, data source status). The header is written automatically on first run; later rows preserve column order. Errors are caught and logged — the Flask app keeps running even if the disk is full or the file is locked.

### Mobile dashboard — `server/templates/dashboard.html`
- Section A — live sensor readings (temperature, humidity, light).
- Section B — rule-based decision (status badge, main issue, suggestion, LED action, comfort level).
- Section C — ML prediction (label, status badge, suggestion).
- Comparison bar — "Matched" (green) or "Different, please check manually" (red).
- Section D — system info (device ID, last update, data source status).
- Polls `/data` every 2 seconds. Manual refresh button included.

### Data trends page — `server/templates/trends.html`
- Route: `/trends`
- API: `/history?limit=40`
- Purpose: shows historical trend charts from the CSV log, a visual mirror of the 8×8 LED matrix icon, and the current ML prediction card.
- Tested status: confirmed working with five boards — temperature trend, humidity trend, light trend, LED matrix visual mirror, and ML prediction card.

## Current Working Status

End-to-end pipeline confirmed working: sensors → Arduino → Flask → rule engine + ML model → CSV log → dashboard on phone.

| Component | Status |
|-----------|--------|
| DHT11 temperature + humidity | ✅ Working |
| TEMT6000 light | ✅ Working |
| Arduino UNO R3 → JSON via COM4 | ✅ Working |
| 8×8 LED matrix — 4 icons | ✅ Working |
| 3 W LED auto on/off with hysteresis | ✅ Working |
| Flask server receives and parses data | ✅ Working |
| Rule-based decision engine | ✅ Working |
| ML Decision Tree prediction (parallel) | ✅ Working |
| Rule vs ML comparison bar | ✅ Working |
| CSV history log (`server/data/sensor_log.csv`) | ✅ Working |
| `/data` endpoint returns live JSON | ✅ Working |
| Dashboard displays four sections on phone | ✅ Working |
| `/trends` data trend page | ✅ Tested |
| `/history?limit=40` CSV history API | ✅ Tested |
| Five-board trend dashboard | ✅ Tested |
| Magic QR Refresh — psutil adapter scan | ✅ Working |
| Clean `CTRL+C` shutdown | ✅ Working |

Sample `/data` output:
```json
{
  "device_id":          "Room_A01",
  "temperature":        26.0,
  "humidity":           54.7,
  "light":              139,
  "status":             "Warning",
  "main_issue":         "Light too low",
  "suggestion":         "Turn on the LED light or increase room lighting.",
  "led_action":         "ON",
  "comfort_level":      "Uncomfortable",
  "ml_label":           "too_dark",
  "ml_status":          "Warning",
  "ml_suggestion":      "Turn on the LED light or increase room lighting.",
  "last_update":        "2026-05-12 13:34:24",
  "data_source_status": "Live sensor data"
}
```

## LED Matrix Icons

The 8×8 LED matrix gives **simple local feedback** — visible without any phone or laptop. The firmware uses local thresholds that differ from the server's comfort rules so the icon stays a quick at-a-glance indicator.

| Icon  | Trigger (firmware) | Meaning |
|-------|--------------------|---------|
| 🌧 Rain  | `humidity > 70 %` | Too humid |
| 🌙 Moon  | `light < 150`     | Too dark |
| ☀ Sun   | `light > 850`     | Too bright |
| 😊 Smile | otherwise         | All normal |

Priority order: **rain → moon → sun → smile**. The phone dashboard gives the full numerical detail; these two outputs complement each other.

## 3 W Auto-LED

The 3 W LED on `D8` reacts to ambient light independently of the network:

- `light < 250` → LED turns **ON**
- `light > 550` → LED turns **OFF**
- in between → keeps its previous state (hysteresis dead-band, no flicker)

The hysteresis window prevents the LED from flickering near the threshold. The server's `decision_engine.led_action` is informational (shown on the dashboard) and does **not** drive the LED — the Arduino owns that decision locally so it works even if Flask is offline.

## `data_source_status` Badge

| Value | Meaning |
|-------|---------|
| `"Waiting for sensor data"` | Server started but no valid Arduino JSON received yet (badge: orange) |
| `"Live sensor data"` | Valid JSON arrived; values are real (badge: green) |

If the Arduino sends an `ERROR` line (DHT11 read failure), the previous values are kept and the badge stays green — the display never goes blank.

## Notes
- `server/data/sensor_log.csv` is created automatically; the `data/` folder is git-ignorable.
- The standalone `arduino/matrix_test/matrix_test.ino` sketch is a simpler bitmap-only icon tester — use it if you only have the matrix wired up and want to verify it before adding the sensors.
- `generate_qr.py` is a manual fallback that writes a single QR PNG to `docs/dashboard_qr.png` — useful if you want to embed the QR in a slide deck or a printout. The live `/qr` page is preferred for demos.
