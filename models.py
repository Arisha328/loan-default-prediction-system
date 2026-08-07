"""
models.py
---------
SQLAlchemy ORM models for the AI Loan Default Prediction System.

Tables
------
User        - registered users (and admins, distinguished by is_admin)
Prediction  - one row per prediction made by a user, stored for history,
              the dashboard, admin views, and CSV/PDF export.
"""

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active_user = db.Column(db.Boolean, default=True, nullable=False)
    theme_preference = db.Column(db.String(10), default="light", nullable=False)
    profile_image = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def initials(self):
        parts = [p for p in self.full_name.strip().split(" ") if p]
        if not parts:
            return "?"
        if len(parts) == 1:
            return parts[0][0].upper()
        return (parts[0][0] + parts[-1][0]).upper()

    predictions = db.relationship(
        "Prediction", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        return check_password_hash(self.password_hash, raw_password)

    # Flask-Login requires this to reflect account status
    @property
    def is_active(self):
        return self.is_active_user

    def __repr__(self):
        return f"<User {self.email}>"


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # --- Raw inputs (kept for history / re-display / export) ---
    age = db.Column(db.Integer, nullable=False)
    income = db.Column(db.Float, nullable=False)
    loan_amount = db.Column(db.Float, nullable=False)
    credit_score = db.Column(db.Integer, nullable=False)
    months_employed = db.Column(db.Integer, nullable=False)
    num_credit_lines = db.Column(db.Integer, nullable=False)
    interest_rate = db.Column(db.Float, nullable=False)
    loan_term = db.Column(db.Integer, nullable=False)
    dti_ratio = db.Column(db.Float, nullable=False)
    education = db.Column(db.String(50), nullable=False)
    employment_type = db.Column(db.String(50), nullable=False)
    marital_status = db.Column(db.String(50), nullable=False)
    has_mortgage = db.Column(db.String(10), nullable=False)
    has_dependents = db.Column(db.String(10), nullable=False)
    loan_purpose = db.Column(db.String(50), nullable=False)
    has_co_signer = db.Column(db.String(10), nullable=False)

    # --- Model output ---
    prediction_label = db.Column(db.String(10), nullable=False)  # "Low Risk" / "High Risk"
    probability = db.Column(db.Float, nullable=False)  # probability of default (0-1)
    recommendation = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=False)  # JSON-encoded list of reason strings

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.created_at.strftime("%Y-%m-%d %H:%M"),
            "age": self.age,
            "income": self.income,
            "credit_score": self.credit_score,
            "loan_amount": self.loan_amount,
            "prediction": self.prediction_label,
            "probability": round(self.probability * 100, 2),
            "recommendation": self.recommendation,
        }
