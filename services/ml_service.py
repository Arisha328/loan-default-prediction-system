"""
services/ml_service.py
-----------------------
Loads the trained model, scaler, and label encoders once at import time and
exposes a single `predict(payload)` function that the /predict route (and
the JSON API) call. Also produces a lightweight, rule-based explanation of
*why* the model reached its verdict, since Logistic Regression coefficients
combined with the scaled feature values give a natural "reason" ranking.
"""

import joblib
import numpy as np
import pandas as pd

from config import Config

_model = None
_scaler = None
_encoders = None
_feature_columns = None


def _load_artifacts():
    global _model, _scaler, _encoders, _feature_columns
    if _model is None:
        _model = joblib.load(Config.MODEL_PATH)
        _scaler = joblib.load(Config.SCALER_PATH)
        _encoders = joblib.load(Config.ENCODERS_PATH)
        _feature_columns = joblib.load(Config.FEATURE_COLUMNS_PATH)
    return _model, _scaler, _encoders, _feature_columns


# snake_case form field -> trained column name
NUMERIC_FIELD_MAP = {
    "age": "Age",
    "income": "Income",
    "loan_amount": "LoanAmount",
    "credit_score": "CreditScore",
    "months_employed": "MonthsEmployed",
    "num_credit_lines": "NumCreditLines",
    "interest_rate": "InterestRate",
    "loan_term": "LoanTerm",
    "dti_ratio": "DTIRatio",
}

CATEGORICAL_FIELD_MAP = {
    "education": "Education",
    "employment_type": "EmploymentType",
    "marital_status": "MaritalStatus",
    "has_mortgage": "HasMortgage",
    "has_dependents": "HasDependents",
    "loan_purpose": "LoanPurpose",
    "has_co_signer": "HasCoSigner",
}

# Human-readable reason templates, keyed by trained column name, used when
# that feature is pushing the applicant toward higher default risk.
RISK_REASON_TEMPLATES = {
    "CreditScore": "Low credit score ({value})",
    "DTIRatio": "High debt-to-income ratio ({value:.2f})",
    "InterestRate": "High interest rate ({value:.1f}%)",
    "LoanAmount": "High loan amount (${value:,.0f})",
    "Income": "Relatively low income (${value:,.0f})",
    "MonthsEmployed": "Short employment history ({value} months)",
    "NumCreditLines": "High number of open credit lines ({value})",
    "Age": "Applicant age ({value}) is a contributing factor",
    "LoanTerm": "Long loan term ({value} months)",
    "EmploymentType": "Employment type increases risk",
    "MaritalStatus": "Marital status is a contributing factor",
    "Education": "Education level is a contributing factor",
    "HasMortgage": "Existing mortgage obligation",
    "HasDependents": "Has dependents, increasing financial obligations",
    "LoanPurpose": "Loan purpose carries added risk",
    "HasCoSigner": "No co-signer on the loan",
}

PROTECTIVE_REASON_TEMPLATES = {
    "CreditScore": "Strong credit score ({value})",
    "DTIRatio": "Healthy debt-to-income ratio ({value:.2f})",
    "InterestRate": "Favorable interest rate ({value:.1f}%)",
    "Income": "Solid annual income (${value:,.0f})",
    "MonthsEmployed": "Stable, long employment history ({value} months)",
    "HasCoSigner": "Loan has a co-signer",
    "HasMortgage": "No existing mortgage obligation",
    "NumCreditLines": "Reasonable number of open credit lines ({value})",
}


def build_input_row(payload: dict):
    """
    payload: dict with snake_case keys matching PredictionForm field names,
    with categorical values as their raw string labels (e.g. "Bachelor's").
    Returns (ordered_feature_array, row_dict_by_trained_column_name).
    """
    _, _, encoders, feature_columns = _load_artifacts()

    row = {}
    for snake_key, train_col in NUMERIC_FIELD_MAP.items():
        row[train_col] = float(payload[snake_key])

    for snake_key, train_col in CATEGORICAL_FIELD_MAP.items():
        raw_value = str(payload[snake_key])
        encoder = encoders[train_col]
        if raw_value in encoder.classes_:
            encoded_value = encoder.transform([raw_value])[0]
        else:
            # Unseen category fallback: use the most frequent class (index 0)
            encoded_value = 0
        row[train_col] = float(encoded_value)

    ordered_df = pd.DataFrame([[row[col] for col in feature_columns]], columns=feature_columns)
    return ordered_df, row


def predict(payload: dict):
    """
    Returns a dict:
        {
            "label": "Low Risk" | "High Risk",
            "probability": float (0-1, probability of default),
            "recommendation": str,
            "reasons": [str, ...]
        }
    """
    model, scaler, _, feature_columns = _load_artifacts()

    raw_row, row_dict = build_input_row(payload)
    scaled_row = scaler.transform(raw_row)

    proba_default = float(model.predict_proba(scaled_row)[0][1])
    label = "High Risk" if proba_default >= 0.5 else "Low Risk"

    reasons = _explain(model, feature_columns, scaled_row, row_dict)
    recommendation = _recommend(label, proba_default)

    return {
        "label": label,
        "probability": proba_default,
        "recommendation": recommendation,
        "reasons": reasons,
    }


def _explain(model, feature_columns, scaled_row, row_dict, top_n=4):
    """
    Logistic Regression score = sum(coef_i * scaled_value_i) + intercept.
    Each term's contribution to the *positive* (default) class tells us how
    much that feature pushed the prediction toward high or low risk. We rank
    features by the magnitude of their contribution and phrase the top ones
    in plain language.
    """
    coefs = model.coef_[0]
    contributions = coefs * scaled_row[0]
    ranked_idx = np.argsort(-np.abs(contributions))

    reasons = []
    for idx in ranked_idx:
        col = feature_columns[idx]
        contribution = contributions[idx]
        value = row_dict[col]

        template = (
            RISK_REASON_TEMPLATES.get(col)
            if contribution > 0
            else PROTECTIVE_REASON_TEMPLATES.get(col)
        )
        if not template:
            continue

        try:
            text = template.format(value=value)
        except (ValueError, TypeError):
            text = template.format(value=str(value))

        reasons.append(text)
        if len(reasons) >= top_n:
            break

    if not reasons:
        reasons.append("Overall financial profile aligns with historical patterns for this outcome.")

    return reasons


def _recommend(label, proba_default):
    if label == "High Risk":
        if proba_default >= 0.75:
            return (
                "This applicant shows a very high likelihood of default. Recommend declining "
                "the loan, or requiring a co-signer, additional collateral, and a substantially "
                "reduced loan amount."
            )
        return (
            "This applicant shows elevated default risk. Consider a higher interest rate, a "
            "shorter loan term, or requiring a co-signer before approval."
        )
    else:
        if proba_default <= 0.15:
            return "This applicant shows strong repayment capacity. Recommend approval under standard terms."
        return (
            "This applicant shows acceptable risk overall, though some factors warrant "
            "monitoring. Standard approval is reasonable with routine follow-up."
        )
