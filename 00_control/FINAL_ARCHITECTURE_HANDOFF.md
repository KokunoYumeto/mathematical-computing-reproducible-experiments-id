# O002/B80 Mathematical Computing — final architecture and existing-task handoff

Selected: 2026-08-21T23:43:24+02:00  
Coordinator: `01a01ec1-e685-70d0-b022-211396334723`  
Sole course-production owner: `01a01f42-f9d5-7391-93ec-bc76c130b2a1`  
Task title: `Bahasa Indonesia — Mathematical Computing & Reproducibility (O002)`  
Task created by this decision: **no**  
Handoff delivery: `2026-08-22T05:54:29+02:00`; direct task readback passed

## Decision

O002/B80 selects the existing independently authored Indonesian coursebook,
*Komputasi Matematis dan Eksperimen yang Dapat Direproduksi*, as its sole
narrative spine, subject to the exact completion boundary below. No external
textbook is selected for wholesale translation and no second overlapping
computing book is required.

The existing twelve units and all sixty exercises are retained. Completion of
the draft did not determine this choice: root separately compared serious open
alternatives and audited the local source against the actual A30-entry B80
scope. That audit found the original book substantially better on exact versus
floating computation, experiment design, testing, provenance, reproducibility,
and the distinction between computational evidence and proof. It also found
three non-negotiable curricular failures in the current twelve-unit boundary:
it does not actually teach novice Python before using advanced Python, it has
zero SciPy use, and its SageMath bridge is optional and unexecuted.

The selected final architecture is therefore the current original course plus
two compulsory original primer units and bounded in-place SciPy, SageMath,
plotting, mastery, environment, and truth-state repairs. Scientific Python
Lectures, the official Sage Tutorial, Fangohr, RSE with Python, and Mathematical
Python remain technical references/comparators only. Their prose, code,
figures, exercises, and solutions are not part of the selected edition unless a
future component record explicitly admits exact bytes under their own license.

## Controlling curricular boundary

`C:\Users\Floris\Downloads\curriculum.json` defines B80 as an A30-entry course
covering Python, SageMath, SymPy, NumPy/SciPy, exact versus floating
computation, plotting, data, tests, literate notebooks, and reproducible
numerical experiments. Its outcome is to implement mathematical objects and
experiments while distinguishing computation, evidence, and proof.

The course cannot silently assume calculus, linear algebra, differential
equations, or prior programming. Later mathematical examples may remain as
clearly deferred extension routes, but they are not B80 completion evidence.

## Existing twelve-unit witness retained

Read-only root audit of
`C:\Users\Floris\Documents\interlanguage\04_mirrors\id\mathematical-computing-reproducible-experiments-id`
at the selection boundary found:

- twelve Quarto source units, 137,999 bytes and about 17,808 word-like tokens;
- sixty stable exercise IDs; every unit presents five exercises with hints and
  full solutions;
- twelve original Python modules, 102,293 bytes;
- thirteen test files, 71,661 bytes; the current receipt reports 115/115 tests
  passing on Python 3.13.1;
- a JSON-Schema-backed locale-neutral backend with twelve complete unit
  records, twenty-four text/code components, stable section/exercise IDs, and
  ordered relations;
- a current 98-page source-native PDF, 501,936 bytes, SHA-256
  `763008d2bfb37eef6f97398d3bea458f093ffb099e44ce8987bc387eff4146fd`;
- current `BUILD_QA.json`, 10,644 bytes, SHA-256
  `6cf68f308628ff1937567463447d4bf3890f7bb93fc05f7408adf5e841382ae3`;
- current 55-row output manifest covering 2,692,076 bytes, manifest file
  SHA-256
  `608b07d43a01447d9c01f072abab5a24ea0a2c3765e1ccfb8471cb266bf8cb04`;
- source manifest SHA-256
  `85fdf4ce2622f8cf8aa4eaecdd18f47069ed8031ead9f2b2f21af14031c367db`;
- authority manifest SHA-256
  `219a3fa6e0c52f335e08cab3d50b71a37a1c70edd19c526dcc4b5c69ecc5633f`;
  and
