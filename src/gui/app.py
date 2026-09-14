"""
src/gui/app.py
QR Brick Builder — LEGO-themed QR generator GUI.
"""
from __future__ import annotations

import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox
from PIL import Image, ImageTk

from core.generator import generate_qr_image, generate_qr
from src.gui.qr_type_panel import QRTypePanel
from src.gui.history import HistoryPanel
from utils.helpers import copy_image_to_clipboard


# ── LEGO color palette ───────────────────────────────────────────────────────
LEGO_RED    = "#d01012"
LEGO_BLUE   = "#0088dd"
LEGO_MID    = "#3377aa"
LEGO_YELLOW = "#ffff00"
LEGO_LIGHT  = "#ebebeb"
LEGO_DARK   = "#1a1a1a"
LEGO_WHITE  = "#ffffff"
LEGO_GREEN  = "#00a650"

FONT_BOLD = ("Arial Black", 10)
FONT_SMALL_BOLD = ("Arial Black", 7)
FONT_MONO = ("Consolas", 10)

PREVIEW_SIZE = 200


# ── Small widgets ────────────────────────────────────────────────────────────

def make_stud(parent, color=LEGO_RED, size=16) -> tk.Canvas:
    """Draw a single LEGO stud (circle with inner highlight ring)."""
    canvas = tk.Canvas(parent, width=size, height=size,
                       bg=parent["bg"], highlightthickness=0)
    pad = 1
    canvas.create_oval(pad, pad, size - pad, size - pad,
                       fill=color, outline="#333333", width=1)
    inner = pad + size * 0.2
    canvas.create_oval(inner, inner, size - inner, size - inner,
                       fill="", outline="#cccccc", width=1)
    return canvas


def stud_row(parent, bg, colors):
    """A horizontal strip of studs."""
    frame = tk.Frame(parent, bg=bg, height=28)
    frame.pack(fill="x")
    frame.pack_propagate(False)
    inner = tk.Frame(frame, bg=bg)
    inner.pack(anchor="w", padx=12, pady=5)
    for c in colors:
        s = make_stud(inner, color=c, size=18)
        s.pack(side="left", padx=5)
    return frame


class BrickButton(tk.Canvas):
    """A button styled as a LEGO brick with stud and press animation."""

    def __init__(self, parent, text, command, bg=LEGO_YELLOW,
                 fg=LEGO_DARK, width=200, height=42, **kwargs):
        super().__init__(parent, width=width, height=height,
                         highlightthickness=0, bg=parent["bg"], **kwargs)
        self._bg = bg
        self._fg = fg
        self._text = text
        self._cmd = command
        self._draw()
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Enter>", lambda e: self._draw(hover=True))
        self.bind("<Leave>", lambda e: self._draw())

    def _shadow_color(self):
        r, g, b = self.winfo_rgb(self._bg)
        r, g, b = r // 256, g // 256, b // 256
        return f"#{max(r-50,0):02x}{max(g-50,0):02x}{max(b-50,0):02x}"

    def _highlight_color(self):
        r, g, b = self.winfo_rgb(self._bg)
        r, g, b = r // 256, g // 256, b // 256
        return f"#{min(r+40,255):02x}{min(g+40,255):02x}{min(b+40,255):02x}"

    def _draw(self, pressed=False, hover=False):
        self.delete("all")
        w, h = int(self["width"]), int(self["height"])
        offset = 0 if pressed else 4
        shadow = self._shadow_color()
        bg = self._highlight_color() if hover else self._bg

        if not pressed:
            self.create_rectangle(0, offset, w, h,
                                  fill=shadow, outline="", width=0)
        y_top = offset if pressed else 0
        self.create_rectangle(0, y_top, w, h - (0 if pressed else offset),
                               fill=bg, outline=LEGO_DARK, width=2)
        sx, sy, sr = w // 2, y_top + 6, 6
        self.create_oval(sx - sr, sy - sr, sx + sr, sy + sr,
                         fill=bg, outline=LEGO_DARK, width=1)
        self.create_oval(sx - sr + 2, sy - sr + 2,
                         sx + sr - 2, sy + sr - 2,
                         fill="", outline="#cccccc", width=1)
        lbl_color = LEGO_DARK if hover else self._fg
        self.create_text(w // 2, y_top + (h - y_top) // 2 + 4,
                         text=self._text, fill=lbl_color,
                         font=("Arial Black", 10, "bold"))

    def _on_press(self, _):
        self._draw(pressed=True)
        if self._cmd:
            self._cmd()

    def _on_release(self, _):
        self._draw()


