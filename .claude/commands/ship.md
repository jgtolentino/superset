# Ship Orchestrator

You are the **ORCHESTRATOR**. Your role is to coordinate a complete docs-to-code workflow.

## Input
$ARGUMENTS

## Workflow

Execute these steps in order:

### 1. Plan
Run `/project:plan` with the user's request.
- Review the plan output
- Confirm scope is appropriate

### 2. Implement
Run `/project:implement` using the plan.
- Verify changes match the plan
- Check for minimal diffs

### 3. Verify
Run `/project:verify` until green.
- Fix any issues that arise
- Rerun until all checks pass

### 4. Commit
If verification passes:
```bash
git add -A
git commit -m "$(cat <<'EOF'
<type>(<scope>): <subject>

<body explaining what and why>
EOF
)"
```

### 5. Prepare PR Summary
Generate a PR-ready summary:

```markdown
## Summary
- What was changed and why

## Approach
- How it was implemented
- Key decisions made

## Verification Evidence
- Commands run
- Results

## Risks/Rollback
- Potential issues
- How to revert if needed
```

## Commit Message Format

Use conventional commits:
- `feat(scope):` - New feature
- `fix(scope):` - Bug fix
- `docs(scope):` - Documentation
- `refactor(scope):` - Code refactor
- `test(scope):` - Tests
- `chore(scope):` - Maintenance

## Constraints

- Do NOT push unless explicitly requested
- Do NOT create PR unless explicitly requested
- Abort if verification fails after 3 attempts
- Report all evidence transparently
