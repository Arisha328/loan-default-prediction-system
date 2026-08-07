"""
routes/main.py
---------------
Landing page, dashboard, prediction flow, history, exports, and the static
informational pages (about / contact / faq).
"""

import json
import os
from datetime import datetime, timedelta

from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required

from config import Config
from extensions import db
from forms import ChangePasswordForm, ContactForm, PredictionForm, ProfileForm
from models import Prediction
from services import avatar_service, export_service, ml_service

main_bp = Blueprint("main", __name__)


# ---------------------------------------------------------------- Landing --
@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


# --------------------------------------------------------------- Dashboard --
@main_bp.route("/dashboard")
@login_required
def dashboard():
    user_predictions = Prediction.query.filter_by(user_id=current_user.id)

    total_predictions = user_predictions.count()
    high_risk = user_predictions.filter_by(prediction_label="High Risk").count()
    low_risk = total_predictions - high_risk

    recent = (
        user_predictions.order_by(Prediction.created_at.desc()).limit(5).all()
    )

    # Monthly prediction counts (last 6 months) for the trend chart
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    monthly_rows = (
        user_predictions.filter(Prediction.created_at >= six_months_ago)
        .with_entities(Prediction.created_at, Prediction.prediction_label)
        .all()
    )
    monthly_counts = {}
    for created_at, _ in monthly_rows:
        key = created_at.strftime("%b %Y")
        monthly_counts[key] = monthly_counts.get(key, 0) + 1

    return render_template(
        "dashboard.html",
        total_predictions=total_predictions,
        high_risk=high_risk,
        low_risk=low_risk,
        recent=recent,
        monthly_labels=list(monthly_counts.keys()),
        monthly_values=list(monthly_counts.values()),
    )


# -------------------------------------------------------------- Prediction --
@main_bp.route("/predict", methods=["GET", "POST"])
@login_required
def predict():
    form = PredictionForm()

    if form.validate_on_submit():
        payload = {
            "age": form.age.data,
            "income": form.income.data,
            "loan_amount": form.loan_amount.data,
            "credit_score": form.credit_score.data,
            "months_employed": form.months_employed.data,
            "num_credit_lines": form.num_credit_lines.data,
            "interest_rate": form.interest_rate.data,
            "loan_term": int(form.loan_term.data),
            "dti_ratio": form.dti_ratio.data,
            "education": form.education.data,
            "employment_type": form.employment_type.data,
            "marital_status": form.marital_status.data,
            "has_mortgage": form.has_mortgage.data,
            "has_dependents": form.has_dependents.data,
            "loan_purpose": form.loan_purpose.data,
            "has_co_signer": form.has_co_signer.data,
        }

        result = ml_service.predict(payload)

        record = Prediction(
            user_id=current_user.id,
            age=payload["age"],
            income=payload["income"],
            loan_amount=payload["loan_amount"],
            credit_score=payload["credit_score"],
            months_employed=payload["months_employed"],
            num_credit_lines=payload["num_credit_lines"],
            interest_rate=payload["interest_rate"],
            loan_term=payload["loan_term"],
            dti_ratio=payload["dti_ratio"],
            education=payload["education"],
            employment_type=payload["employment_type"],
            marital_status=payload["marital_status"],
            has_mortgage=payload["has_mortgage"],
            has_dependents=payload["has_dependents"],
            loan_purpose=payload["loan_purpose"],
            has_co_signer=payload["has_co_signer"],
            prediction_label=result["label"],
            probability=result["probability"],
            recommendation=result["recommendation"],
            explanation=json.dumps(result["reasons"]),
        )
        db.session.add(record)
        db.session.commit()

        return redirect(url_for("main.result", prediction_id=record.id))

    return render_template("predict.html", form=form)


@main_bp.route("/result/<int:prediction_id>")
@login_required
def result(prediction_id):
    record = Prediction.query.get_or_404(prediction_id)
    if record.user_id != current_user.id and not current_user.is_admin:
        flash("You do not have permission to view that prediction.", "danger")
        return redirect(url_for("main.dashboard"))

    reasons = json.loads(record.explanation)
    return render_template("result.html", record=record, reasons=reasons)


