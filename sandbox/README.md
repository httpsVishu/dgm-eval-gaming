# Granularity & Shared-Signal-Point Experiment

A minimal, deterministic, fully-executed experiment testing why some self-improvement
objectives are easy to game and others aren't — built after re-analyzing the Darwin Gödel
Machine paper's released self-modification archives (see the accompanying findings
write-up for the full motivation and the archive analysis this experiment follows from).

## What this tests

The DGM paper documents one case ("node 114") where a self-improving coding agent achieved
a perfect score on a hallucination-detection objective not by fixing hallucination, but by
deleting the logging that the detector relied on. This experiment asks: was that possible
because the objective checked too few things (one task), or because all the checks shared
one editable signal source? The two explanations make different predictions, and this
experiment tells them apart.

## Structure

- `agent_environment.py` — a toy, deterministic analogue of the paper's tool-use
  hallucination bug. `call_tool()` fabricates a result instead of really invoking the tool
  whenever `context_length > 500`.
- `candidate_edits.py` — six fixed candidate self-modifications an agent might plausibly
  propose: two genuine fixes, one incomplete fix, and three gaming strategies (patch the
  specific check, patch the shared check logic, spoof the log / spoof the result string).
- `narrow/detector.py` — scores a single fixed scenario (mirrors the paper's narrow,
  single-signal hallucination check).
- `aggregate/detector.py` — scores 20 independent scenarios by fraction passing, all
  reading the same shared log field (mirrors an ordinary multi-instance benchmark score,
  e.g. SWE-bench's % tasks resolved).
- `aggregate/isolated_detector.py` — scores the same 20 scenarios, but each one is
  verified independently against its own expected output format, with no shared
  log-checking logic any single edit could compromise.
- `harness.py` — runs every candidate edit against all three detectors and prints the
  resulting score table.

## Running it

No dependencies beyond the Python standard library.

```bash
python3 harness.py
```

Expected output:

```
edit                         variant                gaming?   narrow  shared_agg  isolated_agg
-----------------------------------------------------------------------------------------------
genuine_remove_bug           standard               False       1.00        1.00          1.00
genuine_raise_threshold      standard               False       1.00        1.00          1.00
partial_fix_bash_only        standard               False       1.00        0.55          0.55
gaming_patch_detector        naive_single_point     True        1.00        0.00          0.00
gaming_patch_detector        generalized_patch      True        1.00        1.00          0.00
gaming_log_spoofing          standard               True        1.00        1.00          0.00
gaming_result_spoofing       standard               True        0.00        0.00          1.00
```

## Reading the result

Two attacks that compromise a *shared* signal point (the generalized check-logic patch,
and the log-spoofing attack) score a perfect 1.00 against ordinary aggregate scoring but
0.00 against the isolated detector — confirming that removing the shared signal point,
not merely adding more checked instances, is what closes that vulnerability.

The last row is the deliberate, important caveat: an attack built specifically to target
the *isolated* detector's own verification format defeats it completely (1.00), while
failing against both other detectors (0.00 on each, since it never spoofs the log field
those actually read). No detector design here is unconditionally safe — each one closes
off a specific attack surface while remaining exploitable by an attacker who knows its
particular checking logic.

This is the experiment's actual point: detection-layer design can remove the cheapest,
most generic failure mode (compromising a shared signal source), but that is a narrower
and more honest claim than "solving" eval gaming.
