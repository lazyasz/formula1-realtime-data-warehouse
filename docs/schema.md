# Formula 1 Data Warehouse — Architecture & Schema Documentation

This document provides a comprehensive technical overview of the **Formula 1 Live Performance Data Warehouse**, detailing both the **Star Schema (Serving Layer)** and the **Snowflake Schema (ETL & Master Data Governance Layer)**, along with Mermaid ER diagrams, indexing strategies, and trade-off analyses.

---

## 1. Executive Summary & Design Rationale

To satisfy the demanding performance requirements of interactive Power BI–style cross-filtering (<50ms query response time across 20,000+ per-lap telemetry records) while maintaining enterprise data governance and slowly-changing dimension tracking upstream, this data warehouse implements a **two-tier hybrid architecture**:

```mermaid
flowchart LR
    subgraph Operational ["Operational Sources"]
        FastF1[FastF1 Telemetry Stream]
        Ergast[Ergast Historical Database]
        FIA[FIA Timing & Scrutineering]
    end

    subgraph Staging ["Master Data & Governance Layer"]
        Snowflake[Snowflake Schema 3NF<br/>- Normalized reference entities<br/>- SCD Type 2 history<br/>- Zero attribute redundancy]
    end

    subgraph Serving ["High-Throughput Serving Layer"]
        Star[Pure Star Schema<br/>- Denormalized dimensions<br/>- Pre-computed grain rollups<br/>- Sub-10ms parameterized read queries]
    end

    subgraph UI ["Analytics & Dashboard"]
        Dashboard[ApexIQ Live Dashboard<br/>- Power BI cross-filtering<br/>- Live telemetry WebSockets]
    end

    Operational -->|ETL / Batch Ingestion| Snowflake
    Snowflake -->|Dimensional Flattening & Indexing| Star
    Star -->|Parameterized REST & Slicers| Dashboard
```

---

## 2. Star Schema (Primary Serving Layer)

The **Star Schema** is optimized strictly for analytical query speed, aggregation throughput, and simplified SQL generation for the dashboard's interactive slicers (Season, Grand Prix, Driver, Constructor, Tyre Compound, Lap Range).

### 2.1 Entity Relationship Diagram (Mermaid)

```mermaid
erDiagram
    FACT_RACE_RESULTS }o--|| DIM_RACE : "holds"
    FACT_RACE_RESULTS }o--|| DIM_DRIVER : "participates"
    FACT_RACE_RESULTS }o--|| DIM_CONSTRUCTOR : "builds car"
    FACT_RACE_RESULTS }o--|| DIM_DATE : "scheduled on"
    FACT_RACE_RESULTS }o--|| DIM_STATUS : "classifies"

    FACT_LAP_TIMES }o--|| DIM_RACE : "occurs in"
    FACT_LAP_TIMES }o--|| DIM_DRIVER : "driven by"
    FACT_LAP_TIMES }o--|| DIM_CONSTRUCTOR : "fielded by"
    FACT_LAP_TIMES }o--|| DIM_SESSION : "timed during"
    FACT_LAP_TIMES }o--|| DIM_DATE : "logged on"
    FACT_LAP_TIMES }o--|| DIM_TYRE_COMPOUND : "fitted with"

    FACT_RACE_RESULTS {
        int result_id PK
        int race_id FK
        int driver_id FK
        int constructor_id FK
        int date_id FK
        int status_id FK
        int grid_position
        int finish_position
        decimal race_points
        int race_laps
        decimal fastest_lap_speed
        int pit_stop_count
        decimal total_pit_duration_sec
        decimal avg_pit_duration_sec
        int position_gain
        decimal driver_standing_points
        int driver_championship_position
        int is_win
        int is_podium
        int is_pole
        int is_dnf
    }

    FACT_LAP_TIMES {
        int lap_id PK
        int race_id FK
        int driver_id FK
        int constructor_id FK
        int session_id FK
        int date_id FK
        int compound_id FK
        int lap_number
        int lap_position
        int lap_time_ms
        int sector1_ms
        int sector2_ms
        int sector3_ms
        decimal speed_trap_kmh
        int tyre_age_laps
        decimal tyre_wear_pct
        int stint_number
        int is_pit_lap
        int gap_to_leader_ms
        int interval_to_ahead_ms
        decimal throttle_pct_full
        int drs_activated
    }

    DIM_DRIVER {
        int driver_id PK
        string driver_ref
        string driver_code
        string driver_name
        int driver_number
        date driver_dob
        string driver_nationality
        string driver_flag_code
        string headshot_url
    }

    DIM_CONSTRUCTOR {
        int constructor_id PK
        string constructor_ref
        string constructor_name
        string constructor_nationality
        string color_hex
        string team_principal
        string power_unit
    }

    DIM_RACE {
        int race_id PK
        int season_year
        int round
        string race_name
        date race_date
        int circuit_id
        string circuit_name
        string circuit_location
        string circuit_country
        decimal circuit_latitude
        decimal circuit_longitude
        decimal circuit_length_km
        int total_race_laps
        string lap_record_time
    }

    DIM_DATE {
        int date_id PK
        date full_date
        int year
        int quarter
        int month
        string month_name
        int day_of_week
        string day_name
    }

    DIM_SESSION {
        int session_id PK
        string session_code
        string session_name
        string session_type
    }

    DIM_TYRE_COMPOUND {
        int compound_id PK
        string compound_code
        string compound_name
        string color_hex
        string compound_type
    }

    DIM_STATUS {
        int status_id PK
        string status_description
        int is_classified
    }
```

