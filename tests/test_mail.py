import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('pilot_mail', Path(__file__).resolve().parents[1] / 'scripts/mail.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class MailChecks(unittest.TestCase):
    def test_without_credentials_does_not_send(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(m, 'deliver') as send:
            m.main()
            send.assert_not_called()

    def test_connection_test_uses_only_configured_recipient(self):
        env = {'SMTP_USER': 'pilot@example.com', 'SMTP_PASSWORD': 'fake-for-test', 'MAIL_TEST': 'true'}
        with patch.dict(os.environ, env, clear=True), patch.object(m, 'deliver') as send:
            m.main()
            send.assert_called_once()
            msg = send.call_args.args[0]
            self.assertEqual(msg['To'], 'pilot@example.com')
            self.assertIn('no confirma', msg.get_content())

if __name__ == '__main__':
    unittest.main()
