"""
src/gui/qr_type_panel.py
Segmented tab strip + responsive modern input fields for each QR content type.
"""
from __future__ import annotations
import tkinter as tk
from typing import Callable

from utils.helpers import (
    format_url, format_wifi, format_vcard, format_email, format_sms
)

# ── Design Tokens ────────────────────────────────────────────────────────────
BG_PANEL     = "#1e293b"   # Slate card surface
BG_INPUT     = "#0f172a"   # Inset dark input background
BG_TAB_IDLE  = "#0f172a"   # Inactive tab background
BG_TAB_HOVER = "#334155"   # Inactive tab hover
ACCENT       = "#6366f1"   # Indigo active color
ACCENT_HOVER = "#4f46e5"

BORDER_IDLE  = "#334155"
BORDER_FOCUS = "#6366f1"

TEXT_MAIN    = "#f8fafc"
TEXT_MUTED   = "#94a3b8"
TEXT_DIM     = "#64748b"

FONT_TAB     = ("Segoe UI", 9, "bold")
FONT_LABEL   = ("Segoe UI", 8, "bold")
FONT_INPUT   = ("Segoe UI", 9)
FONT_MONO    = ("Consolas", 9)
FONT_SMALL   = ("Segoe UI", 8)

TABS = [
    ("🔗", "URL"),
    ("📶", "WiFi"),
    ("📇", "Contact"),
    ("📧", "Email"),
    ("💬", "SMS"),
    ("📝", "Text"),
]


def _create_entry(parent, var: tk.StringVar, placeholder: str = "", show: str = "") -> tk.Entry:
    """Create a modern styled text entry."""
    entry = tk.Entry(
        parent,
        textvariable=var,
        font=FONT_INPUT,
        relief="flat",
        bg=BG_INPUT,
        fg=TEXT_MAIN,
        insertbackground=TEXT_MAIN,
        highlightthickness=1,
        highlightbackground=BORDER_IDLE,
        highlightcolor=BORDER_FOCUS,
        show=show,
    )
    if placeholder and not var.get():
        var.set(placeholder)
    return entry


def _create_label(parent, text: str) -> tk.Label:
    """Create a consistent small field label."""
    return tk.Label(
        parent,
        text=text.upper(),
        bg=parent["bg"],
        fg=TEXT_MUTED,
        font=FONT_LABEL,
        anchor="w",
    )


