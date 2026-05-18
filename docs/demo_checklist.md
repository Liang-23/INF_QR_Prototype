# Demo Checklist

Use this checklist before the live presentation to confirm that the full prototype is
working correctly. Go through each step in order. Only move to the next step after the
current one is confirmed.

---

## Hardware Setup

- [ ] **Step 1 — Connect Arduino UNO R3 to laptop.**
  Plug the USB-A to USB-B cable into the Arduino and into a USB port on the laptop.
  The green power LED on the Arduino should turn on.

- [ ] **Step 2 — Check DHT11 wiring.**
  Confirm the three DHT11 wires are connected correctly:
  - VCC → 5V on Arduino
  - GND → GND on Arduino
  - DATA → Digital pin 2 (D2) on Arduino

- [ ] **Step 3 — Check TEMT6000 wiring.**
  Confirm the three TEMT6000 wires are connected correctly:
  - VCC → 3.3V on Arduino
  - GND → GND on Arduino
  - Signal (SIG) → Analog pin A0 on Arduino

- [ ] **Step 3b — Check I2C LED matrix wiring.**
  Confirm the four matrix wires are connected correctly:
  - VCC → 5V on Arduino
  - GND → GND on Arduino
  - SDA → Analog pin A4 on Arduino
  - SCL → Analog pin A5 on Arduino
  The matrix I2C address must be 0x70 (default on most HT16K33 boards).

---

## Arduino Verification

- [ ] **Step 4 — Confirm Arduino port is COM4.**
  Open the Arduino IDE. Go to **Tools → Port** and confirm that **COM4** is selected
  and matches the connected Arduino. If a different port is shown, select the correct
  one and update `SERIAL_PORT` in `server/app.py` to match.

- [ ] **Step 5 — Upload or confirm Arduino sketch.**
  Open `arduino/sensor_reader/sensor_reader.ino` in the Arduino IDE.
  If the sketch has not been uploaded yet, click **Upload**.
  If it was already uploaded in a previous session, this step can be skipped.

- [ ] **Step 6 — Close the Arduino Serial Monitor.**
  If the Serial Monitor is open in the Arduino IDE, close it.
  The Serial Monitor and the Flask server cannot use the same COM port at the same time.
  Leaving it open will prevent Flask from reading sensor data.

---

## Flask Server

- [ ] **Step 7 — Run the Flask server.**
  Open a terminal, navigate to the server folder, and start the server:
  ```bash
  cd server
  python app.py
  ```
  The terminal should print a message showing the server address and a QR code.
  There should be no error messages. If you see a `SerialException`, go back and
  check Steps 4 and 6.

---

## Laptop Dashboard

- [ ] **Step 8 — Open the laptop dashboard.**
  Open a browser on the laptop and go to:
  ```
  http://127.0.0.1:5000
  ```
  The dashboard should load and display sensor readings.

- [ ] **Step 9 — Open the /data page.**
  In the same browser, go to:
  ```
  http://127.0.0.1:5000/data
  ```
  A JSON object should appear showing `device_id`, `temperature`, `humidity`, `light`,
  `status`, and `last_update`. Confirm all six fields are present and contain real values
  (not `null` or `0`).

- [ ] **Step 10 — Confirm real sensor values update.**
  Go back to `http://127.0.0.1:5000` and watch the values for 10–15 seconds.
  The "Last Update" time should change every 3 seconds, confirming that live data is
  flowing from the Arduino to the dashboard.

---

## Phone Access

- [ ] **Step 11 — Confirm laptop and phone are on the same Wi-Fi network.**
  On the laptop, check the connected Wi-Fi network name.
  On the phone, go to **Settings → Wi-Fi** and confirm it is connected to the same network.
  If they are on different networks, the phone will not be able to reach the Flask server.

