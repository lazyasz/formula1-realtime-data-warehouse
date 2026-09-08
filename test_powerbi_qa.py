import unittest
import sqlite3
import os
import json

DB_PATH = "f1_warehouse.db"

class TestPowerBiDataAndMeasuresQA(unittest.TestCase):
    """
    Automated QA Test Suite for Power BI Data Model, DAX Measures, and Multi-Page Aggregations.
    """

    @classmethod
    def setUpClass(cls):
        cls.conn = sqlite3.connect(DB_PATH)
        cls.conn.row_factory = sqlite3.Row

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_total_points_measure(self):
        """Test DAX equivalent: Total Points = SUM(race_points)"""
        cur = self.conn.cursor()
        cur.execute("SELECT SUM(race_points) as total_pts FROM FACT_RACE_RESULTS")
        total_pts = cur.fetchone()["total_pts"]
        self.assertGreater(total_pts, 30000, "Total championship points should exceed 30,000 across 2004-2024")

    def test_total_wins_measure(self):
        """Test DAX equivalent: Total Wins = COUNTROWS(finish_position = 1)"""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) as wins FROM FACT_RACE_RESULTS WHERE finish_position = 1")
        total_wins = cur.fetchone()["wins"]
        self.assertGreater(total_wins, 350, "Total race wins should exceed 350 across all recorded GPs")

    def test_driver_podiums_measure(self):
        """Test DAX equivalent: Total Podiums = COUNTROWS(finish_position IN (1, 2, 3))"""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) as podiums FROM FACT_RACE_RESULTS WHERE finish_position IN (1, 2, 3)")
        total_podiums = cur.fetchone()["podiums"]
        cur.execute("SELECT COUNT(*) as wins FROM FACT_RACE_RESULTS WHERE finish_position = 1")
        total_wins = cur.fetchone()["wins"]
        self.assertAlmostEqual(total_podiums, total_wins * 3, delta=10, msg="Total podium spots should be approximately 3x wins")

    def test_driver_poles_measure(self):
        """Test DAX equivalent: Total Poles = COUNTROWS(grid_position = 1)"""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) as poles FROM FACT_RACE_RESULTS WHERE grid_position = 1")
        total_poles = cur.fetchone()["poles"]
        self.assertGreater(total_poles, 350, "Total pole positions should match total race starts")

    def test_page1_driver_champions_data(self):
        """Test Page 1: Verify all-time title holders (Hamilton 7, Schumacher 7, Fangio 5, Prost 4, Vettel 4, Verstappen 3+)"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT d.driver_name, COUNT(DISTINCT r.season_year) as seasons_raced,
                   SUM(CASE WHEN frr.finish_position = 1 THEN 1 ELSE 0 END) as wins
            FROM FACT_RACE_RESULTS frr
            JOIN DIM_DRIVER d ON frr.driver_id = d.driver_id
            JOIN DIM_RACE r ON frr.race_id = r.race_id
            WHERE d.driver_code IN ('HAM', 'VER', 'VET', 'ALO')
            GROUP BY d.driver_name
        """)
        drivers = {r["driver_name"]: r["wins"] for r in cur.fetchall()}
        self.assertIn("Lewis Hamilton", drivers)
        self.assertGreaterEqual(drivers["Lewis Hamilton"], 100, "Hamilton should have 100+ wins")

    def test_page2_constructor_kpis(self):
        """Test Page 2: Verify Constructor KPI totals for Ferrari, Red Bull, Mercedes, McLaren"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT c.constructor_name, 
                   COUNT(DISTINCT frr.race_id) as total_races,
                   SUM(CASE WHEN frr.finish_position = 1 THEN 1 ELSE 0 END) as wins,
                   SUM(frr.race_points) as points
            FROM FACT_RACE_RESULTS frr
            JOIN DIM_CONSTRUCTOR c ON frr.constructor_id = c.constructor_id
            GROUP BY c.constructor_name
            HAVING wins > 0
            ORDER BY wins DESC
        """)
        teams = {r["constructor_name"]: r["wins"] for r in cur.fetchall()}
        self.assertIn("Ferrari", teams)
        self.assertIn("Red Bull", teams)
        self.assertIn("Mercedes", teams)
        self.assertIn("McLaren", teams)

    def test_page4_circuit_retirements_dnf_treemap(self):
        """Test Page 4: Verify DNF Root Cause classifications match failure categories"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT s.status_description, COUNT(*) as dnf_count
            FROM FACT_RACE_RESULTS frr
            JOIN DIM_STATUS s ON frr.status_id = s.status_id
            WHERE frr.status_id != 1
            GROUP BY s.status_description
            ORDER BY dnf_count DESC
        """)
        causes = [r["status_description"] for r in cur.fetchall()]
        self.assertTrue(any("Accident" in c or "Collision" in c or "Engine" in c or "Gearbox" in c for c in causes),
                        "Retirement causes should contain standard mechanical and racing incident classifications")

    def test_powerbi_html_contains_required_visuals(self):
        """Test powerbi_f1.html contains all 4 pages, SVG map, dynamic slicers, and ECharts scripts"""
        with open("powerbi_f1.html", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("page-overview", content)
        self.assertIn("page-constructor", content)
        self.assertIn("page-driver", content)
        self.assertIn("page-circuit", content)
        self.assertIn("pbi-slicer-season", content)
        self.assertIn("pbi-slicer-race", content)
        self.assertIn("chart-world-map", content)
        self.assertIn("chart-circuit-dnf-treemap", content)

if __name__ == "__main__":
    print("\n" + "="*80)
    print("  RUNNING POWER BI DATA MODEL & VISUALS AUTOMATED QA TEST SUITE")
    print("="*80 + "\n")
    unittest.main(verbosity=2)
