# Presentation Script

## Duration: ~5 minutes

---

### 1. Introduction (30s)
- State the problem: environmental monitoring is usually expensive or requires dedicated displays.
- Our solution: use a phone as the display — no app install, just scan a QR code.

### 2. System Overview (60s)
- Walk through the architecture diagram (see `system_architecture.md`).
- Point out each physical component on the desk: sensors, Arduino, LED matrix, laptop.
- Explain the two outputs:
  - **LED matrix** — simple icon visible locally, no phone or network needed.
  - **Phone dashboard** — full numerical detail (temperature, humidity, light values, timestamps) over Wi-Fi.

### 3. Live Demo (90s)
1. Show Arduino connected to laptop via USB. Point out the LED matrix displaying the current icon.
2. Open terminal — show raw serial output from sensor.
3. Start Flask server — show QR code in browser at `/qr`.
4. Scan QR code with phone — dashboard loads showing all numerical values.
5. Cover the TEMT6000 sensor — matrix switches from smile to moon icon (light too low);
   light value drops on phone dashboard simultaneously.
6. Breathe on DHT11 sensor — humidity rises on phone dashboard.
   If humidity exceeds 70%, matrix switches to rain icon.
7. Point out the difference: the matrix gives instant local feedback; the phone shows exact numbers.

### 4. Key Design Decisions (60s)
- Why Flask over a cloud backend: low latency, works offline on LAN.
- Why QR code: zero-friction access for any smartphone.
- Why Arduino UNO: widely available, easy USB serial bridge.

### 5. Limitations & Future Work (30s)
- Currently LAN-only; could add ngrok / cloud relay for remote access.
- Single reading stored in memory; could persist to database for history.
- No authentication; add basic auth for non-demo environments.

### 6. Q&A

---

## Talking Points Cheat Sheet
- Sensors used: DHT11 (temperature & humidity, pin D2) and TEMT6000 (ambient light, pin A0)
- LED matrix: I2C 8x8 display (SDA=A4, SCL=A5) showing 4 icons — moon, sun, rain, smile
- Two outputs: LED matrix = local simple icon; phone dashboard = full numerical detail
- Matrix icon logic: rain (humidity > 70%) → moon (light < 150) → sun (light > 850) → smile (normal)
- Refresh rate: every 3 seconds (configurable in dashboard JS)
- Gateway role: Arduino UNO R3 has no Wi-Fi — the laptop bridges USB Serial to LAN HTTP
- Tested on: mobile Chrome via QR code scan (confirmed working 2026-05-13)
