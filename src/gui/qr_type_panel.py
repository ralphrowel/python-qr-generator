"""
src/gui/qr_type_panel.py
Segmented tab strip + dynamic input fields for each QR content type.
"""
from __future__ import annotations
import tkinter as tk
from tkinter import ttk
from typing import Callable

from utils.helpers import (
    format_url, format_wifi, format_vcard, format_email, format_sms
)

# ── palette (duplicated here to avoid circular imports) ──────────────────────
LEGO_RED    = "#d01012"
LEGO_BLUE   = "#0088dd"
LEGO_MID    = "#3377aa"
LEGO_YELLOW = "#ffff00"
LEGO_LIGHT  = "#ebebeb"
LEGO_DARK   = "#1a1a1a"
LEGO_WHITE  = "#ffffff"
LEGO_GREEN  = "#00a650"

TABS = [
    ("🔗", "URL"),
    ("📶", "WiFi"),
    ("📇", "Contact"),
    ("📧", "Email"),
    ("💬", "SMS"),
    ("📝", "Text"),
]


def _entry(parent, var: tk.StringVar, placeholder: str = "") -> tk.Entry:
    e = tk.Entry(
        parent, textvariable=var,
        font=("Consolas", 9), relief="flat",
        bg=LEGO_LIGHT, fg=LEGO_DARK,
        insertbackground=LEGO_RED,
        highlightthickness=2,
        highlightbackground=LEGO_MID,
        highlightcolor=LEGO_RED,
    )
    if placeholder and not var.get():
        var.set(placeholder)
    return e


def _label(parent, text: str) -> tk.Label:
    return tk.Label(
        parent, text=text,
        bg=parent["bg"], fg=LEGO_MID,
        font=("Arial Black", 7),
        anchor="w",
    )


