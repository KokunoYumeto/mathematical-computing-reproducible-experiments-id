# Komputasi Matematis dan Eksperimen yang Dapat Direproduksi

Edisi lengkap Bahasa Indonesia (`id-ID`) untuk peran kurikulum B80 / proyek
O002. Buku ini merupakan karya independen dan tidak menyiratkan dukungan dari
penulis atau lembaga yang dibahas sebagai sumber perbandingan.

- Pembaca HTML: <https://kokunoyumeto.github.io/mathematical-computing-reproducible-experiments-id/>
- PDF dan paket preservasi: <https://doi.org/10.5281/zenodo.22052053>
- Repositori sumber: <https://github.com/KokunoYumeto/mathematical-computing-reproducible-experiments-id>

Ini adalah buku ajar baru yang memperkenalkan pemrograman dan eksperimen
komputasional setelah kompetensi prasyarat A30 (prakalulus). Buku ini tidak
menganggap pembaca telah menyelesaikan kalkulus, aljabar linear, atau persamaan
diferensial.

Sumber edisi memuat dua belas unit yang membentuk satu alur dari representasi
dan bukti sampai proyek akhir yang dapat diperiksa. Setiap unit memiliki kode
yang dapat dijalankan, pengujian, serta lima latihan dengan petunjuk dan solusi
lengkap: 60 latihan, 60 petunjuk, dan 60 solusi seluruhnya. Status penerimaan
pembaca ditentukan oleh `00_control/CURRENT_STATE.md`.

Sumber pembaca berada di `source/`, pengujian di `tests/`, catatan kendali di
`00_control/`, rekaman backend stabil di `backend/`, dan pembaca terbangun di
`output/`. Salinan `docs/` menyediakan bytes HTML yang sama untuk GitHub Pages.

Teks asli proyek dilisensikan dengan CC BY-SA 4.0. Kode asli proyek
dilisensikan dengan MIT. Sumber rujukan/donor mempertahankan lisensi masing-
masing dan tidak otomatis menjadi bagian dari buku ini. Tidak ada bytes donor
yang diadaptasi ke dalam edisi 12-unit saat ini.

Build lokal yang dibekukan memakai Quarto, Python, Jupyter, dan LuaLaTeX:

```text
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
```

Perintah tersebut menjalankan QA sumber, seluruh tes, build HTML/PDF, dua belas
eksperimen, QA pembaca, dan manifest SHA-256. Batas rilis 2026.08.22 lulus
115/115 pengujian dan dua build bersih menghasilkan manifest keluaran 60 berkas
yang identik byte demi byte.