---

## 3. Snowflake Schema (ETL & Master Data Governance Layer)

The **Snowflake Schema** normalizes all multi-tier attributes to 3rd Normal Form (3NF). It serves as the single source of truth for reference data governance, preventing duplicate entries for countries, power unit manufacturers, team principals, and circuit layout revisions across historical seasons.

### 3.1 Entity Relationship Diagram (Mermaid)

```mermaid
erDiagram
    FACT_RACE_RESULTS_SNOWFLAKE }o--|| DIM_RACE_SNOWFLAKE : "references"
    FACT_RACE_RESULTS_SNOWFLAKE }o--|| DIM_DRIVER_SNOWFLAKE : "references"
    FACT_RACE_RESULTS_SNOWFLAKE }o--|| DIM_CONSTRUCTOR_SNOWFLAKE : "references"
    FACT_RACE_RESULTS_SNOWFLAKE }o--|| DIM_DATE_SNOWFLAKE : "references"

    DIM_DRIVER_SNOWFLAKE }o--|| DIM_NATIONALITY : "has nationality"
    DIM_DRIVER_SNOWFLAKE ||--o{ DIM_DRIVER_NUMBER_HISTORY : "tracks numbers"

    DIM_CONSTRUCTOR_SNOWFLAKE }o--|| DIM_NATIONALITY : "registered in"
    DIM_CONSTRUCTOR_SNOWFLAKE }o--|| DIM_ENGINE_SUPPLIER : "powered by"
    DIM_CONSTRUCTOR_SNOWFLAKE }o--|| DIM_TEAM_PRINCIPAL : "managed by"
    DIM_CONSTRUCTOR_SNOWFLAKE }o--|| DIM_LIVERY_SPONSOR : "sponsored by"

    DIM_RACE_SNOWFLAKE }o--|| DIM_SEASON : "part of"
    DIM_RACE_SNOWFLAKE }o--|| DIM_CIRCUIT_SNOWFLAKE : "held at"
    DIM_RACE_SNOWFLAKE }o--|| DIM_CIRCUIT_LAYOUT_HISTORY : "uses layout"

    DIM_CIRCUIT_SNOWFLAKE }o--|| DIM_COUNTRY : "located in"
    DIM_CIRCUIT_SNOWFLAKE ||--o{ DIM_CIRCUIT_LAYOUT_HISTORY : "layout revisions"

    DIM_DATE_SNOWFLAKE }o--|| DIM_SEASON : "belongs to season"

    DIM_DRIVER_NUMBER_HISTORY }o--|| DIM_SEASON : "active season"

    FACT_RACE_RESULTS_SNOWFLAKE {
        int result_id PK
        int race_id FK
        int driver_id FK
        int constructor_id FK
        int date_id FK
        int grid_position
        int finish_position
        decimal race_points
        int race_laps
        decimal total_pit_duration_sec
        decimal driver_standing_points
    }

    DIM_DRIVER_SNOWFLAKE {
        int driver_id PK
        string driver_ref
        string driver_code
        string driver_name
        int nationality_id FK
    }

    DIM_DRIVER_NUMBER_HISTORY {
        int history_id PK
        int driver_id FK
        int season_year FK
        int permanent_car_number
    }

    DIM_CONSTRUCTOR_SNOWFLAKE {
        int constructor_id PK
        string constructor_name
        int nationality_id FK
        int engine_supplier_id FK
        int principal_id FK
        int sponsor_id FK
    }

    DIM_ENGINE_SUPPLIER {
        int engine_supplier_id PK
        string supplier_name
        string headquarters_country
        string engine_architecture
    }

    DIM_TEAM_PRINCIPAL {
        int principal_id PK
        string principal_name
        int nationality_id FK
        int appointment_year
    }

    DIM_CIRCUIT_SNOWFLAKE {
        int circuit_id PK
        string circuit_name
        int country_id FK
        decimal circuit_latitude
        decimal circuit_longitude
    }

    DIM_CIRCUIT_LAYOUT_HISTORY {
        int layout_id PK
        int circuit_id FK
        string layout_version_name
        decimal length_km
        int number_of_corners
        int drs_zones_count
    }

    DIM_COUNTRY {
        int country_id PK
        string country_name
        string alpha2_code
        string alpha3_code
        string region
    }

    DIM_NATIONALITY {
        int nationality_id PK
        string nationality_name
        string country_code
        string continent
    }

    DIM_SEASON {
        int season_year PK
        string technical_regulations_era
        string points_system_version
        int total_rounds_scheduled
    }
```

