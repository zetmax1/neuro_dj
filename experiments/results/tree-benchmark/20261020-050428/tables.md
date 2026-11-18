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
| deep_chain | 100000 | shoxni o‘qish | read | 699.402 | timeout | — | timeout |
| deep_chain | 100000 | ajdodlarni o‘qish | read | 628.611 | timeout | — | timeout |
| deep_chain | 100000 | oxiriga barg qo‘shish | write | 472.095 | 1.677 | 281.427 [235.169, 365.018] | CTE tezroq |
| deep_chain | 100000 | eng chapga barg qo‘shish | write | 1022.98 | 2.421 | 422.457 [381.918, 452.996] | CTE tezroq |
| deep_chain | 100000 | shoxni ko‘chirish | write | 1074.294 | timeout | — | timeout |
| deep_chain | 100000 | shoxni o‘chirish | write | 26013.409 | 28212.383 | 0.922 [0.796, 1.033] | taqqoslanadigan |

## 2. SQL so‘rovlar va o‘zgargan qatorlar

So‘rovlar soni — `CaptureQueriesContext`, har takrorda. O‘zgargan qatorlar
bitta qo‘shimcha, **o‘lchanmagan** takrorda sanaladi: amaldan oldin va keyin
ustunlar solishtiriladi. MPTT ning ko‘chirish qatori shu ustunda ko‘rinadi —
oraliqlar jadvalning katta qismida qayta yoziladi.

| Shakl | Hajm | Amal | MPTT SQL | CTE SQL | MPTT o‘zgargan | CTE o‘zgargan |
|---|---|---|---|---|---|---|
| deep_chain | 100000 | shoxni o‘qish | 2 | — | — | — |
| deep_chain | 100000 | ajdodlarni o‘qish | 2 | — | — | — |
| deep_chain | 100000 | oxiriga barg qo‘shish | 6 | 4 | 52275 | 1 |
| deep_chain | 100000 | eng chapga barg qo‘shish | 6 | 4 | 100001 | 1 |
| deep_chain | 100000 | shoxni ko‘chirish | 6 | — | 84459 | — |
| deep_chain | 100000 | shoxni o‘chirish | 0 | 0 | 52273 | 0 |

## 3. Dumi (p95)

p95 da’voga kirmaydi (D63), lekin UI uchun eng yomon holat ham muhim.

| Shakl | Hajm | Amal | MPTT p95 (ms) | CTE p95 (ms) |
|---|---|---|---|---|
| deep_chain | 100000 | shoxni o‘qish | 1426.144 | — |
| deep_chain | 100000 | ajdodlarni o‘qish | 1426.109 | — |
| deep_chain | 100000 | oxiriga barg qo‘shish | 1150.759 | 2.346 |
| deep_chain | 100000 | eng chapga barg qo‘shish | 1061.475 | 3.05 |
| deep_chain | 100000 | shoxni ko‘chirish | 1152.008 | — |
| deep_chain | 100000 | shoxni o‘chirish | 51918.606 | 49519.82 |

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
| deep_chain | 100000 | 2 | unlocked | 0.017 | 0.969 | [0.017, 0.023] | MPTT tezroq | ha | yo‘q | 6 | 64 |
| deep_chain | 100000 | 4 | unlocked | 0.033 | 0.545 | [0.042, 0.062] | MPTT tezroq | ha | yo‘q | 12 | 114 |
| deep_chain | 100000 | 8 | unlocked | 0.067 | 0.414 | [0.095, 0.238] | MPTT tezroq | ha | yo‘q | 24 | 139 |
| deep_chain | 100000 | 8 | locked | 0.067 | 1.14 | [0.056, 0.059] | MPTT tezroq | ha | ha | 24 | 23 |

## 5. O‘lchangan daraxtlar

Benchmark'ning kirishi fayl emas, generator: uning izi — `parent_id`
ketma-ketligining sha256'si. Ikkala usul bir xil ketma-ketlikdan quriladi,
shuning uchun hash ikki qatorda bir xil bo‘ladi. Qurish vaqti amal emas va
o‘lchovga kirmaydi.

| Shakl | Hajm | Usul | Tugun | Maks chuqurlik | sha256 | Qurish (s) |
|---|---|---|---|---|---|---|
| deep_chain | 100000 | mptt | 100000 | 99999 | `6cc718522da2` | 5.908 |
| deep_chain | 100000 | cte | 100000 | 99999 | `6cc718522da2` | 3.268 |

## 6. O‘qish qoidasi (natijadan oldin yozilgan)

H4 qo‘llab-quvvatlandi: to‘rtta yozish amalining har birida, har bir shakl va hajmda “CTE tezroq”; o‘qishda hech bir katakda CTE 1,5 barobardan ko‘proq sekin emas; parallel yozishdan keyin CTE da yaxlitlik buzilishi yo‘q (D63)

**Xulosa: qo‘llab-quvvatlanmadi.**

| Shart | Buzilgan katak | Qaysi |
|---|---|---|
| yozish amallari | 1 | delete_branch@deep_chain/100000 |
| o‘qish amallari | 0 | — |
| parallel yozishdagi yaxlitlik | 0 | — |
| son chiqmagan kataklar | 3 | read_branch@deep_chain/100000, read_ancestors@deep_chain/100000, move_branch@deep_chain/100000 |

## 7. Muhit

Vaqt o‘lchovlari mashinaga bog‘liq; nisbat va uning oralig‘i kamroq
bog‘liq, shuning uchun da’vo ular ustiga qurilgan.

- PostgreSQL: 16.15 (Debian 16.15-1.pgdg13+2), `shared_buffers` 128MB, `fsync` on, `synchronous_commit` on
- baza: `neurolearn_bench` (alias `benchmark`)
- CPU: 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz, mantiqiy yadro 16, governor powersave
- RAM: 15615896 kB, bo‘sh 7568264 kB
- yuklama (boshida): 1.81
- platforma: Linux-7.0.0-38-generic-x86_64-with-glibc2.43

Ishga tushirish paytida eng ko‘p CPU yegan jarayonlar:

| Jarayon | CPU % |
|---|---|
| `python` | 205 |
| `ps` | 100 |
| `antigravity-ide` | 20.1 |
| `chrome` | 17.9 |
| `chrome` | 15.8 |

## 8. Manba va ishga tushirish (D48)

- kod commit'i: `9f97aa7`
- buyruq: `python manage.py run_tree_benchmark --database benchmark --shapes deep_chain --sizes 100000 --warmups 5 --repeats 30 --timeout 120.0 --parallel-repeats 3 --seed 20261006 --memory-limit-gb 8.0`
- vaqt: 2026-10-20T05:04:28.422089+00:00
- python: 3.12.3, Linux-7.0.0-38-generic-x86_64-with-glibc2.43
- git holati boshida: `9f97aa7`, toza (2026-10-20T03:53:03.467494+00:00)
- git holati oxirida: `9f97aa7`, toza (2026-10-20T05:04:28.421825+00:00)
- seed: bootstrap = 20261006, targets = 20261006, trees = 20261006
- paketlar: django 6.0.5, django-mptt 0.18.0, django-tree-queries 0.24.0, psycopg 3.3.6

| Fayl | sha256 | Bayt |
|---|---|---|
| — | — | — |

