# H2 — test vaqtida masala qiyinligi muzlatilganda (D60): ASSISTments 2009–2010 skill builder

Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.

> **`--quick` ishga tushirish — dissertatsiya natijasi emas.** Bu quvurni
> sinash uchun: talabalarning bir qismi.

**Asosiy H2 jadvali almashtirilmaydi.** Bu — sezgirlik tahlili (D60): II bob
modelida masala qiyinligi `b_q` online yangilanadi, shuning uchun “hozirgi”
ustun asosiy natija bo‘lib qoladi. Chegaralar: G_MAX = 0.3, S_MAX = 0.1.

Ikki variant bir xil moslangan modellardan olinadi: har model bir marta
moslanadi va ikki marta so‘roqlanadi.

- **hozirgi** — H2 ning o‘zi: `b_q` va `n_q` test oqimida yangilanib boradi;
- **frozen** — `b_q` va `n_q` o‘qitish to‘plamida isitilgan qiymatda qoladi;
  θ talabaning o‘z javoblari bilan yangilanishda davom etadi.

BKT nazorat sifatida turadi: u `b_q` ni o‘qimaydi, shuning uchun ikki ustunda
aynan bir xil chiqishi shart. DKT o‘qitishdan keyin qotiriladi, shuning uchun
uning ikki ustundagi sonlari bir xil; u D56 uchun kerak.

## 1. Natija (barcha fold'lar birga)

AUC uchun 95% ishonch oralig‘i — talabalar bo‘yicha bootstrap,
1000 replikat. Oxirgi ustundan bitta oldingisi — masalaning birinchi
qatorlari bo‘yicha AUC (D57 sezgirligi).

| Model | Variant | AUC [95% CI] | RMSE | Aniqlik | Birinchi qatorlar AUC | Javob |
|---|---|---|---|---|---|---|
| BKT | current | 0.697 [0.684, 0.71] | 0.432 | 0.735 | 0.694 | 53652 |
| BKT | frozen | 0.697 [0.684, 0.71] | 0.432 | 0.735 | 0.694 | 53652 |
| BKT+IRT (λ=0) | current | 0.71 [0.697, 0.723] | 0.431 | 0.735 | 0.708 | 53652 |
| BKT+IRT (λ=0) | frozen | 0.71 [0.697, 0.723] | 0.431 | 0.735 | 0.707 | 53652 |
| Elo/Rasch | current | 0.696 [0.682, 0.711] | 0.431 | 0.729 | 0.697 | 53652 |
| Elo/Rasch | frozen | 0.694 [0.68, 0.709] | 0.432 | 0.727 | 0.694 | 53652 |
| DKT | current | 0.646 [0.634, 0.658] | 0.454 | 0.711 | 0.645 | 53652 |
| DKT | frozen | 0.646 [0.634, 0.658] | 0.454 | 0.711 | 0.645 | 53652 |

## 2. Kontrastlar

Farq — ikki modelning AUC'lari ayirmasi; ishonch oralig‘i — talabalar bo‘yicha
juftlik bootstrap (har replikatda ikkala model uchun bir xil talabalar).
DeLong javoblarni mustaqil deb hisoblaydi, shuning uchun uning p qiymati
haqiqiydan kichik bo‘lishi mumkin; Holm — shu variantdagi juftliklar oilasi uchun.

| Kontrast | Qaror | Variant | Farq [95% CI] | p (DeLong) | p (Holm) |
|---|---|---|---|---|---|
| BKT+IRT (λ=0) − BKT | D53 | current | 0.013 [0.011, 0.015] | 0 | 0 |
| BKT+IRT (λ=0) − BKT | D53 | frozen | 0.013 [0.011, 0.015] | 0 | 0 |
| BKT+IRT (λ=0) − DKT | D56 | current | 0.064 [0.056, 0.072] | 0 | 0 |
| BKT+IRT (λ=0) − DKT | D56 | frozen | 0.064 [0.056, 0.072] | 0 | 0 |
| Elo/Rasch − DKT | D60 | current | 0.05 [0.037, 0.062] | 0 | 0 |
| Elo/Rasch − DKT | D60 | frozen | 0.048 [0.035, 0.06] | 0 | 0 |

## 3. D53 va D56 ikkala variantda

