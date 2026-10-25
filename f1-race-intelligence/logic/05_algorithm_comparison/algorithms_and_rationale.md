# 05. Classification Algorithms & Theoretical Rationale

## 1. Overview of Evaluated Model Families

Formula 1 race winner classification is characterized by:
- **Severe Class Imbalance:** Exactly 1 winner out of 20 to 24 drivers per Grand Prix (~$4.67\%$ positive class prevalence, 20.42:1 negative-to-positive ratio).
- **Non-Linear Feature Interactions:** Starting grid position interacts strongly with constructor aerodynamic pace, tire degradation characteristics, and driver rolling form.
- **Strict Information Temporality:** Feature values evolve continuously across calendar rounds; model training must strictly respect $T_{\text{train}} < T_{\text{test}}$ to prevent look-ahead leakage.

To systematically evaluate suitability, 7 distinct classification architectures representing distinct inductive biases were benchmarked:

---

## 2. Model Formulations & Inductive Biases

### 1. Dummy Classifier (Baseline Control)
- **Role:** Empirical control floor to establish minimum performance under stochastic assignment.
- **Mechanism:** Uniform prior distribution over classes ($P(Y=1) = 0.50$).
- **Theoretical Flaw:** Ignores all qualifying positions, car characteristics, and driver telemetry. Yields $\text{ROC-AUC} \approx 0.5000$.

### 2. Baseline Logistic Regression (Grid Position Only)
- **Role:** Monolithic linear baseline reflecting the historic motorsport adage: *"The driver on pole position wins the race."*
- **Mathematical Form:**
  $$P(\text{Win} \mid x) = \sigma(w_0 + w_1 \cdot \text{grid\_position})$$
- **Limitations:** Incapable of modeling overtaking dynamics, mechanical retirements, weather perturbations, or team dominance cycles. Performs poorly when backmarker anomalies or wet qualifying sessions jumble the grid.

### 3. Decision Tree Classifier (CART)
- **Role:** Transparent single-estimator non-linear baseline.
- **Mechanism:** Recursive binary splitting using Gini impurity or Shannon entropy, with maximum tree depth capped at 5 and class weighting applied.
- **Limitations:** Highly prone to high variance and step-function decision boundaries; sensitive to small perturbations in training splits.

### 4. Random Forest Classifier (Bagging Ensemble)
- **Role:** Variance-reduction ensemble combining 150 de-correlated CART trees.
- **Mechanism:** Bootstrap aggregating (bagging) with random feature subspace sampling ($m = \sqrt{p}$) at each node split. Incorporates inverse class frequency weights:
  $$w_c = \frac{N}{2 \cdot N_c}$$
- **Strengths:** Robust against overfitting, captures multi-feature interactions (e.g., Grid $\times$ Constructor rolling points), and provides out-of-bag feature importance estimates.

### 5. Gradient Boosting Classifier (GBDT)
- **Role:** Sequential additive boosting ensemble.
- **Mechanism:** Greedily fits shallow decision trees (depth 3) to the negative pseudo-gradients of the binomial log-likelihood loss:
  $$F_m(x) = F_{m-1}(x) + \gamma_m h_m(x)$$
- **Strengths:** High capacity to correct residuals from previous estimators, generating steep decision surfaces around grid slots 1 through 3.

### 6. LightGBM Classifier
- **Role:** Scalable gradient boosting optimized for leaf-wise tree growth.
- **Mechanism:** Leaf-wise (best-first) tree expansion with Gradient-based One-Side Sampling (GOSS) and Exclusive Feature Bundling (EFB). Uses `is_unbalance=True` to adapt loss gradients for race winner sparsity.
- **Strengths:** Ultra-low inference latency, efficient memory footprint, and strong calibration.

### 7. XGBoost Classifier (Selected Champion)
- **Role:** Regularized extreme gradient boosting algorithm.
- **Objective Function:**
  $$\mathcal{L}^{(t)} = \sum_{i=1}^n l\left(y_i, \hat{y}_i^{(t-1)} + f_t(x_i)\right) + \Omega(f_t)$$
  $$\Omega(f) = \gamma T + \frac{1}{2} \lambda \sum_{j=1}^T w_j^2$$
- **Strengths for Motorsport Classification:**
  - **Second-Order Taylor Approximation:** Utilizes analytical first ($g_i$) and second ($h_i$) order gradients for precise Newton descent steps.
  - **Explicit $L_2$ Leaf Regularization ($\lambda$):** Prevents leaf weight saturation on dominant eras (e.g., Schumacher 2002/2004, Hamilton 2014–2020, Verstappen 2022–2023).
  - **Cost-Sensitive Weighting:** `scale_pos_weight=15` effectively counters the 20:1 imbalance without artificial SMOTE synthesis.

---

## 3. Justification for Champion Architecture Selection

XGBoost Classifier was selected as the operational champion for deployment based on three critical empirical criteria:

1. **Discriminative Capacity:** Achieves the highest ROC-AUC on unseen ground-effect era test races ($0.9635$), outperforming the linear baseline ($0.9198$) by $+4.37$ AUC points and Decision Trees ($0.9177$) by $+4.58$ AUC points.
2. **Race-Level Top-1 Winner Precision:** Successfully identifies the exact race winner in **54.4% (37/68)** of unseen Grands Prix across 2022–2024, placing the true winner in the Top-3 predictions in **88.2% (60/68)** of Grands Prix.
3. **Probability Calibration:** Maintains a low Brier score loss ($0.0678$), ensuring that predicted probabilities can be accurately mapped to calibrated race-day odds.
