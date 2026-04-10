from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


RPC_SCRIPT_PATH = Path(__file__).resolve().parents[1] / "skills" / "delegating-pi-sessions" / "scripts" / "pi_delegate_rpc.py"
SCRIPT_PATH = Path(__file__).resolve().parents[1] / "skills" / "delegating-pi-sessions" / "scripts" / "pi_delegate_inherit_session.py"


def write_session_file(path: Path, *entries: dict[str, object]) -> None:
    path.write_text("\n".join(json.dumps(entry) for entry in entries) + "\n", encoding="utf-8")


class DelegatingPiSessionsScriptTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertFalse(RPC_SCRIPT_PATH.exists())
        spec = importlib.util.spec_from_file_location("pi_delegate_inherit_session", SCRIPT_PATH)
        if spec is None or spec.loader is None:
            raise AssertionError(f"Unable to load module from {SCRIPT_PATH}")
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_resolve_source_session_file_prefers_explicit_path_then_env(self) -> None:
        explicit = Path("/tmp/explicit-session.jsonl")
        env = {"PI_SESSION_FILE": "/tmp/env-session.jsonl"}

        self.assertEqual(explicit, self.module.resolve_source_session_file(explicit, env))
        self.assertEqual(Path("/tmp/env-session.jsonl"), self.module.resolve_source_session_file(None, env))

    def test_resolve_source_session_file_requires_explicit_or_env(self) -> None:
        with self.assertRaisesRegex(ValueError, "PI_SESSION_FILE"):
            self.module.resolve_source_session_file(None, {})

    def test_read_session_defaults_prefers_latest_model_change_and_thinking(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_file = Path(temp_dir) / "source-session.jsonl"
            write_session_file(
                session_file,
                {"type": "session", "version": 3, "id": "session-id", "timestamp": "2026-04-10T09:00:00Z", "cwd": "/tmp/project"},
                {"type": "message", "message": {"role": "assistant"}, "provider": "openai", "model": "gpt-5"},
                {"type": "thinking_level_change", "thinkingLevel": "medium"},
                {"type": "model_change", "provider": "openrouter", "modelId": "anthropic/claude-sonnet-4-5"},
                {"type": "thinking_level_change", "thinkingLevel": "high"},
            )

            defaults = self.module.read_session_defaults(session_file)

            self.assertEqual("openrouter/anthropic/claude-sonnet-4-5", defaults.model)
            self.assertEqual("high", defaults.thinking)

    def test_read_session_defaults_falls_back_to_assistant_message_model(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_file = Path(temp_dir) / "source-session.jsonl"
            write_session_file(
                session_file,
                {"type": "session", "version": 3, "id": "session-id", "timestamp": "2026-04-10T09:00:00Z", "cwd": "/tmp/project"},
                {
                    "type": "message",
                    "message": {"role": "assistant"},
                    "provider": "openai",
                    "model": "gpt-5",
                },
            )

            defaults = self.module.read_session_defaults(session_file)

            self.assertEqual("openai/gpt-5", defaults.model)
            self.assertIsNone(defaults.thinking)

    def test_read_session_defaults_rejects_missing_invalid_or_model_less_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            missing_session_file = temp_path / "missing-session.jsonl"
            with self.assertRaisesRegex(FileNotFoundError, "does not exist"):
                self.module.read_session_defaults(missing_session_file)

            invalid_session_file = temp_path / "invalid-session.jsonl"
            invalid_session_file.write_text("not-json\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid JSON"):
                self.module.read_session_defaults(invalid_session_file)

            model_less_session_file = temp_path / "model-less-session.jsonl"
            write_session_file(
                model_less_session_file,
                {"type": "session", "version": 3, "id": "session-id", "timestamp": "2026-04-10T09:00:00Z", "cwd": "/tmp/project"},
                {"type": "thinking_level_change", "thinkingLevel": "low"},
            )
            with self.assertRaisesRegex(ValueError, "Unable to resolve model"):
                self.module.read_session_defaults(model_less_session_file)

    def test_format_shell_exports_quotes_values_and_handles_missing_thinking(self) -> None:
        defaults = self.module.SessionDefaults(model="openrouter/anthropic/claude sonnet", thinking=None)

        self.assertEqual(
            "delegate_model='openrouter/anthropic/claude sonnet'\ndelegate_thinking=''\n",
            self.module.format_shell_exports(defaults),
        )

    def test_main_prints_shell_exports(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_file = Path(temp_dir) / "source-session.jsonl"
            write_session_file(
                session_file,
                {"type": "session", "version": 3, "id": "session-id", "timestamp": "2026-04-10T09:00:00Z", "cwd": "/tmp/project"},
                {"type": "model_change", "provider": "openai", "modelId": "gpt-5"},
                {"type": "thinking_level_change", "thinkingLevel": "minimal"},
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            exit_code = self.module.main(["--session-file", str(session_file)], env={}, stdout=stdout, stderr=stderr)

            self.assertEqual(0, exit_code)
            self.assertEqual("delegate_model=openai/gpt-5\ndelegate_thinking=minimal\n", stdout.getvalue())
            self.assertEqual("", stderr.getvalue())

    def test_main_can_print_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            session_file = Path(temp_dir) / "source-session.jsonl"
            write_session_file(
                session_file,
                {"type": "session", "version": 3, "id": "session-id", "timestamp": "2026-04-10T09:00:00Z", "cwd": "/tmp/project"},
                {"type": "model_change", "provider": "openai", "modelId": "gpt-5"},
            )

            stdout = io.StringIO()
            stderr = io.StringIO()
            exit_code = self.module.main(["--format", "json", "--session-file", str(session_file)], env={}, stdout=stdout, stderr=stderr)

            self.assertEqual(0, exit_code)
            self.assertEqual({"model": "openai/gpt-5", "thinking": None}, json.loads(stdout.getvalue()))
            self.assertEqual("", stderr.getvalue())

    def test_main_reports_resolution_errors(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        exit_code = self.module.main([], env={}, stdout=stdout, stderr=stderr)

        self.assertEqual(1, exit_code)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("PI_SESSION_FILE", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
