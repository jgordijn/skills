---
name: context7-docs
description: Use when working with any library or framework and needing up-to-date documentation, API references, or code examples. Use when unsure about current API signatures, deprecated patterns, or version-specific behavior. Consult before relying on training data for library usage.
---

# Context7 Documentation Lookup

## Overview

Context7 provides up-to-date library documentation via a REST API. Use it to get current, accurate docs instead of relying on potentially outdated training data.

## When to Use

- Working with a library and unsure about current API
- Need code examples for a specific library feature
- Checking if an API is deprecated or changed
- Version-specific documentation needed
- Unfamiliar library or recent major version changes

## Quick Reference

| Action | Endpoint | Key Params |
|--------|----------|------------|
| Find library ID | `GET https://context7.com/api/v2/libs/search` | `libraryName`, `query` |
| Get docs/context | `GET https://context7.com/api/v2/context` | `libraryId`, `query`, `type` |

## Two-Step Workflow

### Step 1: Search for the library

```bash
curl -s 'https://context7.com/api/v2/libs/search?libraryName=LIBRARY&query=YOUR_QUESTION'
```

Pick the best match from results. Use the `id` field (format: `/owner/repo`) as `libraryId` in step 2.

**Choosing the right result:** Prefer entries with `state: "finalized"`, high `trustScore` (0-10), and `verified: true`. The results are already ranked by relevance.

### Step 2: Get documentation context

```bash
curl -s 'https://context7.com/api/v2/context?libraryId=/owner/repo&query=YOUR_QUESTION'
```

Returns relevant documentation snippets and code examples as plain text (default).

**Parameters:**

| Param | Required | Description |
|-------|----------|-------------|
| `libraryId` | Yes | From search results, format `/owner/repo` or `/owner/repo/version` |
| `query` | Yes | Natural language question (max 500 chars) |
| `type` | No | `txt` (default) or `json` for structured response |

## Example

Looking up Next.js App Router documentation:

```bash
# Step 1: Find the library
curl -s 'https://context7.com/api/v2/libs/search?libraryName=nextjs&query=app+router+layouts'
# → Use id "/vercel/next.js" from results

# Step 2: Get docs
curl -s 'https://context7.com/api/v2/context?libraryId=/vercel/next.js&query=how+to+use+app+router+layouts'
```

## Auth & Rate Limits

- **No auth required** for basic usage
- For higher rate limits, use Bearer token: `Authorization: Bearer <API_KEY>`
- API keys start with `ctx7sk` prefix, get one at context7.com/dashboard
- On 429 (rate limited), check `Retry-After` header

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Using library name as `libraryId` | Always search first to get the correct `/owner/repo` format ID |
| Skipping search step | The `libraryId` is NOT the npm/pip package name |
| Overly broad query | Be specific: "useState hook patterns" not just "react" |
| Ignoring `state` field | Only use libraries with `state: "finalized"` |

## Response Codes

- **200**: Success
- **202**: Library is still processing, try again later
- **301**: Library ID changed, follow redirect
- **404**: Library not found
- **429**: Rate limited
