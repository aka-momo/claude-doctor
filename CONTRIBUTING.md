# Contributing to claude-doctor

Guidelines for maintaining skills in this plugin as generic, publicly-releasable tools.

## Core Principle

Every skill must work for **any** Claude Code project regardless of language, framework, or organizational structure.

## What to Avoid

### No project-specific content

- No company names, team names, squad names, or organizational references
- No hardcoded directory conventions from any specific project
- No references to specific CI/CD tools, deployment systems, or internal infrastructure
- No assumptions about team structure, code ownership systems, or review processes

### No framework-specific assumptions

- Do not assume the project uses any particular language or framework
- Do not reference framework-specific tooling as if it is universal
- Linters should be referenced generically ("your project's linters") with specific names only as parenthetical examples

### No external CDN dependencies

- HTML assets must be fully self-contained
- Use system font stacks (`system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif`), not hosted fonts
- Do not load JavaScript libraries from CDNs — inline or use simpler alternatives

## Language Diversity in Examples

All examples (documentation, evals, agent prompts, JSON schemas) must represent a **mix of languages**.

- No single language should exceed 60% of all examples across a skill
- Evals must cover at least 3 different languages
- Glob pattern examples should be polyglot (e.g., `src/**/*.ts`, `lib/**/*.py`, `app/**/*.rb`)
- When showing a file path example, rotate through TypeScript, Python, Ruby, Go, and others

## Accuracy

- All claims about Claude Code behavior must match the official documentation at https://code.claude.com/docs
- Do not invent specific numbers or limits unless they come from official docs — use qualitative guidance instead
- When referencing official recommendations, note the source

## Review Checklist

Before any release, verify each skill against these criteria:

1. **No project-specific terms** — No company names, team names, or internal tooling paths
2. **No external CDNs** — HTML files must not load fonts, scripts, or stylesheets from external URLs
3. **No custom fonts** — Use system font stacks only
4. **Language diversity** — Scan `.md` and `.json` files for file extension references and confirm no single language dominates
5. **Accuracy** — Cross-reference claims against official Claude Code docs

## Adding a New Skill

1. Create a directory under `skills/<skill-name>/`
2. Add a `SKILL.md` with proper frontmatter (`name`, `description`)
3. Follow the same directory conventions as existing skills (scripts in `scripts/`, docs in `references/`, etc.)
4. Update the root `README.md` to list the new skill
5. If the skill has its own contributing guidelines, add them as a section in the skill's `references/` directory
