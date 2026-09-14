"""
src/gui/app.py
QR Studio — Modern Professional QR Code Generator Desktop Application.
"""
from __future__ import annotations

import os
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
from PIL import Image, ImageTk

from core.generator import generate_qr_image, generate_qr
from src.gui.qr_type_panel import QRTypePanel
from src.gui.history import HistoryPanel
from utils.helpers import copy_image_to_clipboard

# ── Design Tokens ────────────────────────────────────────────────────────────
BG_APP       = "#0b0f19"   # Dark slate background
BG_HEADER    = "#1e293b"   # Header bar surface
BG_CARD      = "#1e293b"   # Slate card surface
BG_INPUT     = "#0f172a"   # Inset field background
BG_SURFACE   = "#0f172a"   # Inner preview frame background
BG_HOVER     = "#334155"   # Hover state
BORDER_COLOR = "#334155"   # Subtle border
BORDER_FOCUS = "#6366f1"   # Accent highlight

TEXT_MAIN    = "#f8fafc"   # Crisp white
TEXT_MUTED   = "#94a3b8"   # Secondary muted
TEXT_DIM     = "#64748b"   # Tertiary helper

ACCENT       = "#6366f1"   # Electric Indigo
ACCENT_HOVER = "#4f46e5"   # Indigo hover
ACCENT_GREEN = "#10b981"   # Emerald success / live sync
DANGER       = "#ef4444"

FONT_FAMILY  = "Segoe UI"
FONT_TITLE   = (FONT_FAMILY, 12, "bold")
FONT_HEADING = (FONT_FAMILY, 9, "bold")
FONT_BODY    = (FONT_FAMILY, 9)
FONT_BOLD    = (FONT_FAMILY, 9, "bold")
FONT_SMALL   = (FONT_FAMILY, 8)
FONT_MONO    = ("Consolas", 9)

PREVIEW_SIZE = 210

COLOR_PRESETS = [
    ("Classic", "#000000", "#ffffff"),
    ("Slate",   "#0f172a", "#f8fafc"),
    ("Indigo",  "#4338ca", "#eef2ff"),
    ("Emerald", "#065f46", "#ecfdf5"),
    ("Cyan",    "#06b6d4", "#0b0f19"),
    ("Sunset",  "#9f1239", "#fff1f2"),
]


class ModernButton(tk.Label):
    """Modern flat button with hover states and click callback."""

    def __init__(
        self,
        parent,
        text: str,
        command=None,
        bg=ACCENT,
        fg="#ffffff",
        hover_bg=ACCENT_HOVER,
        font=FONT_BOLD,
        pady=8,
        padx=12,
        **kwargs,
    ):
        super().__init__(
            parent,
            text=text,
            bg=bg,
            fg=fg,
            font=font,
            cursor="hand2",
            padx=padx,
            pady=pady,
            **kwargs,
        )
        self._default_bg = bg
        self._hover_bg = hover_bg
        self._cmd = command

        self.bind("<Enter>", lambda _: self.configure(bg=self._hover_bg))
        self.bind("<Leave>", lambda _: self.configure(bg=self._default_bg))
        self.bind("<Button-1>", self._on_click)

    def _on_click(self, _):
        if self._cmd:
            self._cmd()


class ModernColorSwatch(tk.Frame):
    """A sleek color-picker swatch with hex indicator."""

    def __init__(self, parent, label: str, initial: str, on_change=None, **kwargs):
        super().__init__(parent, bg=BG_CARD, **kwargs)
        self.color = initial
        self._label_text = label
        self._on_change = on_change

        lbl_frame = tk.Frame(self, bg=BG_CARD)
        lbl_frame.pack(fill="x", pady=(0, 2))

        tk.Label(
            lbl_frame,
            text=label.upper(),
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=FONT_SMALL,
        ).pack(side="left")

        self.hex_label = tk.Label(
            lbl_frame,
            text=self.color.upper(),
            bg=BG_CARD,
            fg=TEXT_DIM,
            font=FONT_SMALL,
        )
        self.hex_label.pack(side="right")

        # Clickable swatch box
        self.swatch = tk.Frame(
            self,
            bg=initial,
            height=28,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
        )
        self.swatch.pack(fill="x")
        self.swatch.pack_propagate(False)
        self.swatch.bind("<Button-1>", self._pick)

    def set_color(self, new_color: str):
        self.color = new_color
        self.swatch.configure(bg=self.color)
        self.hex_label.configure(text=self.color.upper())

    def _pick(self, _):
        result = colorchooser.askcolor(
            color=self.color,
            title=f"Select {self._label_text} Color",
        )
        if result and result[1]:
            self.set_color(result[1])
            if self._on_change:
                self._on_change()