- [ ] **Step 12 — Confirm the QR code uses the current laptop IP address.**
  On the laptop, open a terminal and run:
  ```bash
  ipconfig
  ```
  Find the **Wi-Fi** section and note the **IPv4 Address** (for example, `192.168.1.25`).
  Check that the QR code printed by Flask encodes a URL starting with that same IP address,
  for example `http://192.168.1.25:5000`. If the IP has changed since the server started,
  restart the Flask server to regenerate the QR code.

- [ ] **Step 13 — Scan the QR code using the phone.**
  Open the phone camera and point it at the QR code displayed in the Flask terminal or
  browser. A notification should appear — tap it to open the link.

- [ ] **Step 14 — Confirm the phone dashboard opens.**
  The phone browser should load the same dashboard seen on the laptop, showing live
  temperature, humidity, light level, status, and last update time.
  Wait a few seconds and confirm the values are updating.

---

## Sensor Reaction Tests

- [ ] **Step 15 — Test TEMT6000 by covering the sensor.**
  Place a finger or hand over the TEMT6000 light sensor to block the light.
  Watch the **Light** value on the phone or laptop dashboard.
  The number should drop noticeably within a few seconds.
  The LED matrix should switch from the smile icon to the **moon icon** (light too low).

- [ ] **Step 16 — Test DHT11 by breathing gently near the sensor.**
  Breathe slowly and gently toward the DHT11 sensor (do not blow hard).
  Watch the **Humidity** value on the dashboard — it should rise slightly as the warm,
  moist air reaches the sensor. Temperature may also change by 1–2 degrees.
  If humidity rises above 70%, the LED matrix should switch to the **rain icon**.

- [ ] **Step 16b — Confirm LED matrix icon under normal conditions.**
  Under normal indoor conditions (humidity ≤ 70%, ambient light between 150 and 850),
  the matrix should display the **smile icon**.
  This confirms the matrix is running and all four icons are correctly implemented.

---

## Evidence

- [ ] **Step 17 — Take screenshots for evidence.**
  Capture screenshots for each item listed in `docs/demo_evidence.md`:
  - Arduino Serial Monitor showing JSON output
  - Flask terminal showing received data
  - `/data` page JSON in browser
  - Laptop dashboard
  - Phone dashboard
  - QR code
  - Dashboard showing sensor reaction (Step 15 or 16)

  Save all screenshots in the `evidence/` folder inside the project root.

---

## Troubleshooting

**Flask cannot open COM4 (`SerialException` error)**
Go to **Arduino IDE → Tools → Port** and check which port the Arduino is listed under.
Update `SERIAL_PORT` in `server/app.py` to match that port exactly (for example, `"COM3"`
or `"COM5"`). Also make sure the Arduino Serial Monitor is fully closed before running Flask.

**Phone cannot open the dashboard**
Check the following in order:
1. The phone and laptop are on the same Wi-Fi network.
2. The URL on the phone uses the laptop's current IPv4 address (run `ipconfig` to verify).
3. Windows Firewall is not blocking port 5000. Go to **Windows Defender Firewall →
   Allow an app through** and allow Python, or temporarily disable the firewall for
   private networks.

**QR code does not open the correct page**
The laptop's IP address may have changed since the Flask server was started. Stop the server
(press `Ctrl + C` in the terminal), run `ipconfig` to find the new IP address, then restart
the server with `python app.py`. The new QR code will encode the updated address.

**DHT11 shows ERROR or -999**
Check the wiring: VCC to 5V, GND to GND, and DATA to pin D2. Confirm the `DHT` library
is installed in the Arduino IDE (**Sketch → Include Library → Manage Libraries → search
"DHT sensor library" by Adafruit**). Re-upload the sketch after fixing the wiring.

**Light value does not change when covering the sensor**
Confirm the TEMT6000 signal wire is connected to **pin A0** on the Arduino.
Check that VCC is connected to 3.3V (not 5V) and GND is connected to GND.
Re-upload the Arduino sketch if wiring was changed.
