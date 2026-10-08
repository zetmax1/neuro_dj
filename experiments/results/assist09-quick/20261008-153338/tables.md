# H2 — ASSISTments 2009–2010 skill builder: modellarni solishtirish

Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.

Baholash protokoli: D57 — har bir qator faqat talabaning oldingi
masalalaridagi (`order_id`) javoblardan bashorat qilinadi.

> **`--quick` ishga tushirish — dissertatsiya natijasi emas.** Bu quvurni
> sinash uchun: talabalarning bir qismi va kam epoch. To‘liq natija uchun
> `python -m experiments.h2` bayroqsiz ishga tushiriladi.

## 1. Pooled natija (barcha qismlar birga)

AUC uchun 95% ishonch oralig‘i — talabalar bo‘yicha bootstrap (javoblar talaba ichida klasterlangan).

| Model | AUC [95% CI] | RMSE | Aniqlik | Javob |
|---|---|---|---|---|
| BKT | 0.697 [0.683, 0.71] | 0.432 | 0.736 | 53652 |
| BKT+IRT (λ=0) | 0.71 [0.697, 0.723] | 0.431 | 0.736 | 53652 |
| BKT+IRT+Pre | ishga tushirilmadi: prerekvizit grafi yo‘q — ASSISTments 2009 uchun E_P mavjud emas (D53) | — | — | — |
| Elo/Rasch | 0.696 [0.682, 0.711] | 0.431 | 0.729 | 53652 |
| PFA | 0.7 [0.686, 0.714] | 0.427 | 0.737 | 53652 |
| DKT | 0.646 [0.634, 0.658] | 0.454 | 0.711 | 53652 |
| AKT | 0.669 [0.655, 0.684] | 0.439 | 0.713 | 53652 |

## 2. Dastlabki urinishlar (AUC)

Har bir talabaning birinchi k javobi alohida. Prerekvizitga asoslangan
boshlang‘ich qiymat faqat shu yerda ta’sir ko‘rsatishi mumkin: o‘ninchi
javobda dalil har qanday priordan ustun bo‘lib ketadi.

`Tarixsiz` — modelning tarixdan bashorat qila olmagan javoblari soni:
ular base rate bilan baholanadi. Ketma-ketlik modellarida har bir talaba
uchun bitta shunday javob bor, ya’ni k = 3 ustunining uchdan biri doimiy
qiymat — shuning uchun DKT va AKT ning dastlabki ustunlari modelga nisbatan
pastroq o‘qiladi.

| Model | Hammasi | Birinchi 3 | Birinchi 5 | Tarixsiz |
|---|---|---|---|---|
| BKT | 0.697 | 0.677 | 0.699 | 0 |
| BKT+IRT (λ=0) | 0.71 | 0.685 | 0.705 | 0 |
| Elo/Rasch | 0.696 | 0.678 | 0.704 | 0 |
| PFA | 0.7 | 0.679 | 0.693 | 0 |
| DKT | 0.646 | 0.496 | 0.55 | 816 |
| AKT | 0.669 | 0.611 | 0.652 | 816 |

## 3. Juftlik solishtirishlari (DeLong, Holm tuzatmasi bilan)

Juftlashgan test: ikki model bir xil javoblarda baholangan, shuning uchun
AUC'lar orasidagi korrelyatsiya ayiriladi. Holm — butun juftliklar
oilasi uchun.

**Ikki cheklov ochiq aytiladi.**

1. DeLong javoblarni mustaqil deb hisoblaydi, bu jadvaldagi prognozlar esa
   besh qismdan birlashtirilgan va talaba ichida klasterlangan. Shuning uchun
   bu yerdagi p qiymatlari haqiqiydan **kichik** bo‘lishi mumkin. Yuqoridagi
   birinchi jadvaldagi ishonch oralig‘i talabalar bo‘yicha bootstrap bilan
   olingan va shu
   ma’noda ishonchliroq; DeLong juftliklarni tartiblash uchun ishlatiladi,
   oralig‘ni belgilash uchun emas.
2. BKT, BKT+IRT va BKT+IRT+Pre bir xil moslangan P0/PT/P(G)/P(S) ni
   bo‘lishadi (`parameters.shared_by_flag_variants`). Ablatsiya bitta
   narsani o‘zgartirishi kerak, shuning uchun bayroq o‘zgaradi, moslash
   emas. Bu IRT variantlari uchun kichik noqulaylik: parametrlar ular uchun
   optimallashtirilmagan.

