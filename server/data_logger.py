# data_logger.py
# Saves every live sensor record into a CSV file for later analysis.
#
# Public function:
#   save_sensor_data(data)
#
# Storage location: data/sensor_log.csv (created next to this file).
# The data/ folder is created automatically on first use.
#
# Uses the built-in csv module only — no pandas needed for logging.

import csv
import os

# ---------------------------------------------------------
# File paths
# ---------------------------------------------------------
# Using __file__ keeps the path correct no matter what working
# directory you start Flask from.
# LOG_FOLDER -> C:\Users\uaena\Desktop\INF_QR_Prototype\server\data
# LOG_FILE   -> C:\Users\uaena\Desktop\INF_QR_Prototype\server\data\sensor_log.csv
LOG_FOLDER = os.path.join(os.path.dirname(__file__), "data")
LOG_FILE   = os.path.join(LOG_FOLDER, "sensor_log.csv")

# ---------------------------------------------------------
# CSV column order
# ---------------------------------------------------------
# Order must stay fixed once the file exists, otherwise rows
# would misalign on the next run.
CSV_COLUMNS = [
    "timestamp",
    "device_id",
    "temperature",
    "humidity",
    "light",
    "status",
    "main_issue",
    "suggestion",
    "led_action",
    "comfort_level",
    "ml_label",
    "ml_status",
    "ml_suggestion",
    "data_source_status",
]


def save_sensor_data(data):
    """
    Append one row of sensor data to data/sensor_log.csv.

    On the very first call (when the file does not yet exist) the
    header is written before the first data row.

    Parameters
    ----------
    data : dict — the complete latest_data dictionary from app.py
    """
    try:
        # 1. Make sure the data/ folder exists.
        #    exist_ok=True means no error is raised if it is already there.
        os.makedirs(LOG_FOLDER, exist_ok=True)

        # 2. Check whether the CSV file exists BEFORE opening it.
        #    If it does not, we know we still need to write the header.
        file_exists = os.path.isfile(LOG_FILE)

        # 3. Build one row dictionary aligned to CSV_COLUMNS.
        #    data["last_update"] is used as the timestamp.
        #    .get(key, "") protects against any missing keys.
        row = {
            "timestamp":          data.get("last_update", ""),
            "device_id":          data.get("device_id", ""),
            "temperature":        data.get("temperature", ""),
            "humidity":           data.get("humidity", ""),
            "light":              data.get("light", ""),
            "status":             data.get("status", ""),
            "main_issue":         data.get("main_issue", ""),
            "suggestion":         data.get("suggestion", ""),
            "led_action":         data.get("led_action", ""),
            "comfort_level":      data.get("comfort_level", ""),
            "ml_label":           data.get("ml_label", ""),
            "ml_status":          data.get("ml_status", ""),
            "ml_suggestion":      data.get("ml_suggestion", ""),
            "data_source_status": data.get("data_source_status", ""),
        }

        # 4. Open the CSV in append mode (creates the file if missing).
        #    newline="" prevents blank lines between rows on Windows.
        #    encoding="utf-8" handles any special characters safely.
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)

            # Write the header only on the very first save.
            if not file_exists:
                writer.writeheader()

            # Write the actual data row.
            writer.writerow(row)

        # 5. Tell the user the save succeeded.
        print("[Logger] Data saved to CSV.")

    except Exception as e:
        # Any unexpected error (disk full, permission denied, locked file, ...).
        # We print the error but do NOT crash the Flask app or the serial thread.
        print(f"[Logger] Failed to save data: {e}")
