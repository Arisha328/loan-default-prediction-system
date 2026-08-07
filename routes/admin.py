"""
routes/admin.py
-----------------
Admin-only views: manage users, manage predictions, view aggregate stats.
Protected by the `admin_required` decorator, which builds on Flask-Login's
current_user and checks the is_admin flag.
"""

from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from extensions import db
from models import Prediction, User

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return view_func(*args, **kwargs)

    return wrapped


@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_predictions = Prediction.query.count()
    high_risk = Prediction.query.filter_by(prediction_label="High Risk").count()
    low_risk = total_predictions - high_risk

    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_predictions = Prediction.query.order_by(Prediction.created_at.desc()).limit(8).all()

    return render_template(
        "admin.html",
        total_users=total_users,
        total_predictions=total_predictions,
        high_risk=high_risk,
        low_risk=low_risk,
        recent_users=recent_users,
        recent_predictions=recent_predictions,
    )


@admin_bp.route("/users")
@login_required
@admin_required
def users():
    all_users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin_users.html", users=all_users)


@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot delete your own admin account.", "danger")
        return redirect(url_for("admin.users"))

    db.session.delete(user)
    db.session.commit()
    flash(f"User {user.email} and their predictions were deleted.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/users/<int:user_id>/toggle-active", methods=["POST"])
@login_required
@admin_required
def toggle_active(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own admin account.", "danger")
        return redirect(url_for("admin.users"))

    user.is_active_user = not user.is_active_user
    db.session.commit()
    status = "activated" if user.is_active_user else "deactivated"
    flash(f"User {user.email} {status}.", "success")
    return redirect(url_for("admin.users"))


@admin_bp.route("/predictions")
@login_required
@admin_required
def predictions():
    all_predictions = Prediction.query.order_by(Prediction.created_at.desc()).all()
    return render_template("admin_predictions.html", predictions=all_predictions)


@admin_bp.route("/predictions/<int:prediction_id>/delete", methods=["POST"])
@login_required
@admin_required
def delete_prediction(prediction_id):
    record = Prediction.query.get_or_404(prediction_id)
    db.session.delete(record)
    db.session.commit()
    flash("Prediction record deleted.", "success")
    return redirect(url_for("admin.predictions"))
