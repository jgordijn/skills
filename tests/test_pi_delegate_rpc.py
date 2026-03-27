from __future__ import annotations

import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "skills" / "delegating-pi-sessions" / "scripts" / "pi_delegate_rpc.py"


class FakeStdin:
    def __init__(self) -> None:
        self.writes: list[str] = []
        self.closed = False

    def write(self, text: str) -> None:
        self.writes.append(text)

    def flush(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True


class FakeProcess:
    def __init__(self, stdout_text: str, stderr_text: str = "", returncode: int = 0) -> None:
        self.stdin = FakeStdin()
        self.stdout = io.StringIO(stdout_text)
        self.stderr = io.StringIO(stderr_text)
        self.returncode = returncode
        self.terminated = False

    def poll(self) -> int | None:
        return self.returncode if self.stdin.closed else None

    def wait(self, timeout: float | None = None) -> int:
        self.stdin.close()
        return self.returncode

    def terminate(self) -> None:
        self.terminated = True
        self.stdin.close()


class PiDelegateRpcTests(unittest.TestCase):
    def setUp(self) -> None:
        spec = importlib.util.spec_from_file_location("pi_delegate_rpc", MODULE_PATH)
        if spec is None or spec.loader is None:
            raise AssertionError(f"Unable to load module from {MODULE_PATH}")
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_send_command_appends_jsonl_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)

            exit_code = self.module.main(
                [
                    "send",
                    str(runtime_dir),
                    "--type",
                    "steer",
                    "--message",
                    "Keep audit history in mind",
                ]
            )

            self.assertEqual(0, exit_code)
            commands_path = runtime_dir / "commands.jsonl"
            payload = json.loads(commands_path.read_text(encoding="utf-8").strip())
            self.assertEqual(
                {"type": "steer", "message": "Keep audit history in mind"},
                payload,
            )

    def test_run_processes_events_commands_and_writes_final_report(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workdir = root / "repo"
            workdir.mkdir()
            prompt_file = root / "delegate.md"
            prompt_file.write_text("Finish the delegated task", encoding="utf-8")
            runtime_dir = root / "runtime"

            events = "\n".join(
                [
                    json.dumps({"type": "agent_start"}),
                    json.dumps({"type": "message_start"}),
                    json.dumps(
                        {
                            "type": "message_update",
                            "assistantMessageEvent": {
                                "type": "text_delta",
                                "delta": "Delegated summary",
                            },
                        }
                    ),
                    json.dumps({"type": "message_end"}),
                    json.dumps(
                        {
                            "type": "response",
                            "command": "get_state",
                            "success": True,
                            "data": {
                                "isStreaming": False,
                                "pendingMessageCount": 0,
                            },
                        }
                    ),
                    json.dumps({"type": "agent_end", "messages": []}),
                ]
            )
            process = FakeProcess(events, stderr_text="delegate stderr\n")

            manager = self.module.DelegateManager(
                workdir=workdir,
                prompt_file=prompt_file,
                runtime_dir=runtime_dir,
                model="openai/gpt-5",
                process_factory=lambda *args, **kwargs: process,
                poll_interval=0.0,
                exit_grace_seconds=0.0,
                sleep=lambda _seconds: None,
            )

            self.assertEqual(0, manager.run())

            sent_payloads = [json.loads(item) for item in process.stdin.writes]
            self.assertEqual(
                {
                    "id": "initial-prompt",
                    "type": "prompt",
                    "message": "Finish the delegated task",
                },
                sent_payloads[0],
            )
            self.assertTrue((runtime_dir / "events.jsonl").exists())
            self.assertEqual(
                "Delegated summary",
                (runtime_dir / "assistant-last.txt").read_text(encoding="utf-8"),
            )
            self.assertEqual(
                "Delegated summary",
                (runtime_dir / "final-report.txt").read_text(encoding="utf-8"),
            )
            status = json.loads((runtime_dir / "status.json").read_text(encoding="utf-8"))
            self.assertEqual("completed", status["phase"])
            self.assertFalse(status["piRunning"])
            self.assertEqual("get_state", status["lastResponse"]["command"])
            self.assertEqual("delegate stderr\n", (runtime_dir / "stderr.log").read_text(encoding="utf-8"))

    def test_run_records_invalid_command_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            workdir = root / "repo"
            workdir.mkdir()
            prompt_file = root / "delegate.md"
            prompt_file.write_text("Inspect things", encoding="utf-8")
            runtime_dir = root / "runtime"
            runtime_dir.mkdir()
            (runtime_dir / "commands.jsonl").write_text("not-json\n", encoding="utf-8")

            process = FakeProcess(json.dumps({"type": "agent_end", "messages": []}))
            manager = self.module.DelegateManager(
                workdir=workdir,
                prompt_file=prompt_file,
                runtime_dir=runtime_dir,
                model="openai/gpt-5",
                process_factory=lambda *args, **kwargs: process,
                poll_interval=0.0,
                exit_grace_seconds=0.0,
                sleep=lambda _seconds: None,
            )

            self.assertEqual(0, manager.run())
            status = json.loads((runtime_dir / "status.json").read_text(encoding="utf-8"))
            self.assertIn("Invalid command JSON", status["errors"][0])

    def test_status_command_prints_status_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            runtime_dir = Path(temp_dir)
            expected = {"phase": "running", "piRunning": True}
            (runtime_dir / "status.json").write_text(json.dumps(expected), encoding="utf-8")

            with io.StringIO() as output, redirect_stdout(output):
                exit_code = self.module.main(["status", str(runtime_dir)])
                printed = output.getvalue()

            self.assertEqual(0, exit_code)
            self.assertEqual(json.dumps(expected, indent=2) + "\n", printed)


if __name__ == "__main__":
    unittest.main()
