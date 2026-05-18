# generate_qr.py
# Generates a QR code image pointing to the Flask dashboard URL.
# Scan the saved image with a phone to open the dashboard instantly.
#
# How to run:
#   cd server
#   python generate_qr.py

import qrcode

# ---------------------------------------------------------
# Change this URL to the exact address that works on the phone.
# Use your laptop's Wi-Fi IPv4 address (run 'ipconfig' on Windows).
# Example: http://192.168.1.25:5000
# ---------------------------------------------------------
DASHBOARD_URL = "http://172.20.10.4:5000"   #172.20.10.9  172.20.10.4

# qrcode.make() takes a text string and returns a QR code image object.
# Any phone camera or QR scanner app can read this image and open the URL.
qr_image = qrcode.make(DASHBOARD_URL)

# The output path is relative to this file (server/).
# Saving one level up into docs/ keeps all documentation assets together.
OUTPUT_PATH = "../docs/dashboard_qr.png"

# save() writes the image to disk as a PNG file.
qr_image.save(OUTPUT_PATH)

print("QR code saved successfully.")
print(f"  File       : {OUTPUT_PATH}")
print(f"  URL        : {DASHBOARD_URL}")
print(f"  Encoded in QR: {DASHBOARD_URL}")
print("Open the PNG file and scan it with your phone to launch the dashboard.")
