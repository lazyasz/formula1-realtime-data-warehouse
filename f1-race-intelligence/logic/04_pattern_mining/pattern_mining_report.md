# 04. Pattern Mining Report: Apriori vs. FP-Growth

## 1. Executive Summary

This report documents the empirical association rule mining evaluation on the complete 1994–2024 Formula 1 dataset (12,358 transactions across 577 Grands Prix) with 24 discretized items. Both **Apriori** and **FP-Growth** were executed using identical parameters:
- Minimum Support Threshold: $0.02$ ($2.0\%$ of all race entries $\approx 247$ entries)
- Minimum Confidence Threshold: $0.25$ ($25.0\%$)

---

## 2. Algorithm Execution & Benchmark Comparison

| Metric | Apriori Algorithm | FP-Growth Algorithm | Comparison / Validation |
|---|---|---|---|
| **Data Structure** | Hash tree candidate generation ($k$-itemsets) | Compact FP-Tree (prefix tree) | Algorithmic Paradigm |
| **Passes over Dataset** | Multiple iterations ($k$ passes) | Exactly 2 scans | I/O Complexity |
| **Execution Runtime (s)** | 0.0730 s | 0.2304 s | Small item vocabulary (24 items) |
| **Frequent Itemsets Found** | 414 itemsets | 414 itemsets | **100% Identical (Verified)** |
| **Association Rules Generated** | 1,393 rules | 1,393 rules | **100% Identical (Verified)** |
| **Mathematical Equivalence** | Baseline | Matched Apriori bitwise | Equivalence Check: PASSED |

### Observations on Runtime
For dense matrices with very small vocabulary sizes ($N=24$ symbolic items), candidate generation overhead in Apriori is minimal because $k \le 5$. FP-Growth constructs the header table and recursive conditional FP-trees; on large transaction alphabets ($N > 1,000$), FP-Growth demonstrates order-of-magnitude speedups over Apriori. In our domain, both execute in sub-second time while yielding mathematically identical results.

---

## 3. Discovered High-Lift Association Rules

Association rules are exported in [association_rules.csv](file:///C:/Users/dhruv/.gemini/antigravity-ide/scratch/f1_dw/f1-race-intelligence/04_pattern_mining/association_rules.csv). Below are key domain-validated patterns discovered in the historical data:

### Top Rules Predicting Race Winners (`Outcome_Winner`)

| Antecedent (Conditions) | Consequent | Support | Confidence | Lift | Interpretation |
|---|---|---:|---:|---:|---|
| `{Grid_Pole_P1, Outcome_Podium}` | `{Beat_Teammate_In_Quali, Outcome_Winner}` | 0.0224 | 0.6427 | **17.19x** | Pole-sitters who achieve a podium win the race 64.3% of the time, exceeding random chance by 17.2x. |
| `{Grid_Pole_P1, Outcome_Podium, Outcome_Points}` | `{Beat_Teammate_In_Quali, Outcome_Winner}` | 0.0224 | 0.6427 | **17.19x** | Confluence of pole position and finishing integrity strongly associates with victory. |
| `{Driver_Form_Elite_P1_P3, Grid_Pole_P1}` | `{Outcome_Winner}` | 0.0205 | 0.5284 | **11.31x** | Elite rolling form (rolling average $\le 3.0$) combined with Pole position yields a 52.8% win conversion rate. |
| `{Grid_Pole_P1, Team_Form_Elite_Top4}` | `{Outcome_Winner}` | 0.0218 | 0.4912 | **10.51x** | Top-tier constructor rolling form combined with pole yields nearly 50% win probability. |

### Top Rules for Race Podiums (`Outcome_Podium`)

| Antecedent | Consequent | Support | Confidence | Lift | Interpretation |
|---|---|---:|---:|---:|---|
| `{Grid_FrontRow_P2, Team_Form_Elite_Top4}` | `{Outcome_Podium}` | 0.0312 | 0.7241 | **5.17x** | Front-row start in an elite car converts to a podium finish 72.4% of the time. |
| `{Grid_Top4, Driver_Form_Elite_P1_P3}` | `{Outcome_Podium}` | 0.0456 | 0.6890 | **4.92x** | Elite drivers starting in the top 4 convert to a podium in 68.9% of races. |

### Top Rules for Race Retirements (`Outcome_DNF`)

| Antecedent | Consequent | Support | Confidence | Lift | Interpretation |
|---|---|---:|---:|---:|---|
| `{Grid_Backmarker, Team_Midfield_Customer}` | `{Outcome_DNF}` | 0.1245 | 0.3852 | **1.37x** | Backmarkers in customer machinery experience disproportionate retirement rates (~38.5%). |

---

## 4. Methodological Conclusion

1. **Verification of Equivalence:** Both Apriori and FP-Growth confirmed discovery of identical frequent itemsets (414 itemsets) at $\text{min\_support} = 0.02$.
2. **Empirical Validation:** Association rules empirically reflect the high leverage of pole position (`Grid_Pole_P1`), recent driver form (`Driver_Form_Elite_P1_P3`), and constructor stability (`Team_Form_Elite_Top4`).
3. **Appropriate Usage:** These rules substantiate the feature engineering choices for supervised modeling in Parameter 06 and 07, demonstrating that grid position and rolling form are the most potent signals.
