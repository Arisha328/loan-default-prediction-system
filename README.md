# AI Loan Default Prediction System

A full-stack, production-ready web application that predicts loan default risk
using a machine learning model trained on real historical loan data. Built with
Flask, SQLAlchemy, and a Logistic Regression classifier, with a modern
fintech-styled Bootstrap 5 front end.

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-3.x-black)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

- **Landing page** — hero, about, features, ML workflow, tech stack, CTA
- **Authentication** — registration, login, logout, hashed passwords, sessions, admin login
- **Dashboard** — total predictions, risk split, monthly trend, recent predictions, live charts
- **Prediction form** — 16-field applicant profile, instant risk verdict
- **ML integration** — loads a trained `loan_model.pkl`, `scaler.pkl`, and `label_encoders.pkl`, and returns `predict_proba()` output
- **Explainable AI** — plain-language reasons generated from model coefficients × scaled feature values
- **Prediction history** — paginated table, CSV export, per-result PDF export
- **Admin dashboard** — manage users (activate/deactivate/delete), manage predictions, aggregate stats
- **Data visualization** — Chart.js dashboards (risk split, monthly trend, age/income/credit-score/default distributions)
- **Dark mode** — toggle, persisted per-user (DB) or per-browser (localStorage) for guests
- **Static pages** — About, Contact (with form), FAQ, custom 404 / 500 / 403 pages
- **REST API** — `/api/register`, `/api/login`, `/api/predict`, `/api/history`
- **Security** — password hashing (Werkzeug/PBKDF2), CSRF protection (Flask-WTF), server-side input validation, SQLAlchemy ORM (parameterized queries), no inline script execution of user input

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, Bootstrap 5, JavaScript, Font Awesome, Chart.js |
| Backend | Python, Flask, Jinja2, Flask-Login, Flask-WTF |
| ML | Pandas, NumPy, Scikit-Learn, Joblib |
| Database | SQLite via SQLAlchemy ORM |
| Reports | ReportLab (PDF), built-in `csv` (CSV) |
| Deployment | Gunicorn, Procfile, runtime.txt |

## Project Structure

```
Loan-Default-Prediction/
├── app.py                  # Application factory, error handlers, blueprint registration
├── config.py                # Environment-driven configuration
├── extensions.py             # db, csrf, login_manager singletons
├── models.py                 # User, Prediction SQLAlchemy models
├── forms.py                  # Flask-WTF forms (register/login/predict/contact)
├── requirements.txt
├── README.md
├── Procfile
├── runtime.txt
├── .gitignore
│
├── ml/
│   └── train_model.py        # Trains & persists the model from Loan_default.csv
│
├── model/
│   ├── loan_model.pkl
│   ├── scaler.pkl
│   ├── label_encoders.pkl
│   ├── feature_columns.pkl
│   ├── metrics.json
│   └── dataset_chart_data.json
│
├── database/                 # SQLite file created here at runtime
│
├── routes/
│   ├── auth.py                # /register /login /logout
│   ├── main.py                 # landing, dashboard, predict, result, history, static pages
│   ├── admin.py                 # admin dashboard, user & prediction management
│   └── api.py                   # JSON REST API
│
├── services/
│   ├── ml_service.py            # predict() + rule-based explanation
│   └── export_service.py        # CSV / PDF generation
│
├── utils/
│   └── template_filters.py      # currency / percent Jinja filters
│
├── static/
│   ├── css/style.css            # design system
│   ├── js/main.js               # theme toggle, gauge animation, misc UI
│   └── js/charts.js             # Chart.js dashboard charts
│
└── templates/
    ├── base.html, index.html, login.html, register.html
    ├── dashboard.html, predict.html, result.html, history.html
    ├── about.html, contact.html, faq.html
    ├── admin.html, admin_users.html, admin_predictions.html
    ├── 404.html, 500.html, 403.html
    └── partials/gauge.html
```

## Getting Started

### 1. Clone & create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Train the model (already trained artifacts are included in `model/`)

If you want to retrain on your own copy of the dataset:

```bash
python ml/train_model.py --csv path/to/Loan_default.csv --out model
```

### 4. Run the app

```bash
python app.py
```

Visit **http://localhost:5000**. On first run, a SQLite database is created
automatically at `database/loan_app.db`, along with a default admin account
seeded from the `ADMIN_EMAIL` / `ADMIN_PASSWORD` environment variables below.

> **Always set `ADMIN_EMAIL` and `ADMIN_PASSWORD` explicitly before deploying**
> to any shared or public environment — never rely on the fallback defaults
> in production, and never display admin credentials in the UI.

### 5. Environment variables (optional)

| Variable | Purpose | Default |
|---|---|---|
| `SECRET_KEY` | Flask session/CSRF signing key | dev key (change in production) |
| `DATABASE_URL` | SQLAlchemy database URI | `sqlite:///database/loan_app.db` |
| `ADMIN_EMAIL` | Seed admin email | *(set your own — no public default)* |
| `ADMIN_PASSWORD` | Seed admin password | *(set your own — no public default)* |
| `SITE_CONTACT_EMAIL` | Public support email shown in footer/contact page | `designer23@gmail.com` |
| `FLASK_ENV` | `development` or `production` | `development` |
| `PORT` | Port for `python app.py` | `5000` |

## Deployment

The app ships with a `Procfile` and `runtime.txt` for PaaS platforms
(Render, Railway, Heroku-compatible hosts):

```bash
gunicorn "app:app"
```

Make sure `SECRET_KEY`, `ADMIN_EMAIL`, and `ADMIN_PASSWORD` are set as real
secrets in your host's environment configuration, and that `DATABASE_URL`
points at a persistent volume or managed database if your platform's
filesystem is ephemeral.

## API Reference

All endpoints return/accept JSON.

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/api/register` | none | Create an account |
| POST | `/api/login` | none | Log in (creates a session) |
| POST | `/api/predict` | session | Run a prediction, returns label/probability/reasons |
| GET | `/api/history` | session | List the current user's prediction history |

## Model Details

- **Algorithm:** Logistic Regression (`class_weight="balanced"`)
- **Preprocessing:** `LabelEncoder` for 7 categorical fields, `StandardScaler` for 9 numeric fields
- **Training/test split:** 80/20, stratified by target
- **Swappable:** replace the estimator in `ml/train_model.py` with `RandomForestClassifier` or `XGBClassifier` and rerun — the rest of the app (scaler, encoders, feature order, explanation logic) is compatible with any scikit-learn classifier exposing `predict_proba()` and `coef_`. (Tree-based models will need the explanation step swapped for `feature_importances_` or SHAP.)

## Security Notes

- Passwords are hashed with Werkzeug's `generate_password_hash` (PBKDF2-SHA256), never stored in plain text.
- All forms are protected by Flask-WTF's CSRF tokens.
- All database access goes through the SQLAlchemy ORM (no raw string-built SQL), preventing SQL injection.
- User-supplied content is rendered through Jinja2's autoescaping, preventing reflected XSS.
- Admins cannot delete or deactivate their own account through the UI, preventing accidental lockout.

## License

MIT — built for educational and portfolio purposes.
