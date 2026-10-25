"""
Apriori Frequent Itemset & Association Rule Mining (Parameter 04)
=================================================================
Implements the classical level-wise candidate generation Apriori algorithm
on discretized Formula 1 Grand Prix race transactions (1994–2024).

Measures:
- Execution runtime
- Total frequent itemsets discovered
- Association rules generated (Support, Confidence, Lift)
"""

import os
import time
import pandas as pd
import numpy as np
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules

def build_race_transactions(df: pd.DataFrame) -> list:
    """Discretizes pre-race features and race outcomes into transaction itemsets."""
    transactions = []
    
    for _, row in df.iterrows():
        items = []
        
        # 1. Starting Grid Bracket
        grid = int(row.get("grid_position", 20))
        if grid == 1:
            items.append("Grid_Pole_P1")
        elif grid == 2:
            items.append("Grid_FrontRow_P2")
        elif grid <= 4:
            items.append("Grid_Top4")
        elif grid <= 10:
            items.append("Grid_Top10")
        else:
            items.append("Grid_Backmarker")
            
        # 2. Constructor Tier
        team = str(row.get("constructor_name", "")).lower()
        if "ferrari" in team:
            items.append("Team_Ferrari")
        elif "mclaren" in team:
            items.append("Team_McLaren")
        elif "williams" in team:
            items.append("Team_Williams")
        elif "red bull" in team:
            items.append("Team_RedBull")
        elif "mercedes" in team:
            items.append("Team_Mercedes")
        else:
            items.append("Team_Midfield_Customer")
            
        # 3. Driver Recent Form (5-race rolling finish)
        d_form = float(row.get("driver_rolling_finish_5", 14.0))
        if d_form <= 3.0:
            items.append("Driver_Form_Elite_P1_P3")
        elif d_form <= 6.0:
            items.append("Driver_Form_Front_P4_P6")
        elif d_form <= 10.0:
            items.append("Driver_Form_Points_P7_P10")
        else:
            items.append("Driver_Form_Midfield")

        # 4. Constructor Recent Form (10-entry rolling finish)
        c_form = float(row.get("constructor_rolling_finish_10", 12.0))
        if c_form <= 4.0:
            items.append("Team_Form_Elite_Top4")
        elif c_form <= 8.0:
            items.append("Team_Form_Competitive")

        # 5. Circuit Experience & Track Affinity
        exp = int(row.get("circuit_experience", 0))
        if exp >= 5:
            items.append("Circuit_Veteran_5Plus")
        c_win_rate = float(row.get("circuit_win_rate", 0.0))
        if c_win_rate > 0.20:
            items.append("Circuit_Prior_Multi_Winner")

        # 6. Teammate Battle
        if int(row.get("ahead_of_teammate_grid", 0)) == 1:
            items.append("Beat_Teammate_In_Quali")

        # 7. Actual Outcomes
        if int(row.get("target_is_win", 0)) == 1:
            items.append("Outcome_Winner")
        if int(row.get("target_is_podium", 0)) == 1:
            items.append("Outcome_Podium")
        if int(row.get("target_is_points", 0)) == 1:
            items.append("Outcome_Points")
        if int(row.get("target_is_dnf", 0)) == 1:
            items.append("Outcome_DNF")

        transactions.append(items)
        
    return transactions

def run_apriori_analysis(min_support=0.02, min_confidence=0.25):
    print("=" * 80)
    print("   PARAMETER 04: APRIORI ASSOCIATION MINING ANALYSIS")
    print("=" * 80)

    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv")
    if not os.path.exists(data_path):
        data_path = os.path.join(os.path.dirname(__file__), "..", "..", "F1_RACE_LAB_FEATURES_1994_2024.csv")
    
    df = pd.read_csv(data_path, low_memory=False)
    print(f"[+] Loaded {len(df):,} race records.")
    
    transactions = build_race_transactions(df)
    print(f"[+] Discretized into {len(transactions):,} transaction itemsets.")

    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    encoded_df = pd.DataFrame(te_ary, columns=te.columns_)
    print(f"[+] Binary Transaction Matrix shape: {encoded_df.shape} ({encoded_df.shape[1]} unique items).")

    # Benchmark Apriori
    print(f"\n[*] Executing Apriori (min_support={min_support})...")
    t0 = time.perf_counter()
    apriori_itemsets = apriori(encoded_df, min_support=min_support, use_colnames=True)
    t_elapsed = time.perf_counter() - t0
    print(f"[+] Apriori completed in {t_elapsed:.4f} seconds.")
    print(f"[+] Frequent Itemsets Found: {len(apriori_itemsets):,}")

    # Generate Rules
    rules = association_rules(apriori_itemsets, metric="confidence", min_threshold=min_confidence)
    rules["antecedents_str"] = rules["antecedents"].apply(lambda x: ", ".join(sorted(list(x))))
    rules["consequents_str"] = rules["consequents"].apply(lambda x: ", ".join(sorted(list(x))))
    print(f"[+] Total Association Rules generated: {len(rules):,}")

    # Top rules leading to Outcome_Winner
    winner_rules = rules[rules["consequents_str"].str.contains("Outcome_Winner", na=False)].sort_values(by="lift", ascending=False)
    print(f"[+] Rules predicting 'Outcome_Winner': {len(winner_rules):,}")
    if len(winner_rules) > 0:
        print("\n--- TOP 3 RULES FOR RACE WINNER ---")
        for i, (_, r) in enumerate(winner_rules.head(3).iterrows(), 1):
            print(f"  {i}. {{{r['antecedents_str']}}} -> {{{r['consequents_str']}}} | Conf: {r['confidence']:.2f} | Lift: {r['lift']:.2f}x | Supp: {r['support']:.3f}")

    return {
        "algorithm": "Apriori",
        "runtime_sec": round(t_elapsed, 4),
        "total_itemsets": len(apriori_itemsets),
        "total_rules": len(rules)
    }

if __name__ == "__main__":
    run_apriori_analysis()
