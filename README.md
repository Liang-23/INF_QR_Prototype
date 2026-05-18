# INF QR Environmental Monitor

A prototype IoT system that streams sensor data from an Arduino to a phone browser via QR code — no app required.

## Architecture
```
Sensors → Arduino UNO R3 → USB Serial → Flask Server → QR Code → Phone Browser
                    ↓
           I2C 8x8 LED Matrix (local visual feedback)
```

## Quick Start

### 1. Flash Arduino
Open `arduino/sensor_reader/sensor_reader.ino` in the Arduino IDE and upload to the UNO R3.

### 2. Install Python dependencies
```bash
cd server
pip install -r requirements.txt
```

### 3. Check the COM port
Open `server/app.py` and set `SERIAL_PORT` to the port shown in **Arduino IDE → Tools → Port**.
The correct port is different on every computer (e.g. `"COM4"` on Windows, `"/dev/ttyUSB0"` on Linux/Mac).

### 4. Run the server
```bash
python app.py
```
Scan the printed QR code with your phone (must be on the same Wi-Fi network).

## Open Dashboard on Phone

Follow these steps to open the live dashboard on your phone.

### 1. Connect to the same Wi-Fi
Make sure both your laptop and your phone are connected to the **same Wi-Fi network**.

### 2. Start the Flask server
```bash
cd server
python app.py
```

### 3. Find your laptop's IPv4 address
Open a new terminal on Windows and run:
```bash
ipconfig
```
Look for the **Wi-Fi** section and note the **IPv4 Address**, for example:
```
IPv4 Address. . . . . . . . . . . : 192.168.1.25
```

### 4. Open the dashboard on your phone
Type this into your phone's browser (replace the IP with your own):
```
http://192.168.1.25:5000
```

### 5. Troubleshooting
- **Page does not load:** Check that Windows Firewall is not blocking port 5000.
  Go to **Windows Defender Firewall → Allow an app** and allow Python, or temporarily
  disable the firewall for private networks during testing.
- **Flask not reachable:** Confirm the server started with `host="0.0.0.0"` (already set in `app.py`).
- **Wrong IP:** Run `ipconfig` again — your IP may change each time you reconnect to Wi-Fi.

## Magic QR Refresh

When you switch hotspots, the laptop's IPv4 address changes and the old QR code
stops working. The Magic QR Refresh page solves this automatically — no manual
IP entry required.

**How it works:**
The Flask server uses `psutil` to scan all real network adapters, filters out
virtual adapters (VPN, VMware, WSL, Bluetooth…) and bad IP ranges, then scores
the remaining candidates to pick the best phone-reachable IPv4 automatically.

**How to use it:**

1. Connect your laptop and phone to the **same Wi-Fi or hotspot**.
2. Start the Flask server:
   ```bash
   cd server
   python app.py
   ```
3. On your **laptop** browser, open:
   ```
   http://127.0.0.1:5000/qr
   ```
4. The page shows the best-detected IPv4, the encoded URL, and the QR code.
5. Scan the QR code with your phone — it opens the live dashboard.
6. If you switch hotspots, click **"↻ Refresh QR Code"** on the `/qr` page.
   The server re-scans the adapters and generates a new QR code instantly.

The **"📱 Show QR Code"** button on the main dashboard also opens this page directly.

## Project Structure
```
INF_QR_Prototype/
├── arduino/
│   └── sensor_reader/
│       └── sensor_reader.ino   # Arduino firmware
├── server/
│   ├── app.py              # Flask server + serial reader
│   ├── requirements.txt
│   └── templates/
│       └── dashboard.html  # Mobile dashboard
├── docs/
│   ├── system_architecture.md
│   ├── testing_log.md
│   └── presentation_script.md
├── README.md
└── CLAUDE.md
```

## Hardware
- Arduino UNO R3
- DHT11 temperature & humidity sensor (connected to D2)
- TEMT6000 ambient light sensor (connected to A0)
- I2C 8x8 LED matrix (connected via SDA=A4, SCL=A5, address 0x70)
- USB-A to USB-B cable
- Laptop with Python 3.x
- Phone

## Current Working Status

✅ Full end-to-end pipeline confirmed working as of 2026-05-13. QR code phase complete.

| Component | Status |
|-----------|--------|
| DHT11 real temperature data | ✅ Working |
| DHT11 real humidity data | ✅ Working |
| TEMT6000 real light data | ✅ Working |
| Arduino UNO R3 → JSON via COM4 | ✅ Working |
| Flask server receives and parses data | ✅ Working |
| `/data` endpoint returns live JSON | ✅ Working |
| Status judgment (e.g. low light warning) | ✅ Working |
| Dashboard displays real-time sensor values | ✅ Working |
| QR code opens dashboard on phone | ✅ Working |
| I2C 8x8 LED matrix shows live icons | ✅ Working |

Sample `/data` output:
```json
{
  "device_id": "Room_A01",
  "humidity": 54.7,
  "last_update": "2026-05-12 13:34:24",
  "light": 139,
  "status": "Warning: Light too low",
  "temperature": 26,
  "data_source_status": "Live sensor data"
}
```

## LED Matrix Icons

The I2C 8x8 LED matrix provides **simple local feedback** directly on the device —
no phone or laptop required. It shows one of four icons at all times:

| Icon | Condition | Trigger |
|------|-----------|---------|
| 🌧 Rain | Humidity too high | humidity > 70 % |
| 🌙 Moon | Light too low | light < 150 |
| ☀ Sun | Light too high | light > 850 |
| 😊 Smile | All conditions normal | everything else |

The LED matrix gives quick at-a-glance feedback for anyone near the device.
The phone dashboard provides the full numerical detail (exact values, timestamps, status text).
These two outputs complement each other — they are not duplicates.

### `data_source_status` field

This field tells the dashboard whether real sensor data is flowing:

| Value | Meaning |
|-------|---------|
| `"Waiting for sensor data"` | Server started but no valid Arduino JSON received yet |
| `"Live sensor data"` | Valid sensor JSON arrived and the displayed values are real |

The dashboard shows this value as a small badge below the device ID — orange while waiting, green once live data arrives. If the Arduino sends an `ERROR` line (DHT11 read failure), the previous data is kept and the badge stays green so the display does not go blank.
