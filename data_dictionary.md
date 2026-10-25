# F1 Race Performance Data Warehouse — Tailored Data Dictionary

This document details the database schema for the F1 Race Performance Data Warehouse tailored to the pre-joined master CSV dataset `F1_Warehouse_Master_65_Columns_2004_2024.csv` (which has 68 columns).

> [!IMPORTANT]
> **Schema Differences & Comparison:**
> - **Star Schema**: Fully denormalized. `DIM_CIRCUIT` is merged into `DIM_RACE`, removing the circuit table and foreign key. This reduces join depth during querying.
> - **Snowflake Schema**: Normalized. `DIM_CIRCUIT` remains a separate dimension, referenced by `DIM_RACE` using `circuit_id` as a foreign key. This reduces duplicate circuit records.

---

## Dimension Tables

### 1. `DIM_DRIVER`
*Used in: Star Schema & Snowflake Schema (Identical)*

Stores descriptive attributes of Formula 1 drivers.

| Column Name | Data Type | Key | Description | CSV Source Column | Notes |
|---|---|---|---|---|---|
| `driver_id` | INT | PK | Unique identifier for each driver. | `driver_id` | Primary surrogate key |
| `driver_ref` | VARCHAR(50) | Unique | Code-like reference name for the driver. | `driver_ref` | e.g. "hamilton" |
| `driver_code` | VARCHAR(3) | | Standard three-letter abbreviation. | `driver_code` | e.g. "HAM" |
| `driver_name` | VARCHAR(100) | | Full name of the driver. | `driver_name` | e.g. "Lewis Hamilton" |
| `driver_dob` | DATE | | Driver's date of birth. | `driver_dob` | |
| `driver_nationality` | VARCHAR(50) | | Nationality of the driver. | `driver_nationality` | |

---

### 2. `DIM_CONSTRUCTOR`
*Used in: Star Schema & Snowflake Schema (Identical)*

Stores attributes of F1 teams/constructors.

| Column Name | Data Type | Key | Description | CSV Source Column | Notes |
|---|---|---|---|---|---|
| `constructor_id` | INT | PK | Unique identifier for each constructor. | `constructor_id` | Primary surrogate key |
| `constructor_ref` | VARCHAR(50) | Unique | Code-like reference name for the constructor. | `constructor_ref` | e.g. "mclaren" |
| `constructor_name` | VARCHAR(100) | | Official name of the constructor. | `constructor_name` | e.g. "McLaren" |
| `constructor_nationality` | VARCHAR(50) | | Nationality of the constructor team. | `constructor_nationality` | |

---

### 3. `DIM_CIRCUIT`
*Used in: Snowflake Schema only (Merged into DIM_RACE in Star Schema)*

Stores details of racetracks/circuits.

| Column Name | Data Type | Key | Description | CSV Source Column | Notes |
|---|---|---|---|---|---|
| `circuit_id` | INT | PK | Unique identifier for each circuit. | `circuit_id` | Primary surrogate key |
| `circuit_name` | VARCHAR(150) | | Official name of the circuit. | `circuit_name` | |
| `circuit_location` | VARCHAR(100) | | City or local area of the circuit. | `circuit_location` | |
| `circuit_country` | VARCHAR(100) | | Country where the circuit is located. | `circuit_country` | |
| `circuit_latitude` | DECIMAL(9,6) | | Geographic latitude coordinate. | `circuit_latitude` | |
| `circuit_longitude` | DECIMAL(9,6) | | Geographic longitude coordinate. | `circuit_longitude` | |
| `circuit_altitude_m` | INT | | Elevation of the circuit in meters. | `circuit_altitude_m` | |

---

### 4. `DIM_RACE`
Stores information about specific races (Grands Prix).

*Note: In the **Star Schema**, this table includes denormalized circuit fields. In the **Snowflake Schema**, this table references `DIM_CIRCUIT` via `circuit_id`.*

