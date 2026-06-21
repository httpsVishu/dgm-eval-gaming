# Eval Gaming in the Darwin Gödel Machine: An Archive Audit

## Why we looked at this
Link to the paper: https://arxiv.org/abs/2505.22954

The Darwin Gödel Machine (DGM) paper is about an AI system that rewrites its own code
to get better at coding using benchmark scores as the signal for what counts as an
improvement. Buried in the appendix is one uncomfortable result: in a dedicated
experiment on fixing tool-use hallucination, a self-modifying agent ("node 114") did not
fix the bug at all. It found and deleted the logging that its own hallucination
detector depended on. No logging meant no detected hallucination, so the score went
to a perfect 2.0 while the actual problem was still sitting there, untouched.

The paper mentions this once, calls it a critically important open problem and moves
on. That's the part that stuck with us. If a system can hit a perfect score by quietly
breaking the thing measuring it, what does that say about every other score the paper
reports?

## What we had to work with

The DGM authors released the complete raw archive of every self-modification from
their main experiments — not just the final code, but every diff, every reasoning
transcript and every resulting score, across all three run conditions (full DGM, no
self-improvement, no open-ended exploration) on both SWE-bench and Polyglot. That's
488 individual self-modification attempts, each one a real decision a real agent made
about what to change in its own codebase. This is ground truth, not a guess.

Link to the raw archive: https://drive.google.com/drive/folders/1Kcu9TbIa9Z50pJ7S6hH9omzzD1pxIYZC

## Our approach (in three steps)

**Step 1: Re-analyze the archive.** Before building anything, we wanted to know
whether node 114 was a one-off accident or something that happens routinely. We
checked every single diff for two things: did it ever touch the official benchmark
grading code and did it ever show the specific fingerprint of node 114's trick
(deleting a check or a log line without replacing it with something better). The
answers were surprising — see below.

**Step 2: Build a sandbox to test the explanation.** The archive told us *what*
didn't happen, but we needed a controlled experiment to explain *why* node 114 worked
when nothing else like it did. So we built a small, fully working simulation of the
hallucination bug and tested several possible fixes (some honest, some deliberately
designed to cheat) against different ways of scoring them to isolate exactly which
property made one objective gameable and another one not.

**Step 3: Ground it in theory and be honest about the limits.** Once we had a
working explanation, we checked it against existing reward-hacking research to make
sure we were not just describing a coincidence and we specifically went looking for
ways our own explanation could be wrong or incomplete, which it was, in one important
way we think is worth knowing about.

## What we found

Across all 488 self-modifications, we found zero instances of node-114-style cheating.
The official benchmark code was never touched because in these runs it physically
sits outside the folder the agent can edit. And the specific "deleted a check without
replacing it" signature showed up only 8 times, every single one of which, on manual
inspection, turned out to be either a broken feature attempt or a legitimate rewrite,
not cheating.

So why did node 114 succeed elsewhere? Our answer, confirmed by the sandbox: it is not
about how many things an objective checks. It is about whether all those checks secretly
read from one shared, editable signal. Node 114's three checks all pulled from a single
logging function, means break that one function, break all three checks at once. SWE-bench
and Polyglot do not have that weakness since every task runs its own independent test
with no shared signal source to attack.

The honest twist: this protection is not absolute. We built a detector specifically
designed to remove every shared signal point and it worked until we built one more
attack specifically aimed at that detector's own logic, which got through completely.
There is no detector design that is safe against every possible attacker, only designs
that are safe against attackers who don't already know how the design works.

## What's in this repo

- [`archive_reanalysis.md`](./archive_reanalysis.md) — the full write-up of everything
  above, in detail, with the actual numbers, the theory and what this means in
  practice for anyone designing a detection layer for a system like this.
- [`sandbox/`](./sandbox) — the runnable experiment from Step 2. No setup required;
  see `sandbox/README.md` for how to run it yourself.

## A note on what this is

This is not a research paper and we are not claiming to have solved anything. It is an
independent audit of data that was already public. It is built on top of the Darwin Gödel
Machine, a piece of work we think is genuinely excellent and worth taking seriously.
All credit for the DGM itself, including the node 114 finding that started this whole
investigation, belongs to its authors: Jenny Zhang, Shengran Hu, Cong Lu, Robert Lange
and Jeff Clune. We are standing entirely on their published paper and the archive data
they chose to release alongside it. Without that openness, none of this would have
been possible to check at all.

If anything here is wrong, incomplete or missing context the original authors would
have caught immediately, that is on us, not on the DGM paper or its findings.
