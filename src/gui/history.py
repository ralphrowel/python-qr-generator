"""
src/gui/history.py
HistoryPanel — Modern scrollable session history of generated QR codes.
"""
from __future__ import annotations

import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime
from typing import Callable

# ── Design Tokens ────────────────────────────────────────────────────────────
BG_CONTAINER = "#1e293b"   # Slate card surface
BG_CARD      = "#0f172a"   # Inset card background
BG_HOVER     = "#1e2c44"   # Card hover state
BORDER_COLOR = "#334155"   # Subtle border

TEXT_MAIN    = "#f8fafc"
TEXT_MUTED   = "#94a3b8"
TEXT_DIM     = "#64748b"
ACCENT       = "#6366f1"
DANGER       = "#ef4444"

FONT_HEADING = ("Segoe UI", 9, "bold")
FONT_TITLE   = ("Segoe UI", 8, "bold")
FONT_SUB     = ("Segoe UI", 8)
FONT_MONO    = ("Consolas", 8)
FONT_CAPTION = ("Segoe UI", 7)
FONT_BADGE   = ("Segoe UI", 7, "bold")

THUMB_SIZE = 46
MAX_HISTORY = 12


def _get_type_icon(data: str, settings: dict) -> str:
    idx = settings.get("tab_index")
    if idx is not None:
        icons = ["🔗", "📶", "📇", "📧", "💬", "📝"]
        if 0 <= idx < len(icons):
            return icons[idx]
    if data.startswith("WIFI:"):
        return "📶"
    if data.startswith("BEGIN:VCARD"):
        return "📇"
    if data.startswith("mailto:"):
        return "📧"
    if data.startswith("SMSTO:"):
        return "💬"
    if data.startswith("http://") or data.startswith("https://"):
        return "🔗"
    return "📝"


class HistoryItem:
    def __init__(self, img: Image.Image, label: str, data: str, settings: dict):
        self.img = img
        self.label = label
        self.data = data
        self.settings = settings  # dict of all settings to restore
        self.timestamp = datetime.now().strftime("%I:%M %p")


