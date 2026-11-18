# H2 — ASSISTments 2009–2010 skill builder: modellarni solishtirish

Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.

Baholash protokoli: D57 — har bir qator faqat talabaning oldingi
masalalaridagi (`order_id`) javoblardan bashorat qilinadi.

## 1. Pooled natija (barcha qismlar birga)

AUC uchun 95% ishonch oralig‘i — talabalar bo‘yicha bootstrap (javoblar talaba ichida klasterlangan).

| Model | AUC [95% CI] | RMSE | Aniqlik | Javob |
|---|---|---|---|---|
| BKT | 0.707 [0.701, 0.714] | 0.449 | 0.705 | 338001 |
| BKT+IRT (λ=0) | 0.723 [0.717, 0.73] | 0.446 | 0.707 | 338001 |
| BKT+IRT+Pre | ishga tushirilmadi: prerekvizit grafi yo‘q — ASSISTments 2009 uchun E_P mavjud emas (D53) | — | — | — |
| Elo/Rasch | 0.762 [0.757, 0.767] | 0.427 | 0.727 | 338001 |
| PFA | 0.704 [0.698, 0.71] | 0.446 | 0.699 | 338001 |
| DKT | 0.727 [0.721, 0.733] | 0.441 | 0.71 | 338001 |
| AKT | 0.708 [0.701, 0.715] | 0.447 | 0.711 | 338001 |

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
| BKT | 0.707 | 0.681 | 0.702 | 0 |
| BKT+IRT (λ=0) | 0.723 | 0.688 | 0.708 | 0 |
| Elo/Rasch | 0.762 | 0.686 | 0.709 | 0 |
| PFA | 0.704 | 0.669 | 0.681 | 0 |
| DKT | 0.727 | 0.646 | 0.691 | 6010 |
| AKT | 0.708 | 0.634 | 0.673 | 6010 |

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
| BKT | BKT+IRT (λ=0) | 0.707 | 0.723 | -0.016 | -90.618 | 0 | 0 | ha |
| BKT | Elo/Rasch | 0.707 | 0.762 | -0.055 | -56.762 | 0 | 0 | ha |
| BKT | DKT | 0.707 | 0.727 | -0.02 | -26.108 | 0 | 0 | ha |
| BKT+IRT (λ=0) | Elo/Rasch | 0.723 | 0.762 | -0.039 | -43.99 | 0 | 0 | ha |
| BKT+IRT (λ=0) | PFA | 0.723 | 0.704 | 0.019 | 33.867 | 0 | 0 | ha |
| BKT+IRT (λ=0) | AKT | 0.723 | 0.708 | 0.015 | 19.277 | 0 | 0 | ha |
| Elo/Rasch | PFA | 0.762 | 0.704 | 0.058 | 61.934 | 0 | 0 | ha |
| Elo/Rasch | DKT | 0.762 | 0.727 | 0.035 | 38.146 | 0 | 0 | ha |
| Elo/Rasch | AKT | 0.762 | 0.708 | 0.054 | 61.337 | 0 | 0 | ha |
| PFA | DKT | 0.704 | 0.727 | -0.023 | -28.576 | 0 | 0 | ha |
| DKT | AKT | 0.727 | 0.708 | 0.019 | 28.045 | 0 | 0 | ha |
| BKT+IRT (λ=0) | DKT | 0.723 | 0.727 | -0.004 | -5.313 | 0 | 0 | ha |
| BKT | PFA | 0.707 | 0.704 | 0.003 | 5.025 | 0 | 0 | ha |
| PFA | AKT | 0.704 | 0.708 | -0.004 | -4.386 | 0 | 0 | ha |
| BKT | AKT | 0.707 | 0.708 | -0.001 | -1.138 | 0.255 | 0.255 | yo‘q |

### Gipoteza farqlari

A − B, gipotezadagi yo‘nalishda. Oraliq — talabalar bo‘yicha juftlangan
bootstrap: har bir replikatda ikkala model uchun bir xil talabalar olinadi.
p — yuqoridagi oiladagi o‘sha juftlikning DeLong p qiymati.

| A − B | Qaror | Farq [95% CI] | DeLong p | p (Holm) |
|---|---|---|---|---|
| BKT+IRT (λ=0) − BKT | D53 | 0.016 [0.015, 0.017] | 0 | 0 |
| BKT+IRT (λ=0) − DKT | D56 | -0.004 [-0.006, -0.002] | 0 | 0 |

## 4. Qismlar bo‘yicha AUC

Bo‘lish talabalar bo‘yicha: bitta talabaning javoblari hech qachon
o‘qitish va test to‘plamlariga bo‘linmaydi.

