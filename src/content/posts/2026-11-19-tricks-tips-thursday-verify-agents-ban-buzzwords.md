---
title: "Tricks & Tips Thursday: Verify Agents, Ban Buzzwords"
description: "Six copyable patterns: end-to-end tests, property tests and a separate grader for agent output, plus a grep-able style contract for LLM prose."
pubDate: 2026-11-19
tags: ["agents", "testing", "evals", "prompting", "llm", "tips-thursday"]
kind: tips
sources: ["https://claude.dev/blog/how-the-claude-code-team-thinks-about-verification/", "https://dev.to/qunirice_verase_1ab0caeba/how-to-make-an-llm-stop-writing-like-an-llm-style-contracts-and-checks-i9a"]
canonical:
---

Agent output looks right until you run it, and LLM prose sounds fine until you read it twice. This week's tricks make both checkable by a script instead of by your tired eyes.

```diagram
{
  "type": "compare",
  "title": "Supervising by Eye vs. Automatic Checks",
  "caption": "Checks stop depending on your attention once scripts enforce them.",
  "before": {
    "heading": "Before",
    "points": [
      "Check every agent output yourself",
      "Unit tests pass while feature is broken",
      "Agent grades its own work",
      "\"Write naturally\" is untestable"
    ]
  },
  "after": {
    "heading": "After",
    "points": [
      "End-to-end test covers a real user flow",
      "Separate grader scores output against rubric",
      "Repeated failures become hook or CLAUDE.md rule",
      "Banned-phrase file lets a grep lint prose"
    ]
  }
}
```

## Situation
You can only supervise one or two agents at a time if you have to check everything yourself. The Claude Code team says that is the ceiling without verification loops.

The prose side has the same problem. Generic assistant text is full of hedging and buzzwords, and "write naturally" is not a rule you can test.

## Task
I want agent code and agent writing to be checked by something automatic. That means tests that are hard to fool, a grader that is not the author, and style rules a script can enforce.

## Action

### Start with one end-to-end test
If you can only invest in one test type, the Claude Code team's post says to pick end-to-end. Describe a real user flow, such as add to cart, check out, reach the confirmation page. Either the whole feature works or it doesn't (via Hacker News).

Why it works: unit tests can pass while the feature is broken, because both the agent and the test miss the full task.

### Write a feature map and use it as the rubric
List features from the user's point of view: paths, keyboard shortcuts, selectors, expected results. The post says this map doubles as a guide and a grading rubric for the agent (via Hacker News). Pair it with a skill that boots, drives and inspects the real app, for example through CDP, simulators or API harnesses.

Why it works: the agent gets hands and eyes on the running system, and "done" has a definition.

### Add a round-trip property test
Pick something with an inverse, like encode/decode or parse/serialize, and let a library hunt for counterexamples. The post names fast-check for JS/TS, Hypothesis for Python and proptest for Rust (via Hacker News).

```python
from hypothesis import given, strategies as st

@given(st.text())
def test_roundtrip(s):
    assert decode(encode(s)) == s
```
<!-- VERIFY: run this snippet and confirm it works -->

Why it works: it covers the edge cases people forget, which the post says is where agents often fail.

### Use a separate grader, then feed failures back
Have a different pass grade the output against a rubric instead of letting the author mark its own work. The company says this improved task success by up to 10 points in internal tests on structured file generation, with the biggest gains on the hardest problems. When the agent keeps failing the same check, turn it into a hook or an explicit CLAUDE.md rule.

Why it works: the check runs as ordinary software, and the rule stops the same failure from coming back (mostly, as the post itself hedges).

### Write a style contract you can grep
Replace "sound human" with rules a script can test: sentence limit, paragraph limit, active voice, and a banned-phrase file (via dev.to LLM). The author's list includes "in today's", "delve", "unlock" and "seamless". Then lint the draft:

```bash
if grep -n -i -F -f banned_phrases.txt draft.md; then
  echo "banned phrase found"; exit 1
fi
```
<!-- VERIFY: run this snippet and confirm it works -->

Why it works: a banned list turns taste into an exit code. Keep a human review step for accuracy, as the author does.

### Give the model an escape hatch and a BAD/GOOD pair
Tell the editor prompt to write "check documentation" when a fact is missing, and forbid invented versions, prices and URLs. Add one before/after example. The author's pair swaps "API logs are a game-changer for reliability" for a sentence naming the request ID, status code and latency (via dev.to LLM).

Why it works: the model gets a sanctioned alternative to guessing, and the example shows what concrete looks like.

## Result
Your checks stop depending on your attention. A real-flow test, a property test and a grader catch agent mistakes, and a grep catches the prose tics.

Keep the tests fast and stable. The post warns that flaky tests teach agents to rerun instead of fix, and slow ones get run less often.

- Pick E2E first, add property tests for anything with an inverse, and grade with a separate pass.
- Turn repeated agent failures into a hook or a CLAUDE.md rule.
- Make style rules greppable, ban phrases in a file, and let the model say "check documentation".

## My take

TODO(nilay): add your own favourite trick, or a gotcha you hit while trying these, then delete this line.

## Sources

- [How the Claude Code team thinks about verification / claude.dev Blog](https://claude.dev/blog/how-the-claude-code-team-thinks-about-verification/) (Hacker News)
- [How to Make an LLM Stop Writing Like an LLM: Style Contracts and Checks](https://dev.to/qunirice_verase_1ab0caeba/how-to-make-an-llm-stop-writing-like-an-llm-style-contracts-and-checks-i9a) (dev.to LLM)
