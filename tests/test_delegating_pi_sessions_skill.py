from __future__ import annotations

import unittest
from pathlib import Path


SKILL_PATH = Path(__file__).resolve().parents[1] / "skills" / "delegating-pi-sessions" / "SKILL.md"


class DelegatingPiSessionsSkillTests(unittest.TestCase):
    def test_skill_uses_project_tmp_sessions_from_visible_subtask_hosts(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("with or without a separate git worktree", content)
        self.assertIn("`pi -p`", content)
        self.assertIn("--session-dir .tmp/pi-sessions", content)
        self.assertIn(".tmp/delegate-name.log", content)
        self.assertIn("Do not use `--no-session`", content)
        self.assertNotIn("/path/to/workdir/.tmp/pi-sessions", content)
        self.assertNotIn("Default to a direct one-shot `pi -p` launch", content)

    def test_skill_uses_bundled_extension_to_detect_current_runtime_defaults(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("get_current_pi_session_settings", content)
        self.assertIn("../extensions/current-pi-session-settings.js", content)
        self.assertIn("call `get_current_pi_session_settings`", content)
        self.assertIn("active runtime", content)
        self.assertIn("unless the user explicitly asks for a different provider, model, or thinking level", content)

    def test_skill_keeps_saved_session_helper_only_as_a_fallback(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("scripts/pi_delegate_inherit_session.py", content)
        self.assertIn("saved session file", content)
        self.assertIn("fallback", content)
        self.assertNotIn("python3 - <<'PY'", content)
        self.assertNotIn("<skill-dir>/scripts/pi_delegate_inherit_session.py", content)

    def test_skill_no_longer_describes_rpc_runtime_control_files(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertNotIn("pi_delegate_rpc.py", content)
        self.assertNotIn("commands.jsonl", content)
        self.assertNotIn("events.jsonl", content)
        self.assertNotIn("status.json", content)
        self.assertNotIn("final-report.txt", content)

    def test_skill_documents_supaterm_or_tmux_detection_with_tmux_fallback(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn('if [ -n "$TMUX" ]; then', content)
        self.assertIn('elif [ -n "${SUPATERM_SOCKET_PATH:-}" ] && command -v sp >/dev/null; then', content)
        self.assertIn("fallback to tmux", content)
        self.assertIn("sp tab new --focus --cwd /path/to/workdir --script", content)

    def test_skill_uses_pi_subtask_title_template_for_tabs_and_windows(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("`[PI-SUB] <description>`", content)
        self.assertIn('"[PI-SUB] Review code"', content)
        self.assertIn('tmux new-window -n "[PI-SUB] Review code"', content)
        self.assertIn('sp tab rename "[PI-SUB] Review code"', content)

    def test_skill_auto_closes_supaterm_tabs_and_tmux_windows_after_delegate_finishes(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertNotIn("; exec zsh", content)
        self.assertGreaterEqual(content.count("tmux kill-window"), 2)
        self.assertIn("sp tab close", content)


if __name__ == "__main__":
    unittest.main()
