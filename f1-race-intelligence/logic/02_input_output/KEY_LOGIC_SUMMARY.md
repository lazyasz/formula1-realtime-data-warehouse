# 02. Input / Output: Key Logic & Core Summary

## 1. 16 Input Features (Pre-Race $T_0$ Boundary)

| # | Feature | Type | Range | Meaning |
|---|---|---|---|---|
| 1 | `grid_position` | Int | [1, 20] | Starting grid slot after qualifying & penalties |
| 2–3 | `driver_rolling_finish_5`, `_points_5` | Float | [1, 24], [0, 26] | Driver mean finish & points over prior 5 GPs |
| 4–5 | `constructor_rolling_finish_10`, `_points_10` | Float | [1, 24], [0, 44] | Constructor team form across prior 10 entries |
| 6–9 | `circuit_avg_finish`, `_win_rate`, `_podium_rate`, `_experience` | Float / Int | Historical track-specific form of driver |
| 10 | `season_points_before` | Float | $\ge 0$ | Current championship points entering the round |
| 11–13 | `career_starts`, `_win_rate`, `_dnf_rate` | Int / Float | Career baseline durability & win conversion |
| 14 | `ahead_of_teammate_grid` | Binary | {0, 1} | 1 if outqualified direct teammate (car parity check) |
| 15 | `driver_age` | Float | [17, 55] | Driver age at race date |
| 16 | `grid_vs_form_gap` | Float | [-20, 20] | $\Delta = \text{grid} - \text{driver\_rolling\_finish\_5}$ |

## 2. Output Specification & Invariants
- **Primary Binary Target:** `predicted_win` $\in \{0, 1\}$ (assigned to $\text{argmax}(P_{\text{win}})$ on grid).
- **Calibrated Win Probability:** $P(\text{Win}_i \mid \text{Race } j) \in [0.0, 1.0]$.
  $$\sum_{i=1}^{M_j} P(\text{Win}_i \mid \text{Race } j) = 1.0000 \quad \text{(Mutual Exclusivity Enforced)}$$
- **Multi-Class Odds:** `predicted_podium` ($P \in [0, 1]$), `predicted_points` ($P \in [0, 1]$).
- **Continuous Target:** `predicted_finish_position` $\in [1.0, 24.0]$ (Random Forest regressor).

## 3. Minimal JSON Schema Validation Logic
```python
import jsonschema, json

with open("02_input_output/input_schema.json") as f:
    input_schema = json.load(f)

# Validate payload before inference
sample_payload = {
    "race_id": 1120, "season": 2024, "round": 12, "circuit_id": "silverstone",
    "drivers": [{
        "driver_id": "hamilton", "grid_position": 2,
        "driver_rolling_finish_5": 4.2, "constructor_rolling_finish_10": 3.8,
        "circuit_win_rate": 0.444, "ahead_of_teammate_grid": 0
    }]
}
jsonschema.validate(instance=sample_payload, schema=input_schema)  # Raises if invalid
```