| Model | 1-qism | 2-qism | 3-qism | 4-qism | 5-qism |
|---|---|---|---|---|---|
| BKT | 0.712 | 0.718 | 0.696 | 0.711 | 0.698 |
| BKT+IRT (λ=0) | 0.728 | 0.733 | 0.713 | 0.727 | 0.715 |
| Elo/Rasch | 0.764 | 0.767 | 0.756 | 0.763 | 0.758 |
| PFA | 0.711 | 0.713 | 0.696 | 0.707 | 0.694 |
| DKT | 0.732 | 0.735 | 0.718 | 0.732 | 0.719 |
| AKT | 0.708 | 0.728 | 0.689 | 0.706 | 0.717 |

## 5. Aqlga muvofiqlik chegarasi (D53)

- DKT AUC: 0.727
- kutilgan oraliq: 0.7–0.8
- adabiyotdagi qiymat (Xiong va boshq., EDM 2016, takrorsiz): 0.73–0.75
- oraliq ichidami: ha

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

Jami moslash: 555 (5 qismda)

| Parametr | Ruxsat etilgan qiymatlar | Eng pastda | Eng yuqorida | Yuqoridagilar ulushi | Shiftni kim belgilaydi |
|---|---|---|---|---|---|
| P0 | 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9 | 48 | 61 | 0.11 | grid |
| PT | 0.05, 0.1, 0.15, 0.2, 0.3, 0.4 | 133 | 84 | 0.151 | grid |
| P(G) | 0.05, 0.1, 0.15, 0.2, 0.25, 0.29 | 16 | 434 | 0.782 | II bob |
| P(S) | 0.01, 0.03, 0.05, 0.07, 0.09, 0.097 | 12 | 487 | 0.877 | II bob |

## 7. pyBKT bilan o‘zaro tekshiruv (D53)

Bir xil mavzular ikki marta moslanadi: `neuro_model.calibrate` ning
chegaralangan grid search'i va pyBKT ning EM'i. Farqning tizimli sababi —
II bobning chegaralari (G_MAX = 0.3, S_MAX = 0.1), pyBKT ularni bilmaydi. Ikkala
parametr to‘plami bir xil ta’rif bilan baholanadi: `calibrate.log_likelihood`.

Chegaradan tashqarida chiqqan pyBKT baholari: 5 / 5

| Mavzu | Javob | P0 (grid / EM) | PT | P(G) | P(S) | logL (grid / EM) | EM chegaradan tashqarida |
|---|---|---|---|---|---|---|---|
| 311 | 2813 | 0.5 / 0.707 | 0.05 / 0.049 | 0.29 / 0.318 | 0.097 / 0.208 | -1670.232 / -1587.966 | G0, S0 |
| 47 | 2700 | 0.6 / 0.72 | 0.05 / 0.022 | 0.29 / 0.434 | 0.097 / 0.215 | -1689.816 / -1563.976 | G0, S0 |
| 75 | 1617 | 0.6 / 0.759 | 0.1 / 0.084 | 0.29 / 0.322 | 0.097 / 0.177 | -865.238 / -827.488 | G0, S0 |
| 50 | 1564 | 0.7 / 0.625 | 0.1 / 0.082 | 0.29 / 0.462 | 0.097 / 0.08 | -736.775 / -724.852 | G0 |
| 85 | 1309 | 0.9 / 0.793 | 0.1 / 0.1 | 0.29 / 0.487 | 0.097 / 0.087 | -526.244 / -523.416 | G0 |

## 8. Ma’lumot va tozalash (D50)

- xom qatorlar: 525534, talabalar: 4217, bo‘sh `skill_id`: 66326
- tozalangandan keyin: 338001 qator, 4163 talaba, 123 mavzu, bir nechta skill'li `order_id`: 47037
- ishlatilgan: 338001 javob, 4163 talaba
- `--original-only`: yo‘q
- bo‘lish: 5 qism, talabalar bo‘yicha, validatsiya ulushi 0.2, seed 20261006
- DKT/AKT epoch chegarasi: 10

Tozalash qoidalari (D50, o‘zgarmas):

1. drop rows with an empty skill_id
1. de-duplicate on (order_id, skill_id), keeping the first occurrence
1. order by user_id, then order_id
1. original is a flag (--original-only), off by default

## 9. Manba va ishga tushirish (D48)

- kod commit'i: `e97621c`
- buyruq: `python -m experiments.h2`
- vaqt: 2026-10-09T05:54:43.373827+00:00
- python: 3.12.3, Linux-7.0.0-38-generic-x86_64-with-glibc2.43
- git holati boshida: `e97621c`, toza (2026-10-09T03:38:25.396928+00:00)
- git holati oxirida: `e97621c`, toza (2026-10-09T05:54:43.373800+00:00)
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
| BKT | 0.704 | 0.448 | 0.706 | 283105 |
| BKT+IRT (λ=0) | 0.721 | 0.446 | 0.707 | 283105 |
| Elo/Rasch | 0.764 | 0.425 | 0.729 | 283105 |
| PFA | 0.7 | 0.446 | 0.699 | 283105 |
| DKT | 0.737 | 0.434 | 0.718 | 283105 |
| AKT | 0.711 | 0.443 | 0.713 | 283105 |

