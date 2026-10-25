# 07. Innovation Proposal: Multi-Horizon Rolling Momentum & Group Softmax Constraint

## 1. Motivation & Problem Statement

In Formula 1 motorsport analytics, naive models rely heavily on qualifying grid slot ($P_1, P_2, \dots$) as a static proxy for victory. While pole position is historically influential, relying solely on starting slot exhibits fundamental domain deficiencies:

1. **Failure to Model Aerodynamic & Engine Upgrades:** In modern Formula 1, cars receive major aerodynamic package upgrades every 3 to 5 races. A driver qualifying 3rd in an upgraded McLaren or Red Bull often possesses vastly superior race-pace degradation compared to a driver qualifying 1st on low fuel in a car with severe tire wear.
2. **Ignoring Track Specialization:** Certain drivers display track affinity (e.g., Lewis Hamilton at Silverstone, Max Verstappen at Spa-Francorchamps, Fernando Alonso at Monaco) that consistently overcomes marginal car deficits.
3. **The Unconstrained Probability Paradox:** Standard binary classifiers predict independent probabilities $\hat{p}_i \in [0, 1]$ for each driver. Across a 20-car grid, this frequently generates scenarios where three drivers all have predicted probabilities $> 50\%$, or where the sum of probabilities across the grid is $1.85$, violating the physical domain invariant that **strictly one driver can win a Grand Prix**.

---

## 2. Proposed Technical Innovation

We implement a four-pillar innovation architecture:

### Pillar 1: Leakage-Safe Multi-Horizon Rolling Momentum
Instead of static season averages, we construct moving windows that update dynamically across time while strictly enforcing the $t-1$ boundary:
- **Driver Short-Term Form (`driver_rolling_finish_5`):** 5-race exponential finish average capturing recent driving confidence and setup breakthroughs.
- **Constructor Medium-Term Form (`constructor_rolling_finish_10`):** 10-entry rolling finish average across both team cars, isolating factory engineering performance from single-driver anomalies.

### Pillar 2: Track Affinity Memory
- **Circuit Experience (`circuit_experience`):** Cumulative starts at the venue.
- **Circuit Win Rate (`circuit_win_rate`):** Historical win conversion rate at this specific circuit prior to the current season.

### Pillar 3: Intra-Team Teammate Relational Signal
- **`ahead_of_teammate_grid`:** Denotes whether a driver defeated their garage teammate in Saturday qualifying. Because teammates drive identical machinery under identical engine modes, out-qualifying a teammate isolates driver execution from vehicle package dominance.

### Pillar 4: Mutually Exclusive Group-Softmax Calibration Layer
To resolve the unconstrained probability paradox, the model serving layer introduces a temperature-scaled group softmax across the active grid:
$$P(\text{Driver } i \text{ Wins} \mid \text{Race } R) = \frac{\exp\left( \frac{\text{logit}_i}{T} \right)}{\sum_{k \in \text{Grid}_R} \exp\left( \frac{\text{logit}_k}{T} \right)}$$
Enforcing:
$$\sum_{i \in \text{Grid}_R} P(\text{Driver } i \text{ Wins}) = 1.0000 \quad \forall R$$

---

## 3. Experimental Design & Hypotheses

- **Control Baseline:** Logistic Regression trained exclusively on `grid_position` on 1994–2021 data.
- **Experimental Treatment:** Extreme Gradient Boosted Trees (XGBoost) trained with the 16 multi-horizon innovation features, cost-sensitive weight (`scale_pos_weight=15`), and group softmax calibration on the identical 1994–2021 training set.
- **Evaluation Benchmark:** Out-of-sample holdout on the modern Ground-Effect regulatory era (2022–2024, 68 Grands Prix, 1,359 entries).
- **Hypothesis:** The innovation will yield statistically significant gains in ROC-AUC ($> +0.03$), PR-AUC ($> +0.15$), and Top-1 race winner accuracy ($> +5\%$) on unseen Grands Prix.
