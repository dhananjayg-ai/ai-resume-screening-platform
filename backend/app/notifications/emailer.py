"""Send email notifications to shortlisted candidates via SMTP.

If SMTP env vars are not configured (or sending fails, e.g. no network access
in a demo/sandboxed environment), this gracefully no-ops and logs the
notification to the NotificationLog table instead of raising -- so the rest
of the system (and the HTTP request handling it) is never blocked by email
delivery issues.

Two SMTP connection modes are supported, selected by `settings.smtp_use_ssl`:
  - STARTTLS (default, typically port 587): connect in plaintext, then
    upgrade the connection to TLS with `starttls()` before authenticating.
  - Implicit SSL/TLS (typically port 465): the connection is encrypted from
    the first byte via `smtplib.SMTP_SSL`.
"""
import logging
import smtplib
from email.mime.text import MIMEText

from sqlalchemy.orm import Session

from app import models
from app.config import settings

logger = logging.getLogger(__name__)

TEST_EMAIL_SUBJECT = "AI Resume Screening Platform -- SMTP test email"
TEST_EMAIL_BODY = (
    "This is a test email from the AI Resume Screening and Recruitment Platform.\n\n"
    "If you received this, outbound email notifications are configured correctly."
)


def _smtp_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_user and settings.smtp_password and settings.smtp_from)


def _open_connection() -> smtplib.SMTP:
    """Open and authenticate an SMTP connection using the configured mode
    (implicit SSL or STARTTLS). Caller is responsible for closing it (both
    SMTP and SMTP_SSL support use as a context manager)."""
    if settings.smtp_use_ssl:
        server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10)
    else:
        server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)
        server.starttls()
    server.login(settings.smtp_user, settings.smtp_password)
    return server


def _send_mime(to_email: str, subject: str, body: str) -> None:
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to_email

    with _open_connection() as server:
        server.sendmail(settings.smtp_from, [to_email], msg.as_string())


def send_email_notification(
    db: Session,
    candidate: models.Candidate,
    subject: str,
    body: str,
    job_id: int | None = None,
) -> models.NotificationLog:
    """Attempt to send an email; always persist a NotificationLog row recording
    the outcome ('sent', 'failed', or 'skipped_no_smtp_config')."""
    status = "skipped_no_smtp_config"

    if not candidate.email:
        status = "failed_no_candidate_email"
        logger.warning("Candidate %s has no email on file; cannot send notification.", candidate.id)
    elif _smtp_configured():
        try:
            _send_mime(candidate.email, subject, body)
            status = "sent"
        except Exception as exc:
            logger.warning("Failed to send email to %s: %s", candidate.email, exc)
            status = "failed"
    else:
        logger.info(
            "SMTP not configured; logging notification instead of sending for candidate %s.",
            candidate.id,
        )

    log_entry = models.NotificationLog(
        candidate_id=candidate.id,
        job_id=job_id,
        channel="email",
        subject=subject,
        body=body,
        status=status,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def test_smtp_connection() -> dict:
    """Connect + authenticate to the configured SMTP server without sending
    any mail. Returns {"status": ..., "detail": ...} where status is one of
    'ok', 'not_configured', 'auth_error', 'connection_error', 'smtp_error'."""
    if not _smtp_configured():
        return {
            "status": "not_configured",
            "detail": (
                "SMTP is not configured (SMTP_HOST / SMTP_USER / SMTP_PASSWORD / SMTP_FROM "
                "are not all set). Notifications will be logged instead of sent."
            ),
        }
    try:
        with _open_connection():
            pass
        mode = "implicit SSL" if settings.smtp_use_ssl else "STARTTLS"
        return {
            "status": "ok",
            "detail": f"Connected and authenticated to {settings.smtp_host}:{settings.smtp_port} ({mode}).",
        }
    except smtplib.SMTPAuthenticationError as exc:
        logger.warning("SMTP auth error during test-connection: %s", exc)
        return {"status": "auth_error", "detail": f"Authentication failed: {exc}"}
    except (smtplib.SMTPException, OSError, TimeoutError) as exc:
        logger.warning("SMTP connection error during test-connection: %s", exc)
        return {"status": "connection_error", "detail": f"Could not connect: {exc}"}
    except Exception as exc:  # pragma: no cover - defensive catch-all
        logger.warning("Unexpected error during SMTP test-connection: %s", exc)
        return {"status": "smtp_error", "detail": str(exc)}


def send_test_email(to_email: str) -> dict:
    """Actually send a short test email to `to_email`. Returns
    {"status": ..., "detail": ...} with the same status vocabulary as
    `test_smtp_connection`, plus 'sent' on success."""
    if not _smtp_configured():
        return {
            "status": "not_configured",
            "detail": (
                "SMTP is not configured (SMTP_HOST / SMTP_USER / SMTP_PASSWORD / SMTP_FROM "
                "are not all set)."
            ),
        }
    try:
        _send_mime(to_email, TEST_EMAIL_SUBJECT, TEST_EMAIL_BODY)
        return {"status": "sent", "detail": f"Test email sent to {to_email}."}
    except smtplib.SMTPAuthenticationError as exc:
        logger.warning("SMTP auth error sending test email: %s", exc)
        return {"status": "auth_error", "detail": f"Authentication failed: {exc}"}
    except (smtplib.SMTPException, OSError, TimeoutError) as exc:
        logger.warning("SMTP connection error sending test email: %s", exc)
        return {"status": "connection_error", "detail": f"Could not send: {exc}"}
    except Exception as exc:  # pragma: no cover - defensive catch-all
        logger.warning("Unexpected error sending test email: %s", exc)
        return {"status": "smtp_error", "detail": str(exc)}
