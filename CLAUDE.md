# CLAUDE.md

## Project
INF QR Environmental Monitor — IoT prototype for a course presentation.

## Architecture
```
Sensors → Arduino UNO R3 → USB Serial → Laptop Python Flask Server → QR Webpage → Phone
```

## Hardware
- Arduino UNO R3
- DHT11 temperature and humidity sensor (connected to D2)
- TEMT6000 ambient light sensor (connected to A0)
- I2C 8x8 LED matrix (SDA=A4, SCL=A5, address 0x70)
- USB cable
- Laptop
- Phone

## Important Constraint
Arduino UNO R3 does not have built-in Wi-Fi. The laptop acts as a temporary gateway
between the Arduino (via USB Serial) and the phone (via LAN HTTP). Do not redesign
the project around ESP32 or any Wi-Fi-capable board unless explicitly asked.

## Stack
- **Firmware**: Arduino C++ (Arduino IDE), targets UNO R3
- **Server**: Python 3, Flask, PySerial, qrcode
- **Frontend**: Vanilla HTML/CSS/JS (no framework), mobile-first

## Development Rules
- Keep code beginner-friendly — avoid advanced patterns or abstractions.
- Explain each file clearly with short inline comments where helpful.
- Work in small steps; verify each stage before moving to the next.
- Keep Arduino code, Python server code, dashboard HTML, and documentation strictly separated.
- Use simple academic English in all documentation.
- Do not over-complicate the architecture — prefer a working prototype over a perfect but complex system.

## Key Conventions
- Serial format from Arduino: JSON object with `device_id`, `temperature`, `humidity`, `light`
- Flask server runs on port 5000, binds to `0.0.0.0`
- Dashboard polls `/data` (JSON) every 3 seconds via `fetch`
- `/data` response shape: `{ device_id, temperature, humidity, light, status, last_update }`

## Flask Routes
| Route | Purpose |
|-------|---------|
| `/` | Main sensor dashboard (`dashboard.html`) |
| `/data` | Live sensor JSON API, polled every 3 s |
| `/qr` | Magic QR Refresh page (`qr.html`) — shows dynamic QR code |
| `/qr.png` | QR code image generated in memory from current IPv4 |

## Magic QR Refresh Feature (permanent — do not remove)
The laptop IPv4 address changes each time a different personal hotspot is used.
To solve this, the Flask app auto-detects the current IPv4 via a UDP socket trick
(`socket.connect("8.8.8.8", 80)`) and generates a fresh QR code on every `/qr` request.

- `get_local_ipv4()` — detects current outgoing network IP
- `build_dashboard_url()` — returns `http://<current-ip>:5000`
- `/qr` renders `server/templates/qr.html` with live IP and URL
- `/qr.png` serves a QR PNG generated in memory (no file written to disk)
- Dashboard has a **"Show QR Code"** button linking to `/qr`

**Do not revert to manual static QR generation unless explicitly asked.**
**Do not remove `get_local_ipv4()`, `build_dashboard_url()`, `/qr`, or `/qr.png`.**

## Current Status (as of 2026-05-13)
QR code phase complete. Full end-to-end pipeline confirmed working.

- [x] DHT11 real temperature data working
- [x] DHT11 real humidity data working
- [x] TEMT6000 real light data working
- [x] Arduino UNO R3 sends JSON through COM4
- [x] Flask receives and parses JSON data
- [x] `/data` API returns live environmental data
- [x] Dashboard displays real-time sensor values on phone
- [x] QR code opens dashboard on phone over LAN
- [x] Magic QR Refresh — `/qr` auto-detects IPv4 and regenerates QR on demand
- [x] I2C 8x8 LED matrix shows 4 simple icons (moon, sun, rain, smile)

## LED Matrix Icons (permanent — 4 icons only)
The matrix shows one icon at a time based on the current sensor reading.
Priority order: rain → moon → sun → smile.

| Icon | Condition |
|------|-----------|
| Rain | humidity > 70 % |
| Moon | light < 150 |
| Sun  | light > 850 |
| Smile | all normal |

The matrix gives simple **local** feedback; the phone dashboard gives full **numerical** detail.
Do not add more icons unless explicitly asked. Keep the logic in `updateMatrixIcon()`.

## Demo (Achieved)
A user scans a QR code on their phone and opens a mobile dashboard displaying:
- Temperature
- Humidity
- Light level
- Status
- Last update time

The I2C LED matrix simultaneously shows a simple icon reflecting the current condition.

## Workflow Notes
- Test Arduino output first in Arduino IDE Serial Monitor before connecting Flask.
- Current Windows Arduino port: **COM4** (set as `SERIAL_PORT` in `server/app.py`).
- The COM port is different on every computer — check Arduino IDE → Tools → Port.
- Phone and laptop must be on the same Wi-Fi network for QR access to work.

## Out of Scope (for now)
- Cloud or remote access
- Data persistence beyond in-memory latest reading
- Authentication
- ESP32 or any Wi-Fi-capable microcontroller redesign
