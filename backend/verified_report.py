"""Opt-in verified report delivery. Only numerical results, never photos."""
import hashlib
import hmac
import json
import os
import secrets
import smtplib
import ssl
import time
from email.message import EmailMessage
from email.utils import parseaddr

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from backend import databases

router = APIRouter(prefix="/reports/verify", tags=["verified report email"])

class StartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=5, max_length=254)
    consent_to_email: StrictBool
    yellow_fraction: float = Field(ge=0, le=1)
    brown_fraction: float = Field(ge=0, le=1)
    anomaly_score: float = Field(ge=0, le=1)
    leaf_coverage_fraction: float = Field(ge=0, le=1)

class ConfirmRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: str = Field(min_length=20, max_length=100)
    code: str = Field(pattern=r"^\d{6}$")

def config():
    from pathlib import Path
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    host = os.getenv("VIGILO_SMTP_HOST", "").strip()
    sender = os.getenv("VIGILO_SMTP_FROM", "").strip()
    user = os.getenv("VIGILO_SMTP_USER", "").strip()
    password = os.getenv("VIGILO_SMTP_PASSWORD", "")
    pepper = os.getenv("VIGILO_REPORT_SECRET", "")
    if not all((host, sender, user, password, pepper)) or len(pepper) < 32:
        raise HTTPException(503, "Verified email is not configured. Set SMTP and VIGILO_REPORT_SECRET.")
    return host, sender, user, password, pepper

def send_mail(destination, subject, content, cfg):
    host, sender, user, password, _ = cfg
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = destination
    msg["Subject"] = subject
    msg.set_content(content)
    try:
        with smtplib.SMTP_SSL(host, int(os.getenv("VIGILO_SMTP_PORT", "465")),
                              timeout=12, context=ssl.create_default_context()) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
    except (OSError, ValueError, smtplib.SMTPException) as exc:
        raise HTTPException(502, "Email provider did not accept the message.") from exc

def init():
    with databases.connection() as db:
        db.execute("""CREATE TABLE IF NOT EXISTS verified_report_requests (
          id TEXT PRIMARY KEY, email TEXT NOT NULL, code_digest TEXT NOT NULL,
          payload TEXT NOT NULL, ip_digest TEXT NOT NULL,
          created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
          attempts INTEGER NOT NULL DEFAULT 0, fulfilled INTEGER NOT NULL DEFAULT 0
        )""")

def digest(value, secret):
    return hmac.new(secret.encode(), value.encode(), hashlib.sha256).hexdigest()

@router.post("/start")
def start(req: StartRequest, request: Request):
    if not req.consent_to_email:
        raise HTTPException(400, "Email consent is required.")
    email = req.email.strip()
    if email != parseaddr(email)[1] or any(c in email for c in "\r\n") or "@" not in email:
        raise HTTPException(422, "Enter a valid email address.")
    cfg = config()
    init()
    now = int(time.time())
    ip = request.client.host if request.client else "unknown"
    ip_digest = digest(ip, cfg[4])
    with databases.connection() as db:
        recent = db.execute("""SELECT COUNT(*) FROM verified_report_requests
            WHERE ip_digest=? AND created_at>?""",
            (ip_digest, now - 86400)).fetchone()[0]
        email_recent = db.execute("""SELECT COUNT(*) FROM verified_report_requests
            WHERE email=? AND created_at>?""", (email, now - 86400)).fetchone()[0]
        if recent >= 5 or email_recent >= 3:
            raise HTTPException(429, "Too many verification requests today. Try again tomorrow.")
        request_id = secrets.token_urlsafe(24)
        code = f"{secrets.randbelow(1000000):06d}"
        payload = json.dumps({
            "yellow_fraction": req.yellow_fraction, "brown_fraction": req.brown_fraction,
            "anomaly_score": req.anomaly_score, "leaf_coverage_fraction": req.leaf_coverage_fraction
        })
        db.execute("""INSERT INTO verified_report_requests
            (id,email,code_digest,payload,ip_digest,created_at,expires_at)
            VALUES (?,?,?,?,?,?,?)""",
            (request_id, email, digest(request_id + ":" + code, cfg[4]),
             payload, ip_digest, now, now+600))
    send_mail(email, "Verify your VigiloForge crop report",
              f"Your VigiloForge verification code is {code}.\nIt expires in 10 minutes.\n"
              "If you did not request this, ignore the message.", cfg)
    return {"request_id": request_id, "message": "Verification code sent. Check your inbox."}

@router.post("/confirm")
def confirm(req: ConfirmRequest):
    cfg = config()
    init()
    with databases.connection() as db:
        row = db.execute("SELECT * FROM verified_report_requests WHERE id=?", (req.request_id,)).fetchone()
        if not row or row["fulfilled"] or row["expires_at"] < int(time.time()) or row["attempts"] >= 5:
            raise HTTPException(400, "Code expired, already used, or too many attempts.")
        db.execute("UPDATE verified_report_requests SET attempts=attempts+1 WHERE id=?", (req.request_id,))
        if not hmac.compare_digest(row["code_digest"], digest(req.request_id+":"+req.code,cfg[4])):
            raise HTTPException(400, "Incorrect code.")
        # Consume before calling the provider to avoid multiple reports on concurrent attempts.
        db.execute("UPDATE verified_report_requests SET fulfilled=1 WHERE id=?", (req.request_id,))
    values = json.loads(row["payload"])
    body = ("VigiloForge numerical crop observations (heuristic, not a disease diagnosis)\n\n"
        f"Yellow area: {values['yellow_fraction']*100:.1f}%\n"
        f"Brown area: {values['brown_fraction']*100:.1f}%\n"
        f"Visible discoloration: {values['anomaly_score']*100:.1f}/100\n"
        f"Leaf coverage: {values['leaf_coverage_fraction']*100:.1f}%\n\n"
        "No photograph attached. Results vary with lighting and framing.\n"
        "This verification does not create an account or unlock additional scans.")
    send_mail(row["email"], "Your VigiloForge crop report", body, cfg)
    return {"sent": True, "message": "Report accepted by your email provider."}
