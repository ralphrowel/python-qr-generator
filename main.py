import tkinter as tk
from src.gui.app import QRApp

if __name__ == "__main__":
    root = tk.Tk()
    app = QRApp(root)
    root.mainloop()