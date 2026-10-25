"""Small HTTPS client for Resend with bounded retries and idempotency."""

from dataclasses import dataclass
import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


RESEND_EMAILS_URL = "https://api.resend.com/emails"


@dataclass(frozen=True)
class ResendResult:
    accepted: bool
    message_id: str | None = None
    retries: int = 0
    error: str | None = None
    http_status: int | None = None
    transient: bool = False


def _bounded_int(value, default, minimum, maximum):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(minimum, min(parsed, maximum))


def _response_body(response):
    try:
        raw = response.read(8192)
    except Exception:
        return {}
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    try:
        value = json.loads(raw or "{}")
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _safe_api_error(status, payload):
    code = payload.get("name") or payload.get("code")
    if isinstance(code, str) and code:
        return f"Resend API rechazó la solicitud (HTTP {status}, código {code[:80]})."
    return f"Resend API rechazó la solicitud (HTTP {status})."


def _retry_after(headers):
    try:
        value = headers.get("Retry-After", "")
        return max(0.0, min(float(value), 2.0))
    except (AttributeError, TypeError, ValueError):
        return None


def send_email(*, api_key, sender, recipient, subject, text_body, html_body=None, reply_to=None,
               attachments=None, idempotency_key, timeout_seconds=10, max_retries=2):
    if not api_key or not sender or not recipient or not subject or not idempotency_key:
        return ResendResult(False, error="Configuración de Resend incompleta.")
    timeout = _bounded_int(timeout_seconds, 10, 1, 60)
    retries_limit = _bounded_int(max_retries, 2, 0, 5)
    payload = {"from": sender, "to": [recipient], "subject": subject, "text": text_body or ""}
    if html_body:
        payload["html"] = html_body
    if reply_to:
        payload["reply_to"] = [reply_to]
    if attachments:
        payload["attachments"] = attachments
    request = Request(
        RESEND_EMAILS_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AFCyber-Solutions/1.0",
            "Idempotency-Key": idempotency_key[:256],
        },
    )
    for attempt in range(retries_limit + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                status = int(getattr(response, "status", None) or response.getcode())
                response_payload = _response_body(response)
            if 200 <= status < 300:
                message_id = response_payload.get("id")
                if isinstance(message_id, str) and message_id:
                    return ResendResult(True, message_id=message_id[:255], retries=attempt, http_status=status)
                return ResendResult(False, retries=attempt, http_status=status, error="Respuesta de Resend sin identificador.")
            transient = status == 429 or status >= 500 or status in {408, 425}
            if transient and attempt < retries_limit:
                time.sleep(min(2.0, 0.25 * (2 ** attempt)))
                continue
            return ResendResult(False, retries=attempt, http_status=status, transient=transient,
                                error=_safe_api_error(status, response_payload))
        except HTTPError as exc:
            status = int(exc.code)
            response_payload = _response_body(exc)
            transient = status == 429 or status >= 500 or status in {408, 425}
            if transient and attempt < retries_limit:
                delay = _retry_after(getattr(exc, "headers", None))
                time.sleep(delay if delay is not None else min(2.0, 0.25 * (2 ** attempt)))
                continue
            return ResendResult(False, retries=attempt, http_status=status, transient=transient,
                                error=_safe_api_error(status, response_payload))
        except (TimeoutError, URLError, OSError):
            if attempt < retries_limit:
                time.sleep(min(2.0, 0.25 * (2 ** attempt)))
                continue
            return ResendResult(False, retries=attempt, transient=True, error="No fue posible comunicarse con Resend.")
        except Exception:
            return ResendResult(False, retries=attempt, error="Error inesperado al procesar el correo.")
    return ResendResult(False, retries=retries_limit, transient=True, error="No fue posible enviar el correo.")
