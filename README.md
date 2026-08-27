# 🔐 Kvaults

A local, encrypted password manager built with Python and Tkinter. Your passwords never leave your machine.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python) ![License](https://img.shields.io/badge/License-MIT-green)

## Features

- **AES-256 encryption** — passwords encrypted with Fernet (PBKDF2 + SHA-256, 480,000 iterations)
- **Two-factor authentication** — TOTP-based 2FA with QR code setup
- **Password generator** — cryptographically secure, configurable length (12–32 chars)
- **Strength meter** — real-time password strength feedback
- **Security report** — vault-wide health overview: weak & reused password detection
- **Auto-lock** — locks after 5 minutes of inactivity
- **Backup & restore** — export/import your vault as a `.db` file
- **Clipboard safety** — copied passwords auto-clear after 30 seconds
- **Dark UI** — clean, modern dark theme built with Tkinter
- **Brand logos** — saved services use cached logos from the public SVGL API, with offline monogram fallbacks

## Screenshots

> _Add screenshots here_

## Installation

**Requirements:** Python 3.10+

```bash
git clone https://github.com/yourusername/kvaults.git
cd kvaults
pip install -r requirements.txt
python vault.py
```

### Dependencies

```
cryptography>=41.0.0
pyotp>=2.9.0
qrcode[pil]>=7.4.2
Pillow>=10.0.0
CairoSVG>=2.7.0
```

## Usage

1. Launch the app — enter a master password to create or unlock your vault
2. Add entries with site name, username, password, URL, and notes
3. Use the sidebar to copy, reveal, edit, delete, backup, or run a security report
4. Optionally enable 2FA via **Setup 2FA** in the sidebar

## Security

| Layer | Detail |
|---|---|
| Encryption | Fernet (AES-128-CBC + HMAC-SHA256) |
| Key derivation | PBKDF2-HMAC-SHA256, 480,000 iterations |
| Storage | Local SQLite (`vault.db`) — never synced |
| 2FA | TOTP (RFC 6238) via `pyotp` |
| Clipboard | Auto-cleared after 30 seconds |

> ⚠️ Your master password is never stored. If you lose it, your vault cannot be recovered.

## File Structure

```
kvaults/
├── vault.py        # UI & app logic
├── storage.py      # SQLite read/write
├── crypto.py       # Key derivation
├── requirements.txt
└── vault.db        # Created on first run (gitignored)
```

## License

All rights reserved. This project is not open source and may not be copied, modified, or distributed without permission.
