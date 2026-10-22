"""Email notification endpoints for shortlisted candidates."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.database import get_db
from app.notifications.emailer import send_email_notification, send_test_email, test_smtp_connection
from app.schemas import NotificationOut, NotificationRequest, SmtpTestRequest, SmtpTestResult
from app.serializers import notification_to_out

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.post("/send", response_model=NotificationOut)
def send_notification(payload: NotificationRequest, db: Session = Depends(get_db)):
    candidate = db.query(models.Candidate).filter(models.Candidate.id == payload.candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")

    log_entry = send_email_notification(
        db=db,
        candidate=candidate,
        subject=payload.subject,
        body=payload.body,
        job_id=payload.job_id,
    )
    return notification_to_out(log_entry)


@router.get("/", response_model=list[NotificationOut])
def list_notifications(db: Session = Depends(get_db)):
    notifications = (
        db.query(models.NotificationLog)
        .order_by(models.NotificationLog.created_at.desc())
        .all()
    )
    return [notification_to_out(n) for n in notifications]


@router.post("/test-connection", response_model=SmtpTestResult)
def test_connection():
    """Attempt to connect + authenticate to the configured SMTP server
    without sending any mail. Used by the frontend's 'Test SMTP Connection'
    action for immediate pass/fail feedback."""
    return test_smtp_connection()


@router.post("/send-test", response_model=SmtpTestResult)
def send_test(payload: SmtpTestRequest):
    """Actually send a short test email, to `to_email` if given, otherwise to
    the configured SMTP_FROM address. Used by the frontend's 'Send Test
    Email' action."""
    to_email = payload.to_email or settings.smtp_from
    if not to_email:
        raise HTTPException(
            status_code=400,
            detail="No recipient email given and SMTP_FROM is not configured.",
        )
    return send_test_email(to_email)
