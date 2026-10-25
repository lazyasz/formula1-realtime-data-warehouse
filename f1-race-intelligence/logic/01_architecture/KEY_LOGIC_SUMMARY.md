# 01. Architecture: Key Logic & Core Summary

## 1. System Pipeline at a Glance
```
Historical Data (1994–2024, 12,358 entries)
  │
  ├──> Chronological Ingestion (t₁ < t₂ ... < tₙ) — Zero lookahead
  │
  ├──> Pre-Race Feature Pipeline (16 features computed strictly at T₀ before start)
  │       │
  │       ├── [Branch A: Supervised Classification]
  │       │     ├── Train (1994–2021) ──> Cost-Sensitive XGBoost (scale_pos_weight=15)
  │       │     ├── Temporal Holdout (2022–2024: 68 GPs)
  │       │     └── Temperature-Scaled Group Softmax (∑ P(win) = 1.0 per race)
  │       │
  │       └── [Branch B: Unsupervised Pattern Mining]
  │             ├── Discretize to 24 symbolic transaction tokens
  │             └── Apriori & FP-Growth Rule Mining (min_sup=0.02, min_conf=0.25)
  │
  └──> Serving Layer: race_lab_service.py + REST API + Interactive Dashboard
```

## 2. Core Architectural Principles
1. **Temporal Isolation:** All training and validation splits follow strict chronological boundaries ($\max T_{\text{train}} = 2021 < \min T_{\text{test}} = 2022$). No randomized k-fold splits.
2. **Pre-Race Information Boundary ($T_0$):** Only data known 30 minutes before race start is admitted (grid slot, rolling form, historical track affinity). In-race data (pit strategy, safety cars, fastest lap) is strictly excluded.
3. **Decoupled Unsupervised Branch:** Pattern mining is purely exploratory/descriptive; it does not leak into supervised classification targets.

## 3. Minimal Pipeline Execution Logic
```python
# Sequential pipeline flow
df = load_and_validate_f1_data("f1_warehouse.db")
df = df.sort_values(by=["season", "round", "grid_position"]).reset_index(drop=True)

# Split strictly on time
train_df = df[df["season"] <= 2021]
test_df  = df[df["season"] >= 2022]

# Train classifier with group constraint
model = XGBClassifier(scale_pos_weight=15, max_depth=4, subsample=0.85)
model.fit(train_df[FEATURE_COLS], train_df["target_is_win"])

# Group softmax per Grand Prix
probs = model.predict_proba(test_df[FEATURE_COLS])[:, 1]
test_df["win_prob"] = test_df.groupby("race_id")["raw_prob"].transform(lambda p: np.exp(p)/np.sum(np.exp(p)))
```
