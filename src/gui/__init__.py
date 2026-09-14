class QRApp:

    def __init__(self, root):
        self.root = root
        self.root.title("QR Brick Builder")

        self.root.geometry("700x550")
        self.root.resizable(False, False)

        self.root.configure(bg=LEGO_LIGHT)

        self._build_ui()