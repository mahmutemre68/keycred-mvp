"""
KeyCred Score Certificate Generator
────────────────────────────────────
Generates a premium, anti-fraud PDF certificate with QR code
for tenants who have been approved (keycred_score >= 650).
"""

import hashlib
import io
import os
import uuid
from datetime import datetime, timedelta, timezone

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


# ── Constants ─────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
LOGO_PATH = os.path.join(os.path.dirname(__file__), "keycred-logo.png")

# Colour palette (matching frontend dark theme)
DARK_BG = colors.HexColor("#0a0e1a")
CARD_BG = colors.HexColor("#111827")
ACCENT = colors.HexColor("#6366f1")
ACCENT_LIGHT = colors.HexColor("#818cf8")
GREEN = colors.HexColor("#34d399")
GOLD = colors.HexColor("#fbbf24")
RED = colors.HexColor("#f87171")
TEXT_PRIMARY = colors.HexColor("#f1f5f9")
TEXT_MUTED = colors.HexColor("#94a3b8")
BORDER_COLOR = colors.HexColor("#1e293b")


def _risk_color(risk_level: str) -> colors.HexColor:
    return {"LOW": GREEN, "MEDIUM": GOLD, "HIGH": RED}.get(risk_level, TEXT_MUTED)


def _generate_certificate_id() -> str:
    """Create a unique certificate ID."""
    return f"KC-{uuid.uuid4().hex[:8].upper()}"


def _generate_verification_hash(cert_id: str, score: int, tenant_name: str) -> str:
    """SHA-256 hash for anti-fraud verification."""
    payload = f"{cert_id}:{score}:{tenant_name}:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    return hashlib.sha256(payload.encode()).hexdigest()[:24]


def _draw_watermark(c: canvas.Canvas):
    """Draw diagonal repeating watermark text."""
    c.saveState()
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#1a1f36"))
    c.rotate(35)
    for x in range(-200, 900, 180):
        for y in range(-400, 600, 60):
            c.drawString(x, y, "KEYCRED VERIFIED  •  KEYCRED VERIFIED")
    c.restoreState()


def _draw_border(c: canvas.Canvas):
    """Draw an ornamental double border."""
    # Outer border
    c.setStrokeColor(ACCENT)
    c.setLineWidth(2)
    c.roundRect(12 * mm, 12 * mm, PAGE_W - 24 * mm, PAGE_H - 24 * mm, 8 * mm)
    # Inner border
    c.setStrokeColor(BORDER_COLOR)
    c.setLineWidth(0.5)
    c.roundRect(15 * mm, 15 * mm, PAGE_W - 30 * mm, PAGE_H - 30 * mm, 6 * mm)


