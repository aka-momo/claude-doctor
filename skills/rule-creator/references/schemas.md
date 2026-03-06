# JSON Schemas

This document defines the JSON schemas used by rule-creator.

---

## evals.json (Content Quality Evals)

Defines content quality evals for a rule. Used by the grader agent to evaluate rule effectiveness. Located at `evals/evals.json` within the skill directory.

```json
{
  "rule_name": "example-rule",
  "rule_file": ".claude/rules/example.md",
  "evals": [
    {
      "id": 1,
      "prompt": "User's example prompt",
      "expected_output": "Description of expected result",
      "files": ["evals/files/utils.py"],
      "expectations": [
        "The output follows the rule's directive",
        "The rule's concern was addressed without prompting"
      ],
      "rule_file": ".claude/rules/example.md",
      "notes": "Optional notes about this eval"
    }
  ]
}
```

**Fields:**
- `rule_name`: Descriptive name for the rule being tested
- `rule_file`: Path to the rule file (relative to repo root), default for all evals. Use `null` when per-eval overrides are the pattern and there is no single default rule
- `evals[].id`: Unique integer identifier
- `evals[].prompt`: The task to execute
- `evals[].expected_output`: Human-readable description of success
- `evals[].files`: Optional list of input file paths
- `evals[].expectations`: List of verifiable statements
- `evals[].rule_file`: Optional per-eval rule file override. `null` means no specific rule file (e.g., tests general workflow without a particular rule)
- `evals[].notes`: Optional notes about the eval case

---

## trigger_eval_set.json (Trigger Evals)

Used by `scripts/run_eval.py` and `scripts/run_loop.py` for description optimization. A flat JSON array where each item tests whether the skill description triggers Claude to invoke the skill.

```json
[
  { "query": "Create a new coding rule for error handling", "should_trigger": true },
  { "query": "Write a React component for the dashboard", "should_trigger": false }
]
```

**Fields:**
- `query`: A user message to test
- `should_trigger`: Whether the skill should activate for this query

---

## history.json

Tracks version progression during rule optimization. Located at workspace root.

```json
{
  "started_at": "2026-01-15T10:30:00Z",
  "rule_name": "import-ordering",
  "current_best": "v2",
  "iterations": [
    {
      "version": "v0",
      "parent": null,
      "expectation_pass_rate": 0.65,
      "grading_result": "baseline",
      "is_current_best": false
    },
    {
      "version": "v2",
      "parent": "v1",
      "expectation_pass_rate": 0.85,
      "grading_result": "won",
      "is_current_best": true
    }
  ]
}
```

**Fields:**
- `started_at`: ISO timestamp of when improvement started
- `rule_name`: Name of the rule being improved
- `current_best`: Version identifier of the best performer
- `iterations[].version`: Version identifier (v0, v1, ...)
- `iterations[].parent`: Parent version this was derived from
- `iterations[].expectation_pass_rate`: Pass rate from grading
- `iterations[].grading_result`: "baseline", "won", "lost", or "tie"
- `iterations[].is_current_best`: Whether this is the current best version

---

## grading.json

Output from the grader agent. Located at `<run-dir>/grading.json`.

```json
{
  "expectations": [
    {
      "text": "Claude adds the copyright header to the new source file",
      "passed": true,
      "evidence": "Found in output: copyright header present at line 1"
    },
    {
      "text": "The rule did not cause unwanted side effects",
      "passed": true,
      "evidence": "Output only contains changes relevant to the requested task"
    }
  ],
  "summary": {
    "passed": 2,
    "failed": 0,
    "total": 2,
    "pass_rate": 1.0
  },
  "execution_metrics": {
    "tool_calls": {
      "Read": 5,
      "Write": 2,
      "Bash": 3
    },
    "total_tool_calls": 10,
    "total_steps": 4,
    "errors_encountered": 0,
    "output_chars": 8200,
    "transcript_chars": 2400
  },
  "timing": {
    "executor_duration_seconds": 45.0,
    "grader_duration_seconds": 12.0,
    "total_duration_seconds": 57.0
  },
  "claims": [
    {
      "claim": "The rule was followed without explicit prompting",
      "type": "quality",
      "verified": true,
      "evidence": "Transcript Step 1 shows copyright header added proactively"
    }
  ],
  "user_notes_summary": {
    "uncertainties": [],
    "needs_review": [],
    "workarounds": []
  },
  "eval_feedback": {
    "suggestions": [
      {
        "expectation": "Claude adds copyright header",
        "reason": "Claude may add this by default even without the rule — consider testing with a less common directive to better discriminate rule effectiveness"
      }
    ],
    "overall": "Consider adding a negative test case for out-of-scope file types."
  }
}
```

