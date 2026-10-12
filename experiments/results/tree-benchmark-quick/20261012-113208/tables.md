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

> **`--quick` ishga tushirish — dissertatsiya natijasi emas.** Bu quvurni
> sinash uchun: kichik daraxt, kam takror va qisqa parallel bosqich.
> To‘liq natija uchun `manage.py run_tree_benchmark` bayroqsiz
> ishga tushiriladi.

## 1. Amallar

| Shakl | Hajm | Amal | Tur | MPTT mediana (ms) | CTE mediana (ms) | ρ [CI] | Xulosa |
|---|---|---|---|---|---|---|---|
| course_like | 1000 | shoxni o‘qish | read | 1.173 | 3.597 | 0.326 [0.326, 0.453] | MPTT tezroq |
| course_like | 1000 | ajdodlarni o‘qish | read | 1.233 | 6.191 | 0.199 [0.179, 0.217] | MPTT tezroq |
| course_like | 1000 | oxiriga barg qo‘shish | write | 7.725 | 0.802 | 9.632 [3.264, 11.745] | CTE tezroq |
| course_like | 1000 | eng chapga barg qo‘shish | write | 8.504 | 0.985 | 8.634 [2.185, 11.159] | CTE tezroq |
| course_like | 1000 | shoxni ko‘chirish | write | 9.111 | 4.927 | 1.849 [1.627, 2.105] | CTE tezroq |
| course_like | 1000 | shoxni o‘chirish | write | 9.799 | 1.858 | 5.274 [2.242, 5.828] | CTE tezroq |
| deep_chain | 1000 | shoxni o‘qish | read | 4.442 | 193.383 | 0.023 [0.021, 0.029] | MPTT tezroq |
| deep_chain | 1000 | ajdodlarni o‘qish | read | 3.386 | 169.46 | 0.02 [0.013, 0.022] | MPTT tezroq |
| deep_chain | 1000 | oxiriga barg qo‘shish | write | 4.75 | 0.74 | 6.419 [3.264, 10.334] | CTE tezroq |
| deep_chain | 1000 | eng chapga barg qo‘shish | write | 9.326 | 0.8 | 11.658 [10.15, 13.3] | CTE tezroq |
| deep_chain | 1000 | shoxni ko‘chirish | write | 8.975 | 78.596 | 0.114 [0.11, 0.116] | MPTT tezroq |
| deep_chain | 1000 | shoxni o‘chirish | write | error | error | — | hisoblanmadi |
| random | 1000 | shoxni o‘qish | read | 0.999 | 3.841 | 0.26 [0.249, 0.305] | MPTT tezroq |
| random | 1000 | ajdodlarni o‘qish | read | 1.228 | 7.309 | 0.168 [0.152, 0.206] | MPTT tezroq |
| random | 1000 | oxiriga barg qo‘shish | write | 7.432 | 0.73 | 10.181 [2.556, 11.206] | CTE tezroq |
| random | 1000 | eng chapga barg qo‘shish | write | 7.206 | 0.859 | 8.389 [1.889, 14.128] | CTE tezroq |
| random | 1000 | shoxni ko‘chirish | write | 8.902 | 5.554 | 1.603 [1.576, 1.79] | CTE tezroq |
| random | 1000 | shoxni o‘chirish | write | 10.345 | 2.147 | 4.818 [1.43, 7.657] | CTE tezroq |

## 2. SQL so‘rovlar va o‘zgargan qatorlar

So‘rovlar soni — `CaptureQueriesContext`, har takrorda. O‘zgargan qatorlar
bitta qo‘shimcha, **o‘lchanmagan** takrorda sanaladi: amaldan oldin va keyin
ustunlar solishtiriladi. MPTT ning ko‘chirish qatori shu ustunda ko‘rinadi —
oraliqlar jadvalning katta qismida qayta yoziladi.

