#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable


JsonDict = dict[str, Any]
ProcessFactory = Callable[..., subprocess.Popen[str]]
SleepFn = Callable[[float], None]
ClockFn = Callable[[], float]


class DelegateRuntime:
    def __init__(self, runtime_dir: Path) -> None:
        self.runtime_dir = runtime_dir
        self.commands_file = runtime_dir / "commands.jsonl"
        self.events_file = runtime_dir / "events.jsonl"
        self.stderr_file = runtime_dir / "stderr.log"
        self.status_file = runtime_dir / "status.json"
        self.last_assistant_file = runtime_dir / "assistant-last.txt"
        self.final_report_file = runtime_dir / "final-report.txt"

    def ensure(self) -> None:
        self.runtime_dir.mkdir(parents=True, exist_ok=True)
        for path in (
            self.commands_file,
            self.events_file,
            self.stderr_file,
            self.last_assistant_file,
            self.final_report_file,
        ):
            path.touch(exist_ok=True)


class CommandQueue:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.offset = 0

    def read_new(self) -> tuple[list[JsonDict], list[str]]:
        if not self.path.exists():
            return [], []

        payloads: list[JsonDict] = []
        errors: list[str] = []
        with self.path.open("r", encoding="utf-8") as handle:
            handle.seek(self.offset)
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payloads.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    errors.append(f"Invalid command JSON: {exc}: {line}")
            self.offset = handle.tell()
        return payloads, errors


