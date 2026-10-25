"""
Formula 1 Frequent Pattern Mining & Association Rule Discovery Engine
=====================================================================
Implements, executes, and benchmarks:
1. Apriori Algorithm (Level-wise Candidate Generation)
2. FP-Growth Algorithm (Frequent Pattern Tree & Conditional Pattern Bases)

Analyzes 8,650 Grand Prix race transactions across:
- Grid Position Brackets
- Car Specifications & Power Units
- Pit Stop Counts & Duration Losses
- Circuit Track Record Deltas & Speed Traps
- Championship Standing Context
- Race Outcomes (Winner, Podium, Points, DNF)

Outputs:
- f1_frequent_itemsets.csv
- f1_association_rules.csv
- Execution latency & algorithmic efficiency benchmark
"""

import time
import sqlite3
import pandas as pd
import numpy as np
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, fpgrowth, association_rules

def build_f1_transactions(df: pd.DataFrame) -> list:
    """Converts 8,650 race result records into categorical itemset transactions."""
    transactions = []

    for _, row in df.iterrows():
        items = []

        # 1. Grid Position Item
        grid = row["grid_position"]
        if grid == 1:
            items.append("Grid_P1_Pole")
        elif grid == 2:
            items.append("Grid_P2_FrontRow")
        elif grid <= 5:
            items.append("Grid_P3_P5_Top5")
        elif grid <= 10:
            items.append("Grid_P6_P10_MidfieldTop")
        elif grid <= 15:
            items.append("Grid_P11_P15_MidfieldBack")
        else:
            items.append("Grid_P16_Plus_Backmarker")

        # 2. Constructor & Power Unit Items
        team = str(row["constructor_ref"]).lower()
        if "red_bull" in team:
            items.append("Team_RedBull")
        elif "ferrari" in team:
            items.append("Team_Ferrari")
        elif "mercedes" in team:
            items.append("Team_Mercedes")
        elif "mclaren" in team:
            items.append("Team_McLaren")
        else:
            items.append("Team_Customer_or_Midfield")

        pu = str(row.get("car_power_unit_supplier", "")).lower()
        if "ferrari" in pu:
            items.append("PU_Ferrari")
        elif "mercedes" in pu:
            items.append("PU_Mercedes")
        elif "honda" in pu or "red bull" in pu:
            items.append("PU_Honda_RBPT")
        elif "renault" in pu:
            items.append("PU_Renault")

        # 3. Car Technical Specs & Power Tier
        bhp = row.get("car_estimated_power_bhp", 850)
        if bhp >= 1000:
            items.append("Car_BHP_1000Plus_Hybrid")
        elif bhp >= 900:
            items.append("Car_BHP_900_V10_Hybrid")
        else:
            items.append("Car_BHP_750_V8_Era")

        p2w = row.get("car_power_to_weight_ratio", 1.25)
        if p2w >= 1.35:
            items.append("PowerWeight_High_1.35Plus")
        else:
            items.append("PowerWeight_Standard")

        rel = row.get("car_mechanical_reliability_score", 0.9)
        if rel >= 0.95:
            items.append("Reliability_High_95Plus")

        # 4. Pit Stop Strategy Items
        stops = row.get("pit_stop_count", 2)
        if stops == 1:
            items.append("Pit_1Stop_LowLoss")
        elif stops == 2:
            items.append("Pit_2Stop_Standard")
        elif stops >= 3:
            items.append("Pit_3PlusStop_Aggressive")

        crew_score = row.get("pit_crew_efficiency_score", 80)
        if crew_score >= 93:
            items.append("PitCrew_Elite_93Plus")
        elif crew_score >= 88:
            items.append("PitCrew_UpperMid_88_92")

        # 5. Lap Record & Pace Metrics
        record_delta = row.get("driver_lap_record_delta_sec", 5.0)
        if record_delta <= 1.5:
            items.append("Pace_RecordGap_Under1.5s")
        elif record_delta <= 3.5:
            items.append("Pace_RecordGap_Under3.5s")

        quali_delta = row.get("driver_quali_to_record_delta_sec", 5.0)
        if quali_delta <= 1.0:
            items.append("Quali_RecordGap_Under1.0s")

        # 6. Championship Standing Context
        champ_pos = row.get("driver_championship_position", 10)
        if champ_pos == 1:
            items.append("Champ_Leader_P1")
        elif champ_pos <= 3:
            items.append("Champ_Top3_Contender")
        elif champ_pos <= 6:
            items.append("Champ_Top6")

        wins_in_season = row.get("driver_championship_wins", 0)
        if wins_in_season >= 3:
            items.append("Season_MultiWinner_3Plus")

        # 7. Outcome Target Items
        if row["is_win"] == 1:
            items.append("Outcome_Winner_P1")
        if row["is_podium"] == 1:
            items.append("Outcome_Podium_P1_P3")
        if row["is_top_10"] == 1:
            items.append("Outcome_Points_P1_P10")
        if row.get("is_dnf", 0) == 1:
            items.append("Outcome_DNF")

        transactions.append(items)

    return transactions

