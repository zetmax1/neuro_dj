# H1 — Junyi Academy (2015): tayyorlik qoidalari

Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.

Birlik — javob emas, **qaror**: talabaning mashqqa birinchi urinishi,
prerekvizitlari bor va kamida bittasi oldin ishlangan (D61). Shu paytda
qoidalar “bu talaba tayyormi?” degan savolga javob beradi; keyin
talabaning o‘sha mashqdagi dastlabki javoblari qoidani tekshiradi.

P(L) — BKT+IRT (λ=0) oqimidan; r_s(w), R_s(w) va M — `neuro_model.readiness`,
ya’ni platformaning o‘zi chaqiradigan funksiyalar. Javob berilmagan
prerekvizit platformadagidek P(L) = 0 va M = yo‘q bilan kiradi.

## 1. Qoidalar (II bobning τ va δ si bilan)

τ = 0.95, δ = 0.1, `pass_mark` = 0.6; muvaffaqiyatsizlik — mashqdagi dastlabki k = 3 javobda to‘g‘rilar ulushi 0.5 dan kam.

Voqea: 9664, talaba: 695, mavzu: 504; o‘rtacha prerekvizit soni 1.581.

| Qoida | Oila | Voqea | Belgilangan | Xato | Qamrov | Xato ulushi |
|---|---|---|---|---|---|---|
| ehtimoliy (r ≥ τ) | II bob | 9664 | 6795 | 1023 | 0.703 | 0.151 |
| II bob R (M, δ bilan) | II bob | 9664 | 6803 | 1027 | 0.704 | 0.151 |
| bajarilganlik | taqqoslash | 9664 | 7136 | 1189 | 0.738 | 0.167 |
| o‘tish bali | taqqoslash | 9664 | 9239 | 1411 | 0.956 | 0.153 |
| earned_proficiency | platforma | 9664 | 6532 | 956 | 0.676 | 0.146 |

## 2. Teng qamrov

Qamrov va xato ulushi birga harakat qiladi, shuning uchun taqqoslash teng
qamrovda qilinadi: τ validatsiya qismida taqqoslanadigan qoidaning
qamroviga moslanadi, o‘lchov esa test qismida (D62). τ ustuni — har bir
fold uchun tanlangan qiymat.

Farqning ishonch oralig‘i — talabalar bo‘yicha klasterlangan bootstrap, 1000 replika, 95 %.

Oxirgi uch ustun — sezgirlik (D62a): faqat mashqda kamida k ta javobi
bor voqealar. p — bootstrap'dan, ikki tomonlama; Holm — ehtimoliy
qoidaning ikki taqqoslashi bitta oila. O‘qish qoidasi CI ga qaraydi.