class ColorSwatch(tk.Frame):
    """A labeled color-picker swatch."""

    def __init__(self, parent, label, initial, on_change=None, **kwargs):
        super().__init__(parent, bg=LEGO_LIGHT, **kwargs)
        self.color = initial
        self._label_text = label
        self._on_change = on_change

        tk.Label(self, text=label.upper(),
                 bg=LEGO_LIGHT, fg=LEGO_MID,
                 font=FONT_SMALL_BOLD).pack(anchor="w")

        self.swatch = tk.Canvas(self, width=70, height=28,
                                cursor="hand2", highlightthickness=2,
                                highlightbackground=LEGO_MID)
        self.swatch.configure(bg=initial)
        self.swatch.pack()
        self.swatch.bind("<Button-1>", self._pick)

    def _pick(self, _):
        result = colorchooser.askcolor(
            color=self.color, title=f"Pick {self._label_text}"
        )
        if result and result[1]:
            self.color = result[1]
            self.swatch.configure(bg=self.color)
            if self._on_change:
                self._on_change()


# ── Main app ─────────────────────────────────────────────────────────────────

class QRApp:

    STUD_COLORS = [LEGO_RED, LEGO_YELLOW, LEGO_BLUE, LEGO_MID,
                   LEGO_RED, LEGO_MID, LEGO_YELLOW, LEGO_RED,
                   LEGO_BLUE, LEGO_YELLOW, LEGO_RED, LEGO_MID,
                   LEGO_YELLOW, LEGO_BLUE]

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("QR Brick Builder")
        self.root.resizable(True, True)
        self.root.minsize(860, 620)
        self.root.configure(bg=LEGO_LIGHT)

        self._current_image: Image.Image | None = None
        self._preview_tk: ImageTk.PhotoImage | None = None
        self._debounce_job = None

        self._build_ui()
        self.root.geometry("980x680")
        self._bind_shortcuts()
        self._schedule_stud_animation()

    # ── Keyboard shortcuts ───────────────────────────────────────────────────

    def _bind_shortcuts(self):
        self.root.bind("<Control-Return>", lambda _: self.generate())
        self.root.bind("<Control-s>",      lambda _: self.save_as())
        self.root.bind("<Control-S>",      lambda _: self.save_as())
        self.root.bind("<Control-c>",      lambda _: self.copy_to_clipboard())

    # ── Stud animation ───────────────────────────────────────────────────────

    def _schedule_stud_animation(self):
        """Cycle the title-bar stud colors every 800 ms."""
        self._stud_offset = 0
        self._animate_studs()

    def _animate_studs(self):
        if not self._stud_canvases:
            return
        cycle = self.STUD_COLORS
        n = len(cycle)
        for i, canvas in enumerate(self._stud_canvases):
            color = cycle[(i + self._stud_offset) % n]
            canvas.itemconfig("oval", fill=color)
        self._stud_offset = (self._stud_offset + 1) % n
        self.root.after(800, self._animate_studs)

    # ── Layout ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_top_bar()
        body = tk.Frame(self.root, bg=LEGO_LIGHT)
        body.pack(fill="both", expand=True)
        self._build_left(body)
        self._build_right(body)
        self._build_status_bar()

    def _build_top_bar(self):
        bar = tk.Frame(self.root, bg=LEGO_RED, height=44)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        row = tk.Frame(bar, bg=LEGO_RED)
        row.pack(fill="x", padx=10)

        self._stud_canvases: list[tk.Canvas] = []
        stud_colors_left  = [LEGO_YELLOW, LEGO_BLUE, LEGO_RED]
        stud_colors_right = [LEGO_BLUE, LEGO_YELLOW, LEGO_RED]

        for color in stud_colors_left:
            c = self._make_animated_stud(row, color)
            c.pack(side="left", pady=10, padx=4)

        tk.Label(row, text="⬛ QR BRICK BUILDER",
                 bg=LEGO_RED, fg=LEGO_WHITE,
                 font=("Arial Black", 13)).pack(side="left", padx=10)

        for color in stud_colors_right:
            c = self._make_animated_stud(row, color)
            c.pack(side="right", pady=10, padx=4)

    def _make_animated_stud(self, parent, color, size=22) -> tk.Canvas:
        """Like make_stud but with a tag so items can be recolored."""
        canvas = tk.Canvas(parent, width=size, height=size,
                           bg=parent["bg"], highlightthickness=0)
        pad = 1
        canvas.create_oval(pad, pad, size - pad, size - pad,
                            fill=color, outline="#333333", width=1, tags="oval")
        inner = pad + size * 0.2
        canvas.create_oval(inner, inner, size - inner, size - inner,
                            fill="", outline="#cccccc", width=1)
        self._stud_canvases.append(canvas)
        return canvas

    def _section(self, parent, text):
        tk.Label(parent, text=text.upper(),
                 bg=parent["bg"], fg=LEGO_MID,
                 font=FONT_SMALL_BOLD).pack(anchor="w", pady=(10, 2))

    def _build_left(self, body):
        left = tk.Frame(body, bg=LEGO_WHITE, padx=18, pady=14, width=370)
        left.pack(side="left", fill="both", expand=True)
        left.pack_propagate(False)

        # QR type panel (tabs + dynamic fields)
        self._section(left, "Content")
        self.type_panel = QRTypePanel(
            left,
            on_change=self._on_data_change,
            bg=LEGO_WHITE,
        )
        self.type_panel.pack(fill="x")

        # Label
        self._section(left, "Label")
        self.label_var = tk.StringVar(value="Scan me!")
        tk.Entry(left, textvariable=self.label_var,
                 font=FONT_MONO, relief="flat",
                 bg=LEGO_LIGHT, fg=LEGO_DARK,
                 insertbackground=LEGO_RED,
                 highlightthickness=2,
                 highlightbackground=LEGO_MID,
                 highlightcolor=LEGO_RED).pack(fill="x")

        # Colors
        self._section(left, "Colors")
        color_row = tk.Frame(left, bg=LEGO_WHITE)
        color_row.pack(fill="x", pady=2)
        self.dark_swatch = ColorSwatch(
            color_row, "dark", LEGO_DARK,
            on_change=self._trigger_live_preview,
        )
        self.light_swatch = ColorSwatch(
            color_row, "light", LEGO_WHITE,
            on_change=self._trigger_live_preview,
        )
        self.dark_swatch.pack(side="left", padx=(0, 8))
        self.light_swatch.pack(side="left")

        # Error correction
        self._section(left, "Error Correction")
        self.ec_var = tk.StringVar(value="M")
        ec_frame = tk.Frame(left, bg=LEGO_WHITE)
        ec_frame.pack(fill="x", pady=2)
        for level in ["L", "M", "Q", "H"]:
            tk.Radiobutton(
                ec_frame, text=level,
                variable=self.ec_var, value=level,
                bg=LEGO_WHITE, fg=LEGO_DARK,
                activebackground=LEGO_LIGHT,
                selectcolor=LEGO_YELLOW,
                font=("Arial Black", 8),
                command=self._trigger_live_preview,
            ).pack(side="left", padx=4)

        # Size
        self._section(left, "Size")
        self.size_var = tk.IntVar(value=300)
        size_frame = tk.Frame(left, bg=LEGO_WHITE)
        size_frame.pack(fill="x", pady=2)
        self._size_btns: dict[str, tk.Button] = {}
        for lbl, val in [("S", 150), ("M", 300), ("L", 450), ("XL", 600)]:
            btn = tk.Button(
                size_frame, text=lbl, width=4,
                relief="raised", bd=3,
                font=("Arial Black", 8),
                bg=LEGO_LIGHT, fg=LEGO_MID,
                activebackground=LEGO_BLUE,
                activeforeground=LEGO_WHITE,
                command=lambda v=val, l=lbl: self._select_size(v, l),
            )
            btn.pack(side="left", padx=3)
            self._size_btns[lbl] = btn
        self._select_size(300, "M")

        # Action buttons
        btn_row = tk.Frame(left, bg=LEGO_WHITE)
        btn_row.pack(pady=(14, 4), anchor="center")

        BrickButton(btn_row, "⚙  GENERATE  (Ctrl+↵)",
                    command=self.generate,
                    bg=LEGO_YELLOW, fg=LEGO_DARK,
                    width=240, height=44).pack(side="left", padx=4)

        BrickButton(btn_row, "💾  SAVE AS  (Ctrl+S)",
                    command=self.save_as,
                    bg=LEGO_BLUE, fg=LEGO_WHITE,
                    width=180, height=44).pack(side="left", padx=4)

        BrickButton(btn_row, "📋  COPY  (Ctrl+C)",
                    command=self.copy_to_clipboard,
                    bg=LEGO_MID, fg=LEGO_WHITE,
                    width=150, height=44).pack(side="left", padx=4)

    def _build_right(self, body):
        right = tk.Frame(body, bg=LEGO_BLUE, padx=10, pady=10, width=260)
        right.pack(side="right", fill="both")
        right.pack_propagate(False)

        # Preview area
        tk.Label(right, text="PREVIEW",
                 bg=LEGO_BLUE, fg=LEGO_WHITE,
                 font=("Arial Black", 8)).pack(pady=(0, 6))

        preview_outer = tk.Frame(right, bg=LEGO_WHITE, padx=8, pady=8)
        preview_outer.pack()

        self.preview_canvas = tk.Canvas(
            preview_outer,
            width=PREVIEW_SIZE, height=PREVIEW_SIZE,
            bg=LEGO_LIGHT, highlightthickness=0,
        )
        self.preview_canvas.pack()
        self._draw_placeholder()

        self.preview_label = tk.Label(
            right, text="",
            bg=LEGO_BLUE, fg=LEGO_WHITE,
            font=("Arial Black", 8),
            wraplength=200,
        )
        self.preview_label.pack(pady=(6, 0))

        # History panel
        tk.Frame(right, bg=LEGO_MID, height=2).pack(fill="x", pady=8)

        self.history_panel = HistoryPanel(
            right,
            on_restore=self._restore_history_item,
            bg=LEGO_BLUE,
        )
        self.history_panel.pack(fill="both", expand=True)

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=LEGO_MID, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)

        # Studs left side
        stud_inner = tk.Frame(bar, bg=LEGO_MID)
        stud_inner.pack(side="left", padx=6, pady=4)
        for color in [LEGO_RED, LEGO_YELLOW, LEGO_BLUE]:
            make_stud(stud_inner, color=color, size=16).pack(side="left", padx=3)

        self.status_var = tk.StringVar(value="Ready to build  •  Ctrl+Enter to generate")
        tk.Label(
            bar, textvariable=self.status_var,
            bg=LEGO_MID, fg=LEGO_YELLOW,
            font=("Arial", 8),
        ).pack(side="left", padx=8)

        tk.Label(
            bar, text="QR BRICK BUILDER v2.0",
            bg=LEGO_MID, fg=LEGO_LIGHT,
            font=("Arial", 7),
        ).pack(side="right", padx=10)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _select_size(self, value: int, label: str):
        self.size_var.set(value)
        for lbl, btn in self._size_btns.items():
            if lbl == label:
                btn.configure(bg=LEGO_RED, fg=LEGO_WHITE, relief="sunken")
            else:
                btn.configure(bg=LEGO_LIGHT, fg=LEGO_MID, relief="raised")
        self._trigger_live_preview()

    def _draw_placeholder(self):
        c = self.preview_canvas
        c.delete("all")
        c.configure(bg=LEGO_LIGHT)
        sq = 18
        positions = [
            (10, 10), (10, 28), (10, 46), (28, 10), (46, 10),
            (28, 46), (46, 28), (46, 46),
            (94, 10), (94, 28), (94, 46), (112, 10), (130, 10),
            (112, 46), (130, 28), (130, 46),
            (10, 94), (10, 112), (10, 130), (28, 94), (46, 94),
            (28, 130), (46, 112), (46, 130),
            (70, 64), (88, 64), (106, 64),
            (64, 82), (82, 82), (100, 82), (118, 82),
        ]
        for x, y in positions:
            c.create_rectangle(x, y, x + sq, y + sq,
                               fill=LEGO_MID, outline="")
        c.create_text(
            PREVIEW_SIZE // 2, PREVIEW_SIZE - 14,
            text="enter content → live preview",
            fill=LEGO_MID, font=("Arial", 7),
        )

    def _set_status(self, text: str):
        self.status_var.set(text)
        self.root.update_idletasks()

    # ── Live preview ─────────────────────────────────────────────────────────

    def _on_data_change(self, data: str):
        """Called by QRTypePanel on every keystroke."""
        self._trigger_live_preview()

    def _trigger_live_preview(self):
        """Debounce live preview — waits 350 ms after last change."""
        if self._debounce_job is not None:
            self.root.after_cancel(self._debounce_job)
        self._debounce_job = self.root.after(350, self._run_live_preview)

    def _run_live_preview(self):
        self._debounce_job = None
        try:
            data = self.type_panel.get_data()
            if not data.strip():
                return
            img = generate_qr_image(
                data,
                fill_color=self.dark_swatch.color,
                back_color=self.light_swatch.color,
                box_size=max(2, self.size_var.get() // 100),
                error_correction=self.ec_var.get(),
            )
            self._current_image = img
            self._show_preview(img)
            self._set_status("Live preview updated")
        except Exception as e:
            self._set_status(f"Preview error: {e}")

    def _show_preview(self, img: Image.Image):
        display = img.resize((PREVIEW_SIZE, PREVIEW_SIZE), Image.NEAREST)
        self._preview_tk = ImageTk.PhotoImage(display)
        self.preview_canvas.delete("all")
        self.preview_canvas.create_image(0, 0, anchor="nw",
                                         image=self._preview_tk)

    # ── Generate & Export ────────────────────────────────────────────────────

    def generate(self):
        data = self.type_panel.get_data().strip()
        if not data:
            messagebox.showerror("Error", "Please enter content first.")
            return

        self._set_status("Generating…")
        try:
            img = generate_qr_image(
                data,
                fill_color=self.dark_swatch.color,
                back_color=self.light_swatch.color,
                box_size=max(2, self.size_var.get() // 100),
                error_correction=self.ec_var.get(),
            )
        except Exception as e:
            messagebox.showerror("Generation Error", str(e))
            self._set_status("Generation failed.")
            return

        self._current_image = img
        self._show_preview(img)

        label_text = self.label_var.get().strip()
        self.preview_label.configure(text=label_text)

        # Save to default path
        filename = generate_qr(
            data,
            fill_color=self.dark_swatch.color,
            back_color=self.light_swatch.color,
            box_size=max(2, self.size_var.get() // 100),
            error_correction=self.ec_var.get(),
        )

        # Add to history
        self.history_panel.add(
            img=img,
            label=label_text or data[:24],
            data=data,
            settings={
                "dark_color":        self.dark_swatch.color,
                "light_color":       self.light_swatch.color,
                "error_correction":  self.ec_var.get(),
                "size":              self.size_var.get(),
                "label":             label_text,
            },
        )

        self._set_status(f"✔ Saved to {filename}  •  Ctrl+S to choose location")

    def save_as(self):
        if self._current_image is None:
            messagebox.showinfo("No QR Yet", "Generate a QR code first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("JPEG Image", "*.jpg"),
                       ("All files", "*.*")],
            title="Save QR Code As",
            initialfile="qr_code.png",
        )
        if path:
            self._current_image.save(path)
            self._set_status(f"✔ Saved to {path}")

    def copy_to_clipboard(self):
        if self._current_image is None:
            messagebox.showinfo("No QR Yet", "Generate a QR code first.")
            return
        ok = copy_image_to_clipboard(self._current_image)
        if ok:
            self._set_status("✔ Image copied to clipboard!")
        else:
            messagebox.showwarning(
                "Clipboard Unavailable",
                "pywin32 is not installed. Run:\n\n  pip install pywin32\n\n"
                "to enable clipboard copy.",
            )

    # ── History restore ──────────────────────────────────────────────────────

    def _restore_history_item(self, item):
        """Re-load settings from a history entry."""
        s = item.settings
        self.dark_swatch.color = s["dark_color"]
        self.dark_swatch.swatch.configure(bg=s["dark_color"])
        self.light_swatch.color = s["light_color"]
        self.light_swatch.swatch.configure(bg=s["light_color"])
        self.ec_var.set(s["error_correction"])
        self.label_var.set(s["label"])
        # restore size button highlight
        size_map = {150: "S", 300: "M", 450: "L", 600: "XL"}
        lbl = size_map.get(s["size"], "M")
        self._select_size(s["size"], lbl)
        # show the image
        self._current_image = item.img
        self._show_preview(item.img)
        self.preview_label.configure(text=item.label)
        self._set_status(f"Restored: {item.label or item.data[:30]}")