- backend catalog SHA-256
  `7d8eb9a3f9fc398e5abea77e517046f5feb37eb3e1197048555d3b9646aa21bf`.

All current reader prose, exercises, figures, data, and code are independently
authored rather than adapted donor expression. Text is CC BY-SA 4.0 and code is
MIT. The reader produces offline HTML and PDF, uses MathML in HTML, carries
license files, records toolchain versions, and has been inspected at desktop
and narrow widths.

This is a real current rendered witness, not a finished curriculum edition.
The owner reported that the final visual receipt, corrected test receipt,
standalone provenance/runtime-license closure, two identical clean builds, and
replacement of stale controls still remain. Its next automatic turn then
failed at the account usage limit. Root does not manufacture final admission
from a successful intermediate build.

## Why the current twelve-unit boundary is incomplete

### A30-entry Python failure

The introduction says Python begins from zero, but Unit 1 immediately uses
imports, objects, keyword arguments, CLI scripts, annotations, `argparse`,
`Path`, JSON, and typed dictionaries. Unit 2 uses comprehensions, generators,
functions, mutation, conditionals, and exceptions without first teaching the
language path that makes them legible. A learner entering only with precalculus
cannot honestly be assumed to infer those concepts from production scripts.

### Missing executable SciPy

There are zero `SciPy` occurrences in the current source/code/test boundary and
SciPy is absent from the environment. B80 explicitly names NumPy/SciPy. The
course's own numerical-method and stability themes make a small, tested SciPy
surface pedagogically necessary rather than a checklist insertion.

### Missing executable SageMath

Unit 5 contains one optional Sage source bridge, generated as a string and not
executed under Sage. Sage is absent from the dependency and QA receipts. B80
explicitly names SageMath, so the final course needs a real local Sage runtime,
objects, exercises, tests, and a separately frozen environment.

### Additional partial gaps

- Unit 4 teaches visualization integrity exceptionally well, but it sends a
  beginner to a production plotting script without progressively teaching
  `fig`/`ax`, plot/scatter/errorbar, labels, units, legends, descriptions, and
  deterministic saving.
- Unit 9 gives strong data/provenance theory but assumes paths, files, CSV,
  JSON, and exceptions; those belong in the novice primer.
- Unit 8 gives strong testing theory but needs one learner-visible red-green
  test workflow before the project suite can count as learner mastery.
- Direct dependencies are pinned, and the build records Python/Quarto/TeX
  versions, but this is not a complete transitive environment lock and there is
  no Sage profile.
- Unit 11 includes B30 quadrature, B40 linear systems, and B70 Euler material.
  Those are useful later extension routes, not A30-entry core requirements.
- The backend's `edition_complete` and pass states must not claim curricular
  completeness before these gaps and final receipts close.

## Exact final course architecture

### Primer P01 — Menjalankan Eksperimen Python

Insert compulsory stable unit `o002.p01` before current Unit 1. Cover local
runtime and terminal, Jupyter/Quarto cells, expressions, names and assignment,
integers/floats/strings/booleans/`None`, operators, function calls, imports,
help, tracebacks, scripts, restart-and-run-all, hidden notebook state, and the
difference between computation and displayed output.

### Primer P02 — Kontrol, Koleksi, Fungsi, Modul, dan Berkas

Insert compulsory stable unit `o002.p02` before current Unit 1. Cover lists,
tuples, dictionaries, sets, indexing/slicing, `if`, `for`, `while`, explicit
loops before comprehensions, `def`, parameters/return/scope, exceptions,
modules and `__main__`, `Path`, text/CSV/JSON files, and one real `unittest`
red-green workflow.

The primer source, code, exercises, tests, outputs, and backend records are
original CC BY-SA 4.0/MIT components. Existing `o002.u01`–`o002.u12` IDs remain
stable; do not renumber them merely because two prerequisite units precede
them.

### Required in-place additions

1. **Unit 4 — plotting construction:** add a progressive learner-facing
   Matplotlib lab from figure/axes creation through plot/scatter/error bars,
   labels, units, legends, accessible descriptions, and deterministic output.
