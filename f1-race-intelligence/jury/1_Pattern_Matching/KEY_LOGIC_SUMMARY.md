# 04. Pattern Mining: Key Logic & Core Summary

## 1. Paradigm Distinction: Pattern Mining vs. Classification
- **Supervised ML (05–07):** Predictive. Uses pre-race $X$ to estimate $P(\text{Win})$. Strict chronological split.
- **Association Mining (04):** Unsupervised & descriptive. Discovers co-occurrence rules $X \Rightarrow Y$ across all 12,358 race transactions without temporal separation.

## 2. Discretization & Vocabulary (24 Symbolic Tokens)
Features are bucketed into binary transaction tokens:
- **Grid:** `Grid_Pole_P1`, `Grid_FrontRow_P2`, `Grid_Top4`, `Grid_Top10`, `Grid_Backmarker`
- **Constructor:** `Team_Ferrari`, `Team_RedBull`, `Team_McLaren`, `Team_Mercedes`, etc.
- **Form:** `Driver_Form_Elite_P1_P3` (mean $\le 3.0$), `Team_Form_Elite_Top4` (mean $\le 4.0$)
- **Outcomes:** `Outcome_Winner`, `Outcome_Podium`, `Outcome_Points`, `Outcome_DNF`

## 3. Apriori vs. FP-Growth Benchmark
- Parameters: $\text{min\_support} = 0.02$ ($2.0\% \approx 247$ transactions), $\text{min\_confidence} = 0.25$ ($25\%$).

| Metric | Apriori (Candidate Generation) | FP-Growth (FP-Tree) | Status |
|---|---|---|---|
| **Data Structure** | Hash tree $k$-itemset combinations | Compact prefix tree (header table) | — |
| **Database Scans** | Multiple ($k$ passes) | Exactly 2 scans | — |
| **Itemsets Found** | 414 itemsets | 414 itemsets | **100% Identical** |
| **Rules Generated** | 1,393 rules | 1,393 rules | **100% Identical** |
| **Equivalence** | Baseline | Matched bitwise | **PASSED** |

## 4. Key Discovered Rules
1. `{Grid_Pole_P1, Outcome_Podium} => {Outcome_Winner}` $\to$ **Lift: 17.19x**, Conf: 64.3%
2. `{Driver_Form_Elite_P1_P3, Grid_Pole_P1} => {Outcome_Winner}` $\to$ **Lift: 11.31x**, Conf: 52.8%
3. `{Grid_FrontRow_P2, Team_Form_Elite_Top4} => {Outcome_Podium}` $\to$ **Lift: 5.17x**, Conf: 72.4%

## 5. Minimal Execution Code
```python
from mlxtend.frequent_patterns import apriori, fpgrowth, association_rules
import pandas as pd

# Load one-hot encoded transaction basket
df_basket = pd.read_csv("data/processed/pattern_transactions_1994_2024.csv")

# 1. FP-Growth Frequent Itemsets
frequent_itemsets = fpgrowth(df_basket, min_support=0.02, use_colnames=True)
assert len(frequent_itemsets) == 414, "Itemset count mismatch!"

# 2. Association Rules
rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.25)
rules = rules.sort_values(by="lift", ascending=False)
rules.to_csv("04_pattern_mining/association_rules.csv", index=False)
```
