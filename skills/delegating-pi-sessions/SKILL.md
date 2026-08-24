---
name: delegating-pi-sessions
description: Use when delegating work to another Pi session, with or without a separate git worktree, or when coordinating parallel non-overlapping tasks.
---

# Delegating Pi Sessions

## Overview

All delegates are interactive Pi agents in a newly created Herdr tab. The parent owns the tab lifetime: retain it while reuse may help, and close it only after the result is captured and the child is no longer needed.

Never use `pi -p`, RPC, tmux, or Supaterm for delegation. Herdr's interactive Pi agent surface is the only supported launch path.

## Preconditions

Herdr is required:

```bash
test "${HERDR_ENV:-}" = 1
```

If this fails, stop and explain that delegation requires running inside Herdr.

## Choose the workspace

| Situation | Location |
|---|---|
| Read-only work or non-overlapping files | Current worktree |
| Overlapping edits, risky work, or an independently mergeable commit | Separate worktree |

Before code changes, follow the applicable repository instructions about asking whether to use a worktree. For isolation, create it beneath the repository and use it as the tab cwd:

```bash
git worktree add .worktrees/<name> -b <branch> <base-commit>
```

Give each child exact ownership. Never let parent and child concurrently edit overlapping files.

## Choose the model route

Unless the user specifies a route, select it by role:

| Delegate role | Model | Thinking |
|---|---|---|
| Standard programming or implementation | `github-copilot/gpt-5.6-sol` | thinking `medium` |
| Critical code review or adversarial verification | `github-copilot/kimi-k3` | thinking `high` |
| Easy, mechanical, tightly bounded work | `github-copilot/gpt-5.6-luna` | thinking `max` |

An explicit user-specified provider, model, or thinking always overrides the role default. Preserve every explicitly specified route component and never silently replace it. If the requested route is unavailable, report the problem and ask before substituting.

Initialize the route explicitly. Set `delegate_role` to `standard`, `critical`, or `easy`; set either requested value when the user supplied that component. Resolving each final value against a nonempty default ensures the launch never receives an empty model or thinking value.

```bash
delegate_role="standard" # change to critical or easy for that role
requested_model=""       # set to an explicit user-requested provider/model
requested_thinking=""    # set to an explicit user-requested thinking level

case "$delegate_role" in
  standard)
    default_model="github-copilot/gpt-5.6-sol"
    default_thinking="medium"
    ;;
  critical)
    default_model="github-copilot/kimi-k3"
    default_thinking="high"
    ;;
  easy)
    default_model="github-copilot/gpt-5.6-luna"
    default_thinking="max"
    ;;
  *)
    echo "unknown delegate role: $delegate_role" >&2
    exit 2
    ;;
esac

model="${requested_model:-$default_model}"
thinking="${requested_thinking:-$default_thinking}"
: "${model:?model must be set}"
: "${thinking:?thinking must be set}"
```

Even when using defaults, pass both final values explicitly.

## Create the Herdr tab and agent

Keep user focus unchanged. Parse both the new tab ID and root pane ID from the JSON response; never infer either ID.

```bash
herdr tab create \
  --workspace "$HERDR_WORKSPACE_ID" \
  --cwd /absolute/path/to/workdir \
  --label "[PI-SUB] <description>" \
  --no-focus

# Replace both placeholders after parsing the tab-create JSON response.
agent_name="<unique-name>"
root_pane_id="<root-pane-id-from-tab-create-json>"
: "${agent_name:?agent_name must be set}"
: "${root_pane_id:?root_pane_id must be set}"

# The separator is mandatory: --model and --thinking are Pi arguments, not Herdr options.
herdr agent start "$agent_name" --kind pi --pane "$root_pane_id" -- --model "$model" --thinking "$thinking"
herdr agent prompt "$agent_name" '<focused delegate prompt>'
```

Do not use `--wait` when the parent has other useful work; blocking defeats delegation. The child must not close its own pane or tab.

## Delegate prompt

Include:

- exact scope and owned files
- forbidden files and non-overlapping boundaries
- applicable repository instructions and wiki requirements
- required verification and commit/push requirements
- a concise final handoff with result, changed files, tests, commit, and blockers
- an instruction to remain available after the handoff; the parent decides whether to reuse or close the tab
- the exact instruction: "do not run any Herdr or Supaterm close command"

## Monitor, reuse, and collect

Use Herdr and repository state rather than a separate protocol:

```bash
herdr agent get <unique-name>
herdr agent read <unique-name> --source recent-unwrapped --lines 120
herdr agent wait <unique-name> --timeout 120000
git -C /absolute/path/to/workdir status --short
```

When settled, capture the handoff. If the output is incomplete, prompt the same child for clarification or another related task. Reuse is preferred when the existing context helps.

A `blocked`, failed, or unclear child is not finished. Inspect it and preserve its tab until resolved or deliberately abandoned.

## Parent-owned cleanup

The parent owns the tab lifetime and must close only the recorded tab ID when all are true:

1. The child is settled and no longer needed.
2. Its handoff and any required evidence have been captured.
3. No follow-up or reuse is expected.
4. Any branch/commit needed from its worktree is safely recorded.

```bash
herdr tab close <recorded-tab-id>
```

Do not ask the child to close itself. Do not close a tab by label, position, focused state, or guessed ID. Keep the tab open when explicitly requested or when diagnosis/follow-up is still needed.

## Common mistakes

- **Child closes itself** → the parent may still need its context; parent owns cleanup.
- **Parent closes immediately at first idle state** → capture and validate the handoff first.
- **Using a new worktree automatically** → isolate only when ownership or risk requires it.
- **Overlapping edits** → redefine ownership or isolate before launching.
- **Using RPC or one-shot launchers** → use the interactive Herdr agent surface.
- **Losing IDs** → store the exact tab and pane IDs returned by `herdr tab create`.