def run_pattern_mining():
    print("================================================================================")
    print("   FORMULA 1 FREQUENT PATTERN MINING: APRIORI VS. FP-GROWTH BENCHMARK")
    print("================================================================================")

    csv_path = "F1_ML_Winner_Prediction_Dataset.csv"
    df = pd.read_csv(csv_path, low_memory=False)
    print(f"[*] Loaded {len(df):,} race records.")

    # 1. Build Transactions
    print("\n[*] Converting tabular race dataset into Market Basket transactions...")
    transactions = build_f1_transactions(df)
    print(f"[+] Total Transactions Generated: {len(transactions):,}")
    print(f"[+] Sample Transaction 1: {transactions[0]}")

    # 2. One-Hot Encode Transactions
    te = TransactionEncoder()
    te_ary = te.fit(transactions).transform(transactions)
    df_encoded = pd.DataFrame(te_ary, columns=te.columns_)
    print(f"[+] One-Hot Matrix Shape: {df_encoded.shape[0]:,} transactions x {df_encoded.shape[1]} unique items")

    MIN_SUPPORT = 0.02  # 2% minimum support (173+ race entries)
    MIN_CONFIDENCE = 0.50 # 50% minimum confidence

    # 3. Run APRIORI Algorithm
    print(f"\n[*] 1. EXECUTING APRIORI ALGORITHM (min_support={MIN_SUPPORT*100:.1f}%)...")
    start_apriori = time.time()
    frequent_itemsets_apriori = apriori(df_encoded, min_support=MIN_SUPPORT, use_colnames=True)
    apriori_time = time.time() - start_apriori
    print(f"[OK] Apriori Complete: Found {len(frequent_itemsets_apriori)} frequent itemsets in {apriori_time*1000:.2f} ms")

    # 4. Run FP-GROWTH Algorithm
    print(f"\n[*] 2. EXECUTING FP-GROWTH ALGORITHM (min_support={MIN_SUPPORT*100:.1f}%)...")
    start_fpgrowth = time.time()
    frequent_itemsets_fpgrowth = fpgrowth(df_encoded, min_support=MIN_SUPPORT, use_colnames=True)
    fpgrowth_time = time.time() - start_fpgrowth
    print(f"[OK] FP-Growth Complete: Found {len(frequent_itemsets_fpgrowth)} frequent itemsets in {fpgrowth_time*1000:.2f} ms")

    speedup = apriori_time / fpgrowth_time if fpgrowth_time > 0 else 1.0
    print(f"\n[*] PERFORMANCE BENCHMARK:")
    print(f"    - Apriori Runtime   : {apriori_time*1000:.2f} ms (Requires multiple full-table candidate passes)")
    print(f"    - FP-Growth Runtime : {fpgrowth_time*1000:.2f} ms (Prefix FP-Tree node compression, 2 passes)")
    print(f"    - FP-Growth Speedup : {speedup:.2f}x FASTER")

    # 5. Extract Association Rules
    print(f"\n[*] 3. EXTRACTING ASSOCIATION RULES (min_confidence={MIN_CONFIDENCE*100:.1f}%)...")
    rules = association_rules(frequent_itemsets_fpgrowth, metric="confidence", min_threshold=MIN_CONFIDENCE)
    print(f"[+] Total Association Rules Generated: {len(rules):,}")

    # Add itemset lengths
    rules["antecedent_len"] = rules["antecedents"].apply(lambda x: len(x))
    rules["consequent_len"] = rules["consequents"].apply(lambda x: len(x))

    # Format frozenset to string
    rules["antecedent_str"] = rules["antecedents"].apply(lambda x: ", ".join(list(x)))
    rules["consequent_str"] = rules["consequents"].apply(lambda x: ", ".join(list(x)))

    # Filter for Race Outcome Rules
    winner_rules = rules[rules["consequent_str"].str.contains("Outcome_Winner_P1")].sort_values(by="lift", ascending=False)
    podium_rules = rules[rules["consequent_str"].str.contains("Outcome_Podium_P1_P3")].sort_values(by="lift", ascending=False)
    points_rules = rules[rules["consequent_str"].str.contains("Outcome_Points_P1_P10")].sort_values(by="confidence", ascending=False)
    dnf_rules = rules[rules["consequent_str"].str.contains("Outcome_DNF")].sort_values(by="lift", ascending=False)

    print("\n" + "="*95)
    print(f"{'ANTECEDENTS (IF)':<55} => {'CONSEQUENT (THEN)':<20} | {'SUPP':<6} | {'CONF':<6} | {'LIFT'}")
    print("="*95)

    print("\n[=== HIGH-CONFIDENCE RACE WINNER PATTERNS (Outcome_Winner_P1) ===]")
    for _, r in winner_rules.head(5).iterrows():
        print(f"  {r['antecedent_str']:<53} => {r['consequent_str']:<20} | {r['support']*100:>4.1f}% | {r['confidence']*100:>4.1f}% | {r['lift']:.2f}x")

    print("\n[=== HIGH-CONFIDENCE PODIUM PATTERNS (Outcome_Podium_P1_P3) ===]")
    for _, r in podium_rules.head(5).iterrows():
        print(f"  {r['antecedent_str']:<53} => {r['consequent_str']:<20} | {r['support']*100:>4.1f}% | {r['confidence']*100:>4.1f}% | {r['lift']:.2f}x")

    print("\n[=== HIGH-CONFIDENCE POINTS SCORER PATTERNS (Outcome_Points_P1_P10) ===]")
    for _, r in points_rules.head(5).iterrows():
        print(f"  {r['antecedent_str']:<53} => {r['consequent_str']:<20} | {r['support']*100:>4.1f}% | {r['confidence']*100:>4.1f}% | {r['lift']:.2f}x")

    print("\n[=== HIGH-RISK DNF / RETIREMENT PATTERNS (Outcome_DNF) ===]")
    for _, r in dnf_rules.head(5).iterrows():
        print(f"  {r['antecedent_str']:<53} => {r['consequent_str']:<20} | {r['support']*100:>4.1f}% | {r['confidence']*100:>4.1f}% | {r['lift']:.2f}x")

    print("="*95)

    # 6. Save Artifacts
    frequent_itemsets_fpgrowth["itemset_str"] = frequent_itemsets_fpgrowth["itemsets"].apply(lambda x: ", ".join(list(x)))
    frequent_itemsets_fpgrowth.to_csv("f1_frequent_itemsets.csv", index=False)
    rules.to_csv("f1_association_rules.csv", index=False)
    print("\n[OK] Saved frequent itemsets to: 'f1_frequent_itemsets.csv'")
    print("[OK] Saved association rules to: 'f1_association_rules.csv'")

    return {
        "apriori_time_ms": apriori_time * 1000,
        "fpgrowth_time_ms": fpgrowth_time * 1000,
        "speedup": speedup,
        "itemset_count": len(frequent_itemsets_fpgrowth),
        "rules_count": len(rules)
    }

if __name__ == "__main__":
    run_pattern_mining()
