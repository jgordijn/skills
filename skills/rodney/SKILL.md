---
name: rodney
description: Use when automating Chrome browser interactions from the command line — web scraping, testing, screenshots, form filling, accessibility audits, or any task requiring headless browser control. Rodney drives a persistent Chrome instance via CLI commands. <examples><example>Take a screenshot of a website</example><example>Scrape text from a web page</example><example>Fill in a form and submit it</example><example>Run accessibility checks on a page</example><example>Automate browser interactions</example><example>Check if an element exists on a page</example></examples>
---

Always consult the full README for the latest commands and options: https://raw.githubusercontent.com/simonw/rodney/refs/heads/main/README.md

# Rodney — Chrome Automation from the Command Line

A Go CLI tool that drives a persistent headless Chrome instance. Each command connects to the same long-running Chrome process, making it easy to script multi-step browser interactions.

**Repository**: https://github.com/simonw/rodney

## Prerequisites

- Go 1.21+ (to build from source)
- Google Chrome or Chromium installed (or set `ROD_CHROME_BIN=/path/to/chrome`)

Build: `go build -o rodney .`

Install from releases: check https://github.com/simonw/rodney/releases

## Architecture

Each CLI invocation is a short-lived process. Chrome runs independently and tabs persist between commands.

```
rodney start    → launches Chrome, saves WebSocket URL to ~/.rodney/state.json
rodney open URL → connects via WebSocket, navigates, disconnects
rodney js EXPR  → connects, evaluates JS, prints result, disconnects
rodney stop     → shuts down Chrome, cleans up state
```

## Essential Workflow

Always follow this pattern:

```bash
# 1. Start browser
rodney start

# 2. Navigate and interact
rodney open https://example.com
rodney waitstable

# 3. Do work (extract data, screenshot, fill forms, etc.)
rodney title
rodney screenshot output.png

# 4. Stop when done
rodney stop
```

## Command Reference

### Browser Lifecycle

| Command | Description |
|---|---|
| `rodney start` | Launch headless Chrome |
| `rodney start --show` | Launch with visible window |
| `rodney start --insecure` / `-k` | Ignore TLS errors |
| `rodney start --local` | Directory-scoped session in `./.rodney/` |
| `rodney connect host:9222` | Connect to existing Chrome on remote debug port |
| `rodney status` | Show browser info and active page |
| `rodney stop` | Shut down Chrome |

### Navigation

| Command | Description |
|---|---|
| `rodney open <url>` | Navigate to URL (`http://` added if missing) |
| `rodney back` | Go back in history |
| `rodney forward` | Go forward in history |
| `rodney reload [--hard]` | Reload page (`--hard` bypasses cache) |
| `rodney clear-cache` | Clear the browser cache |

### Extract Information

| Command | Description |
|---|---|
| `rodney url` | Print current URL |
| `rodney title` | Print page title |
| `rodney text "<selector>"` | Print text content of element |
| `rodney html "<selector>"` | Print outer HTML of element |
| `rodney html` | Print full page HTML |
| `rodney attr "<selector>" <name>` | Print attribute value |
| `rodney pdf [file]` | Save page as PDF |

### Run JavaScript

| Command | Description |
|---|---|
| `rodney js <expression>` | Evaluate JS expression (auto-wrapped in arrow function) |

Examples:
```bash
rodney js document.title
rodney js "1 + 2"
rodney js 'document.querySelector("h1").textContent'
rodney js '[1,2,3].map(x => x * 2)'           # Returns pretty-printed JSON
rodney js 'document.querySelectorAll("a").length'
```

### Interact with Elements

| Command | Description |
|---|---|
| `rodney click "<selector>"` | Click element |
| `rodney input "<selector>" "<text>"` | Type into input field |
| `rodney clear "<selector>"` | Clear input field |
| `rodney file "<selector>" <path\|->` | Set file on file input (`-` for stdin) |
| `rodney download "<selector>" [file\|-]` | Download href/src target (`-` for stdout) |
| `rodney select "<selector>" "<value>"` | Select dropdown by value |
| `rodney submit "<selector>"` | Submit a form |
| `rodney hover "<selector>"` | Hover over element |
| `rodney focus "<selector>"` | Focus element |

### Wait for Conditions

| Command | Description |
|---|---|
| `rodney wait "<selector>"` | Wait for element to appear and be visible |
| `rodney waitload` | Wait for page load event |
| `rodney waitstable` | Wait for DOM to stop changing |
| `rodney waitidle` | Wait for network to be idle |
| `rodney sleep <seconds>` | Sleep for N seconds |

