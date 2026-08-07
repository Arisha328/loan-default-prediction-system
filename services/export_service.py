"""
services/export_service.py
----------------------------
Generates downloadable CSV and PDF exports of a user's prediction history
(or a single prediction report).
"""

import csv
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def predictions_to_csv(predictions):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Prediction ID",
            "Date",
            "Age",
            "Income",
            "Credit Score",
            "Loan Amount",
            "Prediction",
            "Probability (%)",
            "Recommendation",
        ]
    )
    for p in predictions:
        d = p.to_dict()
        writer.writerow(
            [
                d["id"],
                d["date"],
                d["age"],
                d["income"],
                d["credit_score"],
                d["loan_amount"],
                d["prediction"],
                d["probability"],
                d["recommendation"],
            ]
        )
    output.seek(0)
    return output.getvalue().encode("utf-8")


def single_prediction_to_pdf(prediction, user):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle", parent=styles["Title"], textColor=colors.HexColor("#12213F"), spaceAfter=6
    )
    normal = styles["Normal"]

    risk_color = colors.HexColor("#C23B4B") if prediction.prediction_label == "High Risk" else colors.HexColor("#1E8E5A")

    elements = [
        Paragraph("AI Loan Default Prediction Report", title_style),
        Paragraph(f"Generated for: {user.full_name} ({user.email})", normal),
        Paragraph(f"Date: {prediction.created_at.strftime('%B %d, %Y %H:%M')}", normal),
        Spacer(1, 16),
        Paragraph(
            f'<font color="{risk_color.hexval()}"><b>Result: {prediction.prediction_label}</b></font>'
            f" &nbsp;&nbsp; Default Probability: {round(prediction.probability * 100, 2)}%",
            styles["Heading2"],
        ),
        Spacer(1, 10),
    ]

    data = [
        ["Field", "Value"],
        ["Age", prediction.age],
        ["Income", f"${prediction.income:,.0f}"],
        ["Loan Amount", f"${prediction.loan_amount:,.0f}"],
        ["Credit Score", prediction.credit_score],
        ["Months Employed", prediction.months_employed],
        ["Number of Credit Lines", prediction.num_credit_lines],
        ["Interest Rate", f"{prediction.interest_rate}%"],
        ["Loan Term", f"{prediction.loan_term} months"],
        ["DTI Ratio", prediction.dti_ratio],
        ["Education", prediction.education],
        ["Employment Type", prediction.employment_type],
        ["Marital Status", prediction.marital_status],
        ["Has Mortgage", prediction.has_mortgage],
        ["Has Dependents", prediction.has_dependents],
        ["Loan Purpose", prediction.loan_purpose],
        ["Has Co-Signer", prediction.has_co_signer],
    ]
    table = Table(data, colWidths=[220, 260])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#12213F")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#D9DEE8")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F7FB")]),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 16))
    elements.append(Paragraph("Recommendation", styles["Heading3"]))
    elements.append(Paragraph(prediction.recommendation, normal))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()
