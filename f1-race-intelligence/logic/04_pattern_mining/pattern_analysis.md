# 04. Pattern Analysis: Unsupervised Association Mining vs. Supervised Classification

## 1. Conceptual Distinction

In this Formula 1 Race Intelligence project, **pattern matching and association rule mining** are clearly separated from **supervised classification**:

| Dimension | Supervised Classification (Parameter 05, 06, 07) | Association Rule Mining (Parameter 04: Apriori & FP-Growth) |
|---|---|---|
| **Paradigm** | Supervised learning with temporal holdout | Unsupervised pattern discovery |
| **Input Structure** | Feature vector $X \in \mathbb{R}^{d}$ for individual race entrant | Transaction itemsets $T = \{i_1, i_2, \dots, i_k\} \subseteq I$ |
| **Target Variable** | Explicit ground truth label $y \in \{0, 1\}$ (`target_is_win`) | None (discovers co-occurrences across any subset of items) |
| **Objective** | Minimize classification loss / log-loss; predict win probabilities | Discover frequent itemsets $X \Rightarrow Y$ meeting support & confidence thresholds |
| **Validation Method** | Chronological train/test split (1994–2021 train, 2022–2024 test) | Support, Confidence, Lift, Leverage on complete corpus |
| **Leakage Rule** | Post-race events strictly forbidden in feature vector | Pre-race attributes and race outcomes co-mined to extract descriptive association patterns |

> **Critical Note on Evaluation:** Association rule mining is **descriptive and exploratory**, not predictive. A rule such as $\{ \text{Grid\_Pole\_P1}, \text{Outcome\_Podium} \} \Rightarrow \{ \text{Outcome\_Winner} \}$ describes empirical correlation in historical races, but cannot replace a probabilistic classifier that predicts race outcomes using strictly pre-race inputs.

---

## 2. Transaction Itemset Construction

To apply Apriori and FP-Growth, continuous and categorical features from the 12,358 race entries (1994–2024) are discretized into a binary basket of 24 distinct symbolic items:

### Discretization Rules

1. **Starting Grid Bracket (`grid_position`):**
   - `Grid_Pole_P1`: Grid == 1 (Pole position)
   - `Grid_FrontRow_P2`: Grid == 2
   - `Grid_Top4`: Grid in [3, 4]
   - `Grid_Top10`: Grid in [5, 10]
   - `Grid_Backmarker`: Grid > 10

2. **Constructor Entity (`constructor_name`):**
   - `Team_Ferrari`, `Team_McLaren`, `Team_Williams`, `Team_RedBull`, `Team_Mercedes`, `Team_Midfield_Customer`

3. **Driver Recent Form (`driver_rolling_finish_5`):**
   - `Driver_Form_Elite_P1_P3`: Mean finish $\le 3.0$
   - `Driver_Form_Front_P4_P6`: Mean finish in $(3.0, 6.0]$
   - `Driver_Form_Points_P7_P10`: Mean finish in $(6.0, 10.0]$
   - `Driver_Form_Midfield`: Mean finish $> 10.0$

4. **Constructor Rolling Form (`constructor_rolling_finish_10`):**
   - `Team_Form_Elite_Top4`: Constructor rolling average $\le 4.0$
   - `Team_Form_Competitive`: Constructor rolling average in $(4.0, 8.0]$

5. **Track Affinity & Experience:**
   - `Circuit_Veteran_5Plus`: Prior starts at this circuit $\ge 5$
   - `Circuit_Prior_Multi_Winner`: Circuit historical win rate $> 20\%$

6. **Intra-Team Metric:**
   - `Beat_Teammate_In_Quali`: `ahead_of_teammate_grid == 1`

7. **Race Outcomes:**
   - `Outcome_Winner`: Winner (`target_is_win == 1`)
   - `Outcome_Podium`: Podium (`target_is_podium == 1`)
   - `Outcome_Points`: Points finish (`target_is_points == 1`)
   - `Outcome_DNF`: Did Not Finish (`target_is_dnf == 1`)

---

## 3. Metric Formulations

Given an association rule $X \Rightarrow Y$ where $X, Y \subseteq I$ and $X \cap Y = \emptyset$:

1. **Support:**
   $$\text{Support}(X \Rightarrow Y) = P(X \cup Y) = \frac{\sigma(X \cup Y)}{|D|}$$
   Proportion of race entries containing both itemsets $X$ and $Y$.

2. **Confidence:**
   $$\text{Confidence}(X \Rightarrow Y) = P(Y \mid X) = \frac{\text{Support}(X \cup Y)}{\text{Support}(X)}$$
   Conditional probability that itemset $Y$ occurs given that itemset $X$ is present.

3. **Lift:**
   $$\text{Lift}(X \Rightarrow Y) = \frac{P(X \cup Y)}{P(X) \cdot P(Y)} = \frac{\text{Confidence}(X \Rightarrow Y)}{\text{Support}(Y)}$$
   Measures how much more often $X$ and $Y$ occur together than would be expected if they were statistically independent. $\text{Lift} > 1.0$ indicates strong positive association.

4. **Leverage:**
   $$\text{Leverage}(X \Rightarrow Y) = \text{Support}(X \cup Y) - (\text{Support}(X) \cdot \text{Support}(Y))$$

5. **Conviction:**
   $$\text{Conviction}(X \Rightarrow Y) = \frac{1 - \text{Support}(Y)}{1 - \text{Confidence}(X \Rightarrow Y)}$$
