# O002 current state

Status date: 2026-08-22

Status: selected B80 architecture in production

Branch: `codex/b80-final-architecture`

## Preserved historical boundary

The independently authored 12-unit edition remains complete, verified, and
published as GitHub tag `v2026.08.22` and Zenodo DOI
`10.5281/zenodo.22052053`. Its 60 exercises, 115/115-test receipt, 98-page PDF,
offline HTML, manifests, and public-byte receipt remain valid. That release is
an immutable historical witness and is not being withdrawn or rewritten.

## Live selected curriculum truth

The curriculum coordinator independently selected this original narrative
spine for B80, but only under the exact 14-unit completion architecture in
`FINAL_ARCHITECTURE_HANDOFF.md`. The selected B80 curriculum is therefore
**not complete** at the published 12-unit boundary.

The backend is now `o002.backend.v2` and explicitly records:

- `standalone_edition_complete: true`;
- `b80_curriculum_complete: false`;
- 12 of 14 selected units currently admitted;
- next unit `o002.p01`;
- P01/P02, Unit 4 plotting, Unit 5 local Sage, Unit 6/11 SciPy, Unit 11
  prerequisite deferral, resolved environment locks, expanded formats,
  determinism, accessibility, and final receipts as open requirements; and
- Units 4, 5, 6, and 11 as `repair_required` for the selected architecture.

The exact generated backend is 22,863 bytes with SHA-256
`92cdbd1864a79be524018eb6fcdbf2a46b76f0b3b32373fb7a855f5f5357fc17`;
Draft 2020-12 JSON Schema validation passes. This is a truth-correction
checkpoint, not a final reader build.

## Rights and next action

Current and planned reader expression is original CC BY-SA 4.0; original code
is MIT. External works remain comparison authorities only and no donor bytes
are admitted. No upstream author has been contacted.

Next executable action: admit P01 contiguously with its QMD, code, tests, five
exercise/hint/check/solution sets, result artifact, backend records, source QA,
and a pushed verified checkpoint. P02 follows immediately. Released Pages stay
on the immutable historical reader until a later expanded boundary itself
passes its release gates.
