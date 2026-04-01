from __future__ import annotations

import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "skills" / "delegating-pi-sessions" / "scripts" / "pi_delegate_rpc.py"


class DelegatingPiSessionsScriptTests(unittest.TestCase):
    def test_python_rpc_helper_script_is_removed(self) -> None:
        self.assertFalse(SCRIPT_PATH.exists())


if __name__ == "__main__":
    unittest.main()
