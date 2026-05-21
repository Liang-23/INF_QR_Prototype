# app.py
# Flask server that reads JSON from Arduino over USB Serial,
# stores the latest reading, and serves it to the phone dashboard.

import csv
import io
import json
import os
import socket
import threading
import time
from datetime import datetime

import psutil
import qrcode
import serial
from flask import Flask, jsonify, redirect, render_template, request, send_file

# Import the rule-based decision engine from the same folder.
from decision_engine import analyze_environment

# Tell Python where to find the ml_model folder.
# __file__ is the path of app.py itself.
# os.path.dirname(__file__) is the server/ folder.
# Going one level up (..) reaches the project root, then we enter ml_model/.
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ml_model"))

# Now Python can find model_predict.py inside ml_model/.
# The rule-based engine is still the MAIN controller — the ML result
# is shown alongside it as an extra prediction only.
from model_predict import predict_environment_condition

# Import the CSV historical data logger from the same folder.
# Every live record is appended to data/sensor_log.csv for later analysis.
from data_logger import save_sensor_data

# ---------------------------------------------------------
# Configuration — change SERIAL_PORT to match your system.
# Change this value to the port shown in Arduino IDE → Tools → Port.
# Windows example: "COM4", "COM5"
# Mac/Linux example: "/dev/ttyUSB0", "/dev/ttyACM0"
# ---------------------------------------------------------
SERIAL_PORT = "COM4"
BAUD_RATE = 9600

app = Flask(__name__)

# Global variable that holds the open serial port object.
# It starts as None and is set by read_serial() once the port opens.
# The shutdown handler uses it to close the port cleanly on CTRL+C.
serial_connection = None

# Global dictionary that holds the most recent sensor reading.
# It is updated by the background thread and read by the /data route.
latest_data = {
    "device_id":          "—",
    "temperature":        "—",
    "humidity":           "—",
    "light":              "—",
    "status":             "Waiting for data...",
    "main_issue":         "—",
    "suggestion":         "—",
    "led_action":         "—",
    "comfort_level":      "—",
    # ML model fields — populated once sensor data arrives.
    "ml_label":           "—",
    "ml_status":          "—",
    "ml_suggestion":      "—",
    "last_update":        "—",
    "data_source_status": "Waiting for sensor data",
}


# ---------------------------------------------------------
# IP detection configuration
# ---------------------------------------------------------

# These IP prefixes are never reachable from a phone on a normal network.
BAD_IP_PREFIXES = ("127.", "169.254.", "198.18.", "198.19.")

# Adapter names containing these words are virtual or system-only.
# psutil returns the adapter name as shown in Windows Network Connections.
BAD_ADAPTER_KEYWORDS = (
    "vEthernet", "WSL", "VMware", "VirtualBox",
    "Bluetooth", "Loopback", "VPN", "ZeroTier",
    "Tailscale", "Docker",
)

# Adapters containing these words are physical Wi-Fi interfaces — prefer them.
PREFERRED_ADAPTER_KEYWORDS = ("Wi-Fi", "WLAN", "Wireless")


def is_private_ip(ip):
    """
    Return True if the IP is in a private range a phone can reach.
    Covers: 10.x.x.x, 192.168.x.x, and 172.16.x.x – 172.31.x.x
    (the last range includes personal hotspot addresses like 172.20.10.x).
    """
    if ip.startswith("10.") or ip.startswith("192.168."):
        return True
    parts = ip.split(".")
    if len(parts) == 4 and parts[0] == "172":
        try:
            if 16 <= int(parts[1]) <= 31:
                return True
        except ValueError:
            pass
    return False