| Column Name | Data Type | Key | Description | CSV Source Column | Schema Role |
|---|---|---|---|---|---|
| `race_id` | INT | PK | Unique identifier for each race. | `race_id` | Star & Snowflake PK |
| `season_year` | INT | Unique-1 | The year of the championship season. | `season` | Star & Snowflake |
| `round` | INT | Unique-2 | The round number in the championship calendar. | `round` | Star & Snowflake |
| `race_name` | VARCHAR(100) | | The official name of the Grand Prix. | `race_name` | Star & Snowflake |
| `circuit_id` | INT | FK (Snowflake) | Circuit identifier. | `circuit_id` | Star (Attribute) / Snowflake (FK to `DIM_CIRCUIT`) |
| **`circuit_name`** | VARCHAR(150) | | Official name of the circuit. | `circuit_name` | **Star Schema Only** (Denormalized) |
| **`circuit_location`** | VARCHAR(100) | | City or local area of the circuit. | `circuit_location` | **Star Schema Only** (Denormalized) |
| **`circuit_country`** | VARCHAR(100) | | Country where the circuit is located. | `circuit_country` | **Star Schema Only** (Denormalized) |
| **`circuit_latitude`** | DECIMAL(9,6) | | Geographic latitude coordinate. | `circuit_latitude` | **Star Schema Only** (Denormalized) |
| **`circuit_longitude`** | DECIMAL(9,6) | | Geographic longitude coordinate. | `circuit_longitude` | **Star Schema Only** (Denormalized) |
| **`circuit_altitude_m`** | INT | | Elevation of the circuit in meters. | `circuit_altitude_m` | **Star Schema Only** (Denormalized) |
| `race_date` | DATE | | Scheduled date of the race. | `race_date` | Star & Snowflake |
| `race_start_time` | TIME | | Scheduled start time of the race (UTC). | `race_start_time` | Star & Snowflake |

---

### 5. `DIM_STATUS`
*Used in: Star Schema & Snowflake Schema (Identical)*

Stores status codes representing how a driver finished a race or retired.

| Column Name | Data Type | Key | Description | CSV Source Column | Notes |
|---|---|---|---|---|---|
| `status_id` | SERIAL | PK | Auto-incremented identifier for status. | Derived during staging | Primary surrogate key |
| `status_description` | VARCHAR(100) | Unique | Description of status (e.g. "Finished", "Collision"). | `race_status` | |

---

### 6. `DIM_DATE`
*Used in: Star Schema & Snowflake Schema (Identical)*

Stores calendar helper fields to facilitate time-based slicing.

| Column Name | Data Type | Key | Description | CSV Source Column | Notes |
|---|---|---|---|---|---|
| `date_id` | INT | PK | Unique key formatted as YYYYMMDD. | Derived from `race_date` | e.g. `20080316` |
| `full_date` | DATE | Unique | The calendar date value. | Derived from `race_date` | e.g., `2008-03-16` |
| `year` | INT | | The calendar year. | Derived from `race_date` | |
| `quarter` | INT | | The calendar quarter (1-4). | Derived from `race_date` | |
| `month` | INT | | The calendar month number (1-12). | Derived from `race_date` | |
| `month_name` | VARCHAR(20) | | Full text month name (e.g. "March"). | Derived from `race_date` | |
| `day_of_week` | INT | | Day of week index (1 = Monday, 7 = Sunday). | Derived from `race_date` | |
| `day_name` | VARCHAR(20) | | Full text day name (e.g. "Sunday"). | Derived from `race_date` | |

---

## Fact Table: `FACT_RACE_RESULTS`
*Used in: Star Schema & Snowflake Schema (Identical)*

Records driver and team overall performance metrics per race.

