<div align="center">

# 🌊 NAYA PANI (नया पानी)
### Photorealistic 3D Hydrological Digital Twin, USGS MODFLOW 6 Physics Engine & AI Forecasting Platform

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.42+-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Three.js](https://img.shields.io/badge/Three.js-WebGL%202.0-black?logo=three.js&logoColor=white)](https://threejs.org/)
[![USGS MODFLOW 6](https://img.shields.io/badge/USGS-MODFLOW%206%20Physics-006699?logo=open-access&logoColor=white)](https://www.usgs.gov/software/modflow-6-usgs-modular-hydrologic-model)
[![FastAPI](https://img.shields.io/badge/FastAPI-Microservices-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![CGWA](https://img.shields.io/badge/CGWA-GEC--2015%20Auditor-0D9488)](http://cgwa-noc.gov.in/)
[![NVIDIA Omniverse](https://img.shields.io/badge/NVIDIA-OpenUSD%20SimReady-76B900?logo=nvidia&logoColor=white)](https://www.nvidia.com/en-us/omniverse/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<p align="center">
  <b>A living, interactive 50 km radius geospatial environmental digital twin, finite-difference groundwater numerical solver, statutory CGWA 2020 regulatory compliance auditor, live IoT DWLR telemetry network, and multi-model machine learning forecasting suite for the Rajasthan Luni River Basin.</b>
</p>

[Key Features](#-key-features) • [System Architecture](#-system-architecture) • [Technology Stack](#-technology-stack) • [REST API Documentation](#-rest-api-microservices) • [1-Click Quick Start](#-quick-start--installation) • [Author & Citation](#-author--citation)

</div>

---

## 🏛️ Author & Research Affiliation

This project was conceived, architected, and engineered by:

* **Aman Kumar Ranjan** ([@Amankumarranjan8969](https://github.com/Amankumarranjan8969))
* **Institution**: **National Institute of Hydrology (NIH), Roorkee**, Uttarakhand, India
* **Initiative**: Undertaken as part of the Hydrological Sciences & Groundwater Intelligence research internship in collaboration with Ministry of Jal Shakti guidelines.

> *"Transforming traditional static hydrogeological workbooks into a coupled, living 3D digital twin backed by rigorous numerical physics, statutory regulatory governance, and explainable artificial intelligence."*

### Citation (BibTeX)
```bibtex
@software{ranjan2026nayapani,
  author       = {Aman Kumar Ranjan},
  title        = {{NAYA PANI: Photorealistic 3D Hydrological Digital Twin, USGS MODFLOW 6 Physics Engine and Groundwater AI Forecasting Platform}},
  institution  = {National Institute of Hydrology (NIH), Roorkee},
  year         = {2026},
  publisher    = {GitHub},
  url          = {https://github.com/Amankumarranjan8969/Groundwater-RAG-forecast}
}
```

---

## 🌟 Key Features

### 1. Photorealistic 50 km Regional 3D Digital Twin (WebGL / Three.js)
- **Geographic Extent**: Continuously models an entire $50\text{ km}$ radius region ($\sim 7,854\text{ km}^2$) centered on the arid **Thar Desert & Luni River Basin**.
- **Terrain & Photogrammetry**: Georeferenced Digital Elevation Model (DEM) with high-frequency normal bump maps and georeferenced satellite textures.
- **Physical 3D Assets**: Real 3D tree mesh models (`tree_sonnerat.obj`, `tree_walnut.obj` with Bark and Foliage material shaders), xerophytic scrub bushes (*Capparis decidua* / Kair), authentic rural settlements, and georeferenced river courses.
- **Atmospheric Shaders**: Real-time daylight solar azimuth calculation, dynamic precipitation particle physics, dynamic cloud cover, and seasonal haze.
- **Subsurface Solute Transport Plume**: 380-particle advection-dispersion plume simulating salinity and fluoride migration from the saline Luni riverbed into adjacent unconfined alluvium.
- **Dual Display Modes**: Embedded responsive canvas with full inspection toolbar (`⛶ Fullscreen`, layer toggles, weather sliders) plus a dedicated standalone viewer (`twin_fullscreen.html`).

### 2. USGS MODFLOW 6 3D Finite-Difference Physics Solver
- **Governing Equations**: Physics-informed numerical solver solving the 3D groundwater flow equation:
  $$\nabla \cdot (\mathbf{K} \nabla h) + W = S_s \frac{\partial h}{\partial t}$$
- **Stratigraphy Domain**: 5 coupled geological layers (Alluvium, Sandstone, Fractured Basalt, Confining Shale/Clay, Granitic Basement) across a $40 \times 40$ structured spatial grid.
- **Live Output Metrics**: Maximum local cone drawdown ($m$), mean regional hydraulic head ($m\text{ ASL}$), net recharge inflow ($\text{m}^3/\text{day}$), and mass balance discrepancy ($<0.05\%$).
- **One-Click USGS MODFLOW 6 Package Exporter**: Automatically generates and downloads a complete, runnable **USGS MODFLOW 6 project ZIP** (`rajasthan_luni_modflow6_project.zip`) containing standard input packages (`sim.nam`, `dis`, `npf`, `ic`, `chd`, `wel`, `rch`, `oc`, `ims`) compatible with FloPy and official USGS executables.

### 3. Statutory CGWA 2020 & GEC-2015 Regulatory Compliance Auditor
- **Statutory Framework**: Formulated strictly according to Ministry of Jal Shakti Gazette Notification S.O. 3289(E) and Ground Water Estimation Committee (GEC-2015) methodology.
- **Extraction Auditing**: Automatically calculates Stage of Groundwater Extraction ($\text{SOGWE } \%$), Annual Extractable Ground Water Resource, Total Annual Extraction Draft, and statutory categorizations:
  - **Safe** ($\le 70\%$)
  - **Semi-Critical** ($70\% - 90\%$)
  - **Critical** ($90\% - 100\%$)
  - **Over-Exploited** ($> 100\%$)
  - **Saline** ($EC > 3000\ \mu\text{S/cm}$)
- **Statutory NOC Clearance Rules**: Outlines commercial/industrial NOC clearance eligibility, water conservation fee bands, and mandatory recharge obligations ($100\% - 200\%$).
- **MAR AHP Suitability Ranking**: Analytical Hierarchy Process (AHP) multi-criteria ranking for Managed Aquifer Recharge interventions (Check-Dams, Percolation Ponds, Subsurface Dykes, Recharge Shafts).

### 4. Live CGWB DWLR IoT Telemetry Stream & Edge QA/QC Filter
- **Sensor Network**: Real-time Digital Water Level Recorder (DWLR) and solar tube-well SCADA telemetry streams.
- **Automated Edge QA/QC Filter**:
  - Rate-of-change spike rejection ($>2.5\text{ m/day}$ delta threshold).
  - Low battery cutoff alert ($<3.2\text{ V}$).
  - Physical boundary compliance ($0.1\text{ to } 150\text{ mbgl}$).
  - Signal RSSI signal-to-noise health diagnostic.
- **Real-Time Simulation**: 15-minute telemetry sync tick button and instant GeoJSON spatial layer serialization.

### 5. Multi-Family Machine Learning & Deep Learning Forecasting
- **Headline ML Suite**: SVR (RBF Kernel), Random Forest, Gradient Boosting (GBDT), CatBoost, XGBoost, LightGBM, and mRMR (Minimum Redundancy Maximum Relevance) feature selection.
- **Physics-Informed & Deep Learning Suite**:
  - **PINN** (Physics-Informed Neural Network with soft water-balance loss regularization).
  - **Reservoir Computing (Echo State Network - ESN)** riding non-linear lag trajectories.
  - **SARIMAX** classical auto-regressive baseline with meteorological drivers.
  - **PyTorch LSTM** recurrent network over deep multi-step lag sequences.
- **Scenario Projections**: Recursive auto-regressive 1–10 year seasonal forecasts under variable precipitation, drought anomalies, and pumping draft factors.

### 6. Explainable AI (XAI) & Hydrogeological Diagnostics
- **SHAP (SHapley Additive exPlanations)**: TreeExplainer and KernelExplainer waterfall plots and global feature attribution beeswarms.
- **Sensitivity Ranking**: Leave-One-Feature-Out (LOFO) validation drop ranking.
- **Hydro Diagnostics**: Continuous wavelet scalograms (Morlet / Ricker), Taylor diagrams comparing correlation vs. normalized standard deviation, ACF/PACF autocorrelation, and cross-correlation timelines.

### 7. Context-Aware RAG Copilot ("Ask Naya Pani")
- **Bi-Directional Context Sync**: Synchronized with active 3D camera coordinates, selected wellhead sensors, scenario levers, and live MODFLOW state.
- **Enterprise Security**: Sanitization layer protecting against prompt injection, unauthorized system disclosure, and cross-session data leakage.
- **Provenance Tracing**: Every answer cites exact workbook rows, telemetry sensors, and grounded scientific literature in `rag/knowledge_base/`.

### 8. NVIDIA Omniverse & OpenUSD SimReady Stage Bridge
- Compiles full hydrogeological stages into Pixar OpenUSD (`.usda`) scene descriptions (`/World/RajasthanBasin/MonitoringNetwork/...`).
- Validates 3D hydro assets against NVIDIA Omniverse SimReady schemas (physics-ready semantics, mass balance metadata, and verifiable data provenance).

### 9. Production FastAPI Microservices (`api_service.py`)
- Independent REST API backend running on port `8080` providing programmatic access to MODFLOW 6 solvers, live DWLR telemetry packets, CGWA audits, and Omniverse sessions.
- Interactive Swagger / OpenAPI documentation served at `http://localhost:8080/docs`.

### 10. Automated Scientific Word Report Generator (`scientific_report.py`)
- Single-click compilation of complete analysis runs into executive Word documents (`.docx`) complete with figures, statistical validation tables, model comparisons, and statutory citations.

---

## 🏗️ System Architecture

```
                                  NAYA PANI ARCHITECTURE
                                  
  [ Excel Workbooks / DWLR IoT Telemetry Streams ]
                       │
                       ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      DATA INGESTION & PIPELINE ENGINE                   │
 │   • Data Quality & Outlier Detection  • Lag Feature Engineering        │
 │   • Edge QA/QC Spike Rejection Filter • GEC-2015 Hydrological Baseline │
 └─────────────────────────────────┬──────────────────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
┌──────────────────┐     ┌──────────────────┐     ┌──────────────────────┐
│  AI FORECASTING  │     │ USGS MODFLOW 6   │     │   CGWA REGULATORY    │
│  ML / DL SUITE   │     │ NUMERICAL SOLVER │     │   STATUTORY AUDITOR  │
│ • SVR, RF, GBDT  │     │ • 5 Geo Layers   │     │ • SOGWE % Auditor    │
│ • CatBoost, XGB  │     │ • 40x40 Grid     │     │ • Safe/OE Category   │
│ • PINN, ESN, LSTM│     │ • Darcy Vectors  │     │ • NOC Rules & Fees   │
│ • SHAP & LOFO XAI│     │ • ZIP Exporter   │     │ • MAR AHP Intervent. │
└────────┬─────────┘     └────────┬─────────┘     └──────────┬───────────┘
         │                        │                          │
         └────────────────────────┼──────────────────────────┘
                                  ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                         COUPLED DIGITAL TWIN HUB                       │
 │   • Sustainable Water-Budget Capacity Planner                          │
 │   • Subsurface Salinity/Fluoride Advection-Dispersion Plume            │
 │   • Context-Aware RAG Copilot ("Ask Naya Pani")                        │
 └────────────────────────────────┬───────────────────────────────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
┌─────────────────────────────────┐               ┌───────────────────────┐
│     INTERACTIVE USER CLIENTS    │               │  FASTAPI MICROSERVICE │
│ • Streamlit Web Dashboard (8501)│               │  REST API (Port 8080) │
│ • Photorealistic Three.js (3D)  │               │ • /api/v1/telemetry   │
│ • Standalone Fullscreen 3D Twin │               │ • /api/v1/modflow     │
│ • NVIDIA OpenUSD Stage (.usda)  │               │ • /api/v1/cgwa        │
│ • Automated Word Report (.docx) │               │ • Swagger UI (/docs)  │
└─────────────────────────────────┘               └───────────────────────┘
```

---

## 💻 Technology Stack

| Component | Technologies |
|---|---|
| **User Interface & Dashboard** | Streamlit, HTML5, CSS3, JavaScript, Plotly Express/Graph Objects, KaTeX |
| **3D Rendering & WebGL Engine** | Three.js (r128), WebGL 2.0, OBJLoader, MTLLoader, OrbitControls |
| **3D Assets & Geospatial Data** | Wavefront OBJ/MTL, Georeferenced DEM elevation matrices, Normal Maps, Satellite Textures |
| **Numerical Hydrology** | USGS MODFLOW 6, FloPy, SciPy (Sparse / Spatial IDW), NumPy, Pandas |
| **Statutory & Regulatory Rules** | CGWA 2020 Gazette Notification S.O. 3289(E), GEC-2015 Methodology |
| **Machine Learning Suite** | Scikit-Learn, CatBoost, XGBoost, LightGBM, mRMR, Statsmodels |
| **Deep Learning & PINN** | PyTorch (LSTM), Reservoir Computing (Echo State Networks), Physics-Informed Neural Nets |
| **Explainable AI (XAI)** | SHAP (Shapley Additive exPlanations), Leave-One-Feature-Out (LOFO) Sensitivity |
| **IoT & Telemetry Processing** | Edge QA/QC sliding-window filters, GeoJSON serialization, SCADA buffers |
| **Context Retrieval & RAG** | Vector similarity retriever, TF-IDF lexical index, Provenance tracking, Security guardrails |
| **3D Scene Interoperability** | Pixar OpenUSD (`.usda`), NVIDIA Omniverse SimReady Hydro Schemas |
| **Microservices Backend** | FastAPI, Uvicorn, Pydantic v2, Argon2-cffi |
| **Reporting & Export** | python-docx, openpyxl, standard MODFLOW 6 input package format |
| **Automation & Launchers** | Windows Batch Script (`.bat`), Native PowerShell Script (`.ps1`) |

---

## 🔌 REST API Microservices (`api_service.py`)

Naya Pani includes an independent, production-ready **FastAPI** microservice suite running on port `8080`.

To start the API standalone:
```bash
python -m uvicorn api_service:app --port 8080 --host 127.0.0.1
```

Once running, explore the interactive **OpenAPI / Swagger documentation** at:
👉 **`http://localhost:8080/docs`**

### Available Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/v1/health` | System health check and status of all numerical and AI engines |
| `GET` | `/api/v1/telemetry/latest` | Returns latest verified DWLR telemetry packets from all monitoring stations |
| `POST` | `/api/v1/telemetry/sync` | Triggers a 15-minute telemetry sync tick with automated Edge QA/QC filtering |
| `GET` | `/api/v1/telemetry/geojson` | Returns all active monitoring well coordinates and stress levels as GeoJSON |
| `POST` | `/api/v1/modflow/solve` | Executes the 3D finite-difference groundwater solver given baseline DTWL and pumping draft |
| `GET` | `/api/v1/modflow/download-bundle` | Streams a complete, runnable USGS MODFLOW 6 project ZIP archive |
| `POST` | `/api/v1/cgwa/audit` | Performs statutory CGWA assessment (SOGWE %, Over-Exploited category, NOC rules) |
| `GET` | `/api/v1/digital-twin/omniverse-session` | Retrieves active NVIDIA Omniverse live session channel and OpenUSD metadata |

---

## 🚀 Quick Start & Installation

### Option 1: True 1-Click Launch (Windows Explorer)
1. Open File Explorer in the project root.
2. **Double-click:**
   ```text
   START_NAYA_PANI.bat
   ```
   *The launcher will automatically detect Python, set up `.venv`, install all dependencies, start the background services, and open your browser to `http://localhost:8501`.*

### Option 2: PowerShell 1-Click Launch
In PowerShell, run:
```powershell
.\START_NAYA_PANI.ps1
```
*(Or if script execution policy is restricted: `powershell -ExecutionPolicy Bypass -File .\START_NAYA_PANI.ps1`)*

### Option 3: Manual Developer Setup (Cross-Platform)

```bash
# 1. Clone the repository
git clone https://github.com/Amankumarranjan8969/Groundwater-RAG-forecast.git
cd Groundwater-RAG-forecast

# 2. Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux / macOS:
source .venv/bin/activate

# 3. Upgrade packaging tools and install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# 4. Launch the application
streamlit run app.py --server.port 8501
```

Open your browser at **`http://localhost:8501`**.

---

## 📂 Pre-Packaged Sample Datasets (`sample_data/`)

Validated, real-world seasonal workbooks for the **Rajasthan Luni River Basin** are provided in `sample_data/`:

| Dataset | Observations | District / Block | Key Characteristics |
|---|---|---|---|
| `sample_data/Ajmer_Luni.xlsx` | 116 records | Ajmer (Pisangan block) | Upstream semi-arid alluvial aquifer |
| `sample_data/Barmer_Luni2.xlsx` | Regional basin | Barmer (Balotra block) | Arid Thar desert zone with saline river dynamics |
| `sample_data/Jodhpur_Luni.xlsx` | Regional basin | Jodhpur | Deep groundwater table with seasonal agricultural draft |
| `sample_data/Pali_Luni2.xlsx` | Central basin | Pali | Industrial and agrarian mixed-use unconfined alluvium |
| `sample_data/Rajsamand_Luni.xlsx`| Headwaters | Rajsamand | Hard rock upper catchment boundary |

> **How to Test**: Simply drag and drop any of these Excel files into the sidebar file uploader on the dashboard, configure your parameters, and click **"Run complete analysis"**!

---

## 🗂️ Project Directory Structure

```text
Groundwater-RAG-forecast/
├── app.py                         # Main Streamlit enterprise application and page transitions
├── digital_twin.py                # 3D Digital Twin Three.js renderer, MODFLOW solver UI, CGWA tabs
├── twin_engine.py                 # Coupled simulation engine, OpenUSD stage exporter, water-budget planner
├── modflow_engine.py              # USGS MODFLOW 6 3D finite-difference physics numerical solver
├── telemetry_stream.py            # Live CGWB DWLR IoT telemetry buffer with Edge QA/QC filter
├── cgwa_auditor.py                # Statutory CGWA 2020 & GEC-2015 extraction assessment engine
├── pipeline.py                    # Data validation, lag preparation, model training & cross-validation
├── deep_models.py                 # PINN, Echo State Networks (ESN), SARIMA, and PyTorch LSTM models
├── scientific_report.py           # Automated Microsoft Word (.docx) scientific report compiler
├── security_engine.py             # RAG prompt injection detection and response sanitization
├── session_store.py               # Temporary in-memory workspace session cache
├── admin_dashboard.py             # Administrative control panel and telemetry monitor
├── admin_security.py              # Argon2 password hashing and brute-force throttling
├── api_service.py                 # Production FastAPI REST microservices (Port 8080)
├── pwa_server.py                  # Progressive Web App (PWA) server integration
├── test_digital_twin_and_rag.py   # Comprehensive 8-suite automated verification test suite
├── requirements.txt               # Pinned production Python dependencies
├── .env.example                   # Safe template for environment variables and API keys
├── .gitignore                     # Production Git ignore rules (protects credentials & large caches)
├── LICENSE                        # MIT Open Source License
├── README.md                      # Comprehensive technical documentation & citation
│
├── .streamlit/
│   ├── config.toml                # Streamlit server and theme configuration (enableStaticServing=true)
│   └── secrets.toml.example       # Safe template for OIDC and administrative secrets
│
├── static/                        # Production 3D assets, textures, and standalone viewer
│   ├── tree_sonnerat.obj          # Centered 3D OBJ mesh: Sonnerat canopy & trunk
│   ├── tree_sonnerat.mtl          # Wavefront MTL material definition
│   ├── tree_walnut.obj            # Centered 3D OBJ mesh: Walnut foliage & trunk
│   ├── tree_walnut.mtl            # Wavefront MTL material definition
│   ├── Bark___S.jpg               # High-resolution trunk bark texture
│   ├── Sonnerat.jpg               # High-resolution Sonnerat foliage texture
│   ├── Bark___0.jpg               # Walnut bark texture
│   ├── Walnut_L.jpg               # Walnut foliage texture
│   ├── Grass1.jpg                 # Ground photogrammetry surface texture
│   ├── elevation_luni_50km.json   # 50 km radius georeferenced DEM elevation matrix
│   ├── satellite_luni_50km.jpg    # Georeferenced satellite surface imagery
│   ├── normal_luni_50km.jpg       # High-frequency normal relief bump map
│   ├── twin_fullscreen.html       # Standalone Fullscreen 3D Digital Twin Viewer
│   └── favicon.ico, logo.png      # Application branding icons
│
├── sample_data/                   # Real-world validated Excel workbooks for immediate testing
│   ├── Ajmer_Luni.xlsx
│   ├── Barmer_Luni2.xlsx
│   ├── Jodhpur_Luni.xlsx
│   ├── Pali_Luni2.xlsx
│   └── Rajsamand_Luni.xlsx
│
├── rag/                           # Retrieval-Augmented Generation (RAG) AI Assistant
│   ├── assistant.py               # RAG response synthesis and prompt assembly
│   ├── context.py                 # Live Digital Twin context synchronization
│   ├── llm_provider.py            # Optional cloud LLM bridge (Gemini / Anthropic) with local fallback
│   ├── retriever.py               # Lexical and semantic document retriever
│   ├── smalltalk.py               # Conversational intent classifier
│   └── knowledge_base/            # Grounded hydrogeology scientific documentation
│       ├── digital_twin.md        # 3D Digital Twin documentation
│       ├── deep_models.md         # PINN and neural network methodology
│       ├── metrics.md             # Evaluation metrics (R2, RMSE, MAE)
│       ├── overview.md            # Luni Basin hydrogeology overview
│       ├── seasons.md             # Monsoon, Pre-, Post-, and Non-Monsoon definitions
│       └── troubleshooting.md     # Hydrogeological diagnostics FAQ
│
├── START_NAYA_PANI.bat            # Windows 1-click launcher (CMD / File Explorer)
├── START_NAYA_PANI.ps1            # Windows 1-click launcher (PowerShell)
├── START_3D_TWIN_ONLY.bat         # Standalone 3D twin viewer launcher
├── INSTALL_DEPENDENCIES.bat       # Manual dependency installer script
├── RUN_TESTS.bat                  # Automated test suite runner (CMD)
├── RUN_TESTS.ps1                  # Automated test suite runner (PowerShell)
└── START_HERE.html                # Offline interactive welcome and quick-start guide
```

---

## 🧪 Verification & Automated Test Suite

Naya Pani includes an end-to-end automated verification suite in `test_digital_twin_and_rag.py`.

To run the full suite:
```bash
python test_digital_twin_and_rag.py
```

### Verified Test Suites:
1. `[PASS]` **Syntax & Imports**: Zero compilation or import errors across all modules.
2. `[PASS]` **Workbook & Spatial Metadata**: 116 records, geospatial coordinate retention (`LATITUDE`, `LONGITUDE`, `DISTRICT`, `BLOCK`).
3. `[PASS]` **Coupled Simulation Engine**: Verified baseline ($7.94\text{ mbgl}$), drought stress ($+0.44\text{ m}$), and recharge recovery ($-1.43\text{ m}$).
4. `[PASS]` **3D Hydrogeological Twin Figure**: Real geodesic and conceptual fallback modes.
5. `[PASS]` **RAG + Twin Synchronization**: Context alignment, security guardrails, and provenance tagging.
6. `[PASS]` **Assistant Parity**: 100% parity across Main AI Assistant, Floating Icon, and Twin Copilot across all 8 pages.
7. `[PASS]` **NVIDIA OpenUSD & SimReady Validation**: Validates `.usda` stage hierarchy and Sustainable Water-Budget planner.
8. `[PASS]` **Industry Engines**: USGS MODFLOW 6 finite-difference solver, live DWLR telemetry stream, CGWA audit, and FastAPI client.

---

## 🔒 Security & Privacy

- **Zero Secret Leaks**: All private credentials, passwords, session tokens, and API keys are excluded via `.gitignore`.
- **Pre-Hashed Authentication**: Uses **Argon2** password hashing with exponential backoff throttling against brute-force attacks.
- **RAG Security Guard**: Built-in sanitization engine rejects prompt injection attempts and filters sensitive operational parameters.
- **Air-Gapped Operation**: The entire platform (3D Digital Twin, MODFLOW 6 physics, CGWA auditor, ML/DL models, and local RAG composition) runs **100% locally and offline** without requiring external cloud connections.

---

## 📜 License & Acknowledgments

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

### Acknowledgments
* **National Institute of Hydrology (NIH), Roorkee** for providing research guidance, domain expertise, and dataset validation.
* **Ministry of Jal Shakti, Government of India** for statutory CGWA guidelines and groundwater estimation committee (GEC-2015) methodologies.
* **USGS Hydrology Software Program** for open standards in modular groundwater flow modeling (MODFLOW 6).
* **NVIDIA Omniverse Team** for open standards in OpenUSD and SimReady environmental simulation schemas.

---

<div align="center">
  <b>NAYA PANI (नया पानी) — Advancing Groundwater Resilience Through 3D Digital Twins and Artificial Intelligence.</b><br>
  <sub>Developed by Aman Kumar Ranjan at NIH Roorkee.</sub>
</div>
