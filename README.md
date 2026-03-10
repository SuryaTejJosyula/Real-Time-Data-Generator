# Fabric Real-Time Data Generator

Stream synthetic real-time data to **Microsoft Fabric Eventstream** — no data engineering experience needed. Select an industry, pick a use case, enter your Eventstream connection string, and watch events flow.

![Login screen with Microsoft RTI icon]

---

## Option A — Download the pre-built app (Windows)

1. Go to the [Releases](../../releases) page of this repository.
2. Download **`FabricRTDG.exe`** from the latest release.
3. Double-click it — no Python, no installation required.

> Windows SmartScreen may show a warning the first time because the .exe is unsigned.  
> Click **"More info" → "Run anyway"** to proceed.

---

## Option B — Run from source

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10 or newer |
| pip | bundled with Python |

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/<your-org>/fabric-rtdg.git
cd fabric-rtdg

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the app
python main.py
```

---

## Option C — Build the .exe yourself

```bash
# 1. Clone + install requirements (same as Option B above)

# 2. Double-click build.bat  — OR run in a terminal:
build.bat
```

The script will:
- Verify Python is on your PATH
- Install PyInstaller if missing
- Bundle everything into **`dist\FabricRTDG.exe`** (single file, ~60 MB)

---

## Using the app

1. **Sign in** with your Microsoft 365 / Fabric account (MSAL interactive login).
2. **Select an industry** — Retail, Healthcare, Finance, Manufacturing, Transportation, Energy, Telecom, or Smart City.
3. **Pick a use case** — each has a description and sample schema (click **Details**).
4. **Enter your Eventstream endpoint** in the connection bar at the top of any page:
   - *Connection string* — copy from your Fabric Eventstream custom endpoint
   - *Event Hub / entity name* — the entity name shown in the Eventstream UI
5. Click **Connect**, then **Start** to begin streaming.

---

## Getting an Eventstream connection string

1. Open [Microsoft Fabric](https://app.fabric.microsoft.com).
2. Navigate to your workspace → **Real-Time Intelligence** → **Eventstream**.
3. Add a **Custom endpoint** as source.
4. Copy the **Connection string (primary key)** and the **Entity name**.

---

## Project structure

```
fabric-rtdg/
├── main.py                   # Entry point
├── config.py                 # App constants (client id, scopes, defaults)
├── requirements.txt
├── build.bat                 # Windows build script (produces .exe)
├── fabric_rtdg.spec          # PyInstaller spec
├── assets/
│   ├── icons/
│   │   └── real_time_intelligence_icon.svg
│   └── styles/
│       └── dark_theme.qss
├── core/
│   ├── auth.py               # MSAL login
│   ├── eventhub_client.py    # Azure Event Hub sender
│   ├── stream_worker.py      # Background streaming thread
│   └── generators/           # 8 industry data generators
│       ├── retail.py
│       ├── healthcare.py
│       ├── finance.py
│       ├── manufacturing.py
│       ├── transportation.py
│       ├── energy.py
│       ├── telecom.py
│       └── smart_city.py
└── ui/
    ├── main_window.py
    ├── login_page.py
    ├── industry_page.py
    ├── use_cases_page.py
    ├── streaming_page.py
    └── components/
        ├── bounce_button.py
        ├── conn_bar.py
        └── log_display.py
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `PyQt6` | Desktop UI framework |
| `qtawesome` | Font Awesome icons |
| `azure-eventhub` | Send events to Fabric Eventstream |
| `msal` | Microsoft Entra ID (AAD) login |
| `faker` | Synthetic data generation |
| `python-dotenv` | Optional local env overrides |

---

## License

MIT — see [LICENSE](LICENSE).
