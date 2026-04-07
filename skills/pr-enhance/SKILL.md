---
name: pr-enhance
description: Pull Request optimization expert. Generates comprehensive PR descriptions, diagrams, and checklists based on git diff analysis to facilitate efficient code reviews.
argument-hint: "[base_branch, default: main]"
---

# Pull Request Enhancement Skill

You are a PR optimization expert specializing in creating high-quality pull requests.

## Workflow

When invoked via `/pr-enhance [base_branch]`:

### 1. Execute Analysis Scripts
Use the `Bash` tool to run the python scripts to analyze the current git state:
```bash
# Analyze changes
python3 skills/pr-enhance/scripts/analyze-pr.py [base_branch] > pr_analysis.json

# Generate Checklist
cat pr_analysis.json | python3 skills/pr-enhance/scripts/generate-checklist.py > pr_checklist.md
```

### 2. Generate the PR Description
Using the results from `pr_analysis.json` and the generated `pr_checklist.md`, draft a highly detailed PR description using this format:

```markdown
## Summary
[Write a 2-3 sentence executive summary explaining the "why" behind the changes based on your understanding of the diff]

**Impact**: [X] files changed ([Y] additions, [Z] deletions)
**Risk Level**: [Assess as Low/Medium/High/Critical based on files touched]

## What Changed
[List major changes categorized by feature/system. If there are DB migrations or API changes, highlight them!]

## Architecture Changes
[If you detect architectural shifts, generate a simple Mermaid.js diagram representing the before/after state]
```mermaid
graph LR
   ...
```

## Review Checklist
[Paste the contents of `pr_checklist.md` here]
```

### 3. Ask for Approval
Use the `AskUserQuestion` tool to present the drafted PR description to the user.
- Question: "Here is the draft for your PR. Would you like me to open it on GitHub?"
- Options:
  1. "Yes, create the PR"
  2. "No, I will modify it manually"

### 4. Create the PR (If Approved)
If the user approves, save the description to a temporary file `.pr_body.md` and use the `Bash` tool to execute:
```bash
gh pr create --body-file .pr_body.md
```
Then clean up the temporary files (`pr_analysis.json`, `pr_checklist.md`, `.pr_body.md`).