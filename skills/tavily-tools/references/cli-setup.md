# Tavily CLI Setup

Installation and authentication guide for the Tavily CLI.

## Installation

### Quick Install

```bash
curl -fsSL https://cli.tavily.com/install.sh | bash
```

### Verify Installation

```bash
tvly --version
```

## Authentication

### Interactive Login (Recommended)

```bash
tvly login
```

This opens a browser to authenticate with your Tavily account.

### API Key

For CI/CD or automated environments, follow Tavily's documentation for secure key management. Get your API key from [tavily.com](https://tavily.com).

## Troubleshooting

### Command Not Found

If `tvly` is not found after installation:

```bash
# Reload shell
source ~/.zshrc  # or ~/.bashrc

# Or add to PATH manually
export PATH="$HOME/.tavily/bin:$PATH"
```

### Authentication Issues

```bash
# Re-authenticate
tvly logout
tvly login

# Verify API key is set
echo $TAVILY_API_KEY
```

### Rate Limits

Tavily has API rate limits based on your plan:

| Plan | Extract Calls | Search Calls |
|------|---------------|--------------|
| Free | 1,000/month | 1,000/month |
| Pro | Metered | Metered |

Check usage at [tavily.com/dashboard](https://tavily.com/dashboard).
