# Testing Log

## Project: INF QR Environmental Monitor
## Last Updated: 2026-05-13

This document records all tests performed on the prototype system. Each test is listed
with its procedure, expected result, and actual result. All tests below were conducted
on the same physical hardware setup: Arduino UNO R3 connected via USB to a Windows
laptop on COM4, with the Flask server running on port 5000.

---

## Test Results

| Test ID | Test Item | Procedure | Expected Result | Actual Result | Status |
|---------|-----------|-----------|-----------------|---------------|--------|
| T01 | Arduino fake JSON output | Upload the Arduino sketch. Open the Arduino IDE Serial Monitor at 9600 baud. Observe the output. | Arduino prints a valid JSON object containing `device_id`, `temperature`, `humidity`, and `light` once per second. | Arduino printed correctly formatted JSON at 9600 baud. All four fields were present and readable. | ✅ Pass |
| T02 | Flask reads Arduino JSON through COM4 | Close the Arduino Serial Monitor. Run `python app.py` in the `server/` folder. Observe the Flask terminal output. | Flask connects to COM4, reads the JSON from the Arduino, and prints the parsed values in the terminal without errors. | Flask connected to COM4 successfully. Parsed JSON values were printed in the terminal. No `SerialException` errors occurred. | ✅ Pass |
| T03 | TEMT6000 light sensor reading | Run the Flask server. Open `http://127.0.0.1:5000/data` in a browser. Cover and uncover the TEMT6000 sensor and observe the `light` field. | The `light` value changes when the sensor is covered (decreases) and uncovered (increases). | The `light` value dropped when the sensor was covered and recovered when uncovered. Readings changed within one update cycle (3 seconds). | ✅ Pass |
| T04 | DHT11 temperature reading | Run the Flask server. Open `http://127.0.0.1:5000/data`. Breathe gently near the DHT11 sensor and observe the `temperature` field. | The `temperature` field shows a realistic room temperature value (approximately 20–35°C) and responds to a warm breath near the sensor. | Temperature reported as 26°C under normal room conditions. Value increased slightly after a breath was directed at the sensor. | ✅ Pass |
| T05 | DHT11 humidity reading | Run the Flask server. Open `http://127.0.0.1:5000/data`. Breathe gently near the DHT11 sensor and observe the `humidity` field. | The `humidity` field shows a realistic percentage value (approximately 30–80%) and rises when warm breath is directed at the sensor. | Humidity reported as 54.7% under normal room conditions. Value increased noticeably after a breath was directed at the sensor. | ✅ Pass |
| T06 | `/data` API real sensor output | Run the Flask server. Open `http://127.0.0.1:5000/data` in a browser. | The browser displays a complete JSON object with all six fields: `device_id`, `temperature`, `humidity`, `light`, `status`, and `last_update`. All values are real (not null or placeholder). | JSON object returned correctly with all six fields populated. Example: `temperature: 26`, `humidity: 54.7`, `light: 139`, `status: "Warning: Light too low"`. | ✅ Pass |
| T07 | Dashboard live update | Open `http://127.0.0.1:5000` in a browser. Wait and observe the displayed sensor values and the "Last Update" timestamp. | The dashboard refreshes every 3 seconds. The "Last Update" timestamp changes with each refresh, and sensor values reflect the latest Arduino reading. | The dashboard updated every 3 seconds as expected. The timestamp incremented correctly. Sensor values changed in response to physical changes at the sensors. | ✅ Pass |
| T08 | Low light warning status | Run the Flask server in a dimly lit environment (or cover the TEMT6000 sensor). Open `/data` and observe the `status` field. | When the light reading is below the threshold, the `status` field shows `"Warning: Light too low"`. | With `light: 139` in indoor conditions, the status field returned `"Warning: Light too low"`. The warning appeared correctly on the dashboard. | ✅ Pass |
| T09 | Phone dashboard access | Connect the phone and laptop to the same Wi-Fi network. On the phone browser, type `http://<laptop-IP>:5000`. | The phone browser loads the live dashboard and displays current sensor values. Values update every 3 seconds without requiring a manual page refresh. | Dashboard loaded successfully on the phone browser. All sensor values were visible and updated live every 3 seconds. | ✅ Pass |
| T10 | QR code dashboard access | Run the Flask server. A QR code encoding the laptop's LAN URL is displayed in the terminal. Scan the QR code with the phone camera. | The phone camera recognises the QR code and offers a link. Tapping the link opens the live dashboard in the phone browser. | The phone camera scanned the QR code successfully. The link resolved to the correct LAN URL. The dashboard opened immediately on the phone browser. | ✅ Pass |

| T15 | LED matrix icon display | Run the full sketch. Observe the matrix under normal indoor conditions (humidity ≤ 70%, 150 ≤ light ≤ 850). Then breathe on the DHT11 to raise humidity above 70% and observe the icon change. | Matrix shows smile icon under normal conditions. Icon changes to rain when humidity exceeds 70%. Covering the TEMT6000 switches to moon icon (light < 150). | — | ⏳ Pending |
| T13 | Dashboard live data status | Start Flask and open `http://127.0.0.1:5000`. Observe the status badge before and after Arduino JSON arrives. | Badge shows "Waiting for sensor data" (orange) on startup, then switches to "Live sensor data" (green) as soon as the first valid Arduino JSON is received. | — | ⏳ Pending |
| T14 | Arduino ERROR line handling | Simulate a DHT11 failure by sending `ERROR` over Serial (or unplug the sensor briefly). Open `/data` while the error occurs. | Flask prints a warning in the terminal but does not crash or clear `latest_data`. The dashboard continues showing the last known values. | — | ⏳ Pending |
| T11 | Automatic IPv4 QR refresh | Start Flask. Open `http://127.0.0.1:5000/qr`. Observe the best-detected IP and candidates table. Switch hotspot, restart Flask, click "↻ Refresh QR Code". | System detects the current laptop IPv4 from real network adapters and regenerates a scannable QR code automatically, without any manual IP entry. | — | ⏳ Pending |
| T12 | Virtual adapter filtering | Run Flask while a VPN or VMware adapter is active. Open `/qr` and check the candidates table. | Virtual adapters (VPN, VMware, WSL, Bluetooth…) are excluded from the table. The selected IP belongs to the real Wi-Fi or hotspot adapter. | — | ⏳ Pending |

---

## Summary

| Total Tests | Passed | Failed | Pending |
|-------------|--------|--------|---------|
| 15 | 10 | 0 | 5 |

10 of 15 tests passed. T11–T15 are pending and will be verified during demo rehearsal.
