/*
  sensor_reader.ino
  Stage 4: DHT11 + TEMT6000 + I2C 8x8 LED matrix (4 icons) + 3W auto LED.

  The 8x8 matrix shows one of four icons based on current conditions:
    Rain   — humidity too high (> 70 %)
    Moon   — light too low    (< 150)
    Sun    — light too high   (> 850)
    Smile  — everything normal

  The 3W LED on D8 turns ON automatically when the room is dark,
  and turns OFF when it is bright. Hysteresis prevents flickering.

  Serial JSON output is unchanged so Flask receives the same data as before.

  Hardware wiring:
    DHT11     DATA → Arduino D2  |  VCC → 5V  |  GND → GND
    TEMT6000  SIG  → Arduino A0  |  VCC → 5V  |  GND → GND
    Matrix    SDA  → Arduino A4  |  SCL → A5  |  VCC → 5V  |  GND → GND
    3W LED    S/IN → Arduino D8  |  VCC → 5V  |  GND → GND
    Matrix I2C address: 0x70 (default on most HT16K33 boards)

  Libraries required (Arduino IDE → Sketch → Include Library → Manage Libraries):
    - DHT sensor library      by Adafruit
    - Adafruit Unified Sensor by Adafruit  (install when prompted)
    - Adafruit GFX Library    by Adafruit
    - Adafruit LED Backpack   by Adafruit
    - Wire                    built-in, no install needed
*/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_LEDBackpack.h>
#include <DHT.h>

// ---------- Sensor configuration ----------
#define DHTPIN  2
#define DHTTYPE DHT11

// ---------- 3W LED configuration ----------
// D8 drives the LED module's S/IN pin.
#define LED_PIN 8

// Set to true  if the LED turns ON when D8 is HIGH (most modules).
// Set to false if the LED turns ON when D8 is LOW  (active-low modules).
const bool LED_ACTIVE_HIGH = true;

// Hysteresis thresholds — adjust these if your room needs different levels.
// Light value is 0 (pitch dark) → 1023 (very bright), from analogRead(A0).
const int LED_ON_THRESHOLD  = 250;   // turn LED ON  when light drops below this
const int LED_OFF_THRESHOLD = 550;   // turn LED OFF when light rises above this

DHT dht(DHTPIN, DHTTYPE);
Adafruit_8x8matrix matrix = Adafruit_8x8matrix();

// Remembers the current LED state so hysteresis can hold it in the dead-band.
bool ledState = false;   // false = OFF, true = ON

// ---------- Matrix rotation ----------
// 0 = default orientation.
// If icons look sideways or upside-down on your physical board,
// try MATRIX_ROTATION = 1, 2, or 3 (each step rotates 90° clockwise).
const uint8_t MATRIX_ROTATION = 3;

// ---------- Test mode switch ----------
// Set to true to cycle through all four icons on the matrix (2 s each).
// Set to false to run the normal sensor-driven logic.
const bool TEST_ICON_MODE = false;

// ---------- setLED() ----------
// Drives D8 HIGH or LOW, respecting the LED_ACTIVE_HIGH polarity setting.
void setLED(bool on) {
  if (LED_ACTIVE_HIGH) {
    digitalWrite(LED_PIN, on ? HIGH : LOW);
  } else {
    digitalWrite(LED_PIN, on ? LOW : HIGH);   // active-low module
  }
}

// ---------- updateAutoLED() ----------
// Reads the current light level, applies hysteresis, updates D8,
// and prints a status line such as: LIGHT=120,LED=ON,STATUS=DARK
//
// Hysteresis rules:
//   light < LED_ON_THRESHOLD  → LED ON  (dark room)
//   light > LED_OFF_THRESHOLD → LED OFF (bright room)
//   between the two thresholds → keep previous state (dead-band, no flicker)
void updateAutoLED(int lightValue) {
  // Decide new state only outside the dead-band.
  if (lightValue < LED_ON_THRESHOLD) {
    ledState = true;    // definitely dark → turn on
  } else if (lightValue > LED_OFF_THRESHOLD) {
    ledState = false;   // definitely bright → turn off
  }
  // If between thresholds, ledState is unchanged (hysteresis dead-band).

  setLED(ledState);

  // Print human-readable status line for Serial Monitor.
  Serial.print("LIGHT=");
  Serial.print(lightValue);
  Serial.print(",LED=");
  Serial.print(ledState ? "ON" : "OFF");
  Serial.print(",STATUS=");
  Serial.println(ledState ? "DARK" : "BRIGHT");
}

