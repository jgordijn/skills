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

    def test_skill_documents_supaterm_or_tmux_detection_with_tmux_fallback(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("if [ -n \"$TMUX\" ]; then", content)
        self.assertIn("elif [ -n \"${SUPATERM_SOCKET_PATH:-}\" ] && command -v sp >/dev/null; then", content)
        self.assertIn("fallback to tmux", content)
        self.assertIn("sp tab new --focus --cwd /path/to/worktree --script", content)

    def test_skill_does_not_keep_shell_open_after_delegate_finishes(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertNotIn("; exec zsh", content)
    def test_skill_supaterm_path_auto_closes_tab_after_delegate_finishes(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("sp tab close", content)
        lines = content.splitlines()
        in_supaterm_branch = False
        supaterm_has_close = False
        tmux_has_close = False
        for line in lines:
            if 'elif [ -n "${SUPATERM_SOCKET_PATH:-}" ]' in line:
                in_supaterm_branch = True
            elif line.strip().startswith("else"):
                in_supaterm_branch = False
            if "sp tab close" in line:
                if in_supaterm_branch:
                    supaterm_has_close = True
                else:
                    tmux_has_close = True
        self.assertTrue(supaterm_has_close, "Supaterm branch should include 'sp tab close'")
        self.assertFalse(tmux_has_close, "tmux branches should NOT include 'sp tab close'")




if __name__ == "__main__":
    unittest.main()
