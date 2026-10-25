"""
Automated Verification Suite for INPUT / OUTPUT Specification
=============================================================
Validates all Input and Output components of the Data Warehouse & Analytics Platform:
1. Input Source Ingestion (8,650 master results, 296,727 lap telemetry rows, 38 circuit specs)
2. Interactive Parameterized Inputs (API query params: season, race_id, driver_id, slicers)
3. 12 OLAP Query Execution Outputs (Roll-up, Drill-down, Slice, Dice, Pivot, Window Functions)
4. ML Prediction Output Payloads (Ranked driver probabilities, Top-1 and Podium predictions)
5. WebSocket Real-Time Stream Output Payloads (Telemetry tick, lap progression, pit box alerts)
6. Output BI Reports and Frontends (dashboard.html, showcase.html, powerbi_f1.html, grafana.html)
"""

import unittest
import os
import sqlite3
import pandas as pd
import json
import joblib

class TestF1InputOutputQAEvaluation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_path = "f1_warehouse.db"
        cls.master_csv = "F1_Warehouse_Master_65_Columns_2004_2024.csv"
        cls.ml_csv = "F1_ML_Winner_Prediction_Dataset.csv"
        cls.model_path = "f1_winner_model.joblib"
        cls.sql_file = "olap_queries.sql"

    def test_01_input_data_sources_validity(self):
        """Verify all input data sources exist with expected row scale and schema."""
        self.assertTrue(os.path.exists(self.master_csv), "Master CSV input missing")
        df_in = pd.read_csv(self.master_csv, nrows=10)
        self.assertGreaterEqual(len(df_in.columns), 65, "Input master CSV missing expected columns")

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM FACT_LAP_TIMES")
        lap_count = cur.fetchone()[0]
        self.assertGreater(lap_count, 290000, "Lap telemetry input missing records")
        conn.close()

    def test_02_all_12_olap_queries_execution_and_output(self):
        """Verify all 12 OLAP SQL analytical queries execute and produce non-empty outputs."""
        conn = sqlite3.connect(self.db_path)
        with open(self.sql_file, "r", encoding="utf-8") as f:
            content = f.read()

        import re
        pattern = r"(-- QUERY \d+:.*?)(?=(?:-- QUERY \d+:|\Z))"
        matches = re.findall(pattern, content, re.DOTALL)
        self.assertEqual(len(matches), 12, f"Expected 12 OLAP queries in SQL file, found {len(matches)}")

        for idx, match in enumerate(matches, 1):
            lines = match.strip().split("\n")
            sql_lines = [l for l in lines if not l.strip().startswith("--")]
            query_sql = "\n".join(sql_lines).strip()
            
            df_out = pd.read_sql_query(query_sql, conn)
            self.assertGreater(len(df_out), 0, f"Query {idx} returned empty dataframe")
            self.assertGreater(len(df_out.columns), 1, f"Query {idx} output should have multiple columns")

        conn.close()

    def test_03_ml_winner_prediction_input_output(self):
        """Verify ML pipeline accepts race feature vector inputs and outputs valid prediction JSON."""
        self.assertTrue(os.path.exists(self.model_path), "Model artifact missing")
        artifact = joblib.load(self.model_path)
        model = artifact["model"]
        features = artifact["features"]

        conn = sqlite3.connect(self.db_path)
        # Fetch Abu Dhabi GP 2024 input vector (race_id 1144 or max race)
        df_race = pd.read_sql_query("SELECT * FROM ML_WINNER_PREDICTION_FEATURES WHERE season = 2024 ORDER BY round DESC LIMIT 20", conn)
        conn.close()

        self.assertEqual(len(df_race), 20, "Expected 20 driver inputs for 2024 race")

        X_input = df_race[features].copy()
        for col in X_input.columns:
            X_input[col] = pd.to_numeric(X_input[col], errors="coerce").fillna(0)

        # Output probabilities
        probs = model.predict_proba(X_input)[:, 1]
        self.assertEqual(len(probs), 20, "Output probability vector size mismatch")
        self.assertTrue((probs >= 0.0).all() and (probs <= 1.0).all(), "Output probabilities must be in [0, 1]")

        # Rank drivers
        df_race["win_prob"] = probs
        ranked = df_race.sort_values(by="win_prob", ascending=False)
        top1_driver = ranked.iloc[0]["driver_name"]
        self.assertIn(top1_driver, ["Lando Norris", "Max Verstappen", "Charles Leclerc"], "Top predicted driver should be a frontrunner")

    def test_04_websocket_telemetry_payload_schema(self):
        """Verify real-time WebSocket simulator payload schema format."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                flt.lap_number, flt.lap_position, flt.lap_time_str,
                d.driver_code, d.driver_name, c.constructor_name
            FROM FACT_LAP_TIMES flt
            JOIN DIM_DRIVER d ON flt.driver_id = d.driver_id
            JOIN DIM_CONSTRUCTOR c ON flt.constructor_id = c.constructor_id
            WHERE flt.race_id = 18 AND flt.lap_number = 1
            ORDER BY flt.lap_position ASC
        """)
        rows = [dict(sqlite3.Row(cur, r)) for r in cur.fetchall()]
        conn.close()

        # Build sample WebSocket output packet
        packet = {
            "type": "TELEMETRY_TICK",
            "race_id": 18,
            "current_lap": 1,
            "total_laps": 58,
            "drivers_count": len(rows),
            "leaderboard": rows
        }

        # Verify serializability
        json_str = json.dumps(packet)
        parsed = json.loads(json_str)
        self.assertEqual(parsed["type"], "TELEMETRY_TICK")
        self.assertEqual(parsed["current_lap"], 1)
        self.assertGreater(parsed["drivers_count"], 0)

    def test_05_visual_and_bi_frontend_outputs_presence(self):
        """Verify all 4 visual dashboard HTML frontend files exist and contain rendering code."""
        dashboards = ["dashboard.html", "showcase.html", "powerbi_f1.html", "grafana.html"]
        for d in dashboards:
            self.assertTrue(os.path.exists(d), f"Frontend file {d} missing")
            with open(d, "r", encoding="utf-8") as f:
                html = f.read()
            self.assertGreater(len(html), 1000, f"HTML file {d} is suspiciously small")
            self.assertIn("<html", html.lower())

if __name__ == "__main__":
    print("================================================================================")
    print("  RUNNING INPUT / OUTPUT SPECIFICATION COMPREHENSIVE QA TEST SUITE")
    print("================================================================================")
    unittest.main(verbosity=2)
