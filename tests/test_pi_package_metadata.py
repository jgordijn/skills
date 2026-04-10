from __future__ import annotations

import json
import unittest
from pathlib import Path


PACKAGE_PATH = Path(__file__).resolve().parents[1] / "package.json"


class PiPackageMetadataTests(unittest.TestCase):
    def test_package_manifest_registers_skills_and_extensions(self) -> None:
        package = json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(["./skills"], package["pi"]["skills"])
        self.assertEqual(["./extensions"], package["pi"]["extensions"])


if __name__ == "__main__":
    unittest.main()