D60 ning o‘qish qoidasi (natijadan oldin yozilgan): da’vo ikkala variantda ham
bajarilsa “mustahkam” deb yoziladi. D53 — farq nolidan yuqori; D56 — farqning
ishonch oralig‘ining pastki chegarasi -0.01 dan past emas.

| Da'vo | Variant | Farq [95% CI] | Bajarildi | Mustahkam |
|---|---|---|---|---|
| D53 | current | 0.013 [0.011, 0.015] | o‘tdi | o‘tdi |
| D53 | frozen | 0.013 [0.011, 0.015] | o‘tdi | o‘tdi |
| D56 | current | 0.064 [0.056, 0.072] | o‘tdi | o‘tdi |
| D56 | frozen | 0.064 [0.056, 0.072] | o‘tdi | o‘tdi |

## 4. Darvozalar

Takrorlanish darvozasi: “hozirgi” ustun H2 natijasini (`experiments/results/assist09-quick/20261009-124538`) 6 xonaga qadar takrorlashi shart, aks holda hech narsa yozilmaydi. DKT — D58
chegarasi (0.001).
Nazorat: BKT ning ikki ustundagi bashoratlari orasidagi eng katta farq.

| Darvoza | Model | Bu run | H2 / kutilgan | Natija |
|---|---|---|---|---|
| takrorlanish | BKT | 0.697 | 0.697 | o‘tdi |
| takrorlanish | BKT+IRT (λ=0) | 0.71 | 0.71 | o‘tdi |
| DKT (D58) | DKT | 0.646 | 0.646 | o‘tdi |
| nazorat | BKT | 0 | 0 | o‘tdi |

## 5. Fold'lar bo‘yicha AUC

| Model | Variant | 1-qism | 2-qism | 3-qism | 4-qism | 5-qism |
|---|---|---|---|---|---|---|
| BKT | current | 0.727 | 0.718 | 0.668 | 0.683 | 0.688 |
| BKT | frozen | 0.727 | 0.718 | 0.668 | 0.683 | 0.688 |
| BKT+IRT (λ=0) | current | 0.738 | 0.729 | 0.684 | 0.698 | 0.7 |
| BKT+IRT (λ=0) | frozen | 0.738 | 0.729 | 0.684 | 0.697 | 0.7 |
| Elo/Rasch | current | 0.716 | 0.71 | 0.675 | 0.691 | 0.682 |
| Elo/Rasch | frozen | 0.714 | 0.707 | 0.677 | 0.687 | 0.68 |
| DKT | current | 0.671 | 0.635 | 0.616 | 0.65 | 0.652 |
| DKT | frozen | 0.671 | 0.635 | 0.616 | 0.65 | 0.652 |

## 6. Ma'lumot, parametrlar va ishga tushirish

- ishlatilgan: 53652 javob, 500 talaba
- bo‘linish: 5 qism, seed 20261006, validatsiya ulushi 0.2
- BKT parametrlari: checkpoint (`h2-bounds-a3694827cc18bd15`)
- DKT: checkpoint, 3 epoch
- reference: `experiments/results/assist09-quick/20261009-124538` (`5294f82`)

## 7. Manba va ishga tushirish (D48)

- kod commit'i: `6e0278c`
- buyruq: `python -m experiments.h2_frozen --quick --reference experiments/results/assist09-quick/20261009-124538`
- vaqt: 2026-10-12T05:28:56.887032+00:00
- python: 3.12.3, Linux-7.0.0-38-generic-x86_64-with-glibc2.43
- git holati boshida: `6e0278c`, toza (2026-10-12T05:18:33.198825+00:00)
- git holati oxirida: `6e0278c`, toza (2026-10-12T05:28:56.887012+00:00)
- seed: bootstrap = 20261006, models = 20261006, split = 20261006
- paketlar: numpy 1.26.4, pandas 2.3.3, pyBKT 1.4.3, pykt 0.0.38, scipy 1.14.1, sklearn 1.6.1, torch 2.5.1+cpu

| Fayl | sha256 | Bayt |
|---|---|---|
| `assistments2009` | `f22e3fb7872c1784ce93b0f9ebabbe0cbcac4f896fd8b4a11667b9715d77dbdc` | 83201940 |

