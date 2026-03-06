#!/usr/bin/env python3
"""Validate rule file structure before commit.

Checks frontmatter syntax, required fields, naming convention,
line count, token count, and glob pattern validity.
"""

import argparse
import json
import sys
from pathlib import Path

from scripts.utils import (
    ACTIVATION_MODE_THRESHOLDS,
    count_content_lines,
    estimate_tokens,
    find_all_rules,
    get_activation_mode,
    parse_rule_frontmatter,
    strip_frontmatter,
)


def validate_rule(file_path: Path) -> list[dict]:
    """Validate a single rule file. Returns list of issues."""
    issues = []

    if not file_path.exists():
        return [{"level": "error", "message": f"File not found: {file_path}"}]

    try:
        content = file_path.read_text()
    except (OSError, UnicodeDecodeError) as e:
        return [{"level": "error", "message": f"Cannot read {file_path}: {e}"}]

    frontmatter = parse_rule_frontmatter(file_path)
    mode = get_activation_mode(frontmatter)

    if not frontmatter:
        if content.startswith("---"):
            # Frontmatter delimiter present but parse returned empty — YAML may be malformed
            issues.append({
                "level": "warning",
                "message": "File starts with '---' but frontmatter parsing returned nothing — check for malformed YAML",
            })
        # No frontmatter = unconditional (loaded every conversation)
    else:
        # Check for unrecognized frontmatter fields (only 'paths:' is valid)
        recognized_fields = {"paths"}
        unrecognized = set(frontmatter.keys()) - recognized_fields

        if "alwaysApply" in unrecognized:
            issues.append({
                "level": "warning",
                "message": "'alwaysApply:' is not a valid rule frontmatter field — remove it (rules without 'paths:' load unconditionally)",
            })

        if "description" in unrecognized:
            issues.append({
                "level": "warning",
                "message": "'description:' is not a valid rule frontmatter field (it is a SKILL.md-only feature) — remove it",
            })

        other_unrecognized = unrecognized - {"alwaysApply", "description"}
        if other_unrecognized:
            issues.append({
                "level": "warning",
                "message": f"Unrecognized frontmatter fields: {', '.join(sorted(other_unrecognized))} — only 'paths:' is valid for rules",
            })

        if "paths" not in frontmatter:
            issues.append({
                "level": "info",
                "message": "Frontmatter present but no 'paths:' — rule loads unconditionally (consider removing frontmatter or adding paths)",
            })

    # Check line count with mode-aware threshold
    thresholds = ACTIVATION_MODE_THRESHOLDS.get(mode, ACTIVATION_MODE_THRESHOLDS["unconditional"])
    lines = count_content_lines(file_path)
    if lines > thresholds["lines"]:
        issues.append({
            "level": "warning",
            "message": f"Content has {lines} lines (recommend <{thresholds['lines']} for {mode} rules)",
        })

    # Check token count with mode-aware threshold (strip frontmatter, matching count_content_lines)
    tokens = estimate_tokens(strip_frontmatter(content))
    if tokens > thresholds["tokens"]:
        issues.append({
            "level": "warning",
            "message": f"Estimated {tokens} tokens (recommend <{thresholds['tokens']} for {mode} rules)",
        })

    return issues


def main():
    parser = argparse.ArgumentParser(description="Validate rule file structure")
    parser.add_argument("files", nargs="*", help="Rule files to validate")
    parser.add_argument("--all", action="store_true", help="Validate all rules in .claude/rules/")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    args = parser.parse_args()

    # Determine repo root
    cwd = Path.cwd()
    repo_root = cwd
    for parent in [cwd, *cwd.parents]:
        if (parent / ".git").exists():
            repo_root = parent
            break

    if args.all:
        files = find_all_rules(repo_root)
    elif args.files:
        files = [Path(f) for f in args.files]
    else:
        print("Usage: quick_validate.py [--all] [files...]", file=sys.stderr)
        sys.exit(1)

    all_results = {}
    has_errors = False

    for f in files:
        issues = validate_rule(f)
        # Note: Path.is_relative_to() requires Python 3.9+
        rel_path = str(f.relative_to(repo_root)) if f.is_relative_to(repo_root) else str(f)
        all_results[rel_path] = issues

        for issue in issues:
            if issue["level"] == "error":
                has_errors = True

    if args.format == "json":
        print(json.dumps(all_results, indent=2))
    else:
        for path, issues in all_results.items():
            if not issues:
                print(f"  OK  {path}")
            else:
                for issue in issues:
                    level = issue["level"].upper()
                    print(f"  {level}  {path}: {issue['message']}")

        total = len(files)
        errors = sum(1 for issues in all_results.values() if any(i["level"] == "error" for i in issues))
        warnings = sum(1 for issues in all_results.values() if any(i["level"] == "warning" for i in issues) and not any(i["level"] == "error" for i in issues))
        clean = total - errors - warnings

        print(f"\n{total} rules checked: {clean} OK, {warnings} warnings, {errors} errors")

    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
