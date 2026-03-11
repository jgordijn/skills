#!/usr/bin/env python3
"""Run pi in RPC mode with a prompt file and structured logging.

This helper is meant for delegated work launched in tmux. It:
- starts `pi --mode rpc`
- sends one initial prompt loaded from a file
- writes every RPC event to a JSONL log file
- mirrors a compact human-readable progress stream to stdout
- sends an `abort` command on SIGINT/SIGTERM

Example:
    ./scripts/pi-rpc-prompt-runner.py \
      /path/to/worktree \
      /path/to/delegate.md \
      --model <provider/model> \
      --log-file /path/to/delegate.jsonl \
      --stderr-file /path/to/delegate.stderr.log
"""

from __future__ import annotations

import argparse
import json
import signal
import subprocess
import sys
import tempfile
import threading
from pathlib import Path
from typing import Any


class Runner:
    def __init__(self, workdir: Path, prompt_file: Path, log_file: Path, stderr_file: Path, model: str) -> None:
        self.workdir = workdir
        self.prompt_file = prompt_file
        self.log_file = log_file
        self.stderr_file = stderr_file
        self.model = model
        self.proc: subprocess.Popen[str] | None = None
        self.stopping = False

    def send(self, payload: dict[str, Any]) -> None:
        if self.proc is None or self.proc.stdin is None:
            return
        self.proc.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()

    def handle_signal(self, signum: int, _frame: object) -> None:
        self.stopping = True
        print(f"\n[rpc] received signal {signum}, requesting abort", flush=True)
        try:
            self.send({"type": "abort"})
        except Exception as exc:  # pragma: no cover - best effort shutdown
            print(f"[rpc] failed to send abort: {exc}", flush=True)

    def pump_stderr(self) -> None:
        assert self.proc is not None and self.proc.stderr is not None
        with self.stderr_file.open("a", encoding="utf-8") as handle:
            for line in self.proc.stderr:
                handle.write(line)
                handle.flush()
                sys.stdout.write(f"[stderr] {line}")
                sys.stdout.flush()

    def print_event(self, event: dict[str, Any]) -> bool:
        event_type = event.get("type")

        if event_type == "response":
            print(
                f"[response] command={event.get('command')} success={event.get('success')}",
                flush=True,
            )
            return False
        if event_type == "agent_start":
            print("[agent_start]", flush=True)
            return False
        if event_type == "agent_end":
            messages = len(event.get("messages", []) or [])
            print(f"\n[agent_end] messages={messages}", flush=True)
            return True
        if event_type == "turn_start":
            print("[turn_start]", flush=True)
            return False
        if event_type == "turn_end":
            tool_results = len(event.get("toolResults", []) or [])
            print(f"[turn_end] toolResults={tool_results}", flush=True)
            return False
        if event_type == "message_start":
            print("[message_start]", flush=True)
            return False
        if event_type == "message_end":
            print("\n[message_end]", flush=True)
            return False
        if event_type == "message_update":
            delta = event.get("assistantMessageEvent", {}) or {}
            delta_type = delta.get("type")
            if delta_type == "text_delta":
                text = delta.get("delta", "")
                if text:
                    sys.stdout.write(text)
                    sys.stdout.flush()
            elif delta_type == "toolcall_end":
                tool_call = delta.get("toolCall", {}) or {}
                print(f"\n[toolcall_end] {tool_call.get('name')}", flush=True)
            elif delta_type == "error":
                print(f"\n[message_error] {delta.get('reason')}", flush=True)
            return False
        if event_type == "tool_execution_start":
            print(f"\n[tool_start] {event.get('toolName')}", flush=True)
            return False
        if event_type == "tool_execution_end":
            print(
                f"[tool_end] {event.get('toolName')} error={event.get('isError')}",
                flush=True,
            )
            return False
        if event_type == "auto_retry_start":
            print(
                f"[auto_retry_start] attempt={event.get('attempt')} delayMs={event.get('delayMs')}",
                flush=True,
            )
            return False
        if event_type == "auto_retry_end":
            print(
                f"[auto_retry_end] success={event.get('success')} attempt={event.get('attempt')}",
                flush=True,
            )
            return False
        if event_type == "auto_compaction_start":
            print(f"[auto_compaction_start] reason={event.get('reason')}", flush=True)
            return False
        if event_type == "auto_compaction_end":
            print(
                f"[auto_compaction_end] aborted={event.get('aborted')} willRetry={event.get('willRetry')}",
                flush=True,
            )
            return False
        if event_type == "extension_error":
            print(f"[extension_error] {event.get('error')}", flush=True)
            return False

        print(f"[{event_type}]", flush=True)
        return False

    def run(self) -> int:
        prompt = self.prompt_file.read_text(encoding="utf-8")
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.stderr_file.parent.mkdir(parents=True, exist_ok=True)

        self.proc = subprocess.Popen(
            ["pi", "--mode", "rpc", "--model", self.model, "--no-session"],
            cwd=self.workdir,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

        threading.Thread(target=self.pump_stderr, daemon=True).start()

        print(f"[rpc] cwd={self.workdir}", flush=True)
        print(f"[rpc] prompt={self.prompt_file}", flush=True)
        print(f"[rpc] log={self.log_file}", flush=True)
        print(f"[rpc] stderr={self.stderr_file}", flush=True)
        print(f"[rpc] model={self.model}", flush=True)
        print("[rpc] sending prompt", flush=True)
        self.send({"id": "req-1", "type": "prompt", "message": prompt})

        assert self.proc.stdout is not None
        with self.log_file.open("a", encoding="utf-8") as log_handle:
            for raw in self.proc.stdout:
                log_handle.write(raw)
                log_handle.flush()
                line = raw.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    print(f"[raw] {line}", flush=True)
                    continue
                if self.print_event(event):
                    break

        return_code = self.proc.wait()
        print(f"[rpc] pi exited with code {return_code}", flush=True)
        return return_code


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run pi in RPC mode with structured logging.")
    parser.add_argument("workdir", type=Path, help="Working directory to run pi in")
    parser.add_argument("prompt_file", type=Path, help="File containing the prompt to send")
    parser.add_argument(
        "--log-file",
        type=Path,
        default=Path(tempfile.gettempdir()) / "pi-rpc-prompt-runner.jsonl",
        help="JSONL file for raw RPC events",
    )
    parser.add_argument(
        "--stderr-file",
        type=Path,
        default=Path(tempfile.gettempdir()) / "pi-rpc-prompt-runner.stderr.log",
        help="File for pi stderr output",
    )
    parser.add_argument(
        "--model",
        required=True,
        help="Model pattern or provider/model id",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    runner = Runner(
        workdir=args.workdir,
        prompt_file=args.prompt_file,
        log_file=args.log_file,
        stderr_file=args.stderr_file,
        model=args.model,
    )
    return runner.run()


if __name__ == "__main__":
    raise SystemExit(main())
