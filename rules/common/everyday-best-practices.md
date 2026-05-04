# Everyday Best Practices

## Timezone

- **Storage:** UTC with `Z` suffix
- **Display:** Local timezone with compact offset (`+0800`)

Check local timezone:
```bash
date +"%Z %z"   # CST +0800
```

Example:
```python
utc_now = datetime.now(timezone.utc)                    # Storage: 2026-05-03T04:21:35Z
display = utc_now.astimezone().strftime("%Y-%m-%d %H:%M %z")  # Display: 2026-05-03 12:21 +0800
```

## File Paths

- **Always absolute, never relative** — cwd resets between bash calls in subagent threads
- **Code snippets:** Only when load-bearing (bugs, function signatures) — do not recap code merely read

## Communication Style

- **Emojis:** Avoid — clear communication requires plain text
- **Tool calls:** No colon prefix — "Let me read the file." not "Let me read the file:"
