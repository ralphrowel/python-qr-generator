import tkinter as tk
from tkinter import messagebox
from core.generator import generate_qr


class QRApp:

    def __init__(self, root):
        self.root = root
        self.root.title("QR Generator")
        self.root.geometry("500x300")

        self.main_frame = tk.Frame(root, padx=20, pady=20)
        self.main_frame.pack(fill="both", expand=True)

        self.label = tk.Label(
            self.main_frame,
            text="Enter Text or URL:"
        )
        self.label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        self.entry = tk.Entry(
            self.main_frame,
            width=40
        )
        self.entry.grid(row=1, column=0, padx=5, pady=5)

        self.button = tk.Button(
            self.main_frame,
            text="Generate QR",
            command=self.generate
        )
        self.button.grid(row=2, column=0, pady=15)

    def generate(self):
        source = self.entry.get().strip()

        if not source:
            messagebox.showerror(
                "Error",
                "Please enter text or a URL."
            )
            return

        filename = generate_qr(source)

        messagebox.showinfo(
            "Success",
            f"QR code saved as {filename}"
        )