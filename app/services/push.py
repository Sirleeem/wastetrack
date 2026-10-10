"""Web Push notifications for the WasteTrack PWA (pywebpush + VAPID)."""

from __future__ import annotations

import json
import logging
import threading

from flask import current_app

log = logging.getLogger(__name__)


def _vapid_config():
    return {
        "public": current_app.config.get("VAPID_PUBLIC_KEY", ""),
        "private": current_app.config.get("VAPID_PRIVATE_KEY", ""),
        "sub": current_app.config.get("VAPID_CLAIMS_SUB", "mailto:admin@wastetrack.app"),
    }


def push_enabled() -> bool:
    cfg = _vapid_config()
    return bool(cfg["public"] and cfg["private"])


def _send_one(subscription, payload: dict) -> bool:
    """Send to a single subscription. Returns False if the subscription is dead."""
    from pywebpush import WebPushException, webpush

    cfg = _vapid_config()
    try:
        webpush(
            subscription_info={
                "endpoint": subscription.endpoint,
                "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
            },
            data=json.dumps(payload),
            vapid_private_key=cfg["private"],
            vapid_claims={"sub": cfg["sub"]},
        )
        return True
    except WebPushException as exc:
        status = getattr(exc.response, "status_code", None)
        log.warning("push failed (status=%s): %s", status, exc)
        return status not in (404, 410)
    except Exception as exc:  # noqa: BLE001 - never break the request on notify
        log.warning("push error: %s", exc)
        return True


def notify_user(user_id: int, title: str, body: str, url: str = "/") -> None:
    """Queue push notifications to all of a user's devices (background thread)."""
    if not push_enabled():
        return
    app = current_app._get_current_object()

    def _work():
        with app.app_context():
            from app.extensions import db
            from app.models import PushSubscription

            subs = PushSubscription.query.filter_by(user_id=user_id).all()
            payload = {"title": title, "body": body, "url": url}
            dead = []
            for sub in subs:
                if not _send_one(sub, payload):
                    dead.append(sub)
            for sub in dead:
                db.session.delete(sub)
            if dead:
                db.session.commit()

    threading.Thread(target=_work, daemon=True).start()


def notify_officer_assignment(report, officer) -> None:
    """Push notification when an admin assigns a report to an officer."""
    title = "New WasteTrack task"
    body = (
        f"Task {report.tracking_code} ({report.urgency} urgency) at "
        f"{report.address or 'your area'}. Open your dashboard to start."
    )
    notify_user(officer.id, title, body, url="/officer/tasks")
