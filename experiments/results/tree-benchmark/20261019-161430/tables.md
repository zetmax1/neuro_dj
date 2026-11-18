# H4 — daraxtni saqlash usullari: MPTT va CTE

Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.

Ikkita jadval bir xil daraxtni saqlaydi: `MpttNode` — oraliq kodlash
(django-mptt), `CteNode` — qo‘shni ro‘yxat va rekursiv CTE
(django-tree-queries), ya’ni platformaning o‘zi ishlatadigan usul (D3).

ρ = mediana(MPTT) / mediana(CTE), ya’ni ρ > 1 — CTE tezroq. Oraliq —
juftlashtirilgan bootstrap (1000 replika, 95 %): har takrorda ikkala usul
bir xil nishon tugunda ishlagan.

O‘zgartiruvchi amallar tranzaksiyada o‘lchanadi va orqaga qaytariladi,
shuning uchun har takror bir xil daraxtdan boshlanadi; commit'ning narxi
o‘lchovga kirmaydi va bu ikkala usulga teng ta’sir qiladi (D63).

## 1. Amallar

| Shakl | Hajm | Amal | Tur | MPTT mediana (ms) | CTE mediana (ms) | ρ [CI] | Xulosa |
|---|---|---|---|---|---|---|---|

## 2. SQL so‘rovlar va o‘zgargan qatorlar

So‘rovlar soni — `CaptureQueriesContext`, har takrorda. O‘zgargan qatorlar
bitta qo‘shimcha, **o‘lchanmagan** takrorda sanaladi: amaldan oldin va keyin
ustunlar solishtiriladi. MPTT ning ko‘chirish qatori shu ustunda ko‘rinadi —
oraliqlar jadvalning katta qismida qayta yoziladi.

| Shakl | Hajm | Amal | MPTT SQL | CTE SQL | MPTT o‘zgargan | CTE o‘zgargan |
|---|---|---|---|---|---|---|

## 3. Dumi (p95)

p95 da’voga kirmaydi (D63), lekin UI uchun eng yomon holat ham muhim.

| Shakl | Hajm | Amal | MPTT p95 (ms) | CTE p95 (ms) |
|---|---|---|---|---|

## 4. Parallel yozish va yaxlitlik

Har bir jarayon o‘z ulanishi bilan, belgilangan vaqt davomida aralash
qo‘shish va ko‘chirish bajaradi. ρ — CTE ning o‘tkazuvchanligi MPTT ga
nisbatan (ρ > 1 — CTE tezroq). Yaxlitlik ustunlari parallel yozish
**tugagandan keyin** o‘qiladi: Y1 ikkala usulda, oraliqlar tekshiruvi
MPTT da.

Variant (D63a): `unlocked` — har bir usulning o‘z yozish yo‘li, qulfsiz;
`locked` — platformaning yo‘li, `pg_advisory_xact_lock` bilan. D63 ning
yaxlitlik sharti **qulfli** variantdan o‘qiladi; qulfsiz qatorlar
saqlash usulining o‘zi nimani kafolatlaganini ko‘rsatadi.