### Screenshots

| Command | Description |
|---|---|
| `rodney screenshot [file]` | Save page screenshot (default: screenshot.png) |
| `rodney screenshot -w 1280 -h 720 out.png` | Set viewport size |
| `rodney screenshot-el "<selector>" [file]` | Screenshot specific element |

### Tab Management

| Command | Description |
|---|---|
| `rodney pages` | List all tabs (`*` marks active) |
| `rodney newpage [url]` | Open URL in new tab |
| `rodney page <index>` | Switch to tab by index |
| `rodney closepage [index]` | Close tab (active if no index) |

### Element Checks

| Command | Description |
|---|---|
| `rodney exists "<selector>"` | Exit 0 if exists, exit 1 if not |
| `rodney count "<selector>"` | Print number of matching elements |
| `rodney visible "<selector>"` | Exit 0 if visible, exit 1 if not |
| `rodney assert <expr> [expected] [-m msg]` | Assert truthy or equality (exit 1 on fail) |

### Accessibility

| Command | Description |
|---|---|
| `rodney ax-tree [--depth N] [--json]` | Dump full accessibility tree |
| `rodney ax-find [--role R] [--name N] [--json]` | Find accessible nodes |
| `rodney ax-node "<selector>" [--json]` | Inspect element's a11y properties |

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Check failed — command ran but condition not met (exists, visible, assert) |
| `2` | Error — bad arguments, no browser session, timeout, etc. |

## Configuration

| Environment Variable | Default | Description |
|---|---|---|
| `RODNEY_HOME` | `~/.rodney` | Data directory for state and Chrome profile |
| `ROD_CHROME_BIN` | `/usr/bin/google-chrome` | Path to Chrome/Chromium binary |
| `ROD_TIMEOUT` | `30` | Default timeout in seconds for element queries |
| `HTTPS_PROXY` / `HTTP_PROXY` | (none) | Proxy auto-detected on start |

## Directory-Scoped Sessions

Use `--local` for project-isolated sessions:

```bash
rodney start --local          # State in ./.rodney/state.json
rodney open https://example.com
rodney stop                   # Cleans up local session
```

Auto-detection: without `--local`/`--global`, rodney checks for `./.rodney/state.json` and uses local if found, otherwise global.

## Common Patterns

### Scrape text from a page

```bash
rodney start
rodney open https://example.com
rodney waitstable
rodney text "h1"
rodney text "p"
rodney stop
```

### Fill and submit a form

```bash
rodney start
rodney open https://example.com/login
rodney waitstable
rodney input "#username" "myuser"
rodney input "#password" "mypass"
rodney click "button[type=submit]"
rodney waitstable
rodney stop
```

### Screenshot multiple pages

```bash
rodney start
for url in page1 page2 page3; do
    rodney open "https://example.com/$url"
    rodney waitstable
    rodney screenshot "${url}.png"
done
rodney stop
```

### Assertion / smoke test script

```bash
#!/bin/bash
set -euo pipefail
FAIL=0

check() {
    if ! "$@"; then
        echo "FAIL: $*"
        FAIL=1
    fi
}

rodney start
rodney open "https://example.com"
rodney waitstable

check rodney exists "h1"
check rodney visible "#main-content"
check rodney assert 'document.title' 'Example Domain'
check rodney ax-find --role heading --name "Example Domain"

rodney stop

[ "$FAIL" -ne 0 ] && echo "Some checks failed" && exit 1
echo "All checks passed"
```

### Accessibility audit

```bash
rodney start
rodney open https://example.com
rodney waitstable
rodney ax-tree --json               # Full tree as JSON
rodney ax-find --role button --json  # Find all buttons
rodney ax-node "#submit-btn" --json  # Inspect specific element
rodney stop
```

## Tips

- **Always `waitstable` or `waitload`** after `open` before interacting with the page.
- **Use `--local`** when running in project directories to avoid session conflicts.
- **Use `exists`/`visible` before interacting** with elements that may not be present.
- **Quotes around selectors** — always quote CSS selectors to avoid shell interpretation.
- **`rodney js`** is the escape hatch — anything not covered by built-in commands can be done via JavaScript.
- **Exit code 1 vs 2** — check failures (1) are distinct from errors (2), enabling clean CI scripting with `set -e`.
- **Add `.rodney/` to `.gitignore`** when using local sessions.
