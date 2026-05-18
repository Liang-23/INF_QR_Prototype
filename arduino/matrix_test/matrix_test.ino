/*
  matrix_test.ino
  Purpose: Test an I2C 8x8 LED dot matrix independently.
  This sketch cycles through four icons — moon, sun, rain, smile —
  each displayed for 2 seconds, then repeats forever.

  Hardware:
    Matrix VCC → Arduino 5V
    Matrix GND → Arduino GND
    Matrix SDA → Arduino A4  (SDA)
    Matrix SCL → Arduino A5  (SCL)
    I2C address: 0x70 (default on most HT16K33 breakout boards)

  Libraries required (install via Arduino IDE → Library Manager):
    - Adafruit GFX Library
    - Adafruit LED Backpack Library
    - Wire (built into Arduino IDE, no install needed)
*/

// Wire.h enables I2C communication between the Arduino and the matrix.
#include <Wire.h>

// Adafruit_GFX.h provides the drawing functions (drawBitmap, etc.).
#include <Adafruit_GFX.h>

// Adafruit_LEDBackpack.h provides the Adafruit_8x8matrix class.
#include <Adafruit_LEDBackpack.h>

// Create one matrix object. We will call matrix.begin() in setup().
Adafruit_8x8matrix matrix = Adafruit_8x8matrix();

// ---------------------------------------------------------
// 8x8 bitmap icons
// Each icon is an array of 8 bytes.
// Each byte represents one row; each bit represents one LED.
// Bit 1 = LED on, Bit 0 = LED off.
// The leftmost column is the most significant bit (0x80).
// ---------------------------------------------------------

// Moon icon — crescent shape
static const uint8_t PROGMEM moon_bmp[] = {
  0b00111100,  // row 0:  .##..###
  0b01111110,  // row 1: .######.
  0b11111110,  // row 2: #######.
  0b11111100,  // row 3: ######..
  0b11111100,  // row 4: ######..
  0b11111110,  // row 5: #######.
  0b01111110,  // row 6: .######.
  0b00111100,  // row 7: ..####..
};

// Sun icon — circle with rays
static const uint8_t PROGMEM sun_bmp[] = {
  0b00100100,  // row 0: ..#..#..
  0b10011001,  // row 1: #..##..#
  0b01111110,  // row 2: .######.
  0b00111100,  // row 3: ..####..
  0b00111100,  // row 4: ..####..
  0b01111110,  // row 5: .######.
  0b10011001,  // row 6: #..##..#
  0b00100100,  // row 7: ..#..#..
};

// Rain icon — drops falling downward
static const uint8_t PROGMEM rain_bmp[] = {
  0b01010100,  // row 0: .#.#.#..
  0b10101010,  // row 1: #.#.#.#.
  0b01010101,  // row 2: .#.#.#.#
  0b00000000,  // row 3: ........
  0b01010100,  // row 4: .#.#.#..
  0b10101010,  // row 5: #.#.#.#.
  0b01010101,  // row 6: .#.#.#.#
  0b00000000,  // row 7: ........
};

// Smile icon — happy face
static const uint8_t PROGMEM smile_bmp[] = {
  0b00111100,  // row 0: ..####..
  0b01000010,  // row 1: .#....#.
  0b10100101,  // row 2: #.#..#.#
  0b10000001,  // row 3: #......#
  0b10100101,  // row 4: #.#..#.#
  0b10011001,  // row 5: #..##..#
  0b01000010,  // row 6: .#....#.
  0b00111100,  // row 7: ..####..
};

// setup() runs once when the Arduino is powered on or reset.
void setup() {
  // Start I2C and connect to the matrix at address 0x70.
  // If your board has address jumpers set differently, change 0x70 here.
  matrix.begin(0x70);
}

// showIcon() clears the matrix, draws one 8x8 bitmap, then flushes it to the LEDs.
// bitmap — pointer to the 8-byte array stored in PROGMEM (flash memory)
// holdMs  — how many milliseconds to keep the icon on screen
void showIcon(const uint8_t* bitmap, int holdMs) {
  matrix.clear();

  // drawBitmap() copies an 8x8 bitmap onto the display.
  // Arguments: x offset, y offset, bitmap pointer, width, height, LED colour.
  // LED_ON means maximum brightness.
  matrix.drawBitmap(0, 0, bitmap, 8, 8, LED_ON);

  // writeDisplay() sends the updated buffer to the physical matrix over I2C.
  // Without this call, nothing will appear on screen.
  matrix.writeDisplay();

  // Wait before showing the next icon.
  delay(holdMs);
}

// loop() runs forever, cycling through all four icons.
void loop() {
  showIcon(moon_bmp,  2000);   // show moon  for 2 seconds
  showIcon(sun_bmp,   2000);   // show sun   for 2 seconds
  showIcon(rain_bmp,  2000);   // show rain  for 2 seconds
  showIcon(smile_bmp, 2000);   // show smile for 2 seconds
}
