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
from PIL import Image

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


def generate_qr_image(
    data: str,
    fill_color: str = "#000000",
    back_color: str = "#ffffff",
    error_correction: str = "M",
    box_size: int = _DEFAULT_BOX,
    border: int = _DEFAULT_BORDER,
) -> Image.Image:
    """
    Generate a QR code and return a PIL Image object (no file I/O).
    Useful for live preview rendering.
    """
    qr = _build_qr(data, error_correction, box_size, border)
    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    return img.get_image()


def generate_qr(
    data: str,
    filename: str = "qr_code.png",
    fill_color: str = "#000000",
    back_color: str = "#ffffff",
    error_correction: str = "M",
    box_size: int = _DEFAULT_BOX,
    border: int = _DEFAULT_BORDER,
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
    )
    img.save(filename)
    return filename