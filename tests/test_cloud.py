import copy
import importlib.util
import unittest
from datetime import datetime, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location('updater', Path(__file__).resolve().parents[1] / 'scripts/update.py')
u = importlib.util.module_from_spec(spec)
spec.loader.exec_module(u)

class CloudChecks(unittest.TestCase):
    def setUp(self):
        self.base = {'sections': [{'topic':'inflacion','period':'2026-08-01','fact':'El IPC varió 1,66%.',
                                  'title':'El ritmo de los precios','reading':'Una lectura cautelosa.','limit':'No identifica causalidad.'}]}
        self.cloud = {'fingerprint':'abc','generated_at':datetime.now(timezone.utc).isoformat(),
                      'sections':copy.deepcopy(self.base['sections'])}

    def test_accept_matching_evidence(self):
        u.validate_cloud(self.cloud, 'abc', self.base)

    def test_reject_changed_facts(self):
        self.cloud['sections'][0]['fact'] = 'Otro dato'
        with self.assertRaises(ValueError):u.validate_cloud(self.cloud,'abc',self.base)

    def test_reject_other_fingerprint(self):
        with self.assertRaises(ValueError):u.validate_cloud(self.cloud,'xyz',self.base)

    def test_reject_new_numbers(self):
        self.cloud['sections'][0]['reading'] = 'Una suba de 10%.'
        with self.assertRaises(ValueError):u.validate_cloud(self.cloud,'abc',self.base)

if __name__ == '__main__':unittest.main()
