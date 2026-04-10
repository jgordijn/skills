---
name: delegating-pi-sessions
description: Use when delegating work to another pi session, with or without a separate git worktree, when a simple one-shot `pi -p` run is enough.
---

# Delegating Pi Sessions

## Overview
Use this skill when the goal is **delegate first, choose workspace second**.

Default to a direct one-shot `pi -p` launch, the same style as `ralph-with-pi`, instead of an RPC-managed delegate. Keep the delegate session inside the project under `.tmp/pi-sessions` so the history stays with the worktree.

You do not need a Python helper script for the default case. Use RPC only when you truly need mid-flight control such as `steer`, `follow_up`, or structured event monitoring.

If isolation is required, create a worktree first. If the delegate is only researching, reviewing, or editing files that the coordinator will not touch, the same worktree can be acceptable.

## When to Use
- You want another pi session to work in parallel
- A one-shot delegate is enough
- You want the delegate session written under the project `.tmp`
- You do **not** always want a new worktree just to delegate work

Do not use this when:
- both sessions will edit the same files at the same time
- you need mid-flight steering while the delegate is still running
- the task is too small to justify coordination overhead
- you cannot define a clear owner for the delegate’s scope

## Workspace Choice
| Situation | Recommended workspace |
|-----------|-----------------------|
| Read-only research, investigation, review | Same worktree is fine |
| Delegate owns a non-overlapping file set and coordinator will stay out | Same worktree can be fine |
| Delegate needs isolated commits, risky edits, or later merge/restart safety | Separate worktree |

When in doubt, prefer a worktree. When speed matters and scope is clean, stay in the current worktree.

## Session and Log Layout
Create a local temp area per delegate:

```bash
mkdir -p .tmp/pi-sessions
```

Use these paths from the delegate workdir:
- `.tmp/pi-sessions/` - pi session files for the delegate
- `.tmp/delegate-name.log` - combined stdout and stderr from the delegate run

Do not use `--no-session`; that disables session persistence.

## Launch a Delegate
Run pi directly.

By default, launch the delegate with the same provider/model routing and thinking level as the current session. Only override those inherited defaults when the user explicitly asks for a different provider, model, or thinking level.

If your wrapper exports `PI_SESSION_FILE`, treat it as the source session file and resolve the current session settings once before launching:

```bash
eval "$(
python3 - <<'PY'
import json
import os
import pathlib
import shlex

path = os.environ.get("PI_SESSION_FILE", "").strip()
model = ""
thinking = ""

if path:
    for raw in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        entry = json.loads(raw)
        if entry.get("type") == "model_change":
            provider = (entry.get("provider") or "").strip()
            model_id = (entry.get("modelId") or "").strip()
            if provider and model_id:
                model = f"{provider}/{model_id}"
            elif model_id:
                model = model_id
        elif entry.get("type") == "message":
            message = entry.get("message") or {}
            if message.get("role") == "assistant":
                provider = (entry.get("provider") or "").strip()
                model_id = (entry.get("model") or "").strip()
                if provider and model_id:
                    model = f"{provider}/{model_id}"
                elif model_id:
                    model = model_id
        elif entry.get("type") == "thinking_level_change":
            level = (entry.get("thinkingLevel") or "").strip()
            if level:
                thinking = level

print(f"delegate_model={shlex.quote(model)}")
print(f"delegate_thinking={shlex.quote(thinking)}")
PY
)"
```

If `PI_SESSION_FILE` is not available, copy the current session's provider/model routing and current thinking level into the launch command manually.

```bash
mkdir -p .tmp/pi-sessions
pi -p \
  ${delegate_model:+--model "$delegate_model"} \
  ${delegate_thinking:+--thinking "$delegate_thinking"} \
  --session-dir .tmp/pi-sessions \
  "read and perform @/path/to/delegate.md"
```

If you want the exact `ralph-with-pi` style launch without the loop, this is the equivalent `bun x` form:

```bash
bun x @mariozechner/pi-coding-agent@latest -p \
  ${delegate_model:+--model "$delegate_model"} \
  ${delegate_thinking:+--thinking "$delegate_thinking"} \
  --session-dir .tmp/pi-sessions \
  "read and perform @/path/to/delegate.md"
```

Override the inherited defaults only when needed:

```bash
pi -p --model <provider/model> --thinking <level> \
  --session-dir .tmp/pi-sessions \
  "read and perform @/path/to/delegate.md"
```

Launch it in tmux when you want a persistent terminal window:

```bash
tmux new-window -n delegate-name -c /path/to/workdir 'mkdir -p .tmp/pi-sessions && pi -p \
  --model <current-provider/model> \
  --thinking <current-thinking-level> \
  --session-dir .tmp/pi-sessions \
  "read and perform @/path/to/delegate.md" \
  2>&1 | tee .tmp/delegate-name.log; exec zsh'
```

Substitute `<current-provider/model>` and `<current-thinking-level>` with the inherited values you resolved from the source session file.

## Delegate Prompt Requirements
Include all of these in the delegate prompt:
- exact task scope
- owned files or directories
- forbidden files
- required verification commands
- request to summarize changes at the end
- request to write the final answer as a concise handoff report

## Monitoring
Do not launch and forget. Keep checking progress.

Primary checks:

```bash
tail -n 50 .tmp/delegate-name.log
ls -lt .tmp/pi-sessions
git status --short
git diff --stat
find . -type f -mmin -5
```

If you want to inspect the saved session directly, open the newest JSONL file in `.tmp/pi-sessions/`.

## Limitations
With `pi -p` there is no mid-flight `steer` or `follow_up` channel. If requirements change while the delegate is running, stop it and relaunch with an updated prompt.

If you need structured live control, use an RPC-based workflow instead.

## Coordinator Workflow
1. Decide whether the delegate needs the same worktree or a separate one
2. Write a focused delegate prompt
3. Create `.tmp/pi-sessions`
4. Resolve the inherited provider/model routing and thinking level from the current session
5. Launch the delegate with `pi -p --session-dir`
6. Monitor the log file and repo state
7. Inspect the resulting session file and changed files when the run finishes
8. Verify the result before continuing

## Common Mistakes
- **Using a worktree every time** → choose isolation only when it helps
- **Using the same worktree for overlapping edits** → use a separate worktree instead
- **Using `--no-session`** → no delegate session gets written under `.tmp`
- **Forgetting to inherit current settings** → reuse the current session's provider/model routing and thinking level unless the user asked otherwise
- **Trying to steer the delegate mid-run** → stop and relaunch instead
- **Skipping log capture** → pipe output to `.tmp/delegate-name.log`

## Real-World Impact
This gives you a lightweight delegated-session workflow in pi:
- simple launch
- project-local sessions in `.tmp/pi-sessions`
- inheritance of current provider/model routing and thinking level by default
- no Python helper script
- easy tmux use
- works with the same worktree or a separate one