def get_ipv4_candidates():
    """
    Use psutil to scan every network adapter on this machine and collect
    valid IPv4 addresses.

    Returns a list of dicts: [{"ip": "...", "adapter": "..."}, ...]
    Bad adapters (virtual, VPN, Bluetooth …) and bad IP ranges are excluded.
    """
    candidates = []
    for adapter_name, addresses in psutil.net_if_addrs().items():
        # Skip adapters whose name contains a bad keyword.
        if any(kw.lower() in adapter_name.lower() for kw in BAD_ADAPTER_KEYWORDS):
            continue
        for addr in addresses:
            # socket.AF_INET means IPv4 only — skip IPv6 and MAC addresses.
            if addr.family != socket.AF_INET:
                continue
            ip = addr.address
            # Skip IPs in known-bad ranges.
            if any(ip.startswith(prefix) for prefix in BAD_IP_PREFIXES):
                continue
            candidates.append({"ip": ip, "adapter": adapter_name})
    return candidates


def get_best_local_ipv4():
    """
    Choose the single best IPv4 address from the candidates.

    Scoring (higher = better):
      +10  adapter name contains Wi-Fi / WLAN / Wireless
      +5   IP is in a private range (phone-reachable LAN or hotspot)

    Returns the top-scoring IP, or "127.0.0.1" if no candidates exist.
    """
    candidates = get_ipv4_candidates()
    if not candidates:
        return "127.0.0.1"

    def score(c):
        s = 0
        name = c["adapter"].lower()
        if any(kw.lower() in name for kw in PREFERRED_ADAPTER_KEYWORDS):
            s += 10
        if is_private_ip(c["ip"]):
            s += 5
        return s

    candidates.sort(key=score, reverse=True)
    return candidates[0]["ip"]


def build_dashboard_url():
    """Return the full URL a phone needs to open the dashboard."""
    ip = get_best_local_ipv4()
    return f"http://{ip}:5000"


# get_status() has been replaced by analyze_environment() from decision_engine.py.
# The new function returns a full dict (status, main_issue, suggestion,
# led_action, comfort_level) instead of a single string.


def read_serial():
    """
    Background thread function.
    Opens the serial port and continuously reads lines from the Arduino.
    Valid JSON lines update latest_data.
    """
    global latest_data, serial_connection

    # Keep trying to open the port in case the Arduino is not ready yet.
    while True:
        try:
            # Open the serial connection to the Arduino.
            ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)

            # Save the open port in the module-level variable so that
            # the CTRL+C shutdown handler can close it cleanly.
            serial_connection = ser

            print(f"[Serial] Connected to {SERIAL_PORT} at {BAUD_RATE} baud.")

            while True:
                # readline() waits until a full line (ending with \n) arrives.
                raw = ser.readline()

                # Decode bytes to a plain string and remove whitespace/newlines.
                line = raw.decode("utf-8", errors="ignore").strip()

                # If the Arduino sketch reports a sensor read failure, keep
                # the previous data so the dashboard does not go blank.
                if line == "ERROR":
                    print("[Warning] Arduino reported a sensor read error. "
                          "Keeping previous data. Check DHT11 wiring.")
                    continue   # skip the rest of this loop iteration

                # Only process lines that look like JSON objects.
                if line.startswith("{") and line.endswith("}"):
                    try:
                        data = json.loads(line)

                        # Pull the three sensor values out of the JSON.
                        temp  = float(data.get("temperature", 0))
                        hum   = float(data.get("humidity", 0))
                        light = float(data.get("light", 0))

                        # Run the rule-based decision engine.
                        # result is a dict: status, main_issue, suggestion,
                        #                   led_action, comfort_level
                        # This stays as the MAIN logic — it controls led_action.
                        result = analyze_environment(temp, hum, light)

                        # Run the trained ML model in parallel.
                        # ml_result is a dict: ml_label, ml_status, ml_suggestion
                        # The ML model is shown as an EXTRA prediction only.
                        # It does NOT control the LED — rule-based logic does.
                        ml_result = predict_environment_condition(temp, hum, light)

                        # Update the global dictionary with the new reading.
                        # data_source_status is set to "Live sensor data" to
                        # confirm to the dashboard that real readings are arriving.
                        latest_data = {
                            "device_id":          data.get("device_id", "Unknown"),
                            "temperature":        data.get("temperature"),
                            "humidity":           data.get("humidity"),
                            "light":              data.get("light"),
                            # Rule-based fields (main control logic)
                            "status":             result["status"],
                            "main_issue":         result["main_issue"],
                            "suggestion":         result["suggestion"],
                            "led_action":         result["led_action"],
                            "comfort_level":      result["comfort_level"],
                            # ML-based fields (extra prediction only)
                            "ml_label":           ml_result["ml_label"],
                            "ml_status":          ml_result["ml_status"],
                            "ml_suggestion":      ml_result["ml_suggestion"],
                            "last_update":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "data_source_status": "Live sensor data",
                        }

                        print(f"[Data] {latest_data}")

                        # Append this record to data/sensor_log.csv.
                        # The logger handles its own errors and prints
                        # a [Logger] line on success or failure.
                        save_sensor_data(latest_data)

                    except json.JSONDecodeError:
                        # Line looked like JSON but could not be parsed — skip it.
                        print(f"[Warning] Could not parse line: {line}")

        except serial.SerialException as e:
            # Port not available (Arduino not connected, wrong port, etc.).
            print(f"[Serial] Error: {e}. Retrying in 5 seconds...")
            time.sleep(5)


