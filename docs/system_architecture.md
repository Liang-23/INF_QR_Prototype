# System Architecture

## Overview
IoT QR Environmental Monitoring Prototype

## Data Flow
```
[DHT11 (D2) + TEMT6000 (A0)]
        ↓
[Arduino UNO R3]  — reads sensors, drives LED matrix, outputs JSON over Serial
        ├── I2C → [8x8 LED Matrix]  — shows local icon (moon/sun/rain/smile)
        └── USB Serial (9600 baud, COM4, JSON format)
                ↓
        [Laptop — Python Flask Server]  — parses JSON, stores latest reading
                ↓ HTTP (LAN, port 5000)
        [QR Code]  — encodes http://<laptop-IP>:5000/, scanned by phone
                ↓
        [Phone Browser]  — loads dashboard.html, polls /data every 3s
```

**Two complementary outputs:**
- **LED matrix** — simple local icon, visible without any device. No network needed.
- **Phone dashboard** — full numerical data (exact values, timestamps, status text) over Wi-Fi.

> **Status (2026-05-13):** Full end-to-end pipeline confirmed working. QR code phase complete — phone successfully scans QR code and opens live dashboard over LAN.

## Components

| Component | Role | Notes |
|-----------|------|-------|
| DHT11 | Temperature & humidity sensor | Digital, single-wire protocol, pin D2 |
| TEMT6000 | Ambient light sensor | Analog output on pin A0 |
| I2C 8x8 LED matrix | Local visual icon display | I2C via A4/A5, address 0x70 |
| Arduino UNO R3 | Microcontroller / serial bridge | USB to laptop via COM4 |
| Flask server | Serial reader + HTTP API + QR generator | Python 3.x |
| dashboard.html | Live numerical data display | Mobile-first, no framework |

## Network
- Server binds to `0.0.0.0:5000` on the laptop's LAN IP
- Phone and laptop must be on the same Wi-Fi network
- QR code encodes `http://<laptop-LAN-IP>:5000/`

## Confirmed
- [x] COM port confirmed: **COM4** on current Windows machine
- [x] JSON serial format working: `{"device_id","temperature","humidity","light"}`
- [x] Flask `/data` endpoint returning live sensor values
- [x] Dashboard displays real-time temperature, humidity, light level, status, and last update time
- [x] QR code scanned by phone opens dashboard correctly over LAN
- [x] Laptop gateway role confirmed: Arduino has no Wi-Fi; laptop bridges USB Serial to LAN HTTP
- [x] I2C 8x8 LED matrix shows 4 icons: rain, moon, sun, smile

## Future Considerations
- Decide on data persistence (in-memory vs SQLite) if history is needed
- Add HTTPS / basic auth if demo moves to a public or shared network
