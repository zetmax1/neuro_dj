# H2 — chegaralar sezgirligi (D55): ASSISTments 2009–2010 skill builder

Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.

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
| asosiy | 0.3 | 0.1 | 0.05, 0.1, 0.15, 0.2, 0.25, 0.29 | 0.01, 0.03, 0.05, 0.07, 0.09, 0.097 | 0.967, 0.97 | 0.007 | o‘tdi |
| kengroq | 0.4 | 0.2 | 0.067, 0.133, 0.2, 0.267, 0.333, 0.387 | 0.02, 0.06, 0.1, 0.14, 0.18, 0.194 | 0.967, 0.97 | 0.002 | o‘tdi |
| eng keng | 0.49 | 0.3 | 0.082, 0.163, 0.245, 0.327, 0.408, 0.474 | 0.03, 0.09, 0.15, 0.21, 0.27, 0.291 | 0.967, 0.97 | 0.002 | o‘tdi |

## 2. Natija (barcha fold'lar birga)

AUC uchun 95% ishonch oralig‘i — talabalar bo‘yicha bootstrap,
200 replikat. Log-likelihood — test javoblarida: to‘g‘ri
javobda log p̂, xatoda — xato ehtimolining logarifmi, hammasi qo‘shilgan;
nolga yaqinrog‘i yaxshiroq.

| Sozlama | Model | AUC [95% CI] | RMSE | Aniqlik | Log-likelihood (test) | Javob |
|---|---|---|---|---|---|---|
| asosiy | BKT | 0.707 [0.702, 0.714] | 0.449 | 0.704 | -201910.964 | 338001 |
| asosiy | BKT+IRT (λ=0) | 0.724 [0.718, 0.73] | 0.446 | 0.706 | -199849.37 | 338001 |
| kengroq | BKT | 0.716 [0.71, 0.722] | 0.442 | 0.71 | -194522.795 | 338001 |
| kengroq | BKT+IRT (λ=0) | 0.736 [0.73, 0.742] | 0.436 | 0.715 | -190710.638 | 338001 |
| eng keng | BKT | 0.716 [0.71, 0.722] | 0.441 | 0.711 | -193757.599 | 338001 |
| eng keng | BKT+IRT (λ=0) | 0.747 [0.742, 0.752] | 0.432 | 0.722 | -188005.889 | 338001 |

## 3. BKT+IRT (λ=0) − BKT

Farq — ikki modelning AUC'lari ayirmasi. Ishonch oralig‘i — talabalar bo‘yicha
juftlik bootstrap: har replikatda ikkala model uchun bir xil talabalar olinadi.
DeLong javoblarni mustaqil deb hisoblaydi, shuning uchun uning p qiymati
haqiqiydan kichik bo‘lishi mumkin (H2 jadvalidagi kabi); Holm — sozlamalar
oilasi uchun.

| Sozlama | AUC farqi | 95% CI (bootstrap) | z (DeLong) | p | p (Holm) | Muhim |
|---|---|---|---|---|---|---|
| asosiy | 0.016 | [0.016, 0.017] | 92.003 | 0 | 0 | ha |
| kengroq | 0.02 | [0.019, 0.022] | 79.367 | 0 | 0 | ha |
| eng keng | 0.031 | [0.029, 0.033] | 83.683 | 0 | 0 | ha |

## 4. BKT+IRT (λ=0) − DKT (D56) va BKT+IRT (λ=0) − Elo/Rasch (H2)

DKT bu yerda H2 dagi sozlama, seed va protokol bilan qayta o‘qitiladi; farqning
ishonch oralig‘i — talabalar bo‘yicha juftlik bootstrap. Qayta o‘qitilgan DKT
H2 dagi qiymatdan D58 chegarasidan ko‘p farq qilsa, farq hisoblanmaydi.
Elo/Rasch qayta ishga tushirilmaydi: uning AUC'i H2 natijasidan olinadi va
farq faqat nuqtaviy.

| Sozlama | − DKT [95% CI] | D56 chegarasi | − Elo/Rasch (nuqtaviy) | Elo/Rasch AUC (H2) |
|---|---|---|---|---|
| asosiy | -0.003 [-0.005, -0.001] | -0.01 | -0.038 | 0.762 |
| kengroq | 0.009 [0.007, 0.011] | -0.01 | -0.026 | 0.762 |
| eng keng | 0.02 [0.018, 0.022] | -0.01 | -0.015 | 0.762 |