# ---------------------------------------------------------
# Flask routes
# ---------------------------------------------------------

@app.route("/")
def index():
    # Render the mobile dashboard page.
    return render_template("dashboard.html")


@app.route("/data")
def data():
    # Return the latest sensor reading as a JSON response.
    # The dashboard calls this endpoint every 3 seconds.
    return jsonify(latest_data)


@app.route("/qr")
def qr_page():
    # Re-detect on every request so the page is always fresh.
    candidates    = get_ipv4_candidates()
    best_ip       = get_best_local_ipv4()
    dashboard_url = build_dashboard_url()
    return render_template(
        "qr.html",
        best_ip=best_ip,
        dashboard_url=dashboard_url,
        candidates=candidates,
    )


@app.route("/qr.png")
def qr_png():
    # Generate the QR code image in memory — no file saved to disk.
    # io.BytesIO() is an in-memory buffer; we write the PNG into it
    # and send it directly to the browser without touching the filesystem.
    url = build_dashboard_url()
    img = qrcode.make(url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)   # rewind to the start before sending
    return send_file(buf, mimetype="image/png")


@app.route("/refresh-qr")
def refresh_qr():
    # Re-detect the best IPv4 by redirecting back to /qr.
    # Because /qr calls get_best_local_ipv4() fresh each time,
    # this always picks up the current network state.
    return redirect("/qr")


# ---------------------------------------------------------
# Data Trend page — visual IoT dashboard with charts
# ---------------------------------------------------------

@app.route("/trend")
def trend_page():
    # Old singular URL kept as a shortcut to the final trends page.
    return redirect("/trends")


@app.route("/trends")
def trends_page():
    # Render the final data-trends page (trends.html).
    return render_template("trends.html")


@app.route("/api/history")
def api_history():
    """
    Return the last N rows from sensor_log.csv as a JSON array.
    The trend page fetches this to draw line charts.

    Query parameter:
      ?n=60   (default 60, max 500)

    Each element is a dict matching the CSV columns.
    The list is sorted oldest-first so charts draw left-to-right.
    """
    # How many rows to return (default 60, cap at 500).
    try:
        n = min(int(request.args.get("n", 60)), 500)
    except (ValueError, TypeError):
        n = 60

    # Path to the CSV file — same path used by data_logger.py.
    log_file = os.path.join(os.path.dirname(__file__), "data", "sensor_log.csv")

    # If the file does not exist yet, return an empty list.
    if not os.path.isfile(log_file):
        return jsonify([])

    # Read the CSV into a list of dicts, then take the last N rows.
    rows = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # Keep only the last N rows in memory using a sliding window.
            # For a small log this is fine; for huge files a deque would
            # be more efficient, but simplicity wins here.
            all_rows = list(reader)
            rows = all_rows[-n:]
    except Exception:
        return jsonify([])

    return jsonify(rows)


# ---------------------------------------------------------
# /history — clean JSON endpoint for the trend frontend
# ---------------------------------------------------------

