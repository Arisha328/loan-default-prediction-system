"""
routes/api.py
--------------
Lightweight JSON REST API mirroring the web flows, for programmatic access
(e.g. mobile apps, integrations, testing). All state-changing endpoints
still require a valid logged-in session (login_required) and are protected
by CSRF like the rest of the app; login/register are additionally rate
limited to true form data via Flask-WTF-friendly parsing.

Endpoints:
    POST /api/register
    POST /api/login
    POST /api/predict
    GET  /api/history
"""

import json

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required, login_user

from extensions import db
from models import Prediction, User
from services import ml_service

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/register", methods=["POST"])
def api_register():
    data = request.get_json(silent=True) or {}
    required = ["full_name", "email", "password"]
    if not all(data.get(f) for f in required):
        return jsonify({"error": "full_name, email, and password are required."}), 400

    if User.query.filter_by(email=data["email"].lower().strip()).first():
        return jsonify({"error": "An account with that email already exists."}), 409

    if len(data["password"]) < 8:
        return jsonify({"error": "Password must be at least 8 characters."}), 400

    user = User(full_name=data["full_name"].strip(), email=data["email"].lower().strip())
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Account created successfully.", "user_id": user.id}), 201


@api_bp.route("/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").lower().strip()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password."}), 401
    if not user.is_active_user:
        return jsonify({"error": "This account has been deactivated."}), 403

    login_user(user)
    return jsonify({"message": "Login successful.", "user_id": user.id, "is_admin": user.is_admin})


@api_bp.route("/predict", methods=["POST"])
@login_required
def api_predict():
    data = request.get_json(silent=True) or {}

    required_fields = [
        "age", "income", "loan_amount", "credit_score", "months_employed",
        "num_credit_lines", "interest_rate", "loan_term", "dti_ratio",
        "education", "employment_type", "marital_status", "has_mortgage",
        "has_dependents", "loan_purpose", "has_co_signer",
    ]
    missing = [f for f in required_fields if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        result = ml_service.predict(data)
    except (ValueError, KeyError) as exc:
        return jsonify({"error": f"Invalid input: {exc}"}), 400

    record = Prediction(
        user_id=current_user.id,
        age=int(data["age"]),
        income=float(data["income"]),
        loan_amount=float(data["loan_amount"]),
        credit_score=int(data["credit_score"]),
        months_employed=int(data["months_employed"]),
        num_credit_lines=int(data["num_credit_lines"]),
        interest_rate=float(data["interest_rate"]),
        loan_term=int(data["loan_term"]),
        dti_ratio=float(data["dti_ratio"]),
        education=data["education"],
        employment_type=data["employment_type"],
        marital_status=data["marital_status"],
        has_mortgage=data["has_mortgage"],
        has_dependents=data["has_dependents"],
        loan_purpose=data["loan_purpose"],
        has_co_signer=data["has_co_signer"],
        prediction_label=result["label"],
        probability=result["probability"],
        recommendation=result["recommendation"],
        explanation=json.dumps(result["reasons"]),
    )
    db.session.add(record)
    db.session.commit()

    return jsonify(
        {
            "prediction_id": record.id,
            "label": result["label"],
            "probability": round(result["probability"], 4),
            "recommendation": result["recommendation"],
            "reasons": result["reasons"],
        }
    ), 201


@api_bp.route("/history", methods=["GET"])
@login_required
def api_history():
    predictions = (
        Prediction.query.filter_by(user_id=current_user.id)
        .order_by(Prediction.created_at.desc())
        .all()
    )
    return jsonify([p.to_dict() for p in predictions])
