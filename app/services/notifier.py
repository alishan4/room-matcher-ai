"""Notification helpers for email/SMS/webhook fan-out.

The notifier is intentionally lightweight – each channel is optional and only
activated when the required environment variables are supplied.  This keeps
local development simple (where notifications are logged) while enabling real
integrations in production environments (SMTP/Twilio/webhook).
"""

from __future__ import annotations

import logging
import os
import smtplib
import ssl
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from typing import Any, Dict, List, Optional

import requests


LOGGER = logging.getLogger(__name__)


def _split_csv(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _render_match_summary(matches: List[Dict[str, Any]]) -> str:
    lines = []
    for m in matches:
        name = m.get("other_name") or m.get("other_profile_id") or "Unknown"
        score = m.get("score")
        status = m.get("notification_status") or ("new" if m.get("is_new") else "notified")
        lines.append(f"- {name} (score: {score}, status: {status})")
    return "\n".join(lines)


@dataclass
class NotificationPayload:
    scope: str
    user_profile: Dict[str, Any]
    matches: List[Dict[str, Any]]
    rooms: List[Dict[str, Any]]
    trace: Dict[str, Any]
    summary: Optional[str] = None
    subject: Optional[str] = None
    partner: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class Notifier:
    """Aggregates all outbound notification channels."""

    def __init__(self) -> None:
        self.smtp_host = os.getenv("NOTIFIER_SMTP_HOST")
        self.smtp_port = int(os.getenv("NOTIFIER_SMTP_PORT", "587"))
        self.smtp_user = os.getenv("NOTIFIER_SMTP_USERNAME")
        self.smtp_password = os.getenv("NOTIFIER_SMTP_PASSWORD")
        self.email_sender = os.getenv("NOTIFIER_EMAIL_SENDER")

        self.twilio_account_sid = os.getenv("NOTIFIER_TWILIO_SID")
        self.twilio_auth_token = os.getenv("NOTIFIER_TWILIO_TOKEN")
        self.twilio_from_number = os.getenv("NOTIFIER_TWILIO_FROM")

        self.default_webhooks = _split_csv(os.getenv("NOTIFIER_WEBHOOK_URLS"))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def dispatch(
        self,
        payload: NotificationPayload,
        channels: List[str],
        partner_webhooks: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Send notifications on the desired channels.

        Returns a map detailing the status of each attempted channel.  Any
        runtime errors are caught and returned to the caller – the watcher can
        then record telemetry without the background worker crashing.
        """

        statuses: Dict[str, Any] = {}
        rendered_summary = payload.summary or _render_match_summary(payload.matches)
        subject = payload.subject or f"Room matches for {payload.user_profile.get('name', 'student')}"

        if "email" in channels:
            statuses["email"] = self._send_email(payload, subject, rendered_summary)

        if "sms" in channels:
            statuses["sms"] = self._send_sms(payload, rendered_summary)

        if "webhook" in channels:
            all_hooks = list(self.default_webhooks)
            if partner_webhooks:
                all_hooks.extend(partner_webhooks)
            statuses["webhook"] = self._send_webhooks(payload, rendered_summary, all_hooks)

        return statuses

    # ------------------------------------------------------------------
    # Email
    # ------------------------------------------------------------------
    def _send_email(self, payload: NotificationPayload, subject: str, body: str) -> Dict[str, Any]:
        recipient = payload.user_profile.get("email")
        if not (self.smtp_host and self.email_sender and recipient):
            LOGGER.info("Skipping email notification (missing configuration or recipient).")
            return {"status": "skipped", "reason": "missing_config_or_recipient"}

        message = MIMEText(
            f"Hello {payload.user_profile.get('name', 'there')},\n\n"
            f"Here are your latest roommate matches:\n{body}\n\n"
            f"Trace id: {payload.trace.get('mode')}\n"
        )
        message["Subject"] = subject
        message["From"] = self.email_sender
        message["To"] = recipient

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=15) as server:
                server.starttls(context=context)
                if self.smtp_user and self.smtp_password:
                    server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.email_sender, [recipient], message.as_string())
            LOGGER.info("Sent email notification to %s", recipient)
            return {"status": "sent", "recipient": recipient}
        except Exception as exc:  # pragma: no cover - network errors
            LOGGER.exception("Failed to send email notification")
            return {"status": "error", "error": str(exc)}

    # ------------------------------------------------------------------
    # SMS
    # ------------------------------------------------------------------
    def _send_sms(self, payload: NotificationPayload, body: str) -> Dict[str, Any]:
        recipient = payload.user_profile.get("phone") or payload.user_profile.get("phone_number")
        if not (self.twilio_account_sid and self.twilio_auth_token and self.twilio_from_number and recipient):
            LOGGER.info("Skipping SMS notification (missing configuration or recipient).")
            return {"status": "skipped", "reason": "missing_config_or_recipient"}

        message = f"Matches ready: {body[:140]}"
        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.twilio_account_sid}/Messages.json"
        try:
            response = requests.post(
                url,
                auth=(self.twilio_account_sid, self.twilio_auth_token),
                data={
                    "From": self.twilio_from_number,
                    "To": recipient,
                    "Body": message,
                },
                timeout=10,
            )
            response.raise_for_status()
            LOGGER.info("Sent SMS notification to %s", recipient)
            return {"status": "sent", "recipient": recipient}
        except Exception as exc:  # pragma: no cover - network errors
            LOGGER.exception("Failed to send SMS notification")
            return {"status": "error", "error": str(exc)}

    # ------------------------------------------------------------------
    # Webhooks
    # ------------------------------------------------------------------
    def _send_webhooks(
        self,
        payload: NotificationPayload,
        summary: str,
        hooks: List[str],
    ) -> Dict[str, Any]:
        if not hooks:
            LOGGER.info("Skipping webhook notification (no endpoints configured).")
            return {"status": "skipped", "reason": "missing_endpoints"}

        results = []
        for url in hooks:
            if not url:
                continue
            try:
                response = requests.post(
                    url,
                    json={
                        "scope": payload.scope,
                        "user": payload.user_profile,
                        "matches": payload.matches,
                        "rooms": payload.rooms,
                        "summary": summary,
                        "trace": payload.trace,
                        "metadata": payload.metadata,
                    },
                    timeout=10,
                )
                response.raise_for_status()
                results.append({"status": "sent", "endpoint": url, "code": response.status_code})
            except Exception as exc:  # pragma: no cover - network errors
                LOGGER.exception("Failed to send webhook notification to %s", url)
                results.append({"status": "error", "endpoint": url, "error": str(exc)})

        return {"status": "completed", "results": results}


__all__ = ["NotificationPayload", "Notifier"]

