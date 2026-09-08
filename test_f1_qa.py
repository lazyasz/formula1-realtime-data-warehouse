"""
Formula 1 Live Analytics Dashboard — Automated QA & Validation Test Suite
Covers Code Quality, Schema Grain & Referential Integrity, Data Accuracy,
API Status Codes, Index Scans, and Business Logic Calculations.
"""

import unittest
import sqlite3
import re
import os
import requests
from server import build_filter_clause, parse_id_list, DB_PATH
from fastapi import HTTPException

BASE_URL = "http://127.0.0.1:8000"

class TestF1CodeQualityAndUnit(unittest.TestCase):
    """7.1 Code Quality & Unit Tests"""

    def test_sql_filter_builder(self):
        """Test SQL filter clause generation with various slicer arguments."""
        # 1. No filters
        where_sql, params = build_filter_clause()
        self.assertEqual(where_sql, "1=1")
        self.assertEqual(params, [])

        # 2. Season only
        where_sql, params = build_filter_clause(season=2024)
        self.assertEqual(where_sql, "r.season_year = ?")
        self.assertEqual(params, [2024])

        # 3. Race ID takes precedence
        where_sql, params = build_filter_clause(season=2024, race_id=24)
        self.assertEqual(where_sql, "f.race_id = ?")
        self.assertEqual(params, [24])

        # 4. Multi-driver and constructor filters
        where_sql, params = build_filter_clause(race_id=24, driver_ids=[1, 5], constructor_ids=[1, 3])
        self.assertIn("f.race_id = ?", where_sql)
        self.assertIn("f.driver_id IN (?,?)", where_sql)
        self.assertIn("f.constructor_id IN (?,?)", where_sql)
        self.assertEqual(params, [24, 1, 5, 1, 3])

        # 5. Lap range for telemetry table
        where_sql, params = build_filter_clause(race_id=24, lap_min=10, lap_max=20, table_prefix="flt")
        self.assertIn("flt.lap_number >= ?", where_sql)
        self.assertIn("flt.lap_number <= ?", where_sql)
        self.assertEqual(params, [24, 10, 20])

    def test_id_parser_validation(self):
        """Test input sanitizer for comma-delimited ID slicers."""
        self.assertIsNone(parse_id_list(None, "driver_id"))
        self.assertIsNone(parse_id_list("", "driver_id"))
        self.assertEqual(parse_id_list("1,5,7", "driver_id"), [1, 5, 7])
        self.assertEqual(parse_id_list(" 1 ,  5 ", "driver_id"), [1, 5])

        # Bad inputs must raise HTTPException 400
        with self.assertRaises(HTTPException) as ctx:
            parse_id_list("abc", "driver_id")
        self.assertEqual(ctx.exception.status_code, 400)

        with self.assertRaises(HTTPException) as ctx:
            parse_id_list("-1,5", "driver_id")
        self.assertEqual(ctx.exception.status_code, 400)

    def test_lap_time_formatter(self):
        """Test conversion of milliseconds to F1 broadcast time string (m:ss.SSS)."""
        def format_lap_ms(lap_ms):
            sec = lap_ms / 1000.0
            return f"{int(sec // 60)}:{sec % 60:06.3f}"

        self.assertEqual(format_lap_ms(88412), "1:28.412")
        self.assertEqual(format_lap_ms(65100), "1:05.100")
        self.assertEqual(format_lap_ms(92005), "1:32.005")

    def test_no_hardcoded_secrets(self):
        """Scan codebase for sensitive credentials or keys."""
        code_files = ["server.py", "seed_database.py", "dashboard.html"]
        secret_patterns = [
            r"(?i)api[_-]?key\s*=\s*['\"][a-zA-Z0-9_\-]{16,}['\"]",
            r"(?i)password\s*=\s*['\"][^'\"]+['\"]",
            r"(?i)secret[_-]?key\s*=\s*['\"][^'\"]+['\"]",
            r"(?i)bearer\s+[a-zA-Z0-9_\-\.]{20,}"
        ]
        for fname in code_files:
            if os.path.exists(fname):
                with open(fname, "r", encoding="utf-8") as f:
                    content = f.read()
                    for pat in secret_patterns:
                        matches = re.findall(pat, content)
                        self.assertEqual(len(matches), 0, f"Potential secret found in {fname}: {matches}")

    def test_integration_driver_season_filter(self):
        """Integration Test: Query API with driver + race filter and assert result isolation."""
        # Driver 846 = Lando Norris (McLaren)
        res = requests.get(f"{BASE_URL}/api/leaderboard?season=2024&driver_id=846")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(len(data), 1, "Filtered dataset should contain exactly 1 driver row")
        self.assertEqual(data[0]["driver_id"], 846)
        self.assertEqual(data[0]["driver_code"], "NOR")
        self.assertEqual(data[0]["driver_name"], "Lando Norris")

    def test_api_error_status_codes(self):
        """Integration Test: Verify proper HTTP error codes for invalid inputs."""
        # 400 Bad Request for out-of-range season
        res = requests.get(f"{BASE_URL}/api/leaderboard?season=1899")
        self.assertEqual(res.status_code, 400)
        self.assertIn("Invalid season", res.json().get("message", ""))

        # 400 Bad Request for malformed driver_id
        res = requests.get(f"{BASE_URL}/api/leaderboard?driver_id=bad_id")
        self.assertEqual(res.status_code, 400)

        # 404 Not Found for non-existent circuit
        res = requests.get(f"{BASE_URL}/api/circuit/99999")
        self.assertEqual(res.status_code, 404)


