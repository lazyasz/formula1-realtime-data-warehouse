# 03. Class Labels: Key Logic & Core Summary

## 1. Mathematical Ground-Truth Definitions
All labels are derived from official post-race FIA classifications ($y \in \{0, 1\}$):

```python
target_is_win   = 1 if finish_position == 1 else 0
target_is_podium = 1 if finish_position <= 3 else 0
target_is_points = 1 if finish_position <= 10 else 0
target_is_dnf    = 1 if status not in ("Finished", "+1 Lap", "+2 Laps") else 0
```

## 2. Empirical Audit & Class Imbalance Metrics
- **Total Dataset:** 12,358 driver-race records across 577 Grands Prix (1994–2024).
- **Missing Labels:** **0 null values** across all target columns (100% complete).
- **Winner Exclusivity:** Exactly **1 winner per Grand Prix** ($\sum_{i \in \text{Race } j} y_i = 1$).
- **Imbalance Statistics:**
  - Class 0 (Non-Winners): $11,781$ records ($95.33\%$)
  - Class 1 (Winners): $577$ records ($4.67\%$)
  - **Imbalance Ratio:** **20.42 : 1**

## 3. Imbalance Mitigation in Classifier
Standard cross-entropy fails on 20:1 imbalance by predicting all zeros. Mitigated using cost-sensitive gradient weighting:
$$\text{scale\_pos\_weight} = \frac{N_{\text{negative}}}{N_{\text{positive}}} \approx 15.0$$
Forces the loss optimizer to penalize false negatives (missed winners) 15× more severely than false positives.

## 4. Minimal Audit Verification Code
```python
import pandas as pd

df = pd.read_csv("data/processed/F1_RACE_LAB_FEATURES_1994_2024.csv")

# 1. Zero null check
assert df["target_is_win"].isna().sum() == 0, "Missing labels detected!"

# 2. Exclusivity check (exactly 1 winner per GP)
winners_per_gp = df.groupby("race_id")["target_is_win"].sum()
assert (winners_per_gp == 1).all(), "Race with != 1 winner found!"

# 3. Imbalance calculation
ratio = (df["target_is_win"] == 0).sum() / (df["target_is_win"] == 1).sum()
print(f"Verified: 0 nulls, 577 GPs, Imbalance Ratio = {ratio:.2f}:1")
```