| A | B | AUC A | AUC B | Farq | z | p | p (Holm) | Muhim |
|---|---|---|---|---|---|---|---|---|
| BKT | BKT+IRT (λ=0) | 0.697 | 0.71 | -0.013 | -22.449 | 0 | 0 | ha |
| BKT | DKT | 0.697 | 0.646 | 0.051 | 19.773 | 0 | 0 | ha |
| BKT | AKT | 0.697 | 0.669 | 0.027 | 11.318 | 0 | 0 | ha |
| BKT+IRT (λ=0) | PFA | 0.71 | 0.7 | 0.01 | 6.414 | 0 | 0 | ha |
| BKT+IRT (λ=0) | DKT | 0.71 | 0.646 | 0.064 | 25.263 | 0 | 0 | ha |
| BKT+IRT (λ=0) | AKT | 0.71 | 0.669 | 0.041 | 17.718 | 0 | 0 | ha |
| Elo/Rasch | DKT | 0.696 | 0.646 | 0.05 | 15.307 | 0 | 0 | ha |
| Elo/Rasch | AKT | 0.696 | 0.669 | 0.027 | 10.012 | 0 | 0 | ha |
| PFA | DKT | 0.7 | 0.646 | 0.054 | 19.291 | 0 | 0 | ha |
| PFA | AKT | 0.7 | 0.669 | 0.03 | 11.992 | 0 | 0 | ha |
| DKT | AKT | 0.646 | 0.669 | -0.024 | -8.299 | 0 | 0 | ha |
| BKT+IRT (λ=0) | Elo/Rasch | 0.71 | 0.696 | 0.014 | 5.472 | 0 | 0 | ha |
| BKT | PFA | 0.697 | 0.7 | -0.003 | -1.864 | 0.062 | 0.187 | yo‘q |
| Elo/Rasch | PFA | 0.696 | 0.7 | -0.004 | -1.329 | 0.184 | 0.368 | yo‘q |
| BKT | Elo/Rasch | 0.697 | 0.696 | 0.001 | 0.245 | 0.806 | 0.806 | yo‘q |

### Gipoteza farqlari

A − B, gipotezadagi yo‘nalishda. Oraliq — talabalar bo‘yicha juftlangan
bootstrap: har bir replikatda ikkala model uchun bir xil talabalar olinadi.
p — yuqoridagi oiladagi o‘sha juftlikning DeLong p qiymati.

| A − B | Qaror | Farq [95% CI] | DeLong p | p (Holm) |
|---|---|---|---|---|
| BKT+IRT (λ=0) − BKT | D53 | 0.013 [0.012, 0.015] | 0 | 0 |
| BKT+IRT (λ=0) − DKT | D56 | 0.064 [0.056, 0.072] | 0 | 0 |

## 4. Qismlar bo‘yicha AUC

Bo‘lish talabalar bo‘yicha: bitta talabaning javoblari hech qachon
o‘qitish va test to‘plamlariga bo‘linmaydi.

| Model | 1-qism | 2-qism | 3-qism | 4-qism | 5-qism |
|---|---|---|---|---|---|
| BKT | 0.727 | 0.717 | 0.667 | 0.682 | 0.687 |
| BKT+IRT (λ=0) | 0.738 | 0.729 | 0.684 | 0.698 | 0.7 |
| Elo/Rasch | 0.716 | 0.71 | 0.675 | 0.691 | 0.682 |
| PFA | 0.732 | 0.712 | 0.667 | 0.691 | 0.692 |
| DKT | 0.671 | 0.635 | 0.616 | 0.65 | 0.652 |
| AKT | 0.716 | 0.681 | 0.64 | 0.666 | 0.669 |

## 5. Aqlga muvofiqlik chegarasi (D53)

- DKT AUC: 0.646
- kutilgan oraliq: 0.7–0.8
- adabiyotdagi qiymat (Xiong va boshq., EDM 2016, takrorsiz): 0.73–0.75
- oraliq ichidami: yo‘q

> **Ogohlantirish.** DKT AUC takrorlari olib tashlangan ma’lumot uchun
> qayd etilgan oraliqdan tashqarida. Jadvaldagi boshqa hech narsani o‘qishdan oldin
> D50 tozalashini qayta tekshirish kerak. `--quick` ishga tushirishda bu
> kutilgan: kam talaba va kam epoch bilan DKT to‘liq o‘qitilmaydi.

## 6. Grid tekshiruvi — moslash grid chetiga tegdimi

Eng yuqori ruxsat etilgan qiymatda to‘planib qolgan moslash — moslash emas,
grid'ning “ma’lumot men bera oladigandan ko‘proq xohlaydi” deyishi.

`P0` va `PT` uchun bu grid torligini bildiradi va grid kengaytirilishi kerak.
`P(G)` va `P(S)` uchun boshqa narsani: ularning shiftini grid emas, II bob
belgilaydi (G_MAX = 0.3, S_MAX = 0.1),
chunki γ chegarada aniqlanmagan. Ya’ni u yerdagi to‘planish — chegara
ishlayotgani, va grid'ni kengaytirish moslashni yaxshilamaydi, modelni buzadi.
Shu ishga tushirishdagi pyBKT solishtirishi bunga tashqi dalil: uning EM'ida
chegara yo‘q.

Jami moslash: 420 (5 qismda)