# ----------------------------------------------------------------- History --
@main_bp.route("/history")
@login_required
def history():
    page = request.args.get("page", 1, type=int)
    pagination = (
        Prediction.query.filter_by(user_id=current_user.id)
        .order_by(Prediction.created_at.desc())
        .paginate(page=page, per_page=Config.HISTORY_PAGE_SIZE, error_out=False)
    )
    return render_template("history.html", pagination=pagination)


@main_bp.route("/history/export/csv")
@login_required
def export_history_csv():
    predictions = (
        Prediction.query.filter_by(user_id=current_user.id)
        .order_by(Prediction.created_at.desc())
        .all()
    )
    csv_bytes = export_service.predictions_to_csv(predictions)
    return Response(
        csv_bytes,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=prediction_history.csv"},
    )


@main_bp.route("/result/<int:prediction_id>/export/pdf")
@login_required
def export_result_pdf(prediction_id):
    record = Prediction.query.get_or_404(prediction_id)
    if record.user_id != current_user.id and not current_user.is_admin:
        flash("You do not have permission to export that prediction.", "danger")
        return redirect(url_for("main.dashboard"))

    pdf_bytes = export_service.single_prediction_to_pdf(record, record.user)
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=loan_report_{record.id}.pdf"},
    )


# --------------------------------------------------------------- Profile --
@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    profile_form = ProfileForm(prefix="profile", obj=current_user)
    password_form = ChangePasswordForm(prefix="pwd")

    if "profile-submit" in request.form and profile_form.validate_on_submit():
        current_user.full_name = profile_form.full_name.data.strip()

        avatar_file = profile_form.avatar.data
        if avatar_file and avatar_file.filename:
            new_filename = avatar_service.save_avatar(avatar_file, previous_filename=current_user.profile_image)
            current_user.profile_image = new_filename

        db.session.commit()
        flash("Your profile has been updated.", "success")
        return redirect(url_for("main.profile"))

    if "pwd-submit_password" in request.form and password_form.validate_on_submit():
        if not current_user.check_password(password_form.current_password.data):
            flash("Your current password is incorrect.", "danger")
        else:
            current_user.set_password(password_form.new_password.data)
            db.session.commit()
            flash("Your password has been updated.", "success")
        return redirect(url_for("main.profile"))

    return render_template("profile.html", profile_form=profile_form, password_form=password_form)


# ------------------------------------------------------------- Theme toggle --
@main_bp.route("/toggle-theme", methods=["POST"])
@login_required
def toggle_theme():
    current_user.theme_preference = "dark" if current_user.theme_preference == "light" else "light"
    db.session.commit()
    return {"theme": current_user.theme_preference}


# ------------------------------------------------------------- Static pages --
@main_bp.route("/about")
def about():
    metrics = {}
    if os.path.exists(Config.METRICS_PATH):
        with open(Config.METRICS_PATH) as f:
            metrics = json.load(f)
    return render_template("about.html", metrics=metrics)


@main_bp.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        # In production this would enqueue an email / ticket. For this
        # self-contained project we simply acknowledge receipt.
        flash("Thanks for reaching out! Our team will get back to you within 24 hours.", "success")
        return redirect(url_for("main.contact"))
    return render_template("contact.html", form=form)


@main_bp.route("/faq")
def faq():
    return render_template("faq.html")


# ---------------------------------------------------------------- SEO --
@main_bp.route("/robots.txt")
def robots_txt():
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /dashboard",
        "Disallow: /predict",
        "Disallow: /history",
        "Disallow: /profile",
        "Disallow: /admin",
        "Disallow: /result",
        f"Sitemap: {request.url_root.rstrip('/')}{url_for('main.sitemap_xml')}",
    ]
    return Response("\n".join(lines), mimetype="text/plain")


@main_bp.route("/sitemap.xml")
def sitemap_xml():
    pages = [
        (url_for("main.index"), "1.0"),
        (url_for("main.about"), "0.8"),
        (url_for("main.faq"), "0.6"),
        (url_for("main.contact"), "0.6"),
        (url_for("auth.login"), "0.5"),
        (url_for("auth.register"), "0.7"),
    ]
    root = request.url_root.rstrip("/")
    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, priority in pages:
        xml_parts.append(f"<url><loc>{root}{path}</loc><priority>{priority}</priority></url>")
    xml_parts.append("</urlset>")
    return Response("\n".join(xml_parts), mimetype="application/xml")
