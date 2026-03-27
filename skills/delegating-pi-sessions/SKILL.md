---
name: delegating-pi-sessions
description: Use when delegating work to another pi session, with or without a separate git worktree, and needing RPC supervision, progress monitoring, steering messages, follow-up instructions, or abort/restart control.
---

# Delegating Pi Sessions

## Overview
Use this skill when the goal is **delegate first, choose workspace second**.

Default to a supervised RPC delegate instead of a fire-and-forget `pi -p` run. Monitor the delegate through runtime files, keep the option to intervene with `steer` or `follow_up`, and always collect a final handoff summary from `final-report.txt`.

If isolation is required, create a worktree first. If the delegate is only researching, reviewing, or editing files that the coordinator will not touch, the same worktree can be acceptable.

## When to Use
- You want another pi session to work in parallel
- You need observable progress instead of a blind background run
- You may need to tell the delegate “also keep this in mind” while it is running
- You want the delegate to report back what it did at the end
- You do **not** always want a new worktree just to delegate work

Do not use this when:
- both sessions will edit the same files at the same time
- the task is too small to justify coordination overhead
- you cannot define a clear owner for the delegate’s scope

## Workspace Choice
| Situation | Recommended workspace |
|-----------|-----------------------|
| Read-only research, investigation, review | Same worktree is fine |
| Delegate owns a non-overlapping file set and coordinator will stay out | Same worktree can be fine |
| Delegate needs isolated commits, risky edits, or later merge/restart safety | Separate worktree |

When in doubt, prefer a worktree. When speed matters and scope is clean, stay in the current worktree.

## Runtime Layout
Choose a runtime directory per delegate, for example:

```bash
runtime_dir=/tmp/pi-delegates/audit-history
```

The helper writes these files:
- `commands.jsonl` - queued commands for the delegate manager
- `events.jsonl` - raw RPC output from pi
- `stderr.log` - pi stderr output
- `status.json` - current supervision state
- `assistant-last.txt` - last assistant text seen so far
- `final-report.txt` - final delegate handoff summary

## Launch a Delegate
Resolve the helper path from this skill directory and use the absolute path.

```bash
<skill-dir>/scripts/pi_delegate_rpc.py run /path/to/workdir /path/to/delegate.md \
  --model <provider/model> \
  --runtime-dir /tmp/pi-delegates/delegate-name
```

Use `--exit-grace-seconds <n>` if you want the helper to wait longer after `agent_end` before shutting down, so there is more time to send a late `follow_up`.


Launch it in tmux when you want a persistent supervised session:

```bash
tmux new-window -n delegate-name -c /path/to/workdir '<skill-dir>/scripts/pi_delegate_rpc.py run \
  /path/to/workdir /path/to/delegate.md \
  --model <provider/model> \
  --runtime-dir /tmp/pi-delegates/delegate-name; exec zsh'
```

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
cat /tmp/pi-delegates/delegate-name/status.json
cat /tmp/pi-delegates/delegate-name/assistant-last.txt
tail -n 50 /tmp/pi-delegates/delegate-name/events.jsonl
```

Useful repository checks:
```bash
git -C /path/to/workdir status --short
git -C /path/to/workdir diff --stat
find /path/to/workdir -type f -mmin -5
```

## Intervening While It Runs
This is the key difference from a plain `pi -p` delegate.

Tell the running delegate to keep something in mind:

```bash
<skill-dir>/scripts/pi_delegate_rpc.py send /tmp/pi-delegates/delegate-name \
  --type steer \
  --message "Also keep backward compatibility in mind."
```

Queue a follow-up for after the current task finishes:

```bash
<skill-dir>/scripts/pi_delegate_rpc.py send /tmp/pi-delegates/delegate-name \
  --type follow_up \
  --message "After you finish, give me a short risk summary too."
```

Ask pi for state explicitly:

```bash
<skill-dir>/scripts/pi_delegate_rpc.py send /tmp/pi-delegates/delegate-name --type get_state
```

Abort the delegate:

```bash
<skill-dir>/scripts/pi_delegate_rpc.py send /tmp/pi-delegates/delegate-name --type abort
```

## Coordinator Workflow
1. Decide whether the delegate needs the same worktree or a separate one
2. Write a focused delegate prompt
3. Launch the delegate in RPC mode
4. Monitor `status.json`, `assistant-last.txt`, and repo state
5. If the user adds new guidance, send it with `steer`
6. When the run finishes, read `final-report.txt`
7. Inspect the changed files and verify the result before continuing

## Common Mistakes
- **Using a worktree every time** → choose isolation only when it helps
- **Using the same worktree for overlapping edits** → use a separate worktree instead
- **Forgetting to monitor progress** → read `status.json` and `events.jsonl`
- **Waiting too long to intervene** → send `steer` as soon as the user adds important guidance
- **Ending without a handoff** → read `final-report.txt` and summarize it back to the user

## Real-World Impact
This gives you a practical sub-session workflow in pi:
- RPC-based supervision
- visible progress
- mid-flight guidance with `steer`
- queued follow-ups with `follow_up`
- a final delegate report you can hand back to the user
