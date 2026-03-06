#!/usr/bin/env python3
"""Package a rule for sharing via PR.

Creates a summary README with the rule's purpose and trigger conditions.
"""

import argparse
import json
import sys
from pathlib import Path

from scripts.utils import (
    count_content_lines,
    detect_rule_system,
    estimate_tokens,
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


def package_rule(rule_path: Path, output_dir: Path | None = None) -> dict:
    """Package a rule and return summary info."""
    repo_root = find_repo_root()
    system = detect_rule_system(rule_path)
    frontmatter = parse_rule_frontmatter(rule_path)
    content = rule_path.read_text()
    lines = count_content_lines(rule_path)
    tokens = estimate_tokens(content)

    rel_path = str(rule_path.relative_to(repo_root)) if rule_path.is_relative_to(repo_root) else str(rule_path)

    summary = {
        "file": rel_path,
        "system": system,
        "frontmatter": frontmatter,
        "lines": lines,
        "tokens": tokens,
    }

    # Generate README summary
    readme_lines = [
        f"# Rule: {rel_path}",
        "",
        f"**System:** {system}",
        f"**Lines:** {lines}",
        f"**Tokens:** ~{tokens}",
        "",
    ]

    paths = frontmatter.get("paths", [])
    if isinstance(paths, list) and paths:
        readme_lines.append("**Activates for paths:**")
        for p in paths:
            readme_lines.append(f"- `{p}`")
    else:
        readme_lines.append("**Unconditional** (loaded every conversation)")

    readme_lines.extend(["", "## Content", "", "```markdown"])
    readme_lines.append(strip_frontmatter(content).strip())
    readme_lines.extend(["```", ""])

    summary["readme"] = "\n".join(readme_lines)

    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "README.md").write_text(summary["readme"])
        (output_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
        print(f"Package written to: {output_dir}")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Package a rule for sharing")
    parser.add_argument("rule_path", type=Path, help="Path to the rule file")
    parser.add_argument("--output-dir", "-o", type=Path, default=None,
                        help="Output directory for package (default: print summary)")
    args = parser.parse_args()

    if not args.rule_path.exists():
        print(f"Error: File not found: {args.rule_path}", file=sys.stderr)
        sys.exit(1)

    summary = package_rule(args.rule_path, args.output_dir)

    if not args.output_dir:
        print(summary["readme"])


if __name__ == "__main__":
    main()
