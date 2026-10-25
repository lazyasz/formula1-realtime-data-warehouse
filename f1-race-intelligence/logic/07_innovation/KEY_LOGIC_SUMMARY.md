# 07. Innovation Added: Key Logic & Core Summary

## 1. Domain-Specific Innovations Added
Four engineered improvements over naive grid-only baselines:
1. **Multi-Horizon Rolling Form:** Driver 5-race finish average and Constructor 10-entry rolling pace (isolates modern aero package from career history).
2. **Circuit Affinity Index:** Driver track-specific win rate and experience ($\ge 5$ starts) at the exact circuit.
3. **Intra-Team Qualifying Delta:** `ahead_of_teammate_grid` isolates driver raw pace from machinery performance.
4. **Group-Softmax Probability Constraint:** Enforces $\sum_{i=1}^{M_j} P_i = 1.0000$ per Grand Prix.

## 2. Empirical Benchmark: Baseline vs. Innovation (2022–2024 Holdout)

| Evaluation Metric | Baseline (Grid Only) | Innovation Pipeline | Measured Delta |
|---|---:|---:|---:|
| **ROC-AUC** | 0.9198 | **0.9635** | **+0.0436 (+4.36 pts)** |
| **PR-AUC (Average Precision)** | 0.3994 | **0.6009** | **+0.2015 (+20.15 pts)** |
| **Winner Class Recall** | 0.0000 | **0.8088** | **+0.8088 (+80.88 pts)** |
| **Top-1 Race Winner Hit Rate** | 51.47% (35/68 GPs) | **57.35% (39/68 GPs)** | **+5.88% (+4 GPs)** |
| **Top-3 Podium Winner Presence**| 83.82% (57/68 GPs) | **88.24% (60/68 GPs)** | **+4.41% (+3 GPs)** |
| **Probability Constraint** | Unconstrained ($\sum P \ne 1$) | Enforced ($\sum P = 1.00$) | Domain Validated |

## 3. Real Proof Case: 2024 British GP (Silverstone)
- **Baseline (Grid P1):** Selected George Russell on pole; Russell retired on Lap 34 with water pressure failure.
- **Innovation Model:** Integrated Lewis Hamilton's track affinity (8 previous Silverstone wins) and rolling form, identifying Hamilton ($P_2$ grid) inside top probability window to correctly predict the race winner.

## 4. Minimal Implementation of Rolling Feature Logic
```python
# Zero-leakage rolling finish calculation: shift(1) strictly excludes current race
df = df.sort_values(by=["driver_id", "date"])
df["driver_rolling_finish_5"] = (
    df.groupby("driver_id")["finish_position"]
      .transform(lambda s: s.shift(1).rolling(5, min_periods=1).mean())
)

# Constructor rolling pace across both team cars
df = df.sort_values(by=["constructor_id", "date"])
df["constructor_rolling_finish_10"] = (
    df.groupby("constructor_id")["finish_position"]
      .transform(lambda s: s.shift(1).rolling(10, min_periods=1).mean())
)
```
