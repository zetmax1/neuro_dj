# H2 (D73) — neyron modellar to‘liq o‘qitilganda: post-hoc sezgirlik

Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.

> **Bu H2 ning hukmi emas.** H2 ning hukmi asosiy natijada, natijadan
> oldin belgilangan qoida bo‘yicha chiqarilgan (D56, D59) va bu yerda
> qayta ko‘rilmaydi. Bu jadval bitta savolga javob beradi: neyron
> modellarga to‘liq o‘qitish imkoni berilganda taqqoslash qanday ko‘rinadi.

Ma’lumot, tozalash, foldlar, seed va D57 baholash tartibi asosiy
natijadagi kodning o‘zi (`h2.prepare`, `h2.fold_sets`, `h2.fit_predict`,
`h2.analyse_pooled`). Faqat giperparametrlar va to‘xtash shartlari boshqa.

## 1. O‘qitish sozlamalari

- ko‘pi bilan epoch: 200
- sabr (patience): 10 (pyKT ning `train_model` kodida: 10)
- yaxshilanish chegarasi: 0 (pyKT da 0.001 — kichikroq chegara kechroq to‘xtatadi, ya’ni DKT foydasiga)
- nomzod tanlanadigan metrika: `validation_auc`
- DKT to‘ri: 12 nomzod; AKT/AKT-R: 2 nomzod

## 2. Pooled natija

| Model | AUC [CI] | RMSE | Aniqlik | Sovuq qatorlar |
|---|---|---|---|---|
| BKT+IRT (λ=0) | 0.724 [0.718; 0.73] | 0.446 | 0.706 | 0 |
| DKT | 0.734 [0.728; 0.74] | 0.437 | 0.718 | 6010 |
| AKT | 0.734 [0.728; 0.74] | 0.436 | 0.722 | 6010 |
| AKT-R | 0.752 [0.746; 0.758] | 0.434 | 0.729 | 6010 |

## 3. H2 ning farqlari

Farq — platformaning modeli minus taqqoslanayotgani; oraliq talabalar
bo‘yicha juftlashtirilgan bootstrap.

| a | b | AUC(a) − AUC(b) [CI] | DeLong p | p (Holm) | Qaror |
|---|---|---|---|---|---|
| BKT+IRT (λ=0) | BKT | — | — | — | D53 |
| BKT+IRT (λ=0) | DKT | -0.01 [-0.012; -0.008] | 0 | 0 | D56 |
| BKT+IRT (λ=0) | AKT-R | -0.028 [-0.031; -0.025] | 0 | 0 | D59 |

## 4. Har fold uchun tanlangan kombinatsiya

Tanlov faqat validatsiya AUC bo‘yicha; sinov qismi tanlash paytida ochilmagan.

| Fold | Model | Tanlangan | Validatsiya AUC | Epochlar | Nomzodlar |
|---|---|---|---|---|---|
| 0 | DKT | emb=100, dropout=0.3, lr=0.0001 | 0.733 | 126 | 12 |
| 0 | AKT | lr=0.001 | 0.732 | 48 | 2 |
| 0 | AKT-R | lr=0.001 | 0.752 | 32 | 2 |
| 1 | DKT | emb=200, dropout=0.3, lr=0.0001 | 0.743 | 60 | 12 |
| 1 | AKT | lr=0.0001 | 0.743 | 123 | 2 |
| 1 | AKT-R | lr=0.0001 | 0.76 | 82 | 2 |
| 2 | DKT | emb=100, dropout=0.3, lr=0.0001 | 0.733 | 116 | 12 |
| 2 | AKT | lr=0.0001 | 0.736 | 187 | 2 |
| 2 | AKT-R | lr=0.0001 | 0.757 | 131 | 2 |
| 3 | DKT | emb=200, dropout=0.3, lr=0.0001 | 0.746 | 63 | 12 |
| 3 | AKT | lr=0.0001 | 0.748 | 131 | 2 |
| 3 | AKT-R | lr=0.0001 | 0.765 | 82 | 2 |
| 4 | DKT | emb=200, dropout=0.3, lr=0.0001 | 0.736 | 50 | 12 |
| 4 | AKT | lr=0.001 | 0.741 | 48 | 2 |
| 4 | AKT-R | lr=0.001 | 0.748 | 27 | 2 |

## 5. Nazorat va vaqt

- nazorat modeli: `BKT+IRT (λ=0)`, pooled AUC 0.724 (asosiy natijada 0.724, farq 0, chegara 0)
- nazorat mos keldimi: ha
- birinchi fold (soniya): 14435.5, bashorat (soat): 20.05, byudjet (soat): 24

## 6. O‘qish qoidasi (D73, natijadan oldin belgilangan)

> D73: BKT+IRT − DKT farqining 95 % CI pastki chegarasi SECOND_CONDITION_FLOOR dan kichik bo‘lmasa — ikkinchi shart to‘liq o‘qitilgan DKT ga nisbatan ham bajariladi

- chegara: -0.01
- BKT+IRT − DKT farqining CI pastki chegarasi: -0.012

**Natija: ikkinchi shart faqat 10 epoch bilan cheklangan DKT ga nisbatan bajarilgan**

H2 ning asosiy hukmi o‘zgarmaydi: u natijadan oldin belgilangan qoida bo‘yicha chiqarilgan (D56, D59). Bu — post-hoc sezgirlik.

## 7. Ma’lumot

- to‘plam: ASSISTments 2009–2010 skill builder
- talabalar: 4163, javoblar: 338001

## 8. Manba va ishga tushirish (D48)

- kod commit'i: `4e8403c`
- buyruq: `python -m experiments.h2_tuned`
- vaqt: 2026-11-23T08:55:02.368840+00:00
- python: 3.12.3, Linux-7.0.0-44-generic-x86_64-with-glibc2.43
- git holati boshida: `4e8403c`, toza (2026-11-23T03:48:08.707522+00:00)
- git holati oxirida: `4e8403c`, toza (2026-11-23T08:55:02.368815+00:00)
- seed: bootstrap = 20261006, models = 20261006, split = 20261006
- paketlar: numpy 1.26.4, pandas 2.3.3, pyBKT 1.4.3, pykt 0.0.38, scipy 1.14.1, sklearn 1.6.1, torch 2.5.1+cpu

| Fayl | sha256 | Bayt |
|---|---|---|
| `assistments2009` | `f22e3fb7872c1784ce93b0f9ebabbe0cbcac4f896fd8b4a11667b9715d77dbdc` | 83201940 |