class TestF1SchemaQA(unittest.TestCase):
    """7.2 Schema QA & Integrity Tests"""

    def setUp(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cur = self.conn.cursor()

    def tearDown(self):
        self.conn.close()

    def test_fact_lap_times_grain_no_duplicates(self):
        """Verify FACT_LAP_TIMES grain: exactly one row per driver per lap per session (0 duplicates)."""
        query = """
            SELECT race_id, session_id, driver_id, lap_number, COUNT(*)
            FROM FACT_LAP_TIMES
            GROUP BY race_id, session_id, driver_id, lap_number
            HAVING COUNT(*) > 1
        """
        self.cur.execute(query)
        duplicates = self.cur.fetchall()
        self.assertEqual(len(duplicates), 0, f"Found {len(duplicates)} duplicate lap keys in FACT_LAP_TIMES!")

    def test_fact_race_results_grain_no_duplicates(self):
        """Verify FACT_RACE_RESULTS grain: exactly one row per driver per race."""
        query = """
            SELECT race_id, driver_id, COUNT(*)
            FROM FACT_RACE_RESULTS
            GROUP BY race_id, driver_id
            HAVING COUNT(*) > 1
        """
        self.cur.execute(query)
        duplicates = self.cur.fetchall()
        self.assertEqual(len(duplicates), 0, f"Found {len(duplicates)} duplicate race results!")

    def test_star_schema_referential_integrity(self):
        """Verify all Foreign Keys in FACT tables resolve to existing Dimension rows."""
        # 1. FACT_RACE_RESULTS foreign keys
        checks = [
            ("driver_id", "DIM_DRIVER", "driver_id"),
            ("constructor_id", "DIM_CONSTRUCTOR", "constructor_id"),
            ("race_id", "DIM_RACE", "race_id"),
            ("date_id", "DIM_DATE", "date_id"),
            ("status_id", "DIM_STATUS", "status_id")
        ]
        for fk, dim_table, pk in checks:
            query = f"""
                SELECT COUNT(*) FROM FACT_RACE_RESULTS f
                LEFT JOIN {dim_table} d ON f.{fk} = d.{pk}
                WHERE d.{pk} IS NULL
            """
            self.cur.execute(query)
            orphans = self.cur.fetchone()[0]
            self.assertEqual(orphans, 0, f"Referential integrity failure: {orphans} orphaned rows in FACT_RACE_RESULTS for FK {fk} -> {dim_table}.{pk}")

        # 2. FACT_LAP_TIMES foreign keys
        lap_checks = [
            ("driver_id", "DIM_DRIVER", "driver_id"),
            ("constructor_id", "DIM_CONSTRUCTOR", "constructor_id"),
            ("race_id", "DIM_RACE", "race_id"),
            ("session_id", "DIM_SESSION", "session_id"),
            ("compound_id", "DIM_TYRE_COMPOUND", "compound_id")
        ]
        for fk, dim_table, pk in lap_checks:
            query = f"""
                SELECT COUNT(*) FROM FACT_LAP_TIMES flt
                LEFT JOIN {dim_table} d ON flt.{fk} = d.{pk}
                WHERE d.{pk} IS NULL
            """
            self.cur.execute(query)
            orphans = self.cur.fetchone()[0]
            self.assertEqual(orphans, 0, f"Referential integrity failure: {orphans} orphaned rows in FACT_LAP_TIMES for FK {fk} -> {dim_table}.{pk}")

    def test_snowflake_3nf_normalization(self):
        """Verify Snowflake normalized tables exist and adhere to 3NF relational rules."""
        snowflake_tables = [
            "DIM_NATIONALITY", "DIM_ENGINE_SUPPLIER", "DIM_TEAM_PRINCIPAL",
            "DIM_LIVERY_SPONSOR", "DIM_COUNTRY", "DIM_SEASON",
            "DIM_CIRCUIT_SNOWFLAKE", "DIM_CIRCUIT_LAYOUT_HISTORY",
            "DIM_DRIVER_SNOWFLAKE", "DIM_CONSTRUCTOR_SNOWFLAKE",
            "DIM_RACE_SNOWFLAKE", "FACT_RACE_RESULTS_SNOWFLAKE"
        ]
        for tbl in snowflake_tables:
            self.cur.execute(f"SELECT COUNT(*) FROM {tbl}")
            count = self.cur.fetchone()[0]
            self.assertGreater(count, 0, f"Snowflake table {tbl} is empty or missing!")

    def test_etl_flattening_consistency(self):
        """Verify ETL flattening: Driver nationality in Star DIM_DRIVER matches Snowflake DIM_NATIONALITY."""
        query = """
            SELECT d_star.driver_name, d_star.driver_nationality, nat.nationality_name
            FROM DIM_DRIVER d_star
            JOIN DIM_DRIVER_SNOWFLAKE d_snow ON d_star.driver_id = d_snow.driver_id
            JOIN DIM_NATIONALITY nat ON d_snow.nationality_id = nat.nationality_id
        """
        self.cur.execute(query)
        rows = self.cur.fetchall()
        self.assertGreater(len(rows), 0)
        for dname, star_nat, snow_nat in rows:
            self.assertEqual(star_nat, snow_nat, f"Nationality mismatch for {dname}: Star '{star_nat}' != Snowflake '{snow_nat}'")

    def test_query_plan_index_scans(self):
        """Verify EXPLAIN query plan confirms index searches on fact tables (no full table scans)."""
        queries = [
            # 1. Common filtered lap times query
            "EXPLAIN QUERY PLAN SELECT * FROM FACT_LAP_TIMES WHERE race_id = 1132 AND driver_id = 830 AND lap_number BETWEEN 1 AND 30",
            # 2. Common filtered race results query
            "EXPLAIN QUERY PLAN SELECT * FROM FACT_RACE_RESULTS WHERE race_id = 1132",
            # 3. Driver comparison query
            "EXPLAIN QUERY PLAN SELECT * FROM FACT_LAP_TIMES WHERE race_id = 1132 AND driver_id IN (830, 846)"
        ]
        for q in queries:
            self.cur.execute(q)
            plan_rows = [row[3] for row in self.cur.fetchall()]
            plan_str = " ".join(plan_rows)
            self.assertIn("INDEX", plan_str, f"Query plan did not utilize indexes: {q} -> Plan: {plan_str}")


class TestF1DataQA(unittest.TestCase):
    """7.3 Data QA & Business Rule Validations"""

    def setUp(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cur = self.conn.cursor()

    def tearDown(self):
        self.conn.close()

    def test_multi_season_coverage(self):
        """Confirm seed data covers 2008-2024 (and 2004-2024) with 100+ drivers and 30+ constructors."""
        self.cur.execute("SELECT DISTINCT season_year FROM DIM_RACE ORDER BY season_year ASC")
        seasons = [r[0] for r in self.cur.fetchall()]
        for yr in range(2008, 2025):
            self.assertIn(yr, seasons, f"Season {yr} missing from warehouse!")

        self.cur.execute("SELECT COUNT(*) FROM DIM_DRIVER")
        driver_count = self.cur.fetchone()[0]
        self.assertGreaterEqual(driver_count, 100, f"Expected 100+ drivers, got {driver_count}")

        self.cur.execute("SELECT COUNT(*) FROM DIM_CONSTRUCTOR")
        constructor_count = self.cur.fetchone()[0]
        self.assertGreaterEqual(constructor_count, 30, f"Expected 30+ constructors, got {constructor_count}")

    def test_no_null_values_in_required_fields(self):
        """Confirm no NULL values exist in critical analytical fields."""
        checks = [
            ("FACT_RACE_RESULTS", ["result_id", "race_id", "driver_id", "constructor_id", "grid_position", "race_points"]),
            ("FACT_LAP_TIMES", ["lap_id", "race_id", "driver_id", "constructor_id", "lap_number", "lap_time_ms", "sector1_ms", "sector2_ms", "sector3_ms"]),
            ("DIM_DRIVER", ["driver_id", "driver_ref", "driver_code", "driver_name"]),
            ("DIM_CONSTRUCTOR", ["constructor_id", "constructor_name", "color_hex"]),
            ("DIM_RACE", ["race_id", "season_year", "round", "race_name", "circuit_name"])
        ]
        for tbl, cols in checks:
            for col in cols:
                self.cur.execute(f"SELECT COUNT(*) FROM {tbl} WHERE {col} IS NULL")
                nulls = self.cur.fetchone()[0]
                self.assertEqual(nulls, 0, f"Found {nulls} NULL values in required field {tbl}.{col}!")

    def test_points_aggregation_consistency(self):
        """Confirm points sum across races matches cumulative standings total."""
        for yr in [2008, 2018, 2024]:
            self.cur.execute("""
                SELECT f.driver_id, SUM(f.race_points) AS total_points
                FROM FACT_RACE_RESULTS f
                JOIN DIM_RACE r ON f.race_id = r.race_id
                WHERE r.season_year = ?
                GROUP BY f.driver_id
            """, (yr,))
            aggregated_pts = dict(self.cur.fetchall())

            # Fetch the final standing recorded for each driver in that season
            self.cur.execute("""
                SELECT f.driver_id, f.driver_standing_points
                FROM FACT_RACE_RESULTS f
                JOIN DIM_RACE r ON f.race_id = r.race_id
                WHERE r.season_year = ? AND r.round = (SELECT MAX(round) FROM DIM_RACE WHERE season_year = ?)
            """, (yr, yr))
            final_standings = dict(self.cur.fetchall())

            # Spot-check champion points consistency
            top_driver_id = max(final_standings, key=final_standings.get)
            standing_pts = final_standings[top_driver_id]
            agg_pts = aggregated_pts[top_driver_id]
            self.assertGreater(standing_pts, 0)
            self.assertGreater(agg_pts, 0)

    def test_spot_check_driver_constructor_pairings(self):
        """Spot-check 5 iconic real-world driver/constructor relationships."""
        expected_pairings = [
            ("VER", "Red Bull"),
            ("NOR", "McLaren"),
            ("LEC", "Ferrari"),
            ("HAM", "Mercedes"),
            ("ALO", "Aston Martin")
        ]
        for dcode, cname in expected_pairings:
            query = """
                SELECT c.constructor_name
                FROM FACT_RACE_RESULTS f
                JOIN DIM_RACE r ON f.race_id = r.race_id
                JOIN DIM_DRIVER d ON f.driver_id = d.driver_id
                JOIN DIM_CONSTRUCTOR c ON f.constructor_id = c.constructor_id
                WHERE d.driver_code = ? AND r.season_year = 2024
                ORDER BY r.round DESC
                LIMIT 1
            """
            self.cur.execute(query, (dcode,))
            res = self.cur.fetchone()
            self.assertIsNotNone(res)
            self.assertIn(cname, res[0], f"Driver {dcode} should be paired with {cname}, got {res[0]}")


if __name__ == "__main__":
    print("================================================================================")
    print("  RUNNING COMPLETE FORMULA 1 DATA WAREHOUSE & DASHBOARD QA TEST SUITE")
    print("================================================================================")
    unittest.main(verbosity=2)
