# QR Code Generator

A simple desktop application built with Python and Tkinter that generates QR codes from text or URLs.

## Features

- Clean GUI for entering text or URLs
- Generates QR code images using the `qrcode` library
- Saves output as PNG files

## Requirements

- Python 3.x
- `qrcode[pil]` library

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Enter text or a URL in the input field and click **Generate QR**. The QR code is saved as `qr_code.png` in the project directory.

## Project Structure

```
├── main.py              # Entry point
├── core/
│   └── generator.py     # QR code generation logic
├── src/
│   └── gui/
│       └── app.py       # Tkinter GUI
├── utils/
│   └── helpers.py       # Utility functions
├── requirements.txt
└── README.md
```
