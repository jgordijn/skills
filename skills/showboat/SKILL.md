---
name: showboat
description: Use when creating executable demo documents that show and prove an agent's work — mixing commentary, executable code blocks, and captured output in a verifiable markdown file. <examples><example>Create a demo document</example><example>Build an executable demo</example><example>Create a showboat document</example><example>Show my work in a demo</example><example>Verify a demo document</example></examples>
---

Always consult the full README for the latest commands and options: https://raw.githubusercontent.com/simonw/showboat/refs/heads/main/README.md

# Showboat — Executable Demo Documents

A Go CLI tool that creates markdown documents mixing commentary, executable code blocks, and captured output. The documents serve as both readable documentation and reproducible proof of work. A verifier can re-execute all code blocks and confirm the outputs still match.

**Repository**: https://github.com/simonw/showboat

## Installation

```bash
# Run without installing
uvx showboat --help

# Install via uv or pip
uv tool install showboat
# or
pip install showboat

# Or install the Go binary directly
go install github.com/simonw/showboat@latest
```

## Essential Workflow

Always follow this pattern when building a demo:

```bash
# 1. Create the document
showboat init demo.md "My Demo Title"

# 2. Add commentary explaining what you're about to do
showboat note demo.md "First, let's set up the environment."

# 3. Execute a command and capture its output
showboat exec demo.md bash "echo 'Hello World'"

# 4. If a command fails, remove it and redo
showboat pop demo.md
showboat exec demo.md bash "echo 'Fixed command'"

# 5. Add images when needed
showboat image demo.md screenshot.png
# or with alt text
showboat image demo.md '![Homepage screenshot](screenshot.png)'

# 6. Verify everything still works
showboat verify demo.md
```

## Command Reference

| Command | Description |
|---|---|
| `showboat init <file> <title>` | Create a new demo document (errors if file exists) |
| `showboat note <file> [text]` | Append commentary prose (text or stdin) |
| `showboat exec <file> <lang> [code]` | Run code, capture output, append both to document |
| `showboat image <file> <path>` | Copy image into document directory, append reference |
| `showboat image <file> '![alt](path)'` | Copy image with alt text |
| `showboat pop <file>` | Remove the most recent entry (code+output or note) |
| `showboat verify <file>` | Re-run all code blocks, diff against recorded output |
| `showboat verify <file> --output <new>` | Write updated copy with new outputs |
| `showboat extract <file>` | Emit commands that would recreate the document |
| `showboat extract <file> --filename <name>` | Emit commands with a different filename |

### Global Options

| Option | Description |
|---|---|
| `--workdir <dir>` | Set working directory for code execution (default: current) |
| `--version` | Print version and exit |
| `--help, -h` | Show help message |

## Key Behaviors

### Exec output and exit codes

`exec` prints the captured shell output to stdout and exits with the same exit code as the executed command. This lets you see what happened and react to errors. The output is still appended to the document regardless of exit code.

```bash
showboat exec demo.md bash "echo hello && exit 1"
# prints: hello
# exit code: 1 (same as the executed command)
```

### Pop for error recovery

Use `pop` when a command fails and you want to remove it from the document. For an exec entry it removes both the code block and its output block. For a note it removes the commentary block.

### Stdin support

All commands accept input from stdin when the text/code argument is omitted:

```bash
echo "Hello world" | showboat note demo.md
cat script.sh | showboat exec demo.md bash
```

## Markdown Format

A showboat document is plain markdown with this structure:

````markdown
# My Demo Title

*2026-02-06T15:30:00Z*

Commentary text goes here.

```bash
echo "Hello"
```

```output
Hello
```

```python3
print("Hello from Python")
```

```output
Hello from Python
```

```bash {image}
screenshot.png
```

![screenshot](screenshot.png)
````

Each element maps to exactly one CLI command, making the format fully round-trippable via `extract`.

## Remote Document Streaming

Set `SHOWBOAT_REMOTE_URL` to POST document updates to a remote viewer in real time:

```bash
export SHOWBOAT_REMOTE_URL=https://www.example.com/showboat
# With authentication:
export SHOWBOAT_REMOTE_URL=https://www.example.com/showboat?token=secret-token
```

Each document gets a UUID stored as an HTML comment. Remote errors are warnings only — they never fail the main command.

## Tips

- **Always `init` first** — `exec` and `note` error on non-existent files.
- **Use `pop` to recover from errors** — see the exit code, decide to keep or remove.
- **`verify` is your proof** — run it at the end to confirm all outputs are reproducible.
- **`extract` for portability** — emit the commands to recreate a document elsewhere.
- **Multiple languages** — `exec` supports any interpreter: `bash`, `python`, `python3`, `node`, etc.
- **Commentary between code blocks** — use `note` to explain what you're about to demonstrate.
- **Working directory** — use `--workdir` when commands need to run from a specific directory.