// ---------- drawPointIcon() ----------
// Clears the matrix, lights every pixel listed in points[], then pushes to LEDs.
//
// points : 2D array where each row is { x, y }.
//          x = column (0 = left edge, 7 = right edge).
//          y = row    (0 = top edge,  7 = bottom edge).
// count  : number of { x, y } pairs to draw.
void drawPointIcon(const uint8_t points[][2], uint8_t count) {
  matrix.clear();
  for (uint8_t i = 0; i < count; i++) {
    matrix.drawPixel(points[i][0], points[i][1], LED_ON);
  }
  matrix.writeDisplay();
}

// ---------- Icon pixel coordinates ----------
// Most pixels are kept inside x = 1..6, y = 1..6 so each icon looks centred
// and does not touch the physical frame edges.
// A few icons use y = 0 or y = 7 for ray or drop details — that is intentional.

// ---------- SMILE — all conditions normal ----------
// Full circle outline, single-dot eyes at (2,3) and (5,3),
// solid smile bar at y=5.
static const uint8_t smilePoints[][2] = {
  {2,1}, {3,1}, {4,1},
  {1,2}, {5,2},
  {0,3}, {2,3}, {4,3}, {6,3},
  {0,4}, {2,4}, {4,4}, {6,4},
  {0,5}, {2,5}, {4,5}, {6,5},
  {1,6}, {5,6},
  {2,7}, {3,7}, {4,7},
};
const uint8_t SMILE_COUNT = sizeof(smilePoints) / sizeof(smilePoints[0]);

// ---------- MOON — light too low ----------
// Right-facing crescent: rows 3-4 shift one column left relative to rows 2 and 5,
// creating a concave inner edge that gives the classic crescent silhouette.
static const uint8_t moonPoints[][2] = {
  {3,1},
  {2,2},
  {1,3}, {2,3},
  {1,4}, {2,4},
  {1,5}, {2,5}, {3,5},
  {2,6}, {3,6}, {4,6}, {5,6},
};
const uint8_t MOON_COUNT = sizeof(moonPoints) / sizeof(moonPoints[0]);

// ---------- SUN — light too high ----------
// 3x3 solid disc centred at (3,4) with 8 single-pixel rays:
// one top/bottom cardinal ray, two left/right cardinal rays, and
// four diagonal rays — giving a clear starburst silhouette.
static const uint8_t sunPoints[][2] = {
  {3,1},
  {1,2}, {3,2}, {5,2},
  {2,3}, {3,3}, {4,3},
  {0,4}, {2,4}, {3,4}, {4,4}, {6,4},
  {2,5}, {3,5}, {4,5},
  {1,6}, {3,6}, {5,6},
  {3,7},
};
const uint8_t SUN_COUNT = sizeof(sunPoints) / sizeof(sunPoints[0]);

// ---------- RAIN — humidity too high ----------
// Teardrop / water-drop silhouette: single-pixel tip at top narrows,
// widens to its broadest row at y=4, then narrows back to a round base.
// Matches the humidity / water-drop icon style used in the PPT slides.
static const uint8_t rainPoints[][2] = {
  {2,1}, {3,1}, {4,1},
  {1,2}, {5,2},
  {0,3}, {6,3},
  {0,4}, {6,4},
  {1,5}, {2,5}, {3,5}, {4,5}, {5,5},
  {1,6}, {3,6}, {5,6},
  {1,7}, {3,7}, {5,7},
};
const uint8_t RAIN_COUNT = sizeof(rainPoints) / sizeof(rainPoints[0]);