| Shakl | Hajm | Amal | MPTT SQL | CTE SQL | MPTT o‘zgargan | CTE o‘zgargan |
|---|---|---|---|---|---|---|
| course_like | 1000 | shoxni o‘qish | 2 | 2 | — | — |
| course_like | 1000 | ajdodlarni o‘qish | 2 | 3 | — | — |
| course_like | 1000 | oxiriga barg qo‘shish | 6 | 4 | 536 | 1 |
| course_like | 1000 | eng chapga barg qo‘shish | 6 | 4 | 546 | 1 |
| course_like | 1000 | shoxni ko‘chirish | 6 | 7 | 456 | 1 |
| course_like | 1000 | shoxni o‘chirish | 8 | 6 | 534 | 0 |
| deep_chain | 1000 | shoxni o‘qish | 2 | 2 | — | — |
| deep_chain | 1000 | ajdodlarni o‘qish | 2 | 3 | — | — |
| deep_chain | 1000 | oxiriga barg qo‘shish | 6 | 4 | 411 | 1 |
| deep_chain | 1000 | eng chapga barg qo‘shish | 6 | 4 | 1001 | 1 |
| deep_chain | 1000 | shoxni ko‘chirish | 6 | 7 | 878 | 1 |
| deep_chain | 1000 | shoxni o‘chirish | — | — | — | — |
| random | 1000 | shoxni o‘qish | 2 | 2 | — | — |
| random | 1000 | ajdodlarni o‘qish | 2 | 3 | — | — |
| random | 1000 | oxiriga barg qo‘shish | 6 | 4 | 60 | 1 |
| random | 1000 | eng chapga barg qo‘shish | 6 | 4 | 62 | 1 |
| random | 1000 | shoxni ko‘chirish | 6 | 7 | 869 | 1 |
| random | 1000 | shoxni o‘chirish | 9 | 7 | 58 | 0 |

## 3. Dumi (p95)

p95 da’voga kirmaydi (D63), lekin UI uchun eng yomon holat ham muhim.

| Shakl | Hajm | Amal | MPTT p95 (ms) | CTE p95 (ms) |
|---|---|---|---|---|
| course_like | 1000 | shoxni o‘qish | 1.772 | 4.002 |
| course_like | 1000 | ajdodlarni o‘qish | 1.322 | 6.4 |
| course_like | 1000 | oxiriga barg qo‘shish | 8.388 | 1.039 |
| course_like | 1000 | eng chapga barg qo‘shish | 9.039 | 1.117 |
| course_like | 1000 | shoxni ko‘chirish | 9.72 | 5.407 |
| course_like | 1000 | shoxni o‘chirish | 11.142 | 4.037 |
| deep_chain | 1000 | shoxni o‘qish | 5.617 | 200.683 |
| deep_chain | 1000 | ajdodlarni o‘qish | 4.967 | 228.022 |
| deep_chain | 1000 | oxiriga barg qo‘shish | 7.299 | 0.89 |
| deep_chain | 1000 | eng chapga barg qo‘shish | 10.28 | 0.992 |
| deep_chain | 1000 | shoxni ko‘chirish | 9.02 | 80.38 |
| deep_chain | 1000 | shoxni o‘chirish | — | — |
| random | 1000 | shoxni o‘qish | 1.148 | 3.879 |
| random | 1000 | ajdodlarni o‘qish | 1.461 | 7.357 |
| random | 1000 | oxiriga barg qo‘shish | 8.155 | 0.753 |
| random | 1000 | eng chapga barg qo‘shish | 10.072 | 0.977 |
| random | 1000 | shoxni ko‘chirish | 9.932 | 5.637 |
| random | 1000 | shoxni o‘chirish | 11.679 | 2.263 |

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
| course_like | 1000 | 2 | unlocked | 367.851 | 151.75 | [2.108, 2.843] | CTE tezroq | ha | yo‘q | 16 | 56 |
| course_like | 1000 | 4 | unlocked | 502.237 | 2.982 | [160.582, 176.697] | CTE tezroq | ha | yo‘q | 68 | 10 |
| course_like | 1000 | 4 | locked | 227.415 | 209.595 | [1.079, 1.091] | CTE tezroq | ha | ha | 11 | 9 |
| deep_chain | 1000 | 2 | unlocked | 87.036 | 74.371 | [0.435, 40.977] | taqqoslanadigan | ha | yo‘q | 77 | 210 |
| deep_chain | 1000 | 4 | unlocked | 220.424 | 2.258 | [82.269, 115.209] | CTE tezroq | ha | yo‘q | 117 | 36 |
| deep_chain | 1000 | 4 | locked | 36.244 | 207.389 | [0.144, 0.204] | MPTT tezroq | ha | ha | 48 | 92 |
| random | 1000 | 2 | unlocked | 324.765 | 6.345 | [36.689, 85.212] | CTE tezroq | ha | yo‘q | 36 | 10 |
| random | 1000 | 4 | unlocked | 432.131 | 2.03 | [200.586, 226.236] | CTE tezroq | ha | yo‘q | 51 | 10 |
| random | 1000 | 4 | locked | 192.91 | 223.063 | [0.858, 0.871] | MPTT tezroq | ha | ha | 19 | 14 |

