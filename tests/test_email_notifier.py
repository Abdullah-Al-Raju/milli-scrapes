"""
Unit tests for EmailNotifier.
"""

import unittest
from milli_scrapes.notifier.email import EmailNotifier


class TestEmailNotifier(unittest.TestCase):

    def test_dry_run_alert_dispatch(self):
        notifier = EmailNotifier(
            recipient_email="analystx.raju@gmail.com",
            dry_run=True
        )

        res = notifier.send_alert(
            subject="Test Alert: Seat Available",
            body_text="Seat A1 is ready for booking.",
            snapshot_jpeg=b"\xff\xd8\xff\xe0mock_jpeg_bytes"
        )

        self.assertEqual(res["status"], "simulated")
        self.assertEqual(res["recipient"], "analystx.raju@gmail.com")
        self.assertEqual(res["attachment_bytes"], 19)


if __name__ == "__main__":
    unittest.main()