| Column Name | Data Type | Key | Description | CSV Source Column | Notes |
|---|---|---|---|---|---|
| `result_id` | SERIAL | PK | Auto-incrementing identifier for each result. | Derived by DB | Surrogate primary key |
| `race_id` | INT | FK | ID linking to the race dimension. | `race_id` | Links to `DIM_RACE` |
| `driver_id` | INT | FK | ID linking to the driver dimension. | `driver_id` | Links to `DIM_DRIVER` |
| `constructor_id` | INT | FK | ID linking to the constructor dimension. | `constructor_id` | Links to `DIM_CONSTRUCTOR` |
| `date_id` | INT | FK | ID linking to the date dimension. | `race_date` | Lookup of race date in `DIM_DATE` |
| `status_id` | INT | FK | ID linking to status dimension (finish/retirement reason). | `race_status` | Lookup of status in `DIM_STATUS` |
| `car_number` | INT | | Driver's car number for the race. | `car_number` | |
| `grid_position` | INT | | Starting grid position. | `grid_position` | |
| `qualifying_position` | INT | | Position achieved during qualifying. | `qualifying_position` | |
| `qualifying_best_time_sec` | DECIMAL(6,3) | | Best lap time recorded in qualifying in seconds. | `qualifying_best_time_sec` | |
| `finish_position` | INT | | Final classification position. | `finish_position` | Null if DNF |
| `finish_position_text` | VARCHAR(10) | | Finishing position raw text. | `finish_position_text` | e.g. "1", "R", "D" |
| `race_points` | DECIMAL(5,2) | | Championship points scored in this race. | `race_points` | |
| `race_laps` | INT | | Total laps completed in the race by this driver. | `race_laps` | |
| `race_time` | VARCHAR(20) | | Total race duration formatted as string. | `race_time` | e.g. "1:34:50.616" |
| `race_milliseconds` | BIGINT | | Total race duration in milliseconds. | `race_milliseconds` | |
| `fastest_lap_number` | INT | | Lap number on which fastest lap was set. | `fastest_lap_number` | |
| `fastest_lap_rank` | INT | | Relative ranking of fastest lap in the race. | `fastest_lap_rank` | |
| `fastest_lap_time` | VARCHAR(20) | | Fastest lap time formatted as string. | `fastest_lap_time` | e.g. "1:27.452" |
| `fastest_lap_speed` | DECIMAL(6,3) | | Average speed of fastest lap (km/h). | `fastest_lap_speed` | |
| `pit_stop_count` | INT | | Total pit stops in the race. | `pit_stop_count` | |
| `total_pit_duration_sec` | DECIMAL(7,3) | | Sum of durations of all pit stops. | `total_pit_duration_sec` | |
| `avg_pit_duration_sec` | DECIMAL(6,3) | | Average duration of pit stops. | `avg_pit_duration_sec` | |
| `fastest_pit_duration_sec` | DECIMAL(6,3) | | Shortest pit stop duration. | `fastest_pit_duration_sec` | |
| `last_pit_lap` | INT | | Lap number on which last pit stop was done. | `last_pit_lap` | |
| `laps_recorded` | INT | | Laps for which lap time data was recorded. | `laps_recorded` | |
| `fastest_recorded_lap_ms` | INT | | Fastest recorded lap time in ms. | `fastest_recorded_lap_ms` | |
| `average_lap_ms` | INT | | Average lap time in ms. | `average_lap_ms` | |
| `sprint_position` | INT | | Finish position in sprint race. | `sprint_position` | 0 if no sprint |
| `sprint_points` | DECIMAL(5,2) | | Sprint race points scored. | `sprint_points` | |
| `driver_standing_points` | DECIMAL(7,2) | | Driver's championship points at this race. | `driver_standing_points` | |
| `driver_championship_position` | INT | | Driver's rank in championship at this race. | `driver_championship_position` | |
| `driver_championship_wins` | INT | | Cumulative wins by driver in season. | `driver_championship_wins` | |
| `constructor_standing_points` | DECIMAL(7,2) | | Constructor's championship points at this race. | `constructor_standing_points` | |
| `constructor_championship_position` | INT | | Constructor's rank in championship at this race. | `constructor_championship_position` | |
| `constructor_championship_wins` | INT | | Cumulative wins by constructor in season. | `constructor_championship_wins` | |
| `constructor_race_points` | DECIMAL(7,2) | | Total points scored by constructor in this race. | `constructor_race_points` | |
| `position_gain` | INT | | Places gained/lost (finish_position - grid_position). | `position_gain` | |
| `qualifying_to_finish_delta` | INT | | Places gained/lost from qualifying position. | `qualifying_to_finish_delta` | |
| `is_pole` | INT | | 1 if driver was on pole, else 0. | `is_pole` | |
| `is_podium` | INT | | 1 if driver finished on podium (1-3), else 0. | `is_podium` | |
| `is_win` | INT | | 1 if driver won, else 0. | `is_win` | |
| `is_top_10` | INT | | 1 if driver finished in top 10, else 0. | `is_top_10` | |
| `is_dnf` | INT | | 1 if driver did not finish, else 0. | `is_dnf` | |
| `points_per_lap` | DECIMAL(6,4) | | Points scored per lap. | `points_per_lap` | |
| `race_completion_pct` | DECIMAL(5,4) | | Percentage of race distance completed. | `race_completion_pct` | |
| `driver_age_years` | DECIMAL(5,2) | | Driver's age at date of race. | `driver_age_years` | |
| `driver_standing_gap_to_leader` | DECIMAL(7,2) | | Points behind driver championship leader. | `driver_standing_gap_to_leader` | |
| `constructor_standing_gap_to_leader` | DECIMAL(7,2) | | Points behind constructor championship leader. | `constructor_standing_gap_to_leader` | |

---

## Machine Learning & Winner Prediction Feature Layer

*Table: `ML_WINNER_PREDICTION_FEATURES` (in `f1_warehouse.db`) and `F1_ML_Winner_Prediction_Dataset.csv` (97 total columns)*

