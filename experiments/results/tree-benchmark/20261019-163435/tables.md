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
| deep_chain | 1000 | 2 | unlocked | 132.268 | 144.247 | [0.802, 0.971] | MPTT tezroq | ha | yo‘q | 347 | 4609 |
| deep_chain | 1000 | 4 | unlocked | 196.21 | 2.367 | [34.001, 127.492] | CTE tezroq | ha | yo‘q | 860 | 202 |
| deep_chain | 1000 | 8 | unlocked | 277.724 | 1.3 | [189.404, 281.838] | CTE tezroq | ha | yo‘q | 1042 | 158 |
| deep_chain | 1000 | 8 | locked | 63.437 | 105.947 | [0.597, 0.677] | MPTT tezroq | ha | ha | 186 | 245 |
| deep_chain | 10000 | 2 | unlocked | 0.394 | 3.52 | [0.089, 0.121] | MPTT tezroq | ha | yo‘q | 6 | 98 |
| deep_chain | 10000 | 4 | unlocked | 0.678 | 1.813 | [0.262, 0.468] | MPTT tezroq | ha | yo‘q | 6 | 131 |
| deep_chain | 10000 | 8 | unlocked | 0.838 | 0.954 | [0.562, 1.169] | taqqoslanadigan | ha | yo‘q | 13 | 160 |
| deep_chain | 10000 | 8 | locked | 0.233 | 8.491 | [0.026, 0.029] | MPTT tezroq | ha | ha | 6 | 36 |

## 5. O‘lchangan daraxtlar

Benchmark'ning kirishi fayl emas, generator: uning izi — `parent_id`
ketma-ketligining sha256'si. Ikkala usul bir xil ketma-ketlikdan quriladi,
shuning uchun hash ikki qatorda bir xil bo‘ladi. Qurish vaqti amal emas va
o‘lchovga kirmaydi.

| Shakl | Hajm | Usul | Tugun | Maks chuqurlik | sha256 | Qurish (s) |
|---|---|---|---|---|---|---|
| deep_chain | 1000 | mptt | 1000 | 999 | `2c7d91e72f6a` | 0.062 |
| deep_chain | 1000 | cte | 1000 | 999 | `2c7d91e72f6a` | 0.031 |
| deep_chain | 10000 | mptt | 10000 | 9999 | `71aa31b40fef` | 0.496 |
| deep_chain | 10000 | cte | 10000 | 9999 | `71aa31b40fef` | 0.291 |

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
- RAM: 15615900 kB, bo‘sh 8251008 kB
- yuklama (boshida): 1.81
- platforma: Linux-7.0.0-38-generic-x86_64-with-glibc2.43

Ishga tushirish paytida eng ko‘p CPU yegan jarayonlar:

| Jarayon | CPU % |
|---|---|
| `python` | 270 |
| `gnome-shell` | 16.2 |
| `antigravity-ide` | 9.7 |
| `antigravity-ide` | 8.2 |
| `antigravity-ide` | 5.1 |

## 8. Manba va ishga tushirish (D48)

- kod commit'i: `9f97aa7`
- buyruq: `python manage.py run_tree_benchmark --only-parallel --database benchmark --shapes deep_chain --sizes 1000,10000 --warmups 5 --repeats 30 --timeout 120.0 --parallel-repeats 3 --seed 20261006 --memory-limit-gb 8.0`
- vaqt: 2026-10-19T16:34:35.110467+00:00
- python: 3.12.3, Linux-7.0.0-38-generic-x86_64-with-glibc2.43
- git holati boshida: `9f97aa7`, toza (2026-10-19T16:14:31.580564+00:00)
- git holati oxirida: `9f97aa7`, toza (2026-10-19T16:34:35.110445+00:00)
- seed: bootstrap = 20261006, targets = 20261006, trees = 20261006
- paketlar: django 6.0.5, django-mptt 0.18.0, django-tree-queries 0.24.0, psycopg 3.3.6

| Fayl | sha256 | Bayt |
|---|---|---|
| — | — | — |

