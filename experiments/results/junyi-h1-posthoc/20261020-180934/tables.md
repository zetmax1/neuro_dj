# H1 — post-hoc, tavsifiy tahlil (D71)

> **post-hoc, tavsifiy — D61/D62 ning o‘qish qoidasi va hukmi o‘zgarmaydi.** (D71)

## 1. Qism-to‘plam S: barcha prerekvizitlari voqeadan oldin ishlangan voqealar

Voqealar: S = 7136 / 9664 (ulush 0.738), talabalar 664; r_s(w) = 0 bo‘lgan voqealar (to‘liq to‘plam): 2528.

### k = 3

| Qoida | Voqea | Belgilangan | Xato | Qamrov | Xato ulushi |
|---|---|---|---|---|---|
| ehtimoliy (r ≥ τ) | 7136 | 6795 | 1023 | 0.952 | 0.151 |
| II bob R (M, δ bilan) | 7136 | 6803 | 1027 | 0.953 | 0.151 |
| bajarilganlik | 7136 | 7136 | 1189 | 1 | 0.167 |
| o‘tish bali | 7136 | 6857 | 1042 | 0.961 | 0.152 |
| earned_proficiency | 7136 | 6532 | 956 | 0.915 | 0.146 |

Teng qamrov S da (τ validatsiyaning S qismida). Farq = ehtimoliy − qoida, 95 % CI (talaba bo‘yicha bootstrap, 1000 replika).

