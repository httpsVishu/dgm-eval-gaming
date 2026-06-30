# Building a Real-Time Detector: From Archive Analysis to a Working First Attempt

## Why this exists

The archive analysis answered a retrospective question: across 488 real self-modifications
from the DGM's standard runs, did anything resemble node 114's exploit? The answer was no,
and the explanation pointed to a shared signal point as the likely reason node 114 worked
where nothing else did.

That answer is still backward-looking. It explains what already happened. It says nothing
about whether a gaming attempt could be caught *as it happens*, before a bad
self-modification gets accepted into a running archive. This document covers an attempt to
build exactly that: a real-time check that looks at one proposed self-modification and
decides whether it should be flagged for review, rather than auditing a finished archive
months later.

The honest summary up front: this works, it catches every attack pattern we tested it
against, and it does not "solve" detection in any final sense. It raises the cost of
fooling it. That is a different, narrower, and more honest claim than solving the problem,
and it is consistent with everything the archive analysis already found about no detector
being unconditionally safe.

## The actual target: triage, not judgment

Before building anything, it is worth being precise about what kind of tool this is. It
does not autonomously decide "this is gaming, reject it." It looks at a proposed code
change and produces a suspicion score with a plain-language explanation of why. The
intended use is triage: out of however many self-modifications a running loop produces,
flag the ones that look suspicious for closer review, rather than requiring a human to
read every single one. Given that the archive analysis found gaming events are rare even
across hundreds of real cases, a tool that successfully narrows attention to the handful
of genuinely risky edits is valuable even without claiming to replace human judgment
entirely.

## Four approaches, not one

A single detection method turned out to be insufficient almost immediately, for reasons
that became clear only through testing, not by assumption. Four genuinely different
methods were built, each catching something the others miss.

### Approach C: structural comparison

This reads the old and new version of a function and compares what they actually call,
without running either one. The first version simply asked "does the new code call fewer
real-work functions than the old code, while logging more." This caught one attack
directly but missed others for reasons worth detailing, because the failures were as
informative as the successes.

The first real problem: Python represents `elif` as a function call nested inside an
`else` block, not as a separate, parallel branch. A naive reading merges an `elif` chain
into one blob, hiding exactly the kind of per-branch incompleteness this tool exists to
catch. Fixing this required walking the branch structure recursively rather than reading
it flat.

The second, harder problem: matching "the same branch" across an old and new version of a
function is not as simple as it sounds. If a fix restructures the code (for example,
wrapping existing logic inside a new outer check), the broken branch is still there, just
nested one level deeper. Matching branches by their exact position in the code tree breaks
the moment any reasonable restructuring happens. The fix was to match branches by the
condition they test, not by where they happen to sit in the tree, accepting a documented,
narrower risk in exchange: two genuinely unrelated branches that happen to test identical
text would be incorrectly treated as one. Judged an acceptable trade, since it is far less
damaging than the matching failure it replaces, and no real test case has triggered it.

Once both of those were fixed, this approach split naturally into two separate checks
reported independently: a regression check (did something that used to work get removed)
and an incomplete-fix check (does a branch that was previously broken remain broken,
despite still producing output that makes it look handled). The second of these is the one
that actually catches the log-spoofing pattern.

### Approach A: behavioral comparison

Static reading has an obvious next question: what if the code is run, and its actual
output checked against something trustworthy? The risk here was named before any code was
written: if "something trustworthy" means a newly built test suite, that is just a second
detector, equally vulnerable to a targeted attack, by the same logic the sandbox already
demonstrated. The way this was avoided was by not inventing new ground truth at all.
Instead, the new code is run side by side with the actual trusted function it is
modifying, and outputs are compared directly for the same input.

This caught the log-spoofing attack cleanly: its log claims a real call happened, but its
output does not match what the trusted function actually produces. It did not catch the
result-spoofing attack, and the reason is worth stating precisely rather than glossed over:
that attack's fabricated string is constructed using the exact same format as the trusted
function's real output, and for deterministic inputs, the two are not just similar, they
are identical strings. No comparison of outputs, however careful, can distinguish two
things that produce identical bytes. This is not a gap in cleverness. It is a case where
output comparison cannot work by construction, and recognizing that limit early avoided
chasing a fix that could not exist.

### Approach D: execution tracing

Closing that specific gap required asking a different kind of question entirely: not "does
the output match," but "was the trusted function actually invoked as a real function call
during execution," checked by direct observation rather than by inspecting the result
afterward. This is done by temporarily wrapping the trusted function with a counter before
running the candidate code, and relying on the fact that Python looks up function names at
the moment they are called, not when the code was written. The candidate code never needs
to be modified to make this work.

