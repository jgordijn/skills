#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
from pathlib import Path
from typing import Mapping, NamedTuple, TextIO


class SessionDefaults(NamedTuple):
    model: str
    thinking: str | None


def _optional_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def resolve_source_session_file(
    session_file: Path | None,
    env: Mapping[str, str] | None = None,
) -> Path:
    if session_file is not None:
        return session_file

    source_env = env if env is not None else os.environ
    env_session_file = _optional_text(source_env.get("PI_SESSION_FILE"))
    if env_session_file is None:
        raise ValueError("Provide --session-file or set PI_SESSION_FILE.")
    return Path(env_session_file)


def read_session_defaults(session_file: Path) -> SessionDefaults:
    if not session_file.exists():
        raise FileNotFoundError(f"Source session file does not exist: {session_file}")

    model: str | None = None
    thinking: str | None = None
    with session_file.open("r", encoding="utf-8") as handle:
        for line_number, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in source session file {session_file} at line {line_number}: {exc.msg}"
                ) from exc

            entry_type = entry.get("type")
            if entry_type == "model_change":
                provider = _optional_text(entry.get("provider"))
                model_id = _optional_text(entry.get("modelId"))
                if provider is not None and model_id is not None:
                    model = f"{provider}/{model_id}"
                elif model_id is not None:
                    model = model_id
            elif entry_type == "message":
                message = entry.get("message") or {}
                if message.get("role") == "assistant":
                    provider = _optional_text(entry.get("provider"))
                    model_id = _optional_text(entry.get("model"))
                    if provider is not None and model_id is not None:
                        model = f"{provider}/{model_id}"
                    elif model_id is not None:
                        model = model_id
            elif entry_type == "thinking_level_change":
                thinking = _optional_text(entry.get("thinkingLevel"))

    if model is None:
        raise ValueError(f"Unable to resolve model from source session file {session_file}.")

    return SessionDefaults(model=model, thinking=thinking)


def format_shell_exports(defaults: SessionDefaults) -> str:
    return (
        f"delegate_model={shlex.quote(defaults.model)}\n"
        f"delegate_thinking={shlex.quote(defaults.thinking or '')}\n"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve inherited delegate model and thinking settings from a Pi session file."
    )
    parser.add_argument("--session-file", type=Path, help="Pi source session JSONL file. Defaults to PI_SESSION_FILE.")
    parser.add_argument("--format", choices=["shell", "json"], default="shell")
    return parser


def main(
    argv: list[str] | None = None,
    *,
    env: Mapping[str, str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    args = build_parser().parse_args(argv)
    output = stdout if stdout is not None else sys.stdout
    errors = stderr if stderr is not None else sys.stderr

    try:
        session_file = resolve_source_session_file(args.session_file, env)
        defaults = read_session_defaults(session_file)
    except (FileNotFoundError, ValueError) as exc:
        print(str(exc), file=errors)
        return 1

    if args.format == "json":
        print(json.dumps({"model": defaults.model, "thinking": defaults.thinking}, ensure_ascii=False), file=output)
    else:
        output.write(format_shell_exports(defaults))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
