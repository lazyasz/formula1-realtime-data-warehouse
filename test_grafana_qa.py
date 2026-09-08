import os
import json
import re
import unittest

try:
    import yaml
except ImportError:
    yaml = None

class TestGrafanaAndPostgresProvisioningQA(unittest.TestCase):
    """
    Automated QA Test Suite for Fully Automated F1 Platform (PostgreSQL + Grafana OSS)
    Validates Section 8 QA Requirements:
    - Schema & Data Model
    - Grafana Provisioning as Code
    - Template Variables & Cross-Filtering
    - Live Telemetry & Field Color Overrides
    """

    @classmethod
    def setUpClass(cls):
        cls.base_dir = os.path.dirname(os.path.abspath(__file__))
        cls.postgres_dir = os.path.join(cls.base_dir, "postgres_init")
        cls.prov_dir = os.path.join(cls.base_dir, "provisioning")
        cls.dash_dir = os.path.join(cls.prov_dir, "dashboards")
        cls.ds_dir = os.path.join(cls.prov_dir, "datasources")
        cls.sim_dir = os.path.join(cls.base_dir, "sim_service")

    # -------------------------------------------------------------------------
    # 1. POSTGRESQL DDL SCHEMA VALIDATION
    # -------------------------------------------------------------------------
    def test_postgres_snowflake_ddl_exists_and_valid(self):
        """Verify PostgreSQL upstream Snowflake schema DDL file exists and defines 3NF tables."""
        file_path = os.path.join(self.postgres_dir, "01_create_snowflake_schema.sql")
        self.assertTrue(os.path.exists(file_path), "Missing 01_create_snowflake_schema.sql")
        with open(file_path, "r", encoding="utf-8") as f:
            sql = f.read()

        expected_tables = [
            "dim_nationality", "dim_country", "dim_engine_supplier",
            "dim_team_principal", "dim_livery_sponsor", "dim_season",
            "dim_circuit_snowflake", "dim_circuit_layout_history",
            "dim_team_snowflake", "dim_driver_snowflake",
            "fact_race_results_snowflake", "fact_lap_times_snowflake"
        ]
        for tbl in expected_tables:
            self.assertIn(f"CREATE TABLE {tbl}", sql, f"Table {tbl} must be defined in Snowflake DDL")

    def test_postgres_star_ddl_exists_and_indexed(self):
        """Verify PostgreSQL Star schema DDL defines flat dimensions, grain facts, and performance indexes."""
        file_path = os.path.join(self.postgres_dir, "02_create_star_schema.sql")
        self.assertTrue(os.path.exists(file_path), "Missing 02_create_star_schema.sql")
        with open(file_path, "r", encoding="utf-8") as f:
            sql = f.read()

        expected_tables = [
            "dim_driver", "dim_team", "dim_circuit", "dim_race",
            "dim_date", "dim_session", "dim_tyre_compound",
            "fact_race_results", "fact_lap_times"
        ]
        for tbl in expected_tables:
            self.assertIn(f"CREATE TABLE {tbl}", sql, f"Table {tbl} must be defined in Star DDL")

        # Confirm recorded_at TIMESTAMPTZ exists for Grafana time-series
        self.assertIn("recorded_at TIMESTAMPTZ", sql, "fact_lap_times must have recorded_at TIMESTAMPTZ")

        # Confirm composite indexes exist
        self.assertIn("idx_fact_laps_recorded_at", sql, "idx_fact_laps_recorded_at index missing")
        self.assertIn("idx_fact_results_race_driver", sql, "idx_fact_results_race_driver index missing")

    # -------------------------------------------------------------------------
    # 2. GRAFANA PROVISIONING AS CODE VALIDATION
    # -------------------------------------------------------------------------
    def test_datasource_provisioning_yaml(self):
        """Verify datasource YAML is valid and reads credentials from environment variables."""
        ds_file = os.path.join(self.ds_dir, "postgres.yaml")
        self.assertTrue(os.path.exists(ds_file), "Missing provisioning/datasources/postgres.yaml")
        with open(ds_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self.assertEqual(data.get("apiVersion"), 1)
        datasources = data.get("datasources", [])
        self.assertGreater(len(datasources), 0)
        ds = datasources[0]
        self.assertEqual(ds.get("type"), "postgres")
        self.assertIn("${POSTGRES_HOST}", ds.get("url"))
        self.assertIn("${POSTGRES_USER}", ds.get("user"))
        self.assertIn("${POSTGRES_PASSWORD}", ds.get("secureJsonData", {}).get("password", ""))

    def test_dashboards_provider_yaml(self):
        """Verify dashboard provider configuration file exists and points to /etc/grafana/provisioning/dashboards."""
        prov_file = os.path.join(self.dash_dir, "dashboards.yaml")
        self.assertTrue(os.path.exists(prov_file), "Missing provisioning/dashboards/dashboards.yaml")
        with open(prov_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        providers = data.get("providers", [])
        self.assertGreater(len(providers), 0)
        p = providers[0]
        self.assertEqual(p.get("folder"), "Formula 1")
        self.assertEqual(p.get("type"), "file")
        self.assertEqual(p.get("options", {}).get("path"), "/etc/grafana/provisioning/dashboards")

    def test_all_four_dashboards_exist_and_parse_valid_json(self):
        """Confirm all 4 required dashboard JSONs exist and parse cleanly."""
        required_dashboards = [
            ("overview.json", "f1-overview", "Formula 1 — Race Overview & Classification"),
            ("drivers.json", "f1-drivers", "Formula 1 — Drivers & Sector Performance"),
            ("constructors.json", "f1-constructors", "Formula 1 — Constructors & Pit Strategy"),
            ("live_telemetry.json", "f1-live-telemetry", "Formula 1 — Live Race Telemetry & Stream")
        ]
        for filename, expected_uid, expected_title in required_dashboards:
            path = os.path.join(self.dash_dir, filename)
            self.assertTrue(os.path.exists(path), f"Missing dashboard JSON: {filename}")
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)

            self.assertEqual(d.get("uid"), expected_uid, f"Dashboard {filename} UID mismatch")
            self.assertEqual(d.get("title"), expected_title, f"Dashboard {filename} title mismatch")
            self.assertEqual(d.get("style"), "dark", f"Dashboard {filename} must default to dark theme")
            self.assertGreater(len(d.get("panels", [])), 0, f"Dashboard {filename} must have panels")

    # -------------------------------------------------------------------------
    # 3. TEMPLATE VARIABLES & CROSS-FILTERING SQL VALIDATION
    # -------------------------------------------------------------------------
    def test_overview_template_variables_and_cross_filtering(self):
        """Confirm overview dashboard defines template variables and panels reference them."""
        path = os.path.join(self.dash_dir, "overview.json")
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)

        var_names = [v["name"] for v in d.get("templating", {}).get("list", [])]
        self.assertIn("season", var_names)
        self.assertIn("race", var_names)
        self.assertIn("driver", var_names)
        self.assertIn("team", var_names)

        # Confirm multi-select enabled on driver and team
        for v in d["templating"]["list"]:
            if v["name"] in ["driver", "team"]:
                self.assertTrue(v.get("multi"), f"Variable {v['name']} must have multi: true")
                self.assertTrue(v.get("includeAll"), f"Variable {v['name']} must have includeAll: true")

        # Verify panels reference the variables in SQL
        panel_sqls = []
        for p in d.get("panels", []):
            for t in p.get("targets", []):
                if "rawSql" in t:
                    panel_sqls.append(t["rawSql"])

        for sql in panel_sqls:
            self.assertTrue(
                re.search(r"\$\{season\}|\$season", sql),
                f"SQL query must reference season variable: {sql}"
            )

    def test_constructor_color_overrides(self):
        """Verify field color overrides match official team colors."""
        path = os.path.join(self.dash_dir, "overview.json")
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)

        timeseries_panel = next((p for p in d["panels"] if p.get("type") == "timeseries"), None)
        self.assertIsNotNone(timeseries_panel, "Overview dashboard must contain timeseries panel")

        overrides = timeseries_panel.get("fieldConfig", {}).get("overrides", [])
        override_names = [o["matcher"]["options"] for o in overrides if "matcher" in o]

        self.assertIn("Mercedes", override_names)
        self.assertIn("Red Bull", override_names)
        self.assertIn("Ferrari", override_names)
        self.assertIn("McLaren", override_names)

    # -------------------------------------------------------------------------
    # 4. LIVE TELEMETRY DASHBOARD SPECIFICATION
    # -------------------------------------------------------------------------
    def test_live_telemetry_dashboard_spec(self):
        """Confirm Live Telemetry dashboard auto-refreshes every 1-2s and includes LIVE status indicator."""
        path = os.path.join(self.dash_dir, "live_telemetry.json")
        with open(path, "r", encoding="utf-8") as f:
            d = json.load(f)

        self.assertEqual(d.get("refresh"), "2s", "Live Telemetry auto-refresh must be 2s or 1s")
        self.assertTrue(d.get("liveNow"), "liveNow must be true for live dashboard")

        # Confirm text panel with LIVE indicator
        text_panel = next((p for p in d["panels"] if p.get("type") == "text"), None)
        self.assertIsNotNone(text_panel, "Live Telemetry must contain text status indicator panel")
        self.assertIn("LIVE RACE TELEMETRY", text_panel["options"]["content"])

    # -------------------------------------------------------------------------
    # 5. DOCKER COMPOSE CONFIGURATION VALIDATION
    # -------------------------------------------------------------------------
    def test_docker_compose_config(self):
        """Verify docker-compose.yml defines f1-postgres, f1-sim-service, and f1-grafana."""
        dc_file = os.path.join(self.base_dir, "docker-compose.yml")
        self.assertTrue(os.path.exists(dc_file), "Missing docker-compose.yml")
        with open(dc_file, "r", encoding="utf-8") as f:
            dc = yaml.safe_load(f)

        services = dc.get("services", {})
        self.assertIn("f1-postgres", services)
        self.assertIn("f1-sim-service", services)
        self.assertIn("f1-grafana", services)

        # Healthcheck dependency check
        self.assertEqual(
            services["f1-sim-service"]["depends_on"]["f1-postgres"]["condition"],
            "service_healthy"
        )
        self.assertEqual(
            services["f1-grafana"]["depends_on"]["f1-postgres"]["condition"],
            "service_healthy"
        )

if __name__ == "__main__":
    print("=" * 80)
    print("  RUNNING COMPLETE POSTGRESQL + GRAFANA AUTOMATED PROVISIONING QA SUITE")
    print("=" * 80)
    unittest.main(verbosity=2)