## 5. O‘lchangan daraxtlar

Benchmark'ning kirishi fayl emas, generator: uning izi — `parent_id`
ketma-ketligining sha256'si. Ikkala usul bir xil ketma-ketlikdan quriladi,
shuning uchun hash ikki qatorda bir xil bo‘ladi. Qurish vaqti amal emas va
o‘lchovga kirmaydi.

| Shakl | Hajm | Usul | Tugun | Maks chuqurlik | sha256 | Qurish (s) |
|---|---|---|---|---|---|---|
| course_like | 1000 | mptt | 1000 | 3 | `dee517a825db` | 0.05 |
| course_like | 1000 | cte | 1000 | 3 | `dee517a825db` | 0.021 |
| deep_chain | 1000 | mptt | 1000 | 999 | `2c7d91e72f6a` | 0.035 |
| deep_chain | 1000 | cte | 1000 | 999 | `2c7d91e72f6a` | 0.021 |
| random | 1000 | mptt | 1000 | 12 | `f92083ccb676` | 0.04 |
| random | 1000 | cte | 1000 | 12 | `f92083ccb676` | 0.061 |

## 6. O‘qish qoidasi (natijadan oldin yozilgan)

H4 qo‘llab-quvvatlandi: to‘rtta yozish amalining har birida, har bir shakl va hajmda “CTE tezroq”; o‘qishda hech bir katakda CTE 1,5 barobardan ko‘proq sekin emas; parallel yozishdan keyin CTE da yaxlitlik buzilishi yo‘q (D63)

**Xulosa: qo‘llab-quvvatlanmadi.**

| Shart | Buzilgan katak | Qaysi |
|---|---|---|
| yozish amallari | 1 | move_branch@deep_chain/1000 |
| o‘qish amallari | 6 | read_branch@course_like/1000, read_ancestors@course_like/1000, read_branch@deep_chain/1000, read_ancestors@deep_chain/1000, read_branch@random/1000, read_ancestors@random/1000 |
| parallel yozishdagi yaxlitlik | 0 | — |
| son chiqmagan kataklar | 1 | delete_branch@deep_chain/1000 |

## 7. Muhit

Vaqt o‘lchovlari mashinaga bog‘liq; nisbat va uning oralig‘i kamroq
bog‘liq, shuning uchun da’vo ular ustiga qurilgan.

- PostgreSQL: 16.15 (Debian 16.15-1.pgdg13+2), `shared_buffers` 128MB, `fsync` on, `synchronous_commit` on
- baza: `neurolearn_bench` (alias `benchmark`)
- CPU: 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz, mantiqiy yadro 16, governor powersave
- RAM: 15615888 kB, bo‘sh 6033144 kB
- yuklama (boshida): 1.97
- platforma: Linux-7.0.0-38-generic-x86_64-with-glibc2.43

Ishga tushirish paytida eng ko‘p CPU yegan jarayonlar:

| Jarayon | CPU % |
|---|---|
| `python` | 384 |
| `gnome-shell` | 10.4 |
| `chrome` | 9.7 |
| `chrome` | 6.2 |
| `antigravity-ide` | 6.2 |

## 8. Manba va ishga tushirish (D48)

- kod commit'i: `2a8d1dc`
- buyruq: `python manage.py run_tree_benchmark --quick --database benchmark --shapes course_like,deep_chain,random --warmups 5 --repeats 30 --timeout 120.0 --parallel-repeats 3 --seed 20261006`
- vaqt: 2026-10-12T11:32:08.412028+00:00
- python: 3.12.3, Linux-7.0.0-38-generic-x86_64-with-glibc2.43
- git holati boshida: `2a8d1dc`, toza (2026-10-12T11:28:46.966739+00:00)
- git holati oxirida: `2a8d1dc`, toza (2026-10-12T11:32:08.411998+00:00)
- seed: bootstrap = 20261006, targets = 20261006, trees = 20261006
- paketlar: django 6.0.5, django-mptt 0.18.0, django-tree-queries 0.24.0, psycopg 3.3.6

| Fayl | sha256 | Bayt |
|---|---|---|
| — | — | — |

