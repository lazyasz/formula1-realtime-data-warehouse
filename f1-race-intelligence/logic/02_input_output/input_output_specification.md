# Input / Output Specification (Signal Taxonomy)

## 1. Real Input Features Specification

The machine learning models operate on a pre-race feature vector of **16 predictive continuous and discrete signals** available strictly before the race start:

| # | Feature Name | Data Type | Permissible Range | Domain Meaning & Information Timing |
|---|---|---|---|---|
| 1 | `grid_position` | Integer | $1 \le x \le 20$ | Official starting slot after Saturday qualifying and FIA grid penalties. |
| 2 | `driver_rolling_finish_5` | Float | $1.0 \le x \le 24.0$ | Driver average finish position across the prior 5 races. |
| 3 | `driver_rolling_points_5` | Float | $0.0 \le x \le 26.0$ | Driver average championship points scored across the prior 5 races. |
| 4 | `constructor_rolling_finish_10` | Float | $1.0 \le x \le 24.0$ | Constructor team average finish position across the prior 10 race entries. |
| 5 | `constructor_rolling_points_10` | Float | $0.0 \le x \le 44.0$ | Constructor team average points across the prior 10 race entries. |
| 6 | `circuit_avg_finish` | Float | $1.0 \le x \le 24.0$ | Driver historical average finish position at this specific circuit. |
| 7 | `circuit_win_rate` | Float | $0.0 \le x \le 1.0$ | Driver historical career win rate at this specific circuit. |
| 8 | `circuit_podium_rate` | Float | $0.0 \le x \le 1.0$ | Driver historical career podium rate at this specific circuit. |
| 9 | `circuit_experience` | Integer | $x \ge 0$ | Total number of prior Grands Prix driven at this specific track. |
| 10 | `season_points_before` | Float | $x \ge 0.0$ | Driver points accumulated in current season entering this round. |
| 11 | `career_starts` | Integer | $x \ge 0$ | Cumulative career starts prior to this race. |
| 12 | `career_win_rate` | Float | $0.0 \le x \le 1.0$ | Historical win percentage across all career starts. |
| 13 | `career_dnf_rate` | Float | $0.0 \le x \le 1.0$ | Historical DNF retirement percentage across all career starts. |
| 14 | `ahead_of_teammate_grid` | Binary | $x \in \{0, 1\}$ | 1 if driver outqualified their teammate, 0 otherwise. |
| 15 | `driver_age` | Float | $17.0 \le x \le 55.0$ | Driver age in years at date of Grand Prix. |
| 16 | `grid_vs_form_gap` | Float | $-20.0 \le x \le 20.0$ | Delta between starting grid position and 5-race rolling form. |

## 2. Prediction Targets & Output Format

### Supported Classification Outputs:
1. **Primary Binary Output (`predicted_win` $\in \{0, 1\}$)**:
   * **Winner Class (1)**: Assigned to the single driver with the maximum predicted win probability in that Grand Prix (enforcing exactly 1 winner per race via argmax).
   * **Non-Winner Class (0)**: Assigned to the remaining 19 drivers on the starting grid.
2. **Calibrated Win Probability ($P_{\text{win}} \in [0.0, 1.0]$)**:
   * Calibrated probability normalized across the grid using temperature-scaled group softmax:
     $$\sum_{i=1}^{M_j} P(\text{Win}_i \mid \text{Race } j) = 1.00$$
3. **Multi-Target Extensions**:
   * `predicted_podium` ($P_{\text{podium}} \in [0.0, 1.0]$): Odds of finishing in top 3.
   * `predicted_points` ($P_{\text{points}} \in [0.0, 1.0]$): Odds of finishing in top 10.

### Secondary Regression Output:
* **`predicted_finish_position` ($\hat{y} \in [1.0, 24.0]$)**:
  * Continuous expected finish position produced by an independent Random Forest Regressor (MAE: 3.30 positions).

## 3. Prediction Assumptions & Information Boundaries

1. **Pre-Race Information Boundary**:
   * All inputs reflect state at $T_0$ (pit lane open, 30 minutes before race start).
   * Weather forecasts, track temperature, and official starting grids are finalized.
2. **Absence of In-Race Leakage**:
   * In-race pit stop lap numbers, safety car deployments, mid-race retirements, and race fastest lap times are strictly excluded from pre-race inference.
3. **Exclusivity Constraint**:
   * While multiple drivers may have high probabilities, exactly one driver can win a race. The serving layer converts logits into mutually exclusive probabilities via race-level softmax.
