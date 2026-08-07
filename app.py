"""
app.py
------
Application factory for the AI Loan Default Prediction System.

Run locally:
    python app.py

Run with Gunicorn (production):
    gunicorn "app:create_app()"
"""

import os

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import current_user

from config import config_by_name
from extensions import csrf, db, login_manager
from models import User
from utils.template_filters import register_filters


def create_app(config_name=None):
    config_name = config_name or os.environ.get("FLASK_ENV", "development")
    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["development"]))

    # Ensure the database directory and avatar upload directory exist
    os.makedirs(os.path.join(app.root_path, "database"), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)

    register_filters(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # --- Register blueprints ---
    from routes.admin import admin_bp
    from routes.api import api_bp
    from routes.auth import auth_bp
    from routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    csrf.exempt(api_bp)  # JSON API uses its own auth; CSRF is for form/browser flows

    # --- Context processor: expose current_user's theme everywhere ---
    @app.context_processor
    def inject_globals():
        theme = "light"
        if current_user.is_authenticated:
            theme = current_user.theme_preference
        return {
            "active_theme": theme,
            "app_name": "AI Loan Default Prediction System",
            "site_contact_email": app.config.get("SITE_CONTACT_EMAIL", "designer23@gmail.com"),
        }

    # --- Error handlers ---
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("500.html"), 500

    @app.errorhandler(403)
    def forbidden(e):
        return render_template("403.html"), 403

    @app.errorhandler(413)
    def file_too_large(e):
        flash("That file is too large. Please upload an image under 4 MB.", "danger")
        return redirect(request.referrer or url_for("main.index"))

    with app.app_context():
        db.create_all()
        _ensure_admin_account(db, User)

    return app


def _ensure_admin_account(db, User):
    """Creates a default admin account on first run if none exists."""
    admin_email = os.environ.get("ADMIN_EMAIL", "designer23@gmail.com")
    existing_admin = User.query.filter_by(is_admin=True).first()
    if not existing_admin:
        admin = User(full_name="System Administrator", email=admin_email, is_admin=True)
        admin.set_password(os.environ.get("ADMIN_PASSWORD", "Admin@12345"))
        db.session.add(admin)
        db.session.commit()


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=app.config.get("DEBUG", False))
