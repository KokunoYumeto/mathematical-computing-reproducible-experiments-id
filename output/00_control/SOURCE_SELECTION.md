# O002 source selection and bounded donor policy

Status date: 2026-08-22

## Decision

O002 remains an independently authored Indonesian coursebook. No examined work
is an admissible wholesale spine for the B80 role. This decision was reached
from prerequisite, coverage, rights, source-closure, exercise, and build
evidence; completion of O002 is not evidence for its later admission into the
40-course curriculum. Edition completion and curriculum admission are separate
decisions.

The complete current reader, Units 1-12, is wholly original. It contains no
adapted donor prose, exercises, figures, data, or code. Text is CC BY-SA 4.0
and code is MIT. Completion of this edition does not convert any comparison
source into a component. Future donor-derived components must be declared,
licensed, attributed, and reviewed separately before admission to a later
revision.

## Frozen primary authorities

### Mathematical Python

- Official repository: `patrickwalls/mathematicalpython`.
- Commit: `0687916182ab3ddc9e922d4a6eb603609ba91c36`.
- Tree: `b66a9c79aa7144a75d3f83ba53bba4ff8961f91b`.
- Commit archive: 3,251,649 bytes; SHA-256
  `0cf19ebb4e93197e9d7892d7b814d7dcfd3a5632f188a4a1da6da47e47d656bc`.
- Closure: 42 files, 4,239,044 uncompressed bytes; 31 Jupyter notebooks.
- Rights: CC BY-NC-SA 4.0 blanket notice, with separate or unresolved rights for
  bundled Highlight.js material and two local images.
- Exercise surface: 69 numbered exercises plus seven larger prompts; no answer
  key; seven exercise sections are only “Under construction.”
- Build: not reproducible as frozen. Dependencies are unpinned, current time is
  injected, subprocess failures are ignored, and external assets remain.
- Curricular disposition: later numerical donor only. The official reader
  explicitly assumes differential and integral calculus, linear algebra, and
  differential equations, so it cannot launch B80 from A30.

Potential later boundary: selected numerical applications in root finding,
quadrature, differentiation, differential equations, and linear algebra only
after the corresponding mathematics prerequisites. Introductory Python,
NumPy, and plotting material is not selected because it overlaps the stronger
A30-facing donor. Any adapted component remains CC BY-NC-SA 4.0 and separate
from original O002 CC BY-SA text.

### Research Software Engineering with Python

- Official repository: `merely-useful/py-rse`.
- Branch: `book`.
- Commit: `62217e6606842ab9752fcf8e73954d1eb4a3cf07`.
- Tree: `f570f30bb8ace202550c474e81eb3414e8976be5`.
- Commit archive: 20,728,265 bytes; SHA-256
  `840b78f1f0d8e5520126a25a8152cd198fc867042df08827158bcb44cf482e56`.
- Closure: 358 files, 27,261,558 uncompressed bytes; 27 R Markdown files.
- Rights: CC BY 4.0 text and MIT code, with separately governed/excluded
  publisher material, comic, screenshots, cover photography, adapted upstream
  lessons, and Project Gutenberg data.
- Exercise surface: 110 prompts/checklists, 109 matching solutions. The
  project-structure, local Git, automation, configuration, testing, and
  provenance pool contains 41 solution-backed exercises.
- Build: not reproducible as frozen. The Makefile names missing `CONDUCT.md`,
  dependencies are unpinned, no environment lock is present, and one final
  sample test file has an `IndentationError`.
- Curricular disposition: bounded reproducibility/software-practice donor,
  never the mathematical-computing spine.

Selected conceptual boundary for later adaptation: project structure;
`git-cmdline` commit-message/changes/history/restore/ignore; the automation
sequence from single-file dependencies through pipelines; configuration
formats/command-line/job files; testing assertions/unit/integration/regression/
coverage/TDD; and provenance environment/steps/scripts/inspectability. GitHub
UI, obsolete CI, publisher assets, screenshots, and the bundled novel corpus
are excluded.

### Scientific Python Lectures

- Official repository: `scipy-lectures/scientific-python-lectures`.
- Comparison commit: `817a97d8d9a26eeb4e735a402420cd34dd7e89fc`.
- Rights: CC BY 4.0.
- Source/build surface: editable Markdown/Jupyter Book, notebooks, exercises,
  solutions, data, tests, Make targets, and CI.
- Curricular disposition: strongest A30-facing comparison donor, but not a
  complete B80 spine. No SPL bytes enter the completed current edition. Its
  exact archive and component manifest would have to be frozen before any
  adaptation in a later revision.

Potential later-revision boundary: introductory Python language, NumPy arrays,
Matplotlib, and bounded SciPy/SymPy material. Advanced application-package
chapters remain out of scope. The current edition instead supplies original
Python/NumPy/plotting treatment and does not reproduce overlapping treatment
from Mathematical Python.

## Rejected wholesale alternatives

- Sundnes, *Introduction to Scientific Programming with Python*: coherent and
  beginner-friendly under CC BY 4.0, but its repository lacks a root component
  manifest, names missing build scripts, has unpinned dependencies and dynamic
  dates, and generated notebooks acknowledge ordering inconsistencies.
- Fangohr, *Introduction to Python for Computational Science and Engineering*:
  valuable beginner numerical donor, but CC BY-NC 4.0 and still missing the
  full provenance, experiment-design, and proof/evidence progression.
- Berkeley *Python Numerical Methods*: software is MIT, but the textbook prose
  is not an open translation source.

## Original connective material delivered

The completed edition supplies the coherent progression absent from every candidate: exact
versus floating arithmetic; object/representation/output distinctions;
experiment questions and controls; random seeds; tolerances and error budgets;
invariants and falsification; visualization integrity; canonical artifacts and
hashes; testing and validation; environments, configuration, provenance, and
automation; a small Sage-compatible exact-computation bridge; and the boundary
between computational evidence, counterexample, and proof.

## Self-study closure and remaining limits

Scientific Python Lectures distributes exercises across tutorials; Mathematical
Python has no solutions and unfinished exercise sections; RSE has strong
solutions but teaches software practice rather than mathematical computation.
O002 therefore supplies its own continuous stable-ID assessment spine: five
exercises, five hints, and five full solutions in every unit, plus executable
checks and a verifiable capstone. The reader packages local web runtime assets,
accessible descriptions, a frozen build environment, provenance receipts, and
capstone review criteria. Installation of the declared open-source numerical
stack remains a local prerequisite; Sage is an optional bridge rather than a
required runtime.
