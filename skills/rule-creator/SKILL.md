---
name: rule-creator
description: >
  Create, maintain, audit, remove, improve, and optimize Claude Code project rules (.md files in .claude/rules/).
  Trigger for: "create a rule", "add a coding standard as a Claude rule", "audit my rules", "delete/remove a rule",
  "this rule isn't working", "improve a rule", "optimize this rule", or references to .claude/rules/ and project coding standards.
  Do NOT trigger for creating skills (use skill-creator), editing CLAUDE.md directly, or general code review without rule context.
---

# Rule Creator

A skill for creating, maintaining, and evaluating Claude Code project rules.

## Overview

This skill handles the full lifecycle of project rules:
- **Create** new rules with proper frontmatter and structure
- **Validate** rule files for correctness
- **Audit** all rules for quality, conciseness, and overlap
- **Test** rule effectiveness via eval cases
- **Improve** rules based on eval results
- **Package** rules for sharing via PR

## Rule Frontmatter

Rules live in `.claude/rules/` (native to Claude Code). Frontmatter is optional and controls when a rule activates. The only valid frontmatter field is `paths:`.

### Unconditional rules (no frontmatter)

Rules without frontmatter are loaded at the start of every conversation, with the same priority as `.claude/CLAUDE.md`. Use sparingly — they consume context budget on every query. Keep them short.

### Path-targeted rules
```yaml
---
paths:
  - "lib/**/*.py"
  - "src/**/*.ts"
---
```
The rule activates only when Claude reads files matching the glob patterns (not on every tool use). This is where most rules should live — they only cost context when relevant. Brace expansion is supported (e.g., `"src/**/*.{ts,tsx}"`).

### Choosing the right mode

1. **Applies to specific file types/paths?** → Add `paths:` frontmatter
2. **Must Claude always follow this regardless of files?** → No frontmatter (unconditional)
3. **Not sure?** → Start with `paths:` targeting and broaden to unconditional if needed

> **Note:** `alwaysApply:` and `description:` are **not** valid frontmatter fields for `.claude/rules/` files. These fields are for skills (`SKILL.md`), not rules. If you encounter them in a rule file, remove them — use no frontmatter for unconditional rules, or `paths:` for scoped rules.

## User-Level and Shared Rules

- **`~/.claude/rules/`** — Personal rules applied to every project (e.g., communication preferences, editor style)
- **`.claude/rules/`** — Project rules shared via git (team conventions, project-specific patterns)
- **Symlinks** — Symlink files into `.claude/rules/` to share rules across projects without duplication
- **`@path/to/file`** — Use import syntax in CLAUDE.md to reference larger docs instead of inlining them

## Core Workflow

All script commands below are run from the repository root and `cd` into the skill directory as needed.

### Phase 1: Capture Intent

Understand what the user wants the rule to enforce:
1. What behavior should Claude follow (or avoid)?
2. Which files does this apply to? (path patterns)
3. Is this Claude-specific or a universal standard?
4. Are there examples of the correct vs incorrect behavior?

### Phase 2: Interview & Research

- Check existing rules for overlap (run `cd .claude/skills/rule-creator && python3 -m scripts.audit_rules`)
- Read existing rules in the same path scope to check for semantic contradictions (the audit script catches keyword overlap but not conflicting directives)
- Check CLAUDE.md for conflicting directives — rules and CLAUDE.md are both loaded, and contradictions cause unpredictable behavior
- Read `references/best-practices.md` for writing guidelines
- If the rule targets a specific codebase area, read existing files to understand conventions
- If the user wants deterministic enforcement (e.g., "never allow X"), suggest a hook instead of a rule — rules are advisory, hooks are hard gates
- If the user's need involves a multi-step workflow with scripts or agents, suggest using skill-creator instead — rules are for directives, skills are for workflows
- Consider `@path/to/file` import syntax in CLAUDE.md as an alternative to duplicating large content into a rule

### Proactive Warnings

When you encounter anti-patterns — whether in an existing rule you're fixing, a user request that would create one, or during an audit — **always explain the problem to the user before fixing it**. Don't silently correct issues. The user needs to understand *why* something is wrong so they can avoid repeating it. Key anti-patterns to flag:

- Unrecognized frontmatter fields (e.g., `alwaysApply`, `description`) — not valid for `.claude/rules/` files
- Unconditional 100+ line rule → context bloat on every conversation
- Rules that duplicate linter/CI checks → wasted tokens on already-enforced standards
- Multiple overlapping rules → consolidate to reduce context cost
- Rules contradicting CLAUDE.md directives → unpredictable behavior