class QRTypePanel(tk.Frame):
    """
    A segmented-tab control that shows different input fields
    depending on the selected QR content type.
    Calls `on_change(data_string)` whenever any field updates.
    """

    def __init__(self, parent, on_change: Callable[[str], None], **kwargs):
        bg = kwargs.pop("bg", LEGO_WHITE)
        super().__init__(parent, bg=bg, **kwargs)
        self._bg = bg
        self._on_change = on_change
        self._active_tab = 0
        self._field_frame: tk.Frame | None = None

        self._build_tab_strip()
        self._build_fields(0)

    # ── tab strip ────────────────────────────────────────────────────────────

    def _build_tab_strip(self):
        strip = tk.Frame(self, bg=self._bg)
        strip.pack(fill="x", pady=(0, 6))
        self._tab_btns: list[tk.Button] = []
        for i, (icon, name) in enumerate(TABS):
            btn = tk.Button(
                strip,
                text=f"{icon}\n{name}",
                width=5,
                relief="flat",
                bd=0,
                font=("Arial", 7, "bold"),
                bg=LEGO_LIGHT, fg=LEGO_MID,
                activebackground=LEGO_RED,
                activeforeground=LEGO_WHITE,
                cursor="hand2",
                command=lambda idx=i: self._select_tab(idx),
            )
            btn.pack(side="left", padx=2)
            self._tab_btns.append(btn)
        self._highlight_tab(0)

    def _select_tab(self, idx: int):
        if idx == self._active_tab:
            return
        self._active_tab = idx
        self._highlight_tab(idx)
        if self._field_frame:
            self._field_frame.destroy()
        self._build_fields(idx)
        self._notify()

    def _highlight_tab(self, idx: int):
        for i, btn in enumerate(self._tab_btns):
            if i == idx:
                btn.configure(bg=LEGO_RED, fg=LEGO_WHITE, relief="sunken")
            else:
                btn.configure(bg=LEGO_LIGHT, fg=LEGO_MID, relief="flat")

    # ── field builders ───────────────────────────────────────────────────────

    def _build_fields(self, idx: int):
        self._field_frame = tk.Frame(self, bg=self._bg)
        self._field_frame.pack(fill="x")
        builders = [
            self._fields_url,
            self._fields_wifi,
            self._fields_vcard,
            self._fields_email,
            self._fields_sms,
            self._fields_text,
        ]
        builders[idx](self._field_frame)

    def _trace(self, *_):
        self._notify()

    def _notify(self):
        try:
            data = self.get_data()
            self._on_change(data)
        except Exception:
            pass

    # ── URL ──────────────────────────────────────────────────────────────────
    def _fields_url(self, f):
        self._url_var = tk.StringVar(value="https://example.com")
        _label(f, "URL").pack(anchor="w")
        e = _entry(f, self._url_var)
        e.pack(fill="x")
        self._url_var.trace_add("write", self._trace)

    # ── WiFi ─────────────────────────────────────────────────────────────────
    def _fields_wifi(self, f):
        self._wifi_ssid     = tk.StringVar(value="")
        self._wifi_pass     = tk.StringVar(value="")
        self._wifi_security = tk.StringVar(value="WPA")
        self._wifi_hidden   = tk.BooleanVar(value=False)

        _label(f, "SSID (Network Name)").pack(anchor="w")
        _entry(f, self._wifi_ssid, "MyNetwork").pack(fill="x")

        _label(f, "Password").pack(anchor="w", pady=(4, 0))
        _entry(f, self._wifi_pass).pack(fill="x")

        sec_row = tk.Frame(f, bg=self._bg)
        sec_row.pack(fill="x", pady=(4, 0))
        _label(sec_row, "Security").pack(side="left")
        for sec in ("WPA", "WEP", "None"):
            val = "nopass" if sec == "None" else sec
            tk.Radiobutton(
                sec_row, text=sec,
                variable=self._wifi_security, value=val,
                bg=self._bg, fg=LEGO_DARK,
                selectcolor=LEGO_YELLOW,
                font=("Arial", 8),
            ).pack(side="left", padx=4)

        tk.Checkbutton(
            f, text="Hidden network",
            variable=self._wifi_hidden,
            bg=self._bg, fg=LEGO_DARK,
            selectcolor=LEGO_YELLOW,
            font=("Arial", 8),
        ).pack(anchor="w", pady=(4, 0))

        for v in (self._wifi_ssid, self._wifi_pass,
                  self._wifi_security, self._wifi_hidden):
            v.trace_add("write", self._trace)

    # ── Contact (vCard) ───────────────────────────────────────────────────────
    def _fields_vcard(self, f):
        self._vc_name    = tk.StringVar(value="")
        self._vc_phone   = tk.StringVar(value="")
        self._vc_email   = tk.StringVar(value="")
        self._vc_website = tk.StringVar(value="")

        for lbl, var, ph in [
            ("Full Name",  self._vc_name,    "John Doe"),
            ("Phone",      self._vc_phone,   "+1 555 000 0000"),
            ("Email",      self._vc_email,   "john@example.com"),
            ("Website",    self._vc_website, "https://example.com"),
        ]:
            _label(f, lbl).pack(anchor="w", pady=(4, 0))
            _entry(f, var, ph).pack(fill="x")
            var.trace_add("write", self._trace)

    # ── Email ─────────────────────────────────────────────────────────────────
    def _fields_email(self, f):
        self._em_to      = tk.StringVar(value="")
        self._em_subject = tk.StringVar(value="")

        _label(f, "To").pack(anchor="w")
        _entry(f, self._em_to, "someone@example.com").pack(fill="x")

        _label(f, "Subject").pack(anchor="w", pady=(4, 0))
        _entry(f, self._em_subject).pack(fill="x")

        _label(f, "Body").pack(anchor="w", pady=(4, 0))
        self._em_body = tk.Text(
            f, height=3, font=("Consolas", 9),
            relief="flat", bg=LEGO_LIGHT, fg=LEGO_DARK,
            insertbackground=LEGO_RED,
            highlightthickness=2,
            highlightbackground=LEGO_MID,
        )
        self._em_body.pack(fill="x")
        self._em_body.bind("<KeyRelease>", lambda _: self._notify())

        for v in (self._em_to, self._em_subject):
            v.trace_add("write", self._trace)

    # ── SMS ──────────────────────────────────────────────────────────────────
    def _fields_sms(self, f):
        self._sms_phone   = tk.StringVar(value="")
        self._sms_message = tk.StringVar(value="")

        _label(f, "Phone Number").pack(anchor="w")
        _entry(f, self._sms_phone, "+1 555 000 0000").pack(fill="x")

        _label(f, "Message").pack(anchor="w", pady=(4, 0))
        _entry(f, self._sms_message).pack(fill="x")

        for v in (self._sms_phone, self._sms_message):
            v.trace_add("write", self._trace)

    # ── Plain Text ────────────────────────────────────────────────────────────
    def _fields_text(self, f):
        _label(f, "Text").pack(anchor="w")
        self._plain_text = tk.Text(
            f, height=4, font=("Consolas", 9),
            relief="flat", bg=LEGO_LIGHT, fg=LEGO_DARK,
            insertbackground=LEGO_RED,
            highlightthickness=2,
            highlightbackground=LEGO_MID,
        )
        self._plain_text.pack(fill="x")
        self._plain_text.bind("<KeyRelease>", lambda _: self._notify())

    # ── data getter ───────────────────────────────────────────────────────────

    def get_data(self) -> str:
        """Return the formatted QR data string for the active tab."""
        idx = self._active_tab
        if idx == 0:   # URL
            return format_url(self._url_var.get())
        elif idx == 1:  # WiFi
            return format_wifi(
                self._wifi_ssid.get(),
                self._wifi_pass.get(),
                self._wifi_security.get(),
                self._wifi_hidden.get(),
            )
        elif idx == 2:  # Contact
            return format_vcard(
                self._vc_name.get(),
                self._vc_phone.get(),
                self._vc_email.get(),
                self._vc_website.get(),
            )
        elif idx == 3:  # Email
            body = self._em_body.get("1.0", "end").strip()
            return format_email(
                self._em_to.get(),
                self._em_subject.get(),
                body,
            )
        elif idx == 4:  # SMS
            return format_sms(
                self._sms_phone.get(),
                self._sms_message.get(),
            )
        else:           # Plain text
            return self._plain_text.get("1.0", "end").strip()
