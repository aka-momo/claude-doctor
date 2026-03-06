# Claude Rules Best Practices

Guidelines for writing effective Claude Code rules, based on Anthropic documentation and community experience.

## Conciseness Guidelines

These are recommended targets, not hard limits. Shorter rules get better adherence because they compete with the user's actual task for context window space.

| Scope | Guidance | Notes |
|-------|----------|-------|
| CLAUDE.md (root) | <200 lines | Official recommendation from Anthropic. Use `@path/to/file` imports for larger content |
| Unconditional rule (no frontmatter) | Keep short | Every query pays the cost — the shorter the better |
| `paths:` targeted rule | More room | Only loads for matching files, so less pressure to minimize |
| Unconditional rules total | Minimize | Every unconditional rule taxes every conversation |

Rules are injected into conversation context. Every extra line competes with the user's actual task for context window space. The official docs note that "longer files consume more context and reduce adherence."

## Progressive Disclosure

Structure rules in layers so Claude only loads what it needs:

1. **Unconditional** (no frontmatter) — Only critical, universal rules. Keep as short as possible.
2. **Path-targeted** (`paths:` globs) — Loaded when Claude reads matching files. Most rules should live here.
3. **Referenced docs** — Larger guides linked from rules via `@path/to/file`, read on demand.

## Choosing the Right Activation Mode

Use this decision tree:

1. **Does it apply to specific file types/paths?** (e.g., React patterns, Ruby conventions) → `paths:` globs
2. **Must Claude always follow this regardless of files?** (e.g., commit message format, security rules) → No frontmatter (unconditional)
3. **Not sure yet?** → Start with `paths:` targeting and broaden to unconditional if needed

> **Note:** The only valid frontmatter field for `.claude/rules/` files is `paths:`. Fields like `description:` and `alwaysApply:` belong to skills (`SKILL.md`), not rules. If you encounter them in a rule file, remove them — use no frontmatter for unconditional rules, or `paths:` for scoped rules.

## Path Targeting

Use `paths:` frontmatter to scope rules to relevant files:

```yaml
---
paths:
  - "src/components/**/*.tsx"
  - "lib/**/*.py"
---
```

Prefer specific globs over `**/*`. A rule that only applies to React components should not be loaded when editing Ruby files. Path-scoped rules trigger when Claude **reads** files matching the pattern, not on every tool use. Brace expansion is supported (e.g., `"src/**/*.{ts,tsx}"`).

## Emphasis for Critical Rules

When a directive is genuinely critical, use emphasis sparingly:

- **Bold** for important terms inline
- `IMPORTANT:` prefix for must-follow directives (use rarely)
- Explain *why* something matters rather than shouting ALWAYS/NEVER

Over-emphasis causes all emphasis to be ignored.

## Writing Effective Rules

**Do:**
- Lead with the action: "Use X when Y" not "When Y, you should consider using X"
- Give concrete examples — one good example beats three paragraphs of description
- Explain the *why* — Claude follows reasoned instructions better than arbitrary mandates
- Use tables for option comparison, bullet lists for sequential steps
- Test the rule: does Claude follow it without the rule? If yes, you don't need it

**Don't:**
- State what your project's linters already enforce (e.g., Rubocop, ESLint)
- Duplicate information from framework docs Claude already knows
- Contradict other rules — check for conflicts before adding
- Write rules that only apply to one specific task (use SKILL.md instead)
- Add aspirational rules nobody follows — rules should reflect actual practice

## Rules vs Hooks

Rules are **advisory** — Claude follows them as instructions but can deviate. Hooks are **deterministic** — they run shell commands on events (e.g., pre-commit, post-tool-call) and hard-block if they fail.

| Use a Rule when... | Use a Hook when... |
|--------------------|---------------------|
| Guideline or best practice | Hard requirement that must never be violated |
| Context-dependent judgment | Mechanical check (lint, format, test) |
| "Prefer X over Y" | "Block if X is not done" |
| Teaching Claude patterns | Enforcing gates on tool execution |

If the user wants **guaranteed** enforcement (e.g., "never push without tests"), suggest a hook. If they want **guidance** (e.g., "prefer composition over inheritance"), use a rule.

## User-Level vs Project-Level Rules

| Location | Scope | Use for |
|----------|-------|---------|
| `.claude/rules/` | Project, shared via git | Team conventions, project-specific patterns |
| `~/.claude/rules/` | Personal, all projects | Personal preferences (editor style, communication tone) |

User-level rules in `~/.claude/rules/` apply to every project. Use for preferences like "always use concise responses" or "prefer functional style." Don't put project-specific conventions there.

To share rules across projects without duplication, symlink files into `.claude/rules/`.

## Anti-Patterns

| Anti-Pattern | Why It's Bad | Fix |
|-------------|-------------|-----|
| Kitchen-sink CLAUDE.md | Bloats every query | Split into path-targeted rules |
| "Always do X" without why | Claude ignores arbitrary mandates | Explain the reasoning |
| Duplicating linter rules | Wastes tokens on enforced checks | Remove; trust the linter |
| Contradicting rules | Claude picks one randomly | Resolve the conflict |
| Stale glob patterns | Rule loads for wrong files | Audit with `audit_rules.py` |
| Too many unconditional rules | Taxes every conversation | Use `paths:` targeting |
| Using `alwaysApply:` or `description:` in rules | These are skill fields, not valid for rules | Remove; use no frontmatter (unconditional) or `paths:` |
| Conflicting CLAUDE.md and rules | Unclear which instruction wins | Audit for contradictions |

## Rule Lifecycle

1. **Draft** — Write the rule based on a real problem you observed
2. **Validate** — Check structure with `quick_validate.py`
3. **Test** — Run eval cases to verify Claude follows the rule
4. **Audit** — Periodically check token budget with `audit_rules.py`
5. **Prune** — Remove rules that are no longer needed or effective

## When to Use Rules vs Skills vs Hooks

| Use a Rule when... | Use a Skill when... | Use a Hook when... |
|--------------------|---------------------|---------------------|
| Directive applies to many tasks | Workflow is specific and multi-step | Hard gate on tool execution |
| Content is concise (under ~200 lines) | Content needs scripts, templates, agents | Mechanical check (lint, format) |
| Triggered by file type/path/topic | Triggered by user intent/phrase | Triggered by tool call events |
| "Always do X in this context" | "Here's how to do complex task Y" | "Block unless condition Z is met" |
