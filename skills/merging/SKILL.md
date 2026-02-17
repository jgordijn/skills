---
name: merging
description: Use this when merging one branch into another. Mainly use to merge the main/master branch into the current branch. <examples><example>Merge main</example><example>Merge the master branch into this branch</example></examples>
---

# Merge Main

This command updates the current branch with the latest changes from the another branch. The other branch is mostly main or master. If this is not clear, ask the human.

## Workflow

### Step 1: Check Current Status

Before starting, verify the current state:
- Check which branch you're on
- Verify there are no uncommitted changes
- If there are uncommitted changes, ask the human whether to commit them or stash them

### Step 2: Fetch Latest Changes

Fetch the latest changes from the remote repository (mostly origin, but may be different if indicated, or if origin is missing):

```bash
git fetch origin
```

This downloads the latest changes from remote without modifying your working directory.

### Step 3: Merge Main into Current Branch

Merge the target branch into the current branch:

```bash
git merge origin/main
```

### Step 4: Handle Merge Conflicts

If merge conflicts occur:

1. **Identify conflicted files**: Git will report which files have conflicts
2. **Read each conflict carefully**: Understand what changed in both branches
3. **For each conflict**:
   - Examine the conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
   - Understand what the current branch changed
   - Understand what main branch changed
   - Determine the correct resolution
4. **Resolve conflicts**: Edit files to resolve conflicts, removing conflict markers
5. **Mark as resolved**: `git add <resolved-file>`
6. **Complete the merge**: `git commit` (or `git merge --continue`)

### Step 5: Error Handling

If you encounter any of the following situations, STOP and consult the human:

- Complex conflicts that you're unsure how to resolve
- Conflicts in critical files (build configs, schema definitions, etc.)
- Conflicts that seem to involve significant architectural changes
- Merge errors or warnings you don't understand
- The merge creates broken code or failing tests

### Step 6: Verify the Merge

After successful merge:

1. Verify the application builds: `mvn clean install` or equivalent
2. Run tests if applicable: `mvn verify -Pintegration` or equivalent (check that all tests ran unit and integration)
3. Review the merge commit to ensure nothing was lost

## Important Notes

- **Never force-push** after merging main unless explicitly instructed
- **Always test** after merging to ensure nothing broke
- **Ask before resolving complex conflicts** - it's better to be safe
- **Preserve both changes when in doubt** - you can clean up after human reviews

## Quick Reference

```bash
# Standard merge workflow
git fetch origin
git merge origin/main

# If conflicts occur
# 1. Fix conflicts in files
# 2. Mark as resolved
git add <file>
# 3. Complete merge
git commit
# 4. If there is an upstream push
git push
```
