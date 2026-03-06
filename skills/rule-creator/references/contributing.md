# Rule Creator Contributing Notes

Skill-specific guidelines beyond the root CONTRIBUTING.md.

## Scope

This skill targets `.claude/rules/` exclusively — the native Claude Code rule system. Do not document or reference alternative rule systems, rule distribution tools, or multi-tool rule infrastructure.

## Hardcoded (OK)

- `.claude/rules/` as the rule directory — this is a Claude Code standard
- Frontmatter keys: `paths:` — the only valid rule frontmatter field
- Script names within the skill itself (e.g., `scripts/quick_validate.py`)

## Should Not Be Hardcoded

- File exclusion patterns — do not hardcode specific filenames to skip

## Language Examples

These files contain language-specific examples and must stay balanced:

| File | What to check |
|------|--------------|
| `SKILL.md` | Frontmatter glob examples, negative test examples |
| `references/best-practices.md` | Path targeting examples |
| `references/schemas.md` | JSON schema examples (file paths, rule names, eval names) |
| `agents/grader.md` | Output format example expectations |
| `agents/analyzer.md` | Example notes and analysis patterns |

## Script Architecture

- `utils.py` — Shared utilities (frontmatter parsing, rule discovery, token estimation)
- `quick_validate.py` — Validates rule structure and frontmatter
- `audit_rules.py` — Audits all rules for quality, overlap, and stale patterns
- `package_rule.py` — Packages a rule for sharing via PR
- `aggregate_benchmark.py` — Aggregates eval benchmark results
- `generate_report.py` — Generates HTML report from optimization history
- `run_eval.py` / `run_loop.py` — Description optimization eval pipeline
- `improve_description.py` — Improves skill description based on eval results

## Adding Evals

When adding evals to `evals/evals.json`:

1. Vary the language — don't add another eval in a language that already has 2+ cases
2. Use generic file paths — `src/`, `lib/`, `internal/`, `tests/` are universal
3. Avoid domain-specific model names that imply a particular business
4. Include both positive and negative test cases
5. Test path scoping: a rule for `src/api/` should not activate for `src/utils/`