class QRTypePanel(tk.Frame):
    """
    A segmented-tab control that displays tailored input forms
    for different QR types (URL, WiFi, Contact, Email, SMS, Plain Text).
    Calls `on_change(data_string)` on every keystroke.
    """

    def __init__(self, parent, on_change: Callable[[str], None], **kwargs):
        bg = kwargs.pop("bg", BG_PANEL)
        super().__init__(parent, bg=bg, **kwargs)
        self._bg = bg
        self._on_change = on_change
        self._active_tab = 0
        self._field_frame: tk.Frame | None = None

        self._build_tab_strip()
        self._build_fields(0)

    # ── Tab strip ────────────────────────────────────────────────────────────

    def _build_tab_strip(self):
        strip_container = tk.Frame(self, bg=self._bg)
        strip_container.pack(fill="x", pady=(0, 10))

        # Pill container
        pill_box = tk.Frame(
            strip_container,
            bg=BG_TAB_IDLE,
            padx=2,
            pady=2,
            highlightthickness=1,
            highlightbackground=BORDER_IDLE,
        )
        pill_box.pack(fill="x")

        self._tab_btns: list[tk.Label] = []
        for i, (icon, name) in enumerate(TABS):
            pill_box.columnconfigure(i, weight=1)
            btn = tk.Label(
                pill_box,
                text=f"{icon} {name}",
                font=FONT_TAB,
                bg=BG_TAB_IDLE,
                fg=TEXT_MUTED,
                cursor="hand2",
                padx=8,
                pady=7,
            )
            btn.grid(row=0, column=i, sticky="nsew", padx=1)
            btn.bind("<Button-1>", lambda _, idx=i: self._select_tab(idx))
            btn.bind("<Enter>", lambda _, b=btn, idx=i: self._on_tab_enter(b, idx))
            btn.bind("<Leave>", lambda _, b=btn, idx=i: self._on_tab_leave(b, idx))
            self._tab_btns.append(btn)

        self._highlight_tab(0)

    def _on_tab_enter(self, btn: tk.Label, idx: int):
        if idx != self._active_tab:
            btn.configure(bg=BG_TAB_HOVER, fg=TEXT_MAIN)

    def _on_tab_leave(self, btn: tk.Label, idx: int):
        if idx != self._active_tab:
            btn.configure(bg=BG_TAB_IDLE, fg=TEXT_MUTED)

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
                btn.configure(bg=ACCENT, fg="#ffffff")
            else:
                btn.configure(bg=BG_TAB_IDLE, fg=TEXT_MUTED)

    # ── Field Builders ───────────────────────────────────────────────────────

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
    def _fields_url(self, f: tk.Frame):
        self._url_var = tk.StringVar(value="https://example.com")

        top_row = tk.Frame(f, bg=self._bg)
        top_row.pack(fill="x", pady=(0, 3))
        _create_label(top_row, "Website URL").pack(side="left")

        input_row = tk.Frame(f, bg=self._bg)
        input_row.pack(fill="x")

        e = _create_entry(input_row, self._url_var)
        e.pack(side="left", fill="x", expand=True, ipady=4)

        paste_btn = tk.Label(
            input_row,
            text="📋 Paste",
            bg=BG_TAB_HOVER,
            fg=TEXT_MAIN,
            font=FONT_SMALL,
            cursor="hand2",
            padx=8,
            pady=4,
            highlightthickness=1,
            highlightbackground=BORDER_IDLE,
        )
        paste_btn.pack(side="left", padx=(6, 0))

        def _do_paste(_):
            try:
                clip = f.clipboard_get().strip()
                if clip:
                    self._url_var.set(clip)
            except Exception:
                pass

        paste_btn.bind("<Button-1>", _do_paste)
        paste_btn.bind("<Enter>", lambda _: paste_btn.configure(bg=ACCENT))
        paste_btn.bind("<Leave>", lambda _: paste_btn.configure(bg=BG_TAB_HOVER))

        self._url_var.trace_add("write", self._trace)

    # ── WiFi ─────────────────────────────────────────────────────────────────
    def _fields_wifi(self, f: tk.Frame):
        self._wifi_ssid     = tk.StringVar(value="")
        self._wifi_pass     = tk.StringVar(value="")
        self._wifi_security = tk.StringVar(value="WPA")
        self._wifi_hidden   = tk.BooleanVar(value=False)
        self._wifi_show_pass = False

        grid = tk.Frame(f, bg=self._bg)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1, uniform="wifi")
        grid.columnconfigure(1, weight=1, uniform="wifi")

        # Row 0: SSID
        c0 = tk.Frame(grid, bg=self._bg)
        c0.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        _create_label(c0, "Network SSID").pack(anchor="w", pady=(0, 2))
        _create_entry(c0, self._wifi_ssid, "MyHomeWiFi").pack(fill="x", ipady=4)

        # Row 0: Password + Show/Hide Toggle
        c1 = tk.Frame(grid, bg=self._bg)
        c1.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        _create_label(c1, "Password").pack(anchor="w", pady=(0, 2))

        pass_row = tk.Frame(c1, bg=self._bg)
        pass_row.pack(fill="x")

        self._wifi_pass_entry = _create_entry(pass_row, self._wifi_pass, show="•")
        self._wifi_pass_entry.pack(side="left", fill="x", expand=True, ipady=4)

        eye_btn = tk.Label(
            pass_row,
            text="👁",
            bg=BG_TAB_HOVER,
            fg=TEXT_MAIN,
            font=FONT_SMALL,
            cursor="hand2",
            padx=6,
            pady=4,
            highlightthickness=1,
            highlightbackground=BORDER_IDLE,
        )
        eye_btn.pack(side="left", padx=(4, 0))

        def _toggle_pass(_):
            self._wifi_show_pass = not self._wifi_show_pass
            self._wifi_pass_entry.configure(show="" if self._wifi_show_pass else "•")
            eye_btn.configure(text="🙈" if self._wifi_show_pass else "👁")

        eye_btn.bind("<Button-1>", _toggle_pass)

        # Row 1: Security & Hidden Checkbox
        opt_frame = tk.Frame(f, bg=self._bg)
        opt_frame.pack(fill="x", pady=(8, 0))

        _create_label(opt_frame, "Security:").pack(side="left", padx=(0, 6))
        for sec in ("WPA", "WEP", "None"):
            val = "nopass" if sec == "None" else sec
            rb = tk.Radiobutton(
                opt_frame,
                text=sec,
                variable=self._wifi_security,
                value=val,
                bg=self._bg,
                fg=TEXT_MAIN,
                activebackground=self._bg,
                activeforeground=TEXT_MAIN,
                selectcolor=BG_INPUT,
                font=FONT_INPUT,
                highlightthickness=0,
                bd=0,
            )
            rb.pack(side="left", padx=4)

        cb = tk.Checkbutton(
            opt_frame,
            text="Hidden SSID",
            variable=self._wifi_hidden,
            bg=self._bg,
            fg=TEXT_MUTED,
            activebackground=self._bg,
            activeforeground=TEXT_MAIN,
            selectcolor=BG_INPUT,
            font=FONT_INPUT,
            highlightthickness=0,
            bd=0,
        )
        cb.pack(side="right")

        for v in (self._wifi_ssid, self._wifi_pass,
                  self._wifi_security, self._wifi_hidden):
            v.trace_add("write", self._trace)

    # ── Contact (vCard) ───────────────────────────────────────────────────────
    def _fields_vcard(self, f: tk.Frame):
        self._vc_name    = tk.StringVar(value="")
        self._vc_phone   = tk.StringVar(value="")
        self._vc_email   = tk.StringVar(value="")
        self._vc_website = tk.StringVar(value="")
        self._vc_org     = tk.StringVar(value="")
        self._vc_title   = tk.StringVar(value="")

        grid = tk.Frame(f, bg=self._bg)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1, uniform="vc")
        grid.columnconfigure(1, weight=1, uniform="vc")

        items = [
            ("Full Name", self._vc_name, "John Doe", 0, 0),
            ("Phone Number", self._vc_phone, "+1 555 019 2831", 0, 1),
            ("Email Address", self._vc_email, "john@example.com", 1, 0),
            ("Website", self._vc_website, "https://example.com", 1, 1),
            ("Company / Org", self._vc_org, "Acme Corp", 2, 0),
            ("Job Title", self._vc_title, "Product Designer", 2, 1),
        ]

        for lbl, var, ph, r, c in items:
            cell = tk.Frame(grid, bg=self._bg)
            pad_x = (0, 5) if c == 0 else (5, 0)
            pad_y = (0, 6) if r < 2 else (0, 0)
            cell.grid(row=r, column=c, sticky="nsew", padx=pad_x, pady=pad_y)
            _create_label(cell, lbl).pack(anchor="w", pady=(0, 2))
            _create_entry(cell, var, ph).pack(fill="x", ipady=4)
            var.trace_add("write", self._trace)

    # ── Email ─────────────────────────────────────────────────────────────────
    def _fields_email(self, f: tk.Frame):
        self._em_to      = tk.StringVar(value="")
        self._em_subject = tk.StringVar(value="")

        grid = tk.Frame(f, bg=self._bg)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1, uniform="em")
        grid.columnconfigure(1, weight=1, uniform="em")

        c0 = tk.Frame(grid, bg=self._bg)
        c0.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        _create_label(c0, "Recipient Email").pack(anchor="w", pady=(0, 2))
        _create_entry(c0, self._em_to, "contact@example.com").pack(fill="x", ipady=4)

        c1 = tk.Frame(grid, bg=self._bg)
        c1.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        _create_label(c1, "Subject").pack(anchor="w", pady=(0, 2))
        _create_entry(c1, self._em_subject).pack(fill="x", ipady=4)

        _create_label(f, "Message Body").pack(anchor="w", pady=(6, 2))
        self._em_body = tk.Text(
            f, height=3, font=FONT_INPUT,
            relief="flat", bg=BG_INPUT, fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN,
            highlightthickness=1,
            highlightbackground=BORDER_IDLE,
            highlightcolor=BORDER_FOCUS,
        )
        self._em_body.pack(fill="x")
        self._em_body.bind("<KeyRelease>", lambda _: self._notify())

        for v in (self._em_to, self._em_subject):
            v.trace_add("write", self._trace)

    # ── SMS ──────────────────────────────────────────────────────────────────
    def _fields_sms(self, f: tk.Frame):
        self._sms_phone   = tk.StringVar(value="")
        self._sms_message = tk.StringVar(value="")

        grid = tk.Frame(f, bg=self._bg)
        grid.pack(fill="x")
        grid.columnconfigure(0, weight=1, uniform="sms")
        grid.columnconfigure(1, weight=1, uniform="sms")

        c0 = tk.Frame(grid, bg=self._bg)
        c0.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        _create_label(c0, "Phone Number").pack(anchor="w", pady=(0, 2))
        _create_entry(c0, self._sms_phone, "+1 555 019 2831").pack(fill="x", ipady=4)

        c1 = tk.Frame(grid, bg=self._bg)
        c1.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        _create_label(c1, "Message").pack(anchor="w", pady=(0, 2))
        _create_entry(c1, self._sms_message).pack(fill="x", ipady=4)

        for v in (self._sms_phone, self._sms_message):
            v.trace_add("write", self._trace)

    # ── Plain Text ────────────────────────────────────────────────────────────
    def _fields_text(self, f: tk.Frame):
        top = tk.Frame(f, bg=self._bg)
        top.pack(fill="x", pady=(0, 2))

        _create_label(top, "Plain Text / Notes").pack(side="left")
        self._char_count_lbl = tk.Label(
            top,
            text="0 characters",
            bg=self._bg,
            fg=TEXT_DIM,
            font=FONT_SMALL,
        )
        self._char_count_lbl.pack(side="right")

        self._plain_text = tk.Text(
            f, height=3, font=FONT_INPUT,
            relief="flat", bg=BG_INPUT, fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN,
            highlightthickness=1,
            highlightbackground=BORDER_IDLE,
            highlightcolor=BORDER_FOCUS,
        )
        self._plain_text.pack(fill="x")

        def _on_key(_):
            txt = self._plain_text.get("1.0", "end-1c")
            self._char_count_lbl.configure(text=f"{len(txt)} characters")
            self._notify()

        self._plain_text.bind("<KeyRelease>", _on_key)

    # ── Data Getter & Snapshot ───────────────────────────────────────────────

    def get_active_tab(self) -> int:
        return self._active_tab

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
            org = getattr(self, "_vc_org", tk.StringVar(value="")).get()
            title = getattr(self, "_vc_title", tk.StringVar(value="")).get()
            return format_vcard(
                self._vc_name.get(),
                self._vc_phone.get(),
                self._vc_email.get(),
                self._vc_website.get(),
                org=org,
                title=title,
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

    def get_snapshot(self) -> dict:
        """Capture all current form field states for history restoration."""
        idx = self._active_tab
        snapshot = {"tab_index": idx}
        if idx == 0:
            snapshot["url"] = self._url_var.get()
        elif idx == 1:
            snapshot["wifi_ssid"] = self._wifi_ssid.get()
            snapshot["wifi_pass"] = self._wifi_pass.get()
            snapshot["wifi_sec"]  = self._wifi_security.get()
            snapshot["wifi_hid"]  = self._wifi_hidden.get()
        elif idx == 2:
            snapshot["vc_name"]    = self._vc_name.get()
            snapshot["vc_phone"]   = self._vc_phone.get()
            snapshot["vc_email"]   = self._vc_email.get()
            snapshot["vc_website"] = self._vc_website.get()
            snapshot["vc_org"]     = getattr(self, "_vc_org", tk.StringVar(value="")).get()
            snapshot["vc_title"]   = getattr(self, "_vc_title", tk.StringVar(value="")).get()
        elif idx == 3:
            snapshot["em_to"]      = self._em_to.get()
            snapshot["em_subject"] = self._em_subject.get()
            snapshot["em_body"]    = self._em_body.get("1.0", "end-1c")
        elif idx == 4:
            snapshot["sms_phone"] = self._sms_phone.get()
            snapshot["sms_msg"]   = self._sms_message.get()
        else:
            snapshot["text"] = self._plain_text.get("1.0", "end-1c")
        return snapshot

    def restore_snapshot(self, snapshot: dict):
        """Restore form fields and active tab from a snapshot."""
        idx = snapshot.get("tab_index", 0)
        self._select_tab(idx)
        if idx == 0 and "url" in snapshot:
            self._url_var.set(snapshot["url"])
        elif idx == 1:
            self._wifi_ssid.set(snapshot.get("wifi_ssid", ""))
            self._wifi_pass.set(snapshot.get("wifi_pass", ""))
            self._wifi_security.set(snapshot.get("wifi_sec", "WPA"))
            self._wifi_hidden.set(snapshot.get("wifi_hid", False))
        elif idx == 2:
            self._vc_name.set(snapshot.get("vc_name", ""))
            self._vc_phone.set(snapshot.get("vc_phone", ""))
            self._vc_email.set(snapshot.get("vc_email", ""))
            self._vc_website.set(snapshot.get("vc_website", ""))
            if hasattr(self, "_vc_org"):
                self._vc_org.set(snapshot.get("vc_org", ""))
            if hasattr(self, "_vc_title"):
                self._vc_title.set(snapshot.get("vc_title", ""))
        elif idx == 3:
            self._em_to.set(snapshot.get("em_to", ""))
            self._em_subject.set(snapshot.get("em_subject", ""))
            self._em_body.delete("1.0", "end")
            self._em_body.insert("1.0", snapshot.get("em_body", ""))
        elif idx == 4:
            self._sms_phone.set(snapshot.get("sms_phone", ""))
            self._sms_message.set(snapshot.get("sms_msg", ""))
        elif idx == 5:
            self._plain_text.delete("1.0", "end")
            self._plain_text.insert("1.0", snapshot.get("text", ""))
            if hasattr(self, "_char_count_lbl"):
                self._char_count_lbl.configure(text=f"{len(snapshot.get('text', ''))} characters")
        self._notify()
