# model_predict.py
# Loads the trained Decision Tree model and exposes one function:
#
#   predict_environment_condition(temperature, humidity, light)
#
# Returns a plain dictionary:
#   {
#       "ml_label":      "too_dark",          ← label the model predicted
#       "ml_status":     "Warning",            ← "Normal" or "Warning"
#       "ml_suggestion": "Turn on the LED...", ← human-readable advice
#   }
#
# Run a quick self-test from this folder:
#   python model_predict.py

import os

import joblib
import pandas as pd

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------
# Use __file__ so the model is always found next to this script,
# regardless of the working directory the program was started from.
MODEL_FILE = os.path.join(os.path.dirname(__file__), "environment_model.joblib")

# Feature names — MUST match the column names used during training
# (see train_model.py: df[["temperature", "humidity", "light"]]).
# Using these names removes the sklearn warning:
#   "X does not have valid feature names, but DecisionTreeClassifier
#    was fitted with feature names"
FEATURE_NAMES = ["temperature", "humidity", "light"]

# -------------------------------------------------------
# Suggestion text for each label
# -------------------------------------------------------
SUGGESTIONS = {
    "comfortable": "No action needed.",
    "too_hot":     "Improve ventilation or reduce heat sources.",
    "too_cold":    "Increase heating or close windows.",
    "too_humid":   "Use ventilation or a dehumidifier.",
    "too_dry":     "Use a humidifier or add moisture.",
    "too_dark":    "Turn on the LED light or increase room lighting.",
    "too_bright":  "Reduce direct light or move away from strong light.",
}

# Labels that count as "Normal" — all others are "Warning".
NORMAL_LABELS = {"comfortable"}

# -------------------------------------------------------
# Load model once when this module is imported
# -------------------------------------------------------
# Loading is done at module level so it only happens once per run,
# not every time predict_environment_condition() is called.
_model = joblib.load(MODEL_FILE)


# -------------------------------------------------------
# Public prediction function
# -------------------------------------------------------
def predict_environment_condition(temperature, humidity, light):
    """
    Predict the environmental condition using the trained Decision Tree.

    Parameters
    ----------
    temperature : float — degrees Celsius
    humidity    : float — relative humidity percent
    light       : int/float — raw ADC value (0 dark → 1023 bright)

    Returns
    -------
    dict with keys:
        ml_label      : str — one of the 7 condition labels
        ml_status     : str — "Normal" or "Warning"
        ml_suggestion : str — advice text for the predicted condition
    """
    # Build a 1-row pandas DataFrame with the SAME column names that were
    # used to train the model. Passing a DataFrame (instead of a raw list)
    # makes sklearn happy and removes the "valid feature names" warning.
    features = pd.DataFrame(
        [[temperature, humidity, light]],
        columns=FEATURE_NAMES,
    )

    # model.predict() returns a numpy array — take the first (and only) element.
    ml_label = _model.predict(features)[0]

    # Decide overall status from the label.
    ml_status     = "Normal" if ml_label in NORMAL_LABELS else "Warning"
    ml_suggestion = SUGGESTIONS.get(ml_label, "No suggestion available.")

    return {
        "ml_label":      ml_label,
        "ml_status":     ml_status,
        "ml_suggestion": ml_suggestion,
    }


# -------------------------------------------------------
# Quick self-test — only runs when you call this file directly
# -------------------------------------------------------
if __name__ == "__main__":
    test_cases = [
        # (temperature, humidity, light, description)
        (24.0,  52.0,  400,  "Normal room"),
        (33.0,  55.0,  400,  "Hot room"),
        (15.0,  55.0,  400,  "Cold room"),
        (24.0,  80.0,  400,  "Humid room"),
        (24.0,  25.0,  400,  "Dry room"),
        (24.0,  52.0,  100,  "Dark room"),
        (24.0,  52.0,  900,  "Very bright room"),
    ]

    print(f"{'Description':<22} {'ml_label':<15} {'ml_status':<10} ml_suggestion")
    print("-" * 80)

    for temp, hum, light, description in test_cases:
        result = predict_environment_condition(temp, hum, light)
        print(
            f"{description:<22} "
            f"{result['ml_label']:<15} "
            f"{result['ml_status']:<10} "
            f"{result['ml_suggestion']}"
        )