**Fields:**
- `expectations[]`: Graded expectations with evidence
  - `text`: The original expectation text
  - `passed`: Boolean - true if expectation passes
  - `evidence`: Specific quote or description supporting the verdict
- `summary`: Aggregate pass/fail counts
- `execution_metrics`: Tool usage and output size (from executor's metrics.json)
- `timing`: Wall clock timing (from timing.json)
- `claims`: Extracted and verified claims from the output
- `user_notes_summary`: Issues flagged by the executor
- `eval_feedback`: (optional) Improvement suggestions for the evals

---

## metrics.json

Output from the executor agent. Located at `<run-dir>/outputs/metrics.json`.

```json
{
  "tool_calls": {
    "Read": 5,
    "Write": 2,
    "Bash": 3,
    "Edit": 1
  },
  "total_tool_calls": 11,
  "total_steps": 4,
  "files_created": ["src/utils/format-date.ts"],
  "errors_encountered": 0,
  "output_chars": 8200,
  "transcript_chars": 2400
}
```

---

## timing.json

Wall clock timing for a run. Located at `<run-dir>/timing.json`.

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

**Fields:**
- `total_tokens`: integer — total tokens used during the run
- `duration_ms`: integer — wall-clock time in milliseconds
- `total_duration_seconds`: float — same value as `duration_ms` but in seconds, for convenience

> **Note:** The grader may add additional timing fields (`grader_duration_seconds`, `executor_duration_seconds`) to `grading.json` when it records its own timing breakdown. Those fields belong in grading.json, not here.

---

## benchmark.json

Output from benchmark runs. Located at `benchmarks/<timestamp>/benchmark.json`.

```json
{
  "metadata": {
    "rule_name": "import-ordering",
    "rule_file": ".claude/rules/python-imports.md",
    "executor_model": "claude-sonnet-4-20250514",
    "analyzer_model": "most-capable-model",
    "timestamp": "2026-01-15T10:30:00Z",
    "evals_run": [1, 2, 3],
    "runs_per_configuration": 3
  },
  "runs": [
    {
      "eval_id": 1,
      "eval_name": "new-source-file",
      "configuration": "with_rule",
      "run_number": 1,
      "result": {
        "pass_rate": 1.0,
        "passed": 3,
        "failed": 0,
        "total": 3,
        "time_seconds": 42.5,
        "tokens": 3800,
        "tool_calls": 10,
        "errors": 0
      },
      "expectations": [
        {"text": "...", "passed": true, "evidence": "..."}
      ],
      "notes": []
    }
  ],
  "run_summary": {
    "with_rule": {
      "pass_rate": {"mean": 0.95, "stddev": 0.05, "min": 0.90, "max": 1.0},
      "time_seconds": {"mean": 45.0, "stddev": 12.0, "min": 32.0, "max": 58.0},
      "tokens": {"mean": 3800, "stddev": 400, "min": 3200, "max": 4100}
    },
    "without_rule": {
      "pass_rate": {"mean": 0.35, "stddev": 0.08, "min": 0.28, "max": 0.45},
      "time_seconds": {"mean": 32.0, "stddev": 8.0, "min": 24.0, "max": 42.0},
      "tokens": {"mean": 2100, "stddev": 300, "min": 1800, "max": 2500}
    },
    "delta": {
      "pass_rate": "+0.60",
      "time_seconds": "+13.0",
      "tokens": "+1700"
    }
  },
  "notes": [
    "Rule consistently improves import ordering compliance",
    "Without-rule runs occasionally follow the pattern but not reliably"
  ]
}
```

**Fields:**
- `metadata`: Information about the benchmark run
  - `rule_name`: Name of the rule
  - `rule_file`: Path to the rule file
  - `timestamp`: When the benchmark was run
  - `evals_run`: List of eval names or IDs
  - `runs_per_configuration`: Number of runs per config
- `runs[]`: Individual run results
  - `configuration`: Must be `"with_rule"` or `"without_rule"` (viewer depends on exact string)
  - `result`: Nested object with `pass_rate`, `passed`, `failed`, `total`, `time_seconds`, `tokens`, `tool_calls`, `errors`
- `run_summary`: Statistical aggregates per configuration
  - `delta`: Difference strings like `"+0.60"`, `"+13.0"`
- `notes`: Freeform observations from the analyzer

**Important:** The viewer reads these field names exactly. Using `config` instead of `configuration`, or putting `pass_rate` at the top level of a run instead of nested under `result`, will cause the viewer to show empty/zero values.

---

## comparison.json

Output from blind comparator. Located at `<grading-dir>/comparison-N.json`.

```json
{
  "winner": "A",
  "reasoning": "Output A consistently follows the rule directive while Output B ignores it in edge cases.",
  "rubric": {
    "A": {
      "content": { "correctness": 5, "completeness": 5, "rule_adherence": 4 },
      "structure": { "organization": 4, "conciseness": 5, "naturalness": 4 },
      "content_score": 4.7,
      "structure_score": 4.3,
      "overall_score": 9.0
    },
    "B": {
      "content": { "correctness": 3, "completeness": 2, "rule_adherence": 3 },
      "structure": { "organization": 3, "conciseness": 2, "naturalness": 3 },
      "content_score": 2.7,
      "structure_score": 2.7,
      "overall_score": 5.4
    }
  },
  "output_quality": {
    "A": {
      "score": 9,
      "strengths": ["Rule followed consistently", "No side effects"],
      "weaknesses": ["Minor style difference"]
    },
    "B": {
      "score": 5,
      "strengths": ["Basic structure correct"],
      "weaknesses": ["Rule directive ignored", "Inconsistent behavior"]
    }
  },
  "expectation_results": {
    "A": { "passed": 4, "total": 5, "pass_rate": 0.80, "details": [] },
    "B": { "passed": 2, "total": 5, "pass_rate": 0.40, "details": [] }
  }
}
```

---

## analysis.json

Output from post-hoc analyzer. Located at `<grading-dir>/analysis.json`.

```json
{
  "comparison_summary": {
    "winner": "A",
    "winner_rule": "path/to/winner/rule",
    "loser_rule": "path/to/loser/rule",
    "comparator_reasoning": "Brief summary of why comparator chose winner"
  },
  "winner_strengths": [
    "Clear, specific directive that leaves no ambiguity",
    "Good example that demonstrates the expected pattern"
  ],
  "loser_weaknesses": [
    "Vague wording led to inconsistent interpretation",
    "No example provided for edge case"
  ],
  "instruction_following": {
    "winner": { "score": 9, "issues": [] },
    "loser": { "score": 6, "issues": ["Ignored rule for helper files"] }
  },
  "token_efficiency": {
    "winner": { "tokens": 120, "effectiveness_score": 9, "tokens_per_point": 13.3 },
    "loser": { "tokens": 350, "effectiveness_score": 5, "tokens_per_point": 70.0 }
  },
  "improvement_suggestions": [
    {
      "priority": "high",
      "category": "instructions",
      "suggestion": "Add explicit example for helper file pattern",
      "expected_impact": "Would clarify rule application scope"
    }
  ],
  "transcript_insights": {
    "winner_execution_pattern": "Read rule -> Applied consistently -> Verified",
    "loser_execution_pattern": "Read rule -> Applied partially -> Missed edge case"
  }
}
```

---

## audit_report.json

Output from rule audit. Located at audit output path.

```json
{
  "timestamp": "2026-01-15T10:30:00Z",
  "total_rules": 15,
  "total_tokens": 3200,
  "total_lines": 450,
  "rules": [
    {
      "file": ".claude/rules/api/getting-started.md",
      "system": "claude_rules",
      "lines": 85,
      "tokens": 420,
      "frontmatter_valid": true,
      "issues": []
    },
    {
      "file": ".claude/rules/typescript-strict.md",
      "system": "claude_rules",
      "lines": 5,
      "tokens": 80,
      "frontmatter_valid": true,
      "issues": []
    }
  ],
  "overlaps": [
    {
      "rule_a": ".claude/rules/typescript-strict.md",
      "rule_b": ".claude/rules/rust-ownership.md",
      "shared_keywords": ["memory_safety", "strict_mode"],
      "similarity": 0.35
    }
  ],
  "stale_globs": [],
  "issues": []
}
```

**Fields:**
- `total_tokens`: Estimated total token budget across all rules
- `rules[]`: Per-rule breakdown with line count, token estimate, validation status
- `overlaps[]`: Pairs of rules with significant keyword similarity
- `stale_globs[]`: Glob patterns that match no git-tracked files
- `issues[]`: Summary of all problems found

---

## eval_metadata.json

Metadata for a single eval case within a benchmark run. Located at `<eval-dir>/eval_metadata.json` inside each eval's directory.

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "expectations": [
    {"text": "The output includes type hints on all function signatures", "type": "programmatic"},
    {"text": "The generated code follows idiomatic Go error handling", "type": "qualitative"},
    {"text": "The Ruby file includes a frozen_string_literal comment", "type": "programmatic"}
  ]
}
```

**Fields:**
- `eval_id`: Integer identifier matching the eval's `id` in `evals.json`
- `eval_name`: Human-readable slug for the eval (used as directory name)
- `prompt`: The task prompt given to the executor
- `expectations[]`: List of expectations to grade (uses the same field name as `evals.json` and `grading.json` for pipeline consistency)
  - `text`: Description of what to check
  - `type`: Either `"programmatic"` (can be verified mechanically from outputs) or `"qualitative"` (requires judgment to evaluate)

---

## feedback.json

Output from the eval viewer when the user submits reviews. Located at `<workspace>/iteration-N/feedback.json` (inside the iteration directory).

```json
{
  "reviews": [
    {
      "run_id": "eval-0-with_rule",
      "feedback": "The rule was followed but the output missed edge case X",
      "timestamp": "2026-01-15T10:45:00Z"
    },
    {
      "run_id": "eval-1-with_rule",
      "feedback": "",
      "timestamp": "2026-01-15T10:46:00Z"
    }
  ],
  "status": "complete"
}
```

**Fields:**
- `reviews[]`: Array of per-run feedback entries
  - `run_id`: Identifier matching the run directory path
  - `feedback`: User's text feedback (empty string means no issues found)
  - `timestamp`: When the feedback was submitted
- `status`: Either `"complete"` or `"partial"`

---

## Workspace Directory Layout

The workspace directory is created during benchmark and evaluation runs. Each iteration contains eval results for both configurations (with and without the rule), plus aggregate benchmark data.

```
rule-creator-workspace/
  iteration-1/
    eval-descriptive-name/
      with_rule/
        outputs/           # Files created by the executor
          metrics.json     # Executor tool usage and output stats
          transcript.md    # Execution transcript
          user_notes.md    # Optional executor notes
        grading.json       # Grader output for this run
        timing.json        # Wall clock timing data
      without_rule/
        outputs/
          metrics.json
          transcript.md
          user_notes.md
        grading.json
        timing.json
      eval_metadata.json   # Prompt and expectations for this eval
    benchmark.json         # Aggregated results across all evals
    benchmark.md           # Human-readable summary
    feedback.json          # User review feedback (from eval viewer)
```

**Key conventions:**
- `eval-descriptive-name` directories are named after the eval's `eval_name` slug
- `with_rule` and `without_rule` are the two configurations compared during benchmarking
- `outputs/` is always a subdirectory of the configuration directory
- `grading.json` and `timing.json` are siblings to (not inside) `outputs/`
- `eval_metadata.json` sits at the eval level, shared by both configurations
