# 🏎️ FORMULA 1 ENTERPRISE DATA WAREHOUSE & ANALYTICS PLATFORM (2004–2024)
### Complete Master Project Archive & Deliverables Directory

---

## 📌 1. Project Overview & Architecture Summary

This repository contains the end-to-end implementation of the **Formula 1 Race Performance Data Warehouse**, covering 20+ seasons (2004–2024) of race results, telemetry, pit stop strategies, qualifying sessions, sprint races, and championship standings.

- **Source Dataset:** 65-column comprehensive F1 Master Dataset spanning 2004 to 2024.
- **Architectures Supported:** Dual Schema Architecture (**Ultra-Lean Star Schema** & **Fully Normalized Snowflake Schema**).
- **Core Database Engine:** SQLite 3 (`f1_warehouse.db`, 83.7 MB, pre-seeded and indexed) + PostgreSQL (Docker).
- **OLAP Capabilities:** Multidimensional Data Cube (MOLAP / ROLAP / HOLAP Engine) supporting Drill-Down, Roll-Up, Slice, Dice, and Pivot operations.
- **Business Intelligence & Dashboards:** Power BI Desktop Project (`F1Dashboard.pbix`), Power BI Web Emulator (`powerbi_f1.html`), Dark-themed Web Dashboard (`dashboard.html`), Grafana Telemetry Suite (`grafana.html`), and Interactive Schema Viewer (`schema_viewer.html`).
- **Live Telemetry & Simulation:** Dockerized real-time telemetry streaming service feeding Grafana and WebSockets.

---

## 🗂️ 2. Master Folder Structure & Inventory

