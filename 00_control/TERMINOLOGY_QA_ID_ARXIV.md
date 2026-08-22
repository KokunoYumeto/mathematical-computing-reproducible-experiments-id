# Indonesian field-terminology QA — arXiv TeX witness

Date: 2026-08-22
Result: pass; no reader-wide term replacement justified

## Source identity and reproducible source check

- A.B. Mutiara, *Analisis Kinerja Sistem Cluster Terhadapa Aplikasi Simulasi
  Dinamika Molekular NAMD Memanfaatkan Pustaka CHARM++* (title preserved as
  deposited), arXiv:0807.4609v1, submitted 29 July 2008.
- Official record: <https://arxiv.org/abs/0807.4609>
- Official v1 source: <https://arxiv.org/src/0807.4609v1>
- Downloaded source archive: 155,496 bytes; SHA-256
  `80c2f414b9269d15aaf92db71e7b355ff96301a18e7fc5dbe67d7dbbdc86241c`.
- Inspected TeX member: `paper_abm_knsi_2008.tex`, 31,672 bytes; SHA-256
  `79d96864286223614ec257e42b32811b3b53fcf7075626c726ed1d08495e5a15`.

The paper is a real Indonesian TeX source in scientific and parallel
computing, with numerical molecular-dynamics simulation. It is sufficiently
close to O002 to witness field usage, but it is dated and narrower than the
course. It is therefore evidence of usage, not a sole prescriptive authority.
No prose, code, figure, or data from the paper is incorporated into the
edition; its source license is not treated as permission for adaptation.

## Actual TeX evidence and decisions

Line numbers refer to the exact TeX hash above.

| TeX evidence | Edition convention | Decision |
|---|---|---|
| `komputasi`, `pustaka` (21, 26) | `komputasi`, `pustaka` | Confirmed. |
| numerical equation phrasing (129–131) | `metode numerik`, `secara numerik` | Confirmed. |
| `file masukan`; `masukan dan keluaran` (152, 173–174) | `berkas`; `masukan/keluaran` | Keep modern Indonesian `berkas`; retain API/file literals unchanged. |
| `langkah waktu` (189–191) | `langkah waktu` | Confirmed. |
| `nilai rata-rata` (242–244, 331) | `rata-rata` | Confirmed. |
| `waktu sekuensial`, `waktu paralel` (345–352) | `sekuensial`, `paralel` | Confirmed. |
| `efisiensi paralel` (442–459) | `efisiensi paralel` | Confirmed where the concept occurs. |
| `faktor acak`, `ongkos komunikasi` (541–560) | `faktor acak`; prefer `biaya komunikasi` in new prose | Meaning confirmed; `biaya` is the neutral editorial form. |
| `waktu pemrosesan`, ratio of communication to computation (619, 646–649) | `waktu pemrosesan`; `rasio komunikasi terhadap komputasi` | Confirmed with a grammatical normalization. |
| `algoritma paralel`, `skalabilitas`, `ukuran masalah` (652–655) | `algoritme paralel`, `skalabilitas`, `ukuran masalah` | Keep the edition's established formal `algoritme`; other terms confirmed. |
| dated `tehnik` and `analisa` (33–34, 81–83) | `teknik`, `analisis` | Do not regress to dated/nonstandard spellings. |

## Corpus check and disposition

A bounded search of reader-facing Markdown/QMD found 26 occurrences of
`algoritme` and none of `algoritma`, 11 occurrences of `analisis` and none of
`analisa`, 56 occurrences of `berkas`, 68 of `masukan`, 86 of `keluaran`, 23
of `pustaka`, and 29 of `komputasi`. The three reader-source occurrences of
the English token `file` are intentionally inside a PowerShell option, a
Python traceback, and a literal example path.

The witness confirms the course's main mathematical-computing vocabulary.
Every difference is either a deliberate modern/formal normalization or a
literal programming surface. Consequently no change to the 14-unit reader,
exercise bank, code, or backend is warranted. `GLOSSARY_ID_ID.md` now makes
the decision durable for later editions and locales.

## Provenance disclosure

`README.md` contains the exact model disclosure **OpenAI Codex gpt-5.6-sol,
Ultra**, states that the work was performed at the user's direction, and
explicitly preserves author, source, rights-holder, and human-contributor
attribution. This QA does not change any source or contributor credit.
