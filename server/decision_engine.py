# decision_engine.py
# Rule-based environmental decision engine.
#
# This module contains one public function:
#   analyze_environment(temperature, humidity, light)
#
# It checks the sensor values against fixed thresholds and returns a
# plain dictionary describing what is wrong, what to do about it,
# and whether the 3W LED should be switched on or off.
#
# No machine learning is used — every rule is a simple if/elif check
# so the logic is easy to read, change, and explain in a presentation.


def analyze_environment(temperature, humidity, light):
    """
    Check temperature, humidity, and light against comfort thresholds.

    Parameters
    ----------
    temperature : float   — degrees Celsius from DHT11
    humidity    : float   — relative humidity % from DHT11
    light       : int/float — raw ADC value (0 dark → 1023 bright) from TEMT6000

    Returns
    -------
    dict with keys:
        status        : "Normal" or "Warning"
        main_issue    : short description of what is wrong (or "Environment is comfortable")
        suggestion    : what the user should do
        led_action    : "ON" if the room is too dark, otherwise "OFF"
        comfort_level : "Comfortable" or "Uncomfortable"
    """

    # Collect all problems found so we can join them later.
    issues      = []   # e.g. ["Temperature too high", "Light too low"]
    suggestions = []   # matching advice for each issue

    # Default LED action — only changed to "ON" if light is too low.
    led_action = "OFF"

    # ------------------------------------------------------------------
    # Rule 1 — Temperature
    # ------------------------------------------------------------------
    if temperature > 30:
        issues.append("Temperature too high")
        suggestions.append("Improve ventilation or reduce heat sources.")
    elif temperature < 18:
        issues.append("Temperature too low")
        suggestions.append("Increase heating or close windows.")

    # ------------------------------------------------------------------
    # Rule 2 — Humidity
    # ------------------------------------------------------------------
    if humidity > 70:
        issues.append("Humidity too high")
        suggestions.append("Use ventilation or a dehumidifier.")
    elif humidity < 35:
        issues.append("Humidity too low")
        suggestions.append("Use a humidifier or add moisture.")

    # ------------------------------------------------------------------
    # Rule 3 — Light
    # ------------------------------------------------------------------
    if light < 250:
        issues.append("Light too low")
        suggestions.append("Turn on the LED light or increase room lighting.")
        led_action = "ON"    # room is dark → signal the LED to turn on
    elif light > 850:
        issues.append("Light too high")
        suggestions.append("Reduce direct light or move away from strong light.")
        # led_action stays "OFF" — room is already bright enough

    # ------------------------------------------------------------------
    # Build the result
    # ------------------------------------------------------------------
    if issues:
        # At least one warning was found.
        # Join multiple issues/suggestions with " ; " so they read clearly.
        status        = "Warning"
        main_issue    = "; ".join(issues)
        suggestion    = "; ".join(suggestions)
        comfort_level = "Uncomfortable"
    else:
        # All values are within comfortable ranges.
        status        = "Normal"
        main_issue    = "Environment is comfortable"
        suggestion    = "No action needed."
        comfort_level = "Comfortable"

    return {
        "status":        status,
        "main_issue":    main_issue,
        "suggestion":    suggestion,
        "led_action":    led_action,
        "comfort_level": comfort_level,
    }
