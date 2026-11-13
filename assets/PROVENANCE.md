# Visual provenance

## exactwork-cover.png

- Created: 2026-11-12.
- Method: built-in `image_gen.imagegen` tool; no API or CLI fallback.
- Use: original AI-generated cover artwork for the EXACTWORK README.
- Inputs: the first generation used no reference images. A subsequent correction attempt used that generated image only; no third-party image inputs were supplied.
- Selected output: first generation, copied without modification.
- Format: PNG, RGB, 1536 × 1024 pixels.
- SHA-256: `942b54f621fd1e37b4716ca1a669c1448f32b9b071d87a5c4e19f176141ad20e`.
- Visual meaning: a glass lens and cyan/orange light paths on midnight navy, with the EXACTWORK title and tagline. This is decorative brand artwork, not a technical optics diagram or evidence of measured performance.
- Verification: final saved PNG was independently opened with view_image. The title, tagline, lens, and beams were visible and the text was correct. An earlier agent report of missing elements was not reproduced in this final inspection.

## Original generation prompt

```text
Use case: ads-marketing
Asset type: original GitHub README cover for an open-source agent skill toolkit.
Create a polished wide landscape image, approximately 3:2, with a premium editorial science and engineering aesthetic.
Scene: deep midnight navy background with generous negative space and subtle depth.
Subject: one luminous translucent optical glass prism or precision lens. A few scattered cyan and warm orange light paths enter it and emerge as clean, precisely aligned beams. This is an evocative brand illustration, not a technical optical diagram or a claim of measured performance.
Style: elegant restrained 3D studio rendering, physically tactile glass, controlled glow, sophisticated art direction, crisp edges, subtle atmospheric depth.
Composition: a balanced spacious cover with the luminous lens and beam artwork as the central visual anchor, readable understated typography integrated into the composition.
Text, verbatim: "EXACTWORK"
Second line, verbatim: "Less noise. Complete work."
Render EXACTWORK as one word, uppercase E X A C T W O R K, in clean understated white sans-serif typography. Tagline in smaller white or soft gray text, with exact punctuation.
Constraints: no other text, no numerical benchmarks, no charts, no badges, no robots, no mascots, no competitor logos, no watermark. Original visual identity. Opaque background.
```

## Correction attempt (not selected)

The following edit used the first generated image as its only reference. The first generation was ultimately selected after independent inspection confirmed its complete composition.

```text
Edit this image into a complete premium README cover. Keep the existing midnight navy background and cyan/orange light rays, but ADD the missing central optical lens and typography visibly into the actual final raster image.
At the center place a large luminous translucent vertical precision glass lens, richly detailed with cyan edges and subtle orange reflection. The rays converge into the lens and leave as aligned horizontal beams. This is brand artwork, not a physical optics diagram.
In the upper third add the large clean white uppercase title exactly: "EXACTWORK".
Below the title add the smaller line exactly: "Less noise. Complete work."
Use elegant sans-serif typography, ensure every letter is clearly visible and correctly spelled. Preserve a refined scientific editorial composition with generous spacing. Landscape 1536x1024. No additional text, no benchmarks, no robots, no logos, no watermark. The final saved PNG must visibly contain the lens, title, tagline, background, and beams as one finished opaque raster image.
```

## workflow.svg and comparison.svg

Original editable SVG diagrams authored programmatically from the package design and source-backed comparison. No AI-generated numbers or benchmark graphics are used. Local PNG renderings were inspected for clipping, legibility, and consistent labels. All graphics include descriptive accessible text or README alt text.


## Version 0.2 figures

`workflow.svg`, `comparison.svg`, and `evidence.svg` are editable, programmatically authored figures. Text and values follow the 0.2 study and documentation. PNG previews were inspected for clipping and legibility. The AI-generated cover is decorative; it is not a generated chart or evidence source. The evidence chart uses actual reported usage and includes its small-sample and grading limitations.

## Additional publication explainers (2026-11-13)

`skill-map.svg`, `learning-loop.svg`, `context-example.svg`, `compatibility.svg`, and `quickstart.svg` are original editable SVG figures authored programmatically in the same navy/cyan/amber style as the released diagrams. They introduce no new benchmark claims or third-party logos. Each has accessible SVG title/description and was rendered to a PNG inspection preview.

The context example uses an explicitly synthetic 11-line log. Its initial selected excerpts and coverage counters were generated by the released `context_slice.py` using `--query "request=42" --context 1 --max-lines 3`; this is an illustration of behavior, not a performance measurement. It explicitly marks incomplete selection and an uninspected later failure. Compatibility labels describe documented paths and preserve the distinction from native end-to-end verification. Quickstart commands use a placeholder project path and the actual installer arguments.

The original AI-generated cover remains unchanged. These additional diagrams are code-authored, not AI-generated numerical charts.

