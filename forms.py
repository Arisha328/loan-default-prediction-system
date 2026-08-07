"""
forms.py
--------
Flask-WTF forms. Using WTForms gives us CSRF protection automatically
(via Flask-WTF) plus server-side input validation for every form in the app.
"""

from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import (
    BooleanField,
    FloatField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    SubmitField,
    TextAreaField,
)
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional


class RegisterForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email Address", validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, message="Password must be at least 8 characters.")])
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Create Account")


class LoginForm(FlaskForm):
    email = StringField("Email Address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Login")


class PredictionForm(FlaskForm):
    age = IntegerField("Age", validators=[DataRequired(), NumberRange(min=18, max=100)])
    income = FloatField("Annual Income ($)", validators=[DataRequired(), NumberRange(min=0)])
    loan_amount = FloatField("Loan Amount ($)", validators=[DataRequired(), NumberRange(min=0)])
    credit_score = IntegerField("Credit Score", validators=[DataRequired(), NumberRange(min=300, max=850)])
    months_employed = IntegerField("Months Employed", validators=[DataRequired(), NumberRange(min=0, max=720)])
    num_credit_lines = IntegerField("Number of Credit Lines", validators=[DataRequired(), NumberRange(min=0, max=50)])
    interest_rate = FloatField("Interest Rate (%)", validators=[DataRequired(), NumberRange(min=0, max=100)])
    loan_term = SelectField(
        "Loan Term (months)",
        choices=[("12", "12"), ("24", "24"), ("36", "36"), ("48", "48"), ("60", "60")],
        validators=[DataRequired()],
    )
    dti_ratio = FloatField("Debt-to-Income Ratio", validators=[DataRequired(), NumberRange(min=0, max=1)])

    education = SelectField(
        "Education",
        choices=[("High School", "High School"), ("Bachelor's", "Bachelor's"), ("Master's", "Master's"), ("PhD", "PhD")],
        validators=[DataRequired()],
    )
    employment_type = SelectField(
        "Employment Type",
        choices=[("Full-time", "Full-time"), ("Part-time", "Part-time"), ("Self-employed", "Self-employed"), ("Unemployed", "Unemployed")],
        validators=[DataRequired()],
    )
    marital_status = SelectField(
        "Marital Status",
        choices=[("Single", "Single"), ("Married", "Married"), ("Divorced", "Divorced")],
        validators=[DataRequired()],
    )
    has_mortgage = SelectField("Has Mortgage", choices=[("Yes", "Yes"), ("No", "No")], validators=[DataRequired()])
    has_dependents = SelectField("Has Dependents", choices=[("Yes", "Yes"), ("No", "No")], validators=[DataRequired()])
    loan_purpose = SelectField(
        "Loan Purpose",
        choices=[("Auto", "Auto"), ("Business", "Business"), ("Education", "Education"), ("Home", "Home"), ("Other", "Other")],
        validators=[DataRequired()],
    )
    has_co_signer = SelectField("Has Co-Signer", choices=[("Yes", "Yes"), ("No", "No")], validators=[DataRequired()])

    submit = SubmitField("Predict")


class ContactForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email Address", validators=[DataRequired(), Email()])
    subject = StringField("Subject", validators=[DataRequired(), Length(max=150)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(max=2000)])
    submit = SubmitField("Send Message")


class ProfileForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=120)])
    avatar = FileField(
        "Profile Picture",
        validators=[FileAllowed(["png", "jpg", "jpeg", "webp"], "Images only (PNG, JPG, WEBP).")],
    )
    submit = SubmitField("Save Changes")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField(
        "New Password", validators=[DataRequired(), Length(min=8, message="Password must be at least 8 characters.")]
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[DataRequired(), EqualTo("new_password", message="Passwords must match.")],
    )
    submit_password = SubmitField("Update Password")
