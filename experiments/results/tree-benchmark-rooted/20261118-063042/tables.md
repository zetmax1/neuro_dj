# H4 (D74) — uchinchi o‘qish usuli: so‘ralgan tugundan boshlanadigan CTE

Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.

Uchala usul bir xil daraxtni o‘qiydi. `MPTT` — oraliq kodlash (django-mptt);
`CTE` — django-tree-queries, rekursiya jadvaldagi barcha ildizlardan boshlanadi;
`CTE-rooted` — qo‘lda yozilgan rekursiv CTE, rekursiya **so‘ralgan tugundan**
boshlanadi. Jadval ikkinchi va uchinchi usulda bitta: `CteNode`, ya’ni farq
faqat so‘rovning shaklida (D74).

Yozish amallari o‘lchanmaydi: ular `CTE` bilan aynan bir xil kod.

Oraliq — juftlashtirilgan bootstrap (1000 replika, 95 %): har takrorda uchala usul
bir xil nishon tugunda ishlagan (D63).

## 1. O‘qish amallari — uch usul

| Shakl | Hajm | Amal | MPTT mediana (ms) | CTE mediana (ms) | CTE-rooted mediana (ms) |
|---|---|---|---|---|---|
| course_like | 1000 | shoxni o‘qish | 2.512 | 6.106 | 2.087 |
| course_like | 1000 | ajdodlarni o‘qish | 2.355 | 8.499 | 1.725 |
| course_like | 10000 | shoxni o‘qish | 5.012 | 28.672 | 1.565 |
| course_like | 10000 | ajdodlarni o‘qish | 2.644 | 53.285 | 1.614 |
| course_like | 100000 | shoxni o‘qish | 14.073 | 927.139 | 3.4 |
| course_like | 100000 | ajdodlarni o‘qish | 14.706 | 1641.167 | 2.637 |
| deep_chain | 1000 | shoxni o‘qish | 10.115 | 381.964 | 58.007 |
| deep_chain | 1000 | ajdodlarni o‘qish | 12.208 | 431.998 | 85.746 |
| deep_chain | 10000 | shoxni o‘qish | 54.767 | 28913.347 | 42.377 |
| deep_chain | 10000 | ajdodlarni o‘qish | 45.225 | 27500.581 | 34.004 |
| deep_chain | 100000 | shoxni o‘qish | tekshirib bo‘lmadi — kutubxonaning so‘rovi tugamadi | tekshirib bo‘lmadi — kutubxonaning so‘rovi tugamadi | tekshirib bo‘lmadi — kutubxonaning so‘rovi tugamadi |
| deep_chain | 100000 | ajdodlarni o‘qish | tekshirib bo‘lmadi — kutubxonaning so‘rovi tugamadi | tekshirib bo‘lmadi — kutubxonaning so‘rovi tugamadi | tekshirib bo‘lmadi — kutubxonaning so‘rovi tugamadi |
| random | 1000 | shoxni o‘qish | 0.992 | 4.681 | 0.85 |
| random | 1000 | ajdodlarni o‘qish | 1.193 | 6.996 | 1.03 |
| random | 10000 | shoxni o‘qish | 1.563 | 28.249 | 0.571 |
| random | 10000 | ajdodlarni o‘qish | 1.501 | 66.971 | 0.645 |
| random | 100000 | shoxni o‘qish | 6.442 | 1430.163 | 1.25 |
| random | 100000 | ajdodlarni o‘qish | 8.131 | 2767.374 | 0.714 |

## 2. Nisbatlar

ρ = mediana(CTE-rooted) / mediana(boshqa usul): ρ < 1 — CTE-rooted tezroq.

