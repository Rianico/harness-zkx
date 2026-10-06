# Qoder CLI Agent Reference

Reference for running the Qoder CLI coding agent under Herdr. Herdr knows one kind, `qodercli`;
which build you get is decided by the binary name, not the kind.

## Command & Binary

- `herdr agent start <name> --kind qodercli --pane <pane_id> -- <native-flags>`
- `qoderclicn` is **not** a valid `--kind` (`herdr agent start --help` lists `qodercli` only).
  A kind mismatch is refused before any pane work.
- The binary name picks the distribution and the configuration root:

  | Binary | Distribution | Config root | Trust list |
  |---|---|---|---|
  | `qodercli` | standard | `~/.qoder` | `permissions.trustDirectories` |
  | `qoderclicn` | China | `~/.qoder-cn` | `permissions.trustDirectories` |

- The same program serves both names, so a symlink decides the build. Check before assuming:
  the startup banner reads `Qoder CLI` or `Qoder CLI CN`, and `realpath "$(which qodercli)"`
  shows which build is installed.
- Trust and hooks are **per config root**. Trusting a worktree under `qodercli` does not trust
  it under `qoderclicn`. Override the root for one run with `--config-dir <dir>`.

## YOLO Bootstrap

Pass the bypass mode after `--` so the agent never stops for approval:

```bash
herdr agent start q-impl --kind qodercli --pane "$PANE_ID" -- --permission-mode bypass_permissions
```

- `--permission-mode` choices: `default`, `accept_edits`, `bypass_permissions`, `dont_ask`, `auto`.
  `bypass_permissions` is the YOLO mode; the status line then reads `YOLO`, with
  `Shift+Tab to Auto Mode` as the hint.
- `--dangerously-skip-permissions` is an equivalent consent-gated bypass flag.
- **Bypass mode does not skip folder trust.** A fresh worktree still blocks on the trust
  selector with the bypass flag set (verified: no keystrokes ⇒ still blocked).

## Folder Trust

On first launch in an untrusted directory Qoder CLI shows a blocking two-option selector and
loads nothing else:

```text
 Do you trust the files in this folder?
 /private/tmp/example-worktree
  ❯ 1. Trust folder
    2. Don't trust and exit
 ↑/↓ navigate · Enter select · Esc back
```

Trust is recorded per directory in `<config-root>/settings.json` →
`permissions.trustDirectories`, resolved to a real path (`/tmp/x` is stored as
`/private/tmp/x`). There is no `--approve`-style flag; trust is a durable setting, not a
launch argument.

### Readiness lies: `agent start` reports ready while the trust selector is up

`herdr agent start` returns `agent_status: idle` and `interactive_ready: true`, and the
terminal title already reads `◇ Qoder CLI CN | Ready`, **while the pane is blocked on the
trust selector**. A prompt sent at that moment is swallowed by the selector and the folder
stays untrusted. Treat the title and the ready flag as unproven for this agent and read the
pane instead:

```bash
herdr pane read "$PANE_ID" --source visible --lines 16
```

### The extra CR

Dismiss the selector with one bare Enter before sending any prompt. Prompt text cannot
dismiss it — only `Enter`, `↑`/`↓`, and `Esc` are accepted, so a payload sent as text plus
Enter loses the text and leaves the folder untrusted (verified end to end under Herdr).

```bash
herdr agent send-keys q-impl enter          # the extra CR
sleep 2
herdr pane read "$PANE_ID" --source visible --lines 16   # expect the YOLO status line
herdr_prompt.py q-impl --file ticket.md --no-wait
```

Confirm the main UI before prompting. The ready markers are the `YOLO` badge, the
`Type your message or @path/to/file` prompt, and the `Model · <cwd>` footer; the trust
selector means the CR has not landed yet.

### Pre-trust instead of pressing CR

Seeding the trust list removes the ordering problem entirely — no CR, no race, and it works
from a script. Run it before `herdr agent start`, using the worktree path as the CLI resolves
it (`realpath`):

```bash
WORKTREE=$(realpath "$WORKTREE_PATH")
python3 - "$WORKTREE" <<'EOF'
import json, os, sys
from pathlib import Path
root = Path(os.environ.get("QODER_CONFIG_DIR", Path.home() / ".qoder"))  # ~/.qoder-cn for the CN build
settings = root / "settings.json"
data = json.loads(settings.read_text()) if settings.exists() else {}
trusted = data.setdefault("permissions", {}).setdefault("trustDirectories", [])
if sys.argv[1] not in trusted:
    trusted.append(sys.argv[1])
settings.write_text(json.dumps(data, indent=2))
EOF
```

## Provider & Model

- `-m, --model <model>` — model for the session.
- `--reasoning-effort <level>`, `--thinking <mode>` (`auto`, `adaptive`, …).
- Custom endpoints are configured through `qodercli config`, not launch flags.

## Session & Resume

- Herdr reports **no `agent_session`** for this kind, so `herdr_transcript.py` falls back to
  reading the pane. Resume goes through the CLI's own store, not a session path:
  - `herdr_prompt.py` builds the resume command as `qodercli resume` (or `qoderclicn resume`).
  - `-c, --continue` resumes the most recent session; `-r, --resume [id]` resumes by
    identifier; `--list-sessions` lists them; `--session-id <id>` pins one; `-n, --name <name>`
    labels it.

## Herdr Integration Hook

`herdr integration install qodercli` reports `current (v3)` at
`~/.qoder/hooks/herdr-agent-state.sh`, registered in that root's `settings.json` under
`hooks`. The hook reports the session back with `herdr pane report-agent-session` only when
`HERDR_ENV=1`.

The hook is written to the **standard** root (`~/.qoder`). A CN build reads `~/.qoder-cn`,
which has no such hook, so it never reports a session — install into the root the binary
actually reads, or copy the hook and its `hooks` registration into that root.

## Known Quirks & Failure Modes

- `agent start` ready flag and `Ready` title are false for the trust selector — always read
  the pane (see above).
- A payload sent before the extra CR is silently swallowed; the folder also stays untrusted,
  so the failure repeats on every later prompt until an operator presses Enter.
- Two config roots are easy to mix up when both binaries are on `PATH`; a worktree trusted
  under one is untrusted under the other.
- Startup may print `warnings loading skill configs`; harmless, check with `/skills`.
- The CLI self-updates on launch; an `Update successful!` banner can delay readiness on the
  first run after a release.
