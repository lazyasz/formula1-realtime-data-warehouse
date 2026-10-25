"""
FP-Growth Frequent Itemset & Association Rule Mining (Parameter 04)
===================================================================
Implements the FP-Tree based FP-Growth algorithm on discretized Formula 1
Grand Prix race transactions (1994–2024).

Compares:
- Runtime performance (FP-Growth vs. Apriori)
- Mathematical equivalence of frequent itemsets
- Association rules generation (Support, Confidence, Lift)
- Exports association rules to association_rules.csv
"""

import os
import sys
import time
import pandas as pd
import numpy as np
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import fpgrowth, apriori, association_rules

# Import transaction generator from apriori_analysis
sys.path.append(os.path.dirname(__file__))
from apriori_analysis import build_race_transactions

def run_fpgrowth_analysis(min_support=0.02, min_confidence=0.25, export_csv=True):
    print("=" * 80)
    print("   PARAMETER 04: FP-GROWTH ASSOCIATION MINING & APRIORI COMPARISON")
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
    print(f"[+] Binary Transaction Matrix: {encoded_df.shape[0]} transactions x {encoded_df.shape[1]} unique items.")

    # 1. Benchmark Apriori
    print(f"\n[*] Benchmarking Apriori (min_support={min_support})...")
    t0_ap = time.perf_counter()
    ap_itemsets = apriori(encoded_df, min_support=min_support, use_colnames=True)
    t_ap = time.perf_counter() - t0_ap
    print(f"[+] Apriori runtime: {t_ap:.4f} s | Itemsets: {len(ap_itemsets):,}")

    # 2. Benchmark FP-Growth
    print(f"\n[*] Benchmarking FP-Growth (min_support={min_support})...")
    t0_fp = time.perf_counter()
    fp_itemsets = fpgrowth(encoded_df, min_support=min_support, use_colnames=True)
    t_fp = time.perf_counter() - t0_fp
    print(f"[+] FP-Growth runtime: {t_fp:.4f} s | Itemsets: {len(fp_itemsets):,}")

    speedup = (t_ap / t_fp) if t_fp > 0 else 1.0
    print(f"[+] Speedup factor: {speedup:.2f}x faster execution with FP-Growth")

    # 3. Equivalence Verification
    ap_set = set(frozenset(x) for x in ap_itemsets['itemsets'])
    fp_set = set(frozenset(x) for x in fp_itemsets['itemsets'])
    is_identical = (ap_set == fp_set)
    print(f"[+] Mathematical Itemset Equivalence Check: {'PASSED (100% Identical)' if is_identical else 'FAILED'}")

    # 4. Association Rules Generation
    rules = association_rules(fp_itemsets, metric="confidence", min_threshold=min_confidence)
    rules["antecedents_str"] = rules["antecedents"].apply(lambda x: ", ".join(sorted(list(x))))
    rules["consequents_str"] = rules["consequents"].apply(lambda x: ", ".join(sorted(list(x))))
    print(f"[+] Generated {len(rules):,} association rules (min_confidence={min_confidence}).")

    # Format for export
    export_df = rules[[
        "antecedents_str", "consequents_str", "support", "confidence", "lift", "leverage", "conviction"
    ]].rename(columns={
        "antecedents_str": "antecedents",
        "consequents_str": "consequents"
    }).sort_values(by="lift", ascending=False)

    if export_csv:
        output_csv = os.path.join(os.path.dirname(__file__), "association_rules.csv")
        export_df.to_csv(output_csv, index=False)
        print(f"[+] Exported association rules to: {output_csv}")

    # Inspect top outcome-predicting rules
    print("\n--- TOP HIGH-LIFT RULES DISCOVERED ---")
    for i, (_, r) in enumerate(export_df.head(5).iterrows(), 1):
        print(f"  {i}. {{{r['antecedents']}}} => {{{r['consequents']}}}")
        print(f"     Support: {r['support']:.4f} | Conf: {r['confidence']:.4f} | Lift: {r['lift']:.2f}x")

    winner_rules = export_df[export_df["consequents"].str.contains("Outcome_Winner", na=False)]
    if len(winner_rules) > 0:
        print("\n--- TOP RULES FOR OUTCOME_WINNER ---")
        for i, (_, r) in enumerate(winner_rules.head(3).iterrows(), 1):
            print(f"  {i}. {{{r['antecedents']}}} => {{{r['consequents']}}}")
            print(f"     Support: {r['support']:.4f} | Conf: {r['confidence']:.4f} | Lift: {r['lift']:.2f}x")

    return {
        "apriori_time": round(t_ap, 4),
        "fpgrowth_time": round(t_fp, 4),
        "speedup": round(speedup, 2),
        "itemsets_count": len(fp_itemsets),
        "rules_count": len(rules),
        "is_equivalent": is_identical
    }

if __name__ == "__main__":
    run_fpgrowth_analysis()
