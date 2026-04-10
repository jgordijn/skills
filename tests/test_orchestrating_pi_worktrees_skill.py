from __future__ import annotations

import unittest
from pathlib import Path


SKILL_PATH = Path(__file__).resolve().parents[1] / "skills" / "orchestrating-pi-worktrees" / "SKILL.md"


class OrchestratingPiWorktreesSkillTests(unittest.TestCase):
    def test_skill_uses_rpc_helper_by_default(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("pi-rpc-prompt-runner.py", content)
        self.assertIn("pi --mode rpc", content)
        self.assertIn("plain `pi -p` only when the user asks for it", content)

    def test_skill_uses_bundled_extension_for_current_model_selection(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("get_current_pi_session_settings", content)
        self.assertIn("../extensions/current-pi-session-settings.js", content)
        self.assertIn("active runtime", content)
        self.assertIn("unless the user explicitly asks for another model", content)
        self.assertIn("--model <current-provider/model>", content)


if __name__ == "__main__":
    unittest.main()
