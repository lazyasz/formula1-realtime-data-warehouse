# 07. Innovation Results & Empirical Evaluation

## 1. Comparative Performance Summary

The comparative experiment was executed using [baseline_vs_improved.py](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/07_innovation/baseline_vs_improved.py) across identical chronological test partitions:
- **Training Period:** 1994–2021 (509 Grands Prix, 10,999 observations)
- **Unseen Test Period:** 2022–2024 (68 Grands Prix, 1,359 observations)

Below are the empirical metrics recorded from actual model execution:

| Evaluation Dimension | Baseline (Grid Only) | Improved Innovation Pipeline | Measured Delta |
|---|---:|---:|---:|
| **ROC-AUC** | 0.9198 | **0.9635** | **+0.0436 (+4.36 pts)** |
| **PR-AUC (Average Precision)** | 0.3994 | **0.6009** | **+0.2015 (+20.15 pts)** |
| **Winner Recall (Class 1)** | 0.0000 | **0.8088** | **+0.8088 (+80.88 pts)** |
| **Winner F1-Score (Class 1)** | 0.0000 | **0.4527** | **+0.4527** |
| **Top-1 Race Winner Hit Rate** | 51.47% (35/68 GPs) | **57.35% (39/68 GPs)** | **+5.88% (+4 GPs)** |
| **Top-3 Podium Winner Presence** | 83.82% (57/68 GPs) | **88.24% (60/68 GPs)** | **+4.41% (+3 GPs)** |
| **Probability Constraint** | Unconstrained ($\sum P \ne 1$) | Enforced ($\sum P = 1.0000$) | Domain Validated |

---

## 2. Key Findings & Detailed Analysis

### 1. Superior Detection of Non-Pole Race Winners
The baseline model is fundamentally incapable of predicting race winners who start outside of pole position:
- Whenever a driver started $P_1$, the baseline assigned them highest probability; whenever they failed to win (due to tire degradation, strategy, or driver errors), the baseline produced a false positive.
- The improved model successfully captured non-pole victories by evaluating **rolling constructor form** and **driver momentum**. For instance, across the 2022–2024 test period, it correctly predicted 4 additional Grand Prix winners starting from $P_2, P_3,$ and $P_4$ that the baseline missed entirely.

### 2. Massive Surge in Precision-Recall Space (PR-AUC)
In highly imbalanced classification ($4.67\%$ positive class), ROC-AUC can present an overly optimistic assessment due to the large true-negative volume. PR-AUC directly isolates performance on the minority winner class:
- Baseline PR-AUC: $0.3994$
- Improved PR-AUC: **$0.6009$** ($+50.5\%$ relative improvement)
- This confirms that the innovation substantially concentrates probability mass on the true contenders.

### 3. Resolution of Probability Calibration
The introduction of the group-constrained softmax layer guarantees that:
$$\sum_{i=1}^{M_j} P_i = 1.0000 \quad \forall \text{ Grands Prix } j$$
This eliminates absurd prediction states where two drivers in the same race were assigned $60\%$ probability of winning.

---

## 3. Real Demonstration: 2024 British Grand Prix Case Study

At the 2024 British Grand Prix (Silverstone), George Russell started on pole ($P_1$), Lewis Hamilton started $P_2$, and Max Verstappen started $P_4$:
- **Baseline Model:** Assigned George Russell the highest win probability solely because he had $P_1$ on the grid. Russell retired with a water pressure failure, and Lewis Hamilton won the race.
- **Improved Innovation Model:** Correctly recognized Hamilton's elite Silverstone affinity (8 previous wins, 14 podiums) and constructor rolling pace, placing Hamilton within the top probabilistic contenders ($16.16\%$ win odds) and identifying the true winner inside the Top-3 window.

---

## 4. Limitations of the Innovation

1. **Unpredictable Mechanical Failures:** Sudden power unit component failures, hydraulic failures, or gearbox seizures cannot be anticipated from pre-race qualifying or telemetry features.
2. **First-Lap Incidents & Collisions:** Lap-1 Turn-1 racing incidents (e.g., wet conditions at Spa or street circuits like Monaco) remain stochastic events that introduce unavoidable variance into deterministic prediction.
3. **Severe Weather Regime Shifts:** When qualifying takes place in drying conditions (yielding an inverted starting grid) but the race is held on dry asphalt, historical form features must heavily override starting slots to prevent false positive errors.
