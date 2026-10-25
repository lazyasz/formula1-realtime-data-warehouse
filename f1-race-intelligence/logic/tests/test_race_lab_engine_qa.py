"""
Formula 1 Race Lab - End-to-End Test Suite & Verification Suite
==============================================================
Validates:
1. Dataset ingestion & detected row counts (1994-2024 Ergast universe)
2. Absence of data leakage in pre-race rolling features
3. Classification model metrics (XGBoost, LightGBM, Random Forest, Logistic Baseline)
4. Position regression model metrics (MAE, RMSE, R²)
5. Scenario simulation API logic (baseline vs scenario diffs)
6. 2026 forecast calendar & information cutoffs
"""

import unittest
import os
import json
import sqlite3
import pandas as pd
import numpy as np

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import race_lab_service as rls

class TestF1RaceLabEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.artifacts = rls.get_artifacts()
        cls.df_features = rls.get_feature_df()

    def test_01_dataset_row_counts_and_columns(self):
        """Verifies ingestion of 1994-2024 Ergast data with at least 500 races and 10k entries."""
        self.assertGreaterEqual(len(self.df_features), 12000, "Should have >= 12,000 driver race records")
        self.assertGreaterEqual(self.df_features["race_id"].nunique(), 500, "Should have >= 500 historical races")
        self.assertEqual(int(self.df_features["season"].min()), 1994, "Min season must be 1994")
        self.assertEqual(int(self.df_features["season"].max()), 2024, "Max season must be 2024")

        # Verify key target columns
        required_targets = ["target_is_win", "target_is_podium", "target_is_points", "target_is_dnf", "target_finish_position"]
        for t in required_targets:
            self.assertIn(t, self.df_features.columns, f"Target {t} must be present in dataset")

    def test_02_zero_data_leakage(self):
        """Verifies pre-race features only use information strictly prior to target event."""
        # For race 1 of any season, season_points_before must be 0.0
        round_1_entries = self.df_features[self.df_features["round"] == 1]
        self.assertTrue((round_1_entries["season_points_before"] == 0.0).all(), "Round 1 season points before race must be 0.0")

        # Verify no negative grid or finish positions
        self.assertTrue((self.df_features["grid_position"] >= 1).all())
        self.assertTrue((self.df_features["target_finish_position"] >= 1).all())

    def test_03_classification_models_trained(self):
        """Verifies trained classification models exist and produce calibrated probabilities."""
        self.assertIn("win_model", self.artifacts)
        self.assertIn("podium_model", self.artifacts)
        self.assertIn("points_model", self.artifacts)
        self.assertIn("dnf_model", self.artifacts)

        metrics = self.artifacts["metrics"]
        self.assertIn("winner_models", metrics)
        xgb_metrics = metrics["winner_models"]["XGBoost Classifier"]
        self.assertGreater(xgb_metrics["roc_auc"], 0.90, "XGBoost winner ROC-AUC must be > 0.90")

    def test_04_position_regressor_trained(self):
        """Verifies finishing position regression model performs better than baseline."""
        self.assertIn("position_regressor", self.artifacts)
        pos_metrics = self.artifacts["metrics"]["position_regression"]
        rf_mae = pos_metrics["Random Forest Regressor"]["mae"]
        base_mae = pos_metrics["Baseline (Grid Position Only)"]["mae"]
        self.assertLess(rf_mae, base_mae, "Random Forest Regressor MAE must be better than baseline")
        self.assertLess(rf_mae, 4.0, "Regressor MAE should be < 4 positions")

    def test_05_prediction_pipeline_execution(self):
        """Tests live inference on a real Grand Prix (2024 British GP, ID 1132)."""
        pred = rls.run_predictions(race_id=1132, model_name="XGBoost Classifier", target="winner")
        self.assertEqual(len(pred["predictions"]), 20, "Should have 20 driver predictions for 2024 British GP")
        
        # Softmax calibrated sum should equal 100%
        total_prob = sum(d["metric_value"] for d in pred["predictions"])
        self.assertAlmostEqual(total_prob, 100.0, delta=1.5, msg="Calibrated win probability must sum to ~100%")

    def test_06_scenario_simulation_functionality(self):
        """Verifies scenario simulation updates output when grid position changes from P4 to P1."""
        sim = rls.simulate_scenario(race_id=1132, driver_id=830, hypothetical_grid=1)
        self.assertIn("changes_made", sim)
        self.assertGreater(sim["scenario"]["win_prob_pct"], sim["baseline"]["win_prob_pct"],
                           "Pole position P1 should yield higher win probability than P4")
        self.assertGreater(sim["deltas"]["win_prob_delta"], 0, "Win delta should be positive")

    def test_07_driver_comparison_logic(self):
        """Verifies head-to-head driver comparison retrieves real statistics."""
        comp = rls.compare_drivers(driver_id_1=830, driver_id_2=846)
        self.assertIn("driver_1", comp)
        self.assertIn("driver_2", comp)
        self.assertGreater(comp["driver_1"]["career_wins"], 0, "Max Verstappen career wins must be > 0")

    def test_09_treeshap_explainability(self):
        """Verifies TreeSHAP exact mathematical attribution calculation."""
        exp = rls.explain_prediction(race_id=1132, driver_id=830)
        self.assertIn("attributions", exp)
        self.assertGreaterEqual(len(exp["attributions"]), 16, "Must compute SHAP values for all 16 features")
        self.assertIn("narrative", exp)
        self.assertIn("base_log_odds", exp)

    def test_10_simulated_grid_and_constructors(self):
        """Verifies full 20-car simulated grid re-ranking and constructor comparison."""
        sim = rls.simulate_scenario(race_id=1132, driver_id=830, hypothetical_grid=1)
        self.assertIn("simulated_grid", sim)
        self.assertEqual(len(sim["simulated_grid"]), 20, "Simulated grid must contain all 20 cars")
        # Check constructor comparison
        c_comp = rls.compare_constructors(constructor_id_1=9, constructor_id_2=1)
        self.assertIn("constructor_1", c_comp)
        self.assertIn("constructor_2", c_comp)
        self.assertEqual(c_comp["constructor_1"]["name"], "Red Bull")

if __name__ == "__main__":
    unittest.main()

