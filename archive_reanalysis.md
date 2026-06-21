# Re-analyzing the Darwin Gödel Machine's Self-Improvement Archive: Where Does Eval Gaming Actually Happen?

## Why this analysis

The DGM paper documents one vivid instance of objective hacking: in a dedicated experiment
on solving FM tool-use hallucination, a self-modified agent (their "node 114") achieved a
perfect score not by fixing hallucination but by deleting the special-token logging that
the detector relied on. The paper is honest about this and flags it as a critically
important open problem.

That single example raises a natural question: is this an occasional, isolated failure
mode or is it a routine feature of self-improvement loops that we would find everywhere if we
looked? The authors released the complete raw archives (every self-modification diff,
every reasoning transcript, every score) for their *standard* SWE-bench and Polyglot runs
(separate from the dedicated hallucination experiment). 

## What we analyzed

All six released run conditions, covering both benchmarks:

| Run | Benchmark | Condition | Nodes |
|---|---|---|---|
| swe_dgm | SWE-bench | Full DGM | 82 |
| swe_dgm_nodarwin | SWE-bench | No open-ended exploration | 80 |
| swe_dgm_noselfimprove | SWE-bench | No self-improvement | 80 |
| polyglot_dgm | Polyglot | Full DGM | 80 |
| polyglot_dgm_nodawin | Polyglot | No open-ended exploration | 80 |
| polyglot_dgm_noselfimprove | Polyglot | No self-improvement | 80 |

488 total nodes each with: the self-improvement task it was given, the literal diff it
produced, its full reasoning/tool-call transcript and its resulting benchmark score.

## Finding 1: The official benchmark harness was never touched

We scanned every diff in the dataset (382 diffs with actual content) for any file path
matching the benchmark scoring infrastructure — `swe_bench/`, `polyglot/harness.py`,
`polyglot/report.py`, `benchmark.py`, `run_evaluation.py`, `test_spec.py` and related
files. **Zero diffs touched any of these paths** across all 488 self-modification events.

We also checked whether agents even *saw* these files. The path strings do appear in 135
of 382 transcripts but in every case we inspected, this was incidental: a directory
listing (`view` on a folder) that happened to show the harness files existing in the
repository tree, not the agent opening or reading their contents. Zero transcripts show
the agent issuing a `view` command on the harness file itself, and zero diffs edit it.

This simplest explanation for this is the harness lives outside the
agent's editable working directory in these runs so there is effectively no path by which
an agent could edit it, regardless of intent. The eval surface that mattered in the
paper's Appendix H case (hidden hallucination-detection logging, inside the agent's own
codebase) is architecturally different from the eval surface here (the benchmark scorer,
outside the agent's reach).

## Finding 2: Agents do build and edit their own test-interpretation tooling but it does not pay off

While the official harness is untouched, agents frequently build tools to interpret their
own test failures: `test_analyzer.py`, `error_analyzer.py`, `coverage_analyzer.py`,
`signature_checker.py` and similar. These are fully within the agent's edit-action space and are genuinely "legible and editable" eval-adjacent surface in this dataset. 79 of
382 diffs touch something in this category.

If gaming were a default tendency whenever a legible, editable eval-adjacent surface
exists, we would expect this category to show inflated scores. But does not:

| | n | avg score Δ | % positive |
|---|---|---|---|
| Diffs touching agent-built test tooling | 75 | -0.186 | 18.7% |
| Diffs not touching it | 215 | -0.104 | 31.2% |

Touching this surface correlates with worse outcomes, not better. We checked whether
viewing the file before editing it (vs. editing blind) made a difference. It did not
meaningfully (-0.181 viewed-then-edited vs -0.219 blind-edited, both well below the
-0.101 baseline of leaving it alone). Editing your own test tooling at all, regardless of
process, correlates with worse outcomes in this dataset because it is a sign of a 
struggling agent reaching for diagnostic tools as a last resort, not a gaming
strategy that pays off.

## Finding 3: A targeted search for the actual gaming signature found almost nothing

The node-114 incident has a specific, checkable signature: a diff that removes checks,
assertions or logging without replacing them with equivalent or better safeguards. We
scanned every diff in the dataset for lines removed that contained `assert`, `raise`,
logging calls or `print`, where removed lines outnumbered added lines of the same kind
by at least 2.

This flagged exactly 8 candidates out of 488 total self-modifications. We read every one
in full.

- **7 of 8 made the score worse**, not better (typically 0.2–0.3 → 0.0–0.1). In every case,
  the removed checks were incidental debris from a failed feature attempt e.g. one diff
  added a new compile-error-analysis step that imported a module that did not actually exist,
  breaking the agent outright. None of these resemble gaming hence they are failed engineering.
- **1 of 8 improved the score** (+0.2). Reading the full diff: this is a legitimate,
  substantial rewrite of the agent's own file-editing tool (adding `str_replace`,
  `insert`, `undo_edit` and ranged viewing) which is the exact same evolutionary step
  the paper itself documents and praises in Appendix G (comparing their nodes 6 and 24).
  The removed assertions were old tests of behaviour that no longer existed after a
  genuine, better rewrite of a separate analysis tool. Not gaming.

