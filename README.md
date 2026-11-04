# Komputasi Matematis dan Eksperimen yang Dapat Direproduksi

Buku ajar Bahasa Indonesia yang memperkenalkan pemrograman dan eksperimen komputasional dalam matematika setelah
prakalkulus: dua primer wajib dan dua belas unit utama, 75 latihan dengan petunjuk, jawaban, dan solusi lengkap, serta
lab Python, SciPy, dan SageMath yang berjalan secara lokal, sebagai pembaca HTML, PDF, dan EPUB. Buku ini tidak
mengandaikan kalkulus, aljabar linear, atau persamaan diferensial.

[Baca daring](https://kokunoyumeto.github.io/mathematical-computing-reproducible-experiments-id/) ·
[PDF](https://github.com/KokunoYumeto/mathematical-computing-reproducible-experiments-id/releases/download/v2026.08.22.1/00-b80-id.pdf) · [EPUB](https://github.com/KokunoYumeto/mathematical-computing-reproducible-experiments-id/releases/download/v2026.08.22.1/03-b80-id.epub)

## Cara pembuatan

Buku ini ditulis oleh AI: OpenAI Codex gpt-5.6-sol, Ultra, sebagai karya baru untuk kursus B80
[Program Matematika Indonesia](https://kokunoyumeto.github.io/program-matematika-indonesia/id/#course-B80). Build lokal
memverifikasi lingkungan Python dan SageMath yang dikunci, menjalankan pemeriksaan sumber, seluruh tes, ke-14 permukaan
eksperimen, build HTML/PDF/EPUB, pemeriksaan pembaca, dan manifes SHA-256. Untuk edisi 14-unit, 177 tes dan 7/7 uji
Sage lulus, PDF diperiksa halaman demi halaman, dan dua build bersih menghasilkan manifes yang identik byte demi byte
([status](00_control/CURRENT_STATE.md)). Edisi format PDF, LaTeX, dan EPUB tanggal 3 Oktober 2026 dibuat oleh OpenAI
Codex GPT-6 Astra (Ultra) dari teks yang sama; EPUBCheck 5.4.0 tidak menemukan kesalahan atau peringatan, dan
eksperimen Python/Sage tidak dijalankan ulang untuk edisi itu.

## Status

Edisi lengkap 14-unit, versi 2026.08.22.1. Rilis 12-unit `v2026.08.22` tetap tersedia sebagai edisi historis yang
tidak berubah. Masih mungkin ada kesalahan.

## Isi

- [Rilis v2026.08.22.1](https://github.com/KokunoYumeto/mathematical-computing-reproducible-experiments-id/releases/tag/v2026.08.22.1): edisi format (PDF 135 halaman, LaTeX kumulatif, sumber dan skrip reproduksi, EPUB) dan
  berkas rilis pertama (PDF 159 halaman, EPUB, sumber Quarto dan backend yang dapat disunting, paket luring);
  [rilis 12-unit v2026.08.22](https://github.com/KokunoYumeto/mathematical-computing-reproducible-experiments-id/releases/tag/v2026.08.22).
- `source/`: sumber pembaca (Quarto); `tests/`: pengujian; `backend/`: rekaman stabil; `output/` dan `docs/`: pembaca
  terbangun (situs Pages diterbitkan dari pohon rilis yang telah diverifikasi); `00_control/`: catatan kendali.
- Istilah utama: [glosarium id-ID](GLOSSARY_ID_ID.md) dan
  [pemeriksaan terminologi terhadap sumber TeX berbahasa Indonesia](00_control/TERMINOLOGY_QA_ID_ARXIV.md).

Ikuti [panduan penyiapan lokal](index.qmd#sec-o002-setup) sebelum menjalankan eksperimen. Build lokal memakai Quarto,
Python, Jupyter, dan LuaLaTeX:

```text
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Mode Candidate
```

## Sumber dan atribusi

- Karya independen; sumber rujukan dan pembanding tercantum di [THIRD_PARTY.md](THIRD_PARTY.md). Tidak ada teks, kode,
  atau data dari sumber itu yang diadaptasi ke dalam buku, dan buku ini tidak menyiratkan dukungan dari penulis atau
  lembaga yang dirujuk.
- Komponen runtime pembaca mempertahankan lisensinya sendiri ([RUNTIME-LICENSES.md](RUNTIME-LICENSES.md)).

## Lisensi

Teks tersedia menurut CC BY-SA 4.0 ([LICENSE-TEXT.md](LICENSE-TEXT.md)); kode asli menurut MIT
([LICENSE-CODE.md](LICENSE-CODE.md)).