```
F1_Data_Warehouse_Master_Collection/
│
├── 00_README_MASTER_INDEX.md                           # Master documentation and quick-start guide
│
├── 📁 01_Project_Documentation_and_Reports/             # All Formal Reports, Academic Deliverables & PDFs
│   ├── Formula 1 Analytics Data Warehouse - Jury Project Report.pdf
│   ├── Formula 1 Enterprise Data Warehouse - Comprehensive Project Report.pdf
│   ├── Formula 1 Data Warehouse - Ultra-Lean Star Schema Visualizer.pdf
│   ├── Formula 1 Race Performance Data Warehouse - Technical Report.pdf
│   ├── Formula_1_Race_Performance_Data_Warehouse_Report.docx
│   ├── F1_Project_Report.html                          # Standalone rich HTML presentation report
│   ├── Executive_Summary.md                            # High-level summary of findings & KPIs
│   ├── 11_Full_Project_Report.md                       # Complete 11-section academic project report
│   ├── PROJECT_REPORT_COMPLETE.md                      # Detailed architectural writeup
│   ├── qa-report.md                                    # Validation & QA testing report
│   └── schema.md                                       # Formal schema specification
│
├── 📁 02_Presentation_Viva_and_Guides/                 # Presentation Scripts, Viva Prep & Examiner Q&A
│   ├── 00_LAYMANS_STEP_BY_STEP_GUIDE.md                # Simple analogies explaining DW concepts
│   ├── 01_HOW_TO_PRESENT_TOMORROW_SPEECH_SCRIPT.md     # Word-for-word 5-10 min presentation script
│   ├── 02_CORE_CONCEPTS_AND_WHY_WE_BUILT_THIS.md       # Architectural justification & design decisions
│   ├── 03_VIVA_EXAMINER_QUESTIONS_AND_ANSWERS.md       # 30+ Viva examiner questions & model answers
│   ├── 04_LIVE_DEMO_CLICK_BY_CLICK_STEPS.md            # Exact sequence for a flawless live demo
│   ├── 12_Demonstration_Guide.md                       # Comprehensive demonstration guide
│   ├── NAPKIN_AI_STAR_SCHEMA_PROMPT.md                 # Prompts for visual schema diagram generation
│   ├── run_demo.bat / run_demo.ps1                     # One-click demo launch scripts
│   └── README.md
│
├── 📁 03_Schemas_DDL_and_Data_Dictionary/              # SQL DDLs, Star/Snowflake Schemas & Data Dictionaries
│   ├── create_star_schema.sql                          # Ultra-Lean Star Schema DDL (Facts + Dimensions)
│   ├── create_snowflake_schema.sql                     # Normalized Snowflake Schema DDL
│   ├── create_schema.sql                               # Unified schema definition script
│   ├── snowflake_master_deployment.sql                 # Cloud Snowflake deployment script
│   ├── data_dictionary.md                              # Complete data dictionary for all columns & types
│   ├── source_to_target_mapping.csv                    # Staging to Target mapping table
│   ├── er_diagram_star.mmd                             # Mermaid ER diagram for Star Schema
│   ├── er_diagram_snowflake.mmd                        # Mermaid ER diagram for Snowflake Schema
│   └── er_diagram.mmd                                  # General Mermaid schema diagram
│
├── 📁 04_Databases/                                    # Populated Relational & Warehouse Databases
│   ├── f1_warehouse.db                                 # Full 83.7 MB SQLite DB with all records indexed
│   └── postgres_init/                                  # PostgreSQL Docker container initialization DDLs
│       ├── 01_create_snowflake_schema.sql
│       └── 02_create_star_schema.sql
│
├── 📁 05_Datasets_and_CSV_Tables/                      # Raw Staging Data & Exported Star/Snowflake CSVs
│   ├── RAW_F1_STAGING.csv                              # Master unnormalized staging CSV (3.7 MB)
│   ├── F1_Warehouse_Master_65_Columns_2004_2024.csv    # Full cleaned source dataset (3.7 MB)
│   └── All_Dimension_and_Fact_CSVs/                    # 15 individual CSV tables ready for import
│       ├── FACT_RACE_RESULTS.csv                       # Star Fact table (2.07 MB)
│       ├── FACT_RACE_RESULTS_SNOWFLAKE.csv             # Snowflake Fact table (2.00 MB)
│       ├── DIM_DRIVER.csv                              # Driver dimension
│       ├── DIM_CONSTRUCTOR.csv                         # Constructor dimension
│       ├── DIM_DATE.csv                                # Temporal / Calendar dimension
│       ├── DIM_CIRCUIT_SNOWFLAKE.csv                   # Circuit normalization table
│       ├── DIM_RACE_STAR.csv / DIM_RACE_SNOWFLAKE.csv  # Race dimensions
│       ├── DIM_QUALIFYING.csv                          # Qualifying performance dimension
│       ├── DIM_PIT_STRATEGY.csv                        # Pit stop telemetry dimension
│       ├── DIM_FASTEST_LAP_TELEMETRY.csv               # Fastest lap telemetrics
│       ├── DIM_SPRINT_RESULT.csv                       # Sprint race dimension
│       ├── DIM_STANDINGS_SNAPSHOT.csv                  # Championship points snapshot
│       └── DIM_STATUS.csv                              # Retirement/Finishing status dimension
│
├── 📁 06_ETL_Pipelines_and_Scripts/                    # Automated Extraction, Transformation & Loading
│   ├── etl_master_ingestion.py                         # Master ETL pipeline script
│   ├── etl_pipeline.py                                 # Robust transformation & cleaning pipeline
│   ├── seed_database.py                                # Automated database seeding script
│   ├── f1_cube_engine.py                               # Multidimensional OLAP Data Cube Engine
│   └── server.py                                       # Flask Backend API & WebSocket live telemetry server
│
├── 📁 07_OLAP_Queries_and_Analysis/                    # Complex Analytical Queries & OLAP Operations
│   ├── olap_queries.sql                                # Comprehensive SQL suite (Roll-up, Drill-down, Slice, Dice, Moving Avg, Window Ranking)
│   ├── run_olap_suite.py                               # Automated Python test runner for all OLAP queries
│   ├── 08_Data_Cube_Design.md                          # OLAP Cube dimension & measure specifications
│   └── 09_OLAP_Queries.md                              # Detailed explanation of analytical queries
│
├── 📁 08_Dashboards_and_Visualizations/                # Interactive BI Dashboards & Web Viewers
│   ├── F1Dashboard.pbix                                # Power BI Desktop Project File (7.87 MB)
│   ├── powerbi_f1.html                                 # Standalone interactive Power BI web simulator
│   ├── dashboard.html                                  # Modern dark-mode web analytics dashboard
│   ├── showcase.html                                   # Complete visual interactive showcase
│   ├── grafana.html                                    # Real-time Grafana telemetry dashboard emulator
│   ├── schema_viewer.html                              # Interactive visual ER diagram & schema explorer
│   ├── serve.ps1                                       # PowerShell local web server launcher
│   ├── serve_schema.ps1                                # Schema viewer server script
│   └── 10_Dashboard_Guide.md                           # BI Dashboard setup & usage guide
│
├── 📁 09_Docker_and_Live_Simulation/                   # Microservices, Grafana Provisioning & Simulator
│   ├── docker-compose.yml                              # Multi-container orchestration (Postgres + Grafana + Simulator)
│   ├── provisioning/                                   # Grafana pre-configured dashboard JSONs & data sources
│   │   ├── dashboards/ (overview.json, drivers.json, constructors.json, live_telemetry.json)
│   │   └── datasources/ (postgres.yaml)
│   └── sim_service/                                    # Real-time race simulator microservice
│       ├── Dockerfile, entrypoint.sh, live_simulator.py, etl_and_seed.py, requirements.txt
│
├── 📁 10_Testing_and_QA_Suite/                         # Automated Quality Assurance & Verification
│   ├── test_f1_qa.py                                   # Data integrity & schema constraint tests
│   ├── test_grafana_qa.py                              # Grafana dashboard & API verification
│   └── test_powerbi_qa.py                              # Power BI data model & measure validator
│
└── 📁 11_Original_Modular_Project_Folder/              # Complete original 12-module directory structure
    ├── 01_Problem_Definition/
    ├── 02_Requirement_Analysis/
    ├── 03_Source_Database_Design/
    ├── 04_ETL_Process/
    ├── 05_Data_Warehouse_Architecture/
    ├── 06_Star_and_Snowflake_Schema/
    ├── 07_Fact_and_Dimension_Tables/
    ├── 08_Data_Cube_Design/
    ├── 09_OLAP_Queries/
    ├── 10_Dashboard/
    ├── 11_Project_Report/
    ├── 12_Demonstration/
    ├── FOR_ME_TO_UNDERSTAND/
    └── PROJECT FILES/
```