// ---------- updateMatrixIcon() ----------
// Picks and displays the correct icon for the current sensor readings.
// Priority order: rain → moon → sun → smile.
void updateMatrixIcon(float humidity, int lightValue) {
  if (humidity > 70) {
    drawPointIcon(rainPoints, RAIN_COUNT);    // too humid
  } else if (lightValue < 150) {
    drawPointIcon(moonPoints, MOON_COUNT);    // too dark
  } else if (lightValue > 850) {
    drawPointIcon(sunPoints, SUN_COUNT);      // very bright
  } else {
    drawPointIcon(smilePoints, SMILE_COUNT);  // all normal
  }
}

// ---------- setup() — runs once on power-on or reset ----------
void setup() {
  // Start USB Serial at 9600 baud so Flask can read JSON output.
  Serial.begin(9600);

  // Set D8 as output and make sure the LED starts OFF.
  pinMode(LED_PIN, OUTPUT);
  setLED(false);

  // Start the DHT11 sensor.
  dht.begin();

  // Connect to the LED matrix at I2C address 0x70.
  matrix.begin(0x70);

  // Apply rotation so the icon is the right way up on your board.
  // If icons look rotated, change MATRIX_ROTATION (0, 1, 2, or 3) near the top.
  matrix.setRotation(MATRIX_ROTATION);

  // Show smile on startup as a quick self-test for the matrix.
  drawPointIcon(smilePoints, SMILE_COUNT);
  delay(1000);
}

// ---------- loop() — runs forever ----------
void loop() {
  // --- Always read light first so the 3W LED can react in any mode ---
  // analogRead(A0) returns 0 (very dark) to 1023 (very bright).
  int lightValue = analogRead(A0);

  // Apply hysteresis and update D8. Also prints: LIGHT=x,LED=ON/OFF,STATUS=DARK/BRIGHT
  updateAutoLED(lightValue);

  // --- Icon test mode ---
  // Cycles through all four icons so you can check each one on the real matrix.
  // Change TEST_ICON_MODE to false (near the top) to return to normal operation.
  if (TEST_ICON_MODE) {
    Serial.println("Testing icon: SUN");
    drawPointIcon(sunPoints,   SUN_COUNT);   delay(2000);

    Serial.println("Testing icon: MOON");
    drawPointIcon(moonPoints,  MOON_COUNT);  delay(2000);

    Serial.println("Testing icon: HUMIDITY");
    drawPointIcon(rainPoints,  RAIN_COUNT);  delay(2000);

    Serial.println("Testing icon: SMILE");
    drawPointIcon(smilePoints, SMILE_COUNT); delay(2000);
    return;
  }

  // --- Read DHT11 ---
  float humidity    = dht.readHumidity();
  float temperature = dht.readTemperature();   // Celsius

  if (isnan(humidity) || isnan(temperature)) {
    Serial.println("ERROR");   // Flask keeps previous data; does not crash.
    delay(2000);
    return;
  }

  // --- Update LED matrix icon ---
  updateMatrixIcon(humidity, lightValue);

  // --- Serial Monitor debug output (human-readable) ---
  // Use this to watch live values and tune thresholds.
  Serial.println("---");
  Serial.print("Temp:     "); Serial.print(temperature, 1); Serial.println(" C");
  Serial.print("Humidity: "); Serial.print(humidity, 1);    Serial.println(" %");
  Serial.print("Light:    "); Serial.println(lightValue);
  if (humidity > 70) {
    Serial.println("Icon:     RAIN  (humidity > 70)");
  } else if (lightValue < 150) {
    Serial.println("Icon:     MOON  (light < 150)");
  } else if (lightValue > 850) {
    Serial.println("Icon:     SUN   (light > 850)");
  } else {
    Serial.println("Icon:     SMILE (normal)");
  }

  // --- Send JSON over Serial to Flask ---
  // This format must stay exactly the same — Flask parses these keys by name.
  Serial.print("{\"device_id\":\"Room_A01\"");
  Serial.print(",\"temperature\":");
  Serial.print(temperature, 1);
  Serial.print(",\"humidity\":");
  Serial.print(humidity, 1);
  Serial.print(",\"light\":");
  Serial.print(lightValue);
  Serial.println("}");

  // Wait 3 seconds before the next reading.
  delay(3000);
}
