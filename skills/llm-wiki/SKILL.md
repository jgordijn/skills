---
name: llm-wiki
description: Use when creating, discovering, maintaining, ingesting into, querying, or linting Karpathy-style LLM wikis. Supports layered wikis from the user's home directory down to the current working directory, defaulting new wikis to a contained `.llm-wiki/` directory. <examples><example>Ingest this article into my LLM wiki</example><example>Create an LLM wiki here</example><example>What does my wiki know about agent memory?</example><example>Search my LLM wikis for deployment notes</example><example>Lint the LLM wiki</example><example>File this answer in the wiki</example></examples>
---

# LLM Wiki

Use this skill for Karpathy-style LLM wikis: persistent markdown knowledge bases maintained by the agent from raw sources over time.

Core idea: do not repeatedly rediscover knowledge from raw documents. Compile durable knowledge once into a structured, interlinked wiki, keep it current, and answer future questions from the wiki first.

## Default storage layout

Default new wikis to a contained directory named `.llm-wiki/` at the selected scope:

```text
<scope>/.llm-wiki/
  raw/
    sources/
    assets/
  wiki/
    index.md
    log.md
    overview.md
    sources/
    entities/
    concepts/
    topics/
    questions/
    synthesis/
  .obsidian/        optional
    app.json        optional
```

Use this contained layout unless the user explicitly asks for a visible/direct layout.

Visible/direct layout is also supported for existing wikis:

```text
<scope>/
  raw/
  wiki/
  .obsidian/        optional
```

## Wiki roots and scopes

A scope is a directory between the user's home directory and the current working directory where Pi was started.

A wiki root is either:

- `<scope>/.llm-wiki` for the default contained layout
- `<scope>` for a visible/direct layout with `wiki/index.md`

Label scopes for the user:

- `global` for `~`
- `project` for the current working directory or a project/repository directory
- otherwise show the path

When displaying paths, prefer `~`-relative paths.

## Detecting existing wikis

An LLM wiki exists at a scope if either of these exists:

```text
<scope>/.llm-wiki/wiki/index.md
<scope>/wiki/index.md
```

Treat `.llm-wiki` as the preferred wiki root when both exist at the same scope, but mention both if ambiguity matters.

Discovery shell pattern:

```bash
python3 - <<'PY'
from pathlib import Path
home = Path.home().resolve()
cwd = Path.cwd().resolve()
try:
    rel = cwd.relative_to(home)
except ValueError:
    rel = Path()
scopes = [home]
cur = home
for part in rel.parts:
    cur = cur / part
    scopes.append(cur)
for scope in scopes:
    contained = scope / '.llm-wiki' / 'wiki' / 'index.md'
    direct = scope / 'wiki' / 'index.md'
    if contained.exists():
        print(f'existing\tcontained\t{scope}\t{scope / ".llm-wiki"}')
    if direct.exists():
        print(f'existing\tdirect\t{scope}\t{scope}')
    if not contained.exists() and not direct.exists():
        print(f'new\tcontained\t{scope}\t{scope / ".llm-wiki"}')
PY
```

## Creating a wiki

Only create or modify a wiki when the user explicitly asks to create, initialize, ingest, file, or update.

For a new default contained wiki, create:

```bash
mkdir -p .llm-wiki/raw/sources .llm-wiki/raw/assets \
  .llm-wiki/wiki/{sources,entities,concepts,topics,questions,synthesis}
```

Create initial files if missing:

```text
.llm-wiki/wiki/index.md
.llm-wiki/wiki/log.md
.llm-wiki/wiki/overview.md
```

Suggested initial content:

```markdown
# Wiki Index

This index catalogs durable pages in this LLM wiki. Read this first before querying or ingesting.

## Sources

## Entities

## Concepts

## Topics

## Questions

## Synthesis
```

```markdown
# Wiki Log

Chronological record of wiki operations.
```

```markdown
# Wiki Overview

This LLM wiki compiles durable knowledge for this scope.
```

### Optional Obsidian vault

Ask before creating `.obsidian/` unless the user explicitly requested Obsidian.

If requested, create:

```bash
mkdir -p .llm-wiki/.obsidian
cat > .llm-wiki/.obsidian/app.json <<'EOF'
{
  "attachmentFolderPath": "raw/assets"
}
EOF
```

The Obsidian vault root is `.llm-wiki/`, not the project root, for contained wikis.

## Git ignore guidance

Do not edit `.gitignore` unless the user asks.

If the wiki should remain private/local, suggest ignoring only the contained wiki directory:

```gitignore
.llm-wiki/
```

If the user wants to commit the compiled wiki but not raw sources, discuss a visible/direct or custom layout first. Do not silently ignore broad names like `raw/` or `wiki/` in code repositories.