| Qoida | τ (fold'lar bo‘yicha) | Ehtimoliy qamrov | Qoida qamrovi | Ehtimoliy xato ulushi | Qoida xato ulushi | Farq [CI] | p | Holm p | To‘liq oyna: ehtimoliy | To‘liq oyna: qoida | To‘liq oyna: voqea |
|---|---|---|---|---|---|---|---|---|---|---|---|
| bajarilganlik | 0.028, 0.007, 0.006, 0.009, 0.017 | 0.738 | 0.738 | 0.167 | 0.167 | -0 [-0, 0] | 0.92 | 0.92 | 0.13 | 0.13 | 8384 |
| o‘tish bali | 0, 0, 0, 0, 0 | 1 | 0.956 | 0.169 | 0.153 | 0.017 [0.012, 0.022] | 0 | 0 | 0.131 | 0.121 | 8384 |

## 3. O‘qish qoidasi (natijadan oldin yozilgan)

teng qamrovda ehtimoliy qoidaning xato ulushi bajarilganlik va o‘tish bali qoidalaridan past bo‘lsa va farqlarning 95 % CI si nolni kesib o‘tmasa — qo‘llab-quvvatlandi (D61)

**Xulosa: qo‘llab-quvvatlanmadi.**

cheklov: Junyi platformasi mashqni uning prerekvizitlari o‘zlashtirilgach tavsiya qiladi (suggested), shuning uchun ta’sirning bir qismi grafning o‘zidan emas, platformaning shu graf bo‘yicha yo‘naltirishidan kelishi mumkin (D62a). Tanlangan namunada `suggested` ulushi: 0.218.

| Taqqoslash | Farq | CI | Xulosa |
|---|---|---|---|
| bajarilganlik | -0 | [-0, 0] | aniqlanmadi |
| o‘tish bali | 0.017 | [0.012, 0.022] | qo‘llab-quvvatlanmadi |

## 4. r_s(w) bo‘yicha AUC

Qoidaning emas, qoida ortidagi **bahoning** ajrata olishi: r_s(w) ning
“talaba bu mashqda muvaffaqiyatsiz bo‘lmaydi” ni bashorat qilishi.

| k | Voqea | Muvaffaqiyatsiz | AUC [CI] |
|---|---|---|---|
| 3 | 9664 | 1637 | 0.519 [0.501, 0.537] |
| 5 | 9664 | 1365 | 0.523 [0.504, 0.542] |

## 5. τ × δ sezgirligi

δ faqat M ga (gisterezisga) ta’sir qiladi, shuning uchun ehtimoliy
qoidaning ustunlari har bir τ ichida o‘zgarmaydi — jadval aynan shuni
ko‘rsatish uchun ikkisini yonma-yon qo‘yadi.

| τ | δ | II bob qamrovi | II bob xato ulushi | Ehtimoliy qamrov | Ehtimoliy xato ulushi |
|---|---|---|---|---|---|
| 0.7 | 0.05 | 0.709 | 0.152 | 0.709 | 0.152 |
| 0.7 | 0.1 | 0.709 | 0.152 | 0.709 | 0.152 |
| 0.7 | 0.15 | 0.709 | 0.152 | 0.709 | 0.152 |
| 0.8 | 0.05 | 0.707 | 0.152 | 0.707 | 0.152 |
| 0.8 | 0.1 | 0.708 | 0.151 | 0.707 | 0.152 |
| 0.8 | 0.15 | 0.708 | 0.152 | 0.707 | 0.152 |
| 0.9 | 0.05 | 0.706 | 0.151 | 0.706 | 0.151 |
| 0.9 | 0.1 | 0.706 | 0.152 | 0.706 | 0.151 |
| 0.9 | 0.15 | 0.706 | 0.152 | 0.706 | 0.151 |
| 0.95 | 0.05 | 0.704 | 0.151 | 0.703 | 0.151 |
| 0.95 | 0.1 | 0.704 | 0.151 | 0.703 | 0.151 |
| 0.95 | 0.15 | 0.704 | 0.151 | 0.703 | 0.151 |

## 6. Qismlar

Bo‘lish talabalar bo‘yicha: bitta talabaning javoblari hech qachon
o‘qitish va test to‘plamlariga bo‘linmaydi.

| Fold (indeks) | Train | Validatsiya | Test | Test javob | Test voqea | Validatsiya voqea |
|---|---|---|---|---|---|---|
| 0 | 1280 | 320 | 400 | 46539 | 1756 | 2020 |
| 1 | 1280 | 320 | 400 | 54545 | 2348 | 1995 |
| 2 | 1280 | 320 | 400 | 37800 | 1498 | 1703 |
| 3 | 1280 | 320 | 400 | 54386 | 2089 | 2332 |
| 4 | 1280 | 320 | 400 | 59467 | 1973 | 1247 |

## 7. Ma'lumot

- to‘plam: Junyi Academy (2015)
- litsenziya: Any form of commercial usage is not allowed! (junyi/README.md)
- iqtibos: Haw-Shiuan Chang, Hwai-Jung Hsu and Kuan-Ta Chen, “Modeling Exercise Relationships in E-Learning: A Unified Approach”, EDM 2015

| Ko‘rsatkich | Qiymat |
|---|---|
| mashqlar jadvalidagi qator | 837 |
| noyob mashq | 835 |
| area | 9 |
| topic | 41 |
| o‘qilgan prerekvizit yozuvi | 984 |
| noyob qirra | 979 |
| o‘z-o‘ziga qirra (Y2, tashlangan) | 2 |
| takroriy qirra | 3 |
| nomi topilmagan prerekvizit | 0 |
| birlashtirilgan SCC | 1 |
| birlashtirilgan tugun | 3 |
| mavzu (birlashtirilgandan keyin) | 833 |
| qirra (birlashtirilgandan keyin) | 976 |
| eng uzun yo‘l | 65 |
| prerekvizitsiz mavzu | 97 |
| logdagi qator (butun fayl) | 25925992 |
| logdagi talaba (butun fayl) | 247606 |
| tanlangan talaba | 2000 |
| ishlatilgan javob | 252737 |
| ishlatilgan mavzu | 619 |

Tozalash qoidalari (D61):

- keep only exercises present in the exercise table
- correct is the published first-attempt column; nothing is recomputed
- order by learner, then time_done (µs), then problem_number, then file order
- one answer is one order: order_id is per row (D57)
- review_mode answers are kept; topic_mode and suggested are metadata only
- live is metadata, not a filter

## 8. Manba va ishga tushirish (D48)

- kod commit'i: `2500c77`
- buyruq: `python -m experiments.h1 --workers 5`
- vaqt: 2026-10-19T10:25:25.927625+00:00
- python: 3.12.3, Linux-7.0.0-38-generic-x86_64-with-glibc2.43
- git holati boshida: `2500c77`, toza (2026-10-19T09:47:48.850992+00:00)
- git holati oxirida: `2500c77`, toza (2026-10-19T10:25:25.927605+00:00)
- seed: bootstrap = 20261006, sample = 20261006, split = 20261006
- paketlar: numpy 1.26.4, pandas 2.3.3, pyBKT 1.4.3, pykt 0.0.38, scipy 1.14.1, sklearn 1.6.1, torch 2.5.1+cpu

| Fayl | sha256 | Bayt |
|---|---|---|
| `junyi-exercise-table` | `13292cc2c809985abbacedaba434e39aeb02a7fcb2a32f17b60c4d3f4d769546` | 139957 |
| `junyi-problem-log` | `a7c99ede1f9b19648fdcd953b6ca0b0282bd31f2f913bd9d26b23aa9fcb36a25` | 2668566436 |

