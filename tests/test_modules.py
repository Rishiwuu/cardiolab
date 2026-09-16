"""Unit test suite for CardioLab modules.

Validates that individual components (config, mutation database, simulation engine,
feature extraction, ECG simulation, and clinical insight formatting) behave correctly
and return valid data structures.
"""

import unittest
from pathlib import Path

# Adjust path to import CardioLab modules
import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))

from CardioLab.config import MODEL_DATABASE
from CardioLab.mutation_database import list_mutations, get_mutation
from CardioLab.simulation import run_simulation
from CardioLab.features import extract_ap_features
from CardioLab.ecg import generate_pseudo_ecg, estimate_rr_interval, calculate_heart_rate
from CardioLab.clinical import generate_clinical_insight
from CardioLab.comparison import run_multi_mutation_comparison
from CardioLab.restitution import run_restitution_protocol


class TestMutationDatabase(unittest.TestCase):
    def test_list_mutations(self):
        mutations = list_mutations()
        self.assertIn("Normal", mutations)
        self.assertIn("SCN5A R1623Q", mutations)
        self.assertIn("KCNH2 N588K", mutations)

    def test_get_mutation(self):
        wt = get_mutation("Normal")
        self.assertIsNotNone(wt)
        self.assertEqual(wt["gene"], "None")
        self.assertEqual(wt["multiplier"], 1.0)
        self.assertEqual(wt["simulation"]["operation"], "multiply")

        mut = get_mutation("SCN5A R1623Q")
        self.assertIsNotNone(mut)
        self.assertEqual(mut["gene"], "SCN5A")
        self.assertEqual(mut["multiplier"], 1.5)
        self.assertEqual(mut["simulation"]["parameter"], "ina.gNaBar")


class TestSimulationEngine(unittest.TestCase):
    def test_run_simulation_wildtype(self):
        wt_config = get_mutation("Normal")["simulation"]
        log_normal, log_mutated, pacing_period, warning = run_simulation("Beeler-Reuter", wt_config)

        self.assertIsNone(warning)
        self.assertEqual(pacing_period, 1000.0)
        self.assertIn("membrane.V", log_normal)
        self.assertIn("engine.time", log_normal)
        self.assertIn("membrane.V", log_mutated)

    def test_run_simulation_invalid_model(self):
        with self.assertRaises(ValueError):
            run_simulation("Ten Tusscher", {})


class TestFeatureExtraction(unittest.TestCase):
    def test_extract_ap_features(self):
        # Retrieve wildtype simulation log
        wt_config = get_mutation("Normal")["simulation"]
        log_normal, _, _, _ = run_simulation("Beeler-Reuter", wt_config)

        time = log_normal["engine.time"]
        voltage = log_normal["membrane.V"]

        features = extract_ap_features(time, voltage)
        self.assertIn("resting_potential", features)
        self.assertIn("peak_voltage", features)
        self.assertIn("amplitude", features)
        self.assertIn("max_upstroke_velocity", features)
        self.assertIn("apd90", features)
        self.assertIn("apd50", features)

        self.assertLess(features["resting_potential"], -70.0)
        self.assertGreater(features["peak_voltage"], 0.0)
        self.assertGreater(features["apd90"], 200.0)
        self.assertLess(features["apd90"], 400.0)


class TestECGSimulator(unittest.TestCase):
    def test_generate_pseudo_ecg(self):
        wt_config = get_mutation("Normal")["simulation"]
        log_normal, _, pacing_period, _ = run_simulation("Beeler-Reuter", wt_config)

        time = log_normal["engine.time"]
        voltage = log_normal["membrane.V"]
        features = extract_ap_features(time, voltage)

        ecg_time, ecg_signal = generate_pseudo_ecg(time, voltage, features)
        self.assertEqual(len(ecg_time), len(time))
        self.assertEqual(len(ecg_signal), len(voltage))

        # Check normalization (peak amplitude should be exactly 1.0)
        self.assertAlmostEqual(max(abs(ecg_signal)), 1.0, places=5)

    def test_metrics(self):
        rr = estimate_rr_interval(1000.0)
        self.assertEqual(rr, 1000.0)
        hr = calculate_heart_rate(rr)
        self.assertEqual(hr, 60.0)


class TestClinicalInterpretation(unittest.TestCase):
    def test_clinical_insight(self):
        mut_data = get_mutation("SCN5A R1623Q")
        norm_feat = {"apd90": 290.0}
        mut_feat = {"apd90": 340.0}
        hr = 60.0

        insights = generate_clinical_insight(mut_data, norm_feat, mut_feat, hr)
        self.assertEqual(insights["mutation_title"], "SCN5A R1623Q")
        self.assertEqual(insights["syndrome"], "Long QT Syndrome Type 3 (LQT3)")
        self.assertEqual(insights["normal_apd90"], "290.0 ms")
        self.assertEqual(insights["mutated_apd90"], "340.0 ms")
        self.assertEqual(insights["heart_rate"], "60.0 bpm")
        self.assertIn("Autosomal Dominant", insights["inheritance"])
        self.assertIn("RCV000003294", insights["clinvar_id"])
        self.assertIn("Educational Disclaimer", insights["disclaimer"])


class TestMultiMutationComparison(unittest.TestCase):
    def test_run_multi_mutation_comparison(self):
        # Compare Normal and KCNH2 N588K
        results = run_multi_mutation_comparison("Beeler-Reuter", ["Normal", "KCNH2 N588K"])
        self.assertIn("Normal", results)
        self.assertIn("KCNH2 N588K", results)

        # Check logs and features exist
        normal_log, normal_feats = results["Normal"]
        mutated_log, mutated_feats = results["KCNH2 N588K"]

        self.assertIn("membrane.V", normal_log)
        self.assertIn("membrane.V", mutated_log)
        self.assertGreater(normal_feats["apd90"], 200.0)
        self.assertLess(mutated_feats["apd90"], 260.0)  # SQT1 variant should shorten APD90 vs ~292ms baseline


class TestAPDRestitution(unittest.TestCase):
    def test_run_restitution_protocol(self):
        # Run restitution curve for normal wildtype at 3 cycle lengths
        cycle_lengths = [1000.0, 500.0, 300.0]
        wt_config = get_mutation("Normal")["simulation"]
        results = run_restitution_protocol("Beeler-Reuter", wt_config, cycle_lengths=cycle_lengths, beats_to_steady_state=2)

        self.assertEqual(len(results), len(cycle_lengths))
        # Unpack values
        pcl_1000, apd_1000 = results[0]
        pcl_500, apd_500 = results[1]
        pcl_300, apd_300 = results[2]

        self.assertEqual(pcl_1000, 1000.0)
        self.assertEqual(pcl_500, 500.0)
        self.assertEqual(pcl_300, 300.0)

        # Confirm physiological APD restitution property (shorter pacing period leads to shorter APD)
        self.assertGreaterEqual(apd_1000, apd_500)
        self.assertGreaterEqual(apd_500, apd_300)


if __name__ == "__main__":
    unittest.main()