| Shakl | Hajm | Jarayon | Variant | CTE op/s | MPTT op/s | ρ CI | Xulosa | CTE yaxlit | MPTT yaxlit | CTE xato | MPTT xato |
|---|---|---|---|---|---|---|---|---|---|---|---|
| course_like | 1000 | 2 | unlocked | 146.443 | 67.038 | [1.916, 3.085] | CTE tezroq | ha | yo‘q | 45 | 324 |
| course_like | 1000 | 4 | unlocked | 214.715 | 2.927 | [53.973, 136.24] | CTE tezroq | ha | yo‘q | 125 | 64 |
| course_like | 1000 | 8 | unlocked | 330.303 | 1.557 | [173.115, 224.415] | CTE tezroq | yo‘q | yo‘q | 900 | 78 |
| course_like | 1000 | 8 | locked | 118.973 | 82.758 | [1.289, 1.488] | CTE tezroq | ha | ha | 38 | 16 |
| course_like | 10000 | 2 | unlocked | 123.12 | 3.75 | [27.842, 34.977] | CTE tezroq | ha | yo‘q | 3 | 42 |
| course_like | 10000 | 4 | unlocked | 192.279 | 1.416 | [119.573, 165.33] | CTE tezroq | ha | yo‘q | 4 | 66 |
| course_like | 10000 | 8 | unlocked | 250.026 | 0.831 | [206.122, 309.517] | CTE tezroq | ha | yo‘q | 4 | 85 |
| course_like | 10000 | 8 | locked | 71.433 | 8.783 | [7.839, 8.511] | CTE tezroq | ha | ha | 0 | 0 |
| course_like | 100000 | 2 | unlocked | 6.123 | 0.766 | [6.488, 9.125] | CTE tezroq | ha | yo‘q | 0 | 17 |
| course_like | 100000 | 4 | unlocked | 11.14 | 0.617 | [15.84, 21.685] | CTE tezroq | ha | yo‘q | 0 | 49 |
| course_like | 100000 | 8 | unlocked | 17.605 | 0.68 | [25.394, 27.824] | CTE tezroq | ha | yo‘q | 0 | 52 |
| course_like | 100000 | 8 | locked | 4.109 | 1.14 | [3.259, 3.604] | CTE tezroq | ha | ha | 0 | 0 |
| random | 1000 | 2 | unlocked | 197.868 | 129.667 | [1.287, 2.612] | CTE tezroq | ha | yo‘q | 162 | 1635 |
| random | 1000 | 4 | unlocked | 280.473 | 1.713 | [64.477, 173.34] | CTE tezroq | ha | yo‘q | 291 | 64 |
| random | 1000 | 8 | unlocked | 336.666 | 1.143 | [243.793, 398.893] | CTE tezroq | ha | yo‘q | 940 | 85 |
| random | 1000 | 8 | locked | 124.578 | 151.298 | [0.793, 0.94] | MPTT tezroq | ha | ha | 78 | 97 |
| random | 10000 | 2 | unlocked | 87.518 | 3.439 | [22.389, 26.261] | CTE tezroq | ha | yo‘q | 6 | 45 |
| random | 10000 | 4 | unlocked | 122.537 | 1.553 | [78.56, 92.411] | CTE tezroq | ha | yo‘q | 10 | 63 |
| random | 10000 | 8 | unlocked | 172.916 | 0.847 | [184.698, 258.084] | CTE tezroq | ha | yo‘q | 14 | 94 |
| random | 10000 | 8 | locked | 49.122 | 11.665 | [4.055, 4.295] | CTE tezroq | ha | ha | 6 | 3 |
| random | 100000 | 2 | unlocked | 2.547 | 0.867 | [2.458, 3.963] | CTE tezroq | ha | yo‘q | 2 | 18 |
| random | 100000 | 4 | unlocked | 4.392 | 0.737 | [5.671, 12.066] | CTE tezroq | ha | yo‘q | 3 | 33 |
| random | 100000 | 8 | unlocked | 7.433 | 0.443 | [13.004, 20.477] | CTE tezroq | ha | yo‘q | 3 | 57 |
| random | 100000 | 8 | locked | 1.731 | 0.906 | [1.853, 9.438] | CTE tezroq | ha | ha | 1 | 0 |

## 5. O‘lchangan daraxtlar

Benchmark'ning kirishi fayl emas, generator: uning izi — `parent_id`
ketma-ketligining sha256'si. Ikkala usul bir xil ketma-ketlikdan quriladi,
shuning uchun hash ikki qatorda bir xil bo‘ladi. Qurish vaqti amal emas va
o‘lchovga kirmaydi.

