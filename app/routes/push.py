"""Web Push subscription endpoints for the WasteTrack PWA."""

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import PushSubscription

push_bp = Blueprint("push", __name__, url_prefix="/push")


@push_bp.get("/vapid-key")
def vapid_key():
    return jsonify({"publicKey": current_app.config.get("VAPID_PUBLIC_KEY", "")})


@push_bp.post("/subscribe")
@login_required
def subscribe():
    data = request.get_json(force=True, silent=True) or {}
    endpoint = data.get("endpoint", "")
    keys = data.get("keys", {}) or {}
    if not endpoint or not keys.get("p256dh") or not keys.get("auth"):
        return jsonify({"ok": False, "error": "invalid subscription"}), 400
    existing = PushSubscription.query.filter_by(endpoint=endpoint).first()
    if existing:
        existing.user_id = current_user.id
        existing.p256dh = keys["p256dh"]
        existing.auth = keys["auth"]
    else:
        db.session.add(
            PushSubscription(
                user_id=current_user.id,
                endpoint=endpoint,
                p256dh=keys["p256dh"],
                auth=keys["auth"],
            )
        )
    db.session.commit()
    return jsonify({"ok": True})


@push_bp.post("/unsubscribe")
@login_required
def unsubscribe():
    data = request.get_json(force=True, silent=True) or {}
    endpoint = data.get("endpoint", "")
    if endpoint:
        PushSubscription.query.filter_by(
            endpoint=endpoint, user_id=current_user.id
        ).delete()
        db.session.commit()
    return jsonify({"ok": True})
