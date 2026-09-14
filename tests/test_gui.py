"""
tests/test_gui.py
Automated tests for QR Generator GUI components and logic.
"""
import os
import sys
import unittest
from unittest.mock import patch
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tkinter as tk
from core.generator import generate_qr_image, generate_qr
from utils.helpers import format_url, format_wifi, format_vcard, format_email, format_sms
from src.gui.app import QRApp, COLOR_PRESETS


class TestQRCoreAndHelpers(unittest.TestCase):

    def test_url_formatting(self):
        self.assertEqual(format_url("example.com"), "https://example.com")
        self.assertEqual(format_url("https://test.org"), "https://test.org")

    def test_wifi_formatting(self):
        res = format_wifi("HomeNet", "secret123", "WPA", False)
        self.assertEqual(res, "WIFI:T:WPA;S:HomeNet;P:secret123;H:false;;")

    def test_vcard_formatting(self):
        res = format_vcard("Jane Doe", "+123456", "jane@doe.com", "https://jane.me")
        self.assertIn("BEGIN:VCARD", res)
        self.assertIn("FN:Jane Doe", res)
        self.assertIn("TEL:+123456", res)
        self.assertIn("END:VCARD", res)

    def test_vcard_formatting_with_org_and_title(self):
        res = format_vcard(
            name="Jane Doe",
            phone="+123456",
            email="jane@doe.com",
            website="https://jane.me",
            org="Acme Corp",
            title="Lead Architect",
        )
        self.assertIn("ORG:Acme Corp", res)
        self.assertIn("TITLE:Lead Architect", res)

    def test_image_generation(self):
        img = generate_qr_image("Hello World", box_size=3)
        self.assertIsNotNone(img)
        self.assertGreater(img.size[0], 50)

    def test_image_generation_with_logo(self):
        dummy_logo = Image.new("RGBA", (32, 32), color=(255, 0, 0, 255))
        img = generate_qr_image("https://example.com", box_size=4, logo=dummy_logo)
        self.assertIsNotNone(img)
        self.assertGreater(img.size[0], 80)


class TestQRAppLayout(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.app = QRApp(self.root)
        self.root.update()

    def tearDown(self):
        self.app._on_close()

    def test_all_tabs_visible_and_unclipped(self):
        """Ensure preview canvas and action buttons remain visible across all tabs."""
        for i in range(6):
            self.app.type_panel._select_tab(i)
            self.root.update()
            self.assertTrue(self.app.preview_canvas.winfo_ismapped())
            self.assertTrue(self.app.history_panel.winfo_ismapped())

    def test_color_preset_applied(self):
        """Ensure selecting a color preset correctly updates the swatches."""
        name, dark_c, light_c = COLOR_PRESETS[2]  # Indigo preset
        self.app._apply_preset(dark_c, light_c, self.app._preset_btns[2])
        self.root.update()
        self.assertEqual(self.app.dark_swatch.color, dark_c)
        self.assertEqual(self.app.light_swatch.color, light_c)

    def test_generation_and_history(self):
        self.app.type_panel._select_tab(0)
        self.root.update()

        with patch("tkinter.messagebox.showerror"), patch("tkinter.messagebox.showinfo"):
            self.app.generate()
            self.root.update()
            self.assertEqual(len(self.app.history_panel._items), 1)
            self.assertIsNotNone(self.app._current_image)

            # Test history item restoration
            item = self.app.history_panel._items[0]
            self.app._restore_history_item(item)
            self.root.update()
            self.assertIn("Restored", self.app.status_var.get())

    def test_history_individual_removal(self):
        with patch("tkinter.messagebox.showerror"), patch("tkinter.messagebox.showinfo"):
            self.app.generate()
            self.root.update()
            self.assertEqual(len(self.app.history_panel._items), 1)
            item = self.app.history_panel._items[0]
            self.app.history_panel.remove(item)
            self.root.update()
            self.assertEqual(len(self.app.history_panel._items), 0)

    def test_snapshot_roundtrip(self):
        # Select Contact tab and set details
        self.app.type_panel._select_tab(2)
        self.app.type_panel._vc_name.set("Alice Test")
        self.app.type_panel._vc_org.set("Test Labs")
        snap = self.app.type_panel.get_snapshot()
        self.assertEqual(snap["tab_index"], 2)
        self.assertEqual(snap["vc_name"], "Alice Test")
        self.assertEqual(snap["vc_org"], "Test Labs")

        # Switch to plain text tab
        self.app.type_panel._select_tab(5)
        self.assertEqual(self.app.type_panel.get_active_tab(), 5)

        # Restore previous snapshot
        self.app.type_panel.restore_snapshot(snap)
        self.assertEqual(self.app.type_panel.get_active_tab(), 2)
        self.assertEqual(self.app.type_panel._vc_name.get(), "Alice Test")
        self.assertEqual(self.app.type_panel._vc_org.get(), "Test Labs")


if __name__ == "__main__":
    unittest.main()
