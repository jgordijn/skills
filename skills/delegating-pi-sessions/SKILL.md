---
name: delegating-pi-sessions
description: Use when delegating work to another pi session, with or without a separate git worktree, when a simple one-shot `pi -p` run is enough.
---

# Delegating Pi Sessions

## Overview
Use this skill when the goal is **delegate first, choose workspace second**.

Default to a direct one-shot `pi -p` launch, the same style as `ralph-with-pi`, instead of an RPC-managed delegate. Keep the delegate session inside the project under `.tmp/pi-sessions` so the history stays with the worktree.

Use the bundled extension tool to detect the current provider/model route from the active runtime instead of scraping session JSON inline. Keep the saved-session helper only as a fallback when you must inherit settings from a saved session file outside the live runtime. Use RPC only when you truly need mid-flight control such as `steer`, `follow_up`, or structured event monitoring.

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

## Bundled resources
Paths below are relative to this `SKILL.md` file / skill root.

- `../extensions/current-pi-session-settings.js` - registers the `get_current_pi_session_settings` tool for reading the active runtime model and thinking level
- `scripts/pi_delegate_inherit_session.py` - fallback helper for inheriting settings from a saved session file when the live extension tool is unavailable

## Launch a Delegate
Run pi directly.

By default, call `get_current_pi_session_settings` and use its returned `model` and `thinking` values for the delegate launch. That keeps the delegate on the same provider/model routing and thinking level as the active runtime, unless the user explicitly asks for a different provider, model, or thinking level.

Expected tool result details:
- `provider`
- `modelId`
- `model` (`provider/model`)
- `thinking`

Then launch with those inherited defaults:

```bash
mkdir -p .tmp/pi-sessions
pi -p \
  --model <current-provider/model> \
  --thinking <current-thinking-level> \
  --session-dir .tmp/pi-sessions \
  "read and perform @/path/to/delegate.md"
```

If you want the exact `ralph-with-pi` style launch without the loop, this is the equivalent `bun x` form:

```bash
bun x @mariozechner/pi-coding-agent@latest -p \
  --model <current-provider/model> \
  --thinking <current-thinking-level> \
  --session-dir .tmp/pi-sessions \
  "read and perform @/path/to/delegate.md"
```

Override the inherited defaults only when needed:

```bash
pi -p --model <provider/model> --thinking <level> \
  --session-dir .tmp/pi-sessions \
  "read and perform @/path/to/delegate.md"
```

Launch it in a persistent terminal host when you want the delegate to keep running in its own visible session.

Detect the host in this order: use tmux when you are already inside tmux, otherwise use Supaterm when `SUPATERM_SOCKET_PATH` is set and `sp` is available, and if you are in neither, fallback to tmux.

```bash
if [ -n "$TMUX" ]; then
  tmux new-window -n delegate-name -c /path/to/workdir 'mkdir -p .tmp/pi-sessions && pi -p \
    --model <current-provider/model> \
    --thinking <current-thinking-level> \
    --session-dir .tmp/pi-sessions \
    "read and perform @/path/to/delegate.md" \
    2>&1 | tee .tmp/delegate-name.log'
elif [ -n "${SUPATERM_SOCKET_PATH:-}" ] && command -v sp >/dev/null; then
  sp tab new --focus --cwd /path/to/workdir --script 'mkdir -p .tmp/pi-sessions && pi -p \
    --model <current-provider/model> \
    --thinking <current-thinking-level> \
    --session-dir .tmp/pi-sessions \
    "read and perform @/path/to/delegate.md" \
    2>&1 | tee .tmp/delegate-name.log'
else
  tmux new-window -n delegate-name -c /path/to/workdir 'mkdir -p .tmp/pi-sessions && pi -p \
    --model <current-provider/model> \
    --thinking <current-thinking-level> \
    --session-dir .tmp/pi-sessions \
    "read and perform @/path/to/delegate.md" \
    2>&1 | tee .tmp/delegate-name.log'
fi
```

Inside Supaterm, prefer a new tab because it maps most closely to the separate-window workflow used in tmux. Supaterm also sets ambient targeting variables such as `SUPATERM_SOCKET_PATH`, `SUPATERM_SURFACE_ID`, and `SUPATERM_TAB_ID`, so `sp tab new` can usually target the current space without extra selectors.

Substitute `<current-provider/model>` and `<current-thinking-level>` with the inherited values you got by calling `get_current_pi_session_settings`.

## Fallback for saved session files
If the bundled extension tool is unavailable and you only have a saved session file, use the fallback helper instead of embedding ad-hoc JSON parsing inline:

```bash
helper=scripts/pi_delegate_inherit_session.py
eval "$($helper --session-file /path/to/current-session.jsonl)"
```

Use this only for the saved session file case. In normal pi usage, prefer the active runtime tool.

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
4. Call `get_current_pi_session_settings` to resolve the inherited provider/model routing and thinking level from the active runtime
5. Launch the delegate with `pi -p --session-dir`
6. Monitor the log file and repo state
7. Inspect the resulting session file and changed files when the run finishes
8. Verify the result before continuing

## Common Mistakes
- **Using a worktree every time** → choose isolation only when it helps
- **Using the same worktree for overlapping edits** → use a separate worktree instead
- **Using `--no-session`** → no delegate session gets written under `.tmp`
- **Forgetting to call `get_current_pi_session_settings`** → inherit the current runtime defaults unless the user asked otherwise
- **Reaching for the saved-session fallback too early** → prefer the active runtime tool first
- **Trying to steer the delegate mid-run** → stop and relaunch instead
- **Skipping log capture** → pipe output to `.tmp/delegate-name.log`

## Real-World Impact
This gives you a lightweight delegated-session workflow in pi:
- simple launch
- project-local sessions in `.tmp/pi-sessions`
- inheritance of current provider/model routing and thinking level by default
- reusable extension tool for the active runtime
- saved-session fallback when you truly need it
- easy tmux use
- works with the same worktree or a separate one
