#!/usr/bin/env python3
"""Audit all project rules for quality, conciseness, and overlap.

Scans .claude/rules/ for rule files and reports token budget, per-rule metrics,
overlap detection, stale globs, and validation.
"""

import argparse
import fnmatch
import html
import io
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from scripts.utils import (
    ACTIVATION_MODE_THRESHOLDS,
    count_content_lines,
    detect_rule_system,
    estimate_tokens,
    find_all_rules,
    get_activation_mode,
    parse_rule_frontmatter,
    strip_frontmatter,
)


def find_repo_root() -> Path:
    """Find repo root by walking up from cwd."""
    cwd = Path.cwd()
    for parent in [cwd, *cwd.parents]:
        if (parent / ".git").exists():
            return parent
    return cwd


def get_git_files(repo_root: Path) -> list[str]:
    """Get list of git-tracked files."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, cwd=repo_root, timeout=30,
        )
        return [f for f in result.stdout.strip().split("\n") if f]
    except subprocess.TimeoutExpired:
        print("Warning: git ls-files timed out", file=sys.stderr)
        return []
    except FileNotFoundError:
        print("Warning: git executable not found", file=sys.stderr)
        return []


def extract_keywords(text: str) -> set[str]:
    """Extract meaningful keywords from rule content."""
    # Strip frontmatter and code blocks
    text = strip_frontmatter(text)
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)

    words = re.findall(r"[a-z_]{4,}", text.lower())
    # Filter common words
    stop_words = {
        "that", "this", "with", "from", "have", "will", "been", "they",
        "when", "what", "should", "would", "could", "each", "which",
        "their", "other", "about", "more", "into", "some", "than",
        "only", "also", "make", "like", "then", "just", "over",
        "such", "most", "very", "after", "before", "between", "under",
        "using", "used", "uses", "file", "files", "code", "rule",
        "rules", "example", "following", "ensure", "always", "never",
    }
    return set(words) - stop_words


def calculate_overlap(keywords_a: set[str], keywords_b: set[str]) -> float:
    """Calculate Jaccard similarity between two keyword sets."""
    if not keywords_a or not keywords_b:
        return 0.0
    intersection = keywords_a & keywords_b
    union = keywords_a | keywords_b
    return len(intersection) / len(union)


def check_stale_globs(frontmatter: dict, git_files: list[str]) -> list[str]:
    """Check if glob patterns match any git-tracked files."""

    stale = []
    globs_value = frontmatter.get("globs") or frontmatter.get("glob") or ""

    if isinstance(globs_value, str):
        globs = [g.strip() for g in globs_value.split(",") if g.strip()]
    elif isinstance(globs_value, list):
        globs = globs_value
    else:
        return []

    for glob_pattern in globs:
        matched = any(fnmatch.fnmatch(f, glob_pattern) for f in git_files)
        if not matched:
            stale.append(glob_pattern)

    return stale


def audit_rules(repo_root: Path, include_user_rules: bool = False) -> dict:
    """Run full audit and return report."""
    rules = find_all_rules(repo_root, include_user_rules=include_user_rules)
    git_files = get_git_files(repo_root)

    report = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_rules": len(rules),
        "total_tokens": 0,
        "total_lines": 0,
        "unconditional_tokens": 0,
        "activation_modes": {},
        "rules": [],
        "overlaps": [],
        "stale_globs": [],
        "issues": [],
    }

    rule_keywords = {}

    for rule_path in rules:
        try:
            content = rule_path.read_text()
        except (OSError, UnicodeDecodeError) as e:
            report["issues"].append(f"Cannot read {rule_path}: {e}")
            continue

        try:
            rel_path = str(rule_path.relative_to(repo_root))
        except ValueError:
            rel_path = str(rule_path)
        system = detect_rule_system(rule_path)
        lines = count_content_lines(rule_path)
        tokens = estimate_tokens(content)
        frontmatter = parse_rule_frontmatter(rule_path)
        mode = get_activation_mode(frontmatter)

        # Track activation mode counts and tokens
        report["activation_modes"].setdefault(mode, {"count": 0, "tokens": 0})
        report["activation_modes"][mode]["count"] += 1
        report["activation_modes"][mode]["tokens"] += tokens

        if mode == "unconditional":
            report["unconditional_tokens"] += tokens

        issues = []

        # Check for stale path globs
        paths_value = frontmatter.get("paths", [])
        if isinstance(paths_value, list) and paths_value:
            stale = check_stale_globs({"globs": paths_value}, git_files)
            for s in stale:
                report["stale_globs"].append({"file": rel_path, "glob": s})
                issues.append(f"Stale path pattern: '{s}' matches no files")

        # Check for unrecognized frontmatter fields
        recognized_fields = {"paths"}
        unrecognized = set(frontmatter.keys()) - recognized_fields
        if unrecognized:
            issues.append(f"Unrecognized frontmatter fields: {', '.join(sorted(unrecognized))} — only 'paths:' is valid for rules")

        # Mode-aware size thresholds
        t = ACTIVATION_MODE_THRESHOLDS.get(mode, ACTIVATION_MODE_THRESHOLDS["unconditional"])
        line_threshold, token_threshold = t["lines"], t["tokens"]

        if lines > line_threshold:
            issues.append(f"Long rule: {lines} lines (recommend <{line_threshold} for {mode})")

        if tokens > token_threshold:
            issues.append(f"High token count: {tokens} (recommend <{token_threshold} for {mode})")

        report["rules"].append({
            "file": rel_path,
            "system": system,
            "activation_mode": mode,
            "lines": lines,
            "tokens": tokens,
            "issues": issues,
        })

        report["total_tokens"] += tokens
        report["total_lines"] += lines
        report["issues"].extend(f"{rel_path}: {i}" for i in issues)

        rule_keywords[rel_path] = extract_keywords(content)

    # Check for overlaps
    rule_paths = list(rule_keywords.keys())
    for i in range(len(rule_paths)):
        for j in range(i + 1, len(rule_paths)):
            path_a = rule_paths[i]
            path_b = rule_paths[j]
            similarity = calculate_overlap(rule_keywords[path_a], rule_keywords[path_b])
            if similarity > 0.3:
                shared = sorted(rule_keywords[path_a] & rule_keywords[path_b])[:10]
                report["overlaps"].append({
                    "rule_a": path_a,
                    "rule_b": path_b,
                    "shared_keywords": shared,
                    "similarity": round(similarity, 2),
                })

    return report


def print_text_report(report: dict) -> None:
    """Print human-readable text report."""
    print(f"Rule Audit Report")
    print(f"{'=' * 70}")
    print(f"Total rules: {report['total_rules']}")
    print(f"Total tokens: {report['total_tokens']} (~{report['total_tokens'] * 4} chars)")
    print(f"Unconditional tokens: {report.get('unconditional_tokens', 0)} (keep minimal — loaded every conversation)")
    print(f"Total content lines: {report['total_lines']}")
    print()

    # Activation mode summary
    modes = report.get("activation_modes", {})
    if modes:
        print(f"Activation Mode Breakdown:")
        print(f"{'-' * 50}")
        for mode, data in sorted(modes.items()):
            print(f"  {mode:<20} {data['count']:>3} rules  {data['tokens']:>6} tokens")
        print()

    # Per-rule table
    print(f"{'File':<45} {'Mode':<16} {'Lines':>5} {'Tokens':>6} {'Issues':>6}")
    print(f"{'-' * 45} {'-' * 16} {'-' * 5} {'-' * 6} {'-' * 6}")
    for rule in report["rules"]:
        issues_count = len(rule["issues"])
        marker = " *" if issues_count > 0 else ""
        mode = rule.get("activation_mode", "unknown")
        print(f"{rule['file']:<45} {mode:<16} {rule['lines']:>5} {rule['tokens']:>6} {issues_count:>6}{marker}")

    # Overlaps
    if report["overlaps"]:
        print(f"\nOverlapping Rules (similarity > 0.3):")
        print(f"{'-' * 60}")
        for overlap in report["overlaps"]:
            print(f"  {overlap['rule_a']}")
            print(f"  {overlap['rule_b']}")
            print(f"  Similarity: {overlap['similarity']:.0%}, Shared: {', '.join(overlap['shared_keywords'][:5])}")
            print()

    # Stale globs
    if report["stale_globs"]:
        print(f"\nStale Glob Patterns (match no files):")
        print(f"{'-' * 60}")
        for stale in report["stale_globs"]:
            print(f"  {stale['file']}: '{stale['glob']}'")

    # Issues summary
    if report["issues"]:
        print(f"\nIssues ({len(report['issues'])}):")
        print(f"{'-' * 60}")
        for issue in report["issues"]:
            print(f"  {issue}")


def main():
    parser = argparse.ArgumentParser(description="Audit all project rules")
    parser.add_argument("--format", choices=["text", "json", "html"], default="text",
                        help="Output format (default: text)")
    parser.add_argument("--output", "-o", type=Path, default=None,
                        help="Output file (default: stdout)")
    parser.add_argument("--include-user-rules", action="store_true",
                        help="Also scan ~/.claude/rules/ for user-level rules")
    args = parser.parse_args()

    repo_root = find_repo_root()
    report = audit_rules(repo_root, include_user_rules=args.include_user_rules)

    if args.format == "json":
        output = json.dumps(report, indent=2)
        if args.output:
            args.output.write_text(output)
            print(f"Report written to {args.output}", file=sys.stderr)
        else:
            print(output)
    elif args.format == "html":
        # Generate simple HTML report
        html_out = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Rule Audit Report</title>
<style>body{{font-family:sans-serif;max-width:1000px;margin:0 auto;padding:20px}}
table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:8px;text-align:left}}
th{{background:#333;color:white}}.warn{{color:#d97706}}.error{{color:#c44}}</style></head>
<body><h1>Rule Audit Report</h1>
<p>Total rules: {report['total_rules']} | Total tokens: {report['total_tokens']} | Unconditional tokens: {report.get('unconditional_tokens', 0)} | Lines: {report['total_lines']}</p>
<table><thead><tr><th>File</th><th>Mode</th><th>Lines</th><th>Tokens</th><th>Issues</th></tr></thead><tbody>"""
        for rule in report["rules"]:
            issues_html = "<br>".join(html.escape(i) for i in rule["issues"]) if rule["issues"] else "OK"
            cls = "error" if rule["issues"] else ""
            mode = html.escape(rule.get("activation_mode", "unknown"))
            html_out += f"<tr><td>{html.escape(rule['file'])}</td><td>{mode}</td><td>{rule['lines']}</td><td>{rule['tokens']}</td><td class='{cls}'>{issues_html}</td></tr>"
        html_out += "</tbody></table></body></html>"
        if args.output:
            args.output.write_text(html_out)
            print(f"Report written to {args.output}", file=sys.stderr)
        else:
            print(html_out)
    else:
        if args.output:
            buf = io.StringIO()
            old_stdout = sys.stdout
            sys.stdout = buf
            print_text_report(report)
            sys.stdout = old_stdout
            args.output.write_text(buf.getvalue())
            print(f"Report written to {args.output}", file=sys.stderr)
        else:
            print_text_report(report)


if __name__ == "__main__":
    main()
