# 05. Algorithm Comparison & Validation: Key Logic & Core Summary

## 1. Experimental Protocol & Invariants
- **Universe:** 12,358 entries (577 Grands Prix, 1994–2024).
- **Chronological Split:** Train on 1994–2021 (10,999 rows); Test on 2022–2024 Ground-Effect era (1,359 rows, 68 GPs).
- **Temporal Invariant:** $\max(T_{\text{train}}) = 2021 < \min(T_{\text{test}}) = 2022$. No random k-fold shuffling.

## 2. Benchmark of 7 Model Families (Held-out Test 2022–2024)

| Model Architecture | ROC-AUC | PR-AUC | Balanced Acc | Top-1 Winner Hit (68 GPs) | Top-3 Winner Hit | Inference Latency |
|---|---:|---:|---:|---:|---:|---:|
| **1. Dummy Classifier** | 0.5000 | 0.0500 | 49.28% | 33.8% (23/68) | 76.5% | 0.21 ms |
| **2. Logistic Reg (Grid-Only)** | 0.9198 | 0.3994 | 50.00% | 51.5% (35/68) | 83.8% | 0.38 ms |
| **3. Decision Tree (Depth 5)** | 0.9177 | 0.4715 | 84.75% | 52.9% (36/68) | 76.5% | 0.42 ms |
| **4. Random Forest** | 0.9561 | 0.5866 | 88.19% | 51.5% (35/68) | 86.8% | 14.28 ms |
| **5. Gradient Boosting (GBDT)** | 0.9622 | 0.5994 | 70.20% | 52.9% (36/68) | 86.8% | 3.12 ms |
| **6. LightGBM** | 0.9586 | 0.6152 | 86.02% | 51.5% (35/68) | 83.8% | 4.85 ms |
| **7. XGBoost (Champion)** | **0.9635** | **0.6029** | **86.45%** | **54.4% (37/68)** | **88.2%** | 5.64 ms |

## 3. 6-Fold Expanding-Window Validation
Tested across shifting regulatory periods with zero future leakage:
- **Folds:** 2019 (0.9512), 2020 (0.9213), 2021 (0.9242), 2022 (0.9587), 2023 (0.9856), 2024 (0.9367)
- **Mean ROC-AUC:** **0.9463** | **Mean Top-1 Hit:** **54.44%**

## 4. Minimal Comparison Code Logic
```python
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier

models = {
    "LogisticRegression": LogisticRegression(max_iter=1000),
    "RandomForest": RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42),
    "XGBoost": XGBClassifier(n_estimators=100, max_depth=4, scale_pos_weight=15, random_state=42)
}

for name, clf in models.items():
    clf.fit(X_train, y_train)
    probs = clf.predict_proba(X_test)[:, 1]
    roc = roc_auc_score(y_test, probs)
    print(f"{name:<20}: ROC-AUC = {roc:.4f}")
```