class DelegateManager:
    def __init__(
        self,
        workdir: Path,
        prompt_file: Path,
        runtime_dir: Path,
        model: str,
        *,
        process_factory: ProcessFactory = subprocess.Popen,
        poll_interval: float = 0.2,
        exit_grace_seconds: float = 2.0,
        sleep: SleepFn = time.sleep,
        clock: ClockFn = time.time,
    ) -> None:
        self.workdir = workdir
        self.prompt_file = prompt_file
        self.runtime = DelegateRuntime(runtime_dir)
        self.model = model
        self.process_factory = process_factory
        self.poll_interval = poll_interval
        self.exit_grace_seconds = exit_grace_seconds
        self.sleep = sleep
        self.clock = clock
        self.proc: subprocess.Popen[str] | None = None
        self.command_queue = CommandQueue(self.runtime.commands_file)
        self.stdout_done = False
        self.current_message = ""
        self.agent_finished_at: float | None = None
        self.lock = threading.Lock()
        self.status: JsonDict = {
            "phase": "starting",
            "workdir": str(self.workdir),
            "promptFile": str(self.prompt_file),
            "runtimeDir": str(self.runtime.runtime_dir),
            "commandsFile": str(self.runtime.commands_file),
            "eventsFile": str(self.runtime.events_file),
            "stderrFile": str(self.runtime.stderr_file),
            "assistantLastFile": str(self.runtime.last_assistant_file),
            "finalReportFile": str(self.runtime.final_report_file),
            "model": self.model,
            "piRunning": False,
            "agentStreaming": False,
            "completedTurns": 0,
            "commandsForwarded": 0,
            "lastEventType": None,
            "lastResponse": None,
            "lastToolName": None,
            "lastAssistantText": "",
            "errors": [],
        }

    def send(self, payload: JsonDict) -> None:
        if self.proc is None or self.proc.stdin is None:
            raise RuntimeError("Delegate process is not running")
        self.proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def append_error(self, message: str) -> None:
        with self.lock:
            self.status.setdefault("errors", []).append(message)
            self.write_status()

    def write_status(self) -> None:
        self.runtime.status_file.write_text(json.dumps(self.status, indent=2, ensure_ascii=False), encoding="utf-8")

    def write_last_assistant_text(self, text: str) -> None:
        self.status["lastAssistantText"] = text
        self.runtime.last_assistant_file.write_text(text, encoding="utf-8")

    def write_final_report(self) -> None:
        self.runtime.final_report_file.write_text(str(self.status.get("lastAssistantText", "")), encoding="utf-8")

    def handle_signal(self, signum: int, _frame: object) -> None:
        print(f"[signal] {signum}", flush=True)
        if self.proc is None:
            return
        try:
            self.send({"type": "abort"})
        except RuntimeError:
            return

    def pump_stderr(self) -> None:
        assert self.proc is not None and self.proc.stderr is not None
        with self.runtime.stderr_file.open("a", encoding="utf-8") as handle:
            for line in self.proc.stderr:
                handle.write(line)
                handle.flush()

    def handle_event(self, event: JsonDict) -> None:
        event_type = event.get("type")
        self.status["lastEventType"] = event_type

        if event_type == "response":
            self.status["lastResponse"] = {
                "command": event.get("command"),
                "success": event.get("success"),
            }
            if event.get("command") == "get_state" and event.get("success"):
                data = event.get("data") or {}
                self.status["agentStreaming"] = bool(data.get("isStreaming"))
                self.status["lastState"] = data
            if event.get("command") == "get_last_assistant_text" and event.get("success"):
                data = event.get("data") or {}
                self.write_last_assistant_text(str(data.get("text") or ""))
        elif event_type == "agent_start":
            self.status["phase"] = "running"
            self.status["agentStreaming"] = True
            self.agent_finished_at = None
            print("[agent_start]", flush=True)
        elif event_type == "agent_end":
            self.status["phase"] = "completed"
            self.status["agentStreaming"] = False
            self.status["completedTurns"] += 1
            self.agent_finished_at = self.clock()
            self.write_final_report()
            print("[agent_end]", flush=True)
        elif event_type == "message_start":
            self.current_message = ""
            print("[message_start]", flush=True)
        elif event_type == "message_end":
            self.write_last_assistant_text(self.current_message)
            print("[message_end]", flush=True)
        elif event_type == "message_update":
            assistant_event = event.get("assistantMessageEvent") or {}
            assistant_event_type = assistant_event.get("type")
            if assistant_event_type == "text_delta":
                delta = str(assistant_event.get("delta") or "")
                if delta:
                    self.current_message += delta
                    self.write_last_assistant_text(self.current_message)
                    sys.stdout.write(delta)
                    sys.stdout.flush()
            elif assistant_event_type == "error":
                self.append_error(f"Assistant error: {assistant_event.get('reason')}")
            elif assistant_event_type == "toolcall_end":
                tool_call = assistant_event.get("toolCall") or {}
                print(f"[toolcall_end] {tool_call.get('name')}", flush=True)
        elif event_type == "tool_execution_start":
            self.status["lastToolName"] = event.get("toolName")
            print(f"[tool_start] {event.get('toolName')}", flush=True)
        elif event_type == "tool_execution_end":
            print(f"[tool_end] {event.get('toolName')} error={event.get('isError')}", flush=True)
        elif event_type == "extension_error":
            self.append_error(f"Extension error: {event.get('error')}")
        elif event_type is not None:
            print(f"[{event_type}]", flush=True)

        self.write_status()

    def pump_stdout(self) -> None:
        assert self.proc is not None and self.proc.stdout is not None
        with self.runtime.events_file.open("a", encoding="utf-8") as log_handle:
            for raw in self.proc.stdout:
                log_handle.write(raw)
                log_handle.flush()
                line = raw.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    self.append_error(f"Invalid event JSON: {line}")
                    print(f"[raw] {line}", flush=True)
                    continue
                with self.lock:
                    self.handle_event(event)
        self.stdout_done = True

    def forward_new_commands(self) -> None:
        payloads, errors = self.command_queue.read_new()
        for error in errors:
            self.append_error(error)
        for payload in payloads:
            with self.lock:
                self.send(payload)
                self.status["commandsForwarded"] += 1
                if payload.get("type") in {"prompt", "steer", "follow_up"}:
                    self.status["phase"] = "running"
                    self.status["agentStreaming"] = True
                    self.agent_finished_at = None
                self.write_status()
            print(f"[command] {payload.get('type')}", flush=True)

    def start_process(self) -> None:
        self.proc = self.process_factory(
            ["pi", "--mode", "rpc", "--model", self.model, "--no-session"],
            cwd=self.workdir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.status["piRunning"] = True
        self.write_status()

    def shutdown_process(self) -> int:
        assert self.proc is not None
        if self.proc.stdin is not None and not self.proc.stdin.closed:
            self.proc.stdin.close()
        try:
            return_code = self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.terminate()
            return_code = self.proc.wait(timeout=5)
        self.status["piRunning"] = False
        self.write_status()
        return return_code

    def should_exit(self) -> bool:
        if self.stdout_done:
            return True
        if self.agent_finished_at is None:
            return False
        return self.clock() - self.agent_finished_at >= self.exit_grace_seconds

    def run(self) -> int:
        prompt = self.prompt_file.read_text(encoding="utf-8")
        self.runtime.ensure()
        self.write_status()
        self.start_process()

        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

        stderr_thread = threading.Thread(target=self.pump_stderr, daemon=True)
        stdout_thread = threading.Thread(target=self.pump_stdout, daemon=True)
        stderr_thread.start()
        stdout_thread.start()

        self.send({"id": "initial-prompt", "type": "prompt", "message": prompt})

        while not self.should_exit():
            self.forward_new_commands()
            if self.proc is not None and self.proc.poll() is not None and self.stdout_done:
                break
            self.sleep(self.poll_interval)

        return_code = self.shutdown_process()
        stdout_thread.join(timeout=5)
        stderr_thread.join(timeout=5)
        return return_code


def append_command(runtime_dir: Path, payload: JsonDict) -> None:
    runtime = DelegateRuntime(runtime_dir)
    runtime.ensure()
    with runtime.commands_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def print_status(runtime_dir: Path) -> None:
    runtime = DelegateRuntime(runtime_dir)
    content = json.loads(runtime.status_file.read_text(encoding="utf-8"))
    print(json.dumps(content, indent=2, ensure_ascii=False))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run and supervise delegated pi RPC sessions.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Start a delegated RPC session")
    run_parser.add_argument("workdir", type=Path)
    run_parser.add_argument("prompt_file", type=Path)
    run_parser.add_argument("--runtime-dir", type=Path, required=True)
    run_parser.add_argument("--model", required=True)
    run_parser.add_argument("--poll-interval", type=float, default=0.2)
    run_parser.add_argument("--exit-grace-seconds", type=float, default=2.0)

    send_parser = subparsers.add_parser("send", help="Append a command for the running delegate")
    send_parser.add_argument("runtime_dir", type=Path)
    send_parser.add_argument("--type", required=True, choices=["prompt", "steer", "follow_up", "abort", "get_state", "get_messages", "get_last_assistant_text"])
    send_parser.add_argument("--message")

    status_parser = subparsers.add_parser("status", help="Print the delegate status file")
    status_parser.add_argument("runtime_dir", type=Path)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command == "run":
        manager = DelegateManager(
            workdir=args.workdir,
            prompt_file=args.prompt_file,
            runtime_dir=args.runtime_dir,
            model=args.model,
            poll_interval=args.poll_interval,
            exit_grace_seconds=args.exit_grace_seconds,
        )
        return manager.run()

    if args.command == "send":
        payload: JsonDict = {"type": args.type}
        if args.message is not None:
            payload["message"] = args.message
        append_command(args.runtime_dir, payload)
        return 0

    if args.command == "status":
        print_status(args.runtime_dir)
        return 0

    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
