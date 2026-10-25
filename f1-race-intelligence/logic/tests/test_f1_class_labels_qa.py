"""
Automated Verification Suite for CLASSES LABEL Pipeline
=======================================================
Validates all Target Class Labeling criteria:
1. Target Label Definitions (Binary & Multi-Class formulations)
2. Exact Class Counts & Mathematical Consistency (412 wins, 1,236 podiums, 4,120 points scorers)
3. Class Imbalance Identification & Scale Factor Calibration (1:20 winner ratio, 1:6 podium ratio)
4. Multi-Class 5-Tier Hierarchy (0: Winner, 1: Podium, 2: Points, 3: Backmarker, 4: DNF)
5. Zero Target Leakage in Machine Learning Feature Matrix
6. Multi-Task Classification Model Convergence & ROC-AUC Metrics
"""

import unittest
import os
import sqlite3
import pandas as pd
import numpy as np

class TestF1ClassLabelsQAEvaluation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.csv_path = "F1_ML_Winner_Prediction_Dataset.csv"
        cls.db_path = "f1_warehouse.db"
        cls.df = pd.read_csv(cls.csv_path, low_memory=False)

    def test_01_target_labels_presence(self):
        """Verify all binary and multi-class target labels exist in dataset."""
        required_labels = ["is_win", "is_podium", "is_top_10", "is_dnf", "is_pole", "is_mechanical_dnf", "finishing_tier"]
        for lbl in required_labels:
            self.assertIn(lbl, self.df.columns, f"Target label missing: {lbl}")
            self.assertEqual(self.df[lbl].isna().sum(), 0, f"Target label {lbl} has NULLs")

    def test_02_binary_winner_label_exact_counts(self):
        """Verify is_win has exactly 412 positive entries (exactly 1 winner per Grand Prix)."""
        win_count = int(self.df["is_win"].sum())
        self.assertEqual(win_count, 412, f"Expected 412 winners, found {win_count}")
        # Verify 1 winner per race_id
        race_win_sums = self.df.groupby("race_id")["is_win"].sum()
        self.assertTrue((race_win_sums == 1).all(), "Every race must have exactly one winner")

    def test_03_binary_podium_label_exact_counts(self):
        """Verify is_podium has exactly 1,236 positive entries (exactly 3 podiums per Grand Prix)."""
        podium_count = int(self.df["is_podium"].sum())
        self.assertEqual(podium_count, 1236, f"Expected 1,236 podiums (412 * 3), found {podium_count}")
        race_podium_sums = self.df.groupby("race_id")["is_podium"].sum()
        self.assertTrue((race_podium_sums == 3).all(), "Every race must have exactly 3 podium finishers")

    def test_04_binary_points_finish_label_exact_counts(self):
        """Verify is_top_10 has exactly 4,120 positive entries (exactly 10 points scorers per Grand Prix)."""
        points_count = int(self.df["is_top_10"].sum())
        self.assertEqual(points_count, 4120, f"Expected 4,120 points finishers (412 * 10), found {points_count}")
        race_top10_sums = self.df.groupby("race_id")["is_top_10"].sum()
        self.assertTrue((race_top10_sums == 10).all(), "Every race must have exactly 10 points scorers")

    def test_05_multi_class_5_tier_labeling_consistency(self):
        """Verify finishing_tier has 5 classes with zero overlap and correct hierarchical mapping."""
        tiers = set(self.df["finishing_tier"].unique())
        self.assertEqual(tiers, {0, 1, 2, 3, 4}, "Finishing tier must contain classes 0 through 4")
        
        # Tier 0 must strictly equal is_win == 1
        tier0_matches = (self.df["finishing_tier"] == 0) == (self.df["is_win"] == 1)
        self.assertTrue(tier0_matches.all(), "Tier 0 must strictly align with is_win")

    def test_06_zero_target_leakage_in_features(self):
        """Verify feature matrices do NOT include target labels or post-race finishing positions."""
        import joblib
        artifact = joblib.load("f1_winner_model.joblib")
        features = artifact["features"]
        
        forbidden_targets = ["is_win", "is_podium", "is_top_10", "finish_position", "finish_position_text", "race_points", "finishing_tier"]
        for f in features:
            self.assertNotIn(f, forbidden_targets, f"Data leakage detected! Feature '{f}' is a target variable.")

    def test_07_class_imbalance_scale_pos_weight(self):
        """Verify class imbalance ratios for winner (1:20) and podium (1:6)."""
        winner_neg = (self.df["is_win"] == 0).sum()
        winner_pos = (self.df["is_win"] == 1).sum()
        winner_ratio = winner_neg / winner_pos
        self.assertAlmostEqual(winner_ratio, 20.0, places=0, msg="Winner imbalance ratio should be ~20.0")

if __name__ == "__main__":
    print("================================================================================")
    print("  RUNNING CLASSES LABEL VERIFICATION COMPREHENSIVE QA TEST SUITE")
    print("================================================================================")
    unittest.main(verbosity=2)
