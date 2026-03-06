"""Shared utilities for rule-creator scripts."""

import re
from pathlib import Path


def parse_rule_frontmatter(file_path: Path) -> dict:
    """Parse YAML frontmatter from a rule file.

    Returns a dict with keys found in the frontmatter (e.g., paths).
    Returns empty dict if no frontmatter.

    Note: This is a simplified YAML parser sufficient for rule frontmatter.
    It does not handle nested structures, anchors/aliases, or complex multiline
    strings (e.g., quoted scalars with escape sequences). For full YAML
    compliance, use PyYAML (``yaml.safe_load``).
    """
    content = file_path.read_text(encoding="utf-8")
    lines = content.split("\n")

    if not lines or lines[0].strip() != "---":
        return {}

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return {}

    result = {}
    frontmatter_lines = lines[1:end_idx]
    i = 0
    while i < len(frontmatter_lines):
        line = frontmatter_lines[i]
        match = re.match(r"^(\w[\w-]*):\s*(.*)", line)
        if match:
            key = match.group(1)
            value = match.group(2).strip()
            if value in (">", "|", ">-", "|-"):
                # Multiline scalar
                continuation = []
                i += 1
                while i < len(frontmatter_lines) and (
                    frontmatter_lines[i].startswith("  ")
                    or frontmatter_lines[i].startswith("\t")
                ):
                    continuation.append(frontmatter_lines[i].strip())
                    i += 1
                result[key] = " ".join(continuation)
                continue
            elif value.startswith("["):
                # Inline list
                result[key] = value
            elif value.lower() == "true":
                result[key] = True
            elif value.lower() == "false":
                result[key] = False
            else:
                result[key] = value.strip('"').strip("'")
        elif line.startswith("  - ") and result:
            # YAML list item continuation
            if not result:
                i += 1
                continue
            last_key = list(result.keys())[-1]
            current = result[last_key]
            if isinstance(current, str) and current == "":
                result[last_key] = [line.strip().removeprefix("- ")]
            elif isinstance(current, list):
                result[last_key].append(line.strip().removeprefix("- "))
        i += 1

    return result


# Recommended thresholds — these are guidelines, not official limits.
# Unconditional rules should be kept as short as possible since every
# conversation pays the cost. Path-targeted rules have more room.
ACTIVATION_MODE_THRESHOLDS = {
    "unconditional": {"lines": 50, "tokens": 250},
    "path_targeted": {"lines": 200, "tokens": 1000},
}


def get_activation_mode(frontmatter: dict) -> str:
    """Determine how a rule activates based on its frontmatter.

    Returns one of: 'unconditional', 'path_targeted'.
    - No frontmatter → 'unconditional' (loaded every conversation)
    - Has 'paths:' → 'path_targeted' (loaded when matching files are involved)
    - Has frontmatter but no 'paths:' → 'unconditional' (unrecognized fields are ignored)
    """
    if not frontmatter:
        return "unconditional"

    if "paths" in frontmatter:
        return "path_targeted"
    return "unconditional"


def detect_rule_system(file_path: str | Path) -> str:
    """Detect which rule system a file belongs to.

    Returns 'claude_rules' for .claude/rules/ files, or 'unknown'.
    """
    path_str = str(file_path)
    if ".claude/rules/" in path_str:
        return "claude_rules"
    return "unknown"


def estimate_tokens(text: str) -> int:
    """Estimate token count (~4 chars per token)."""
    # Heuristic: 1 token ≈ 4 characters for English text. This can under-
    # estimate for code-heavy content and over-estimate for short strings;
    # expect ±25% margin of error. For precise counts, use a tokenizer like
    # tiktoken.
    return len(text) // 4


def count_content_lines(file_path: Path) -> int:
    """Count lines excluding YAML frontmatter."""
    content = file_path.read_text(encoding="utf-8")
    stripped = strip_frontmatter(content)
    return len(stripped.strip().split("\n")) if stripped.strip() else 0


def find_all_rules(repo_root: Path, include_user_rules: bool = False) -> list[Path]:
    """Find all rule files in .claude/rules/.

    If include_user_rules is True, also scan ~/.claude/rules/ for user-level rules.
    """
    rules = []

    claude_rules_dir = repo_root / ".claude" / "rules"
    if claude_rules_dir.exists():
        rules.extend(claude_rules_dir.rglob("*.md"))

    if include_user_rules:
        user_rules_dir = Path.home() / ".claude" / "rules"
        if user_rules_dir.exists():
            rules.extend(user_rules_dir.rglob("*.md"))

    return sorted(rules)


def strip_frontmatter(content: str) -> str:
    """Return content without YAML frontmatter."""
    lines = content.split("\n")
    if not lines or lines[0].strip() != "---":
        return content

    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[i + 1:])

    return content
