"""
utils/helpers.py
String formatters for each QR content type + clipboard utility.
"""
from __future__ import annotations

import io
from PIL import Image


# ── QR data string formatters ────────────────────────────────────────────────

def format_url(url: str) -> str:
    """Return url as-is (basic sanitisation)."""
    url = url.strip()
    if url and not url.startswith(("http://", "https://", "ftp://")):
        url = "https://" + url
    return url


def format_wifi(ssid: str, password: str, security: str, hidden: bool) -> str:
    """
    Format a WiFi QR string.
    security: 'WPA', 'WEP', or 'nopass'
    """
    ssid     = _escape_wifi(ssid)
    password = _escape_wifi(password)
    security = security.upper() if security.upper() in ("WPA", "WEP") else "nopass"
    hidden_str = "true" if hidden else "false"
    return f"WIFI:T:{security};S:{ssid};P:{password};H:{hidden_str};;"


def _escape_wifi(value: str) -> str:
    """Escape special chars in WiFi QR strings."""
    for ch in ('\\', ';', ',', '"', ':'):
        value = value.replace(ch, '\\' + ch)
    return value


def format_vcard(
    name: str,
    phone: str = "",
    email: str = "",
    website: str = "",
    org: str = "",
    title: str = "",
) -> str:
    """Format a vCard 3.0 QR string."""
    lines = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"FN:{name}",
    ]
    if org:
        lines.append(f"ORG:{org}")
    if title:
        lines.append(f"TITLE:{title}")
    if phone:
        lines.append(f"TEL:{phone}")
    if email:
        lines.append(f"EMAIL:{email}")
    if website:
        lines.append(f"URL:{website}")
    lines.append("END:VCARD")
    return "\n".join(lines)


def format_email(to: str, subject: str, body: str) -> str:
    """Format a mailto: QR string."""
    from urllib.parse import urlencode, quote
    params: dict[str, str] = {}
    if subject:
        params["subject"] = subject
    if body:
        params["body"] = body
    query = "&".join(f"{k}={quote(v)}" for k, v in params.items())
    return f"mailto:{to}" + (f"?{query}" if query else "")


def format_sms(phone: str, message: str) -> str:
    """Format an SMS QR string."""
    if message:
        return f"SMSTO:{phone}:{message}"
    return f"SMSTO:{phone}"


# ── Clipboard ────────────────────────────────────────────────────────────────

def copy_image_to_clipboard(img: Image.Image) -> bool:
    """
    Copy a PIL Image to the Windows clipboard as a DIB.
    Returns True on success, False if win32clipboard is unavailable.
    """
    try:
        import win32clipboard  # type: ignore
        import win32con         # type: ignore

        # Convert to BMP bytes in memory
        output = io.BytesIO()
        img.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]  # strip BMP file header (14 bytes)

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_DIB, data)
        win32clipboard.CloseClipboard()
        return True
    except ImportError:
        return False
    except Exception:
        return False
