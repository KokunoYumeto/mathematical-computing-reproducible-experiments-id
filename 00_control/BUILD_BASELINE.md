# O002 final build baseline

Status date: 2026-08-22

Boundary: complete, locally verified, and published 12-unit Indonesian edition.
Curriculum admission remains a separate evidence-based decision.

## Frozen toolchain

- Python 3.13.1
- Quarto 1.9.37
- LuaHBTeX 1.25.7
- MiKTeX 26.5
- `SOURCE_DATE_EPOCH=1787270400`; `FORCE_SOURCE_DATE=1`
- local `o002-frozen` Jupyter kernel; no paid or remote execution service

`output/TOOLCHAIN_QA.json` is 271 bytes with SHA-256
`6e38ac29060b39079c8e80cb0bb75433cb5745ef4c10dff7472b1d09ab4b34e0`.

## Source, tests, backend, and experiments

- Source QA: pass; 12 QMD/code/test triplets; zero errors.
- Assessment: 60 exercises, 60 hints, and 60 full solutions with stable IDs.
- Tests: 115 run; zero failures, errors, skips, or unexpected successes.
- Backend: JSON Schema pass; 12 units; 24 original components; 60 exercises;
  complete references; `last_complete_unit=o002.u12`; `next_unit=null`;
  `edition_complete=true`.
- Backend QA: source, tests, reader build, and PDF visual review are `pass`;
  audio is `not_applicable` because the edition has no audio/widget surface.
- All twelve canonical experiment paths pass. Unit 4 data/figure/alt-text/
  manifest closure and Unit 12 manifest/artifact/claim verification pass.
- Public-byte privacy checks find no local profile path.

Receipts:

- `SOURCE_QA.json`: 96 bytes; SHA-256
  `c0cfb5cc97194d9ea9224013f883a8876a3f8301be9d333c058f11f3da84f47b`.
- `TEST_QA.json`: 290 bytes; SHA-256
  `fd99841678c1d6ab13242747ed2cef33e50a7e9e798f000af02ae8b0c93d56f9`.
- `BUILD_QA.json`: 12,471 bytes; 59 exact other-file receipts; all 17
  checks true; SHA-256
  `af46934b52548503ae915f7ff3a00da385f997680bea8d9869bf0058ed2217be`.

## Reader closure

- Output tree: 60 files, 2,736,794 bytes.
- HTML: 13 Indonesian pages; responsive viewport; 1,007 unique IDs and no
  duplicate; 587 valid local links; 143 valid search entries; 221 runtime
  references across 17 local assets; no external runtime; no missing local
  target or fragment.
- Mathematics: 229 native MathML elements (34 block, 195 inline) and no
  MathJax/KaTeX/CDN dependency.
- Responsive containment covers tables, preformatted code, and block MathML.
- Browser QA at 390 x 844 found document client/scroll width 375/375 and no
  page overflow; the Unit 12 wide table remains inside a 324-pixel scrolling
  container. At 1440 x 900, document client/scroll width is 1425/1425 and the
  749-pixel main column is centered at 712.44 pixels in the client area.
- Standalone rights/provenance package includes text and code licenses,
  third-party boundaries, runtime inventory and MIT terms, the full local
  Apache-2.0 text for Fuse.js, `backend/catalog.json`, and
  `00_control/SOURCE_SELECTION.md`.

## PDF visual QA

- File: `output/Komputasi-Matematis-dan-Eksperimen-yang-Dapat-Direproduksi.pdf`
- 502,373 bytes; 98 letter-size pages; PDF 1.5; no encryption, form, or
  JavaScript.
- SHA-256:
  `289e744aeef09eb6e546c002e0782a346519a39c5265ae4ef5c9d1e3ce095376`.
- Creation and modification timestamp: 2026-08-21 02:00:00 local time,
  fixed through the build epoch.
- All 98 pages rendered at 120 dpi and inspected through seven contact sheets;
  pages 8, 9, 12, 68, and 93-98 also inspected individually. No clipping,
  overlap, collision, broken glyph, unintended blank content page, or bad
  density remained.
- Visual receipt: 751 bytes; SHA-256
  `a51fb79f7fdd0f5e6a42eee4b70fd72778ddd6fa0259a361ebd2afe31e530bca`.
- Render manifest: 105 rows (98 pages and 7 contact sheets); 12,160 bytes;
  SHA-256
  `9a66e23f5dbdd4d886ed88b4431f5f947023aef4b8ff2aaf289ffdf77b742bd6`.

## Manifests and deterministic pair

- Authority: 402 rows; manifest 83,844 bytes; SHA-256
  `219a3fa6e0c52f335e08cab3d50b71a37a1c70edd19c526dcc4b5c69ecc5633f`.
- Source: 70 rows; manifest 6,975 bytes; SHA-256
  `ff105624a08a78cf1552b0f9044f4b6bd6a93f14a8d245c17d955d27fcdb88d0`.
- Output Build A witness: 60 rows; 6,507 bytes; SHA-256
  `e2108333ac3121137b28646d19f087b07b96178eab34c24a504e1dcdeb7d78f5`.
- Output Build B/current: the same 60 rows and raw bytes, with the same SHA-256.
- Every manifest row matches the current path, byte count, and SHA-256. No
  undeclared output file exists. The build lock and `BUILD_IN_PROGRESS` marker
  are absent.
- Canonical output-tree signature:
  `70ba8f9a758582991f25915de6ca602f890d61444c9cc381f00a560c1cddbf97`.
  It is SHA-256 over a 6,488-byte UTF-8 stream with no BOM or trailing LF:
  recursively enumerate the 60 regular files under `output/`; represent each
  as `path,bytes,sha256` using the lane-root-relative POSIX path, decimal byte
  count, and lowercase raw-file SHA-256; sort by path in Unicode code-point
  order; then join records with one LF.

## Rights and release status

Current Units 1-12 contain no donor bytes. Original text is CC BY-SA 4.0;
original code is MIT; bundled runtime components retain their upstream terms.
The accepted bytes are published at GitHub release `v2026.08.22`, GitHub Pages,
and DOI `10.5281/zenodo.22052053`; public-byte readback passed. The sanitized
details are in `00_control/PUBLICATION_RECEIPT.json`. No upstream author was
contacted. This baseline proves edition completion and publication only and does
not admit the work to the 40-course curriculum.