## 5. Takrorlanish darvozalari (D58)

Asosiy sozlama H2 natijasini (`experiments/results/assist09/20261010-060005`) takrorlashi shart:
BKT va BKT+IRT AUC'i olti xonagacha teng bo‘lmasa, ishga tushirish to‘xtaydi
va hech narsa yozilmaydi. DKT — D58 chegarasi ichida.

| Darvoza | Model | Bu ishga tushirish | H2 | Natija |
|---|---|---|---|---|
| 1-fold | BKT | 0.712 | 0.712 | o‘tdi |
| 1-fold | BKT+IRT (λ=0) | 0.728 | 0.728 | o‘tdi |
| pooled | BKT | 0.707 | 0.707 | o‘tdi |
| pooled | BKT+IRT (λ=0) | 0.724 | 0.724 | o‘tdi |
| pooled | DKT | 0.727 | 0.727 | o‘tdi |

## 6. Chegaraga tiralgan moslashlar

Har bir fold o‘z parametrlarini moslaydi; sonlar barcha fold'lar bo‘yicha
jamlangan. “Eng yuqorida” — grid'ning shu sozlamadagi eng yuqori ruxsat
etilgan qiymati. O‘qitish log-likelihood'i — moslangan mavzular bo‘yicha jami,
barcha fold'larda; sozlamalar bir xil ma’lumotda moslangani uchun solishtiriladi.

| Sozlama | Moslashlar | P(G) eng yuqorida | Ulushi | P(S) eng yuqorida | Ulushi | O‘qitish log-likelihood |
|---|---|---|---|---|---|---|
| asosiy | 555 | 425 | 0.766 | 485 | 0.874 | -804830.354 |
| kengroq | 555 | 218 | 0.393 | 335 | 0.604 | -774410.201 |
| eng keng | 555 | 83 | 0.149 | 153 | 0.276 | -771203.079 |

## 7. Fold'lar bo‘yicha AUC

| Sozlama | Model | 1-qism | 2-qism | 3-qism | 4-qism | 5-qism |
|---|---|---|---|---|---|---|
| asosiy | BKT | 0.712 | 0.717 | 0.697 | 0.712 | 0.698 |
| asosiy | BKT+IRT (λ=0) | 0.728 | 0.733 | 0.714 | 0.728 | 0.716 |
| kengroq | BKT | 0.722 | 0.724 | 0.707 | 0.718 | 0.706 |
| kengroq | BKT+IRT (λ=0) | 0.741 | 0.744 | 0.728 | 0.738 | 0.727 |
| eng keng | BKT | 0.722 | 0.724 | 0.707 | 0.719 | 0.706 |
| eng keng | BKT+IRT (λ=0) | 0.752 | 0.754 | 0.739 | 0.749 | 0.739 |

## 8. Ma’lumot va bo‘lish

- ishlatilgan: 338001 javob, 4163 talaba
- `--original-only`: yo‘q
- bo‘lish: 5 qism, talabalar bo‘yicha, validatsiya ulushi 0.2, seed 20261006 — H2 bilan bir xil
- grid search: 4 jarayonda parallel; natija bunga bog‘liq emas

## 9. Manba va ishga tushirish (D48)

- kod commit'i: `30ad4e4`
- buyruq: `python -m experiments.h2_bounds --reference experiments/results/assist09/20261010-060005 --workers 4`
- vaqt: 2026-10-11T18:37:56.770625+00:00
- python: 3.12.3, Linux-7.0.0-38-generic-x86_64-with-glibc2.43
- git holati boshida: `30ad4e4`, toza (2026-10-11T15:35:42.332791+00:00)
- git holati oxirida: `30ad4e4`, toza (2026-10-11T18:37:56.770604+00:00)
- seed: bootstrap = 20261006, models = 20261006, split = 20261006
- paketlar: numpy 1.26.4, pandas 2.3.3, pyBKT 1.4.3, pykt 0.0.38, scipy 1.14.1, sklearn 1.6.1, torch 2.5.1+cpu

| Fayl | sha256 | Bayt |
|---|---|---|
| `assistments2009` | `f22e3fb7872c1784ce93b0f9ebabbe0cbcac4f896fd8b4a11667b9715d77dbdc` | 83201940 |

