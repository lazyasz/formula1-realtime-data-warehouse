# 06. Classification Algorithm: Key Logic & Core Summary

## 1. Production Champion Architecture: XGBoost
- **Algorithm:** Extreme Gradient Boosted Trees (`XGBClassifier`)
- **Hyperparameters:** `n_estimators=120`, `max_depth=4`, `learning_rate=0.05`, `subsample=0.85`, `colsample_bytree=0.80`, `reg_lambda=1.0`.
- **Cost-Sensitive Loss:** `scale_pos_weight=15.0` to overcome 20.4:1 non-winner to winner class imbalance.
$$\mathcal{L}(\theta) = -\sum_{i=1}^N \left[ 15 \cdot y_i \log \hat{p}_i + (1 - y_i) \log(1 - \hat{p}_i) \right] + \Omega(\text{trees})$$

## 2. In-Race Group Softmax Normalization
Raw per-driver sigmoid probabilities do not sum to 1 within a race. A temperature-scaled group softmax layer converts raw logits into mutually exclusive race probabilities:

$$P(\text{Win}_i \mid \text{Race } j) = \frac{\exp(\hat{z}_i / T)}{\sum_{k \in \text{Race } j} \exp(\hat{z}_k / T)}, \quad T = 1.0$$

Ensures:
1. $\sum_{i \in \text{Race } j} P(\text{Win}_i) = 1.0000$ (Exclusivity constraint)
2. $\text{Predicted Winner} = \arg\max_{i} P(\text{Win}_i \mid \text{Race } j)$

## 3. Minimal Production Training & Persistence Code
```python
import joblib, numpy as np
from xgboost import XGBClassifier

# 1. Fit Cost-Sensitive Champion
champion = XGBClassifier(
    n_estimators=120, max_depth=4, learning_rate=0.05,
    scale_pos_weight=15.0, subsample=0.85, random_state=42
)
champion.fit(X_train, y_train)

# 2. Serialize Pipeline Artifacts
joblib.dump(champion, "models/champion_xgboost_classifier.joblib")

# 3. Group Softmax Inference Function
def predict_race_probabilities(race_df, model, feature_cols, temp=1.0):
    logits = model.predict(race_df[feature_cols], output_margin=True)
    exp_logits = np.exp(logits / temp)
    race_df["win_prob"] = exp_logits / np.sum(exp_logits)
    race_df["predicted_win"] = (race_df["win_prob"] == race_df["win_prob"].max()).astype(int)
    return race_df.sort_values(by="win_prob", ascending=False)
```
