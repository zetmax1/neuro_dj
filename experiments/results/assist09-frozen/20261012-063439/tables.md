# H2 — test vaqtida masala qiyinligi muzlatilganda (D60): ASSISTments 2009–2010 skill builder

Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.

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
| BKT | current | 0.707 [0.701, 0.714] | 0.449 | 0.704 | 0.704 | 338001 |
| BKT | frozen | 0.707 [0.701, 0.714] | 0.449 | 0.704 | 0.704 | 338001 |
| BKT+IRT (λ=0) | current | 0.724 [0.718, 0.73] | 0.446 | 0.706 | 0.722 | 338001 |
| BKT+IRT (λ=0) | frozen | 0.724 [0.718, 0.73] | 0.446 | 0.705 | 0.721 | 338001 |
| Elo/Rasch | current | 0.762 [0.757, 0.767] | 0.427 | 0.727 | 0.764 | 338001 |
| Elo/Rasch | frozen | 0.761 [0.755, 0.766] | 0.428 | 0.726 | 0.762 | 338001 |
| DKT | current | 0.727 [0.721, 0.733] | 0.441 | 0.71 | 0.737 | 338001 |
| DKT | frozen | 0.727 [0.721, 0.733] | 0.441 | 0.71 | 0.737 | 338001 |

## 2. Kontrastlar

Farq — ikki modelning AUC'lari ayirmasi; ishonch oralig‘i — talabalar bo‘yicha
juftlik bootstrap (har replikatda ikkala model uchun bir xil talabalar).
DeLong javoblarni mustaqil deb hisoblaydi, shuning uchun uning p qiymati
haqiqiydan kichik bo‘lishi mumkin; Holm — shu variantdagi juftliklar oilasi uchun.

| Kontrast | Qaror | Variant | Farq [95% CI] | p (DeLong) | p (Holm) |
|---|---|---|---|---|---|
| BKT+IRT (λ=0) − BKT | D53 | current | 0.016 [0.016, 0.017] | 0 | 0 |
| BKT+IRT (λ=0) − BKT | D53 | frozen | 0.016 [0.015, 0.017] | 0 | 0 |
| BKT+IRT (λ=0) − DKT | D56 | current | -0.003 [-0.005, -0.001] | 0 | 0 |
| BKT+IRT (λ=0) − DKT | D56 | frozen | -0.004 [-0.006, -0.002] | 0 | 0 |
| Elo/Rasch − DKT | D60 | current | 0.035 [0.031, 0.039] | 0 | 0 |
| Elo/Rasch − DKT | D60 | frozen | 0.033 [0.029, 0.038] | 0 | 0 |

## 3. D53 va D56 ikkala variantda

D60 ning o‘qish qoidasi (natijadan oldin yozilgan): da’vo ikkala variantda ham
bajarilsa “mustahkam” deb yoziladi. D53 — farq nolidan yuqori; D56 — farqning
ishonch oralig‘ining pastki chegarasi -0.01 dan past emas.

| Da'vo | Variant | Farq [95% CI] | Bajarildi | Mustahkam |
|---|---|---|---|---|
| D53 | current | 0.016 [0.016, 0.017] | o‘tdi | o‘tdi |
| D53 | frozen | 0.016 [0.015, 0.017] | o‘tdi | o‘tdi |
| D56 | current | -0.003 [-0.005, -0.001] | o‘tdi | o‘tdi |
| D56 | frozen | -0.004 [-0.006, -0.002] | o‘tdi | o‘tdi |

## 4. Darvozalar

Takrorlanish darvozasi: “hozirgi” ustun H2 natijasini (`experiments/results/assist09/20261010-060005`) 6 xonaga qadar takrorlashi shart, aks holda hech narsa yozilmaydi. DKT — D58
chegarasi (0.001).
Nazorat: BKT ning ikki ustundagi bashoratlari orasidagi eng katta farq.

| Darvoza | Model | Bu run | H2 / kutilgan | Natija |
|---|---|---|---|---|
| takrorlanish | BKT | 0.707 | 0.707 | o‘tdi |
| takrorlanish | BKT+IRT (λ=0) | 0.724 | 0.724 | o‘tdi |
| DKT (D58) | DKT | 0.727 | 0.727 | o‘tdi |
| nazorat | BKT | 0 | 0 | o‘tdi |

## 5. Fold'lar bo‘yicha AUC

| Model | Variant | 1-qism | 2-qism | 3-qism | 4-qism | 5-qism |
|---|---|---|---|---|---|---|
| BKT | current | 0.712 | 0.717 | 0.697 | 0.712 | 0.698 |
| BKT | frozen | 0.712 | 0.717 | 0.697 | 0.712 | 0.698 |
| BKT+IRT (λ=0) | current | 0.728 | 0.733 | 0.714 | 0.728 | 0.716 |
| BKT+IRT (λ=0) | frozen | 0.728 | 0.732 | 0.714 | 0.728 | 0.716 |
| Elo/Rasch | current | 0.764 | 0.767 | 0.756 | 0.763 | 0.758 |
| Elo/Rasch | frozen | 0.761 | 0.765 | 0.756 | 0.763 | 0.758 |
| DKT | current | 0.732 | 0.735 | 0.718 | 0.732 | 0.719 |
| DKT | frozen | 0.732 | 0.735 | 0.718 | 0.732 | 0.719 |

## 6. Ma'lumot, parametrlar va ishga tushirish

- ishlatilgan: 338001 javob, 4163 talaba
- bo‘linish: 5 qism, seed 20261006, validatsiya ulushi 0.2
- BKT parametrlari: checkpoint (`h2-bounds-99bb9f9117e5e296`)
- DKT: checkpoint, 10 epoch
- reference: `experiments/results/assist09/20261010-060005` (`66ff452`)

## 7. Manba va ishga tushirish (D48)

- kod commit'i: `244f046`
- buyruq: `python -m experiments.h2_frozen --reference experiments/results/assist09/20261010-060005 --workers 4`
- vaqt: 2026-10-12T06:34:39.283944+00:00
- python: 3.12.3, Linux-7.0.0-38-generic-x86_64-with-glibc2.43
- git holati boshida: `244f046`, toza (2026-10-12T05:30:39.272655+00:00)
- git holati oxirida: `244f046`, toza (2026-10-12T06:34:39.283918+00:00)
- seed: bootstrap = 20261006, models = 20261006, split = 20261006
- paketlar: numpy 1.26.4, pandas 2.3.3, pyBKT 1.4.3, pykt 0.0.38, scipy 1.14.1, sklearn 1.6.1, torch 2.5.1+cpu

| Fayl | sha256 | Bayt |
|---|---|---|
| `assistments2009` | `f22e3fb7872c1784ce93b0f9ebabbe0cbcac4f896fd8b4a11667b9715d77dbdc` | 83201940 |

