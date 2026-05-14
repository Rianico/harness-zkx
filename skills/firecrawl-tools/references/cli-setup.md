# CLI Setup

Installation and authentication for the Firecrawl CLI.

## Quick Setup (Recommended)

```bash
npx -y firecrawl-cli@latest init -y --browser
```

This installs `firecrawl-cli` globally, authenticates via browser, and installs all skills.

This setup is safe to re-run when the CLI is missing, stale, or only partially configured.

If `firecrawl` is already installed and you want to update it first:

```bash
npm update -g firecrawl-cli
```

## Manual Install

```bash
npm install -g firecrawl-cli
```

## Verify

First check status:

```bash
fcrawl --status
```

Then run one small real request to prove install, auth, and output all work:

```bash
mkdir -p .lsz/.firecrawl/install-check
fcrawl scrape "https://firecrawl.dev" -o .lsz/.firecrawl/install-check/page.md
```

The install is healthy when both commands succeed.

## Authentication

Authenticate using the built-in login flow:

```bash
fcrawl login --browser
```

This opens the browser for OAuth authentication. Credentials are stored securely by the CLI.

### If authentication fails

Ask the user how they'd like to authenticate:

1. **Login with browser (Recommended)** - Run `fcrawl login --browser`
2. **Enter API key manually** - Run `fcrawl login --api-key "<key>"` with a key from firecrawl.dev

### Command not found

If `firecrawl` is not found after installation:

1. Ensure npm global bin is in PATH
2. Try: `npx firecrawl-cli --version`
3. Reinstall: `npm install -g firecrawl-cli`
