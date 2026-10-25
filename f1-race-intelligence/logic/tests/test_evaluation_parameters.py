"""
System Capabilities Verification Suite for Formula 1 Classification
===================================================================
Automated test suite validating all 8 engineering modules:
- Module 01: Architecture Diagram Pipeline
- Module 02: Input / Output Specification
- Module 03: Class Labels & Target Formulation
- Module 04: Pattern Matching - Apriori & FP-Growth
- Module 05: Algorithm Comparison & Validation
- Module 06: Classification Algorithm Engine
- Module 07: Feature Innovation & Group Softmax
- Module 08: Performance Metrics & Verification
"""

import unittest
import os
import json
import pandas as pd
import numpy as np

class TestF1EvaluationParameters(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Anchor to project root whether test is in logic/tests or tests
        curr = os.path.dirname(os.path.abspath(__file__))
        if os.path.basename(os.path.dirname(curr)) in ["logic", "jury"]:
            cls.root_dir = os.path.abspath(os.path.join(curr, "..", ".."))
        else:
            cls.root_dir = os.path.abspath(os.path.join(curr, ".."))

    def resolve_dir(self, subpath):
        candidates = [
            os.path.join(self.root_dir, "logic", subpath),
            os.path.join(self.root_dir, "jury", subpath),
            os.path.join(self.root_dir, subpath),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return candidates[0]

    def resolve_file(self, *parts):
        candidates = [
            os.path.join(self.root_dir, "logic", *parts),
            os.path.join(self.root_dir, "jury", *parts),
            os.path.join(self.root_dir, *parts),
        ]
        for c in candidates:
            if os.path.exists(c):
                return c
        return candidates[0]

    def test_01_architecture_diagram_parameter(self):
        """[01 Architecture] Verify diagram files and pipeline description exist."""
        p01_dir = self.resolve_dir("01_architecture")
        mmd_file = os.path.join(p01_dir, "architecture_diagram.mmd")
        md_file = os.path.join(p01_dir, "architecture_diagram.md")
        exp_file = os.path.join(p01_dir, "architecture_explanation.md")

        self.assertTrue(os.path.exists(mmd_file), f"architecture_diagram.mmd missing in {p01_dir}")
        self.assertTrue(os.path.exists(md_file), "architecture_diagram.md missing")
        self.assertTrue(os.path.exists(exp_file), "architecture_explanation.md missing")

        with open(mmd_file, "r") as f:
            content = f.read()
            self.assertTrue("graph TD" in content or "flowchart TD" in content)
            self.assertIn("Apriori", content)
            self.assertIn("FP-Growth", content)
            self.assertIn("XGBoost", content)

    def test_02_input_output_parameter(self):
        """[02 Input/Output] Verify input/output schemas and sample predictions."""
        p02_dir = self.resolve_dir("02_input_output")
        in_schema = os.path.join(p02_dir, "input_schema.json")
        out_schema = os.path.join(p02_dir, "output_schema.json")
        sample_pred = os.path.join(p02_dir, "sample_prediction.json")
        spec_md = os.path.join(p02_dir, "input_output_specification.md")

        for fpath in [in_schema, out_schema, sample_pred, spec_md]:
            self.assertTrue(os.path.exists(fpath), f"Missing I/O artifact: {fpath}")

        # Validate JSON schemas
        with open(in_schema) as f:
            data_in = json.load(f)
            self.assertIn("properties", data_in)
            self.assertIn("grid_position", data_in["properties"])
            self.assertGreaterEqual(len(data_in["properties"]), 16)

        with open(sample_pred) as f:
            sample = json.load(f)
            self.assertIn("predictions", sample)
            self.assertGreater(len(sample["predictions"]), 0)

    def test_03_class_labels_parameter(self):
        """[03 Class Labels] Verify label generation, distribution, and zero nulls."""
        p03_dir = self.resolve_dir("03_class_labels")
        script = os.path.join(p03_dir, "label_generation.py")
        defs = os.path.join(p03_dir, "class_label_definitions.md")
        dist = os.path.join(p03_dir, "class_distribution_report.md")

        self.assertTrue(os.path.exists(script), "label_generation.py missing")
        self.assertTrue(os.path.exists(defs), "class_label_definitions.md missing")
        self.assertTrue(os.path.exists(dist), "class_distribution_report.md missing")

        data_csv = self.resolve_file("data", "processed", "F1_RACE_LAB_FEATURES_1994_2024.csv")
        df = pd.read_csv(data_csv, low_memory=False)
        self.assertEqual(df["target_is_win"].isnull().sum(), 0)
        self.assertEqual(int(df["target_is_win"].sum()), 577)

    def test_04_pattern_mining_parameter(self):
        """[04 Pattern Mining] Verify Apriori & FP-Growth scripts and association rules."""
        p04_dir = self.resolve_dir("04_pattern_mining")
        if not os.path.exists(p04_dir):
            p04_dir = self.resolve_dir("1_Pattern_Matching")

        ap_script = os.path.join(p04_dir, "apriori_analysis.py")
        fp_script = os.path.join(p04_dir, "fp_growth_analysis.py")
        rules_csv = os.path.join(p04_dir, "association_rules.csv")
        rpt = os.path.join(p04_dir, "pattern_mining_report.md")

        self.assertTrue(os.path.exists(ap_script), f"apriori_analysis.py missing in {p04_dir}")
        self.assertTrue(os.path.exists(fp_script), "fp_growth_analysis.py missing")
        self.assertTrue(os.path.exists(rules_csv), "association_rules.csv missing")
        self.assertTrue(os.path.exists(rpt), "pattern_mining_report.md missing")

        df_rules = pd.read_csv(rules_csv)
        self.assertGreater(len(df_rules), 100)
        self.assertGreater(df_rules["lift"].max(), 1.0)

    def test_05_algorithm_comparison_parameter(self):
        """[05 Algorithm Comparison] Verify 7 models benchmarked on chronological holdout."""
        p05_dir = self.resolve_dir("05_algorithm_comparison")
        if not os.path.exists(p05_dir):
            p05_dir = self.resolve_dir("2_Classification_Comparison")

        bench_csv = os.path.join(p05_dir, "comparison_results.csv")
        rpt = os.path.join(p05_dir, "comparison_report.md")
        script = os.path.join(p05_dir, "train_comparison.py")
        temp_val = os.path.join(p05_dir, "temporal_validation.py")

        self.assertTrue(os.path.exists(bench_csv), f"comparison_results.csv missing in {p05_dir}")
        self.assertTrue(os.path.exists(rpt), "comparison_report.md missing")
        self.assertTrue(os.path.exists(script), "train_comparison.py missing")
        self.assertTrue(os.path.exists(temp_val), "temporal_validation.py missing")

        df_bench = pd.read_csv(bench_csv)
        self.assertEqual(len(df_bench), 7)
        algo_names = " ".join(df_bench["algorithm"].tolist())
        for model_name in ["Dummy", "Baseline", "Decision Tree", "Random Forest", "Gradient Boosting", "LightGBM", "XGBoost"]:
            self.assertIn(model_name, algo_names)

    def test_06_classification_algorithm_parameter(self):
        """[06 Classification Algorithm] Verify pipeline, model card, and model artifact."""
        p06_dir = self.resolve_dir("06_classification_algorithm")
        if not os.path.exists(p06_dir):
            p06_dir = self.resolve_dir("3_Model_Classification_with_Performance_Metrics")

        fe_script = os.path.join(p06_dir, "feature_engineering.py")
        base_script = os.path.join(p06_dir, "baseline_classifier.py")
        imp_script = os.path.join(p06_dir, "improved_classifier.py")
        card = os.path.join(p06_dir, "model_card.md")
        
        artifact_candidates = [
            self.resolve_file("models", "champion_xgboost_classifier.joblib"),
            self.resolve_file("3_Model_Classification_with_Performance_Metrics", "champion_xgboost_classifier.joblib")
        ]
        artifact_exists = any(os.path.exists(p) for p in artifact_candidates)

        self.assertTrue(os.path.exists(fe_script), "feature_engineering.py missing")
        self.assertTrue(os.path.exists(base_script), "baseline_classifier.py missing")
        self.assertTrue(os.path.exists(imp_script), "improved_classifier.py missing")
        self.assertTrue(os.path.exists(card), "model_card.md missing")
        self.assertTrue(artifact_exists, "champion_xgboost_classifier.joblib missing")

    def test_07_innovation_parameter(self):
        """[07 Innovation] Verify innovation implementation and demonstrable improvement."""
        p07_dir = self.resolve_dir("07_innovation")
        prop = os.path.join(p07_dir, "innovation_proposal.md")
        impl = os.path.join(p07_dir, "innovation_implementation.py")
        exp = os.path.join(p07_dir, "baseline_vs_improved.py")
        res = os.path.join(p07_dir, "innovation_results.md")

        for fpath in [prop, impl, exp, res]:
            self.assertTrue(os.path.exists(fpath), f"Missing innovation artifact: {fpath}")

        # Check that comparison results show improvement over baseline
        p05_dir = self.resolve_dir("05_algorithm_comparison")
        if not os.path.exists(p05_dir):
            p05_dir = self.resolve_dir("2_Classification_Comparison")
        p05_csv = os.path.join(p05_dir, "comparison_results.csv")
        df_bench = pd.read_csv(p05_csv)
        base_auc = df_bench[df_bench["algorithm"].str.contains("Baseline")].iloc[0]["roc_auc"]
        xgb_auc = df_bench[df_bench["algorithm"].str.contains("XGBoost")].iloc[0]["roc_auc"]
        self.assertGreater(xgb_auc, base_auc, "Improved model must outperform baseline in ROC-AUC")

    def test_08_performance_metrics_parameter(self):
        """[08 Performance Metrics] Verify classification report, confusion matrix, and metrics."""
        p08_dir = self.resolve_dir("08_performance_metrics")
        if not os.path.exists(p08_dir):
            p08_dir = self.resolve_dir("3_Model_Classification_with_Performance_Metrics")

        calc_script = os.path.join(p08_dir, "calculate_metrics.py")
        rep_csv = os.path.join(p08_dir, "classification_report.csv")
        cm_csv = os.path.join(p08_dir, "confusion_matrix.csv")
        defs = os.path.join(p08_dir, "metric_definitions.md")
        ana = os.path.join(p08_dir, "performance_analysis.md")

        for fpath in [calc_script, rep_csv, cm_csv, defs, ana]:
            self.assertTrue(os.path.exists(fpath), f"Missing metrics artifact: {fpath}")

        df_cm = pd.read_csv(cm_csv, index_col=0)
        self.assertEqual(df_cm.shape, (2, 2))
        total_eval = df_cm.values.sum()
        self.assertEqual(total_eval, 1359, "Holdout set must evaluate exactly 1,359 entries")

    def test_09_evaluation_index_integrity(self):
        """Verify EVALUATION_INDEX.md exists and contains all core capabilities."""
        index_file = self.resolve_file("EVALUATION_INDEX.md")
        self.assertTrue(os.path.exists(index_file), "EVALUATION_INDEX.md missing")
        with open(index_file) as f:
            content = f.read()
            self.assertIn("Architecture", content)
            self.assertIn("Input / Output", content)
            self.assertIn("Class Labels", content)
            self.assertIn("Pattern Matching", content)
            self.assertIn("Algorithm Comparison", content)
            self.assertIn("Classification Algorithm", content)
            self.assertIn("Innovation", content)
            self.assertIn("Performance Metrics", content)

if __name__ == "__main__":
    unittest.main(verbosity=2)
