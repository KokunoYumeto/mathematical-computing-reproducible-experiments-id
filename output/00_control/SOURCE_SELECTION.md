# O002 source selection and bounded donor policy

Status date: 2026-08-22

## Decision

The curriculum coordinator independently selected this O002 coursebook as the
sole B80 narrative spine under the exact 14-unit architecture recorded in
`FINAL_ARCHITECTURE_HANDOFF.md`. No external work is selected wholesale and no
second overlapping computing book is required. The selection rests on a
separate source/coverage audit, not on sunk work or the prior release.

The preserved 12-unit release and the live 14-unit source are wholly original.
They contain no adapted donor prose, exercises, figures, data, or code. Text is
CC BY-SA 4.0 and code is MIT. P01/P02 and the selected in-place repairs are also
original. Completion does not convert a comparator into a component; future
donor bytes must be declared, licensed, attributed, and reviewed before
admission.

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
  complete B80 spine. No SPL bytes enter the live 14-unit source. Its
  exact archive and component manifest would have to be frozen before any
  adaptation in a later revision.

Potential later-revision boundary: introductory Python language, NumPy arrays,
Matplotlib, and bounded SciPy/SymPy material. Advanced application-package
chapters remain out of scope. The live source instead supplies original
Python/NumPy/plotting treatment and does not reproduce overlapping treatment
from Mathematical Python.

### Introduction to Python for Computational Science and Engineering

- Official author page and repository: Hans Fangohr,
  `fangohr/introduction-to-python-for-computational-science-and-engineering`.
- Citable edition DOI: `10.5281/zenodo.1411868`; official reader identifies the
  work as a beginner-facing Python 3 book for computational science and
  engineering.
- Rights: CC BY-NC 4.0.
- Source surface: editable Jupyter notebooks with official HTML and PDF
  renders; later chapters cover NumPy, SciPy, SymPy, plotting, data, and
  environments.
- Curricular disposition: comparison-only primer authority. It is strong for
  learners without prior programming, but does not provide the complete
  testing, provenance, experiment-design, proof/evidence, SageMath, or
  solution spine required by B80. No Fangohr bytes enter this edition.

### Official Sage Tutorial 10.9

- Official repository authority: SageMath source commit
  `686dc1a8d420c2e0aabadd4f602d9a0aa4690c50`, selected path
  `src/doc/en/tutorial/`.
- Surface: 23 RST documents and 1.075 `sage:` doctest prompts.
- Rights: CC BY-SA 3.0 for the selected tutorial documentation.
- Curricular disposition: authoritative semantic comparator for the bounded
  executed Sage lab. Its prose and doctests are not copied or adapted, and its
  breadth is not substituted for the two B80 mastery exercises.

## Rejected wholesale alternatives

- Sundnes, *Introduction to Scientific Programming with Python*: coherent and
  beginner-friendly under CC BY 4.0, but its repository lacks a root component
  manifest, names missing build scripts, has unpinned dependencies and dynamic
  dates, and generated notebooks acknowledge ordering inconsistencies.
- Berkeley *Python Numerical Methods*: software is MIT, but the textbook prose
  is not an open translation source.

## Original connective material in the selected architecture

The selected 14-unit architecture supplies the coherent progression absent
from every candidate: exact versus floating arithmetic;
object/representation/output distinctions;
experiment questions and controls; random seeds; tolerances and error budgets;
invariants and falsification; visualization integrity; canonical artifacts and
hashes; testing and validation; environments, configuration, provenance, and
automation; a compulsory locally executed SageMath core; and the boundary
between computational evidence, counterexample, and proof.

## Self-study closure and remaining limits

Scientific Python Lectures distributes exercises across tutorials; Mathematical
Python has no solutions and unfinished exercise sections; RSE has strong
solutions but teaches software practice rather than mathematical computation.
O002 therefore supplies its own continuous stable-ID assessment spine: five
exercises, five hints, and five full solutions in every unit. The fifteen new
mastery exercises also have executable checks, and the capstone is verifiable.
The reader packages local web runtime assets,
accessible descriptions, a frozen build environment, provenance receipts, and
capstone review criteria. Installation of the declared open-source numerical
stack remains a local prerequisite. SageMath is a compulsory course surface
with its own frozen local environment and executable receipt; it is not a
remote-service or optional-runtime substitute.