A one-sentence explanation is enough — e.g., "This rule has `alwaysApply: true` in frontmatter, but that's not a valid field for rules — I'll remove the frontmatter so it loads unconditionally."

### Phase 3: Write the Rule

Follow these principles from `references/best-practices.md`:
- **Lead with the action**: "Use X when Y"
- **Give concrete examples**: one good example beats three paragraphs
- **Explain the why**: Claude follows reasoned instructions better than mandates
- **Stay concise**: unconditional rules should be kept minimal since every conversation pays the cost. Path-targeted rules have more room since they only load when relevant
- **Don't duplicate linters**: trust your project's linters
- **Naming**: use kebab-case for rule filenames (e.g., `error-handling.md`, `import-ordering.md`). If a rule already exists for the topic, prefer updating it over creating a new one.

### Phase 4: Validate

Run validation:
```bash
cd .claude/skills/rule-creator && python3 -m scripts.quick_validate <rule-file>
```

Note: Frontmatter is optional for `.claude/rules/` files.

### Phase 5: Test (Optional)

For important rules, create eval cases and run the evaluation pipeline. See "Running and Evaluating Test Cases" below.

### Phase 6: Iterate

Review the rule, check for overlap with existing rules, and iterate based on feedback.

## Running and Evaluating Test Cases

This follows a 5-step process:

Put results in `.claude/skills/rule-creator-workspace/` (a sibling to the skill directory). Organize by iteration (`iteration-1/`, `iteration-2/`, etc.).

### Step 1: Spawn runs (with_rule AND baseline)

For each test case, use the Agent tool to spawn two subagents. **Important: run them sequentially, not in parallel.** The baseline agent temporarily removes the rule file, which would corrupt the with-rule run if both ran simultaneously. Run the with-rule agent first, then the baseline:

**With-rule run:** Execute the task with the rule active. The rule is already in place in `.claude/rules/`. Save to `with_rule/outputs/`.

**Baseline run (without_rule):** After the with-rule run completes, back up the rule file (`cp rule.md rule.md.bak`), remove it, execute the same task, then restore it (`mv rule.md.bak rule.md`). Save to `without_rule/outputs/`.

Write `eval_metadata.json` for each test case with the prompt and expectations.

### Step 2: Draft expectations

Good expectations for rules:
- "Claude follows the rule's directive without being explicitly asked"
- "The rule does NOT activate for unrelated file types" (negative test)
- "The rule doesn't cause unwanted side effects on the output"

### Step 3: Capture timing data

When each subagent completes, save `timing.json` with `total_tokens`, `duration_ms`, and `total_duration_seconds`.

### Step 4: Grade, aggregate, and launch the viewer

1. **Grade each run** — use `agents/grader.md`. Save to `grading.json` with `text`, `passed`, `evidence` fields.
2. **Aggregate**:
   ```bash
   cd .claude/skills/rule-creator && python3 -m scripts.aggregate_benchmark <workspace>/iteration-N --rule-name <rule-name>
   ```
3. **Analyze** — read benchmark data and surface patterns per `agents/analyzer.md`.
4. **Launch viewer**:
   ```bash
   cd .claude/skills/rule-creator && nohup python3 eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --rule-name "<rule-name>" \
     --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   VIEWER_PID=$!
   ```
   For iteration 2+, add `--previous-workspace <workspace>/iteration-<N-1>` to show diffs.

### Step 5: Read feedback and iterate

Read `feedback.json` from the workspace. Empty feedback for a run means it looked fine. Kill the viewer when done:
```bash
kill $VIEWER_PID 2>/dev/null
```
Improve the rule based on feedback, rerun into `iteration-<N+1>/`.

## Improving Rules

When improving a rule based on eval results, think carefully — rules get applied across many conversations, so small improvements compound.

1. **Generalize from the feedback.** The user is iterating on a few examples, but the rule will be used thousands of times across many prompts. Rather than adding fiddly fixes for specific test cases, try to understand *why* the model failed and address the underlying cause. If you find yourself writing heavy-handed MUSTs, step back and explain the reasoning instead — Claude follows reasoned instructions better than arbitrary mandates.

2. **Keep the rule lean.** Read the eval transcripts, not just outputs. If the rule is making the model waste time on unproductive steps, cut those parts. Every token in a rule competes for context budget across all conversations. A 50-token rule that achieves 80% of the effect is often better than a 200-token rule at 90%.

3. **Check for over-application.** Rules can bleed into unrelated contexts in ways skills don't. Does the rule cause unwanted changes to files outside its intended scope? Does it activate for file types it shouldn't? Path targeting (`paths:` globs) is your main defense.