class QRApp:
    """Main Application Controller and UI Architecture."""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("QR Studio — Professional Modern QR Code Generator")
        self.root.resizable(True, True)
        self.root.minsize(960, 680)
        self.root.configure(bg=BG_APP)

        self._current_image: Image.Image | None = None
        self._preview_tk: ImageTk.PhotoImage | None = None
        self._debounce_job = None
        self._logo_path: str | None = None

        self.ec_var = tk.StringVar(value="M")
        self.size_var = tk.IntVar(value=300)
        self.label_var = tk.StringVar(value="Scan me!")

        self._build_ui()
        self.root.geometry("1040x730")
        self._bind_shortcuts()

        # Trigger initial preview safely
        self._init_job = self.root.after(100, self._trigger_live_preview)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        """Clean up pending after callbacks before destroying."""
        if self._debounce_job is not None:
            try:
                self.root.after_cancel(self._debounce_job)
            except Exception:
                pass
            self._debounce_job = None
        if hasattr(self, "_init_job") and self._init_job is not None:
            try:
                self.root.after_cancel(self._init_job)
            except Exception:
                pass
            self._init_job = None
        self.root.destroy()

    # ── Shortcuts ────────────────────────────────────────────────────────────

    def _bind_shortcuts(self):
        self.root.bind("<Control-Return>", lambda _: self.generate())
        self.root.bind("<Control-s>",      lambda _: self.save_as())
        self.root.bind("<Control-S>",      lambda _: self.save_as())
        self.root.bind("<Control-c>",      lambda _: self.copy_to_clipboard())

    # ── UI Construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()

        # Main 2-column workspace container
        self.workspace = tk.Frame(self.root, bg=BG_APP)
        self.workspace.pack(fill="both", expand=True, padx=14, pady=8)

        # Right Column (Live Preview + Actions + History)
        self._build_right_column(self.workspace)

        # Left Column (Configuration & Form Cards in responsive scroll view)
        self._build_left_column(self.workspace)

        self._build_status_bar()

    def _build_header(self):
        header = tk.Frame(self.root, bg=BG_HEADER, height=52)
        header.pack(fill="x")
        header.pack_propagate(False)

        inner = tk.Frame(header, bg=BG_HEADER)
        inner.pack(fill="both", expand=True, padx=16)

        # Brand Badge & Title
        badge = tk.Label(
            inner,
            text=" ⚡ ",
            bg=ACCENT,
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            padx=3,
            pady=1,
        )
        badge.pack(side="left", pady=11, padx=(0, 10))

        title_lbl = tk.Label(
            inner,
            text="QR STUDIO",
            bg=BG_HEADER,
            fg=TEXT_MAIN,
            font=FONT_TITLE,
        )
        title_lbl.pack(side="left", pady=11)

        subtitle_lbl = tk.Label(
            inner,
            text="Professional Generator & Customizer",
            bg=BG_HEADER,
            fg=TEXT_MUTED,
            font=FONT_BODY,
        )
        subtitle_lbl.pack(side="left", padx=12, pady=11)

        # Version & Ready Badges
        ver_pill = tk.Label(
            inner,
            text="v2.2 Pro",
            bg=BG_APP,
            fg=TEXT_MUTED,
            font=FONT_SMALL,
            padx=8,
            pady=3,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
        )
        ver_pill.pack(side="right", pady=14)

        status_pill = tk.Label(
            inner,
            text="● Ready",
            bg=BG_HEADER,
            fg=ACCENT_GREEN,
            font=FONT_SMALL,
            padx=8,
        )
        status_pill.pack(side="right", pady=14, padx=(0, 8))

    def _build_left_column(self, parent: tk.Frame):
        """Left Column: Content Definition and Customization Cards with smooth scrolling."""
        self.left_container = tk.Frame(parent, bg=BG_APP)
        self.left_container.pack(side="left", fill="both", expand=True, padx=(0, 12))

        # Scrollable Canvas container for Left column
        self._left_canvas = tk.Canvas(
            self.left_container,
            bg=BG_APP,
            highlightthickness=0,
            bd=0,
        )
        self._left_scrollbar = tk.Scrollbar(
            self.left_container,
            orient="vertical",
            command=self._left_canvas.yview,
        )
        self._left_canvas.configure(yscrollcommand=self._left_scrollbar.set)

        self._left_scrollbar.pack(side="right", fill="y")
        self._left_canvas.pack(side="left", fill="both", expand=True)

        self._left_content = tk.Frame(self._left_canvas, bg=BG_APP)
        self._left_window = self._left_canvas.create_window(
            (0, 0), window=self._left_content, anchor="nw",
        )

        def _on_left_frame_config(_):
            self._left_canvas.configure(scrollregion=self._left_canvas.bbox("all"))

        def _on_left_canvas_config(event):
            self._left_canvas.itemconfig(self._left_window, width=event.width)

        self._left_content.bind("<Configure>", _on_left_frame_config)
        self._left_canvas.bind("<Configure>", _on_left_canvas_config)

        def _on_left_wheel(event):
            if self._left_content.winfo_height() > self._left_canvas.winfo_height():
                self._left_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self._left_canvas.bind_all("<MouseWheel>", _on_left_wheel)

        # ── Card 1: Content Definition ───────────────────────────────────────
        content_card = tk.Frame(
            self._left_content,
            bg=BG_CARD,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            padx=16,
            pady=14,
        )
        content_card.pack(fill="x", pady=(0, 10))

        tk.Label(
            content_card,
            text="1. SELECT CONTENT TYPE & INPUT DATA",
            bg=BG_CARD,
            fg=TEXT_MAIN,
            font=FONT_HEADING,
        ).pack(anchor="w", pady=(0, 10))

        self.type_panel = QRTypePanel(
            content_card,
            on_change=self._on_data_change,
            bg=BG_CARD,
        )
        self.type_panel.pack(fill="x")

        # ── Card 2: Customization Settings ───────────────────────────────────
        settings_card = tk.Frame(
            self._left_content,
            bg=BG_CARD,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            padx=16,
            pady=14,
        )
        settings_card.pack(fill="x")

        tk.Label(
            settings_card,
            text="2. DESIGN & ENCODING SETTINGS",
            bg=BG_CARD,
            fg=TEXT_MAIN,
            font=FONT_HEADING,
        ).pack(anchor="w", pady=(0, 12))

        # ── Color Presets Strip ──────────────────────────────────────────────
        preset_box = tk.Frame(settings_card, bg=BG_CARD)
        preset_box.pack(fill="x", pady=(0, 12))

        tk.Label(
            preset_box,
            text="QUICK COLOR PRESETS",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=FONT_SMALL,
        ).pack(anchor="w", pady=(0, 4))

        preset_strip = tk.Frame(
            preset_box,
            bg=BG_INPUT,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            padx=3,
            pady=3,
        )
        preset_strip.pack(fill="x")

        self._preset_btns: list[tk.Label] = []
        for idx, (name, dark_c, light_c) in enumerate(COLOR_PRESETS):
            preset_strip.columnconfigure(idx, weight=1)
            btn = tk.Label(
                preset_strip,
                text=name,
                bg=BG_INPUT,
                fg=TEXT_MUTED,
                font=FONT_SMALL,
                cursor="hand2",
                pady=4,
            )
            btn.grid(row=0, column=idx, sticky="nsew", padx=1)
            btn.bind("<Button-1>", lambda _, d=dark_c, l=light_c, b=btn: self._apply_preset(d, l, b))
            self._preset_btns.append(btn)

        # Highlight default Classic preset
        if self._preset_btns:
            self._preset_btns[0].configure(bg=ACCENT, fg="#ffffff")

        # ── Settings 2-Column Grid ───────────────────────────────────────────
        settings_grid = tk.Frame(settings_card, bg=BG_CARD)
        settings_grid.pack(fill="x")
        settings_grid.columnconfigure(0, weight=1, uniform="settings")
        settings_grid.columnconfigure(1, weight=1, uniform="settings")

        # Cell (0,0): Label Text
        cell_lbl = tk.Frame(settings_grid, bg=BG_CARD)
        cell_lbl.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))

        tk.Label(
            cell_lbl,
            text="PREVIEW CAPTION / LABEL",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=FONT_SMALL,
        ).pack(anchor="w", pady=(0, 3))

        self.label_var = tk.StringVar(value="Scan me!")
        self.label_entry = tk.Entry(
            cell_lbl,
            textvariable=self.label_var,
            font=FONT_BODY,
            relief="flat",
            bg=BG_INPUT,
            fg=TEXT_MAIN,
            insertbackground=TEXT_MAIN,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=BORDER_FOCUS,
        )
        self.label_entry.pack(fill="x", ipady=4)
        self.label_var.trace_add("write", lambda *_: self._update_caption_preview())

        # Cell (0,1): Custom Colors (Foreground & Background)
        cell_colors = tk.Frame(settings_grid, bg=BG_CARD)
        cell_colors.grid(row=0, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))

        color_row = tk.Frame(cell_colors, bg=BG_CARD)
        color_row.pack(fill="x")
        color_row.columnconfigure(0, weight=1, uniform="color")
        color_row.columnconfigure(1, weight=1, uniform="color")

        self.dark_swatch = ModernColorSwatch(
            color_row,
            "Foreground",
            "#000000",
            on_change=self._on_custom_color,
        )
        self.dark_swatch.grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.light_swatch = ModernColorSwatch(
            color_row,
            "Background",
            "#ffffff",
            on_change=self._on_custom_color,
        )
        self.light_swatch.grid(row=0, column=1, sticky="nsew", padx=(5, 0))

        # Cell (1,0): Error Correction Selector
        cell_ec = tk.Frame(settings_grid, bg=BG_CARD)
        cell_ec.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=(0, 12))

        tk.Label(
            cell_ec,
            text="ERROR CORRECTION LEVEL",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=FONT_SMALL,
        ).pack(anchor="w", pady=(0, 4))

        self.ec_var = tk.StringVar(value="M")
        ec_strip = tk.Frame(
            cell_ec,
            bg=BG_INPUT,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            padx=2,
            pady=2,
        )
        ec_strip.pack(fill="x")

        self._ec_btns: dict[str, tk.Label] = {}
        levels = [("L", "7%"), ("M", "15%"), ("Q", "25%"), ("H", "30%")]
        for idx, (code, pct) in enumerate(levels):
            ec_strip.columnconfigure(idx, weight=1)
            btn = tk.Label(
                ec_strip,
                text=f"{code} ({pct})",
                bg=BG_INPUT,
                fg=TEXT_MUTED,
                font=FONT_SMALL,
                cursor="hand2",
                pady=5,
            )
            btn.grid(row=0, column=idx, sticky="nsew", padx=1)
            btn.bind("<Button-1>", lambda _, c=code: self._select_ec(c))
            self._ec_btns[code] = btn
        self._select_ec("M")

        # Cell (1,1): Size Selector
        cell_size = tk.Frame(settings_grid, bg=BG_CARD)
        cell_size.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=(0, 12))

        tk.Label(
            cell_size,
            text="EXPORT RESOLUTION",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=FONT_SMALL,
        ).pack(anchor="w", pady=(0, 4))

        self.size_var = tk.IntVar(value=300)
        size_strip = tk.Frame(
            cell_size,
            bg=BG_INPUT,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            padx=2,
            pady=2,
        )
        size_strip.pack(fill="x")

        self._size_btns: dict[str, tk.Label] = {}
        sizes = [("S", 150), ("M", 300), ("L", 450), ("XL", 600)]
        for idx, (lbl, val) in enumerate(sizes):
            size_strip.columnconfigure(idx, weight=1)
            btn = tk.Label(
                size_strip,
                text=f"{lbl} ({val}px)",
                bg=BG_INPUT,
                fg=TEXT_MUTED,
                font=FONT_SMALL,
                cursor="hand2",
                pady=5,
            )
            btn.grid(row=0, column=idx, sticky="nsew", padx=1)
            btn.bind("<Button-1>", lambda _, v=val, l=lbl: self._select_size(v, l))
            self._size_btns[lbl] = btn
        self._select_size(300, "M")

        # ── Row 3: Optional Center Logo Embed ────────────────────────────────
        logo_frame = tk.Frame(settings_card, bg=BG_CARD)
        logo_frame.pack(fill="x", pady=(4, 0))

        tk.Label(
            logo_frame,
            text="OPTIONAL CENTER LOGO",
            bg=BG_CARD,
            fg=TEXT_MUTED,
            font=FONT_SMALL,
        ).pack(anchor="w", pady=(0, 3))

        logo_controls = tk.Frame(logo_frame, bg=BG_CARD)
        logo_controls.pack(fill="x")

        self.logo_btn = tk.Label(
            logo_controls,
            text="📁 Choose Logo Image…",
            bg=BG_INPUT,
            fg=TEXT_MAIN,
            font=FONT_SMALL,
            cursor="hand2",
            padx=10,
            pady=5,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
        )
        self.logo_btn.pack(side="left")
        self.logo_btn.bind("<Button-1>", lambda _: self._choose_logo())
        self.logo_btn.bind("<Enter>", lambda _: self.logo_btn.configure(bg=BG_HOVER))
        self.logo_btn.bind("<Leave>", lambda _: self.logo_btn.configure(bg=BG_INPUT))

        self.logo_name_lbl = tk.Label(
            logo_controls,
            text="No logo loaded (standard QR)",
            bg=BG_CARD,
            fg=TEXT_DIM,
            font=FONT_SMALL,
        )
        self.logo_name_lbl.pack(side="left", padx=10)

        self.remove_logo_btn = tk.Label(
            logo_controls,
            text="✕ Remove",
            bg=BG_CARD,
            fg=DANGER,
            font=FONT_SMALL,
            cursor="hand2",
            padx=6,
            pady=2,
        )
        self.remove_logo_btn.pack(side="right")
        self.remove_logo_btn.pack_forget()  # hidden until logo loaded
        self.remove_logo_btn.bind("<Button-1>", lambda _: self._remove_logo())

    def _apply_preset(self, dark_c: str, light_c: str, target_btn: tk.Label):
        self.dark_swatch.set_color(dark_c)
        self.light_swatch.set_color(light_c)
        for btn in self._preset_btns:
            btn.configure(bg=BG_INPUT, fg=TEXT_MUTED)
        target_btn.configure(bg=ACCENT, fg="#ffffff")
        self._trigger_live_preview()

    def _on_custom_color(self):
        # Deselect preset buttons when user manually changes custom color
        for btn in self._preset_btns:
            btn.configure(bg=BG_INPUT, fg=TEXT_MUTED)
        self._trigger_live_preview()

    def _choose_logo(self):
        path = filedialog.askopenfilename(
            title="Select Logo Image",
            filetypes=[
                ("Image Files", "*.png;*.jpg;*.jpeg;*.bmp;*.webp;*.ico"),
                ("All Files", "*.*"),
            ],
        )
        if path:
            self._logo_path = path
            fname = os.path.basename(path)
            self.logo_name_lbl.configure(text=f"Loaded: {fname}", fg=ACCENT_GREEN)
            self.remove_logo_btn.pack(side="right")
            self._trigger_live_preview()
            self._set_status(f"Logo loaded: {fname}")

    def _remove_logo(self):
        self._logo_path = None
        self.logo_name_lbl.configure(text="No logo loaded (standard QR)", fg=TEXT_DIM)
        self.remove_logo_btn.pack_forget()
        self._trigger_live_preview()
        self._set_status("Logo removed")

    def _build_right_column(self, parent: tk.Frame):
        """Right Column: Live Preview, Action Buttons, and History Panel."""
        right = tk.Frame(parent, bg=BG_APP, width=380)
        right.pack(side="right", fill="both")
        right.pack_propagate(False)

        # ── Preview & Actions Card ───────────────────────────────────────────
        preview_card = tk.Frame(
            right,
            bg=BG_CARD,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            padx=14,
            pady=12,
        )
        preview_card.pack(fill="x", pady=(0, 10))

        preview_hdr = tk.Frame(preview_card, bg=BG_CARD)
        preview_hdr.pack(fill="x", pady=(0, 8))

        tk.Label(
            preview_hdr,
            text="LIVE PREVIEW",
            bg=BG_CARD,
            fg=TEXT_MAIN,
            font=FONT_HEADING,
        ).pack(side="left")

        live_badge = tk.Label(
            preview_hdr,
            text="● Live Sync",
            bg=BG_CARD,
            fg=ACCENT_GREEN,
            font=FONT_SMALL,
        )
        live_badge.pack(side="right")

        # Centered Canvas Container
        canvas_container = tk.Frame(
            preview_card,
            bg=BG_SURFACE,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            padx=8,
            pady=8,
        )
        canvas_container.pack()

        self.preview_canvas = tk.Canvas(
            canvas_container,
            width=PREVIEW_SIZE,
            height=PREVIEW_SIZE,
            bg=BG_SURFACE,
            highlightthickness=0,
            bd=0,
        )
        self.preview_canvas.pack()
        self._draw_placeholder()

        # Specs pill
        self.preview_specs_lbl = tk.Label(
            preview_card,
            text="300 × 300 px • Level M (15%) • PNG",
            bg=BG_CARD,
            fg=TEXT_DIM,
            font=FONT_SMALL,
        )
        self.preview_specs_lbl.pack(pady=(4, 2))

        # Caption label under preview
        self.preview_label = tk.Label(
            preview_card,
            text="Scan me!",
            bg=BG_CARD,
            fg=TEXT_MAIN,
            font=FONT_BOLD,
            wraplength=340,
        )
        self.preview_label.pack(pady=(2, 10))

        # ── Action Buttons Toolbar ───────────────────────────────────────────
        ModernButton(
            preview_card,
            text="⚡  GENERATE QR CODE  (Ctrl+↵)",
            command=self.generate,
            bg=ACCENT,
            fg="#ffffff",
            hover_bg=ACCENT_HOVER,
            font=FONT_BOLD,
            pady=10,
        ).pack(fill="x", pady=(0, 6))

        sec_row = tk.Frame(preview_card, bg=BG_CARD)
        sec_row.pack(fill="x")
        sec_row.columnconfigure(0, weight=1)
        sec_row.columnconfigure(1, weight=1)

        btn_save = ModernButton(
            sec_row,
            text="💾 Save (Ctrl+S)",
            command=self.save_as,
            bg=BG_HOVER,
            fg=TEXT_MAIN,
            hover_bg="#475569",
            font=FONT_SMALL,
            pady=7,
        )
        btn_save.grid(row=0, column=0, sticky="nsew", padx=(0, 4))

        btn_copy = ModernButton(
            sec_row,
            text="📋 Copy (Ctrl+C)",
            command=self.copy_to_clipboard,
            bg=BG_HOVER,
            fg=TEXT_MAIN,
            hover_bg="#475569",
            font=FONT_SMALL,
            pady=7,
        )
        btn_copy.grid(row=0, column=1, sticky="nsew", padx=(4, 0))

        # ── History Card ─────────────────────────────────────────────────────
        history_card = tk.Frame(
            right,
            bg=BG_CARD,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            padx=4,
            pady=6,
        )
        history_card.pack(fill="both", expand=True)

        self.history_panel = HistoryPanel(
            history_card,
            on_restore=self._restore_history_item,
            bg=BG_CARD,
        )
        self.history_panel.pack(fill="both", expand=True)

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=BG_HEADER, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        self.status_var = tk.StringVar(value="Ready • Press Ctrl+Enter to generate")
        status_lbl = tk.Label(
            bar,
            textvariable=self.status_var,
            bg=BG_HEADER,
            fg=TEXT_MUTED,
            font=FONT_SMALL,
        )
        status_lbl.pack(side="left", padx=14)

        shortcuts_lbl = tk.Label(
            bar,
            text="Ctrl+Enter: Generate  •  Ctrl+S: Save  •  Ctrl+C: Copy",
            bg=BG_HEADER,
            fg=TEXT_DIM,
            font=FONT_SMALL,
        )
        shortcuts_lbl.pack(side="right", padx=14)

    # ── Helpers & State Updaters ─────────────────────────────────────────────

    def _select_ec(self, level: str):
        self.ec_var.set(level)
        for code, btn in self._ec_btns.items():
            if code == level:
                btn.configure(bg=ACCENT, fg="#ffffff")
            else:
                btn.configure(bg=BG_INPUT, fg=TEXT_MUTED)
        self._update_specs_label()
        self._trigger_live_preview()

    def _select_size(self, value: int, label: str):
        self.size_var.set(value)
        for lbl, btn in self._size_btns.items():
            if lbl == label:
                btn.configure(bg=ACCENT, fg="#ffffff")
            else:
                btn.configure(bg=BG_INPUT, fg=TEXT_MUTED)
        self._update_specs_label()
        self._trigger_live_preview()

    def _update_specs_label(self):
        if not hasattr(self, "preview_specs_lbl") or not hasattr(self, "size_var") or not hasattr(self, "ec_var"):
            return
        sz = self.size_var.get()
        ec = self.ec_var.get()
        pct_map = {"L": "7%", "M": "15%", "Q": "25%", "H": "30%"}
        pct = pct_map.get(ec, "15%")
        self.preview_specs_lbl.configure(
            text=f"{sz} × {sz} px • Level {ec} ({pct}) • PNG"
        )

    def _update_caption_preview(self):
        text = self.label_var.get().strip()
        self.preview_label.configure(text=text)

    def _set_status(self, text: str):
        self.status_var.set(text)
        self.root.update_idletasks()

    def _draw_placeholder(self):
        c = self.preview_canvas
        c.delete("all")
        c.configure(bg=BG_SURFACE)
        sq = 18
        positions = [
            (20, 20), (20, 38), (20, 56), (38, 20), (56, 20),
            (38, 56), (56, 38), (56, 56),
            (114, 20), (114, 38), (114, 56), (132, 20), (150, 20),
            (132, 56), (150, 38), (150, 56),
            (20, 114), (20, 132), (20, 150), (38, 114), (56, 114),
            (38, 150), (56, 132), (56, 150),
            (90, 84), (108, 84), (126, 84),
            (84, 102), (102, 102), (120, 102), (138, 102),
        ]
        for x, y in positions:
            c.create_rectangle(x, y, x + sq, y + sq, fill=BORDER_COLOR, outline="")
        c.create_text(
            PREVIEW_SIZE // 2,
            PREVIEW_SIZE - 20,
            text="Enter content to preview",
            fill=TEXT_DIM,
            font=FONT_SMALL,
        )

    # ── Live Preview Debounce ────────────────────────────────────────────────

    def _on_data_change(self, data: str):
        """Called automatically when content inputs update."""
        self._trigger_live_preview()

    def _trigger_live_preview(self):
        """Debounces generation to prevent UI stutter during typing."""
        if self._debounce_job is not None:
            self.root.after_cancel(self._debounce_job)
        self._debounce_job = self.root.after(300, self._run_live_preview)

    def _run_live_preview(self):
        self._debounce_job = None
        try:
            data = self.type_panel.get_data().strip()
            if not data:
                self._draw_placeholder()
                return

            img = generate_qr_image(
                data,
                fill_color=self.dark_swatch.color,
                back_color=self.light_swatch.color,
                box_size=max(2, self.size_var.get() // 100),
                error_correction=self.ec_var.get(),
                logo=self._logo_path,
            )
            self._current_image = img
            self._show_preview(img)
            self._set_status("Live preview synchronized")
        except Exception as e:
            self._set_status(f"Preview error: {e}")

    def _show_preview(self, img: Image.Image):
        display = img.resize((PREVIEW_SIZE, PREVIEW_SIZE), Image.NEAREST)
        self._preview_tk = ImageTk.PhotoImage(display)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(0, 0, anchor="nw", image=self._preview_tk)

    # ── Generation & Export ──────────────────────────────────────────────────

    def generate(self):
        data = self.type_panel.get_data().strip()
        if not data:
            messagebox.showerror("Missing Data", "Please enter content before generating.")
            return

        self._set_status("Generating QR code…")
        try:
            img = generate_qr_image(
                data,
                fill_color=self.dark_swatch.color,
                back_color=self.light_swatch.color,
                box_size=max(2, self.size_var.get() // 100),
                error_correction=self.ec_var.get(),
                logo=self._logo_path,
            )
        except Exception as e:
            messagebox.showerror("Generation Error", str(e))
            self._set_status("Generation failed.")
            return

        self._current_image = img
        self._show_preview(img)

        label_text = self.label_var.get().strip()
        self.preview_label.configure(text=label_text)

        # Save to default file
        filename = generate_qr(
            data,
            fill_color=self.dark_swatch.color,
            back_color=self.light_swatch.color,
            box_size=max(2, self.size_var.get() // 100),
            error_correction=self.ec_var.get(),
            logo=self._logo_path,
        )

        # Record in history panel with snapshot for complete restoration
        self.history_panel.add(
            img=img,
            label=label_text or data[:24],
            data=data,
            settings={
                "dark_color":       self.dark_swatch.color,
                "light_color":      self.light_swatch.color,
                "error_correction": self.ec_var.get(),
                "size":             self.size_var.get(),
                "label":            label_text,
                "snapshot":         self.type_panel.get_snapshot(),
                "tab_index":        self.type_panel.get_active_tab(),
            },
        )

        self._set_status(f"✔ Saved to {filename} • Ctrl+S to export elsewhere")

    def save_as(self):
        if self._current_image is None:
            messagebox.showinfo("No QR Yet", "Please generate a QR code first.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG Image", "*.png"),
                ("JPEG Image", "*.jpg"),
                ("All files", "*.*"),
            ],
            title="Export QR Code",
            initialfile="qr_code.png",
        )
        if path:
            self._current_image.save(path)
            self._set_status(f"✔ Successfully exported to {path}")

    def copy_to_clipboard(self):
        if self._current_image is None:
            messagebox.showinfo("No QR Yet", "Please generate a QR code first.")
            return

        ok = copy_image_to_clipboard(self._current_image)
        if ok:
            self._set_status("✔ QR Code copied to clipboard!")
        else:
            messagebox.showwarning(
                "Clipboard Unavailable",
                "pywin32 is not installed. Run:\n\n  pip install pywin32\n\n"
                "to enable direct clipboard copying.",
            )

    # ── History Restoration ──────────────────────────────────────────────────

    def _restore_history_item(self, item):
        """Restore all parameters and image from a past history entry."""
        s = item.settings
        self.dark_swatch.set_color(s["dark_color"])
        self.light_swatch.set_color(s["light_color"])
        self._select_ec(s["error_correction"])
        self.label_var.set(s.get("label", ""))

        size_map = {150: "S", 300: "M", 450: "L", 600: "XL"}
        lbl = size_map.get(s["size"], "M")
        self._select_size(s["size"], lbl)

        # Restore form fields if snapshot is available
        snapshot = s.get("snapshot")
        if snapshot:
            self.type_panel.restore_snapshot(snapshot)

        self._current_image = item.img
        self._show_preview(item.img)
        self.preview_label.configure(text=item.label)
        self._set_status(f"Restored: {item.label or item.data[:28]}")