---

## 🚀 3. Quick Start Guide: How to Run Everything

### A. Run OLAP Queries & Cube Engine
To execute the automated OLAP analytical query suite:
```powershell
python "07_OLAP_Queries_and_Analysis\run_olap_suite.py"
```
To run multidimensional cube operations (Roll-up, Drill-down, Slice, Dice, Pivot):
```powershell
python "06_ETL_Pipelines_and_Scripts\f1_cube_engine.py"
```

### B. Launch Interactive Web Dashboards
To launch the interactive dashboards in your web browser:
1. Double-click or open `08_Dashboards_and_Visualizations\powerbi_f1.html` or `08_Dashboards_and_Visualizations\dashboard.html` in Chrome/Edge/Firefox.
2. Or run the local server script:
```powershell
powershell -ExecutionPolicy Bypass -File "08_Dashboards_and_Visualizations\serve.ps1"
```

### C. Open Power BI Dashboard
Open `08_Dashboards_and_Visualizations\F1Dashboard.pbix` in Microsoft Power BI Desktop. All relationships between `FACT_RACE_RESULTS` and Dimension tables are pre-configured.

### D. Run Docker Containerized Environment (Postgres + Grafana)
```powershell
cd "09_Docker_and_Live_Simulation"
docker-compose up --build
```
- Grafana UI: `http://localhost:3000` (User: `admin`, Password: `f1password`)
- PostgreSQL Warehouse: `localhost:5432` (Database: `f1_warehouse`)

---

## 🏆 4. Key Highlights & Achievements
- **Dual Schema Support:** Demonstrates the trade-offs between Star Schema (de-normalized, high-speed read analytics) and Snowflake Schema (3NF normalized, storage-optimized).
- **Comprehensive Granularity:** Tracks lap times down to milliseconds, tyre stint degradation, pit stop durations, qualifying gaps (Q1, Q2, Q3), and sprint race points.
- **Enterprise-Ready:** Fully automated Python ETL pipelines, SQL DDL migrations, pre-built Power BI & Grafana dashboards, Dockerized services, and thorough Viva exam preparation guides.
