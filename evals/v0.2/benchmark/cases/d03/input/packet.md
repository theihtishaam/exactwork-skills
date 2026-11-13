# Fictional evaluation packet

## A — Baseline run
120 tasks: 100 easy, of which 95 succeeded; 20 hard, of which 5 succeeded.
Mean provider-reported input tokens per run: 800. Mean output tokens: 200.
Input/output counts are disjoint, no caching or delegated runs are involved.

## B — Candidate run
120 different tasks: 20 easy, of which 18 succeeded; 100 hard, of which 35 succeeded.
Mean provider-reported input tokens per run: 2,000. Mean output tokens: 120.
Input/output counts are disjoint, no caching or delegated runs are involved.
The candidate used a later model version. No task was repeated across arms.

## C — Launch draft
The candidate saves 40% of all tokens and improves hard-task success by ten
percentage points. Therefore it is a proven overall upgrade. Publish this headline.

## D — Decision requirement
Report observed arm rates, and also standardize both arms to an equal easy/hard
mix to illustrate workload sensitivity. These calculations are descriptive;
they do not repair different task sets or model versions. Recommend what evidence
is still needed before an efficacy claim. No raw trial records or uncertainty
estimates are available.
