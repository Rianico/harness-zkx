# /// script
# dependencies = []
# ///
"""
Secret scrubbing functionality for observations.

Redacts sensitive data before observations are persisted.
"""

import re

# Secret patterns to redact
SECRET_PATTERNS = [
    # OpenAI API keys
    (r"sk-proj-[a-zA-Z0-9]{32,}", "OpenAI API key"),
    (r"sk-[a-zA-Z0-9]{16,}", "API key"),
    # GPT tokens
    (r"gpt_[a-zA-Z0-9]{16,}", "GPT token"),
    # GitHub tokens
    (r"ghp_[a-zA-Z0-9]{36,}", "GitHub token"),
    (r"gho_[a-zA-Z0-9]{36,}", "GitHub OAuth token"),
    (r"ghu_[a-zA-Z0-9]{36,}", "GitHub user token"),
    (r"ghs_[a-zA-Z0-9]{36,}", "GitHub server token"),
    (r"ghr_[a-zA-Z0-9]{36,}", "GitHub refresh token"),
    # Slack tokens
    (r"xox[baprs]-[0-9]{10,}-[0-9]{10,}-[a-zA-Z0-9]{24,}", "Slack token"),
    # AWS credentials
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"(?<![A-Za-z0-9/+])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])", "AWS secret key candidate"),
    # Generic tokens
    (r"TOKEN\s*=\s*[a-zA-Z0-9_\-]{16,}", "TOKEN assignment"),
    (r"PASSWORD\s*=\s*[^\s\n]+", "PASSWORD assignment"),
    (r"SECRET_KEY\s*=\s*[^\s\n]+", "SECRET_KEY assignment"),
    # Authorization headers
    (r"Authorization:\s*Bearer\s+[a-zA-Z0-9_\-\.]+", "Authorization header"),
    (r"Bearer\s+[a-zA-Z0-9_\-\.]{16,}", "Bearer token"),
    # Basic auth in URLs
    (r"://[^:\s]+:[^@\s]+@", "credentials in URL"),
    # Basic auth in curl commands (-u user:password)
    (r"-u\s+\S+:\S+", "curl basic auth"),
    # Private keys
    (
        r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----"
        r"[\s\S]*?"
        r"-----END\s+(RSA\s+)?PRIVATE\s+KEY-----",
        "Private key",
    ),
]


def scrub_secrets(text: str) -> str:
    """
    Redact sensitive data from text.

    Args:
        text: The text to scrub.

    Returns:
        Text with secrets replaced by [REDACTED].
    """
    result = text
    for pattern, _ in SECRET_PATTERNS:
        result = re.sub(pattern, "[REDACTED]", result)

    return result


def scrub_value(value: object) -> object:
    """
    Recursively scrub secrets from any value.

    Args:
        value: The value to scrub (str, dict, list, or other).

    Returns:
        A new value with secrets redacted.
    """
    if isinstance(value, str):
        return scrub_secrets(value)
    if isinstance(value, dict):
        return {k: scrub_value(v) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub_value(item) for item in value]
    return value


def scrub_dict(data: dict) -> dict:
    """
    Recursively scrub secrets from a dictionary.

    Args:
        data: The dictionary to scrub.

    Returns:
        A new dictionary with secrets redacted.
    """
    result: dict = {}
    for key, value in data.items():
        result[key] = scrub_value(value)
    return result


def scrub_list(data: list) -> list:
    """
    Recursively scrub secrets from a list.

    Args:
        data: The list to scrub.

    Returns:
        A new list with secrets redacted.
    """
    result: list = []
    for item in data:
        result.append(scrub_value(item))
    return result
