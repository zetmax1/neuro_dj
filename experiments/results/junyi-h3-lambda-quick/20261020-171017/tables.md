# H3 — λ egri chizig‘i, asl graf (D71)

> **post-hoc, tavsifiy — D61/D62 ning o‘qish qoidasi va hukmi o‘zgarmaydi.** (D71)

> **`--quick` ishga tushirish — dissertatsiya natijasi emas.**

λ qat’iy (validatsiyada tanlanmaydi); grafsiz — BKT+IRT (λ = 0). AUC — test qismi, mavzudagi dastlabki k urinish; 95 % CI — talaba bo‘yicha bootstrap, 100 replika.

| λ | AUC, k = 3 [CI] | AUC, k = 5 [CI] | Butun to‘plam AUC |
|---|---|---|---|
| grafsiz | 0.747 [0.724; 0.764] | 0.767 [0.747; 0.785] | 0.752 |
| λ=0.1 | 0.75 [0.729; 0.767] | 0.769 [0.749; 0.788] | 0.753 |
| λ=0.25 | 0.752 [0.731; 0.769] | 0.771 [0.752; 0.789] | 0.754 |
| λ=0.5 | 0.753 [0.733; 0.771] | 0.772 [0.753; 0.788] | 0.755 |
| λ=0.75 | 0.747 [0.727; 0.767] | 0.769 [0.75; 0.785] | 0.755 |
| λ=1 | 0.739 [0.718; 0.76] | 0.763 [0.744; 0.781] | 0.754 |

Javoblar: k = 3: 5563 (200 talaba); k = 5: 8455 (200 talaba).

## Manba va takrorlanish

- buyruq: `python -m experiments.d71 --quick --workers 5`
- commit: `f88ded8`; asl natija: `experiments/results/junyi-h3-quick/20261019-094724`
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

