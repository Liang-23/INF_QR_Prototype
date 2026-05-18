# Demo Evidence

## 1. Prototype Status

The system is confirmed working end-to-end as of 2026-05-13.

```
DHT11 + TEMT6000 → Arduino UNO R3 → COM4 → Flask Server → QR Code → Phone Dashboard
```

All stages of the data pipeline have been tested and verified. The phone successfully
scans the QR code and opens the live environmental monitoring dashboard over a local
Wi-Fi network. Sensor values update automatically every 3 seconds.

---

## 2. Evidence Checklist

| Evidence Item | Description | File / Screenshot Name | Status |
|---|---|---|---|
| Arduino Serial Monitor JSON output | Raw JSON printed in Arduino IDE Serial Monitor showing sensor values | `evidence/arduino_serial_monitor.png` | To be captured |
| Flask terminal receiving data | Flask server terminal showing incoming serial data and server startup | `evidence/flask_terminal.png` | To be captured |
| `/data` API JSON output | Browser or curl output showing the live `/data` endpoint response | `evidence/api_data_response.png` | To be captured |
| Laptop dashboard screenshot | Dashboard viewed in a laptop browser at `http://localhost:5000` | `evidence/laptop_dashboard.png` | To be captured |
| Phone dashboard screenshot | Dashboard opened on phone browser after scanning the QR code | `evidence/phone_dashboard.png` | To be captured |
| QR code image | QR code printed in Flask terminal or browser, encoding the LAN URL | `evidence/qr_code.png` | To be captured |
| Sensor reaction test | Phone dashboard showing a change in temperature or humidity after breathing on the DHT11 sensor | `evidence/sensor_reaction_test.png` | To be captured |

> **Note:** Screenshots should be saved in an `evidence/` folder inside the project root.
> Update the Status column to ✅ Captured once each screenshot is taken.

---

## 3. Example Real Data

The following JSON was returned by the `/data` endpoint during a live test session:

```json
{
  "device_id": "Room_A01",
  "humidity": 54.7,
  "last_update": "2026-05-12 13:34:24",
  "light": 139,
  "status": "Warning: Light too low",
  "temperature": 26
}
```

---

## 4. Explanation of Status Warning

The `status` field in the response above shows `"Warning: Light too low"`. This warning
was triggered because the light sensor (TEMT6000) returned a value of `139`, which falls
below the threshold defined in the Flask server logic for acceptable indoor light levels.

The Arduino reads an analog voltage from the TEMT6000 on pin A0 and maps it to a
0–1023 integer range. A low integer value corresponds to low ambient light. When the
Flask server receives this value, it evaluates it against a pre-set threshold and assigns
an appropriate status message. In this case, the indoor lighting at the time of testing
was dim, which caused the warning to appear on the dashboard.

This demonstrates that the status logic is functioning correctly — the system not only
displays raw sensor values but also provides a simple environmental assessment in
real time.

---

## 5. Remaining Improvements

The current prototype is functional and suitable for a course demonstration. However,
several improvements could be made in future work:

- **Remove the laptop gateway.** The current design requires a laptop to bridge the
  Arduino (USB Serial) and the phone (LAN HTTP), because the Arduino UNO R3 has no
  built-in Wi-Fi. Replacing the UNO R3 with an ESP32 microcontroller would allow the
  device to connect directly to Wi-Fi and serve data without a laptop intermediary.

- **Add a cloud database.** At present, the Flask server stores only the most recent
  sensor reading in memory. Connecting to a cloud database (such as Firebase or
  InfluxDB) would allow readings to be stored persistently and accessed remotely.

- **Add historical charts.** With stored data, the dashboard could display time-series
  graphs showing how temperature, humidity, and light levels have changed over time.
  This would make the system more useful for long-term environmental monitoring.

- **Improve the dashboard user interface.** The current dashboard is functional and
  mobile-friendly but minimal. Future versions could include colour-coded alerts,
  customisable thresholds, and a more polished visual design.

- **Add more sensors.** Additional sensors such as a CO2 sensor, a noise level sensor,
  or a motion detector could be integrated to expand the range of environmental
  conditions monitored by the system.