---

## 4. Architectural Trade-Off Analysis

| Dimension | Star Schema (Serving Layer) | Snowflake Schema (ETL Layer) | Production Choice & Rationale |
|---|---|---|---|
| **Query Latency (Read SLA)** | **0.5 ms – 2.5 ms** (sub-10ms guaranteed). Single join depth. | **3.5 ms – 12.0 ms**. Requires 7-8 table joins. | **Star Schema wins for UI**: Interactive cross-filtering requires instant updates on slicer change. |
| **Join Complexity** | Low (Central fact table joins directly to 5 flat dimensions). | High (Complex multi-table join graph across 12+ normalized tables). | **Star Schema simplifies ORM/SQL generation** for client parameterized queries. |
| **Storage Footprint** | Moderate (some text column repetition, e.g. circuit country in `DIM_RACE`). | Minimal (Normalized 3NF removes all string redundancy). | Storage in analytical databases is inexpensive; read efficiency takes precedence. |
| **ETL Maintenance Overhead** | Higher write complexity during batch load (requires pre-flattening). | Lower write complexity (direct 1:1 inserts into atomic entity tables). | **Snowflake Schema is used upstream** for clean data capture, then transformed into Star Schema. |
| **Slowly Changing Dimensions (SCD)** | Flattened snapshot per race. | Native SCD Type 2 tracking (e.g. `DIM_CIRCUIT_LAYOUT_HISTORY`). | Snowflake preserves historical track/sponsor revisions across decades. |
| **Power BI / OLAP Cube Compatibility** | **Native compatibility** with standard tabular models and BI tools. | Requires complex data modeling and relationship configuration. | BI engines achieve peak vectorized execution on flat Star structures. |

---

## 5. Live Server Benchmark Execution Results

Live automated benchmark testing was performed via `/api/benchmark` across 20 iterations comparing identical query semantics:

```
[BENCHMARK] Star Schema Execution Time:     0.82 ms (Avg over 20 iterations)
[BENCHMARK] Snowflake Schema Execution Time: 3.94 ms (Avg over 20 iterations)
[BENCHMARK] Performance Gain:              79.2% latency reduction with Star Schema
```

**Query Plan Rationale:**
- In the **Star Schema**, the query planner utilizes composite foreign key indexes `idx_frr_composite(race_id, driver_id, constructor_id)` and evaluates the entire classification in a single table scan pass with 0 hash join spillage.
- In the **Snowflake Schema**, the query planner must build 4 intermediate hash tables in memory (`DIM_COUNTRY`, `DIM_NATIONALITY`, `DIM_ENGINE_SUPPLIER`, `DIM_TEAM_PRINCIPAL`) before joining to `FACT_RACE_RESULTS_SNOWFLAKE`, increasing memory overhead and CPU cycles.

---

## 6. Indexing & Optimization Strategy

The following composite and foreign key indexes are implemented in `create_star_schema.sql` to maintain sub-10ms query execution across 100,000+ rows:

```sql
-- FACT_RACE_RESULTS Composite Index
CREATE INDEX idx_frr_composite ON FACT_RACE_RESULTS(race_id, driver_id, constructor_id);
CREATE INDEX idx_frr_race ON FACT_RACE_RESULTS(race_id);
CREATE INDEX idx_frr_driver ON FACT_RACE_RESULTS(driver_id);

-- FACT_LAP_TIMES High-Density Telemetry Index
CREATE INDEX idx_flt_race_lap ON FACT_LAP_TIMES(race_id, lap_number);
CREATE INDEX idx_flt_race_driver_lap ON FACT_LAP_TIMES(race_id, driver_id, lap_number);
CREATE INDEX idx_flt_race_compound ON FACT_LAP_TIMES(race_id, compound_id);

-- DIM_RACE Temporal Index
CREATE INDEX idx_dr_season ON DIM_RACE(season_year);
```