4. **Look for repeated work across test cases.** Read the transcripts and notice if the subagents all independently took the same multi-step approach. If all test runs show the same pattern, that's a signal the rule should address it more directly.

5. **Test negative cases.** Ensure the rule doesn't trigger where it shouldn't. A rule for Python files should not affect TypeScript. A rule for frontend components should not affect backend handlers.

6. **Always explain what you changed and why.** When fixing anti-patterns or improving rules, tell the user what the problem was and how your change addresses it. Silent fixes leave users unable to learn from the issue or catch it themselves next time.

## Removing Rules

Before deleting a rule, check whether other rules reference it (e.g., via `references/` pointers or overlap notes). Confirm deletion with the user. If the rule was unconditional (no frontmatter), note that removing it saves context budget on every future conversation.

## Rule Auditing

Run a full audit of all project rules (from the repository root):
```bash
cd .claude/skills/rule-creator && python3 -m scripts.audit_rules
```

This reports:
- Token budget broken down by activation mode (`unconditional`, `path_targeted`)
- Per-rule token and line counts with activation mode column
- Overlap detection between rules
- Stale glob patterns (matching no files)
- Frontmatter validation issues (including unrecognized fields)

**Budget guidance:** Keep unconditional rules as small as possible — they consume context on every conversation. Path-targeted rules only cost tokens when activated, so they're cheaper. If the audit shows high unconditional totals, convert rules to `paths:` targeting.

Use `--include-user-rules` to also scan `~/.claude/rules/` for user-level rules.

## Claude.ai-Specific Instructions

In Claude.ai (no subagents, no `claude -p`):
- Execute each test task within the conversation with the rule's directives in mind. Compare the output against eval expectations manually.
- Skip baseline runs — without subagents, the comparison isn't meaningful.
- Present results directly in conversation. For files the user needs to inspect, create them as artifacts or describe the contents inline.
- Ask for feedback inline: "How does this look? Anything you'd change?"
- Skip description optimization and blind comparison (both require CLI).

## Cowork-Specific Instructions

- Subagents work, so the main workflow (spawn runs, grade evals) all works. Remember that with-rule and baseline runs must be sequential (the baseline temporarily removes the rule file), but grading multiple evals can be parallel. If timeouts are an issue, run test prompts in series.
- You don't have a browser, so use `--static <output_path>` for the eval viewer instead of starting a server.
- Generate the eval viewer before evaluating results yourself. This lets the human review outputs in parallel while you analyze, saving wall-clock time.
- Feedback works differently: the viewer's "Submit All Reviews" downloads `feedback.json` as a file.
- Description optimization should work since it uses `claude -p` via subprocess.

## Communicating with the User

Pay attention to context cues about the user's technical level. Some users creating rules are deeply technical; others may be less familiar with coding jargon. In the default case:
- "evaluation" and "benchmark" are fine to use
- For "JSON", "expectation", or "frontmatter", briefly explain if you're not sure the user knows the term
- Match the user's communication style — if they're casual, be casual back

## The Core Loop

Follow the Core Workflow phases (above) in order. Three steps that matter most:

1. **Generate the eval viewer early** — the human can review outputs in parallel while you analyze, cutting wall-clock time significantly.
2. **Run baselines** (with_rule AND without_rule) unless in Claude.ai — without a baseline, you cannot tell whether the rule actually changed behavior or the model would have done the same thing anyway.
3. **Iterate on feedback** until the user is satisfied — rules affect every future conversation, so incremental refinement has compounding value.

Add these to your TodoList (if you have one). If in Cowork, specifically add "Generate eval viewer so human can review test cases."

## Reference Files

**Agents** (read when spawning subagents):
- `agents/grader.md` — Evaluate expectations against outputs
- `agents/comparator.md` — Blind A/B comparison
- `agents/analyzer.md` — Post-hoc analysis and benchmark patterns

**References** (read for context):
- `references/best-practices.md` — Rule writing guidelines
- `references/schemas.md` — JSON schemas for all data structures
- `references/advanced-workflows.md` — Description optimization and blind comparison workflows

**Scripts** (execute directly):
- `scripts/quick_validate.py` — Validate rule structure
- `scripts/audit_rules.py` — Audit all rules for quality
- `scripts/run_eval.py` — Test trigger accuracy for skill description
- `scripts/improve_description.py` — Improve skill description based on eval results
- `scripts/run_loop.py` — Eval + improve iteration loop
- `scripts/aggregate_benchmark.py` — Aggregate benchmark results
- `scripts/generate_report.py` — HTML report from optimization
- `scripts/package_rule.py` — Package rule for sharing/PR
