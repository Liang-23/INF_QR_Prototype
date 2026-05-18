# generate_dataset.py
# Generates a labelled CSV dataset for training the environmental condition model.
#
# Output file: sensor_dataset.csv
# Columns: temperature, humidity, light, label
#
# Label priority (highest to lowest):
#   too_hot > too_cold > too_humid > too_dry > too_dark > too_bright > comfortable
#
# Run this script once before training:
#   python generate_dataset.py

import csv
import random

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------
OUTPUT_FILE  = "sensor_dataset.csv"
NUM_SAMPLES  = 1000          # total rows to generate
RANDOM_SEED  = 42            # fixed seed → same dataset every run

# -------------------------------------------------------
# Label assignment function
# -------------------------------------------------------
def assign_label(temperature, humidity, light):
    """
    Apply the priority-based rule set and return a single label string.

    Priority order:
      1. too_hot   — temperature > 30
      2. too_cold  — temperature < 18
      3. too_humid — humidity > 70
      4. too_dry   — humidity < 35
      5. too_dark  — light < 250
      6. too_bright — light > 850
      7. comfortable — everything within comfortable range
    """
    if temperature > 30:
        return "too_hot"
    if temperature < 18:
        return "too_cold"
    if humidity > 70:
        return "too_humid"
    if humidity < 35:
        return "too_dry"
    if light < 250:
        return "too_dark"
    if light > 850:
        return "too_bright"
    return "comfortable"

# -------------------------------------------------------
# Dataset generation
# -------------------------------------------------------
random.seed(RANDOM_SEED)

rows = []

for _ in range(NUM_SAMPLES):
    # Generate random sensor values within realistic hardware ranges.
    # DHT11 measures roughly 0–50 °C and 20–95 % RH.
    # TEMT6000 returns 0–1023 from analogRead.
    temperature = round(random.uniform(10.0, 40.0), 1)   # degrees Celsius
    humidity    = round(random.uniform(20.0, 90.0), 1)   # percent
    light       = random.randint(0, 1023)                 # ADC units

    label = assign_label(temperature, humidity, light)
    rows.append([temperature, humidity, light, label])

# Write to CSV — utf-8, Unix line endings for cross-platform compatibility.
with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["temperature", "humidity", "light", "label"])  # header
    writer.writerows(rows)

# -------------------------------------------------------
# Summary
# -------------------------------------------------------
print(f"Dataset saved → {OUTPUT_FILE}")
print(f"Total rows    : {len(rows)}")

# Count how many rows belong to each label.
from collections import Counter
label_counts = Counter(row[3] for row in rows)
print("\nLabel distribution:")
for label, count in sorted(label_counts.items()):
    print(f"  {label:<15} {count}")
