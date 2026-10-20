# H3 — λ egri chizig‘i, asl graf (D71)

> **post-hoc, tavsifiy — D61/D62 ning o‘qish qoidasi va hukmi o‘zgarmaydi.** (D71)

λ qat’iy (validatsiyada tanlanmaydi); grafsiz — BKT+IRT (λ = 0). AUC — test qismi, mavzudagi dastlabki k urinish; 95 % CI — talaba bo‘yicha bootstrap, 1000 replika.

| λ | AUC, k = 3 [CI] | AUC, k = 5 [CI] | Butun to‘plam AUC |
|---|---|---|---|
| grafsiz | 0.784 [0.776; 0.791] | 0.794 [0.787; 0.8] | 0.772 |
| λ=0.1 | 0.784 [0.776; 0.79] | 0.793 [0.787; 0.799] | 0.772 |
| λ=0.25 | 0.782 [0.776; 0.789] | 0.792 [0.786; 0.799] | 0.772 |
| λ=0.5 | 0.776 [0.769; 0.783] | 0.789 [0.782; 0.795] | 0.771 |
| λ=0.75 | 0.763 [0.756; 0.77] | 0.781 [0.774; 0.787] | 0.769 |
| λ=1 | 0.748 [0.741; 0.756] | 0.771 [0.764; 0.778] | 0.767 |

Javoblar: k = 3: 54798 (2000 talaba); k = 5: 84143 (2000 talaba).

## Manba va takrorlanish

- buyruq: `python -m experiments.d71 --workers 5`
- commit: `c1ad4a9`; asl natija: `experiments/results/junyi-h3/20261019-122423`
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