## Ingest workflow with layered wiki selection

When the user asks to ingest a source and does not specify a wiki:

1. Discover all scopes from `~` to the current working directory.
2. Find existing wikis at those scopes.
3. Find scopes without wikis as possible new wiki locations.
4. Present a numbered menu grouped as `Existing` and `New`.
5. Ask the user to reply with a number.
6. Do not ingest until the user chooses.

Example menu:

```text
Where do you want to ingest?

Existing:
1: global: ~
2: project: ~/projects/x/y/z

New:
3: ~/projects/x
4: ~/projects/x/y

Reply with a number.
```

If the user selects a new location, initialize the contained `.llm-wiki/` there, then ingest.

### Ingest steps

For the selected wiki root:

1. Inspect existing wiki layout and any local instructions.
2. Read `wiki/index.md` first.
3. Read recent entries from `wiki/log.md`.
4. Preserve the raw source under `raw/sources/` or record its stable location.
5. Read the source and needed assets.
6. Identify affected pages.
7. Create or update pages in appropriate homes:
   - `wiki/sources/` for source summaries
   - `wiki/entities/` for named people, orgs, systems, APIs, files, modules, services
   - `wiki/concepts/` for reusable ideas, rules, abstractions, patterns
   - `wiki/topics/` for broad subject areas
   - `wiki/questions/` for filed answers to specific questions
   - `wiki/synthesis/` for cross-source models, decisions, timelines, comparisons, and interpretations
8. Integrate into existing pages rather than only adding isolated summaries.
9. Add source references near important claims.
10. Mark contradictions explicitly; do not silently erase tension.
11. Update `wiki/index.md`.
12. Append to `wiki/log.md` using this heading style:

```markdown
## [YYYY-MM-DD] ingest | Source title
```

13. Report changed files and key judgments.

Prefer one source at a time unless the user asks for batch ingestion.

## Query workflow across layered wikis

When the user asks for information that may be in the wiki:

1. Discover all existing LLM wikis from the current directory up to `~`.
2. Read each discovered `wiki/index.md` first.
3. Search relevant wiki pages with `rg` or available local search tools.
4. Read the most relevant pages before answering.
5. Prefer more local/specific wikis for project-specific facts.
6. Use broader/global wikis for reusable concepts, personal preferences, general research, and cross-project context.
7. If wikis conflict, state the conflict and prefer the more local wiki for local/project-specific claims.
8. Cite page paths in the answer when possible.
9. Use raw sources only when the wiki lacks enough detail or a claim needs verification.
10. If the answer is durable, offer to file it, but do not write unless the user explicitly asks.

Do not answer from general model memory when a relevant discovered wiki likely contains the answer.

## Filing answers back

Only file an answer when the user explicitly says something like:

- `file this`
- `add this to the wiki`
- `update the wiki`
- `ingest this answer`

If the target wiki is unspecified, use the same numbered wiki selection flow as ingest.

File durable outputs such as comparisons, decisions, explanations, timelines, research notes, and reusable syntheses under `wiki/questions/`, `wiki/synthesis/`, or another suitable existing convention. Update related pages, update `wiki/index.md`, and append a `query` or `maintenance` log entry.

## Lint workflow

When asked to lint, audit, or health-check:

1. If no specific wiki is named, discover and ask which wiki or wikis to lint.
2. Check for:
   - missing or stale index entries
   - unresolved or broken links
   - orphan pages
   - duplicate or overlapping pages
   - unsupported important claims
   - contradictions
   - stale claims superseded by newer sources
   - source summaries not integrated elsewhere
   - empty schema directories despite matching knowledge
   - question pages that should be factored into concepts/entities/synthesis
3. Apply safe fixes only when requested or clearly implied.
4. Append a log entry:

```markdown
## [YYYY-MM-DD] lint | Scope
```

## Linking conventions

Follow the existing wiki's convention.

- If the wiki uses Obsidian links, use Obsidian-compatible wikilinks.
- If the wiki uses markdown links, use relative markdown links.
- For Obsidian links to files in folders, prefer path-qualified aliases like `[[concepts/source-provenance|Source Provenance]]`.
- Do not introduce unresolved links knowingly.

## Operating rules

- The user curates sources and decides what is worth filing.
- The agent maintains the wiki when explicitly asked.
- Read/search/query is allowed when relevant; writes require explicit intent.
- Raw sources are immutable.
- Wiki pages should compound knowledge rather than accumulate disconnected summaries.
- Preserve provenance.
- Prefer small, reviewable edits.
- Keep global and local knowledge layered, not mixed accidentally.
