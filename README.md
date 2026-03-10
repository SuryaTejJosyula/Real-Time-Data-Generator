# Fabric Real-Time Data Generator

Stream synthetic real-time data to **Microsoft Fabric Eventstream** — no data engineering experience needed. Select an industry, pick a use case, enter your Eventstream connection string, and watch events flow.

![Fabric Real-Time Data Generator UI](RTDG.png)

---

## Option A — Download and run (Windows)

1. Go to the [Releases](../../releases) page of this repository.
2. Download **`FabricRTDG.zip`** from the latest release and extract it anywhere.
3. Install **[Python 3.10+](https://www.python.org/downloads/)** if you don't have it — tick **"Add Python to PATH"** during setup.
4. Double-click **`run.bat`** inside the extracted folder.

`run.bat` creates a local virtual environment, installs all dependencies automatically, and launches the app. Subsequent runs skip the install step and start instantly.

> **How are releases published?**  
> A GitHub Actions workflow ([`.github/workflows/release.yml`](.github/workflows/release.yml)) packages the source and uploads `FabricRTDG.zip` automatically when a version tag (e.g. `v1.0.0`) is pushed.

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

The script will:
- Verify Python is on your PATH
- Install PyInstaller if missing
- Bundle everything into **`dist\FabricRTDG.exe`** (single file, ~60 MB)

---

## Using the app

1. **Select an industry** — Retail, Healthcare, Finance, Manufacturing, Transportation, Energy, Telecom, Smart City, or Information Technology.
2. **Pick a use case** — each has a description and sample schema (click **Details**).
3. **Enter your Eventstream endpoint** in the connection bar at the top of the streaming page:
   - *Connection string* — copy from your Fabric Eventstream custom endpoint
   - *Event Hub / entity name* — the entity name shown in the Eventstream UI
4. Click **Connect**, then **Start** to begin streaming.
5. Adjust the **Stream Rate** (10 / 100 / 500 / 1 000 events/sec) at any time.
6. Open the **Dashboard** to monitor all active streams side-by-side.

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
├── config.py                 # App constants and defaults
├── requirements.txt
├── build.bat                 # Windows build script (produces .exe)
├── fabric_rtdg.spec          # PyInstaller spec
├── .github/
│   └── workflows/
│       └── release.yml       # Auto-builds .exe and publishes GitHub Release on tag push
├── assets/
│   ├── icons/
│   └── styles/
│       └── dark_theme.qss
├── core/
│   ├── eventhub_client.py    # Azure Event Hub sender
│   ├── stream_worker.py      # Background streaming thread
│   └── generators/           # 9 industry data generators
│       ├── retail.py
│       ├── healthcare.py
│       ├── finance.py
│       ├── manufacturing.py
│       ├── transportation.py
│       ├── energy.py
│       ├── telecom.py
│       ├── smart_city.py
│       └── information_technology.py
└── ui/
    ├── main_window.py
    ├── industry_page.py
    ├── use_cases_page.py
    ├── streaming_page.py
    ├── sidebar.py
    ├── dashboard_page.py
    └── components/
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
| `faker` | Synthetic data generation |
| `requests` | HTTP utilities |
| `python-dotenv` | Optional local env overrides |

---

## License

MIT — see [LICENSE](LICENSE).
