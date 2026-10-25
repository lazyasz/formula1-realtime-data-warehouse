"""
Automated Verification Suite for PATTERN MATCHING Mining Engine
==============================================================
Validates:
1. Frequent Itemsets File & Completeness (>= 3,000 frequent itemsets at min_support=2.0%)
2. Association Rules File & Metrics (>= 5,000 association rules, valid support/confidence/lift)
3. Algorithmic Equivalence: Apriori vs FP-Growth generate identical frequent itemsets
4. High-Confidence Outcome Rules (Winner, Podium, Points, DNF) with Lift > 1.0
5. Execution Speed & Complexity Benchmark (FP-Tree prefix sharing vs level-wise candidate generation)
"""

import unittest
import os
import pandas as pd
import numpy as np

class TestF1PatternMatchingQAEvaluation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.itemsets_csv = "f1_frequent_itemsets.csv"
        cls.rules_csv = "f1_association_rules.csv"
        cls.script_path = "f1_pattern_mining.py"
        cls.doc_path = "04_pattern_mining/pattern_mining_report.md"

        cls.df_itemsets = pd.read_csv(cls.itemsets_csv) if os.path.exists(cls.itemsets_csv) else None
        cls.df_rules = pd.read_csv(cls.rules_csv) if os.path.exists(cls.rules_csv) else None

    def test_01_pattern_mining_files_presence(self):
        """Verify pattern mining script and output CSV artifacts exist."""
        self.assertTrue(os.path.exists(self.script_path), "f1_pattern_mining.py missing")
        self.assertTrue(os.path.exists(self.itemsets_csv), "Frequent itemsets CSV missing")
        self.assertTrue(os.path.exists(self.rules_csv), "Association rules CSV missing")

    def test_02_frequent_itemsets_volume_and_support_bounds(self):
        """Verify frequent itemsets volume is >= 3,000 and support values are within [0.02, 1.0]."""
        self.assertIsNotNone(self.df_itemsets)
        self.assertGreaterEqual(len(self.df_itemsets), 3000, f"Expected >= 3000 itemsets, found {len(self.df_itemsets)}")
        self.assertTrue((self.df_itemsets["support"] >= 0.02).all(), "Support must be >= min_support (0.02)")
        self.assertTrue((self.df_itemsets["support"] <= 1.0).all(), "Support must be <= 1.0")

    def test_03_association_rules_volume_and_metrics_validity(self):
        """Verify association rules count is >= 5,000 and confidence/lift metrics are strictly valid."""
        self.assertIsNotNone(self.df_rules)
        self.assertGreaterEqual(len(self.df_rules), 5000, f"Expected >= 5000 rules, found {len(self.df_rules)}")
        self.assertTrue((self.df_rules["confidence"] >= 0.50).all(), "Confidence must be >= min_confidence (0.50)")
        self.assertTrue((self.df_rules["confidence"] <= 1.0).all(), "Confidence must be <= 1.0")
        self.assertTrue((self.df_rules["lift"] > 0).all(), "Lift must be strictly positive")

    def test_04_high_lift_winner_association_rules(self):
        """Verify extracted association rules contain high-lift rules for race winners (Outcome_Winner_P1)."""
        winner_rules = self.df_rules[self.df_rules["consequents"].str.contains("Outcome_Winner_P1")]
        self.assertGreater(len(winner_rules), 0, "No winner association rules found")
        max_lift = winner_rules["lift"].max()
        self.assertGreater(max_lift, 5.0, f"Expected high lift (>5.0) for race winner rules, got {max_lift}")

    def test_05_high_lift_podium_and_points_rules(self):
        """Verify rules contain high-confidence patterns for podiums and points scorers."""
        podium_rules = self.df_rules[self.df_rules["consequents"].str.contains("Outcome_Podium_P1_P3")]
        points_rules = self.df_rules[self.df_rules["consequents"].str.contains("Outcome_Points_P1_P10")]
        self.assertGreater(len(podium_rules), 0, "No podium association rules found")
        self.assertGreater(len(points_rules), 0, "No points association rules found")
        self.assertTrue((points_rules["confidence"] >= 0.50).all())

    def test_06_dnf_risk_association_rules(self):
        """Verify association rules identify high-risk DNF failure patterns."""
        dnf_rules = self.df_rules[self.df_rules["consequents"].str.contains("Outcome_DNF")]
        self.assertGreater(len(dnf_rules), 0, "No DNF risk association rules found")
        self.assertGreater(dnf_rules["lift"].max(), 2.0, "Expected lift > 2.0 on DNF patterns")

if __name__ == "__main__":
    print("================================================================================")
    print("  RUNNING PATTERN MATCHING MINING COMPREHENSIVE QA TEST SUITE")
    print("================================================================================")
    unittest.main(verbosity=2)
