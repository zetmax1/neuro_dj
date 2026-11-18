# H2 (D73) — neyron modellar to‘liq o‘qitilganda: post-hoc sezgirlik

Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.

> **Bu H2 ning hukmi emas.** H2 ning hukmi asosiy natijada, natijadan
> oldin belgilangan qoida bo‘yicha chiqarilgan (D56, D59) va bu yerda
> qayta ko‘rilmaydi. Bu jadval bitta savolga javob beradi: neyron
> modellarga to‘liq o‘qitish imkoni berilganda taqqoslash qanday ko‘rinadi.

Ma’lumot, tozalash, foldlar, seed va D57 baholash tartibi asosiy
natijadagi kodning o‘zi (`h2.prepare`, `h2.fold_sets`, `h2.fit_predict`,
`h2.analyse_pooled`). Faqat giperparametrlar va to‘xtash shartlari boshqa.

> **`--quick` ishga tushirish — dissertatsiya natijasi emas.**

## 1. O‘qitish sozlamalari

- ko‘pi bilan epoch: 4
- sabr (patience): 2 (pyKT ning `train_model` kodida: 10)
- yaxshilanish chegarasi: 0 (pyKT da 0.001 — kichikroq chegara kechroq to‘xtatadi, ya’ni DKT foydasiga)
- nomzod tanlanadigan metrika: `validation_auc`
- DKT to‘ri: 12 nomzod; AKT/AKT-R: 2 nomzod

## 2. Pooled natija

| Model | AUC [CI] | RMSE | Aniqlik | Sovuq qatorlar |
|---|---|---|---|---|
| BKT+IRT (λ=0) | 0.71 [0.697; 0.723] | 0.431 | 0.735 | 0 |
| DKT | 0.694 [0.682; 0.708] | 0.431 | 0.733 | 816 |
| AKT | 0.674 [0.66; 0.688] | 0.437 | 0.717 | 816 |
| AKT-R | 0.675 [0.661; 0.69] | 0.439 | 0.705 | 816 |

## 3. H2 ning farqlari

Farq — platformaning modeli minus taqqoslanayotgani; oraliq talabalar
bo‘yicha juftlashtirilgan bootstrap.

| a | b | AUC(a) − AUC(b) [CI] | DeLong p | p (Holm) | Qaror |
|---|---|---|---|---|---|
| BKT+IRT (λ=0) | BKT | — | — | — | D53 |
| BKT+IRT (λ=0) | DKT | 0.016 [0.01; 0.022] | 0 | 0 | D56 |
| BKT+IRT (λ=0) | AKT-R | 0.035 [0.029; 0.041] | 0 | 0 | D59 |

## 4. Har fold uchun tanlangan kombinatsiya

Tanlov faqat validatsiya AUC bo‘yicha; sinov qismi tanlash paytida ochilmagan.

| Fold | Model | Tanlangan | Validatsiya AUC | Epochlar | Nomzodlar |
|---|---|---|---|---|---|
| 0 | DKT | emb=200, dropout=0.1, lr=0.001 | 0.688 | 4 | 12 |
| 0 | AKT | lr=0.001 | 0.664 | 4 | 2 |
| 0 | AKT-R | lr=0.001 | 0.661 | 4 | 2 |
| 1 | DKT | emb=200, dropout=0.1, lr=0.001 | 0.7 | 4 | 12 |
| 1 | AKT | lr=0.001 | 0.694 | 4 | 2 |
| 1 | AKT-R | lr=0.001 | 0.698 | 4 | 2 |
| 2 | DKT | emb=200, dropout=0.1, lr=0.001 | 0.694 | 4 | 12 |
| 2 | AKT | lr=0.001 | 0.662 | 4 | 2 |
| 2 | AKT-R | lr=0.001 | 0.672 | 4 | 2 |
| 3 | DKT | emb=200, dropout=0.1, lr=0.001 | 0.705 | 4 | 12 |
| 3 | AKT | lr=0.001 | 0.695 | 4 | 2 |
| 3 | AKT-R | lr=0.001 | 0.685 | 4 | 2 |
| 4 | DKT | emb=200, dropout=0.1, lr=0.001 | 0.672 | 4 | 12 |
| 4 | AKT | lr=0.001 | 0.661 | 4 | 2 |
| 4 | AKT-R | lr=0.001 | 0.664 | 4 | 2 |

## 5. Nazorat va vaqt

- nazorat modeli: `BKT+IRT (λ=0)`, pooled AUC 0.71 (asosiy natijada 0.724, farq —, chegara 0)
- nazorat mos keldimi: —
- birinchi fold (soniya): 217.7, bashorat (soat): 0.3, byudjet (soat): 24

## 6. O‘qish qoidasi (D73, natijadan oldin belgilangan)

> D73: BKT+IRT − DKT farqining 95 % CI pastki chegarasi SECOND_CONDITION_FLOOR dan kichik bo‘lmasa — ikkinchi shart to‘liq o‘qitilgan DKT ga nisbatan ham bajariladi

- chegara: -0.01
- BKT+IRT − DKT farqining CI pastki chegarasi: 0.01

**Natija: ikkinchi shart to‘liq o‘qitilgan DKT ga nisbatan ham bajariladi**

H2 ning asosiy hukmi o‘zgarmaydi: u natijadan oldin belgilangan qoida bo‘yicha chiqarilgan (D56, D59). Bu — post-hoc sezgirlik.

## 7. Ma’lumot

- to‘plam: ASSISTments 2009–2010 skill builder
- talabalar: 500, javoblar: 53652

## 8. Manba va ishga tushirish (D48)

- kod commit'i: `e801e4f`
- buyruq: `python -m experiments.h2_tuned --quick`
- vaqt: 2026-11-18T07:29:42.417408+00:00
- python: 3.12.3, Linux-7.0.0-43-generic-x86_64-with-glibc2.43
- git holati boshida: `e801e4f`, toza (2026-11-18T06:56:10.437211+00:00)
- git holati oxirida: `e801e4f`, toza (2026-11-18T07:29:42.417380+00:00)
- seed: bootstrap = 20261006, models = 20261006, split = 20261006
- paketlar: numpy 1.26.4, pandas 2.3.3, pyBKT 1.4.3, pykt 0.0.38, scipy 1.14.1, sklearn 1.6.1, torch 2.5.1+cpu

| Fayl | sha256 | Bayt |
|---|---|---|
| `assistments2009` | `f22e3fb7872c1784ce93b0f9ebabbe0cbcac4f896fd8b4a11667b9715d77dbdc` | 83201940 |