| Shakl | Hajm | Amal | ρ rooted/MPTT [CI] | ρ rooted/CTE [CI] |
|---|---|---|---|---|
| course_like | 1000 | shoxni o‘qish | 0.831 [0.763; 0.883] | 0.342 [0.323; 0.363] |
| course_like | 1000 | ajdodlarni o‘qish | 0.732 [0.643; 0.808] | 0.203 [0.18; 0.211] |
| course_like | 10000 | shoxni o‘qish | 0.312 [0.271; 0.372] | 0.055 [0.051; 0.062] |
| course_like | 10000 | ajdodlarni o‘qish | 0.61 [0.529; 0.703] | 0.03 [0.026; 0.036] |
| course_like | 100000 | shoxni o‘qish | 0.242 [0.217; 0.277] | 0.004 [0.003; 0.004] |
| course_like | 100000 | ajdodlarni o‘qish | 0.179 [0.163; 0.195] | 0.002 [0.001; 0.002] |
| deep_chain | 1000 | shoxni o‘qish | 5.735 [3.58; 6.783] | 0.152 [0.091; 0.173] |
| deep_chain | 1000 | ajdodlarni o‘qish | 7.023 [4.925; 8.321] | 0.198 [0.133; 0.239] |
| deep_chain | 10000 | shoxni o‘qish | 0.774 [0.48; 1.037] | 0.001 [0.001; 0.002] |
| deep_chain | 10000 | ajdodlarni o‘qish | 0.752 [0.527; 1.084] | 0.001 [0.001; 0.002] |
| deep_chain | 100000 | shoxni o‘qish | — | — |
| deep_chain | 100000 | ajdodlarni o‘qish | — | — |
| random | 1000 | shoxni o‘qish | 0.857 [0.746; 0.954] | 0.182 [0.154; 0.207] |
| random | 1000 | ajdodlarni o‘qish | 0.864 [0.727; 0.983] | 0.147 [0.135; 0.159] |
| random | 10000 | shoxni o‘qish | 0.365 [0.319; 0.373] | 0.02 [0.02; 0.02] |
| random | 10000 | ajdodlarni o‘qish | 0.43 [0.412; 0.465] | 0.01 [0.009; 0.012] |
| random | 100000 | shoxni o‘qish | 0.194 [0.181; 0.212] | 0.001 [0.001; 0.001] |
| random | 100000 | ajdodlarni o‘qish | 0.088 [0.08; 0.097] | 0 [0; 0] |

## 3. Dumi (p95) va SQL so‘rovlar

p95 da’voga kirmaydi (D63). So‘rovlar soni — `CaptureQueriesContext`,
har takrorda; uchala usulda ham tugun avval alohida so‘rov bilan olinadi.

| Shakl | Hajm | Amal | MPTT p95 | CTE p95 | CTE-rooted p95 | MPTT SQL | CTE SQL | CTE-rooted SQL |
|---|---|---|---|---|---|---|---|---|
| course_like | 1000 | shoxni o‘qish | 3.094 | 7.544 | 2.85 | 2 | 2 | 2 |
| course_like | 1000 | ajdodlarni o‘qish | 3.602 | 19.252 | 2.125 | 2 | 3 | 2 |
| course_like | 10000 | shoxni o‘qish | 6.857 | 49.378 | 1.99 | 2 | 2 | 2 |
| course_like | 10000 | ajdodlarni o‘qish | 3.563 | 64.151 | 2.171 | 2 | 3 | 2 |
| course_like | 100000 | shoxni o‘qish | 16.135 | 983.072 | 6.203 | 2 | 2 | 2 |
| course_like | 100000 | ajdodlarni o‘qish | 18.184 | 1692.104 | 3.58 | 2 | 3 | 2 |
| deep_chain | 1000 | shoxni o‘qish | 17.938 | 511.52 | 109.798 | 2 | 2 | 2 |
| deep_chain | 1000 | ajdodlarni o‘qish | 18.952 | 672.471 | 154.313 | 2 | 3 | 2 |
| deep_chain | 10000 | shoxni o‘qish | 145.763 | 39417.076 | 106.207 | 2 | 2 | 2 |
| deep_chain | 10000 | ajdodlarni o‘qish | 114.45 | 40875.844 | 76.616 | 2 | 3 | 2 |
| deep_chain | 100000 | shoxni o‘qish | tekshirib bo‘lmadi — kutubxonaning so‘rovi tugamadi | tekshirib bo‘lmadi — kutubxonaning so‘rovi tugamadi | tekshirib bo‘lmadi — kutubxonaning so‘rovi tugamadi | — | — | — |
| deep_chain | 100000 | ajdodlarni o‘qish | tekshirib bo‘lmadi — kutubxonaning so‘rovi tugamadi | tekshirib bo‘lmadi — kutubxonaning so‘rovi tugamadi | tekshirib bo‘lmadi — kutubxonaning so‘rovi tugamadi | — | — | — |
| random | 1000 | shoxni o‘qish | 1.198 | 6.433 | 1.078 | 2 | 2 | 2 |
| random | 1000 | ajdodlarni o‘qish | 1.589 | 8.25 | 1.224 | 2 | 3 | 2 |
| random | 10000 | shoxni o‘qish | 1.922 | 33.968 | 0.688 | 2 | 2 | 2 |
| random | 10000 | ajdodlarni o‘qish | 2.002 | 68.418 | 0.93 | 2 | 3 | 2 |
| random | 100000 | shoxni o‘qish | 8.236 | 1556.327 | 1.674 | 2 | 2 | 2 |
| random | 100000 | ajdodlarni o‘qish | 9.162 | 3312.537 | 0.992 | 2 | 3 | 2 |

