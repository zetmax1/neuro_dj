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
| course_like | 1000 | shoxni o‘qish | read | 1.024 | 3.273 | 0.313 [0.289, 0.391] | MPTT tezroq |
| course_like | 1000 | ajdodlarni o‘qish | read | 1.13 | 6.239 | 0.181 [0.161, 0.189] | MPTT tezroq |
| course_like | 1000 | oxiriga barg qo‘shish | write | 8.918 | 0.818 | 10.902 [3.818, 13.322] | CTE tezroq |
| course_like | 1000 | eng chapga barg qo‘shish | write | 9.688 | 0.839 | 11.547 [3.046, 12.793] | CTE tezroq |
| course_like | 1000 | shoxni ko‘chirish | write | 10.926 | 5.19 | 2.105 [1.734, 2.283] | CTE tezroq |
| course_like | 1000 | shoxni o‘chirish | write | 9.769 | 1.806 | 5.409 [2.43, 5.883] | CTE tezroq |
| deep_chain | 1000 | shoxni o‘qish | read | 4.125 | 213.91 | 0.019 [0.014, 0.022] | MPTT tezroq |
| deep_chain | 1000 | ajdodlarni o‘qish | read | 5.36 | 211.826 | 0.025 [0.015, 0.025] | MPTT tezroq |
| deep_chain | 1000 | oxiriga barg qo‘shish | write | 5.312 | 0.782 | 6.793 [2.682, 11.695] | CTE tezroq |
| deep_chain | 1000 | eng chapga barg qo‘shish | write | 10.337 | 0.895 | 11.55 [9.44, 14.433] | CTE tezroq |
| deep_chain | 1000 | shoxni ko‘chirish | write | 8.568 | 75.643 | 0.113 [0.112, 0.119] | MPTT tezroq |
| deep_chain | 1000 | shoxni o‘chirish | write | 268 | 309.504 | 0.866 [0.853, 0.916] | MPTT tezroq |
| random | 1000 | shoxni o‘qish | read | 1.022 | 4.037 | 0.253 [0.218, 0.29] | MPTT tezroq |
| random | 1000 | ajdodlarni o‘qish | read | 1.057 | 6.843 | 0.154 [0.147, 0.172] | MPTT tezroq |
| random | 1000 | oxiriga barg qo‘shish | write | 7.15 | 0.746 | 9.584 [2.191, 12.401] | CTE tezroq |
| random | 1000 | eng chapga barg qo‘shish | write | 6.836 | 0.999 | 6.843 [2.007, 10.253] | CTE tezroq |
| random | 1000 | shoxni ko‘chirish | write | 9.443 | 5.989 | 1.577 [1.557, 1.694] | CTE tezroq |
| random | 1000 | shoxni o‘chirish | write | 8.975 | 1.887 | 4.756 [1.775, 6.457] | CTE tezroq |

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
| deep_chain | 1000 | shoxni o‘chirish | 625 | 623 | 409 | 0 |
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
| course_like | 1000 | shoxni o‘qish | 1.443 | 3.74 |
| course_like | 1000 | ajdodlarni o‘qish | 1.151 | 6.922 |
| course_like | 1000 | oxiriga barg qo‘shish | 9.732 | 1.096 |
| course_like | 1000 | eng chapga barg qo‘shish | 10.413 | 1.153 |
| course_like | 1000 | shoxni ko‘chirish | 11.366 | 5.475 |
| course_like | 1000 | shoxni o‘chirish | 12.355 | 3.646 |
| deep_chain | 1000 | shoxni o‘qish | 5.438 | 254.498 |
| deep_chain | 1000 | ajdodlarni o‘qish | 6.008 | 295.737 |
| deep_chain | 1000 | oxiriga barg qo‘shish | 8.083 | 1.009 |
| deep_chain | 1000 | eng chapga barg qo‘shish | 11.755 | 1.088 |
| deep_chain | 1000 | shoxni ko‘chirish | 9.028 | 77.844 |
| deep_chain | 1000 | shoxni o‘chirish | 371.59 | 433.477 |
| random | 1000 | shoxni o‘qish | 1.155 | 4.105 |
| random | 1000 | ajdodlarni o‘qish | 1.155 | 7.019 |
| random | 1000 | oxiriga barg qo‘shish | 9.08 | 1.145 |
| random | 1000 | eng chapga barg qo‘shish | 10.138 | 1.169 |
| random | 1000 | shoxni ko‘chirish | 10.117 | 6.344 |
| random | 1000 | shoxni o‘chirish | 10.403 | 2.093 |

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
| course_like | 1000 | 2 | unlocked | 363.526 | 100.205 | [2.349, 7.759] | CTE tezroq | ha | yo‘q | 16 | 28 |
| course_like | 1000 | 4 | unlocked | 486.591 | 2.063 | [195.524, 298.087] | CTE tezroq | ha | yo‘q | 39 | 12 |
| course_like | 1000 | 4 | locked | 233.174 | 217.776 | [1.053, 1.089] | CTE tezroq | ha | ha | 11 | 9 |
| deep_chain | 1000 | 2 | unlocked | 89.326 | 42.297 | [1.085, 4.489] | CTE tezroq | ha | yo‘q | 75 | 154 |
| deep_chain | 1000 | 4 | unlocked | 183.837 | 1.452 | [108.895, 154.077] | CTE tezroq | ha | yo‘q | 113 | 32 |
| deep_chain | 1000 | 4 | locked | 39.123 | 208.69 | [0.163, 0.213] | MPTT tezroq | ha | ha | 53 | 96 |
| random | 1000 | 2 | unlocked | 279.455 | 4.268 | [50.886, 84.999] | CTE tezroq | ha | yo‘q | 29 | 10 |
| random | 1000 | 4 | unlocked | 394.805 | 1.872 | [198.107, 222.733] | CTE tezroq | ha | yo‘q | 37 | 14 |
| random | 1000 | 4 | locked | 194.001 | 202.812 | [0.95, 0.964] | MPTT tezroq | ha | ha | 19 | 14 |

