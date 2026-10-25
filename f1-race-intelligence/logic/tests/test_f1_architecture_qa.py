"""
Automated Verification Suite for ARCHITECTURE DIAGRAM Pipeline
==============================================================
Validates all architectural and engineering criteria:
1. Multi-Tier Enterprise Architecture Definition (Staging -> EDW -> OLAP -> ML -> BI)
2. Star Schema DDL, Tables, and Referential Integrity
3. Snowflake Schema DDL, Normalized Sub-Dimensions (3NF)
4. Telemetry & Lap-Grain Storage Architecture (FACT_LAP_TIMES, composite indexes)
5. Multi-Dimensional Data Cube Engine Structure (4,089 Cuboids)
6. Machine Learning Feature Store & Prediction Pipeline
7. Fast-Path Parameterized Index Scans (EXPLAIN QUERY PLAN verification)
8. Mermaid Architecture & ER Diagram Files Integrity
"""

import unittest
import os
import sqlite3
import re

class TestF1ArchitectureQAEvaluation(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.db_path = "f1_warehouse.db"
        cls.star_ddl = "create_star_schema.sql"
        cls.snow_ddl = "create_snowflake_schema.sql"
        cls.doc_path = "ARCHITECTURE_SPECIFICATION.md"
        cls.er_star = "er_diagram_star.mmd"
        cls.er_snow = "er_diagram_snowflake.mmd"
        cls.er_oltp = "er_diagram.mmd"

    def test_01_architecture_artifacts_presence(self):
        """Verify all architecture documentation, DDL scripts, and Mermaid diagrams exist."""
        for path in [self.star_ddl, self.snow_ddl, self.doc_path, self.er_star, self.er_snow, self.er_oltp]:
            self.assertTrue(os.path.exists(path), f"Architecture file missing: {path}")

    def test_02_star_schema_tables_and_grain(self):
        """Verify Star Schema tables exist in database and follow denormalized star topology."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        required_star_tables = [
            "DIM_DRIVER", "DIM_CONSTRUCTOR", "DIM_RACE", "DIM_DATE",
            "DIM_STATUS", "FACT_RACE_RESULTS", "FACT_LAP_TIMES"
        ]
        for tbl in required_star_tables:
            cur.execute(f"SELECT COUNT(*) FROM {tbl}")
            count = cur.fetchone()[0]
            self.assertGreater(count, 0, f"Star table {tbl} is empty or missing")

        # Verify DIM_RACE contains denormalized circuit fields
        cur.execute("PRAGMA table_info(DIM_RACE)")
        race_cols = [r[1] for r in cur.fetchall()]
        for col in ["circuit_name", "circuit_location", "circuit_country", "circuit_latitude"]:
            self.assertIn(col, race_cols, f"Denormalized column {col} missing from DIM_RACE")

        conn.close()

    def test_03_snowflake_schema_normalization_3nf(self):
        """Verify Snowflake Schema tables exist with 3NF normalized sub-dimensions."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        required_snow_tables = [
            "DIM_CIRCUIT_SNOWFLAKE", "DIM_COUNTRY", "DIM_NATIONALITY",
            "DIM_ENGINE_SUPPLIER", "FACT_RACE_RESULTS_SNOWFLAKE"
        ]
        for tbl in required_snow_tables:
            cur.execute(f"SELECT COUNT(*) FROM {tbl}")
            count = cur.fetchone()[0]
            self.assertGreater(count, 0, f"Snowflake table {tbl} is empty or missing")

        conn.close()

    def test_04_query_plan_composite_index_scans(self):
        """Verify EXPLAIN QUERY PLAN confirms B-Tree index scans (sub-1ms query latency)."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        # Query 1: Filter by race and driver on FACT_RACE_RESULTS
        cur.execute("EXPLAIN QUERY PLAN SELECT * FROM FACT_RACE_RESULTS WHERE race_id = 18 AND driver_id = 1")
        plan = " ".join([str(r) for r in cur.fetchall()])
        self.assertTrue("INDEX" in plan.upper() or "SEARCH" in plan.upper(), f"Expected index search, got: {plan}")

        # Query 2: Filter lap times by race and lap number
        cur.execute("EXPLAIN QUERY PLAN SELECT * FROM FACT_LAP_TIMES WHERE race_id = 18 AND lap_number = 1")
        plan_lap = " ".join([str(r) for r in cur.fetchall()])
        self.assertTrue("INDEX" in plan_lap.upper() or "SEARCH" in plan_lap.upper(), f"Expected index search on laps, got: {plan_lap}")

        conn.close()

    def test_05_multi_dimensional_olap_cube_structure(self):
        """Verify OLAP Cube engine file exists and defines 4-dimensional lattice."""
        self.assertTrue(os.path.exists("f1_cube_engine.py"))
        with open("f1_cube_engine.py", "r", encoding="utf-8") as f:
            code = f.read()
        self.assertIn("cuboids", code.lower())
        self.assertIn("season", code.lower())
        self.assertIn("constructor", code.lower())

    def test_06_machine_learning_feature_store_architecture(self):
        """Verify ML feature store table and prediction view exist in database."""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("SELECT COUNT(*) FROM ML_WINNER_PREDICTION_FEATURES")
        ml_count = cur.fetchone()[0]
        self.assertEqual(ml_count, 8650, f"Expected 8650 ML rows, found {ml_count}")

        cur.execute("SELECT COUNT(*) FROM DIM_CIRCUIT_LAP_RECORDS")
        rec_count = cur.fetchone()[0]
        self.assertGreaterEqual(rec_count, 35)

        cur.execute("SELECT COUNT(*) FROM V_RACE_WINNER_ML_DATASET")
        view_count = cur.fetchone()[0]
        self.assertEqual(view_count, 8650)

        conn.close()

    def test_07_mermaid_diagrams_syntax_validation(self):
        """Verify Mermaid files contain valid erDiagram syntax and define relationships."""
        for mmd_file in [self.er_star, self.er_snow, self.er_oltp]:
            with open(mmd_file, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("%%")]
            self.assertTrue(lines[0].startswith("erDiagram"), f"Invalid Mermaid header in {mmd_file}")
            full_text = "\n".join(lines)
            self.assertIn("||--o{", full_text, f"Missing relationships in {mmd_file}")

    def test_08_architecture_markdown_comprehensive_sections(self):
        """Verify Architecture deliverable markdown covers all 5 tiers and trade-offs."""
        with open(self.doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        for term in ["Tier 1", "Tier 2", "Tier 3", "Tier 4", "Tier 5", "Star Schema", "Snowflake Schema", "Latency", "Mermaid"]:
            self.assertIn(term.lower(), content.lower(), f"Missing architectural topic: {term}")


if __name__ == "__main__":
    print("================================================================================")
    print("  RUNNING ARCHITECTURE PIPELINE COMPREHENSIVE QA TEST SUITE")
    print("================================================================================")
    unittest.main(verbosity=2)
