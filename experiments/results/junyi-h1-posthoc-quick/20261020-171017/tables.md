# H1 — post-hoc, tavsifiy tahlil (D71)

> **post-hoc, tavsifiy — D61/D62 ning o‘qish qoidasi va hukmi o‘zgarmaydi.** (D71)

> **`--quick` ishga tushirish — dissertatsiya natijasi emas.**

## 1. Qism-to‘plam S: barcha prerekvizitlari voqeadan oldin ishlangan voqealar

Voqealar: S = 683 / 918 (ulush 0.744), talabalar 73; r_s(w) = 0 bo‘lgan voqealar (to‘liq to‘plam): 235.

### k = 3

| Qoida | Voqea | Belgilangan | Xato | Qamrov | Xato ulushi |
|---|---|---|---|---|---|
| ehtimoliy (r ≥ τ) | 683 | 664 | 83 | 0.972 | 0.125 |
| II bob R (M, δ bilan) | 683 | 665 | 83 | 0.974 | 0.125 |
| bajarilganlik | 683 | 683 | 94 | 1 | 0.138 |
| o‘tish bali | 683 | 668 | 83 | 0.978 | 0.124 |
| earned_proficiency | 683 | 640 | 76 | 0.937 | 0.119 |

Teng qamrov S da (τ validatsiyaning S qismida). Farq = ehtimoliy − qoida, 95 % CI (talaba bo‘yicha bootstrap, 100 replika).

| Taqqoslash | τ (fold'lar) | Ehtimoliy qamrov | Qoida qamrovi | Ehtimoliy xato ulushi | Qoida xato ulushi | Farq [CI] |
|---|---|---|---|---|---|---|
| o‘tish bali | 0.999, 0, 0.995, 0.99, 0.818 | 0.969 | 0.978 | 0.13 | 0.124 | 0.006 [0.002; 0.013] |
| earned_proficiency | 1, 0.996, 0.999, 0.999, 0.997 | 0.925 | 0.937 | 0.125 | 0.119 | 0.006 [-0.001; 0.016] |
| bajarilganlik | — | — | — | — | — | S da hamma voqeani belgilaydi: taqqoslash “hamma tayyor” bilan bir xil, hisoblanmadi |

S da r_s(w) bo‘yicha AUC: 0.576 [0.53; 0.662] (683 voqea, 94 muvaffaqiyatsiz).

### k = 5

| Qoida | Voqea | Belgilangan | Xato | Qamrov | Xato ulushi |
|---|---|---|---|---|---|
| ehtimoliy (r ≥ τ) | 683 | 664 | 67 | 0.972 | 0.101 |
| II bob R (M, δ bilan) | 683 | 665 | 67 | 0.974 | 0.101 |
| bajarilganlik | 683 | 683 | 78 | 1 | 0.114 |
| o‘tish bali | 683 | 668 | 67 | 0.978 | 0.1 |
| earned_proficiency | 683 | 640 | 61 | 0.937 | 0.095 |

Teng qamrov S da (τ validatsiyaning S qismida). Farq = ehtimoliy − qoida, 95 % CI (talaba bo‘yicha bootstrap, 100 replika).

| Taqqoslash | τ (fold'lar) | Ehtimoliy qamrov | Qoida qamrovi | Ehtimoliy xato ulushi | Qoida xato ulushi | Farq [CI] |
|---|---|---|---|---|---|---|
| o‘tish bali | 0.999, 0, 0.995, 0.99, 0.818 | 0.969 | 0.978 | 0.106 | 0.1 | 0.005 [0.001; 0.012] |
| earned_proficiency | 1, 0.996, 0.999, 0.999, 0.997 | 0.925 | 0.937 | 0.101 | 0.095 | 0.006 [-0.001; 0.016] |
| bajarilganlik | — | — | — | — | — | S da hamma voqeani belgilaydi: taqqoslash “hamma tayyor” bilan bir xil, hisoblanmadi |

S da r_s(w) bo‘yicha AUC: 0.583 [0.54; 0.666] (683 voqea, 78 muvaffaqiyatsiz).

## 2. To‘liq to‘plam: r_s(w) bo‘yicha xato–qamrov egri chizig‘i

Nuqtaviy (CI siz). Qatorlar — τ; oxirgi qatorlar — boshqa qoidalar nuqtalari.

| τ / qoida | Qamrov (k = 3) | Xato ulushi (k = 3) | Qamrov (k = 5) | Xato ulushi (k = 5) |
|---|---|---|---|---|
| 0 | 1 | 0.139 | 1 | 0.117 |
| 0.01 | 0.743 | 0.136 | 0.743 | 0.113 |
| 0.02 | 0.743 | 0.136 | 0.743 | 0.113 |
| 0.05 | 0.743 | 0.136 | 0.743 | 0.113 |
| 0.1 | 0.743 | 0.136 | 0.743 | 0.113 |
| 0.2 | 0.737 | 0.131 | 0.737 | 0.108 |
| 0.3 | 0.735 | 0.13 | 0.735 | 0.107 |
| 0.4 | 0.735 | 0.13 | 0.735 | 0.107 |
| 0.5 | 0.735 | 0.13 | 0.735 | 0.107 |
| 0.6 | 0.733 | 0.128 | 0.733 | 0.104 |
| 0.7 | 0.733 | 0.128 | 0.733 | 0.104 |
| 0.8 | 0.73 | 0.127 | 0.73 | 0.103 |
| 0.9 | 0.725 | 0.126 | 0.725 | 0.102 |
| 0.95 | 0.723 | 0.125 | 0.723 | 0.101 |
| 0.99 | 0.723 | 0.125 | 0.723 | 0.101 |
| bajarilganlik | 0.744 | 0.138 | 0.744 | 0.114 |
| o‘tish bali | 0.972 | 0.128 | 0.972 | 0.105 |
| earned_proficiency | 0.697 | 0.119 | 0.697 | 0.095 |

## Manba va takrorlanish

- buyruq: `python -m experiments.d71 --quick --workers 5`
- commit: `f88ded8`; asl natija: `experiments/results/junyi-h1-quick/20261019-092712`
- checkpoint: `{"enabled": true, "key_digest": "fbbe7bb4a698953b", "resumed_items": 0, "resumed_folds": 0}`

| Darvoza | Bu run | Asl run | Teng |
|---|---|---|---|
| h1 events | 918 | 918 | ha |
| h1 subset (every prerequisite answered) | 683 | 683 | ha |
| h1 rule probabilistic (flagged, failed) | 664, 83 | 664, 83 | ha |
| h1 rule chapter_two (flagged, failed) | 665, 83 | 665, 83 | ha |
| h1 rule completeness (flagged, failed) | 683, 94 | 683, 94 | ha |
| h1 rule pass_mark (flagged, failed) | 892, 114 | 892, 114 | ha |
| h1 rule earned_proficiency (flagged, failed) | 640, 76 | 640, 76 | ha |
| h3 asl at λ=0.25, first 3 AUC | 0.752 | 0.752 | ha |
| h3 asl, first 3 answers | 5563 | 5563 | ha |
| h3 asl at λ=0.25, first 5 AUC | 0.771 | 0.771 | ha |
| h3 asl, first 5 answers | 8455 | 8455 | ha |
| h3 grafsiz at λ=0.0, first 3 AUC | 0.747 | 0.747 | ha |
| h3 grafsiz, first 3 answers | 5563 | 5563 | ha |
| h3 grafsiz at λ=0.0, first 5 AUC | 0.767 | 0.767 | ha |
| h3 grafsiz, first 5 answers | 8455 | 8455 | ha |

