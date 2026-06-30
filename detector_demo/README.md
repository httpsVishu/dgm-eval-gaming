# Real-Time Detector: A First Attempt

This follows directly from the archive analysis in the repo root
(`archive_reanalysis.md`). That work was retrospective: it audited 488 already-finished
self-modifications and found no instance of node 114's exploit, then explained why,
pointing to a shared signal point as the likely reason node 114 succeeded where nothing
else did.

This folder is the natural next question: can something resembling that exploit be
caught in real time, before a self-modification is accepted, rather than found by
auditing history afterward.

Read [`DETECTOR_FINDINGS.md`](./DETECTOR_FINDINGS.md) for the full account: four distinct
detection methods, why each one was needed (and what the others missed), the bugs found
and fixed along the way, and an honest account of what this does and does not prove.

## Running it

No dependencies beyond the Python standard library.

```bash
python3 unified_detector.py
```

This runs all four checks against four real test cases (one genuine fix, one incomplete
fix, two distinct gaming strategies) and prints a combined verdict for each, with full
attribution showing which check flagged it and why.

Each individual check can also be run on its own:

```bash
python3 structural_asymmetry_detector.py    # Approach C: reads code, never runs it
python3 behavioral_comparison_detector.py   # Approach A: runs code, compares output
python3 execution_trace_detector.py         # Approach D: runs code, traces real calls
python3 template_similarity_detector.py     # Approach B: reads code, checks for copied wording
```

## The honest scope

This catches every attack pattern built and tested in this project. It has not been run
against a real, live self-improvement loop, only against a small, controlled example
built specifically to test it. Consistent with the rest of this repo's findings: this
raises the cost of a specific, common kind of gaming. It does not close the question.
