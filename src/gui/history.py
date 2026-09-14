"""
src/gui/history.py
HistoryPanel — scrollable session history of generated QR codes.
"""
from __future__ import annotations

import tkinter as tk
from PIL import Image, ImageTk
from datetime import datetime
from typing import Callable

LEGO_RED    = "#d01012"
LEGO_BLUE   = "#0088dd"
LEGO_MID    = "#3377aa"
LEGO_YELLOW = "#ffff00"
LEGO_LIGHT  = "#ebebeb"
LEGO_DARK   = "#1a1a1a"
LEGO_WHITE  = "#ffffff"

THUMB_SIZE = 52
MAX_HISTORY = 10


class HistoryItem:
    def __init__(self, img: Image.Image, label: str, data: str,
                 settings: dict):
        self.img = img
        self.label = label
        self.data = data
        self.settings = settings  # dict of all settings to restore
        self.timestamp = datetime.now().strftime("%H:%M:%S")


class HistoryPanel(tk.Frame):
    """
    Scrollable list of recent QR generations.
    Calls `on_restore(item)` when the user clicks a history entry.
    """

    def __init__(self, parent, on_restore: Callable[[HistoryItem], None],
                 **kwargs):
        bg = kwargs.pop("bg", LEGO_BLUE)
        super().__init__(parent, bg=bg, **kwargs)
        self._bg = bg
        self._on_restore = on_restore
        self._items: list[HistoryItem] = []
        self._thumb_refs: list[ImageTk.PhotoImage] = []  # prevent GC

        self._build()

    def _build(self):
        hdr = tk.Frame(self, bg=self._bg)
        hdr.pack(fill="x", padx=8, pady=(8, 4))
        tk.Label(
            hdr, text="HISTORY",
            bg=self._bg, fg=LEGO_YELLOW,
            font=("Arial Black", 8),
        ).pack(side="left")
        tk.Button(
            hdr, text="✕ Clear",
            relief="flat", bd=0,
            bg=self._bg, fg=LEGO_LIGHT,
            font=("Arial", 7),
            cursor="hand2",
            command=self.clear,
        ).pack(side="right")

        # Scrollable canvas
        container = tk.Frame(self, bg=self._bg)
        container.pack(fill="both", expand=True, padx=4)

        self._canvas = tk.Canvas(
            container, bg=self._bg,
            highlightthickness=0,
        )
        scrollbar = tk.Scrollbar(
            container, orient="vertical",
            command=self._canvas.yview,
        )
        self._canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._list_frame = tk.Frame(self._canvas, bg=self._bg)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._list_frame, anchor="nw",
        )

        self._list_frame.bind("<Configure>", self._on_frame_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._empty_label = tk.Label(
            self._list_frame,
            text="No QR codes yet.\nGenerate one to\nsee it here.",
            bg=self._bg, fg=LEGO_MID,
            font=("Arial", 8),
            justify="center",
        )
        self._empty_label.pack(pady=20)

    def _on_frame_configure(self, _):
        self._canvas.configure(
            scrollregion=self._canvas.bbox("all")
        )

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(
            self._canvas_window, width=event.width
        )

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ── public API ───────────────────────────────────────────────────────────

    def add(self, img: Image.Image, label: str, data: str, settings: dict):
        """Prepend a new item. Removes oldest if over MAX_HISTORY."""
        item = HistoryItem(img, label, data, settings)
        self._items.insert(0, item)
        if len(self._items) > MAX_HISTORY:
            self._items.pop()
        self._refresh()

    def clear(self):
        self._items.clear()
        self._refresh()

    # ── rendering ────────────────────────────────────────────────────────────

    def _refresh(self):
        for widget in self._list_frame.winfo_children():
            widget.destroy()
        self._thumb_refs.clear()

        if not self._items:
            self._empty_label = tk.Label(
                self._list_frame,
                text="No QR codes yet.\nGenerate one to\nsee it here.",
                bg=self._bg, fg=LEGO_MID,
                font=("Arial", 8),
                justify="center",
            )
            self._empty_label.pack(pady=20)
            return

        for i, item in enumerate(self._items):
            self._add_card(i, item)

    def _add_card(self, idx: int, item: HistoryItem):
        card_bg = LEGO_MID if idx % 2 == 0 else self._bg
        card = tk.Frame(
            self._list_frame, bg=card_bg,
            cursor="hand2",
        )
        card.pack(fill="x", padx=4, pady=2)

        # thumbnail
        thumb = item.img.copy().resize(
            (THUMB_SIZE, THUMB_SIZE), Image.NEAREST
        )
        tk_img = ImageTk.PhotoImage(thumb)
        self._thumb_refs.append(tk_img)

        tk.Label(card, image=tk_img, bg=card_bg).pack(
            side="left", padx=6, pady=4
        )

        # text
        info = tk.Frame(card, bg=card_bg)
        info.pack(side="left", fill="x", expand=True, pady=4)

        tk.Label(
            info,
            text=item.label or "(no label)",
            bg=card_bg, fg=LEGO_WHITE,
            font=("Arial Black", 7),
            anchor="w",
        ).pack(anchor="w")

        # truncate long data
        disp = item.data if len(item.data) <= 28 else item.data[:25] + "…"
        tk.Label(
            info, text=disp,
            bg=card_bg, fg=LEGO_LIGHT,
            font=("Consolas", 7),
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            info, text=item.timestamp,
            bg=card_bg, fg=LEGO_MID if card_bg != LEGO_MID else LEGO_LIGHT,
            font=("Arial", 6),
            anchor="w",
        ).pack(anchor="w")

        # click to restore
        for widget in (card, info):
            widget.bind("<Button-1>", lambda _, it=item: self._on_restore(it))
        for child in card.winfo_children():
            child.bind("<Button-1>", lambda _, it=item: self._on_restore(it))
