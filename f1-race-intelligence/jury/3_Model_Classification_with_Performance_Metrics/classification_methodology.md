# 06. Classification Methodology & End-to-End Pipeline

## 1. System Pipeline Overview

The complete machine learning classification system executes in six discrete phases:

```
Historical Dataset (1994–2024, 12,358 entries)
  │
  ▼
Temporal Filtering & Partitioning (Train: 1994–2021 | Holdout: 2022–2024)
  │
  ▼
Leakage-Safe Feature Engineering (16 Continuous & Discrete Signals)
  │
  ▼
Cost-Sensitive Gradient Boosted Training (XGBoost, scale_pos_weight=15)
  │
  ▼
Inference & Post-Processing (Temperature-Scaled Race-Level Group Softmax)
  │
  ▼
Serving Output (Rankings, Calibrated Win Probabilities, Top-1 Predicted Winner)
```

---

## 2. Feature Preprocessing & Engineering Specifications

Every feature $x_t$ at race round $t$ is strictly restricted to events occurring at rounds $\tau < t$:

1. **Driver 5-Race Rolling Finish Form (`driver_rolling_finish_5`):**
   $$\text{Form}_i(t) = \frac{1}{K} \sum_{k=1}^K \text{finish\_position}_i(t-k), \quad K = \min(5, \text{prior\_races})$$
   Smooths out single-race mechanical retirements while capturing recent momentum.
2. **Constructor 10-Entry Rolling Finish Form (`constructor_rolling_finish_10`):**
   Averaged across both team cars over the preceding 5 Grand Prix weekends (10 starts). Captures factory aerodynamic updates and power unit reliability.
3. **Track Affinity Indices (`circuit_win_rate`, `circuit_podium_rate`):**
   Historical win and podium frequency of driver $i$ at circuit $c$ prior to year $y$:
   $$\text{WinRate}_{i,c}(y) = \frac{\sum_{\tau < y} \mathbf{1}(\text{win}_{i,c,\tau})}{\sum_{\tau < y} \mathbf{1}(\text{start}_{i,c,\tau})}$$
4. **Intra-Team Qualifying Flag (`ahead_of_teammate_grid`):**
   Binary indicator denoting if a driver qualified ahead of their direct teammate in identical machinery. Isolates driver skill from constructor package performance.
5. **Grid vs. Form Divergence (`grid_vs_form_gap`):**
   $$\Delta_{\text{grid-form}} = \text{grid\_position} - \text{driver\_rolling\_finish\_5}$$
   Negative values indicate an over-performing qualifying lap relative to baseline race pace (e.g., low-fuel single-lap specialist).

---

## 3. Loss Function & Cost-Sensitive Weighting

Because Formula 1 race winners represent only $4.67\%$ of entries (1 in $\approx 21.4$ entries), standard cross-entropy loss suffers from severe majority-class bias. We formulate the objective with cost-sensitive positive weighting:

$$\mathcal{L}(\theta) = -\sum_{i=1}^N \left[ w \cdot y_i \log \hat{p}_i + (1 - y_i) \log (1 - \hat{p}_i) \right] + \gamma T + \frac{1}{2} \lambda \sum_{j=1}^T w_j^2$$

Where:
- $w = \text{scale\_pos\_weight} = 15.0$ (penalizing false negatives 15x more than false positives)
- $\lambda = 1.0$ ($L_2$ regularization on leaf weights)
- Maximum tree depth: $4$ (prevents deep co-adapted splits)
- Subsample ratio: $0.85$ (stochastic row bagging per tree)

---

## 4. Race-Level Group Softmax & Calibrated Serving

In production inference, individual independent probabilities $\hat{p}_i$ from tree ensembles do not sum to $1.0$ across the starting grid. To satisfy the physical reality that **exactly one driver wins each Grand Prix**, the serving engine passes the raw predicted logits through a temperature-scaled group softmax:

$$\hat{z}_i = \ln \left( \frac{\hat{p}_i}{1 - \hat{p}_i + \epsilon} \right)$$
$$P(\text{Driver } i \text{ Wins} \mid \text{Race } R) = \frac{\exp\left( \hat{z}_i / T \right)}{\sum_{k \in \text{Grid}_R} \exp\left( \hat{z}_k / T \right)}$$

Where temperature $T = 0.8$ sharpens probability mass toward the highest-probability contenders while maintaining smooth odds across podium challengers.
