# O002 current state

Status date: 2026-08-22

Status: complete 14-unit B80 edition; GitHub, Zenodo, and Figshare public;
Indonesian field-terminology QA complete

Branch: `codex/b80-final-architecture`

## Preserved historical boundary

The independently authored 12-unit edition remains complete, verified, and
published as GitHub tag `v2026.08.22` and Zenodo DOI
`10.5281/zenodo.22052053`. Its public bytes are immutable and are not being
withdrawn or rewritten.

## Complete selected curriculum boundary

All fourteen selected units are now admitted: compulsory original primers
`o002.p01` and `o002.p02`, followed by stable retained IDs `o002.u01` through
`o002.u12`. The course contains 75 exercises: the retained 60 have hints,
answers, and complete solutions; the 15 new mastery exercises additionally
have executable checks. Unit 4 now teaches progressive accessible plotting,
Unit 5 executes a frozen local SageMath lab, Units 6 and 11 execute SciPy, and
Unit 11 keeps the A30 bisection route separate from prerequisite-gated
B30/B40/B70 extensions.

The resolved Python and Sage environments, executable lab receipts, source
closure, comparator/rights inventory, and backend schema checks pass. The
learner-facing setup path, P01 prerequisite ordering, Unit 11 route membership,
archive-receipt graph, final-mode completion guard, and responsive overflow
surfaces were repaired after independent audit.

All 177 tests pass and Sage passes 7/7. The HTML reader has 15 pages, 1,355
verified links, and 272 MathML expressions; EPUB has 17 XHTML documents and
272 MathML expressions. The 159-page PDF was inspected page by page. Desktop
and narrow browser geometry, keyboard interaction, contrast, local-resource
closure, responsive tables/code/figures, console state, and accessible
descriptions pass. Two final clean builds have byte-identical source and output
manifests. The current backend is 110,511 bytes with SHA-256
`447a7ae670a8232a08b24db4ab6288df6f0c3b4d46462206b173830fc55c085d`;
it records `b80_curriculum_complete: true`.

## Complete public preservation

Zenodo version `2026.08.22.1` is public in the existing concept lineage as
record `22053905`, DOI `10.5281/zenodo.22053905`, under concept DOI
`10.5281/zenodo.22052052`. Its title and metadata are clean, its record-level
license is CC BY-SA 4.0, and its inventory is exactly five artifacts: HTML,
PDF, EPUB, editable-source ZIP, and offline-reader ZIP. Anonymous download and
SHA-256 readback pass for every file. Durable receipt:
`00_control/PUBLICATION_RECEIPT_FINAL.json` (2,747 bytes; SHA-256
`9dadaec2091ef382b1d55dbd98a848ec06b641b347efc683fbad9724e4c793cf`).

The restored existing GitHub repository is public. Annotated tag
`v2026.08.22.1` targets accepted release commit
`73b809aabd99957453065b0c4884f33a4cf445cb`; its release exposes the exact
five artifacts totaling 3,014,210 bytes. Pages serves 85 paths totaling
4,046,273 bytes from `main:/docs`, with tree SHA-256
`2afb80554d34d35ce889702109e7a2bd908f9c69bde3bc5e5a34fcb8a2c775b2`.
Anonymous hash readback passes for every release asset and Pages path. Durable
receipt: `00_control/GITHUB_PUBLICATION_RECEIPT.json` (3,420 bytes; SHA-256
`5afc69701c84914b0959d2d3bfcec9197ad67ae041187b0303bb2e56a9bd0fcb`).

Figshare canonical item `33314796` is public as version 2, DOI
`10.6084/m9.figshare.33314796.v2`. Its reader-first payload contains seven
files totaling 2,981,079 bytes: the 159-page PDF first, EPUB, offline reader,
editable source, license notice, manifest, and checksums. Anonymous SHA-256
readback passes for all seven. Because Figshare cannot express the mixed
license exactly, public metadata states that its CC0 label applies only to
descriptive metadata; the files retain CC BY-SA 4.0 text, MIT code, and
per-component runtime terms. The earlier zero-file item `33314742` is retained
only as a supersession pointer and is absent from project `280296` and the
Indonesian collection. The canonical item is present in both; the collection
readback is version 36, DOI `10.6084/m9.figshare.c.8668413.v36`. Durable
receipt: `00_control/FIGSHARE_PUBLICATION_RECEIPT.json` (3,803 bytes; SHA-256
`0eaffa05546177cdebbd82e0bdcc1ebadf75e1702b1c11390b5049f3d1abfa92`).

## Final terminology and provenance boundary

The official source archive for Indonesian arXiv:0807.4609v1 was downloaded,
unpacked, and its actual TeX inspected as a bounded scientific-computing usage
witness. It confirms the course's central `komputasi`, `pustaka`,
`masukan/keluaran`, numerical, sequential/parallel, and scalability terms.
Differences are deliberate formal/modern choices (`teknik`, `analisis`,
`berkas`, `algoritme`), so no reader-wide replacement is justified. The exact
source identity, hashes, TeX line evidence, and decision are in
`00_control/TERMINOLOGY_QA_ID_ARXIV.md`; `GLOSSARY_ID_ID.md` fixes the chosen
conventions. README carries the exact disclosure `OpenAI Codex gpt-5.6-sol,
Ultra` and explicitly preserves author, source, rights-holder, and human-credit
relationships. No upstream author has been contacted. No publication,
curriculum, QA, terminology, or provenance gate remains open.