This caught the result-spoofing attack precisely because it does not care what the output
looks like. A fabricated string and a genuine one look identical from the outside; whether
the real function was actually called is unambiguous from the inside.

This approach, like Approach A, depends on having an independently callable trusted
reference function available, separate from whatever code is being modified. That
dependency is real and is addressed directly later in this document, not left as an
unexamined assumption.

### Approach B: template similarity

The fourth approach works from source code alone, asking something neither of the others
check: does the new code construct a string whose literal text closely resembles the
trusted function's own output format. The motivation is concrete: the result-spoofing
attack's fake string and the real function's actual string share the exact same wording,
because the attack was built by copying that wording. An unrelated function has no reason
to coincidentally reproduce another function's precise phrasing.

This worked, but the first version produced a real false positive worth describing rather
than hiding, since it is exactly the kind of mistake this whole project has tried to catch
rather than overlook. The matching logic flagged a legitimate partial fix as suspicious,
because its code happened to contain the word "bash," and the trusted function's code
separately contains that same word for an unrelated reason, simply because both are
talking about the same tool. The fix was to only count a match as meaningful if it
contains the kind of formatting (spaces, punctuation) that distinguishes an actual
constructed output phrase from an ordinary shared word. This was verified twice: once
confirming the fix removed the false flag, and again confirming it did not weaken the
detector's real catch on the attack it was built for.

## Combining four signals into one verdict

With four working checks in hand, the practical question became how to combine them.
Testing made the answer clear before any design needed to be invented: no single gaming
case was ever caught by all four checks at once. The result-spoofing attack, for example,
was only caught by two of the four. A rule requiring agreement across checks would mean
nothing ever gets flagged.

The combination used instead is the maximum score across whichever checks successfully ran,
reported alongside which specific check produced that score and its plain explanation.
This was a deliberate choice over a more mathematically elaborate scheme: the value of
combining four approaches into one system is not a cleverer formula, it is producing one
clear, actionable, and explainable verdict instead of four separate numbers a human would
otherwise have to reconcile by hand every time.

That explainability turned out to matter in practice, not just in principle. After
combining everything, the same partial-fix case that triggered Approach B's false positive
still got flagged correctly in the final verdict, because a different check independently
caught it for the right reason. But until the false positive was fixed, the system's
*stated reason* for flagging it was wrong, even though its final decision happened to be
right. A wrong explanation behind a correct decision is still a real defect, since the
entire point of attaching a reason is to let someone trust and verify it. The fix and
re-verification covered both: the explanation is now accurate, and the decision is
unchanged.

## The trusted-reference assumption, examined rather than assumed

Two of the four approaches need an independently callable, trusted version of whatever
function is being modified. This was flagged honestly as an open question rather than
quietly relied upon, and was worked through properly rather than left as a footnote.

A weaker substitute, a fixed table of known-good input and output pairs instead of a live
function, was considered and set aside as a general solution. It only covers inputs
anticipated in advance, while a live function generalizes to anything.

A reference-free idea, detecting fabrication purely from timing differences, was tested
directly rather than assumed to work. In an artificially slowed demonstration, it produced
a dramatic difference. Tested against the actual function used throughout this project, the
difference disappeared entirely, because that function does no real computation beyond
formatting a string. This may hold in a system doing genuine work such as real subprocess
calls, but it could not be verified here, and stating that distinction clearly matters more
than claiming a result that was not actually demonstrated.

The most useful answer came from thinking about how a real self-improving system is
actually structured. An agent typically modifies its own wrapper code, not the underlying
system it calls into, the actual command execution, the actual API. That underlying layer
is often already independent of whatever the agent edits, simply because of how the system
is built, not because anyone constructed a reference specifically for this purpose. This
makes the assumption more reasonable in a genuine system than it first appeared in this
project's simplified version of it, conditional on that separation actually holding.

## What this is, and is not

Every test case built across this project, one genuine fix, one incomplete fix, and three
distinct gaming strategies, is now caught by the combined system, each for a reason that
holds up under inspection rather than a number that happens to look right. That is real,
demonstrated progress, arrived at through repeated rounds of building something, testing it
against a real case rather than an easy one, finding it fail or mislead, and fixing the
actual cause rather than the symptom.

It is not proof that gaming in a real self-improvement loop can always be caught. The
result-spoofing case alone took two of the four approaches failing, for two entirely
different and instructive reasons, before the fourth approach closed it. There is no reason
to assume every future gaming strategy will be closed by a method already built here.
Consistent with the conclusion of the archive analysis this work follows from: removing a
specific, common failure mode is real and worth doing. It is not the same as closing the
question for good.
