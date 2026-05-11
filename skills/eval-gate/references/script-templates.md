# Eval Script Templates

Reusable script templates for deterministic eval verification. Each script outputs JSON that the orchestrator parses.

## Template: Type Checking

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Type checking eval script. Outputs JSON with status and issues."""
import subprocess
import json
import sys
from pathlib import Path

def main():
    # Run type checker with JSON output
    result = subprocess.run(
        ["basedpyright", "--outputjson"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )

    try:
        data = json.loads(result.stdout) if result.stdout else {}
    except json.JSONDecodeError:
        print(json.dumps({
            "status": "fail",
            "summary": "Failed to parse type checker output",
            "issues": [result.stderr or "Unknown error"]
        }))
        return

    # Extract diagnostics
    diagnostics = data.get("generalDiagnostics", [])
    
    # Filter by severity if needed (e.g., only errors, or errors + warnings)
    issues = [
        f"{d.get('file', 'unknown')}:{d.get('range', {}).get('start', {}).get('line', 0) + 1}: [{d.get('severity_name', 'unknown')}] {d.get('message', '')}"
        for d in diagnostics
        # Adjust filter as needed: if d.get('severity') == 1  # errors only
    ]

    output = {
        "status": "pass" if len(issues) == 0 else "fail",
        "summary": f"{len(issues)} type issues found" if issues else "No type issues",
        "issues": issues,
        "total_diagnostics": len(diagnostics),
        "error_count": sum(1 for d in diagnostics if d.get('severity') == 1),
        "warning_count": sum(1 for d in diagnostics if d.get('severity') == 2)
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
```

## Template: Pattern Check (Bash)

```bash
#!/usr/bin/env bash
# Pattern check eval script. Outputs JSON with status and matching lines.

set -euo pipefail

PATTERN="${1:-}"
PATHS="${2:-src/}"
EXCLUDE="${3:-}"  # Pipe-separated patterns to exclude

if [ -z "$PATTERN" ]; then
    echo '{"status": "fail", "summary": "No pattern provided", "issues": ["Usage: script <pattern> <paths> <exclude_pattern>"]}'
    exit 0
fi

# Build exclude filter
if [ -n "$EXCLUDE" ]; then
    MATCHES=$(rg "$PATTERN" $PATHS --type py | grep -Ev "$EXCLUDE" || true)
else
    MATCHES=$(rg "$PATTERN" $PATHS --type py || true)
fi

if [ -z "$MATCHES" ]; then
    echo '{"status": "pass", "summary": "No matches found", "issues": []}'
else
    ISSUES=$(echo "$MATCHES" | jq -R -s 'split("\n") | map(select(length > 0))')
    echo "{\"status\": \"fail\", \"summary\": \"Pattern found: $PATTERN\", \"issues\": $ISSUES}"
fi
# Always exit 0 — status is in JSON output
```

## Template: Test Runner

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Test runner eval script. Outputs JSON with test results."""
import subprocess
import json
import sys
import re
from pathlib import Path

def main():
    # Run tests
    result = subprocess.run(
        ["uv", "run", "pytest", "tests/", "-q", "--tb=no"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent  # Adjust as needed
    )

    output_text = result.stdout + result.stderr
    
    # Parse pytest output
    # Look for: "X passed", "Y failed", "Z errors"
    passed_match = re.search(r'(\d+) passed', output_text)
    failed_match = re.search(r'(\d+) failed', output_text)
    error_match = re.search(r'(\d+) error', output_text)
    
    passed = int(passed_match.group(1)) if passed_match else 0
    failed = int(failed_match.group(1)) if failed_match else 0
    errors = int(error_match.group(1)) if error_match else 0
    
    # Extract failed test names if any
    issues = []
    if failed > 0 or errors > 0:
        # Simple extraction - adjust based on your pytest output format
        for line in output_text.split('\n'):
            if 'FAILED' in line or 'ERROR' in line:
                issues.append(line.strip())

    output = {
        "status": "pass" if (failed == 0 and errors == 0) else "fail",
        "summary": f"{passed} passed, {failed} failed, {errors} errors",
        "issues": issues,
        "passed": passed,
        "failed": failed,
        "errors": errors
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
```

## Template: LSP Diagnostics

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""LSP workspace diagnostics eval script. Outputs JSON with diagnostics."""
import subprocess
import json
import sys
from pathlib import Path

def main():
    # Run LSP diagnostics command
    result = subprocess.run(
        ["llm-lsp-cli", "lsp", "workspace-diagnostics"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent.parent.parent
    )

    try:
        data = json.loads(result.stdout) if result.stdout else {}
    except json.JSONDecodeError:
        print(json.dumps({
            "status": "fail",
            "summary": "Failed to parse LSP output",
            "issues": [result.stderr or "Unknown error"]
        }))
        return

    # Extract all diagnostics
    issues = []
    for file_entry in data.get("files", []):
        file_path = file_entry.get("file", "unknown")
        for diag in file_entry.get("diagnostics", []):
            severity = diag.get("severity_name", "unknown")
            message = diag.get("message", "")
            range_str = diag.get("range", "")
            code = diag.get("code", "")
            issues.append(f"{file_path}:{range_str}: [{severity}] {message} ({code})")

    # Decide pass/fail based on severity
    # Option 1: Only errors fail
    # has_errors = any(d.get("severity") == 1 for f in data.get("files", []) for d in f.get("diagnostics", []))
    
    # Option 2: Any diagnostic fails (stricter)
    has_issues = len(issues) > 0

    output = {
        "status": "pass" if not has_issues else "fail",
        "summary": f"{len(issues)} diagnostics found" if issues else "No diagnostics",
        "issues": issues,
        "file_count": len(data.get("files", [])),
        "diagnostic_count": len(issues)
    }
    print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
```

## Template: File Existence/Content Check

```bash
#!/usr/bin/env bash
# File check eval script. Outputs JSON with status.

set -euo pipefail

FILE_PATH="${1:-}"
EXPECTED_CONTENT="${2:-}"  # Optional pattern to check in file

if [ -z "$FILE_PATH" ]; then
    echo '{"status": "fail", "summary": "No file path provided", "issues": []}'
    exit 0
fi

if [ ! -f "$FILE_PATH" ]; then
    echo "{\"status\": \"fail\", \"summary\": \"File not found: $FILE_PATH\", \"issues\": [\"File does not exist\"]}"
    exit 0
fi

if [ -n "$EXPECTED_CONTENT" ]; then
    if grep -q "$EXPECTED_CONTENT" "$FILE_PATH"; then
        echo "{\"status\": \"pass\", \"summary\": \"File exists and contains expected content\", \"issues\": []}"
    else
        echo "{\"status\": \"fail\", \"summary\": \"File exists but missing expected content\", \"issues\": [\"Pattern not found: $EXPECTED_CONTENT\"]}"
    fi
else
    echo "{\"status\": \"pass\", \"summary\": \"File exists: $FILE_PATH\", \"issues\": []}"
fi
```

## Usage in Eval Definition

Each criterion references a script:

```markdown
### CAP-01: Type Safety

**Description:** All Python files pass type checking with 0 errors/warnings.

**Grader:** code

**Script:** `scripts/typecheck.py`

**Pass Condition:** JSON output has `"status": "pass"`
```

The eval agent runs:
```bash
uv run scripts/typecheck.py
```

And parses the JSON output to determine pass/fail.