| Shakl | Hajm | Usul | Tugun | Maks chuqurlik | sha256 | Qurish (s) |
|---|---|---|---|---|---|---|
| course_like | 1000 | mptt | 1000 | 3 | `dee517a825db` | 0.104 |
| course_like | 1000 | cte | 1000 | 3 | `dee517a825db` | 0.062 |
| course_like | 10000 | mptt | 10000 | 3 | `6eb0b80090fe` | 0.409 |
| course_like | 10000 | cte | 10000 | 3 | `6eb0b80090fe` | 0.28 |
| course_like | 100000 | mptt | 100000 | 3 | `4cd38264057b` | 3.587 |
| course_like | 100000 | cte | 100000 | 3 | `4cd38264057b` | 2.012 |
| random | 1000 | mptt | 1000 | 12 | `f92083ccb676` | 0.059 |
| random | 1000 | cte | 1000 | 12 | `f92083ccb676` | 0.024 |
| random | 10000 | mptt | 10000 | 17 | `bc4155b2e63d` | 0.382 |
| random | 10000 | cte | 10000 | 17 | `bc4155b2e63d` | 0.233 |
| random | 100000 | mptt | 100000 | 24 | `046e0183f27b` | 4.076 |
| random | 100000 | cte | 100000 | 24 | `046e0183f27b` | 2 |

## 6. O‘qish qoidasi (natijadan oldin yozilgan)

H4 qo‘llab-quvvatlandi: to‘rtta yozish amalining har birida, har bir shakl va hajmda “CTE tezroq”; o‘qishda hech bir katakda CTE 1,5 barobardan ko‘proq sekin emas; parallel yozishdan keyin CTE da yaxlitlik buzilishi yo‘q (D63)

**Xulosa: hisoblanmadi.**

| Shart | Buzilgan katak | Qaysi |
|---|---|---|
| yozish amallari | 0 | — |
| o‘qish amallari | 0 | — |
| parallel yozishdagi yaxlitlik | 0 | — |
| son chiqmagan kataklar | 0 | — |

## 7. Muhit

Vaqt o‘lchovlari mashinaga bog‘liq; nisbat va uning oralig‘i kamroq
bog‘liq, shuning uchun da’vo ular ustiga qurilgan.

- PostgreSQL: 16.15 (Debian 16.15-1.pgdg13+2), `shared_buffers` 128MB, `fsync` on, `synchronous_commit` on
- baza: `neurolearn_bench` (alias `benchmark`)
- CPU: 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz, mantiqiy yadro 16, governor powersave
- RAM: 15615900 kB, bo‘sh 7940464 kB
- yuklama (boshida): 1.43
- platforma: Linux-7.0.0-38-generic-x86_64-with-glibc2.43

Ishga tushirish paytida eng ko‘p CPU yegan jarayonlar:

| Jarayon | CPU % |
|---|---|
| `python` | 216 |
| `gnome-shell` | 27.1 |
| `antigravity-ide` | 22.8 |
| `antigravity-ide` | 16.5 |
| `chrome` | 13.1 |

## 8. Manba va ishga tushirish (D48)

- kod commit'i: `9f97aa7`
- buyruq: `python manage.py run_tree_benchmark --only-parallel --database benchmark --shapes course_like,random --warmups 5 --repeats 30 --timeout 120.0 --parallel-repeats 3 --seed 20261006 --memory-limit-gb 8.0`
- vaqt: 2026-10-19T16:14:30.516914+00:00
- python: 3.12.3, Linux-7.0.0-38-generic-x86_64-with-glibc2.43
- git holati boshida: `9f97aa7`, toza (2026-10-19T15:17:10.189130+00:00)
- git holati oxirida: `9f97aa7`, toza (2026-10-19T16:14:30.516887+00:00)
- seed: bootstrap = 20261006, targets = 20261006, trees = 20261006
- paketlar: django 6.0.5, django-mptt 0.18.0, django-tree-queries 0.24.0, psycopg 3.3.6

| Fayl | sha256 | Bayt |
|---|---|---|
| — | — | — |

