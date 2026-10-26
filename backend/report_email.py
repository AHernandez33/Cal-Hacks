"""Opt-in email of numeric crop observations; no images or locations are mailed."""
import os
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from backend import databases
from backend.identity import workspace_id

router = APIRouter(prefix="/reports", tags=["consented report delivery"])

class ReportRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=254)
    yellow_fraction: float = Field(ge=0, le=1)
    brown_fraction: float = Field(ge=0, le=1)
    anomaly_score: float = Field(ge=0, le=1)
    leaf_coverage_fraction: float = Field(ge=0, le=1)
    consent_to_email: StrictBool

@router.post("/email")
def email_report(req: ReportRequest):
    if not req.consent_to_email:
        raise HTTPException(400, "Consent to email this report is required.")
    # Only authenticated workspaces may send email; public anonymous delivery
    # would allow this endpoint to be used for spam.
    owner = workspace_id.get()
    if owner == "local":
        raise HTTPException(401, "Sign in to a private workspace to email your report.")
    from email.utils import parseaddr
    parsed = parseaddr(req.email)[1]
    if parsed != req.email or "@" not in parsed or any(c in parsed for c in "\r\n"):
        raise HTTPException(422, "Enter a valid email address.")
    host = os.getenv("VIGILO_SMTP_HOST", "").strip()
    sender = os.getenv("VIGILO_SMTP_FROM", "").strip()
    username = os.getenv("VIGILO_SMTP_USER", "").strip()
    password = os.getenv("VIGILO_SMTP_PASSWORD", "")
    if not all((host, sender, username, password)):
        raise HTTPException(503, "Report email delivery is not configured yet.")
    today = datetime.now(timezone.utc).date().isoformat()
    databases.init_db()
    with databases.connection() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS report_email_limits (
            owner_id TEXT NOT NULL,
            day TEXT NOT NULL,
            last_sent_at TEXT,
            PRIMARY KEY(owner_id, day)
        )""")
        existing = db.execute(
            "SELECT 1 FROM report_email_limits WHERE owner_id=? AND day=?",
            (owner, today),
        ).fetchone()
        if existing:
            raise HTTPException(429, "One emailed report per workspace per day in this prototype.")
        # Reserve before network calls to prevent repeated sends.
        db.execute(
            "INSERT INTO report_email_limits(owner_id, day) VALUES (?,?)",
            (owner, today),
        )
    message = EmailMessage()
    message["From"] = sender
    message["To"] = parsed
    message["Subject"] = "Your VigiloForge crop observation"
    message.set_content(
        "VigiloForge crop observation (heuristic, not a disease diagnosis)\n\n"
        f"Yellow area: {req.yellow_fraction * 100:.1f}%\n"
        f"Brown area: {req.brown_fraction * 100:.1f}%\n"
        f"Visible discoloration index: {req.anomaly_score * 100:.1f}/100\n"
        f"Leaf coverage: {req.leaf_coverage_fraction * 100:.1f}%\n\n"
        "These values depend on lighting and camera quality. No photo is attached.\n"
        "You asked for this single report; no marketing emails are enabled.\n"
    )
    try:
        with smtplib.SMTP_SSL(host, int(os.getenv("VIGILO_SMTP_PORT", "465")),
                              timeout=12, context=ssl.create_default_context()) as smtp:
            smtp.login(username, password)
            smtp.send_message(message)
    except (OSError, smtplib.SMTPException, ValueError) as exc:
        # Release the reserved slot when the provider did not confirm acceptance.
        # A production email queue should use idempotency and delivery tracking.
        with databases.connection() as db:
            db.execute("DELETE FROM report_email_limits WHERE owner_id=? AND day=? AND last_sent_at IS NULL", (owner, today))
        raise HTTPException(502, "The email provider did not accept the report. Check SMTP settings and retry.") from exc
    with databases.connection() as db:
        db.execute("UPDATE report_email_limits SET last_sent_at=? WHERE owner_id=? AND day=?",
                   (datetime.now(timezone.utc).isoformat(), owner, today))
    return {"sent": True, "message": "Your crop report was accepted by the email provider. Check your inbox and spam folder."}
