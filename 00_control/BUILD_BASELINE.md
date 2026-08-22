# O002/B80 expanded-release build baseline

Status date: 2026-08-22  
Release version: `2026.08.22.1`  
Git tag: `v2026.08.22.1`  
Reserved Zenodo DOI: `10.5281/zenodo.22053905`  
Historical release preserved: `v2026.08.22`; DOI `10.5281/zenodo.22052053`

This baseline replaces the obsolete 12-unit/115-test/98-page build witness.
It freezes the complete 14-unit reader and the receipts that must be present at
both final-build boundaries. It does not claim that publication has already
occurred or that the two final manifests are identical before those checks are
actually run.

## Selected reader boundary

- Fourteen stable units: compulsory `o002.p01` and `o002.p02`, followed by
  unchanged `o002.u01` through `o002.u12`.
- Seventy-five exercises. The retained sixty have hints, answers, and complete
  solutions; fifteen new mastery exercises also have executable checks.
- Unit 4 includes progressive accessible Matplotlib and data-to-plot-to-manifest
  work. Unit 5 includes a compulsory locally executed SageMath lab. Units 6 and
  11 include tested SciPy work. Unit 11 keeps its bisection path in A30 and
  visibly gates B30/B40/B70 extensions.
- Original reader text is CC BY-SA 4.0 and original code is MIT. Runtime
  components retain their own licenses. Comparator books contribute no reader
  bytes to this release.

## Frozen toolchains and executable evidence

- CPython 3.13.1; Quarto 1.9.37; Pandoc 3.8.3; LuaHBTeX 1.25.7; MiKTeX 26.5.
- `SOURCE_DATE_EPOCH=1787270400`; `FORCE_SOURCE_DATE=1`; local
  `o002-frozen` Jupyter kernel; no paid or remote execution service.
- Toolchain receipt: `output/TOOLCHAIN_QA.json`, 407 bytes, SHA-256
  `772cfad4316293b69981a24c154054b3824cbe2c1d5aa8e61e2f4d8d93fab393`.
- Resolved Python profile: 95 packages. Lock: 1,846 bytes, SHA-256
  `28d1f9a5d2b341628fbc5e182ca523da1cfa33473e5714493f8ca18893c31d9a`.
  Receipt: 17,231 bytes, SHA-256
  `6cff49e768dcb06752191d821e2577c45856313245af6f701f4ab05e2bc56918`.
- Separate local Sage profile: Ubuntu 22.04, SageMath 9.5, 1,064 dpkg
  packages. Lock: 34,181 bytes, SHA-256
  `bbd7f235834660681327b975a816b71aabd6d31946e6c875bf55d06224a5d802`.
  Receipt: 575 bytes, SHA-256
  `5fe62bee0260a17d7f44e488cd58312a7c4b3894ac93a09af837b18273194451`.
- Source QA passes 14 QMD/code/test triplets with zero errors. Receipt:
  96 bytes, SHA-256
  `21aa8027ac6bf524c1dbabc89183dfbb36fbb7dbfa7194cd14d7c7e3c34bb3b9`.
- Python suite: 177 run; zero failures, errors, skips, expected failures, or
  unexpected successes. Receipt: 290 bytes, SHA-256
  `b638859fc58dfc021b5ee547fa947ac60c0a5bf137f90153e562a41dea1922d4`.
- Local Sage lab: 7/7 passing; result SHA-256
  `3b1a401d81985124804e6fb536020fb542acdfea6a635e500f0f3bbe72593b78`.

## Reader formats and accessibility receipts

- HTML: 15 offline Indonesian pages, 1,355 checked links, 272 native MathML
  elements, one described/captioned figure, and no external runtime resource.
  Static receipt: 6,755 bytes, SHA-256
  `f5639c1e151b2a338bde8a9d468f22378acef6b1cd4a70ede7d3402f4d1be03a`.
- Browser QA passes at 1440 x 900 and 390 x 844. The desktop reader exactly
  fills the 800-pixel body track between the two 250-pixel navigation columns,
  with zero overlap. The narrow document is 375/375 client/scroll pixels;
  code wraps, the 1,448-pixel plot scales to 324 pixels, and intentional table
  overflow is confined to labelled keyboard-focusable regions. Enter and Space
  toggle disclosure state, focus is visible, console errors/warnings are zero,
  and measured text/link contrast is at least 4.5:1. Browser receipt:
  `00_control/HTML_BROWSER_QA.json`, 2,886 bytes, SHA-256
  `015e2ecdd9ddec77b3cc7a4af6f992fe60175425520ba830b1d711483cc7efee`.
- EPUB: 291,212 bytes, SHA-256
  `8e9e35dd54be8524a8b7752df0a7285749db4c80fc5a10271eb841c01c0c748d`;
  17 XHTML spine documents and 272 MathML elements. EPUB QA receipt:
  1,316 bytes, SHA-256
  `d49073419637cc6ae99778c08220fa7987bbf432d4c43d458cc7d046c3317864`.
- PDF: 754,845 bytes; 159 letter-size pages; SHA-256
  `f9d3df201c03107be3a3e6f61dd6798485cf20bc35ae14f2911ab212789b5038`.
  Every page was rendered at 120 dpi and reviewed through all ten contact
  sheets plus selected full-size detail pages. The review found no clipping,
  collision, missing glyph, unintended blank content, or unacceptable density.
  PDF visual receipt: 728 bytes, SHA-256
  `4599c9b7c41ef614646d13d5fe7af4310518e4eb07f0c5211312e5aaceedadb2`.
  The PDF is not represented as tagged/accessible.

## Final-build and release gates

The backend must remain `b80_curriculum_complete=false` until the browser,
PDF, EPUB, bundle, and two-build receipts all validate. The release process
must create deterministic editable-source and offline-reader ZIPs, reach a
catalog/bundle fixed point, and then run Final A and Final B from the same
frozen source. Their complete source and output manifests must be byte-identical
before publication. The five release assets are the landing-page HTML, PDF,
EPUB, editable-source ZIP, and offline-reader ZIP.

Zenodo record `22053905` is the authorized new version under concept DOI
`10.5281/zenodo.22052052`; its public artifact bytes must be anonymously read
back and hashed. GitHub publication targets the existing repository and Pages
lineage, but is temporarily deferred while the user's GitHub account is under
support review. That external account state does not delay Zenodo maintenance.
No upstream author is contacted.
