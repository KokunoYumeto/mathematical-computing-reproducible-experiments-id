# Komputasi Matematis dan Eksperimen yang Dapat Direproduksi

Edisi Bahasa Indonesia (`id-ID`) untuk peran kurikulum B80 / proyek O002.
Versi `2026.08.22.1` memuat arsitektur 14-unit yang dipilih: dua primer wajib
diikuti dua belas unit utama, dengan runtime lokal Python, SciPy, dan SageMath.
Rilis 12-unit `v2026.08.22` tetap lengkap dan tidak berubah sebagai edisi
mandiri historis.
Buku ini merupakan karya independen dan tidak menyiratkan dukungan dari penulis
atau lembaga yang dibahas sebagai sumber perbandingan.

Produksi, penerjemahan, dan QA berbantuan model menggunakan **OpenAI Codex gpt-5.6-sol, Ultra**,
atas arahan Floris. Identifikasi ini tidak menggantikan atribusi penulis,
sumber, pemegang hak, atau kontributor manusia yang tercatat.

- Pembaca HTML: <https://kokunoyumeto.github.io/mathematical-computing-reproducible-experiments-id/>
- PDF dan paket preservasi versi 2026.08.22.1: <https://doi.org/10.5281/zenodo.22053905>
- Cermin pembaca dan sumber ringkas di Figshare: <https://doi.org/10.6084/m9.figshare.33314796.v2>
- Rilis historis 12-unit: <https://doi.org/10.5281/zenodo.22052053>
- Repositori sumber: <https://github.com/KokunoYumeto/mathematical-computing-reproducible-experiments-id>

Ini adalah buku ajar baru yang memperkenalkan pemrograman dan eksperimen
komputasional setelah kompetensi prasyarat A30 (prakalulus). Buku ini tidak
menganggap pembaca telah menyelesaikan kalkulus, aljabar linear, atau persamaan
diferensial.

Sumber hidup memuat dua primer wajib dan dua belas unit utama yang membentuk
satu alur dari pemrograman pertama, representasi, dan bukti sampai proyek akhir
yang dapat diperiksa. Enam puluh latihan lama tetap utuh; primer dan lab
penguasaan menambah lima belas latihan sehingga batas baru memuat 75 latihan.
Semua latihan mempunyai petunjuk, jawaban, dan solusi lengkap; lima belas
latihan penguasaan baru juga mempunyai pemeriksaan yang dapat dieksekusi.
Status penerimaan pembaca ditentukan oleh `00_control/CURRENT_STATE.md`.

Sumber pembaca berada di `source/`, pengujian di `tests/`, catatan kendali di
`00_control/`, rekaman backend stabil di `backend/`, dan pembaca terbangun di
`output/`. Situs GitHub Pages diterbitkan dari pohon rilis yang telah
diverifikasi, bukan dari salinan sumber yang dibaca sebagai sumber daya Quarto.
Pilihan istilah utama dicatat dalam [glosarium id-ID](GLOSSARY_ID_ID.md),
beserta [QA terminologi berbasis sumber TeX Indonesia](00_control/TERMINOLOGY_QA_ID_ARXIV.md).

Teks asli proyek dilisensikan dengan CC BY-SA 4.0. Kode asli proyek
dilisensikan dengan MIT. Sumber rujukan/donor mempertahankan lisensi masing-
masing dan tidak otomatis menjadi bagian dari buku ini. Tidak ada byte donor
yang diadaptasi ke dalam sumber hidup 14-unit maupun rilis historis 12-unit.

Ikuti [panduan penyiapan lokal](index.qmd#sec-o002-setup) sebelum menjalankan
eksperimen. Build lokal yang dibekukan memakai Quarto, Python, Jupyter, dan
LuaLaTeX:

```text
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Mode Candidate
```

Perintah tersebut memverifikasi lock Python dan SageMath, menjalankan QA sumber,
seluruh tes, 14 permukaan eksperimen, build HTML/PDF/EPUB, QA pembaca, dan
manifest SHA-256. Batas rilis historis 2026.08.22 lulus 115/115 pengujian dan
dua build bersih menghasilkan manifest keluaran 60 berkas yang identik byte
demi byte; angka itu tidak dipakai sebagai bukti untuk batas 14-unit yang baru.
