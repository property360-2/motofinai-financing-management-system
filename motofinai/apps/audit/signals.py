from __future__ import annotations

from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

from .models import AuditLogEntry


def _extract_ip(request) -> str | None:
    if request is None:
        return None
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _session_key(request) -> str | None:
    if request is None or not hasattr(request, "session"):
        return None
    return request.session.session_key


@receiver(user_logged_in)
def on_user_logged_in(sender, request, user, **kwargs):
    AuditLogEntry.record(
        actor=user,
        action="auth.login",
        ip_address=_extract_ip(request),
        user_agent=request.META.get("HTTP_USER_AGENT", "") if request else "",
        metadata={
            "path": request.path if request else "",
            "session_key": _session_key(request),
        },
    )