@app.route("/history")
def history():
    """
    Return the most recent rows from sensor_log.csv as a JSON object.

    Query parameter:
      ?limit=40   (default 40, max 500)

    Response shape:
      { "history": [ { timestamp, temperature, humidity, light, ... }, ... ] }

    The list is sorted oldest-first so line charts draw left-to-right.
    temperature, humidity, and light are converted to numbers.
    Incomplete rows are skipped safely — Flask never crashes.
    """
    # ---- 1. Parse the ?limit query parameter ----
    # Default to 40 rows.  Cap at 500 to avoid sending huge payloads.
    try:
        limit = min(int(request.args.get("limit", 40)), 500)
    except (ValueError, TypeError):
        limit = 40

    # ---- 2. Build the path to the CSV file ----
    # __file__ is app.py; the CSV lives one folder down in data/.
    # This is the same path data_logger.py uses, so they always point
    # to the same file even if Flask is started from a different directory.
    log_file = os.path.join(os.path.dirname(__file__), "data", "sensor_log.csv")

    # ---- 3. Return an empty history if the file does not exist yet ----
    # The file is created on the first sensor reading, so it may not
    # be there yet when the server first starts.
    if not os.path.isfile(log_file):
        return jsonify({"history": []})

    # ---- 4. Read the CSV, take the last `limit` rows ----
    rows = []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            all_rows = list(reader)
            # Slice the last N rows — already in chronological order.
            raw_rows = all_rows[-limit:]

        # ---- 5. Build clean dicts for the frontend ----
        for raw in raw_rows:
            try:
                # Convert the three sensor columns to numbers.
                # If a value is missing or not a number, default to 0.
                temp  = float(raw.get("temperature", 0) or 0)
                hum   = float(raw.get("humidity",    0) or 0)
                light = float(raw.get("light",       0) or 0)

                rows.append({
                    # timestamp is used as the x-axis label on charts.
                    "timestamp":    raw.get("timestamp",    ""),
                    "temperature":  temp,
                    "humidity":     hum,
                    "light":        light,
                    # Rule-based fields.
                    "status":       raw.get("status",        ""),
                    "main_issue":   raw.get("main_issue",    ""),
                    "led_action":   raw.get("led_action",    ""),
                    "comfort_level":raw.get("comfort_level", ""),
                    # ML fields.
                    "ml_label":     raw.get("ml_label",      ""),
                    "ml_status":    raw.get("ml_status",     ""),
                    "ml_suggestion":raw.get("ml_suggestion", ""),
                })
            except (ValueError, TypeError):
                # Skip any row whose numeric fields are corrupt.
                print("[History] Skipped a row with invalid numeric data.")
                continue

    except Exception as e:
        # File locked, permission error, or any other unexpected problem.
        # Print a clear warning and return an empty history so Flask keeps running.
        print(f"[History] Warning: could not read sensor_log.csv — {e}")
        return jsonify({"history": []})

    return jsonify({"history": rows})


# ---------------------------------------------------------
# Entry point
# ---------------------------------------------------------

if __name__ == "__main__":
    # Start the serial reader in a background thread so it runs
    # alongside Flask without blocking the web server.
    # daemon=True means the thread stops automatically when the program exits.
    serial_thread = threading.Thread(target=read_serial, daemon=True)
    serial_thread.start()

    # Start the Flask web server.
    # host="0.0.0.0" makes it accessible from other devices on the same network.
    # debug=False      — no debug mode (safe for production demos).
    # use_reloader=False — prevents Flask from starting a second copy of the
    #                      process, which would interfere with CTRL+C handling.
    print("[Flask] Server starting at http://0.0.0.0:5000")
    print("[Flask] Press CTRL+C to stop.")
    try:
        app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        # CTRL+C was pressed — shut down cleanly.
        print("\n[System] Server stopped by user.")

        # Close the serial port if it is currently open.
        # This releases COM4 so other programs (e.g. Arduino IDE) can use it.
        if serial_connection and serial_connection.is_open:
            serial_connection.close()
            print("[Serial] Port closed cleanly.")
