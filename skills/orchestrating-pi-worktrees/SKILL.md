---
name: orchestrating-pi-worktrees
description: Use when delegating work to another pi session or splitting non-overlapping coding work across separate pi instances. Create one git worktree and tmux window per delegate, and default to RPC-mode launches via the bundled `pi-rpc-prompt-runner.py` helper for observable, restartable runs.
---

# Orchestrating Pi Worktrees

## Overview
Use separate pi instances when the work can be split into independent file/task boundaries. The coordinator keeps the main worktree clean, commits a shared base first, fans work out into isolated git worktrees, monitors progress, and merges completed branches back.

Core principle: **commit base → isolate work → monitor structurally → merge verified results**.

If you want a simpler one-shot delegation pattern **without always creating a new worktree**, use `delegating-pi-sessions` instead.


## When to Use
- A change has multiple independent subtasks
- Different instances can work on different files without overlap
- You want to delegate this to another pi session or spawn a separate pi run
- You want tmux windows plus a dedicated git worktree per delegate
- You want observable, restartable delegated runs instead of opaque fire-and-forget output

Do not use this when:
- Tasks touch the same files heavily
- The work is too small to justify coordination overhead
- You cannot define clear ownership boundaries per instance

## Quick Reference

| Need | Default |
|------|---------|
| Delegated pi session with supervision | `<skill-dir>/scripts/pi-rpc-prompt-runner.py` → `pi --mode rpc` |
| Passive structured event logging only | `pi --mode json` |
| Explicit fire-and-forget, minimal supervision | `pi -p` only when the user asks for it or supervision truly does not matter |

| Step | Action |
|------|--------|
| 1 | Commit the current base in the coordinator worktree |
| 2 | Create one worktree per delegate branch from that base commit |
| 3 | Give each delegate a non-overlapping scope |
| 4 | Launch each delegate in a new tmux window |
| 5 | Monitor via git state and, if needed, RPC/json logs |
| 6 | Verify delegate branch tests before merging back |
| 7 | Merge branches back into the coordinator worktree |

## Workflow

### 1. Prepare a clean coordinator base
Before spawning delegates:
- verify what you changed
- run relevant tests
- commit only your files

This gives every delegate a stable starting point and makes later merges predictable.

### 2. Split work by ownership, not by hope
Each delegate must own a distinct slice:
- separate directories (`llm/` vs `agent/`)
- separate task groups
- separate tests where possible

Avoid assigning overlapping files or shared task-tracker edits to multiple delegates.

If there is a central checklist file (for example `tasks.md`), the coordinator should usually own it. Delegates should not all edit the same progress file.

### 3. Create one worktree per delegate
Create each worktree from the same committed base point.

Example:
```bash
git worktree add .worktrees/feature-x-llm -b feature-x-llm <base-commit>
git worktree add .worktrees/feature-x-agent -b feature-x-agent <base-commit>
```

Run project setup in each worktree and verify the baseline before delegating.

### 4. Launch in separate tmux windows
Use one tmux window per delegate so each run is isolated and easy to inspect.

Default launch path: start delegated pi sessions with the bundled RPC helper, not plain `pi -p`. Resolve the helper path from the skill directory and use the resulting absolute path when launching from a project worktree.

Example:
```bash
tmux new-window -n llm-tools -c /path/to/worktree '<skill-dir>/scripts/pi-rpc-prompt-runner.py \
  /path/to/worktree /path/to/delegate-llm-tools.md \
  --model <provider/model> \
  --log-file /path/to/logs/llm-tools.jsonl \
  --stderr-file /path/to/logs/llm-tools.stderr.log; exec zsh'

tmux new-window -n agent-server -c /path/to/worktree '<skill-dir>/scripts/pi-rpc-prompt-runner.py \
  /path/to/worktree /path/to/delegate-agent-server.md \
  --model <provider/model> \
  --log-file /path/to/logs/agent-server.jsonl \
  --stderr-file /path/to/logs/agent-server.stderr.log; exec zsh'
```

Use plain `pi -p` only when the user explicitly wants fire-and-forget behavior or when you are certain no monitoring, restart, or abort control will be needed.

The delegate prompt should include:
- exact task ownership
- forbidden files
- required verification commands
- commit requirement
- request to print commit hash on completion

### 5. Default to RPC via the helper script
For delegated worktrees, prefer RPC by default. It gives you structured observability and control from the start instead of only after a run becomes confusing.

Use the bundled helper. Resolve `./scripts/pi-rpc-prompt-runner.py` from the skill directory and use that absolute path when executing from another worktree:
```bash
<skill-dir>/scripts/pi-rpc-prompt-runner.py /path/to/worktree /path/to/delegate.md \
  --model <provider/model> \
  --log-file /path/to/delegate.jsonl \
  --stderr-file /path/to/delegate.stderr.log
```

It starts `pi --mode rpc`, sends one prompt from a file, logs raw JSONL events, mirrors compact progress to stdout, and sends `abort` on Ctrl+C. The caller must choose the model explicitly.

RPC is the default here because it gives you:
- `prompt`
- `get_state`
- `get_messages`
- `get_last_assistant_text`
- `abort`
- structured `agent_start`, `message_update`, and tool execution events

Use `pi --mode json` when you only need passive event logs and not interactive control.

### 6. Monitor structurally, not just visually
If tmux output is weak, monitor using:
- delegate worktree `git status`
- latest commit on delegate branch
- changed file list
- recent file mtimes
- RPC or JSON event logs

Useful checks:
```bash
git -C /path/to/worktree status --short
git -C /path/to/worktree log --oneline -1
git -C /path/to/worktree diff --stat
find /path/to/worktree -type f -mmin -5
```

### 7. Handle stalls explicitly
A delegate may be alive but not progressing. Signs:
- long runtime with no new files
- only dependency churn (`go.mod`, `go.sum`) and no code
- blank tmux pane with no meaningful output

When stalled:
1. inspect worktree status and logs
2. capture any useful output
3. abort the delegate
4. restart it with the RPC helper again unless the user explicitly wants `pi -p`
5. restart from a clean worktree state if needed

### 8. Merge only verified delegate branches
Before merging back:
- inspect changed files for scope creep
- run tests in the delegate worktree
- ensure commit history is clean enough

Then merge into the coordinator worktree.

Example:
```bash
git merge feature-x-llm
git merge feature-x-agent
```

Run final verification again in the coordinator worktree after merges.

## Delegate Prompt Template
Use this structure for each delegate:

```text
You are working in a dedicated git worktree.

Branch: <branch>
Base commit: <sha>

Your scope is ONLY:
- <task list>
- <owned files/directories>

Do NOT edit:
- <forbidden files>
- shared task tracking files unless explicitly assigned

Requirements:
- keep changes minimal and focused
- run gofmt / tests / project verification
- commit only your files
- print a short summary with the commit hash
```

## Common Mistakes
- **Delegates editing the same files** → split by ownership before launch
- **No base commit before fan-out** → branches diverge from moving targets
- **All delegates editing one checklist file** → keep central tracking in the coordinator
- **Using `pi -p` as the default delegate launcher** → use the RPC helper unless the user explicitly wants fire-and-forget
- **Reading only tmux panes** → inspect git state and structured logs too
- **Merging unverified branches** → run tests in delegate worktree first

## Real-World Impact
This workflow turns opaque parallel runs into manageable units:
- isolated code changes
- predictable merges
- restartable delegates
- observable progress when plain tmux output is not enough