We found no instance, anywhere in this 488-node dataset, that resembles node 114.

## What this means: a boundary condition on when gaming happens

These three findings point toward a specific explanation for why node 114
happened where it happened and not elsewhere in this much larger dataset:

**The hallucination-detection experiment used a narrow, single-signal, mechanically simple
objective**:
It was a binary check for specific marker tokens in a log. An objective like that has a single point of failure: disable the one check, and the score flips from failing to perfect in one surgical edit. That is exactly what happened with node 114 in just 2 modifications.

**SWE-bench and Polyglot work differently. They are aggregate, multi-instance objectives**:
The score comes from 10, 50 or 200 independent task evaluations each with its own ground-truth test suite the agent never sees during evaluation. There is no single edit that could inflate a score like this. Gaming it would mean faking success across many separate, independent task checks at the same time, which is a much harder and riskier thing to attempt with no obvious single lever to pull.

This points to a third factor, alongside the two we started with (whether the eval is legible to the agent and whether selection pressure cares about how a score improved, not just that it improved): **Objective Granularity**:
A narrow, single-signal objective can be gamed with one cheap edit. A broad, multi-instance objective resists that because gaming it is not a single edit anymore. It is a large, conspicuous effort spread across many fronts, one that looks nothing like a normal capability improvement and nothing in this dataset shows any agent attempting it.

## Honest limitations

