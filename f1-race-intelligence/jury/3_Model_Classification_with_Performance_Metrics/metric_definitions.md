# 08. Classification Metric Definitions & Mathematical Formulations

## 1. Overview

In Formula 1 race outcome prediction, evaluating a binary classifier on severe class imbalance ($4.67\%$ winner prevalence) requires distinct threshold-dependent and threshold-independent metrics. Standard accuracy alone is deceptive, as a degenerate classifier predicting all zeros trivially achieves $95.33\%$ accuracy while failing to identify a single race winner.

---

## 2. Mathematical Formulations

### 1. Classification Accuracy
$$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$$
Measures overall correctness across all grid entrants.

### 2. Precision (Positive Predictive Value)
$$\text{Precision} = \frac{TP}{TP + FP}$$
The probability that a driver predicted as a race winner actually won the Grand Prix. High precision minimizes false winner declarations.

### 3. Recall (Sensitivity / True Positive Rate)
$$\text{Recall} = \frac{TP}{TP + FN}$$
The proportion of actual race winners correctly identified by the model. High recall ensures the true winner is captured in the model's positive classification set.

### 4. $F_1$-Score (Harmonic Mean)
$$F_1 = 2 \cdot \frac{\text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}} = \frac{2 \cdot TP}{2 \cdot TP + FP + FN}$$
Balances precision and recall without being inflated by the large volume of true negatives ($TN$).

### 5. Area Under the Receiver Operating Characteristic Curve (ROC-AUC)
$$\text{ROC-AUC} = \int_0^1 \text{TPR}(\text{FPR}^{-1}(t)) \, dt$$
Measures ranking ability across all classification thresholds:
$$\text{TPR} = \frac{TP}{TP + FN}, \quad \text{FPR} = \frac{FP}{FP + TN}$$
Represents the probability that a randomly chosen race winner is assigned a higher predicted win probability than a randomly chosen non-winner.

### 6. Area Under the Precision-Recall Curve (PR-AUC / Average Precision)
$$\text{PR-AUC} = \sum_n (R_n - R_{n-1}) P_n$$
Crucial metric for severe class imbalance. Evaluates precision directly across the recall spectrum, completely invariant to large true-negative counts.

### 7. Log Loss (Cross-Entropy Loss)
$$\text{Log Loss} = -\frac{1}{N} \sum_{i=1}^N \left[ y_i \ln(\hat{p}_i) + (1 - y_i) \ln(1 - \hat{p}_i) \right]$$
Penalizes confident incorrect predictions exponentially.

### 8. Brier Calibration Score
$$\text{Brier Score} = \frac{1}{N} \sum_{i=1}^N (\hat{p}_i - y_i)^2$$
Mean squared error between predicted probability $\hat{p}_i \in [0, 1]$ and actual binary outcome $y_i \in \{0, 1\}$. Evaluates probabilistic calibration.

### 9. Top-1 Winner Hit Rate (Domain-Specific Ranking Metric)
$$\text{Top-1 Hit Rate} = \frac{1}{G} \sum_{g=1}^G \mathbf{1}\left( y_{\text{argmax}_{i \in \text{Grid}_g} (\hat{p}_{i,g})} == 1 \right)$$
The percentage of Grands Prix where the single driver assigned the highest predicted probability won the race.
