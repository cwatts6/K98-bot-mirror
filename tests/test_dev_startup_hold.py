import unittest
from unittest.mock import patch

from dev_startup_hold import enforce_dev_startup_hold


class DevStartupHoldTests(unittest.TestCase):
    @patch("dev_startup_hold.sys.platform", "win32")
    def test_guest_name_holds_before_policy_lookup(self):
        with patch("socket.gethostname", return_value="K98-DEV-VM"), patch("os.lstat") as lookup:
            with self.assertRaisesRegex(SystemExit, "^K98 DEV startup held$"):
                enforce_dev_startup_hold()
            lookup.assert_not_called()

    @patch("dev_startup_hold.sys.platform", "win32")
    def test_protected_directory_and_lookup_errors_hold(self):
        for error in (None, PermissionError()):
            with self.subTest(error=error), patch("socket.gethostname", return_value="other"), \
                    patch("os.lstat", side_effect=error):
                with self.assertRaisesRegex(SystemExit, "^K98 DEV startup held$"):
                    enforce_dev_startup_hold()

    @patch("dev_startup_hold.sys.platform", "win32")
    def test_unknown_name_holds(self):
        with patch("socket.gethostname", side_effect=OSError()):
            with self.assertRaisesRegex(SystemExit, "^K98 DEV startup held$"):
                enforce_dev_startup_hold()

    @patch("dev_startup_hold.sys.platform", "win32")
    def test_unenrolled_host_continues(self):
        with patch("socket.gethostname", return_value="other"), patch("os.lstat", side_effect=FileNotFoundError()):
            enforce_dev_startup_hold()