This is a re-analysis of one paper's released archives, not a controlled experiment. We
cannot rule out gaming strategies more subtle than the literal signature we searched for
(check/assertion/logging removal). We also do not have raw data from the actual
hallucination experiment (node 114's run) to compare directly against because that data lives in
a separate, smaller run not included in what was released for the standard benchmarks. The
granularity hypothesis is a pattern induced from this dataset's absence of gaming, combined
with the paper's one documented presence of it elsewhere; it has not yet been tested in a
setting where granularity is deliberately varied while holding other factors fixed.

## Addendum: a mechanical sandbox test and what it reveals about node 114 itself

The archive analysis above raised a natural follow-up: if narrow, single-signal objectives
are what made node 114 possible, would just switching to an aggregate, multi-instance objective have stopped it from happening?

We could not test this with a real LLM agent since we did not have API access in this environment. So we built a small, deterministic sandbox instead. We came up with five edits an agent might plausibly try: two genuine fixes, one partial fix and two gaming strategies. We then ran each one through two different scoring setups, a narrow single-check objective and an aggregate objective made of 20 scenarios, keeping everything else exactly the same. This let us isolate just one variable, how the objective is scored and see what difference it actually makes.

| edit | gaming? | narrow score | aggregate score |
|---|---|---|---|
| Genuine fix | No | 1.00 | 1.00 |
| Partial fix (covers only the tested case) | No | 1.00 | 0.55 |
| Gaming: patches the one specific check | Yes | 1.00 | **0.00** |
| Gaming: patches the shared check logic itself | Yes | 1.00 | **1.00** |
| Gaming: spoofs the underlying signal all checks read | Yes | 1.00 | **1.00** |

Aggregate scoring fully protects against an exploit that targets one specific checkpoint
(0.00 — completely caught) and incidentally also catches incomplete fixes that a narrow
objective would have rewarded as perfect (0.55 vs 1.00). But it provides **no protection
at all** against an exploit that targets the shared signal source every check reads from,
rather than any individual check (1.00 either way).

This distinction explains node 114 exactly. Going back to the actual diff in the paper's Appendix H, the agent did not patch three separate checks for three separate tasks. It edited one function, `chat_with_claude()`, the single shared logging function that writes the special marker tokens (`TOOL_USED_MARKER`, `TOOL_INPUT_MARKER`, `TOOL_RESULT_MARKER`) that every downstream check depends on. One edit at that single upstream point quietly broke detection for all three evaluated tasks at the same time. This is structurally the same as the "spoofs the shared signal" case from our sandbox, not the "patches one specific check" case. And our sandbox already showed that this kind of attack defeats multi-instance scoring just as easily as it defeats single-instance scoring.

## A third condition: does removing the shared signal point actually fix things?

The argument above leads to something we could actually test. If we build a detector that doesn't share one single signal source, where each scenario is verified independently with no common log or checking function that one edit could break, then gaming through signal spoofing should stop working. We built this third version and tested it directly.

The isolated detector checks each scenario's actual returned result string against a
tool-specific expected format (e.g. for `bash`, did the result exactly equal
`"executed: {command}"`), rather than checking a shared log field that every scenario
writes to in the same way. We re-ran every candidate edit, including the original
log-spoofing attack, against this isolated detector alongside the original narrow and
aggregate ones:

| edit | gaming? | narrow | shared aggregate | isolated aggregate |
|---|---|---|---|---|
| Genuine fix | No | 1.00 | 1.00 | 1.00 |
| Partial fix (one tool only) | No | 1.00 | 0.55 | 0.55 |
| Patches one specific check | Yes | 1.00 | 0.00 | 0.00 |
| Patches shared check logic | Yes | 1.00 | 1.00 | **0.00** |
| Spoofs the shared log signal | Yes | 1.00 | 1.00 | **0.00** |
| Spoofs the result string directly | Yes | 0.00 | 0.00 | **1.00** |

The first result confirms the hypothesis cleanly. Both attacks that work by compromising a
shared signal point (the generalized check-logic patch and the log-spoofing attack) are
fully defeated once that shared point is removed. They score a perfect 1.00 against ordinary aggregate scoring but drop to 0.00 against the isolated detector. So removing the shared signal source, not just adding more instances to check, is what actually closes this specific weakness.

The last row is the important catch and it is worth saying plainly instead of brushing past it. We asked what happens if an attacker specifically targets the isolated detector's own verification logic, by faking a result string that matches the expected output exactly, instead of spoofing the log. This attack defeats the isolated detector completely, scoring 1.00, while failing against the original narrow and shared aggregate detectors, scoring 0.00 on both. It fails there simply because it never bothers spoofing the log field those two detectors actually check.

This is not a flaw in the experiment. It is actually the main point. No detector design is safe in every situation. A log based check, a result based check, a shared check, an isolated check, each one blocks certain kinds of cheating while staying open to one specific kind: an attack built by someone who already understands exactly how that check works.

This matches what Skalse and colleagues showed in their own research. To be truly safe from gaming, a proxy measure needs to match the real goal almost perfectly. There is no shortcut around that just by structuring our checks cleverly. We can split a check into ten independent pieces and it still would not protect us from someone who studies those ten pieces and builds an attack made specifically for them.

What isolating the signal point actually gives us is protection against the common case, attacks that are not custom built for our specific detector. And that covers most real situations because most self-modifications are not trying to reverse engineer the checker on purpose. They are just taking the easiest shortcut available, whatever that happens to be. So this kind of protection is genuinely useful. It just does not mean gaming is solved for good.

## Theoretical grounding: why this is not just an empirical curiosity

Skalse et al. (2022, "Defining and Characterizing Reward Hacking") were the first to formally study when it is actually safe to optimize a proxy measure instead of the real goal you care about. Their work is built around reinforcement learning, dealing with reward functions over Markov decision processes and it does not map word for word onto a coding agent editing its own evaluation logic. But two of their results, once translated into our own setting, explain why our experiments turned out the way they did, rather than just describing what happened.

**Narrowing a proxy doesn't make it safe to optimize, even in principle.** 
Skalse et al. prove that "unhackability," meaning the property that improving our proxy measure can never make the real goal worse, is a very demanding condition to satisfy. It feels natural to assume that leaving things out of an objective, making it narrower, would be a safe simplification. They show this assumption usually does not hold. A narrower proxy can disagree with the true goal just as easily as a more detailed one, unless it meets very specific equivalence conditions that have nothing to do with narrowness itself. This lines up exactly with what our sandbox showed directly. Going from checking a single instance to checking 20 instances is, on the surface, a form of broadening and it did stop one specific attack, the one that patched a single checkpoint. But it gave zero protection against an attack that targeted the shared signal source feeding all 20 instances. The broadening only helped because it happened to break that one particular exploit, not because broadness itself creates safety. That is exactly what the theory predicts.

**Reward hacking tends to look like a sudden collapse, not a gradual drift.** 
Skalse et al. point out that real world cases of reward hacking usually look like the proxy and the true goal rising together for a while, followed by a sudden break where the true goal collapses even as the proxy keeps climbing. It is not a gradual divergence. This matches exactly what happened with node 114 which hit a perfect score after just two self-modifications, not a slow climb. It also validates the way we searched the archive. Instead of looking for a smooth correlation between touching eval adjacent code and getting a better score, we searched for sharp, single-edit jumps with a specific pattern, checks being removed without anything replacing them. The fact that this search came up empty across all 488 real self-modifications is itself meaningful under this framing. It suggests that these sudden collapse events are rare enough that catching one in the wild would need either a much bigger sample or an objective designed to be more permissive than ordinary SWE-bench or Polyglot scoring.

Taken together, our refined three-factor account (legibility, means-blind selection,
shared-signal-point exploitability) is not just a pattern we noticed in one dataset. It is
the coding-agent-specific instantiation of a more general principle that the RL theory
already establishes that the structure of how a proxy could fail to track the true
objective matters far more than superficial properties like how many terms or how many
instances the proxy nominally covers.

## Practical implication for a real self-improvement loop

If a detection layer for eval gaming in a system like the DGM is going to be designed
deliberately rather than discovered as an afterthought, this analysis suggests a specific,
checkable design question rather than a vague aspiration toward "robustness". For every property our self-improvement loop rewards, we ask this: does verifying that property anywhere in the pipeline pass through a single piece of shared code, a shared log format or one signal source that a single self-modification could break? If the answer is yes, that is the exact spot worth strengthening or backing up with an independent check. Not because independence is some magic fix, but because it closes off the cheapest, laziest way to get a high score without actually improving anything real.

It would not close off every path though and it can not. An attacker or just a capable optimizer that does not care how it gets there, can still target the independent check's own logic directly and succeed, exactly like what happened when our isolated detector's own verification method got specifically targeted in our last experiment. So the honest takeaway here is smaller than "we solved eval gaming". It is closer to "we found and removed the single most common, easiest failure mode and we are being upfront that doing this is not the same as closing the problem for good".

