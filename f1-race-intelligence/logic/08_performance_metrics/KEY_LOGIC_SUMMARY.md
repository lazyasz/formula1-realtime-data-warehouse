# 08. Performance Metrics: Key Logic & Core Summary

## 1. Empirical Partition Performance (Train vs. Val vs. Test)

| Partition | Seasons & Entrants | ROC-AUC | PR-AUC | Accuracy | Winner Recall | Brier Score | Top-1 Winner Hit |
|---|---|---:|---:|---:|---:|---:|---:|
| **Train** | 1994–2021 (10,999 rows) | 0.9733 | 0.6139 | 91.25% | 93.71% | 0.0626 | 58.7% (299/509) |
| **Validation** | 2022 (440 rows, 22 GPs) | 0.9581 | 0.5313 | 89.55% | 81.82% | 0.0702 | 50.0% (11/22) |
| **Test** | 2023–2024 (919 rows, 46 GPs) | 0.9659 | 0.6307 | 90.53% | 80.43% | 0.0645 | 60.9% (28/46) |
| **Combined Holdout**| **2022–2024 (1,359 rows, 68 GPs)**| **0.9635** | **0.6009** | **90.21%** | **80.88%** | **0.0663** | **57.4% (39/68)** |

## 2. Confusion Matrix & Per-Class Trade-Off (68 Holdout GPs)

| | Predicted Non-Winner (0) | Predicted Winner (1) | Total Actual |
|---|---:|---:|---:|
| **Actual Non-Winner (0)** | **1,171 (TN)** | 120 (FP) | 1,291 |
| **Actual Winner (1)** | 13 (FN) | **55 (TP)** | 68 |

- **Winner Recall (80.88% = 55/68):** Captures over 4 out of 5 true race winners.
- **Winner Precision (31.43% = 55/175):** Multiple genuine contenders cross binary threshold before group softmax normalization.
- **Top-1 Winner Hit Rate:** **57.35% (39/68 GPs)** assigned to exact race winner.
- **Top-3 Podium Winner Presence:** **88.24% (60/68 GPs)**.

## 3. Minimal Metrics Calculation Logic
```python
from sklearn.metrics import roc_auc_score, precision_recall_curve, auc, confusion_matrix, brier_score_loss

# Binary entry metrics
roc_auc = roc_auc_score(y_test, probs)
precision, recall, _ = precision_recall_curve(y_test, probs)
pr_auc = auc(recall, precision)
brier = brier_score_loss(y_test, probs)
tn, fp, fn, tp = confusion_matrix(y_test, (probs >= 0.5).astype(int)).ravel()

# Group race-level top-1 hit rate
top1_hits = test_df.groupby("race_id").apply(
    lambda g: g.loc[g["win_prob"].idxmax(), "target_is_win"]
).sum()
top1_rate = top1_hits / test_df["race_id"].nunique()

print(f"ROC-AUC: {roc_auc:.4f} | PR-AUC: {pr_auc:.4f} | Top-1: {top1_rate*100:.1f}%")
```
