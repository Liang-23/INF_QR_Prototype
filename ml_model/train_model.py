# train_model.py
# Reads sensor_dataset.csv, trains a Decision Tree classifier,
# evaluates accuracy, and saves the trained model to environment_model.joblib.
#
# Requirements:
#   pip install pandas scikit-learn joblib
#
# Run after generating the dataset:
#   python train_model.py

import joblib
import pandas as pd
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

# -------------------------------------------------------
# Step 1 — Load the dataset
# -------------------------------------------------------
DATASET_FILE = "sensor_dataset.csv"
MODEL_FILE   = "environment_model.joblib"

print(f"Loading dataset from {DATASET_FILE} ...")
df = pd.read_csv(DATASET_FILE)

print(f"  Rows loaded : {len(df)}")
print(f"  Columns     : {list(df.columns)}")
print()

# -------------------------------------------------------
# Step 2 — Split features (X) and label (y)
# -------------------------------------------------------
# Features: the three sensor readings the Arduino sends.
X = df[["temperature", "humidity", "light"]]

# Target: the condition label we want to predict.
y = df["label"]

# -------------------------------------------------------
# Step 3 — Train / test split (80 % train, 20 % test)
# -------------------------------------------------------
# random_state=42 makes the split reproducible every run.
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Training samples : {len(X_train)}")
print(f"Testing  samples : {len(X_test)}")
print()

# -------------------------------------------------------
# Step 4 — Train the Decision Tree
# -------------------------------------------------------
# max_depth=10 keeps the tree shallow enough to be fast and
# avoids over-fitting on this small dataset.
# random_state=42 makes tie-breaking reproducible.
print("Training DecisionTreeClassifier ...")
model = DecisionTreeClassifier(max_depth=10, random_state=42)
model.fit(X_train, y_train)
print("  Training complete.")
print()

# -------------------------------------------------------
# Step 5 — Evaluate on the test set
# -------------------------------------------------------
y_pred   = model.predict(X_test)
accuracy = model.score(X_test, y_test)

print(f"Test Accuracy : {accuracy * 100:.2f} %")
print()
print("Classification Report:")
print(classification_report(y_test, y_pred))

# -------------------------------------------------------
# Step 6 — Save the trained model
# -------------------------------------------------------
joblib.dump(model, MODEL_FILE)
print(f"Model saved → {MODEL_FILE}")
