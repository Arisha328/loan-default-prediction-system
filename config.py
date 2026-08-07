"""
config.py
---------
Central configuration for the AI Loan Default Prediction System.
Values are read from environment variables where possible so the same
codebase can run locally, in CI, or on a PaaS like Render/Heroku/Railway.
"""

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # --- Core Flask ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    WTF_CSRF_ENABLED = True

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'database', 'loan_app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- ML Artifacts ---
    MODEL_DIR = os.path.join(BASE_DIR, "model")
    MODEL_PATH = os.path.join(MODEL_DIR, "loan_model.pkl")
    SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
    ENCODERS_PATH = os.path.join(MODEL_DIR, "label_encoders.pkl")
    FEATURE_COLUMNS_PATH = os.path.join(MODEL_DIR, "feature_columns.pkl")
    METRICS_PATH = os.path.join(MODEL_DIR, "metrics.json")
    CHART_DATA_PATH = os.path.join(MODEL_DIR, "dataset_chart_data.json")

    # --- Session ---
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # 8 hours
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # --- Pagination ---
    HISTORY_PAGE_SIZE = 10

    # --- Profile avatar uploads ---
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "avatars")
    ALLOWED_AVATAR_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4 MB upload cap
    AVATAR_SIZE = 320  # px, square, after server-side crop/resize

    # --- Public contact details (footer / contact page) ---
    SITE_CONTACT_EMAIL = os.environ.get("SITE_CONTACT_EMAIL", "designer23@gmail.com")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