## 4. To‘g‘rilik tekshiruvi (D74)

Har bir shakl uchun dastlabki nishonlarda qaytgan `id` lar to‘plami
kutubxonaning `descendants()` / `ancestors()` natijasi bilan solishtirildi.
Mos kelmagan tekshiruv bo‘lsa, o‘lchov umuman yozilmaydi.

- tekshiruvlar soni: 90
- mos kelmaganlari: 0
- tekshirib bo‘lmaganlari (kutubxonaning so‘rovi tugamadi): 10

## 5. O‘qish qoidasi (D74, natijadan oldin belgilangan)

> D74: har bir o‘lchangan o‘qish katagida cte_rooted / mptt nuqtaviy bahosi SLOWDOWN_LIMIT dan oshmasa — tavsiya tasdiqlandi

- chegara: 1.5
- o‘lchangan kataklar: 16
- o‘lchanmagan kataklar: 2
- chegaradan oshgan kataklar: 2

**Natija: tavsiya qisman tasdiqlandi**

Chegaradan oshgan kataklar:

| Shakl | Hajm | Amal | ρ rooted/MPTT |
|---|---|---|---|
| deep_chain | 1000 | read_branch | 5.735 |
| deep_chain | 1000 | read_ancestors | 7.023 |

H4 ning hukmi bu o‘lchovdan o‘zgarmaydi: u D63 da natijadan oldin
belgilangan qoida bo‘yicha chiqarilgan. Bu yerda faqat dissertatsiyaning
tavsiyasi tekshiriladi.

## 6. Daraxtlar

| Usul | Shakl | Hajm | Tugun | Maks. chuqurlik | sha256 |
|---|---|---|---|---|---|
| mptt | course_like | 1000 | 1000 | 3 | `dee517a825db` |
| cte | course_like | 1000 | 1000 | 3 | `dee517a825db` |
| mptt | course_like | 10000 | 10000 | 3 | `6eb0b80090fe` |
| cte | course_like | 10000 | 10000 | 3 | `6eb0b80090fe` |
| mptt | course_like | 100000 | 100000 | 3 | `4cd38264057b` |
| cte | course_like | 100000 | 100000 | 3 | `4cd38264057b` |
| mptt | deep_chain | 1000 | 1000 | 999 | `2c7d91e72f6a` |
| cte | deep_chain | 1000 | 1000 | 999 | `2c7d91e72f6a` |
| mptt | deep_chain | 10000 | 10000 | 9999 | `71aa31b40fef` |
| cte | deep_chain | 10000 | 10000 | 9999 | `71aa31b40fef` |
| mptt | deep_chain | 100000 | 100000 | 99999 | `6cc718522da2` |
| cte | deep_chain | 100000 | 100000 | 99999 | `6cc718522da2` |
| mptt | random | 1000 | 1000 | 12 | `f92083ccb676` |
| cte | random | 1000 | 1000 | 12 | `f92083ccb676` |
| mptt | random | 10000 | 10000 | 17 | `bc4155b2e63d` |
| cte | random | 10000 | 10000 | 17 | `bc4155b2e63d` |
| mptt | random | 100000 | 100000 | 24 | `046e0183f27b` |
| cte | random | 100000 | 100000 | 24 | `046e0183f27b` |

## 7. Muhit

- PostgreSQL: 16.15 (Debian 16.15-1.pgdg13+2)
- baza: `neurolearn_bench`
- umumiy vaqt (soniya): 3988.485

## 8. Manba va ishga tushirish (D48)

- kod commit'i: `309fe20`
- buyruq: `python manage.py run_rooted_benchmark --database benchmark --shapes course_like,deep_chain,random --warmups 5 --repeats 30 --timeout 120.0 --seed 20261006 --memory-limit-gb 8.0`
- vaqt: 2026-11-18T06:30:42.462996+00:00
- python: 3.12.3, Linux-7.0.0-43-generic-x86_64-with-glibc2.43
- git holati boshida: `309fe20`, toza (2026-11-18T05:24:13.921986+00:00)
- git holati oxirida: `309fe20`, toza (2026-11-18T06:30:42.462478+00:00)
- seed: bootstrap = 20261006, targets = 20261006, trees = 20261006
- paketlar: django 6.0.5, django-mptt 0.18.0, django-tree-queries 0.24.0, psycopg 3.3.6

| Fayl | sha256 | Bayt |
|---|---|---|
| — | — | — |