### 1. 🚗 Car Features
| Column Name | Data Type | Description | Source / Derivation |
|---|---|---|---|
| `car_engine_architecture` | VARCHAR(100) | Formula engine specification (e.g. 1.6L V6 Turbo Hybrid, 2.4L V8, 3.0L V10). | Derived from technical regulation era |
| `car_power_unit_supplier` | VARCHAR(50) | Official engine supplier / manufacturer (Ferrari, Mercedes, Red Bull Powertrains, Honda, Renault, BMW). | Manufacturer tracking across seasons |
| `car_estimated_power_bhp` | INT | Engine output rating in BHP, accounting for works factory tier advantages. | Calculated from engine era & supplier |
| `car_min_weight_kg` | INT | Official FIA minimum car weight regulation for that season (605kg–798kg). | FIA Technical Regulations |
| `car_power_to_weight_ratio` | DECIMAL(6,4) | Ratio of engine power to minimum car weight (BHP / kg). | `car_estimated_power_bhp / car_min_weight_kg` |
| `car_aero_regulation_era` | VARCHAR(100) | Aerodynamic formula era (e.g., Ground Effect, Turbo Hybrid Wide, V8 Blown Diffuser). | FIA Aero Rule Epochs |
| `car_chassis_model` | VARCHAR(50) | Constructor chassis model designation (e.g., RB20, SF-24, MCL38, W15). | Constructor Chassis Registry |
| `car_mechanical_reliability_score` | DECIMAL(5,4) | Non-mechanical completion rate (% of races completed without mechanical DNF). | Historical seasonal aggregation |
| `constructor_pace_index` | DECIMAL(5,2) | Relative qualifying pace advantage index (higher = faster chassis). | `21.0 - constructor_season_avg_grid` |

### 2. ⏱️ Lap Record & Track Speed Features
| Column Name | Data Type | Description | Source / Derivation |
|---|---|---|---|
| `circuit_lap_record_sec` | DECIMAL(6,3) | Official all-time FIA race lap record for the circuit (in seconds). | Official F1 Track Records |
| `circuit_lap_record_str` | VARCHAR(20) | Formatted lap record time string (e.g. "1:27.097"). | Official F1 Track Records |
| `circuit_lap_record_holder` | VARCHAR(100) | Driver holding the all-time race lap record. | Official F1 Track Records |
| `circuit_lap_record_year` | INT | Year in which the all-time race lap record was established. | Official F1 Track Records |
| `driver_fastest_lap_sec` | DECIMAL(6,3) | Driver's fastest lap time in the Grand Prix in seconds. | `fastest_lap_time` or `fastest_recorded_lap_ms` |
| `driver_lap_record_delta_sec` | DECIMAL(6,3) | Gap in seconds between driver fastest lap and all-time circuit record. | `driver_fastest_lap_sec - circuit_lap_record_sec` |
| `driver_lap_record_ratio` | DECIMAL(6,4) | Pace ratio against all-time track record (1.0 = equal to record). | `driver_fastest_lap_sec / circuit_lap_record_sec` |
| `driver_quali_to_record_delta_sec` | DECIMAL(6,3) | Delta between qualifying time and circuit lap record limit. | `driver_qualifying_sec - circuit_lap_record_sec` |

### 3. 🛠️ Pit Stop Times & Efficiency Features
| Column Name | Data Type | Description | Source / Derivation |
|---|---|---|---|
| `circuit_pit_lane_loss_sec` | DECIMAL(5,2) | Baseline pit lane transit time penalty for the circuit (19.4s–27.8s). | FIA Circuit Geometry & Speed Limits |
| `pit_crew_efficiency_score` | DECIMAL(5,2) | Constructor pit crew execution benchmark score (0–100 scale). | DHL Fastest Pit Stop Benchmark Data |
| `estimated_stationary_pit_sec` | DECIMAL(6,3) | Estimated wheel-gun stationary tire change time (isolated from pit transit). | `avg_pit_duration_sec - circuit_pit_lane_loss_sec` |
| `total_race_pit_loss_sec` | DECIMAL(7,2) | Net race time invested in pit stops across the Grand Prix. | `(pit_stop_count * circuit_pit_lane_loss_sec) + total_pit_duration_sec` |
| `pit_loss_delta_to_race_mean_sec` | DECIMAL(6,2) | Pit stop efficiency delta relative to the race field average. | `total_race_pit_loss_sec - race_mean_pit_loss` |
| `winning_strategy_stop_count` | INT | Number of pit stops executed by the eventual race winner. | Race winner pit stop count |
| `pit_stop_delta_to_winning_strategy` | INT | Difference in pit stop count from the winning strategy. | `pit_stop_count - winning_strategy_stop_count` |