2. **Unit 5 — executed Sage core:** replace the optional-only bridge with a
   compulsory local lab covering `ZZ`, `QQ`, `RR`, `SR`, parents/coercion,
   polynomial rings, exact factorization, solving, and explicit approximate
   conversion. Run and test it under a frozen Sage environment; SageCell or a
   paid/remote service cannot carry the requirement.
3. **Unit 6 — SciPy stability:** add at least one tested comparison between a
   stable `scipy.special` implementation and a naïve expression, with domain,
   conditioning, forward/backward-error, and proof-boundary discussion.
4. **Unit 11 — SciPy A30 route:** compare the original bisection implementation
   with `scipy.optimize.root_scalar(method="bisect")`; record the SciPy version,
   verify bracketing and result, and keep the comparison inside the A30 path.
5. **Unit 11 — later routes:** retain quadrature, linear-system, and Euler
   sections and Exercises 3–5, but visibly gate them behind B30, B40, and B70.
   They are optional reinforcement until those prerequisites exist. The method
   and theorem, bisection, error-source sections, and Exercises 1–2 remain the
   B80 core.

### Minimum additional mastery

- five executable exercises, each with hint/check/full solution, in P01;
- five executable exercises, each with hint/check/full solution, in P02;
- at least two SciPy and two Sage exercises with full solutions and executable
  validation;
- one clean-kernel notebook exercise that fails under hidden state and succeeds
  after restart/run-all;
- one learner-written module with tests; and
- one data-to-plot-to-manifest exercise with accessible static output.

The current sixty exercises remain; do not replace them with the new minimum.

## Environment, build, accessibility, and backend gates

1. Freeze one fully resolved standard Python environment including NumPy,
   SciPy, SymPy, Matplotlib, Jupyter, Quarto integration, testing, and every
   transitive dependency. Record the exact Python, Quarto, Pandoc, LuaHBTeX,
   TeX distribution, OS-independent package identities, and lock hash.
2. Freeze a separate exact Sage release/environment or immutable open container
   digest. Prove the selected Sage lab and tests run locally and bind its
   receipt into the main course manifest.
3. Produce two clean identical source/output manifests after all content
   repairs. Hard-fail missing/extra units, IDs, code, tests, exercises, hints,
   solutions, assets, licenses, and environment receipts.
4. Re-render the entire final PDF and inspect every page; run desktop/narrow
   HTML geometry, keyboard, contrast, local-resource, MathML, link, and console
   checks. Do not call the ordinary LuaLaTeX PDF tagged/accessible unless that
   is separately proven.
5. Add stable backend records for P01/P02, the Sage/SciPy labs, environments,
   exercises, solutions, generated artifacts, and prerequisite-gated Unit 11
   routes. Clear stale completion claims and restore them only after gates pass.
6. Produce HTML, PDF, EPUB, editable source, machine-readable registry, exact
   provenance/licenses, and an offline learner bundle. Generated notebooks may
   supplement the QMD source but hidden-state behavior must be tested.

## Serious alternatives considered

- **Scientific Python Lectures**, exact `main@817a97d8d9a26eeb4e735a402420cd34dd7e89fc`,
  tree `4af72a3d18cf9bfd32ccbf0c1ea099dd4ba65689`, CC BY 4.0,
  is the strongest editable external computational reference: 443 files,
  57 course Markdown files, 194 Python files, 80 exercises and 34 solution
  blocks, with current NumPy/SciPy/Matplotlib/SymPy and CI. It does not supply
  Sage, the coherent proof/evidence/reproducibility progression, or a complete
  solution/mastery layer, and a wholesale translation would duplicate most of
  the selected original course.
- **Official Sage Tutorial 10.9**, exact
  `686dc1a8d420c2e0aabadd4f602d9a0aa4690c50`, selected source path
  `src/doc/en/tutorial/`, provides 23 CC BY-SA 3.0 RST documents and 1,075
  `sage:` doctest prompts. It is the authoritative semantic comparator for the
  executed Sage lab, but it has no structured exercise/solution bank and would
  import far more Sage breadth than B80 needs.
