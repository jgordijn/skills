from __future__ import annotations

import unittest
from pathlib import Path


SKILL_PATH = Path(__file__).resolve().parents[1] / "skills" / "delegating-pi-sessions" / "SKILL.md"


class DelegatingPiSessionsSkillTests(unittest.TestCase):
    def test_skill_uses_direct_print_mode_with_project_tmp_sessions(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("with or without a separate git worktree", content)
        self.assertIn("`pi -p`", content)
        self.assertIn("--session-dir .tmp/pi-sessions", content)
        self.assertIn(".tmp/delegate-name.log", content)
        self.assertIn("Do not use `--no-session`", content)
        self.assertNotIn("/path/to/workdir/.tmp/pi-sessions", content)

    def test_skill_references_reusable_inheritance_script_instead_of_inline_python(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("same provider/model routing and thinking level as the current session", content)
        self.assertIn("## Bundled scripts", content)
        self.assertIn("relative to this `SKILL.md` file / skill root", content)
        self.assertIn("scripts/pi_delegate_inherit_session.py", content)
        self.assertIn("PI_SESSION_FILE", content)
        self.assertIn("source session file", content)
        self.assertIn("--thinking", content)
        self.assertIn("Only override", content)
        self.assertNotIn("python3 - <<'PY'", content)
        self.assertNotIn("<skill-dir>/scripts/pi_delegate_inherit_session.py", content)

    def test_skill_no_longer_describes_rpc_runtime_control_files(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertNotIn("pi_delegate_rpc.py", content)
        self.assertNotIn("commands.jsonl", content)
        self.assertNotIn("events.jsonl", content)
        self.assertNotIn("status.json", content)
        self.assertNotIn("final-report.txt", content)


if __name__ == "__main__":
    unittest.main()
