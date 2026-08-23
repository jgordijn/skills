from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = ROOT / "skills" / "delegating-pi-sessions" / "SKILL.md"
REMOVED_SKILL_PATH = ROOT / "skills" / "orchestrating-pi-worktrees"


class DelegatingPiSessionsSkillTests(unittest.TestCase):
    def test_skill_is_the_single_herdr_delegation_workflow(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn('test "${HERDR_ENV:-}" = 1', content)
        self.assertIn("herdr tab create", content)
        self.assertIn("herdr agent start", content)
        self.assertIn("herdr agent prompt", content)
        self.assertNotIn("tmux", content.lower())
        self.assertNotIn("supaterm", content.lower())
        self.assertNotIn("--mode rpc", content.lower())
        self.assertNotIn("pi -p", content.lower())

    def test_skill_supports_same_workspace_or_isolated_worktree(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("with or without a separate git worktree", content)
        self.assertIn("git worktree add", content)
        self.assertIn("non-overlapping", content)

    def test_parent_owns_tab_lifetime_and_may_reuse_delegate(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("parent owns the tab lifetime", content.lower())
        self.assertIn("reuse", content.lower())
        self.assertIn("herdr tab close", content)
        self.assertIn("capture", content.lower())
        self.assertIn("child must not close its own pane or tab", content.lower())
        self.assertIn("do not ask the child to close itself", content.lower())

    def test_obsolete_orchestration_skill_is_removed(self) -> None:
        self.assertFalse(REMOVED_SKILL_PATH.exists())


if __name__ == "__main__":
    unittest.main()