## 5. O‘lchangan daraxtlar

Benchmark'ning kirishi fayl emas, generator: uning izi — `parent_id`
ketma-ketligining sha256'si. Ikkala usul bir xil ketma-ketlikdan quriladi,
shuning uchun hash ikki qatorda bir xil bo‘ladi. Qurish vaqti amal emas va
o‘lchovga kirmaydi.

| Shakl | Hajm | Usul | Tugun | Maks chuqurlik | sha256 | Qurish (s) |
|---|---|---|---|---|---|---|
| course_like | 1000 | mptt | 1000 | 3 | `dee517a825db` | 0.042 |
| course_like | 1000 | cte | 1000 | 3 | `dee517a825db` | 0.024 |
| deep_chain | 1000 | mptt | 1000 | 999 | `2c7d91e72f6a` | 0.034 |
| deep_chain | 1000 | cte | 1000 | 999 | `2c7d91e72f6a` | 0.021 |
| random | 1000 | mptt | 1000 | 12 | `f92083ccb676` | 0.036 |
| random | 1000 | cte | 1000 | 12 | `f92083ccb676` | 0.021 |

## 6. O‘qish qoidasi (natijadan oldin yozilgan)

H4 qo‘llab-quvvatlandi: to‘rtta yozish amalining har birida, har bir shakl va hajmda “CTE tezroq”; o‘qishda hech bir katakda CTE 1,5 barobardan ko‘proq sekin emas; parallel yozishdan keyin CTE da yaxlitlik buzilishi yo‘q (D63)

**Xulosa: qo‘llab-quvvatlanmadi.**

| Shart | Buzilgan katak | Qaysi |
|---|---|---|
| yozish amallari | 2 | move_branch@deep_chain/1000, delete_branch@deep_chain/1000 |
| o‘qish amallari | 6 | read_branch@course_like/1000, read_ancestors@course_like/1000, read_branch@deep_chain/1000, read_ancestors@deep_chain/1000, read_branch@random/1000, read_ancestors@random/1000 |
| parallel yozishdagi yaxlitlik | 0 | — |
| son chiqmagan kataklar | 0 | — |

## 7. Muhit

Vaqt o‘lchovlari mashinaga bog‘liq; nisbat va uning oralig‘i kamroq
bog‘liq, shuning uchun da’vo ular ustiga qurilgan.

- PostgreSQL: 16.15 (Debian 16.15-1.pgdg13+2), `shared_buffers` 128MB, `fsync` on, `synchronous_commit` on
- baza: `neurolearn_bench` (alias `benchmark`)
- CPU: 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz, mantiqiy yadro 16, governor powersave
- RAM: 15615888 kB, bo‘sh 6393580 kB
- yuklama (boshida): 1.5
- platforma: Linux-7.0.0-38-generic-x86_64-with-glibc2.43

Ishga tushirish paytida eng ko‘p CPU yegan jarayonlar:

| Jarayon | CPU % |
|---|---|
| `python` | 339 |
| `gnome-shell` | 10.2 |
| `chrome` | 8.9 |
| `antigravity-ide` | 5.9 |
| `antigravity-ide` | 5.8 |

## 8. Manba va ishga tushirish (D48)

- kod commit'i: `4e9f2b9`
- buyruq: `python manage.py run_tree_benchmark --quick --database benchmark --shapes course_like,deep_chain,random --warmups 5 --repeats 30 --timeout 120.0 --parallel-repeats 3 --seed 20261006`
- vaqt: 2026-10-12T13:19:31.541825+00:00
- python: 3.12.3, Linux-7.0.0-38-generic-x86_64-with-glibc2.43
- git holati boshida: `4e9f2b9`, toza (2026-10-12T11:40:08.034243+00:00)
- git holati oxirida: `4e9f2b9`, toza (2026-10-12T13:19:31.541802+00:00)
- seed: bootstrap = 20261006, targets = 20261006, trees = 20261006
- paketlar: django 6.0.5, django-mptt 0.18.0, django-tree-queries 0.24.0, psycopg 3.3.6

| Fayl | sha256 | Bayt |
|---|---|---|
| — | — | — |

