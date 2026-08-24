# MCS CVOR Remote Management System

**South African Air Force (SAAF) CVOR Network Remote Monitoring & Control**

![SAAF](https://img.shields.io/badge/SAAF-CVOR%20Network-0a2158?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-Windows%2011%20%7C%20Ubuntu%2022.04+-lightgrey?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## Overview

The **MCS CVOR Remote Management System** is a comprehensive desktop application for remotely monitoring and controlling all SAAF CVOR (Conventional VHF Omni-directional Range) navigation aid systems based on the **Thales ATM** architecture. The system provides real-time status monitoring, remote parameter configuration, shelter layout management, and full audit trails across all South African Air Force bases.

---

## Features

- 🗺 **Interactive Map** — Folium-powered map of South Africa with all CVOR installations, colour-coded by operational status
- 📡 **Real-time Status Polling** — Automatic 30-second polling of all CVOR systems via Thales TCP/IP protocol
- 🏠 **Base Management** — Add, delete, and split Air Force bases with full audit history
- ⚙️ **Remote Settings** — Set frequency, power, Morse ID, and standby mode remotely over TCP/IP
- 🔄 **Soft Reset** — Remote system reset capability for each CVOR unit
- 🔍 **Auto NIC Detection** — Automatically detects local network interfaces (IP/subnet/gateway) using psutil
- 💾 **Persistent Database** — SQLAlchemy/SQLite database stores all configuration, status history, and shelter layouts
- 📁 **Config File Import** — Import `.ini`, `.sys`, and `.LDA` (Thales LDA format) configuration files
- 🏗 **Shelter Layout Editor** — Full interactive floor-plan editor with drag-and-drop equipment placement
- 📄 **PDF Export** — A3 landscape shelter layout export with SAAF title block and equipment inventory table
- 🖼 **SVG Export** — Vector shelter layout export
- 📦 **Bulk Export** — Export all base data, settings history, and config files as a timestamped ZIP archive
- 📋 **Audit Log** — Complete settings change history with timestamps for each CVOR system
- 🔐 **Alarm Display** — 16-bit alarm word decoding with named alarm descriptions
- 🏷 **Status Badges** — Colour-coded status indicators: ACTIVE (green), INACTIVE (grey), FAULT (red), STANDBY (amber), MAINTENANCE (blue)
- 🔧 **Equipment Palette** — 15-item equipment palette for shelter floor-plan construction
- 📐 **Snap-to-Grid** — 20px grid snapping for precise equipment placement
- ↕️ **Z-Order Control** — Bring forward / send backward for overlapping equipment items
- 🔁 **Rotation & Resize** — Context-menu rotate 90° and resize (wider/narrower/taller/shorter)
- 📊 **CSV & JSON Export** — All base and CVOR data exported in structured CSV and JSON formats
- 🛠 **PyInstaller Build** — Single-file EXE (Windows) and AppImage (Linux) via GitHub Actions

---

## Requirements

| Requirement | Minimum |
|---|---|
| Python | 3.11+ |
| Operating System | Windows 11 or Ubuntu 22.04+ |
| RAM | 4 GB |
| Network | TCP/IP access to CVOR systems (port 5000 default) |
| Display | 1280×800 or higher |

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/schalkpieterse76-afk/MCS.git
cd MCS
```

### 2. Install dependencies

**Linux / macOS:**
```bash
chmod +x install.sh
./install.sh
```

**Windows:**
```bat
install.bat
```

### 3. Run the application

**Linux / macOS:**
```bash
./run.sh
```

**Windows:**
```bat
run.bat
```

Or directly:
```bash
python mcs_cvor/main.py
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                   MCS CVOR Remote Management System              │
├─────────────────┬───────────────────────┬───────────────────────┤
│   UI Layer      │   Business Logic       │   Data Layer          │
│  (PyQt6)        │                        │                       │
│                 │  ┌─────────────────┐   │  ┌─────────────────┐ │
│  ┌───────────┐  │  │  PollWorker     │   │  │  SQLAlchemy     │ │
│  │MainWindow │──┼─▶│  (QThread)      │   │  │  SQLite DB      │ │
│  └───────────┘  │  └────────┬────────┘   │  │  ~/.mcs_cvor/   │ │
│  ┌───────────┐  │           │            │  └─────────────────┘ │
│  │ MapView   │  │  ┌────────▼────────┐   │                       │
│  │(folium)   │  │  │ CVORTCPClient   │   │  ┌─────────────────┐ │
│  └───────────┘  │  │ (asyncio TCP)   │──▶│  │  DBManager      │ │
│  ┌───────────┐  │  └─────────────────┘   │  │  (CRUD ops)     │ │
│  │ CVORDetail│  │                        │  └─────────────────┘ │
│  │ (5 tabs)  │  │  ┌─────────────────┐   │                       │
│  └───────────┘  │  │ Config Parsers  │   │  ┌─────────────────┐ │
│  ┌───────────┐  │  │ .ini/.sys/.LDA  │   │  │ ExportManager   │ │
│  │ Shelter   │  │  └─────────────────┘   │  │ (ZIP/CSV/JSON)  │ │
│  │ Editor    │  │                        │  └─────────────────┘ │
│  └───────────┘  │  ┌─────────────────┐   │                       │
│                 │  │ NetworkDetect   │   │                       │
│                 │  │ (psutil NICs)   │   │                       │
│                 │  └─────────────────┘   │                       │
└─────────────────┴───────────────────────┴───────────────────────┘
```

---

## SAAF Bases

| Base | Code | Location | Latitude | Longitude | Freq (MHz) | Morse |
|---|---|---|---|---|---|---|
| AFB Waterkloof | AFB_WAT | Pretoria | -25.83 | 28.22 | 113.8 | WAT |
| AFB Hoedspruit | AFB_HOE | Hoedspruit | -24.37 | 31.05 | 115.2 | HOE |
| AFB Langebaanweg | AFB_LBW | Langebaanweg | -32.97 | 18.16 | 114.5 | LBW |
| AFB Overberg | AFB_OVB | Overberg | -34.55 | 20.50 | 112.3 | OVB |
| AFB Ysterplaat | AFB_YST | Cape Town | -33.90 | 18.50 | 116.0 | YST |
| AFB Makhado | AFB_MAK | Makhado | -23.16 | 29.70 | 117.5 | MAK |
| AFB Bloemspruit | AFB_BLO | Bloemfontein | -29.09 | 26.30 | 111.8 | BLO |
| AFB Port Elizabeth | AFB_PLZ | Port Elizabeth | -33.98 | 25.62 | 109.6 | PLZ |
| AFB Swartkop | AFB_SWK | Centurion | -25.81 | 28.16 | 110.2 | SWK |
| AFB Durban | AFB_DUR | Durban | -29.97 | 30.95 | 108.4 | DUR |

---

## Config File Import

The system supports three config file formats used by Thales CVOR systems:

### `.ini` — Standard INI format
```ini
[CVOR]
FREQ=113.8
MORSE=WAT
POWER=50
```

### `.sys` — KEY=VALUE with optional sections
```
[NETWORK]
IP=192.168.10.100
MASK=255.255.255.0
GATEWAY=192.168.10.1

[CVOR]
FREQ=113.8
```

### `.LDA` — Thales LDA format (TAG:length:value)
```
FREQ:5:113.8
MORSE:3:WAT
STATUS:6:ACTIVE
MODEL:12:Thales CVOR432
```

To import: select a CVOR system in the tree → CVOR Control tab → Config Files tab → Import Config File.

---

## Database

The database is stored at:
- **Linux/macOS:** `~/.mcs_cvor/mcs_cvor.db`
- **Windows:** `%USERPROFILE%\.mcs_cvor\mcs_cvor.db`

Logs are stored at:
- **Linux/macOS:** `~/.mcs_cvor/logs/mcs_cvor.log`
- **Windows:** `%USERPROFILE%\.mcs_cvor\logs\mcs_cvor.log`

### Database Models

| Model | Description |
|---|---|
| `AirForceBase` | SAAF base record (name, code, location, coordinates) |
| `CVORSystem` | CVOR equipment per base (IP, port, freq, status) |
| `ShelterLayout` | Shelter floor-plan JSON per base |
| `CVORConfigFile` | Imported config files per CVOR system |
| `SettingsHistory` | Audit log of all parameter changes |
| `BaseSplit` | Records base split operations |

---

## Building

### Windows EXE
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name MCS_CVOR \
  --hidden-import PyQt6.QtWebEngineWidgets \
  --hidden-import PyQt6.QtWebEngineCore \
  --hidden-import sqlalchemy.dialects.sqlite \
  mcs_cvor/main.py
# Output: dist/MCS_CVOR.exe
```

### Linux AppImage
Triggered automatically via GitHub Actions on version tags (`v*`).
See `.github/workflows/build-linux.yml`.

### GitHub Actions (automated)
- **CI:** Runs lint + tests on every push/PR to `main`
- **Windows build:** Triggers on `v*` tags → uploads `MCS_CVOR.exe` to GitHub Release
- **Linux build:** Triggers on `v*` tags → uploads `MCS_CVOR-x86_64.AppImage` to GitHub Release

---

## Running Tests

```bash
pip install pytest SQLAlchemy psutil folium
pytest tests/ -v
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## Licence

MIT License — Copyright (c) 2024 MCS / SAAF

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED.

---

*MCS CVOR Remote Management System — Built for the South African Air Force*
