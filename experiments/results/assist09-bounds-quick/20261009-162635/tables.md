# H2 — chegaralar sezgirligi (D55): ASSISTments 2009–2010 skill builder

Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.

> **`--quick` ishga tushirish — dissertatsiya natijasi emas.** Bu quvurni
> sinash uchun: talabalarning bir qismi. To‘liq natija uchun
> `python -m experiments.h2_bounds` bayroqsiz ishga tushiriladi.

**II bob qarori o‘zgarmaydi.** Asosiy natija — G_MAX = 0.3, S_MAX = 0.1 bilan olingani (“asosiy” sozlamasi).
Qolgan sozlamalar faqat eksperiment parametri: ular H2 xulosasi chegaralarga
qanchalik bog‘liqligini ko‘rsatadi. Platformaning konstantalari o‘zgarmagan.

## 1. Sozlamalar va grid

P(G) va P(S) grid'i har sozlamada chegaraga nisbatan quriladi: II bob
grid'ining qiymatlari chegaraga nisbatan ulush sifatida olinadi, shuning uchun
eng yuqori qiymat har sozlamada chegaraning bir xil ulushida turadi. Fold'lar
moslanishidan oldin grid'ning eng yaxshi qiymati eng ko‘p javobli
5 mavzuda chegaralangan L-BFGS-B optimumidan
nisbatan 0.01 dan ko‘p farq qilmasligi tekshiriladi;
aks holda ishga tushirish to‘xtaydi va hech narsa yozilmaydi.

| Sozlama | G_MAX | S_MAX | P(G) qiymatlari | P(S) qiymatlari | Eng yuqori / chegara (G, S) | L-BFGS-B: eng katta nisbiy farq | Tekshiruv |
|---|---|---|---|---|---|---|---|
| asosiy | 0.3 | 0.1 | 0.05, 0.1, 0.15, 0.2, 0.25, 0.29 | 0.01, 0.03, 0.05, 0.07, 0.09, 0.097 | 0.967, 0.97 | 0.006 | o‘tdi |
| kengroq | 0.4 | 0.2 | 0.067, 0.133, 0.2, 0.267, 0.333, 0.387 | 0.02, 0.06, 0.1, 0.14, 0.18, 0.194 | 0.967, 0.97 | 0.004 | o‘tdi |
| eng keng | 0.49 | 0.3 | 0.082, 0.163, 0.245, 0.327, 0.408, 0.474 | 0.03, 0.09, 0.15, 0.21, 0.27, 0.291 | 0.967, 0.97 | 0.004 | o‘tdi |

## 2. Natija (barcha fold'lar birga)

AUC uchun 95% ishonch oralig‘i — talabalar bo‘yicha bootstrap,
200 replikat. Log-likelihood — test javoblarida: to‘g‘ri
javobda log p̂, xatoda — xato ehtimolining logarifmi, hammasi qo‘shilgan;
nolga yaqinrog‘i yaxshiroq.

| Sozlama | Model | AUC [95% CI] | RMSE | Aniqlik | Log-likelihood (test) | Javob |
|---|---|---|---|---|---|---|
| asosiy | BKT | 0.697 [0.684, 0.711] | 0.432 | 0.735 | -30202.714 | 53652 |
| asosiy | BKT+IRT (λ=0) | 0.71 [0.698, 0.724] | 0.431 | 0.735 | -30144.91 | 53652 |
| kengroq | BKT | 0.706 [0.693, 0.72] | 0.426 | 0.74 | -29265.75 | 53652 |
| kengroq | BKT+IRT (λ=0) | 0.72 [0.707, 0.733] | 0.424 | 0.741 | -29173.196 | 53652 |
| eng keng | BKT | 0.704 [0.692, 0.717] | 0.426 | 0.74 | -29275.66 | 53652 |
| eng keng | BKT+IRT (λ=0) | 0.721 [0.71, 0.735] | 0.424 | 0.743 | -29370.805 | 53652 |

## 3. BKT+IRT (λ=0) − BKT

Farq — ikki modelning AUC'lari ayirmasi. Ishonch oralig‘i — talabalar bo‘yicha
juftlik bootstrap: har replikatda ikkala model uchun bir xil talabalar olinadi.
DeLong javoblarni mustaqil deb hisoblaydi, shuning uchun uning p qiymati
haqiqiydan kichik bo‘lishi mumkin (H2 jadvalidagi kabi); Holm — sozlamalar
oilasi uchun.

| Sozlama | AUC farqi | 95% CI (bootstrap) | z (DeLong) | p | p (Holm) | Muhim |
|---|---|---|---|---|---|---|
| asosiy | 0.013 | [0.011, 0.015] | 22.406 | 0 | 0 | ha |
| kengroq | 0.014 | [0.012, 0.015] | 19.791 | 0 | 0 | ha |
| eng keng | 0.018 | [0.016, 0.021] | 18.566 | 0 | 0 | ha |

## 4. BKT+IRT (λ=0) − DKT (D56) va BKT+IRT (λ=0) − Elo/Rasch (H2)

