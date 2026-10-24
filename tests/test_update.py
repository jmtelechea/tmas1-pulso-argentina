import importlib.util
import unittest
from datetime import date
from pathlib import Path

spec = importlib.util.spec_from_file_location('update', Path(__file__).resolve().parents[1] / 'scripts/update.py')
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)

class Checks(unittest.TestCase):
    def test_compound_is_not_sum(self):
        self.assertAlmostEqual(u.compound([{'value': .1}, {'value': .1}]), 21)

    def test_monthly_change(self):
        self.assertAlmostEqual(u.change([{'value': 100}, {'value': 110}]), 10)

    def test_reject_future(self):
        points = [{'date': f'2024-{i:02d}-01', 'value': 100} for i in range(1, 13)]
        points.append({'date': '2099-01-01', 'value': 100})
        with self.assertRaises(ValueError):
            u.validate(points, 'emae')

    def test_reject_missing_month(self):
        points = [{'date': f'2024-{i:02d}-01', 'value': .02} for i in range(1, 13)]
        points.append({'date': '2025-02-01', 'value': .02})
        with self.assertRaises(ValueError):
            u.validate(points, 'ipc')

    def test_reject_nan(self):
        points = [{'date': f'2024-{i:02d}-01', 'value': .02} for i in range(1, 13)]
        points.append({'date': '2025-01-01', 'value': float('nan')})
        with self.assertRaises(ValueError):
            u.validate(points, 'ipc')

if __name__ == '__main__':
    unittest.main()
