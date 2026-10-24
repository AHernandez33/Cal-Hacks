"""Run from SCD root: python -m unittest discover -s tests -p test_federated.py"""
import unittest
import torch
from backend.federated import LeafRiskMLP, fedavg, make_demo_data, run_demo


class FederatedTests(unittest.TestCase):
    def test_disabled_by_default(self):
        with self.assertRaises(PermissionError):
            run_demo(rounds=1)

    def test_one_client_only(self):
        result = run_demo(consent={"greenhouse_a": True}, rounds=2)
        self.assertEqual(result["participating_clients"], ["greenhouse_a"])
        self.assertEqual(len(result["excluded_clients"]), 2)
        self.assertEqual(len(result["history"]), 2)
        for key in ("accuracy", "precision", "recall", "f1"):
            self.assertGreaterEqual(result["federated_final"][key], 0)
            self.assertLessEqual(result["federated_final"][key], 1)

    def test_three_clients(self):
        result = run_demo(consent={name: True for name in (
            "greenhouse_a", "greenhouse_b", "greenhouse_c")}, rounds=2)
        self.assertEqual(len(result["participating_clients"]), 3)
        self.assertEqual(result["holdout_samples"], 240)

    def test_independent_synthetic_sets(self):
        clients, holdout = make_demo_data()
        self.assertFalse(torch.equal(clients[0].features, clients[1].features))
        self.assertFalse(torch.equal(clients[0].features, holdout[0][:120]))

    def test_fedavg_weights(self):
        a, b = LeafRiskMLP(), LeafRiskMLP()
        with torch.no_grad():
            for p in a.parameters():
                p.fill_(0)
            for p in b.parameters():
                p.fill_(1)
        average = fedavg([a, b], [1, 3])
        self.assertTrue(all(torch.allclose(v, torch.full_like(v, 0.75)) for v in average.values()))


if __name__ == "__main__":
    unittest.main()
