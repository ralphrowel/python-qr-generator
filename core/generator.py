"""
core/generator.py
Handles QR code generation with full parameter support.
"""
import qrcode
from qrcode.constants import (
    ERROR_CORRECT_L,
    ERROR_CORRECT_M,
    ERROR_CORRECT_Q,
    ERROR_CORRECT_H,
)
from PIL import Image, ImageDraw

_EC_MAP = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}

_DEFAULT_BOX  = 10
_DEFAULT_BORDER = 4


def _build_qr(
    data: str,
    error_correction: str = "M",
    box_size: int = _DEFAULT_BOX,
    border: int = _DEFAULT_BORDER,
) -> qrcode.QRCode:
    """Build a configured QRCode object (no image yet)."""
    ec = _EC_MAP.get(str(error_correction).upper(), ERROR_CORRECT_M)
    qr = qrcode.QRCode(
        version=None,          # auto-detect
        error_correction=ec,
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)
    return qr


def _embed_logo(
    qr_img: Image.Image,
    logo: Image.Image | str,
    back_color: str = "#ffffff",
) -> Image.Image:
    """Embed a centered logo with a protective margin on top of a QR code."""
    try:
        if isinstance(logo, str):
            logo_img = Image.open(logo)
        else:
            logo_img = logo.copy()
    except Exception:
        return qr_img

    qr_w, qr_h = qr_img.size
    # Keep logo within ~22% of QR dimensions so data remains recoverable
    max_logo_w = max(16, int(qr_w * 0.22))
    max_logo_h = max(16, int(qr_h * 0.22))

    logo_img = logo_img.convert("RGBA")
    logo_img.thumbnail((max_logo_w, max_logo_h), Image.Resampling.LANCZOS)
    lw, lh = logo_img.size

    base = qr_img.convert("RGBA")

    # Protective badge background padding around the logo
    pad = max(4, int(qr_w * 0.02))
    badge_w = lw + pad * 2
    badge_h = lh + pad * 2
    badge_x = (qr_w - badge_w) // 2
    badge_y = (qr_h - badge_h) // 2

    # Draw protective backdrop badge matching the QR back_color
    badge = Image.new("RGBA", (badge_w, badge_h), back_color)
    base.paste(badge, (badge_x, badge_y))

    # Center and paste the logo with its alpha channel
    logo_x = (qr_w - lw) // 2
    logo_y = (qr_h - lh) // 2
    base.paste(logo_img, (logo_x, logo_y), mask=logo_img)

    return base.convert("RGB")


def generate_qr_image(
    data: str,
    fill_color: str = "#000000",
    back_color: str = "#ffffff",
    error_correction: str = "M",
    box_size: int = _DEFAULT_BOX,
    border: int = _DEFAULT_BORDER,
    logo: Image.Image | str | None = None,
) -> Image.Image:
    """
    Generate a QR code and return a PIL Image object (no file I/O).
    If logo is specified, error correction is boosted to H/Q to ensure scannability.
    """
    if logo is not None and str(error_correction).upper() in ("L", "M"):
        error_correction = "H"

    qr = _build_qr(data, error_correction, box_size, border)
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    result = img.get_image()
    if logo is not None:
        result = _embed_logo(result, logo, back_color=back_color)
    return result


def generate_qr(
    data: str,
    filename: str = "qr_code.png",
    fill_color: str = "#000000",
    back_color: str = "#ffffff",
    error_correction: str = "M",
    box_size: int = _DEFAULT_BOX,
    border: int = _DEFAULT_BORDER,
    logo: Image.Image | str | None = None,
) -> str:
    """
    Generate a QR code and save it to *filename*.
    Returns the filename that was saved.
    """
    img = generate_qr_image(
        data,
        fill_color=fill_color,
        back_color=back_color,
        error_correction=error_correction,
        box_size=box_size,
        border=border,
        logo=logo,
    )
    img.save(filename)
    return filename