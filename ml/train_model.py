"""
train_model.py
----------------
Trains the Loan Default Prediction model using the provided dataset
(Loan_default.csv) and persists the trained artifacts:
    - model/loan_model.pkl        (Logistic Regression classifier)
    - model/scaler.pkl            (StandardScaler fit on numeric features)
    - model/label_encoders.pkl    (LabelEncoders for categorical features)
    - model/feature_columns.pkl   (Ordered list of feature names used at train time)
    - model/metrics.json          (Accuracy / precision / recall / f1 for the About page)

Run:
    python ml/train_model.py --csv /path/to/Loan_default.csv
"""

import argparse
import json
import os

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

CATEGORICAL_COLUMNS = [
    "Education",
    "EmploymentType",
    "MaritalStatus",
    "HasMortgage",
    "HasDependents",
    "LoanPurpose",
    "HasCoSigner",
]

NUMERIC_COLUMNS = [
    "Age",
    "Income",
    "LoanAmount",
    "CreditScore",
    "MonthsEmployed",
    "NumCreditLines",
    "InterestRate",
    "LoanTerm",
    "DTIRatio",
]

TARGET_COLUMN = "Default"


def main(csv_path: str, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)

    df = pd.read_csv(csv_path)

    # Drop identifier column if present
    if "LoanID" in df.columns:
        df = df.drop(columns=["LoanID"])

    # Drop rows with a missing target
    df = df.dropna(subset=[TARGET_COLUMN])
    df[TARGET_COLUMN] = df[TARGET_COLUMN].astype(int)

    # Encode categorical columns
    encoders = {}
    for col in CATEGORICAL_COLUMNS:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    feature_columns = NUMERIC_COLUMNS + CATEGORICAL_COLUMNS
    X = df[feature_columns]
    y = df[TARGET_COLUMN]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression(max_iter=3000, class_weight="balanced")
    model.fit(X_train_scaled, y_train)

    y_pred = model.predict(X_test_scaled)
    y_proba = model.predict_proba(X_test_scaled)[:, 1]

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)) * 100, 2),
        "precision": round(float(precision_score(y_test, y_pred)) * 100, 2),
        "recall": round(float(recall_score(y_test, y_pred)) * 100, 2),
        "f1_score": round(float(f1_score(y_test, y_pred)) * 100, 2),
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)) * 100, 2),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "train_rows": int(X_train.shape[0]),
        "test_rows": int(X_test.shape[0]),
        "default_rate_pct": round(float(df[TARGET_COLUMN].mean()) * 100, 2),
        "algorithm": "Logistic Regression (class_weight=balanced)",
    }

    joblib.dump(model, os.path.join(out_dir, "loan_model.pkl"))
    joblib.dump(scaler, os.path.join(out_dir, "scaler.pkl"))
    joblib.dump(encoders, os.path.join(out_dir, "label_encoders.pkl"))
    joblib.dump(feature_columns, os.path.join(out_dir, "feature_columns.pkl"))

    with open(os.path.join(out_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    # Also cache some dataset-level stats used by dashboard charts (income/credit
    # score/age distributions) so the app doesn't need to load the full 24MB CSV.
    chart_data = {
        "age_bins": np.histogram(df["Age"], bins=10)[0].tolist(),
        "age_bin_edges": [round(x, 1) for x in np.histogram(df["Age"], bins=10)[1]],
        "income_bins": np.histogram(df["Income"], bins=10)[0].tolist(),
        "income_bin_edges": [round(x, 1) for x in np.histogram(df["Income"], bins=10)[1]],
        "credit_score_bins": np.histogram(df["CreditScore"], bins=10)[0].tolist(),
        "credit_score_bin_edges": [round(x, 1) for x in np.histogram(df["CreditScore"], bins=10)[1]],
        "default_counts": df[TARGET_COLUMN].value_counts().sort_index().tolist(),
    }
    with open(os.path.join(out_dir, "dataset_chart_data.json"), "w") as f:
        json.dump(chart_data, f, indent=2)

    print("Training complete.")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="Loan_default.csv")
    parser.add_argument("--out", default=os.path.join(os.path.dirname(__file__), "..", "model"))
    args = parser.parse_args()
    main(args.csv, args.out)
