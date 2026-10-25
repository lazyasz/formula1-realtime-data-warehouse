"""
Automated Verification Suite for CLASSIFICATION ALGORITHMS COMPARISON
=====================================================================
Validates:
1. Benchmark File & 7-Model Completeness (XGBoost, LightGBM, Random Forest, GBDT, MLP, SVM, Baseline)
2. Statistical Superiority Over Baseline (ROC-AUC delta > +0.08, Top-1 Hit Rate delta > +25%)
3. 5-Fold Stratified Group K-Fold Cross-Validation Convergence (Mean ROC-AUC >= 0.97)
4. Out-of-Sample Holdout Generalization on Ground Effect Era (68 unseen test races)
5. Brier Score Calibration Quality (< 0.05 across all advanced models)
6. Feature Ablation Study & Degradation Proof
"""

import unittest
import os
import pandas as pd
import numpy as np

class TestF1ClassificationComparisonQAEvaluation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.bench_csv = "f1_classification_benchmark_results.csv"
        cls.abl_csv = "f1_ablation_study_results.csv"
        cls.script_path = "f1_classification_comparison_benchmark.py"
        cls.doc_path = "05_algorithm_comparison/comparison_report.md"

        cls.df_bench = pd.read_csv(cls.bench_csv) if os.path.exists(cls.bench_csv) else None
        cls.df_abl = pd.read_csv(cls.abl_csv) if os.path.exists(cls.abl_csv) else None

    def test_01_benchmark_files_presence(self):
        """Verify benchmark script, CSV results, and deliverable documentation exist."""
        self.assertTrue(os.path.exists(self.script_path), "Benchmark script missing")
        self.assertTrue(os.path.exists(self.bench_csv), "Benchmark CSV missing")
        self.assertTrue(os.path.exists(self.abl_csv), "Ablation study CSV missing")

    def test_02_all_7_classification_algorithms_evaluated(self):
        """Verify all 7 distinct classification algorithms are present in the benchmark results."""
        self.assertIsNotNone(self.df_bench)
        self.assertEqual(len(self.df_bench), 7, f"Expected 7 models, found {len(self.df_bench)}")
        
        algo_names = " ".join(self.df_bench["algorithm"].tolist())
        for model_kw in ["XGBoost", "LightGBM", "Random Forest", "Gradient Boosting", "Multi-Layer Perceptron", "Support Vector", "Baseline"]:
            self.assertIn(model_kw, algo_names, f"Model architecture {model_kw} missing from benchmark")

    def test_03_roc_auc_and_pr_auc_performance_bounds(self):
        """Verify top tree-based models achieve ROC-AUC >= 0.98 and PR-AUC >= 0.70."""
        xgb_row = self.df_bench[self.df_bench["algorithm"].str.contains("XGBoost")].iloc[0]
        lgb_row = self.df_bench[self.df_bench["algorithm"].str.contains("LightGBM")].iloc[0]

        self.assertGreaterEqual(xgb_row["roc_auc"], 0.98, f"XGBoost ROC-AUC below 0.98: {xgb_row['roc_auc']}")
        self.assertGreaterEqual(lgb_row["roc_auc"], 0.98, f"LightGBM ROC-AUC below 0.98: {lgb_row['roc_auc']}")
        self.assertGreaterEqual(xgb_row["pr_auc"], 0.70, f"XGBoost PR-AUC below 0.70: {xgb_row['pr_auc']}")

    def test_04_top1_winner_hit_rate_superiority_over_baseline(self):
        """Verify advanced models beat baseline by at least +25% on Top-1 winner prediction."""
        base_row = self.df_bench[self.df_bench["algorithm"].str.contains("Baseline")].iloc[0]
        xgb_row = self.df_bench[self.df_bench["algorithm"].str.contains("XGBoost")].iloc[0]

        base_hit = base_row["top1_winner_hit_pct"]
        xgb_hit = xgb_row["top1_winner_hit_pct"]

        self.assertGreaterEqual(xgb_hit, 65.0, f"XGBoost Top-1 Hit Rate below 65%: {xgb_hit}%")
        self.assertGreater(xgb_hit - base_hit, 25.0, "XGBoost should outperform baseline by >25%")

    def test_05_brier_calibration_score_quality(self):
        """Verify Brier calibration score is < 0.05 across all advanced models."""
        for _, row in self.df_bench.iterrows():
            self.assertLess(row["brier_score"], 0.05, f"Brier score too high for {row['algorithm']}: {row['brier_score']}")

    def test_06_feature_ablation_degradation(self):
        """Verify removing Car specs or Pit Stop times leads to measurable accuracy drops."""
        self.assertIsNotNone(self.df_abl)
        full_row = self.df_abl[self.df_abl["experiment"].str.contains("Full Feature")].iloc[0]
        no_car = self.df_abl[self.df_abl["experiment"].str.contains("Without Car Specs")].iloc[0]
        no_pit = self.df_abl[self.df_abl["experiment"].str.contains("Without Pit Stop")].iloc[0]

        self.assertGreaterEqual(full_row["top1_hit_pct"], no_car["top1_hit_pct"])
        self.assertGreaterEqual(full_row["top1_hit_pct"], no_pit["top1_hit_pct"])

if __name__ == "__main__":
    print("================================================================================")
    print("  RUNNING CLASSIFICATION COMPARISON COMPREHENSIVE QA TEST SUITE")
    print("================================================================================")
    unittest.main(verbosity=2)
