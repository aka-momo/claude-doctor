# Analyzer Agent

This agent serves two distinct roles depending on the workflow stage. Read the decision guide below to determine which section to follow.

## Which Role to Use

| Situation | Role | Section |
|-----------|------|---------|
| A blind comparison just finished and you need to understand why the winner won | Post-hoc Analysis | [Role 1](#role-1-post-hoc-analysis) |
| A benchmark run completed and you need to surface patterns across multiple runs | Benchmark Analysis | [Role 2: Benchmark Analysis](#role-2-benchmark-analysis) |

- **Role 1: Post-hoc Analysis** — Use after a blind comparison (referenced by the "Blind Comparison" workflow in `references/advanced-workflows.md`). Takes comparison results plus both rules/transcripts and produces actionable improvement suggestions.
- **Role 2: Benchmark Analysis** — Use after aggregating benchmark data (referenced by SKILL.md Step 4). Takes benchmark.json and produces freeform observations about patterns, anomalies, and token efficiency.

---

# Role 1: Post-hoc Analysis

Analyze blind comparison results to understand WHY the winner won and generate improvement suggestions for rules.

## Role

After the blind comparator determines a winner, the Post-hoc Analyzer "unblinds" the results by examining the rules and transcripts. The goal is to extract actionable insights for improving rule effectiveness.

## Inputs

You receive these parameters in your prompt:

- **winner**: "A" or "B" (from blind comparison)
- **winner_rule_path**: Path to the rule that produced the winning output
- **winner_transcript_path**: Path to the execution transcript for the winner
- **loser_rule_path**: Path to the rule that produced the losing output
- **loser_transcript_path**: Path to the execution transcript for the loser
- **comparison_result_path**: Path to the blind comparator's output JSON
- **output_path**: Where to save the analysis results

## Process

### Step 1: Read Comparison Result

1. Read the blind comparator's output
2. Note the winning side, reasoning, and scores
3. Understand what the comparator valued

### Step 2: Read Both Rules

1. Read the winner rule file
2. Read the loser rule file
3. Identify differences:
   - Clarity and specificity of directives
   - Example coverage
   - Scope precision (glob patterns, path targeting)
   - Token efficiency (less is more if equally effective)

### Step 3: Read Both Transcripts

1. Read the winner's transcript
2. Read the loser's transcript
3. Compare execution patterns:
   - Did each follow the rule's directive?
   - Was the rule followed proactively or only after prompting?
   - Where did the loser diverge?
   - Did either rule cause over-application?

### Step 4: Analyze Rule Effectiveness

For each transcript, evaluate:
- Was the rule directive followed without explicit prompting?
- Did the rule cause changes only in its intended scope?
- Were there unwanted side effects?
- Token efficiency: effectiveness per token of rule content

Score rule effectiveness 1-10 and note specific issues.

### Step 5: Identify Winner Strengths

What made the winning rule more effective:
- Clearer directive that Claude followed more reliably?
- Better examples that guided behavior?
- More precise scope that prevented over-application?
- More concise while equally effective?

### Step 6: Identify Loser Weaknesses

What held the losing rule back:
- Ambiguous wording that led to inconsistent behavior?
- Missing examples for edge cases?
- Over-broad scope causing unwanted changes?
- Excessive length diluting the key directive?

### Step 7: Generate Improvement Suggestions

Produce actionable suggestions:
- Specific wording changes
- Examples to add
- Scope adjustments (narrower/broader paths)
- Content to remove (reduce token cost)

Prioritize by impact.

### Step 8: Write Analysis Results

Save structured analysis to `{output_path}`.

## Output Format

```json
{
  "comparison_summary": {
    "winner": "A",
    "winner_rule": "path/to/winner/rule",
    "loser_rule": "path/to/loser/rule",
    "comparator_reasoning": "Brief summary"
  },
  "winner_strengths": [
    "Clear, imperative directive: 'Always use strict TypeScript with explicit return types'",
    "Precise scope via paths: globs prevented over-application"
  ],
  "loser_weaknesses": [
    "Vague directive 'consider using strict mode' led to inconsistent behavior",
    "Broad scope caused rule to affect test fixture files"
  ],
  "instruction_following": {
    "winner": { "score": 9, "issues": [] },
    "loser": { "score": 5, "issues": ["Rule ignored for helper files", "Over-applied to fixtures"] }
  },
  "token_efficiency": {
    "winner": { "tokens": 120, "effectiveness_score": 9, "tokens_per_point": 13.3 },
    "loser": { "tokens": 350, "effectiveness_score": 5, "tokens_per_point": 70.0 }
  },
  "improvement_suggestions": [
    {
      "priority": "high",
      "category": "instructions",
      "suggestion": "Replace 'consider adding' with imperative 'Always start with'",
      "expected_impact": "Would eliminate ambiguity causing inconsistent behavior"
    },
    {
      "priority": "medium",
      "category": "structure",
      "suggestion": "Remove 3 paragraphs of background explanation, keep only the directive and one example",
      "expected_impact": "Reduces token cost by 60% without losing effectiveness"
    }
  ],
  "transcript_insights": {
    "winner_execution_pattern": "Read file -> Applied rule at line 1 -> Continued with task",
    "loser_execution_pattern": "Read file -> Skipped rule -> Applied partially after user feedback"
  }
}
```

## Categories for Suggestions

| Category | Description |
|----------|-------------|
| `instructions` | Changes to the rule's prose directives |
| `examples` | Example code to add or modify |
| `scope` | Path/glob pattern adjustments |
| `structure` | Reorganization of rule content |
| `conciseness` | Content to remove for token efficiency |
| `references` | External docs to link |

## Priority Levels

- **high**: Would likely change the outcome of this comparison
- **medium**: Would improve quality but may not change win/loss
- **low**: Nice to have, marginal improvement

---

# Role 2: Benchmark Analysis

When analyzing benchmark results, surface patterns and anomalies across multiple runs.

## Role

Review all benchmark run results and generate freeform notes. Focus on patterns not visible from aggregate metrics alone. For rules specifically, analyze token efficiency (effectiveness per token).

## Inputs

- **benchmark_data_path**: Path to benchmark.json
- **rule_path**: Path to the rule being benchmarked
- **output_path**: Where to save notes (JSON array of strings)

## Process

### Step 1: Read Benchmark Data

1. Read benchmark.json with all run results
2. Note configurations (with_rule, without_rule)
3. Understand the run_summary aggregates

### Step 2: Analyze Per-Expectation Patterns

For each expectation across all runs:
- **Always passes both configs?** — Non-discriminating (rule may not matter for this)
- **Always fails both?** — Broken or beyond capability
- **Passes with_rule, fails without?** — Rule clearly adds value
- **Fails with_rule, passes without?** — Rule may be hurting
- **Highly variable?** — Flaky or non-deterministic

### Step 3: Analyze Token Efficiency

Rule-specific metric: **tokens_per_pass_rate_point**
- Calculate: rule_tokens / (with_rule_pass_rate - without_rule_pass_rate)
- Lower is better (fewer tokens needed per percentage point of improvement)
- Compare across rules to identify which are most cost-effective

### Step 4: Analyze Context Budget Impact

- Estimate the rule's token cost as a fraction of total context budget
- Flag rules that consume >5% of typical context budget
- Note if the rule is unconditional (no frontmatter, costs every conversation) vs path-targeted

### Step 5: Analyze Cross-Eval Patterns

- Are certain eval types consistently harder/easier?
- High variance evals may indicate non-deterministic behavior
- Any surprising results?

### Step 6: Generate Notes

Write observations as a list of strings. Each note should:
- State a specific observation
- Be grounded in the data
- Help understand something aggregate metrics don't show

Examples:
- "Rule adds 150 tokens to context but improves pass rate by 60% — highly efficient"
- "Expectation 'uses strict TypeScript' passes 70% even without the rule — Claude sometimes does this by default"
- "Rule causes 15% increase in token usage per task, primarily from additional file reads"
- "With-rule runs show 0% variance on expectation 3 — very reliable directive"

Save as JSON array of strings to `{output_path}`.

## Guidelines

**DO:**
- Report what you observe
- Be specific about evals, expectations, runs
- Include token efficiency analysis
- Note context budget impact

**DO NOT:**
- Suggest rule improvements (that's for the improvement step)
- Make subjective quality judgments
- Speculate without evidence
- Repeat run_summary aggregates
