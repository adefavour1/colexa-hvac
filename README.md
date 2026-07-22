# COLEXA HVAC Monitoring & Optimization Platform

A fully offline, locally-hosted HVAC & Facility Infrastructure monitoring platform for Colexa Biosensor Ltd's
regulated cleanroom manufacturing environment (ISO 13485:2016 / FDA 21 CFR Part 11 baseline controls).

## What this replaces

This application digitizes the paper **"HVAC Monitoring Log"** (Doc. No. CBL/ENG/02/R01) currently completed by
hand on the production floor, and layers real-time boundary checking, root cause analysis (RCA), CAPA logging,
compliance reporting, and an immutable audit trail on top of it.

## Monitored Scopes

| Scope | Parameter(s) | Validated Range | Governing SOP |
|---|---|---|---|
| AHU Control Panel | Temperature | 0 – 30 °C | CBL-MNT-02 |
| AHU Control Panel | Relative Humidity | ~30% target | CBL-MNT-02 |
| DHU-1 | RH / DPG | 30 – 40% / 2.5 – 25 mmWC | CBL-MNT-05 |
| DHU-2 | RH / DPG | 30 – 40% / 2.5 – 25 mmWC | CBL-MNT-05 |
| Air Conditioning (3-zone) | Temperature | 20 – 30 °C each | CBL-MNT-02 |
| Air Compressor | Delivery Pressure | 5 – 7 Bar | CBL-MNT-03 |

These ranges come directly from the controlled paper log form. Additional engineering parameters (supply air
temp, differential pressure, filter delta-P, dew point, oil differential, discharge temp) are available on the
module deep-dive pages using conservative GMP-standard defaults — confirm these against equipment datasheets
and your site validation protocol before relying on them as release-critical limits.

## Important note on RCA / CAPA content

The three underlying SOPs (CBL-MNT-02, CBL-MNT-03, CBL-MNT-05) are start-up/shutdown operating procedures. They
do not contain a pre-numbered failure-mode or CAPA-code table. The RCA/CAPA logic in `utils/rca_engine.py` is
built from standard GMP/cleanroom HVAC engineering practice and tags each recommendation back to the specific
SOP that governs the corrective action. **Engineering/QA should formally review and approve this logic before
treating generated CAPA text as validated procedure in a regulated environment.**

## Requirements

- Windows 10/11 (or any OS with Python 3.11+ for development)
- Python 3.11+
- No internet connection required at runtime

## Running in development

```bash
cd COLEXA_HVAC
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
streamlit run app.py
```

Or simply double-click **launch_colexa.bat** (Command Prompt) or run **launch_colexa.ps1** (PowerShell). Both
scripts create a virtual environment on first run, install dependencies, and launch the app automatically.

## Building the standalone executable

```bash
pip install pyinstaller
pyinstaller COLEXA_HVAC.spec
```

The finished `COLEXA_HVAC.exe` will be in `dist/COLEXA_HVAC/`. Double-clicking it starts a local Streamlit
server and opens your default browser — nothing leaves the machine.

## Project Structure

```
COLEXA_HVAC/
├── app.py                          # Main dashboard & telemetry intake
├── run_colexa.py                   # PyInstaller entry point
├── requirements.txt
├── README.md
├── COLEXA_HVAC.spec
├── launch_colexa.bat
├── launch_colexa.ps1
├── database/
│   ├── schema.py                   # Table definitions & connection helper
│   └── operations.py               # Parameterized CRUD operations
├── utils/
│   ├── ui_components.py            # Colexa theme CSS + boundary evaluator
│   ├── rca_engine.py                # Failure-mode dictionary & CAPA logic
│   └── report_generator.py         # ReportLab PDF & OpenPyXL Excel export
├── pages/
│   ├── 1_📊_Executive_Dashboard.py
│   ├── 2_❄️_AHU_Monitoring.py
│   ├── 3_💧_DHU_Monitoring.py
│   ├── 4_🌀_Air_Compressor.py
│   ├── 5_🔍_RCA_and_CAPA.py
│   ├── 6_📋_Compliance_Reports.py
│   ├── 7_📖_SOP_Library.py
│   └── 8_⚙️_System_Settings.py
├── assets/                         # Place logo.jpg here
├── exports/                        # Generated PDFs / Excel files land here
└── logs/                           # db_errors.log written here automatically
```

## Database

SQLite database at `database/colexa_matrix.db`, created automatically on first run. Tables: `facility_logs`,
`ahu_detailed_logs`, `dhu_detailed_logs`, `compressor_logs`, `panel_logs`, `deviation_logs`, `audit_trail`. All
queries use parameterized `?` placeholders — no string-formatted SQL anywhere in the codebase.

## Adding your logo

Place a `logo.jpg` file in the `assets/` folder. The sidebar and PDF reports will automatically pick it up; if
absent, a text fallback is shown instead.
