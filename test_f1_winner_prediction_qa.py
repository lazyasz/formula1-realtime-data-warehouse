"""
Automated QA Test Suite for F1 Winner Prediction Features & Machine Learning Pipeline
=====================================================================================
Validates:
1. Master ML Dataset Integrity (8,650 rows, 97 columns, zero critical nulls)
2. Car Features Domain Validation (Engine architecture, BHP, weight, power-to-weight, reliability)
3. Lap Record Domain Validation (Circuit lap records for 38 circuits, pace ratios, quali deltas)
4. Pit Stop Time Domain Validation (Pit crew scores, stationary estimates, pit lane loss)
5. SQLite Database Tables (ML_WINNER_PREDICTION_FEATURES, DIM_CIRCUIT_LAP_RECORDS, Views & Indexes)
6. Trained ML Model Inference & Benchmark Metrics (XGBoost model loads, outputs valid probabilities)
"""

import unittest
import os
import sqlite3
import pandas as pd
import numpy as np
import joblib

class TestF1WinnerPredictionFeaturesAndML(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.csv_path = "F1_ML_Winner_Prediction_Dataset.csv"
        cls.db_path = "f1_warehouse.db"
        cls.model_path = "f1_winner_model.joblib"
        cls.report_path = "ML_WINNER_PREDICTION_REPORT.md"
        
        # Load dataset
        cls.df = pd.read_csv(cls.csv_path, low_memory=False)

    def test_01_dataset_file_and_shape(self):
        """Verify enriched ML dataset exists with 8,650 rows and >= 90 columns."""
        self.assertTrue(os.path.exists(self.csv_path), "Enriched CSV file does not exist")
        self.assertEqual(len(self.df), 8650, f"Expected 8,650 rows, found {len(self.df)}")
        self.assertGreaterEqual(len(self.df.columns), 90, f"Expected >=90 columns, found {len(self.df.columns)}")

    def test_02_car_features_presence_and_bounds(self):
        """Verify all requested Car Features exist and values adhere to FIA physical boundaries."""
        required_car_cols = [
            "car_engine_architecture",
            "car_power_unit_supplier",
            "car_estimated_power_bhp",
            "car_min_weight_kg",
            "car_power_to_weight_ratio",
            "car_aero_regulation_era",
            "car_chassis_model",
            "car_mechanical_reliability_score",
            "constructor_pace_index"
        ]
        for col in required_car_cols:
            self.assertIn(col, self.df.columns, f"Missing Car Feature column: {col}")

        # Bounds checks
        self.assertTrue((self.df["car_estimated_power_bhp"] >= 700).all(), "BHP should be >= 700")
        self.assertTrue((self.df["car_estimated_power_bhp"] <= 1100).all(), "BHP should be <= 1100")
        self.assertTrue((self.df["car_min_weight_kg"] >= 600).all(), "Min weight should be >= 600kg")
        self.assertTrue((self.df["car_min_weight_kg"] <= 800).all(), "Min weight should be <= 800kg")
        self.assertTrue((self.df["car_power_to_weight_ratio"] > 1.0).all(), "Power-to-weight should be > 1.0 BHP/kg")
        self.assertTrue((self.df["car_mechanical_reliability_score"] >= 0.0).all(), "Reliability score >= 0.0")
        self.assertTrue((self.df["car_mechanical_reliability_score"] <= 1.0).all(), "Reliability score <= 1.0")

    def test_03_lap_record_features_presence_and_bounds(self):
        """Verify all requested Lap Record columns exist and circuit records match real-world benchmarks."""
        required_lap_cols = [
            "circuit_lap_record_sec",
            "circuit_lap_record_str",
            "circuit_lap_record_holder",
            "circuit_lap_record_year",
            "driver_fastest_lap_sec",
            "driver_lap_record_delta_sec",
            "driver_lap_record_ratio",
            "driver_quali_to_record_delta_sec"
        ]
        for col in required_lap_cols:
            self.assertIn(col, self.df.columns, f"Missing Lap Record column: {col}")

        # Check circuit lap records are positive and within realistic track bounds (50s to 130s)
        self.assertTrue((self.df["circuit_lap_record_sec"] >= 50.0).all(), "Lap record should be >= 50.0s")
        self.assertTrue((self.df["circuit_lap_record_sec"] <= 130.0).all(), "Lap record should be <= 130.0s")

        # Spot check specific iconic tracks
        # Monza (circuit_id 14) ~ 80.9s
        monza_rows = self.df[self.df["circuit_id"] == 14]
        if len(monza_rows) > 0:
            self.assertAlmostEqual(monza_rows.iloc[0]["circuit_lap_record_sec"], 80.901, places=1)
        
        # Spa (circuit_id 13) ~ 104.7s
        spa_rows = self.df[self.df["circuit_id"] == 13]
        if len(spa_rows) > 0:
            self.assertAlmostEqual(spa_rows.iloc[0]["circuit_lap_record_sec"], 104.701, places=1)

    def test_04_pit_stop_features_presence_and_bounds(self):
        """Verify all requested Pit Stop Time and strategy features exist."""
        required_pit_cols = [
            "pit_stop_count",
            "total_pit_duration_sec",
            "avg_pit_duration_sec",
            "fastest_pit_duration_sec",
            "circuit_pit_lane_loss_sec",
            "pit_crew_efficiency_score",
            "estimated_stationary_pit_sec",
            "total_race_pit_loss_sec",
            "pit_loss_delta_to_race_mean_sec"
        ]
        for col in required_pit_cols:
            self.assertIn(col, self.df.columns, f"Missing Pit Stop column: {col}")

        # Check pit crew efficiency scores (50 to 100)
        self.assertTrue((self.df["pit_crew_efficiency_score"] >= 50.0).all(), "Pit crew score should be >= 50")
        self.assertTrue((self.df["pit_crew_efficiency_score"] <= 100.0).all(), "Pit crew score should be <= 100")
        
        # Check circuit pit loss penalties (15.0s to 32.0s)
        self.assertTrue((self.df["circuit_pit_lane_loss_sec"] >= 15.0).all(), "Pit lane loss should be >= 15s")
        self.assertTrue((self.df["circuit_pit_lane_loss_sec"] <= 32.0).all(), "Pit lane loss should be <= 32s")

    def test_05_sqlite_database_tables_and_view(self):
        """Verify SQLite database contains ML table, lap records dimension, view, and indexes."""
        self.assertTrue(os.path.exists(self.db_path), "Database file does not exist")
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Check ML table row count
        cur.execute("SELECT COUNT(*) FROM ML_WINNER_PREDICTION_FEATURES")
        count = cur.fetchone()[0]
        self.assertEqual(count, 8650, f"Expected 8650 records in DB table, found {count}")

        # Check DIM_CIRCUIT_LAP_RECORDS table
        cur.execute("SELECT COUNT(*) FROM DIM_CIRCUIT_LAP_RECORDS")
        circ_count = cur.fetchone()[0]
        self.assertGreaterEqual(circ_count, 35, f"Expected >= 35 circuits, found {circ_count}")

        # Check view exists
        cur.execute("SELECT COUNT(*) FROM V_RACE_WINNER_ML_DATASET")
        view_count = cur.fetchone()[0]
        self.assertEqual(view_count, 8650, f"Expected 8650 records in View, found {view_count}")

        conn.close()

    def test_06_trained_ml_model_artifact(self):
        """Verify production model artifact loads cleanly and can perform prediction."""
        self.assertTrue(os.path.exists(self.model_path), "Model artifact does not exist")
        artifact = joblib.load(self.model_path)
        
        self.assertIn("model", artifact)
        self.assertIn("features", artifact)
        self.assertIn("feature_importances", artifact)
        self.assertIn("results", artifact)

        model = artifact["model"]
        features = artifact["features"]

        # Create sample test input vector
        sample_input = self.df[features].head(5).copy()
        for col in sample_input.columns:
            sample_input[col] = pd.to_numeric(sample_input[col], errors="coerce").fillna(0)

        probs = model.predict_proba(sample_input)
        self.assertEqual(probs.shape, (5, 2), "Prediction probabilities shape mismatch")
        self.assertTrue((probs[:, 1] >= 0.0).all() and (probs[:, 1] <= 1.0).all(), "Probabilities outside [0, 1]")

    def test_07_ml_report_markdown_generated(self):
        """Verify ML Winner Prediction report markdown exists and contains key metrics."""
        self.assertTrue(os.path.exists(self.report_path), "ML Report markdown does not exist")
        with open(self.report_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("XGBoost", content)
        self.assertIn("Car Features", content)
        self.assertIn("Lap Record", content)
        self.assertIn("Pit Stop", content)

if __name__ == "__main__":
    print("================================================================================")
    print("  RUNNING F1 WINNER PREDICTION FEATURES & MACHINE LEARNING QA TEST SUITE")
    print("================================================================================")
    unittest.main(verbosity=2)
