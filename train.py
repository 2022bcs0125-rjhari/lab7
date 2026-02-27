import json, joblib
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

# ---------------- INFO ----------------
NAME = "R J Hari"
ROLL = "2022BCS0125"

# ---------------- PATHS ----------------
DATA_PATH = "dataset/winequality-red.csv"

OUTPUT_DIR = Path("app/artifacts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = OUTPUT_DIR / "model.pkl"
RESULTS_PATH = OUTPUT_DIR / "metrics.json"


# ---------------- LOAD DATA ----------------
data = pd.read_csv(DATA_PATH, sep=";")
X = data.drop("quality", axis=1)
y = data["quality"]

# ---------------- SPLIT ----------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# ===============================
# 🔴 EXPERIMENT-SPECIFIC CODE HERE
# ===============================
import xgboost as xgb

EXP_ID = "EXP-07"
MODEL_NAME = "XGBoost fully tuned"

X_train_proc = X_train
X_test_proc = X_test

model = xgb.XGBRegressor(
    n_estimators=600,
    learning_rate=0.03,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    reg_alpha=0.1,
    reg_lambda=1.0,
    random_state=42
)







# ---------------- TRAIN ----------------
model.fit(X_train_proc, y_train)

# ---------------- EVAL ----------------
y_pred = model.predict(X_test_proc)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

# ---------------- SAVE ----------------
joblib.dump(model, MODEL_PATH)

results = {
    "experiment": EXP_ID,
    "model": MODEL_NAME,
    "mse": mse,
    "r2_score": r2
}

with open(RESULTS_PATH, "w") as f:
    json.dump(results, f, indent=4)

print("Name:", NAME)
print("Roll:", ROLL)
print("MSE:", mse)
print("R2:", r2)












