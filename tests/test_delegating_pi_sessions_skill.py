from __future__ import annotations

import unittest
from pathlib import Path


SKILL_PATH = Path(__file__).resolve().parents[1] / "skills" / "delegating-pi-sessions" / "SKILL.md"


class DelegatingPiSessionsSkillTests(unittest.TestCase):
    def test_skill_mentions_optional_worktrees_rpc_and_steering(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("with or without a separate git worktree", content)
        self.assertIn("RPC", content)
        self.assertIn("steer", content)
        self.assertIn("follow_up", content)
        self.assertIn("final-report.txt", content)
        self.assertIn("commands.jsonl", content)


if __name__ == "__main__":
    unittest.main()