class HistoryPanel(tk.Frame):
    """
    Scrollable list of recent QR generations.
    Calls `on_restore(item)` when the user clicks an entry.
    """

    def __init__(self, parent, on_restore: Callable[[HistoryItem], None], **kwargs):
        bg = kwargs.pop("bg", BG_CONTAINER)
        super().__init__(parent, bg=bg, **kwargs)
        self._bg = bg
        self._on_restore = on_restore
        self._items: list[HistoryItem] = []
        self._thumb_refs: list[ImageTk.PhotoImage] = []  # prevent garbage collection

        self._build()

    def _build(self):
        # Header bar
        hdr = tk.Frame(self, bg=self._bg)
        hdr.pack(fill="x", padx=10, pady=(4, 6))

        tk.Label(
            hdr,
            text="RECENT QR CODES",
            bg=self._bg,
            fg=TEXT_MAIN,
            font=FONT_HEADING,
        ).pack(side="left")

        clear_btn = tk.Label(
            hdr,
            text="✕ Clear All",
            bg=self._bg,
            fg=TEXT_DIM,
            font=FONT_CAPTION,
            cursor="hand2",
            padx=4,
            pady=2,
        )
        clear_btn.pack(side="right")
        clear_btn.bind("<Button-1>", lambda _: self.clear())
        clear_btn.bind("<Enter>", lambda _: clear_btn.configure(fg=DANGER))
        clear_btn.bind("<Leave>", lambda _: clear_btn.configure(fg=TEXT_DIM))

        # Scrollable canvas container
        container = tk.Frame(self, bg=self._bg)
        container.pack(fill="both", expand=True, padx=8, pady=(0, 6))

        self._canvas = tk.Canvas(
            container,
            bg=self._bg,
            highlightthickness=0,
            bd=0,
        )
        self._scrollbar = tk.Scrollbar(
            container,
            orient="vertical",
            command=self._canvas.yview,
        )
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._list_frame = tk.Frame(self._canvas, bg=self._bg)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._list_frame, anchor="nw",
        )

        self._list_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._show_empty_state()

    def _show_empty_state(self):
        self._empty_label = tk.Label(
            self._list_frame,
            text="No QR codes generated yet.\nGenerate one to see it in history.",
            bg=self._bg,
            fg=TEXT_DIM,
            font=FONT_SUB,
            justify="center",
        )
        self._empty_label.pack(pady=24)

    def _on_frame_configure(self, _):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if self._list_frame.winfo_height() > self._canvas.winfo_height():
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── Public API ───────────────────────────────────────────────────────────

    def add(self, img: Image.Image, label: str, data: str, settings: dict):
        """Prepend a new item. Removes oldest if exceeding MAX_HISTORY."""
        item = HistoryItem(img, label, data, settings)
        self._items.insert(0, item)
        if len(self._items) > MAX_HISTORY:
            self._items.pop()
        self._refresh()

    def remove(self, item: HistoryItem):
        """Remove a single history item."""
        if item in self._items:
            self._items.remove(item)
            self._refresh()

    def clear(self):
        self._items.clear()
        self._refresh()

    # ── Rendering ────────────────────────────────────────────────────────────

    def _refresh(self):
        for widget in self._list_frame.winfo_children():
            widget.destroy()
        self._thumb_refs.clear()

        if not self._items:
            self._show_empty_state()
            return

        for item in self._items:
            self._add_card(item)

    def _add_card(self, item: HistoryItem):
        card = tk.Frame(
            self._list_frame,
            bg=BG_CARD,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            padx=7,
            pady=6,
        )
        card.pack(fill="x", padx=2, pady=3)

        # Thumbnail
        thumb = item.img.copy().resize((THUMB_SIZE, THUMB_SIZE), Image.NEAREST)
        tk_img = ImageTk.PhotoImage(thumb)
        self._thumb_refs.append(tk_img)

        thumb_label = tk.Label(card, image=tk_img, bg=BG_CARD)
        thumb_label.pack(side="left", padx=(0, 8))

        # Metadata container
        info = tk.Frame(card, bg=BG_CARD)
        info.pack(side="left", fill="x", expand=True)

        # Row 1: Type icon + Title + Delete button
        row1 = tk.Frame(info, bg=BG_CARD)
        row1.pack(fill="x")

        icon = _get_type_icon(item.data, item.settings)
        type_icon_lbl = tk.Label(
            row1,
            text=icon,
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=FONT_TITLE,
        )
        type_icon_lbl.pack(side="left", padx=(0, 4))

        title_text = item.label if item.label else "QR Code"
        title_lbl = tk.Label(
            row1,
            text=title_text,
            bg=BG_CARD,
            fg=TEXT_MAIN,
            font=FONT_TITLE,
            anchor="w",
        )
        title_lbl.pack(side="left", fill="x", expand=True)

        del_btn = tk.Label(
            row1,
            text="✕",
            bg=BG_CARD,
            fg=TEXT_DIM,
            font=FONT_BADGE,
            cursor="hand2",
            padx=4,
            pady=0,
        )
        del_btn.pack(side="right")

        def _on_delete(e):
            self.remove(item)
            return "break"

        del_btn.bind("<Button-1>", _on_delete)
        del_btn.bind("<Enter>", lambda _: del_btn.configure(fg=DANGER))
        del_btn.bind("<Leave>", lambda _: del_btn.configure(fg=TEXT_DIM))

        # Row 2: Data snippet
        disp_data = item.data if len(item.data) <= 26 else item.data[:24] + "…"
        data_lbl = tk.Label(
            info,
            text=disp_data,
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=FONT_MONO,
            anchor="w",
        )
        data_lbl.pack(anchor="w", pady=(1, 0))

        # Row 3: Timestamp & Spec badge
        row3 = tk.Frame(info, bg=BG_CARD)
        row3.pack(fill="x", pady=(2, 0))

        time_lbl = tk.Label(
            row3,
            text=item.timestamp,
            bg=BG_CARD,
            fg=TEXT_DIM,
            font=FONT_CAPTION,
            anchor="w",
        )
        time_lbl.pack(side="left")

        ec_val = item.settings.get("error_correction", "M")
        sz_val = item.settings.get("size", 300)
        spec_lbl = tk.Label(
            row3,
            text=f"EC-{ec_val} • {sz_val}px",
            bg=BG_CARD,
            fg=TEXT_DIM,
            font=FONT_CAPTION,
        )
        spec_lbl.pack(side="right")

        # Hover & Click bindings
        restore_widgets = [card, thumb_label, info, row1, type_icon_lbl, title_lbl, data_lbl, row3, time_lbl, spec_lbl]

        def _enter(_):
            card.configure(bg=BG_HOVER, highlightbackground=ACCENT)
            for w in (info, row1, type_icon_lbl, thumb_label, title_lbl, data_lbl, row3, time_lbl, spec_lbl):
                w.configure(bg=BG_HOVER)

        def _leave(_):
            card.configure(bg=BG_CARD, highlightbackground=BORDER_COLOR)
            for w in (info, row1, type_icon_lbl, thumb_label, title_lbl, data_lbl, row3, time_lbl, spec_lbl):
                w.configure(bg=BG_CARD)

        for w in restore_widgets:
            w.bind("<Enter>", _enter)
            w.bind("<Leave>", _leave)
            w.bind("<Button-1>", lambda _, it=item: self._on_restore(it))