- **Fangohr, Introduction to Python for Computational Science and
  Engineering**, CC BY-NC 4.0, 267 pages/20 chapters, is the strongest
  no-programming-prerequisite prose donor and covers Python, NumPy, SciPy,
  SymPy, plotting, data, and environments. It lacks Sage, systematic testing,
  provenance, experiment protocol, proof/evidence framing, and a complete
  solution layer. Its main value is as a primer comparator; the two bounded
  original primers avoid importing a second overlapping textbook.
- **Research Software Engineering with Python**, exact
  `book@62217e6606842ab9752fcf8e73954d1eb4a3cf07`, CC BY 4.0 text/MIT code,
  has strong testing, automation, configuration, provenance, and 109 keyed
  solutions. It assumes prior Python, uses an obsolete/unlocked build, and
  teaches research software rather than mathematical computing. The selected
  original Units 8–10 already cover its marginal B80 role.
- **Patrick Walls, Mathematical Python**, exact
  `0687916182ab3ddc9e922d4a6eb603609ba91c36`, CC BY-NC-SA 4.0, is rejected as
  a B80 spine because its official prerequisites include differential and
  integral calculus, linear algebra, and differential equations. It has no
  solutions, incomplete exercise sections, an unpinned build, and stale SciPy
  APIs. It remains a later-course comparator only.
- Sundnes, Programming for Computations, Project Pythia, Think Python, the
  Turing RSE course, and old numerical-MOOC material each solve useful subsets
  but either duplicate the selected course, assume the wrong prerequisites,
  lack source/build/solution closure, or omit the mathematical epistemic core.
  ND and proprietary-text alternatives remain ineligible for translation.

The four-layer wholesale Scientific-Python/Sage/RSE/original proposal was
rejected because it would create three overlapping translated books around a
coherent 98-page original course and would still require original integration.
Those sources remain valuable primary references for checking technical
accuracy and exercises; they are not selected reader components.

## Page accounting

The current 98-page original PDF is a selected, exact current rendered witness.
It is added once now and will be **replaced**, not supplemented arithmetically,
by the expanded final O002 render.

- selected core: **15,619** pages;
- separate support: **2,686** pages;
- current-witness teaching package: **18,305** pages;
- selected-corpus working total including the old R012 witness: **18,698** pages;
- rendered universe: **26,265** pages;
- Stage B known core: **4,174** pages.

The final full-curriculum total remains undefined. P01/P02 and the in-place
repairs will change O002 pagination; when the expanded deterministic PDF is
frozen, replace the 98-page witness with that exact count.

## Owner action and release rule

The existing owner must retain all current source and resume in the same task;
no replacement task is created. First correct the backend/control truth state,
then implement P01/P02 and the exact in-place completion boundary. Do not
publish the current draft as a complete B80 edition while the explicit
coverage and receipt gates remain open. A clearly labelled incomplete working
checkpoint may be pushed after its own QA if useful; the complete edition is
pushed immediately when all selected gates pass, without asking Floris for
another confirmation. Every push receives anonymous byte and live-reader
readback.

No upstream message is sent during production. After the entire relevant
corpus, at most one concise, deduplicated, high-confidence issue may be opened,
signed `Codex, on instructions of Floris`.

## Canonical user instruction

The complete file
`C:\Users\Floris\Documents\Obsidian notes\Untitled 1693.md` (10,476 bytes;
SHA-256
`cf913e8cb4d487f4c6958c079b372ccbb2fb5929dd483068441e80cefd6794f2`)
must accompany this handoff verbatim. It is Floris's instruction, not a summary
or permission request.

## Delivery receipt

Root sent one complete message to the existing O002 owner at
`2026-08-22T05:54:29+02:00`. The message contained this selection file in full
and Floris's 10,476-byte canonical `Untitled 1693.md` in full. A direct
readback of turn `01a0279b-05c7-76d0-b622-475baf56ef1a` found the root header,
both begin markers, the canonical end marker, and 28,256 user-message
characters; the task state was `active` / `inProgress`. No new task was
created. This proves delivery, not completion of the selected repairs.