## Task-quality and observed-work chart (2026-11-13)

`quality-and-work.svg` is an original programmatically authored figure generated directly from the published `evals/v0.2/final-results.json`. Development task passes are 4/4, 3/4, and 4/4 for no skill, Exactwork 0.1, and compact 0.2. Held-out public-task passes after the documented blind grader audit are 6/6 for each. Original strict compact held-out score (5/6) remains visible. The lower panel shows visible held-out tool-call items: 29, 24, and 27, on a zero-based full 0–30 scale.

Correctness bars use a full 0–100% scale and label both numerator and denominator. The figure distinguishes development from held-out trials, notes that the six held-out repetitions represent only two unique synthetic tasks, and explicitly disclaims an intelligence score, general accuracy gain, or agent-speed interpretation. The SVG has accessible title/description text; its PNG preview was inspected for legibility and clipping. No frozen results or skill instructions were changed.


## Explanatory banner and comparison refresh (2026-11-13)

The README now uses `exactwork-banner-v2.png`, generated with the built-in image-generation tool. The original cover is retained as a separate asset. The new banner explains the task cycle, the six skills and optional helpers; it contains no generated benchmark values or promises of model improvement. Its text was visually checked.

`inside-a-task.svg` and `worked-example.svg` are code-authored explanatory diagrams; the export example is explicitly illustrative. `tokens-by-task.svg` and `matched-comparison.svg` read values from the unchanged published results JSON. Their scales start at zero, and study limits appear in the figures. `instruction-footprint.svg` reads exact UTF-8 byte sizes of the published entry files, not token estimates. `agent-model-coverage.svg` separates documented destinations, observed installation, and the absence of named-model uplift measurements. All six new SVG previews were visually checked.

Banner prompt (built-in tool):

```text
Create a polished explanatory GitHub README banner for the open source project EXACTWORK. Wide landscape 3:2 canvas, high resolution. Premium editorial software infographic, sharp typography, dark midnight navy background, warm ivory lettering, teal and restrained amber accents, subtle fine grid, exceptionally readable at 900px wide. No robot, brain, mascot, stock photo, charts, fake UI buttons, or performance numbers. Clear hierarchy, spacious rounded rectangular cards, straight connectors with arrows. Use these exact readable texts only:
Top small eyebrow: "PORTABLE AGENT SKILLS"
Huge main brand: "EXACTWORK"
Large subtitle: "Give your agent a clear way to work."
Short line: "Focused tasks. Traceable context. Checked results."
Central explanatory horizontal flow, four equal numbered cards with understated line-art icons:
"01" "Understand" "Define the task"
"02" "Inspect" "Read the evidence"
"03" "Complete" "Do the work"
"04" "Verify" "Check the result"
Below, visually separated section label: "SIX SKILLS. USE WHAT YOU NEED."
Six compact chips in a 3-column 2-row grid with exact labels:
"Execute" "Research" "Review"
"Hand off" "Extract context" "Learn a procedure"
Bottom subtle separated strip with text: "Claude Code / Codex / OpenCode / DeepSeek Harness"
And small but readable footnote: "Optional helpers for source-linked excerpts and project learning with rollback."
Communicate the flow with geometric document, magnifier, tool and check icons. Sophisticated and practical, not a neon sci-fi poster. All text accurately spelled, generous padding, readable contrast, no overlap. Do not imply the product is an autonomous service or claim guaranteed accuracy or savings. No additional text.
```


## Broader project and quality comparison (2026-11-13)

`ecosystem-comparison.svg` summarizes documented scope for ten projects from the pinned sources in `docs/comparison-sources.json`. It is not a feature-exhaustiveness audit or performance ranking. Exactwork is visually highlighted as the subject of the repository. `quality-comparison.svg` uses the unchanged matched-subset results: each tested condition passed 5/5. The remaining eight external projects have no matched measurements in this release, and no model intelligence scores are supplied. Both SVG figures are code-authored and their rendered previews were visually inspected.


## Clarifying sampled pass counts (2026-11-13)

`quality-comparison.svg` now shows the measured token totals in ascending order with explicit "5 of 5" sampled-pass counts. The earlier percentage bars could be mistaken for a universal reliability score. Exactwork 0.2 is first because it used the fewest tokens on this specific subset, not because a general intelligence or quality lead was established. All totals and outcomes remain unchanged. The updated editable figure was rendered and visually inspected.


## Opening results and instruction overhead (2026-11-13)

The README moves the observed-token comparison below the banner and introductory description. `instruction-reduction.svg` adds a separate chart from the existing frozen component measurements: core 554 to 391, research 462 to 334, review 415 to 290, using o200k_base. The figure notes that handoff remains 296 and optional context adds 321. These are static instruction counts, not runtime usage or quality measures. The new SVG was rendered and visually checked.
