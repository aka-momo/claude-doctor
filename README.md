# claude-doctor

A Claude Code plugin for project health — currently includes rule creation, auditing, and validation skills, with more to come.

## Skills

### rule-creator

Handles the full lifecycle of Claude Code project rules (`.claude/rules/*.md`):

- **Create** rules with proper frontmatter and structure
- **Validate** rule files for correctness
- **Audit** all rules for quality, conciseness, and overlap
- **Test** rule effectiveness via eval cases
- **Improve** rules based on eval results
- **Package** rules for sharing

## Installation

### From GitHub (recommended)

```
/plugin marketplace add aka-momo/claude-doctor
/plugin install claude-doctor@claude-doctor
```

### Manual installation

Clone this repo and copy the skills you want into your Claude Code skills directory:

```bash
git clone https://github.com/aka-momo/claude-doctor.git
cp -r claude-doctor/skills/rule-creator ~/.claude/skills/
```

## Usage

Once installed, the rule-creator skill triggers automatically when you ask Claude Code to:

- `"create a rule for..."`
- `"audit my rules"`
- `"improve this rule"`
- `"delete/remove a rule"`
- `"this rule isn't working"`
- Or any reference to `.claude/rules/` and project coding standards

### Examples

**Create a new rule:**
```
Create a rule that enforces snake_case for all Python function names in src/
```

**Audit existing rules:**
```
Audit my project rules for overlap and quality issues
```

**Improve a rule:**
```
This error-handling rule isn't triggering when I edit Python files - can you fix it?
```

## Rule activation modes

Rules support two activation modes per the official Claude Code docs:

| Mode | Frontmatter | When to use |
|------|------------|-------------|
| **Unconditional** | None | Rules Claude must always follow |
| **Path-scoped** | `paths: ["src/**/*.py"]` | Rules for specific file types |

## Project structure

```
claude-doctor/
├── .claude-plugin/
│   ├── plugin.json          # Plugin metadata
│   └── marketplace.json     # Marketplace definition
├── skills/
│   └── rule-creator/        # Rule lifecycle skill
│       ├── SKILL.md
│       ├── scripts/
│       ├── references/
│       ├── agents/
│       ├── evals/
│       ├── eval-viewer/
│       └── assets/
├── CONTRIBUTING.md
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

## Requirements

- [Claude Code](https://claude.ai/code) CLI
- Python 3.9+ (for scripts)
- macOS or Linux (scripts use Unix-specific APIs)
- Python dependencies: `pip install -r requirements.txt`

The eval/optimization scripts also require the `claude` CLI to be on your PATH.

## License

MIT