| Taqqoslash | τ (fold'lar) | Ehtimoliy qamrov | Qoida qamrovi | Ehtimoliy xato ulushi | Qoida xato ulushi | Farq [CI] |
|---|---|---|---|---|---|---|
| o‘tish bali | 0.781, 0.825, 0.863, 0.79, 0.824 | 0.958 | 0.961 | 0.151 | 0.152 | -0.001 [-0.002; 0.001] |
| earned_proficiency | 0.998, 0.998, 0.998, 0.999, 0.999 | 0.91 | 0.915 | 0.147 | 0.146 | 0 [-0.002; 0.003] |
| bajarilganlik | — | — | — | — | — | S da hamma voqeani belgilaydi: taqqoslash “hamma tayyor” bilan bir xil, hisoblanmadi |

S da r_s(w) bo‘yicha AUC: 0.523 [0.496; 0.549] (7136 voqea, 1189 muvaffaqiyatsiz).

### k = 5

| Qoida | Voqea | Belgilangan | Xato | Qamrov | Xato ulushi |
|---|---|---|---|---|---|
| ehtimoliy (r ≥ τ) | 7136 | 6795 | 845 | 0.952 | 0.124 |
| II bob R (M, δ bilan) | 7136 | 6803 | 849 | 0.953 | 0.125 |
| bajarilganlik | 7136 | 7136 | 1004 | 1 | 0.141 |
| o‘tish bali | 7136 | 6857 | 859 | 0.961 | 0.125 |
| earned_proficiency | 7136 | 6532 | 780 | 0.915 | 0.119 |

Teng qamrov S da (τ validatsiyaning S qismida). Farq = ehtimoliy − qoida, 95 % CI (talaba bo‘yicha bootstrap, 1000 replika).

| Taqqoslash | τ (fold'lar) | Ehtimoliy qamrov | Qoida qamrovi | Ehtimoliy xato ulushi | Qoida xato ulushi | Farq [CI] |
|---|---|---|---|---|---|---|
| o‘tish bali | 0.781, 0.825, 0.863, 0.79, 0.824 | 0.958 | 0.961 | 0.125 | 0.125 | -0 [-0.002; 0.002] |
| earned_proficiency | 0.998, 0.998, 0.998, 0.999, 0.999 | 0.91 | 0.915 | 0.12 | 0.119 | 0 [-0.002; 0.003] |
| bajarilganlik | — | — | — | — | — | S da hamma voqeani belgilaydi: taqqoslash “hamma tayyor” bilan bir xil, hisoblanmadi |

S da r_s(w) bo‘yicha AUC: 0.54 [0.515; 0.565] (7136 voqea, 1004 muvaffaqiyatsiz).

## 2. To‘liq to‘plam: r_s(w) bo‘yicha xato–qamrov egri chizig‘i

Nuqtaviy (CI siz). Qatorlar — τ; oxirgi qatorlar — boshqa qoidalar nuqtalari.

| τ / qoida | Qamrov (k = 3) | Xato ulushi (k = 3) | Qamrov (k = 5) | Xato ulushi (k = 5) |
|---|---|---|---|---|
| 0 | 1 | 0.169 | 1 | 0.141 |
| 0.01 | 0.738 | 0.167 | 0.738 | 0.141 |
| 0.02 | 0.738 | 0.166 | 0.738 | 0.14 |
| 0.05 | 0.736 | 0.165 | 0.736 | 0.139 |
| 0.1 | 0.732 | 0.163 | 0.732 | 0.137 |
| 0.2 | 0.722 | 0.158 | 0.722 | 0.132 |
| 0.3 | 0.72 | 0.157 | 0.72 | 0.131 |
| 0.4 | 0.717 | 0.156 | 0.717 | 0.13 |
| 0.5 | 0.714 | 0.154 | 0.714 | 0.128 |
| 0.6 | 0.71 | 0.152 | 0.71 | 0.126 |
| 0.7 | 0.709 | 0.152 | 0.709 | 0.126 |
| 0.8 | 0.707 | 0.152 | 0.707 | 0.125 |
| 0.9 | 0.706 | 0.151 | 0.706 | 0.125 |
| 0.95 | 0.703 | 0.151 | 0.703 | 0.124 |
| 0.99 | 0.695 | 0.149 | 0.695 | 0.123 |
| bajarilganlik | 0.738 | 0.167 | 0.738 | 0.141 |
| o‘tish bali | 0.956 | 0.153 | 0.956 | 0.125 |
| earned_proficiency | 0.676 | 0.146 | 0.676 | 0.119 |

## Manba va takrorlanish

- buyruq: `python -m experiments.d71 --workers 5`
- commit: `c1ad4a9`; asl natija: `experiments/results/junyi-h1/20261019-102526`
- checkpoint: `{"enabled": true, "key_digest": "950ceb8716bad143", "resumed_items": 0, "resumed_folds": 0}`

| Darvoza | Bu run | Asl run | Teng |
|---|---|---|---|
| h1 events | 9664 | 9664 | ha |
| h1 subset (every prerequisite answered) | 7136 | 7136 | ha |
| h1 rule probabilistic (flagged, failed) | 6795, 1023 | 6795, 1023 | ha |
| h1 rule chapter_two (flagged, failed) | 6803, 1027 | 6803, 1027 | ha |
| h1 rule completeness (flagged, failed) | 7136, 1189 | 7136, 1189 | ha |
| h1 rule pass_mark (flagged, failed) | 9239, 1411 | 9239, 1411 | ha |
| h1 rule earned_proficiency (flagged, failed) | 6532, 956 | 6532, 956 | ha |
| h3 asl at λ=0.25, first 3 AUC | 0.782 | 0.782 | ha |
| h3 asl, first 3 answers | 54798 | 54798 | ha |
| h3 asl at λ=0.25, first 5 AUC | 0.792 | 0.792 | ha |
| h3 asl, first 5 answers | 84143 | 84143 | ha |
| h3 grafsiz at λ=0.0, first 3 AUC | 0.784 | 0.784 | ha |
| h3 grafsiz, first 3 answers | 54798 | 54798 | ha |
| h3 grafsiz at λ=0.0, first 5 AUC | 0.794 | 0.794 | ha |
| h3 grafsiz, first 5 answers | 84143 | 84143 | ha |

