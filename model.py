import os
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

print("📌 Starting training...")

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
DATA_PATH = os.path.join(REPO_ROOT, "data", "accidents.csv")

df = pd.read_csv(
    DATA_PATH,
    usecols=[
        "Start_Lat",
        "Start_Lng",
        "Temperature(F)",
        "Visibility(mi)",
        "Precipitation(in)",
        "Severity"
    ]
).sample(n=100000, random_state=42)

print("📌 Data loaded")

df.dropna(inplace=True)

df["Risk"] = df["Severity"].map({
    1: "LOW",
    2: "LOW",
    3: "MODERATE",
    4: "HIGH"
})

X = df.drop(["Severity", "Risk"], axis=1)
y = df["Risk"]

model = RandomForestClassifier(
    n_estimators=50,
    max_depth=15,
    random_state=42,
    n_jobs=-1
)

model.fit(X, y)

MODEL_PATH = os.path.join(REPO_ROOT, "backend", "risk_model.pkl")
joblib.dump(model, MODEL_PATH)

print("✅ Model trained and saved successfully")

