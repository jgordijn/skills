from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_PATH = ROOT / "skills" / "delegating-pi-sessions" / "SKILL.md"
REMOVED_SKILL_PATH = ROOT / "skills" / "orchestrating-pi-worktrees"


class DelegatingPiSessionsSkillTests(unittest.TestCase):
    def test_skill_uses_only_interactive_herdr_delegates(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn('test "${HERDR_ENV:-}" = 1', content)
        self.assertIn("all delegates are interactive pi agents", content.lower())
        self.assertIn("newly created herdr tab", content.lower())
        self.assertIn("herdr tab create", content)
        self.assertIn("herdr agent start", content)
        self.assertIn("herdr agent prompt", content)
        self.assertIn("Never use `pi -p`, RPC, tmux, or Supaterm", content)
        self.assertNotIn("--mode rpc", content.lower())
        self.assertNotIn("tmux new", content.lower())
        self.assertNotIn("sp tab create", content.lower())

    def test_standard_programming_route_uses_sol_medium(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("standard programming or implementation", content.lower())
        self.assertIn("github-copilot/gpt-5.6-sol", content)
        self.assertIn("thinking `medium`", content)

    def test_critical_review_route_uses_kimi_high(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("critical code review or adversarial verification", content.lower())
        self.assertIn("github-copilot/kimi-k3", content)
        self.assertIn("thinking `high`", content)

    def test_easy_mechanical_route_uses_luna_max(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("easy, mechanical, tightly bounded", content.lower())
        self.assertIn("github-copilot/gpt-5.6-luna", content)
        self.assertIn("thinking `max`", content)

    def test_explicit_user_route_always_takes_precedence(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn("explicit user-specified provider, model, or thinking", content.lower())
        self.assertIn("always overrides", content.lower())
        self.assertIn("never silently replace", content.lower())
        self.assertIn("report the problem and ask before substituting", content.lower())

    def test_launch_uses_interactive_herdr_and_pi_argument_passthrough(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")
        command_lines: list[str] = []
        in_bash_block = False
        for line in content.splitlines():
            if line == "```bash":
                in_bash_block = True
            elif line == "```":
                in_bash_block = False
            elif in_bash_block and line.strip() and not line.lstrip().startswith("#"):
                command_lines.append(line.strip())

        expected_launch = (
            'herdr agent start "$agent_name" --kind pi --pane "$root_pane_id" -- '
            '--model "$model" --thinking "$thinking"'
        )
        self.assertEqual(
            [line for line in command_lines if line.startswith("herdr agent start")],
            [expected_launch],
        )
        self.assertNotIn(
            'herdr agent start "$agent_name" --kind pi --pane "$root_pane_id" '
            '--model "$model" --thinking "$thinking"',
            command_lines,
        )
        normalized_commands = "\n".join(command_lines).lower()
        self.assertNotIn("pi -p", normalized_commands)
        self.assertNotIn("--mode rpc", normalized_commands)
        self.assertNotIn("tmux ", normalized_commands)
        self.assertNotIn("sp ", normalized_commands)
        self.assertNotIn("supaterm ", normalized_commands)

    def test_route_selection_initializes_nonempty_launch_variables(self) -> None:
        content = SKILL_PATH.read_text(encoding="utf-8")

        self.assertIn('agent_name="<unique-name>"', content)
        self.assertIn('root_pane_id="<root-pane-id-from-tab-create-json>"', content)
        self.assertIn('model="${requested_model:-$default_model}"', content)
        self.assertIn('thinking="${requested_thinking:-$default_thinking}"', content)
        self.assertIn(': "${agent_name:?agent_name must be set}"', content)
        self.assertIn(': "${root_pane_id:?root_pane_id must be set}"', content)
        self.assertIn(': "${model:?model must be set}"', content)
        self.assertIn(': "${thinking:?thinking must be set}"', content)

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
        self.assertIn("do not run any Herdr or Supaterm close command", content)

    def test_obsolete_orchestration_skill_is_removed(self) -> None:
        self.assertFalse(REMOVED_SKILL_PATH.exists())


if __name__ == "__main__":
    unittest.main()
