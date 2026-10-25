# Data Storage & Pipeline Specifications (1994–2024 Universe)

## 1. Directory Structure

```
data/
├── README.md
├── raw/            # Staging & metadata definitions for historical Ergast dumps (1994–2024)
└── processed/      # Curated, leak-free feature store: F1_RACE_LAB_FEATURES_1994_2024.csv
```

## 2. Dataset Overview

* **Temporal Coverage:** 1994 to 2024 FIA Formula 1 World Championship (31 seasons).
* **Scope:** 598 Championship Grands Prix, 13,248 driver race entries.
* **Grain:** 1 record per driver per Grand Prix.
* **Master Feature Store:** `data/processed/F1_RACE_LAB_FEATURES_1994_2024.csv` (35 columns).

## 3. Pre-Race Feature Groups & Target Taxonomy

### Pre-Race Feature Columns (16 Features Available Strictly Prior to Race Start):
1. `grid_position`: Starting grid position (1 to 20).
2. `driver_rolling_finish_5`: Exponential / moving average finish position over the prior 5 races.
3. `driver_rolling_points_5`: Average championship points scored over the prior 5 races.
4. `constructor_rolling_finish_10`: Constructor team average finish position over the prior 10 entries.
5. `constructor_rolling_points_10`: Constructor team average points over the prior 10 entries.
6. `circuit_avg_finish`: Historical average finish position of the driver at this specific circuit.
7. `circuit_win_rate`: Driver career win rate at this specific circuit ($W_{\text{circuit}} / N_{\text{circuit}}$).
8. `circuit_podium_rate`: Driver career podium rate at this specific circuit.
9. `circuit_experience`: Total career starts at this specific circuit.
10. `season_points_before`: Championship points accumulated entering the round (strictly 0 for Round 1).
11. `career_starts`: Cumulative career Grands Prix starts prior to this race.
12. `career_win_rate`: Career win rate ($W_{\text{career}} / N_{\text{career}}$).
13. `career_dnf_rate`: Historical career mechanical and incident retirement rate.
14. `ahead_of_teammate_grid`: Binary indicator (1 if driver outqualified their teammate, 0 otherwise).
15. `driver_age`: Driver age in years at race date.
16. `grid_vs_form_gap`: Delta between grid slot and 5-race rolling form (`grid_position - driver_rolling_finish_5`).

### Target Columns (Post-Race Classification & Regression Targets):
1. `target_is_win`: 1 if driver finished 1st, 0 otherwise.
2. `target_is_podium`: 1 if driver finished 1st, 2nd, or 3rd, 0 otherwise.
3. `target_is_points`: 1 if driver scored championship points (P1–P10), 0 otherwise.
4. `target_is_dnf`: 1 if driver failed to finish due to mechanical or accident attrition, 0 otherwise.
5. `target_finish_position`: Classified numerical finish position (clipped 1 to 20).