| Parametr | Ruxsat etilgan qiymatlar | Eng pastda | Eng yuqorida | Yuqoridagilar ulushi | Shiftni kim belgilaydi |
|---|---|---|---|---|---|
| P0 | 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9 | 37 | 58 | 0.138 | grid |
| PT | 0.05, 0.1, 0.15, 0.2, 0.3, 0.4 | 84 | 130 | 0.309 | grid |
| P(G) | 0.05, 0.1, 0.15, 0.2, 0.25, 0.29 | 23 | 332 | 0.79 | II bob |
| P(S) | 0.01, 0.03, 0.05, 0.07, 0.09, 0.097 | 7 | 363 | 0.864 | II bob |

## 7. pyBKT bilan o‘zaro tekshiruv (D53)

Bir xil mavzular ikki marta moslanadi: `neuro_model.calibrate` ning
chegaralangan grid search'i va pyBKT ning EM'i. Farqning tizimli sababi —
II bobning chegaralari (G_MAX = 0.3, S_MAX = 0.1), pyBKT ularni bilmaydi. Ikkala
parametr to‘plami bir xil ta’rif bilan baholanadi: `calibrate.log_likelihood`.

Chegaradan tashqarida chiqqan pyBKT baholari: 5 / 5

| Mavzu | Javob | P0 (grid / EM) | PT | P(G) | P(S) | logL (grid / EM) | EM chegaradan tashqarida |
|---|---|---|---|---|---|---|---|
| 311 | 3805 | 0.5 / 0.714 | 0.05 / 0.036 | 0.29 / 0.317 | 0.097 / 0.219 | -2323.05 / -2191.866 | G0, S0 |
| 47 | 2427 | 0.7 / 0.757 | 0.05 / 0.022 | 0.29 / 0.459 | 0.097 / 0.17 | -1360.261 / -1291.092 | G0, S0 |
| 75 | 1732 | 0.7 / 0.783 | 0.15 / 0.118 | 0.29 / 0.369 | 0.097 / 0.181 | -925.342 / -878.364 | G0, S0 |
| 50 | 1575 | 0.7 / 0.633 | 0.1 / 0.114 | 0.29 / 0.428 | 0.09 / 0.074 | -673.569 / -665.707 | G0 |
| 85 | 1373 | 0.8 / 0.545 | 0.3 / 0.103 | 0.29 / 0.657 | 0.097 / 0.047 | -546.051 / -533.038 | G0 |

## 8. Ma’lumot va tozalash (D50)

- xom qatorlar: 525534, talabalar: 4217, bo‘sh `skill_id`: 66326
- tozalangandan keyin: 338001 qator, 4163 talaba, 123 mavzu, bir nechta skill'li `order_id`: 47037
- ishlatilgan: 53652 javob, 500 talaba
- `--original-only`: yo‘q
- bo‘lish: 5 qism, talabalar bo‘yicha, validatsiya ulushi 0.2, seed 20261006
- DKT/AKT epoch chegarasi: 3

Tozalash qoidalari (D50, o‘zgarmas):

1. drop rows with an empty skill_id
1. de-duplicate on (order_id, skill_id), keeping the first occurrence
1. order by user_id, then order_id
1. original is a flag (--original-only), off by default

## 9. Manba va ishga tushirish (D48)

- kod commit'i: `2f7365b`
- buyruq: `python -m experiments.h2 --quick`
- vaqt: 2026-10-08T15:33:38.904775+00:00
- python: 3.12.3, Linux-7.0.0-38-generic-x86_64-with-glibc2.43
- git holati boshida: `2f7365b`, toza (2026-10-08T15:10:00.440628+00:00)
- git holati oxirida: `2f7365b`, toza (2026-10-08T15:33:38.904749+00:00)
- seed: bootstrap = 20261006, models = 20261006, split = 20261006
- paketlar: numpy 1.26.4, pandas 2.3.3, pyBKT 1.4.3, pykt 0.0.38, scipy 1.14.1, sklearn 1.6.1, torch 2.5.1+cpu

| Fayl | sha256 | Bayt |
|---|---|---|
| `assistments2009` | `f22e3fb7872c1784ce93b0f9ebabbe0cbcac4f896fd8b4a11667b9715d77dbdc` | 83201940 |


## 10. Masalaning birinchi qatorlari (D57, sezgirlik)

Har bir masalaning (`order_id`) faqat birinchi qatori. Asosiy natija emas:
bu qatorlarda hech bir model shu masalaning boshqa qatorini ko‘rmagan.

| Model | AUC | RMSE | Aniqlik | Javob |
|---|---|---|---|---|
| BKT | 0.694 | 0.431 | 0.736 | 44994 |
| BKT+IRT (λ=0) | 0.708 | 0.43 | 0.737 | 44994 |
| Elo/Rasch | 0.697 | 0.429 | 0.732 | 44994 |
| PFA | 0.696 | 0.426 | 0.739 | 44994 |
| DKT | 0.645 | 0.452 | 0.715 | 44994 |
| AKT | 0.667 | 0.437 | 0.717 | 44994 |