def _draw_qr(c: canvas.Canvas, data: str, x: float, y: float, size: float = 32 * mm):
    """Generate and draw a QR code on the canvas."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#6366f1", back_color="#111827").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    c.drawImage(ImageReader(buf), x, y, width=size, height=size, mask="auto")


def generate_certificate(
    tenant_name: str,
    keycred_score: int,
    max_rent_limit: float,
    risk_level: str,
    score_breakdown: dict,
    mocked_parameters: dict,
) -> tuple[bytes, str]:
    """
    Generate a premium PDF certificate for an approved tenant.

    Returns the PDF file as bytes.
    """
    cert_id = _generate_certificate_id()
    verification_hash = _generate_verification_hash(cert_id, keycred_score, tenant_name)
    issue_date = datetime.now(timezone.utc)
    expiry_date = issue_date + timedelta(days=90)

    qr_payload = (
        f"https://keycred.io/verify?"
        f"id={cert_id}&hash={verification_hash}&score={keycred_score}"
    )

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)

    # ── Background ────────────────────────────────────────────────────
    c.setFillColor(DARK_BG)
    c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # ── Watermark ─────────────────────────────────────────────────────
    _draw_watermark(c)

    # ── Border ────────────────────────────────────────────────────────
    _draw_border(c)

    y = PAGE_H - 35 * mm

    # ── Logo ──────────────────────────────────────────────────────────
    if os.path.exists(LOGO_PATH):
        logo_size = 22 * mm
        c.drawImage(
            LOGO_PATH,
            (PAGE_W - logo_size) / 2,
            y - logo_size + 5 * mm,
            width=logo_size,
            height=logo_size,
            preserveAspectRatio=True,
            mask="auto",
        )
        y -= logo_size + 4 * mm

    # ── Title ─────────────────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(TEXT_PRIMARY)
    c.drawCentredString(PAGE_W / 2, y, "KEYCRED")
    y -= 8 * mm
    c.setFont("Helvetica", 11)
    c.setFillColor(ACCENT_LIGHT)
    c.drawCentredString(PAGE_W / 2, y, "TENANT CREDITWORTHINESS CERTIFICATE")
    y -= 5 * mm
    c.setFont("Helvetica-Oblique", 8)
    c.setFillColor(TEXT_MUTED)
    c.drawCentredString(PAGE_W / 2, y, "Because trust is priceless")
    y -= 10 * mm

    # ── Divider ───────────────────────────────────────────────────────
    c.setStrokeColor(ACCENT)
    c.setLineWidth(0.8)
    c.line(30 * mm, y, PAGE_W - 30 * mm, y)
    y -= 10 * mm

    # ── Certificate meta ──────────────────────────────────────────────
    c.setFont("Helvetica", 8)
    c.setFillColor(TEXT_MUTED)
    c.drawString(22 * mm, y, f"Certificate ID: {cert_id}")
    c.drawRightString(PAGE_W - 22 * mm, y, f"Verification: {verification_hash}")
    y -= 12 * mm

    # ── Tenant name ───────────────────────────────────────────────────
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawCentredString(PAGE_W / 2, y, "This certificate is issued to")
    y -= 10 * mm
    c.setFont("Helvetica-Bold", 22)
    c.setFillColor(TEXT_PRIMARY)
    c.drawCentredString(PAGE_W / 2, y, tenant_name.upper())
    y -= 14 * mm

    # ── Score display ─────────────────────────────────────────────────
    score_color = _risk_color(risk_level)

    # Score circle background
    circle_x = PAGE_W / 2
    circle_y = y - 18 * mm
    c.setFillColor(CARD_BG)
    c.circle(circle_x, circle_y, 22 * mm, fill=1, stroke=0)
    c.setStrokeColor(score_color)
    c.setLineWidth(3)
    c.circle(circle_x, circle_y, 22 * mm, fill=0, stroke=1)

    # Score number
    c.setFont("Helvetica-Bold", 32)
    c.setFillColor(score_color)
    c.drawCentredString(circle_x, circle_y - 2 * mm, str(keycred_score))
    c.setFont("Helvetica", 8)
    c.setFillColor(TEXT_MUTED)
    c.drawCentredString(circle_x, circle_y - 8 * mm, "/ 1000")
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString(circle_x, circle_y + 14 * mm, "KEYCRED SCORE")

    y = circle_y - 32 * mm

    # ── Risk level badge ──────────────────────────────────────────────
    badge_text = f"Risk Level: {risk_level}"
    c.setFont("Helvetica-Bold", 10)
    tw = c.stringWidth(badge_text, "Helvetica-Bold", 10)
    badge_x = (PAGE_W - tw) / 2 - 8 * mm
    badge_w = tw + 16 * mm

    c.setStrokeColor(score_color)
    c.roundRect(badge_x, y - 2 * mm, badge_w, 8 * mm, 3 * mm, fill=0, stroke=1)
    c.setFillColor(score_color)
    c.drawCentredString(PAGE_W / 2, y, badge_text)
    y -= 16 * mm

    # ── Key metrics table ─────────────────────────────────────────────
    metrics = [
        ("Max Rent Limit", f"₺{max_rent_limit:,.2f}"),
        ("Monthly Income", f"₺{mocked_parameters.get('monthly_income', 0):,.2f}"),
        ("Current Balance", f"₺{mocked_parameters.get('current_balance', 0):,.2f}"),
        ("CC Repayment Ratio", f"{mocked_parameters.get('credit_card_repayment_ratio', 0):.0%}"),
        ("Utility Bills Paid", f"{mocked_parameters.get('utility_bills_paid', 0)} / 3"),
        ("Valid Until", expiry_date.strftime("%d %B %Y")),
    ]

    table_x = 30 * mm
    table_w = PAGE_W - 60 * mm
    row_h = 8 * mm

    for i, (label, value) in enumerate(metrics):
        row_y = y - i * row_h
        # Alternating row background
        if i % 2 == 0:
            c.setFillColor(colors.HexColor("#0f1729"))
            c.rect(table_x, row_y - 2 * mm, table_w, row_h, fill=1, stroke=0)

        c.setFont("Helvetica", 9)
        c.setFillColor(TEXT_MUTED)
        c.drawString(table_x + 4 * mm, row_y, label)

        c.setFont("Helvetica-Bold", 9)
        c.setFillColor(TEXT_PRIMARY)
        c.drawRightString(table_x + table_w - 4 * mm, row_y, value)

    y -= len(metrics) * row_h + 8 * mm

    # ── Score breakdown ───────────────────────────────────────────────
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(ACCENT_LIGHT)
    c.drawString(30 * mm, y, "SCORE BREAKDOWN")
    y -= 6 * mm

    breakdown_items = [
        ("Income vs Rent", score_breakdown.get("income_vs_rent", 0)),
        ("Balance", score_breakdown.get("balance", 0)),
        ("Support Income", score_breakdown.get("support_income", 0)),
        ("Utility Bills", score_breakdown.get("utility_bills", 0)),
        ("CC Repayment", score_breakdown.get("cc_repayment", 0)),
        ("Overdraft", score_breakdown.get("overdraft", 0)),
        ("Cash Advance", score_breakdown.get("cash_advance", 0)),
        ("High Risk", score_breakdown.get("high_risk", 0)),
    ]

    col1_x = 30 * mm
    col2_x = PAGE_W / 2 + 5 * mm

    for i, (label, pts) in enumerate(breakdown_items):
        col_x = col1_x if i < 4 else col2_x
        row_y = y - (i % 4) * 6 * mm

        c.setFont("Helvetica", 8)
        c.setFillColor(TEXT_MUTED)
        c.drawString(col_x, row_y, label)

        pts_str = f"+{pts}" if pts >= 0 else str(pts)
        c.setFont("Helvetica-Bold", 8)
        c.setFillColor(GREEN if pts > 0 else RED if pts < 0 else TEXT_MUTED)
        c.drawString(col_x + 38 * mm, row_y, pts_str)

    y -= 4 * 6 * mm + 6 * mm

    # ── QR Code + Anti-fraud notice ───────────────────────────────────
    qr_size = 28 * mm
    qr_x = 30 * mm
    qr_y = y - qr_size

    _draw_qr(c, qr_payload, qr_x, qr_y, qr_size)

    # Anti-fraud text next to QR
    text_x = qr_x + qr_size + 8 * mm
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(ACCENT)
    c.drawString(text_x, y - 4 * mm, "🔒 Sahteciliğe Karşı Korumalı")

    c.setFont("Helvetica", 7)
    c.setFillColor(TEXT_MUTED)
    notices = [
        "Bu sertifika KeyCred tarafından dijital olarak imzalanmıştır.",
        f"Doğrulama kodu: {verification_hash}",
        "QR kodu okutarak sertifikanın geçerliliğini doğrulayabilirsiniz.",
        f"Geçerlilik: {issue_date.strftime('%d.%m.%Y')} – {expiry_date.strftime('%d.%m.%Y')} (90 gün)",
    ]
    for i, line in enumerate(notices):
        c.drawString(text_x, y - 10 * mm - i * 4 * mm, line)

    # ── Footer ────────────────────────────────────────────────────────
    c.setFont("Helvetica", 7)
    c.setFillColor(TEXT_MUTED)
    c.drawCentredString(PAGE_W / 2, 18 * mm,
        f"KeyCred · Because trust is priceless · Issued {issue_date.strftime('%d %B %Y %H:%M UTC')}")
    c.setFont("Helvetica", 6)
    c.setFillColor(BORDER_COLOR)
    c.drawCentredString(PAGE_W / 2, 14 * mm,
        "This document is generated for demonstration purposes only. KeyCred MVP © 2026")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read(), cert_id
