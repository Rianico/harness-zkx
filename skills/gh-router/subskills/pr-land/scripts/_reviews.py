"""The review-thread read surface: `pr.py --reviews` rendering and its exit rule.

`_github.fetch_review_threads` owns the GraphQL read and the fail-closed
contract. This module owns the caller-facing shape (text or `--json`) and the
stop-condition exit code. It lives outside `pr.py` to keep the entry script a
thin CLI, and outside `_status.py` so the status schema owns no second
rendering path.

Exit: 0 when no thread remains, 1 when any thread remains or no open PR
exists. A failed read raises `PrError`, which `pr.py` maps to exit 1.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import _github
from _options import PrOptions


def run_reviews(options: PrOptions, cwd: Path | None = None) -> int:
    """List unresolved review threads: the post-PR loop's collect step."""
    head = _github.resolve_head(options.head)
    repo = _github.resolve_repo(head)
    ref = _github.lookup_pr(repo, head, state="open", cwd=cwd)
    if ref is None:
        print(f"no open PR for {head}: nothing to collect", file=sys.stderr)
        return 1
    threads = _github.fetch_review_threads(repo, ref.number, cwd=cwd)
    if options.json_output:
        print(
            json.dumps(
                {
                    "pr": ref.number,
                    "url": f"https://github.com/{repo}/pull/{ref.number}",
                    "unresolved": [
                        {
                            "id": thread.thread_id,
                            "path": thread.path,
                            "line": thread.line,
                            "author": thread.author,
                            "outdated": thread.outdated,
                            "body": thread.body,
                        }
                        for thread in threads
                    ],
                },
                indent=2,
            )
        )
    else:
        for thread in threads:
            where = f"{thread.path}:{thread.line}" if thread.line else thread.path
            suffix = " (outdated)" if thread.outdated else ""
            print(f"{where} [{thread.author}]{suffix}")
            print(thread.body.strip() or "(empty body)")
    print(f"reviews: {len(threads)} unresolved", file=sys.stderr)
    return 1 if threads else 0
