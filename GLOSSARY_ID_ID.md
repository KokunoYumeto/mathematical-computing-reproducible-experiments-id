# Glosarium istilah id-ID

Glosarium ini menetapkan bentuk yang dipakai secara konsisten dalam
*Komputasi Matematis dan Eksperimen yang Dapat Direproduksi*. Istilah sumber
berbahasa Inggris dipertahankan di dalam kode atau nama API bila penerjemahan
akan mengubah antarmuka yang harus diketik pembaca.

| Konsep | Bentuk yang dipakai | Catatan penggunaan |
|---|---|---|
| algorithm | **algoritme** | Bentuk editorial baku; jangan menggantinya dengan `algoritma` dalam prosa pembaca. |
| analysis | **analisis** | Gunakan `analisis`, bukan bentuk lama `analisa`. |
| numerical technique / method | **teknik numerik** / **metode numerik** | Pilih menurut makna kalimat; eja `teknik`, bukan `tehnik`. |
| computation / computational | **komputasi** / **komputasional** | `Perhitungan` dipakai hanya bila yang dimaksud memang operasi hitung tertentu. |
| library | **pustaka** | Nama paket dan modul tetap ditulis sebagaimana API aslinya. |
| file | **berkas** | Kata `file` hanya boleh muncul sebagai literal kode, keluaran program, nama format, atau kutipan sumber. |
| input / output | **masukan** / **keluaran** | Nama parameter atau fungsi dalam kode tidak diterjemahkan. |
| exact computation | **komputasi eksak** | Berlawanan dengan pendekatan numerik atau representasi titik-mengambang. |
| floating-point | **titik-mengambang** | Gunakan tanda hubung secara konsisten. |
| error | **galat** | Bedakan galat maju, galat mundur, galat relatif, dan kesalahan implementasi. |
| conditioning | **pengondisian** | Sifat masalah; jangan disamakan dengan stabilitas algoritmik. |
| algorithmic stability | **stabilitas algoritmik** | Sifat algoritme dan implementasinya. |
| time step | **langkah waktu** | Untuk diskretisasi waktu dalam simulasi atau integrasi numerik. |
| sequential / parallel computation | **komputasi sekuensial / paralel** | `Paralel` juga dipakai untuk waktu atau algoritme bila konteksnya jelas. |
| average | **rata-rata** | Nyatakan jenis rerata bila bukan rerata aritmetika biasa. |
| scalability | **skalabilitas** | Tambahkan ukuran masalah atau sumber daya yang diskalakan bila relevan. |
| reproducible experiment | **eksperimen yang dapat direproduksi** | Bentuk judul dan istilah utama buku; jangan dipendekkan menjadi klaim reproduksibilitas tanpa bukti. |
| evidence / proof | **bukti empiris/komputasional** / **bukti matematis** | Keluaran komputasi adalah bukti kerja atau evidensi terbatas, bukan otomatis pembuktian umum. |

## Saksi penggunaan lapangan

QA bertanggal 2026-08-22 membandingkan istilah ini dengan sumber TeX Indonesia
arXiv:0807.4609v1 karya A.B. Mutiara tentang komputasi paralel dan simulasi
numerik. Saksi tersebut menguatkan `komputasi`, `pustaka`,
`masukan/keluaran`, `langkah waktu`, `nilai rata-rata`, `sekuensial`,
`paralel`, dan `skalabilitas`. Perbedaannya didokumentasikan dalam
`00_control/TERMINOLOGY_QA_ID_ARXIV.md`; tidak ada ekspresi sumber yang
disalin ke dalam buku.
