# ADDENDUM to #266-t2-seam-derivation — fold R9b into the same follow-up commit

Read with `rework2.md`; this adds one requirement to R9 and does not change anything else. Same commit, same evidence block.

## R9b — the `--status` payload belongs on stdout, including when degraded

Independently reproduced by the TM at `14bd0b9` with an absolute interpreter (`PATH=/nonexistent`, so git and gh are unresolvable):

```
pr.py --status --head feat-status           → exit 1, stdout 0 bytes, JSON on stderr
pr.py --status                               → exit 1, stdout 0 bytes, JSON on stderr
pr.py --status --head feat-status --title x   → exit 1, stdout 0 bytes, JSON on stderr
```

Two problems, and R9 as written only fixes the first:

1. **Exit 1** — R9's fix (exit 0 on every path) covers this.
2. **The channel** — the refusal payload is written to stderr, leaving stdout empty. ADR-0021 item 1 is explicit: facts go to **stdout**, commentary to stderr. `--status --json` is *the* machine-readable command, so a caller doing `pr.py --status --json | jq .predicates` gets nothing whenever anything degraded.

**Fix**: on `--status`, always write the JSON object to **stdout**, degraded or not — including the `degraded_report` path where head/repo could not be read. Keep the human-readable sentence on stderr (`--verbose` may add source detail there). A refusal entry inside the report is data; the exit code stays 0.

**Evidence**: the three commands above after the fix — exit 0, non-empty stdout that parses as JSON and satisfies the pinned schema, with `refusals[]` naming the failed read; plus a test asserting `json.loads(stdout)` succeeds on a degraded run rather than only checking the exit code.

Do not treat this as a new ticket: same commit, `#266-t2-seam-derivation`, and include it in the reply's evidence under R9.
