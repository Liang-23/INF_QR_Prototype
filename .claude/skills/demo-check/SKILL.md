# Skill: demo-check

Check whether the INF QR Environmental Monitor prototype is ready for a live demo.
Work through each section below in order. Report a clear PASS or FAIL for every item.
Print a final summary at the end. Do not run any destructive commands.

---

## 1. Required Files

Check that the following files exist on disk. FAIL if any are missing.

| File | Purpose |
|------|---------|
| `arduino/sensor_reader/sensor_reader.ino` | Arduino firmware |
| `server/app.py` | Flask server |
| `server/requirements.txt` | Python dependencies |
| `server/generate_qr.py` | QR code generator |
| `server/templates/dashboard.html` | Phone dashboard |
| `docs/dashboard_qr.png` | Pre-generated QR code image |

---

## 2. Python Dependencies

Run the following command and check that flask, pyserial, and qrcode are all listed
as installed. FAIL if any are missing.

```
pip show flask pyserial qrcode
```

If a package is missing, print the fix:
```
pip install -r server/requirements.txt
```

---

## 3. Arduino Port

The current Arduino port is **COM4** (Windows).
Check that COM4 appears in the system's available serial ports by running:

```
python -c "import serial.tools.list_ports; ports = [p.device for p in serial.tools.list_ports.comports()]; print('Available ports:', ports); print('COM4 found:', 'COM4' in ports)"
```

- PASS if COM4 is listed.
- FAIL if COM4 is not listed — remind the user to check Device Manager and
  update `SERIAL_PORT` in `server/app.py` if the port has changed.

---

## 4. Arduino Serial Output

Do NOT open the port from Python for a long read (that would block Flask).
Instead remind the user to verify manually:

> Before running Flask, open Arduino IDE → Serial Monitor at 9600 baud.
> Confirm you see one JSON line every 3 seconds, for example:
> `{"device_id":"Room_A01","temperature":26.0,"humidity":54.7,"light":139}`
> Then close Serial Monitor before starting Flask.

Mark this item as MANUAL CHECK — the user must confirm it themselves.

---

## 5. Flask Server Configuration

Read `server/app.py` and verify:

- `SERIAL_PORT` is set to `"COM4"` — WARN if it is different, remind the user to update it.
- `BAUD_RATE` is `9600`.
- `app.run()` uses `host="0.0.0.0"` and `port=5000` — FAIL if either is wrong, because
  the phone cannot reach the dashboard otherwise.

---

## 6. QR Code URL

Read `server/generate_qr.py` and check `DASHBOARD_URL`:

- Confirm it starts with `http://` (not `https://`).
- Confirm it ends with `:5000`.
- Print the current value so the user can visually confirm the IP is correct
  for today's network.

If the URL looks wrong, remind the user to:
1. Run `ipconfig` on Windows and find the Wi-Fi or hotspot IPv4 address.
2. Update `DASHBOARD_URL` in `server/generate_qr.py`.
3. Re-run `python generate_qr.py` to regenerate `docs/dashboard_qr.png`.

---

## 7. QR Code Image

Check that `docs/dashboard_qr.png` exists and was modified recently
(within the last 24 hours is ideal, but existence is the minimum check).

- PASS if the file exists.
- WARN if it cannot be found — remind the user to run `python server/generate_qr.py`.

---

## 8. Network Readiness

Remind the user to verify manually (MANUAL CHECK):

> - Laptop and phone must be on the same Wi-Fi or hotspot.
> - Run `ipconfig` and confirm the IPv4 address matches `DASHBOARD_URL` in generate_qr.py.
> - Open `http://<laptop-IP>:5000` in the phone browser to confirm access before the demo.
> - If the page does not load, check Windows Firewall → allow Python on private networks.

---

## 9. Final Summary

Print a table like this at the end:

```
===== DEMO READINESS CHECK =====

[PASS] Required files present
[PASS] Python packages installed
[PASS/FAIL] COM4 detected
[MANUAL] Arduino Serial output — user must confirm
[PASS/FAIL] Flask configured correctly (host, port, COM port)
[PASS/WARN] QR code URL uses http + port 5000
[PASS/WARN] docs/dashboard_qr.png exists
[MANUAL] Network — user must confirm same Wi-Fi

Overall: READY FOR DEMO  /  NEEDS ATTENTION (list failed items)
```

If any item is FAIL, list the exact fix the user should apply before proceeding.