DKT bu yerda H2 dagi sozlama, seed va protokol bilan qayta o‘qitiladi; farqning
ishonch oralig‘i — talabalar bo‘yicha juftlik bootstrap. Qayta o‘qitilgan DKT
H2 dagi qiymatdan D58 chegarasidan ko‘p farq qilsa, farq hisoblanmaydi.
Elo/Rasch qayta ishga tushirilmaydi: uning AUC'i H2 natijasidan olinadi va
farq faqat nuqtaviy.

| Sozlama | − DKT [95% CI] | D56 chegarasi | − Elo/Rasch (nuqtaviy) | Elo/Rasch AUC (H2) |
|---|---|---|---|---|
| asosiy | 0.064 [0.057, 0.073] | -0.01 | 0.014 | 0.696 |
| kengroq | 0.074 [0.066, 0.084] | -0.01 | 0.023 | 0.696 |
| eng keng | 0.076 [0.067, 0.086] | -0.01 | 0.025 | 0.696 |

## 5. Takrorlanish darvozalari (D58)

Asosiy sozlama H2 natijasini (`experiments/results/assist09-quick/20261009-124538`) takrorlashi shart:
BKT va BKT+IRT AUC'i olti xonagacha teng bo‘lmasa, ishga tushirish to‘xtaydi
va hech narsa yozilmaydi. DKT — D58 chegarasi ichida.

| Darvoza | Model | Bu ishga tushirish | H2 | Natija |
|---|---|---|---|---|
| 1-fold | BKT | 0.727 | 0.727 | o‘tdi |
| 1-fold | BKT+IRT (λ=0) | 0.738 | 0.738 | o‘tdi |
| pooled | BKT | 0.697 | 0.697 | o‘tdi |
| pooled | BKT+IRT (λ=0) | 0.71 | 0.71 | o‘tdi |
| pooled | DKT | 0.646 | 0.646 | o‘tdi |

## 6. Chegaraga tiralgan moslashlar

Har bir fold o‘z parametrlarini moslaydi; sonlar barcha fold'lar bo‘yicha
jamlangan. “Eng yuqorida” — grid'ning shu sozlamadagi eng yuqori ruxsat
etilgan qiymati. O‘qitish log-likelihood'i — moslangan mavzular bo‘yicha jami,
barcha fold'larda; sozlamalar bir xil ma’lumotda moslangani uchun solishtiriladi.

| Sozlama | Moslashlar | P(G) eng yuqorida | Ulushi | P(S) eng yuqorida | Ulushi | O‘qitish log-likelihood |
|---|---|---|---|---|---|---|
| asosiy | 420 | 332 | 0.79 | 360 | 0.857 | -117102.556 |
| kengroq | 420 | 200 | 0.476 | 204 | 0.486 | -112766.918 |
| eng keng | 420 | 142 | 0.338 | 85 | 0.202 | -112230.601 |

## 7. Fold'lar bo‘yicha AUC

| Sozlama | Model | 1-qism | 2-qism | 3-qism | 4-qism | 5-qism |
|---|---|---|---|---|---|---|
| asosiy | BKT | 0.727 | 0.718 | 0.668 | 0.683 | 0.688 |
| asosiy | BKT+IRT (λ=0) | 0.738 | 0.729 | 0.684 | 0.698 | 0.7 |
| kengroq | BKT | 0.732 | 0.727 | 0.681 | 0.694 | 0.697 |
| kengroq | BKT+IRT (λ=0) | 0.746 | 0.738 | 0.694 | 0.709 | 0.709 |
| eng keng | BKT | 0.73 | 0.724 | 0.677 | 0.692 | 0.696 |
| eng keng | BKT+IRT (λ=0) | 0.75 | 0.737 | 0.696 | 0.712 | 0.711 |

## 8. Ma’lumot va bo‘lish

- ishlatilgan: 53652 javob, 500 talaba
- `--original-only`: yo‘q
- bo‘lish: 5 qism, talabalar bo‘yicha, validatsiya ulushi 0.2, seed 20261006 — H2 bilan bir xil
- grid search: 7 jarayonda parallel; natija bunga bog‘liq emas

## 9. Manba va ishga tushirish (D48)

- kod commit'i: `8f35bbe`
- buyruq: `python -m experiments.h2_bounds --quick --reference experiments/results/assist09-quick/20261009-124538`
- vaqt: 2026-10-09T16:26:35.377165+00:00
- python: 3.12.3, Linux-7.0.0-38-generic-x86_64-with-glibc2.43
- git holati boshida: `8f35bbe`, toza (2026-10-09T16:02:55.912483+00:00)
- git holati oxirida: `8f35bbe`, toza (2026-10-09T16:26:35.377129+00:00)
- seed: bootstrap = 20261006, models = 20261006, split = 20261006
- paketlar: numpy 1.26.4, pandas 2.3.3, pyBKT 1.4.3, pykt 0.0.38, scipy 1.14.1, sklearn 1.6.1, torch 2.5.1+cpu

| Fayl | sha256 | Bayt |
|---|---|---|
| `assistments2009` | `f22e3fb7872c1784ce93b0f9ebabbe0cbcac4f896fd8b4a11667b9715d77dbdc` | 83201940 |

