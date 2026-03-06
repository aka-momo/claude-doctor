# Advanced Workflows

## Description Optimization

For optimizing the rule-creator's own skill description for better triggering accuracy. The `description` field in SKILL.md frontmatter determines when Claude invokes the skill.

### How triggering works

Skills appear in Claude's `available_skills` list with their name + description. Claude decides whether to consult a skill based on that description. Claude only consults skills for tasks it can't easily handle on its own — simple queries may not trigger even if the description matches. Complex, multi-step, or specialized queries reliably trigger when the description matches.

### Step 1: Generate eval queries
Create 20 queries (10 should-trigger, 10 should-not-trigger). Make them realistic — include file paths, personal context, casual speech, typos. Focus on edge cases, not obvious matches. Save as JSON array.

### Step 2: Review with user
Use `assets/eval_review.html` template — this is an interactive HTML template for reviewing and editing eval queries. Replace `__EVAL_DATA_PLACEHOLDER__`, `__RULE_NAME_PLACEHOLDER__`, and `__RULE_DESCRIPTION_PLACEHOLDER__`, then open in browser.

### Step 3: Run optimization loop
```bash
cd .claude/skills/rule-creator && python3 -m scripts.run_loop \
  --eval-set <path-to-eval.json> \
  --rule-path . \
  --model <model-id> \
  --max-iterations 5 \
  --verbose
```

### Step 4: Apply the best description
Take `best_description` from the JSON output and update SKILL.md frontmatter. Show the user before/after and report scores.

## Blind Comparison

For rigorous comparison between two rule versions:

### Process

1. **Prepare two rule versions** — save each as `version-A/` and `version-B/` directories
2. **Run the same eval prompts** with each version, capturing outputs separately
3. **Give both outputs to the comparator agent** (read `agents/comparator.md` for instructions) without revealing which version produced which output
4. **Analyze the results** — use the analyzer agent (read `agents/analyzer.md`, Role 1: Post-hoc Analysis) to understand why the winner won and extract actionable improvements

### Key files

- `agents/comparator.md` — blind A/B comparison
- `agents/analyzer.md` — post-hoc analysis

### Additional comparison dimensions for rules

- **Conciseness**: Is one version more concise while equally effective?
- **Over-application**: Does one version bleed into unrelated contexts?
- **Token efficiency**: Effectiveness per token spent
