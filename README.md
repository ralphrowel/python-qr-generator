# ⚡ QR Studio — Modern QR Code Generator

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![UI Framework](https://img.shields.io/badge/UI-Tkinter%20%7C%20Pillow-indigo.svg)](https://docs.python.org/3/library/tkinter.html)
[![Tests](https://img.shields.io/badge/Tests-11%20Passed-10b981.svg)](tests/)
[![License](https://img.shields.io/badge/License-MIT-slate.svg)](#license)

**QR Studio** is a modern, high-performance desktop application designed for generating, styling, and customizing professional QR codes. Built with Python, Tkinter, and Pillow, it features a sleek dark-slate design system, real-time debounced previewing, 1-click color presets, center logo embedding, and an interactive history panel.

---

## 📸 Overview & Highlights

- **Modern Dark Slate Aesthetic**: Curated Electric Indigo and Slate UI theme (`#0b0f19`, `#1e293b`, `#334155`, `#6366f1`) with smooth hover micro-interactions.
- **⚡ Live Debounced Preview**: Real-time rendering as you type with zero UI lag or freezing.
- **🎨 1-Click Color Presets**: Switch instantly between curated palettes or pick custom foreground and background hex colors.
- **🖼️ Center Logo Embedding**: Upload any custom logo (PNG, JPG, ICO, WebP) with automated error correction adjustment (`H`/`Q`) and protective boundary masking.
- **🗂️ Interactive Session History**: Visual recent-history cards with thumbnail previews, content-type badges, spec pills, individual deletion, and 1-click restoration of all parameters.
- **⌨️ Keyboard Shortcuts**: Fast workflow via `Ctrl+Enter` (Generate), `Ctrl+S` (Save), and `Ctrl+C` (Copy).
- **📱 6 Content Types Supported**: Dedicated, tailored input forms for URLs, WiFi networks, digital business cards (vCard), emails, SMS, and notes.

---

## ✨ Features

### 1. Supported QR Content Types
| Type | Icon | Supported Fields & Features |
| :--- | :---: | :--- |
| **Website URL** | 🔗 | Web address sanitization with a 1-click `📋 Paste` clipboard button. |
| **WiFi Network** | 📶 | Network SSID, Password with `👁`/`🙈` visibility toggle, Security selector (`WPA`, `WEP`, `None`), and Hidden SSID option. |
| **Digital Contact** | 📇 | vCard 3.0 standard format supporting Full Name, Phone Number, Email, Website, Company / Organization, and Job Title. |
| **Email Message** | 📧 | Standard `mailto:` protocol supporting Recipient Email, Subject line, and pre-formatted Message Body. |
| **SMS Message** | 💬 | `SMSTO:` protocol supporting Destination Phone Number and pre-filled Message text. |
| **Plain Text** | 📝 | Multi-line raw text, memos, and notes with a real-time character counter badge. |

### 2. Design & Encoding Customization
- **Quick Palette Presets**:
  - **Classic**: High-contrast Black (`#000000`) on White (`#ffffff`)
  - **Slate**: Navy Slate (`#0f172a`) on Soft Cloud (`#f8fafc`)
  - **Indigo**: Royal Indigo (`#4338ca`) on Soft Ice (`#eef2ff`)
  - **Emerald**: Forest Emerald (`#065f46`) on Mint (`#ecfdf5`)
  - **Cyan**: Vivid Neon Cyan (`#06b6d4`) on Dark Slate (`#0b0f19`)
  - **Sunset**: Berry Crimson (`#9f1239`) on Blush (`#fff1f2`)
- **Custom Color Swatches**: Interactive color pickers with real-time uppercase hex indicators.
- **Error Correction Levels**:
  - `L` — ~7% data recovery
  - `M` — ~15% data recovery *(Default)*
  - `Q` — ~25% data recovery
  - `H` — ~30% data recovery *(Auto-applied when logos are embedded)*
- **Export Resolution**: `S` (150px), `M` (300px), `L` (450px), and `XL` (600px).
- **Custom Label / Caption**: Dynamic label rendered below the QR preview and saved with exported files.

### 3. Session History & Restoration
- Maintains a visual session history of recently generated QR codes.
- Displays metadata including content icon, timestamp, label, data snippet, and resolution/error correction pills.
- **Individual Deletion**: Remove unwanted items with a single click on `✕`.
- **Full Snapshot Restoration**: Clicking a history entry restores not only the colors and size, but also the active tab and its exact form inputs.

---

## 🏗️ Project Architecture

```
qr-generator/
│
├── core/
│   └── generator.py         # QR code generation engine & logo overlay compositing
│
├── src/
│   └── gui/
│       ├── app.py           # Main application controller, UI layout, & state management
│       ├── qr_type_panel.py # Segmented tab strip & input forms for all 6 content types
│       └── history.py       # Scrollable session history panel with interactive cards
│
├── utils/
│   └── helpers.py           # String formatters (vCard, WiFi, mailto, SMS) & clipboard utility
│
├── tests/
│   └── test_gui.py          # Unit tests covering core logic, formatting, and UI features
│
├── requirements.txt         # Python package dependencies
├── main.py                  # Application entry point
└── README.md                # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10** or higher installed on your system.
- *(Windows recommended for direct clipboard copying via `pywin32`).*

### Installation

1. **Clone or navigate to the repository**:
   ```bash
   git clone https://github.com/ralphrowel/python-qr-generator.git
   cd python-qr-generator
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # macOS / Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🖥️ Running the Application

Launch the desktop application using:
```bash
python main.py
```

### Keyboard Shortcuts
| Shortcut | Action |
| :--- | :--- |
| `Ctrl + Enter` | Generate QR Code and add to session history |
| `Ctrl + S` | Export QR Code as PNG or JPEG image |
| `Ctrl + C` | Copy generated QR image directly to clipboard |

---

## 🧪 Running Automated Tests

A comprehensive unit test suite is included in `tests/test_gui.py`:

```bash
# Run all tests
python -m unittest discover tests
```

### Tested Capabilities
- [x] URL sanitization and formatting
- [x] WiFi QR string encoding (WPA, WEP, None, hidden SSID)
- [x] vCard 3.0 formatting with organization and job title support
- [x] Raw image generation and dimension validation
- [x] Center logo compositing and error correction auto-upgrade
- [x] UI tab switching without clipping
- [x] Color preset selection and swatch synchronization
- [x] Generation workflow and history logging
- [x] Individual history card deletion
- [x] Complete form snapshot roundtrip and restoration

---

## 📦 Dependencies

| Package | Purpose |
| :--- | :--- |
| [`qrcode[pil]`](https://pypi.org/project/qrcode/) | QR code matrix generation engine |
| [`Pillow`](https://pypi.org/project/pillow/) | Image processing, resizing, color mapping, and logo overlay |
| [`pywin32`](https://pypi.org/project/pywin32/) | Direct Windows clipboard integration (`CF_DIB` image format) |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
