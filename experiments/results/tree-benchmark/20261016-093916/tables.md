# H4 — daraxtni saqlash usullari: MPTT va CTE

Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.

Ikkita jadval bir xil daraxtni saqlaydi: `MpttNode` — oraliq kodlash
(django-mptt), `CteNode` — qo‘shni ro‘yxat va rekursiv CTE
(django-tree-queries), ya’ni platformaning o‘zi ishlatadigan usul (D3).

ρ = mediana(MPTT) / mediana(CTE), ya’ni ρ > 1 — CTE tezroq. Oraliq —
juftlashtirilgan bootstrap (1000 replika, 95 %): har takrorda ikkala usul
bir xil nishon tugunda ishlagan.

O‘zgartiruvchi amallar tranzaksiyada o‘lchanadi va orqaga qaytariladi,
shuning uchun har takror bir xil daraxtdan boshlanadi; commit'ning narxi
o‘lchovga kirmaydi va bu ikkala usulga teng ta’sir qiladi (D63).

## 1. Amallar

| Shakl | Hajm | Amal | Tur | MPTT mediana (ms) | CTE mediana (ms) | ρ [CI] | Xulosa |
|---|---|---|---|---|---|---|---|
| course_like | 1000 | shoxni o‘qish | read | 1.114 | 3.397 | 0.328 [0.305, 0.352] | MPTT tezroq |
| course_like | 1000 | ajdodlarni o‘qish | read | 0.944 | 5.696 | 0.166 [0.16, 0.177] | MPTT tezroq |
| course_like | 1000 | oxiriga barg qo‘shish | write | 4.251 | 0.753 | 5.645 [4.402, 7.828] | CTE tezroq |
| course_like | 1000 | eng chapga barg qo‘shish | write | 3.778 | 0.736 | 5.133 [4.344, 7.291] | CTE tezroq |
| course_like | 1000 | shoxni ko‘chirish | write | 9.795 | 5.217 | 1.877 [1.825, 1.935] | CTE tezroq |
| course_like | 1000 | shoxni o‘chirish | write | 5.828 | 1.962 | 2.97 [2.624, 3.49] | CTE tezroq |
| course_like | 10000 | shoxni o‘qish | read | 1.748 | 24.013 | 0.073 [0.07, 0.075] | MPTT tezroq |
| course_like | 10000 | ajdodlarni o‘qish | read | 1.782 | 46.178 | 0.039 [0.037, 0.04] | MPTT tezroq |
| course_like | 10000 | oxiriga barg qo‘shish | write | 47.883 | 0.831 | 57.656 [25.429, 68.517] | CTE tezroq |
| course_like | 10000 | eng chapga barg qo‘shish | write | 42.759 | 0.77 | 55.531 [33.986, 66.351] | CTE tezroq |
| course_like | 10000 | shoxni ko‘chirish | write | 70.229 | 20.796 | 3.377 [3.245, 3.474] | CTE tezroq |
| course_like | 10000 | shoxni o‘chirish | write | 43.097 | 1.954 | 22.056 [14.483, 27.445] | CTE tezroq |
| course_like | 100000 | shoxni o‘qish | read | 7.729 | 352.989 | 0.022 [0.021, 0.022] | MPTT tezroq |
| course_like | 100000 | ajdodlarni o‘qish | read | 5.02 | 775.155 | 0.006 [0.005, 0.008] | MPTT tezroq |
| course_like | 100000 | oxiriga barg qo‘shish | write | 321.231 | 0.783 | 409.996 [310.135, 572.115] | CTE tezroq |
| course_like | 100000 | eng chapga barg qo‘shish | write | 426.498 | 0.717 | 595.251 [492.137, 755.253] | CTE tezroq |
| course_like | 100000 | shoxni ko‘chirish | write | 829.022 | 718.395 | 1.154 [1.02, 1.262] | CTE tezroq |
| course_like | 100000 | shoxni o‘chirish | write | 528.659 | 3.927 | 134.622 [108.464, 163.151] | CTE tezroq |
| deep_chain | 1000 | shoxni o‘qish | read | 3.562 | 173.697 | 0.021 [0.018, 0.024] | MPTT tezroq |
| deep_chain | 1000 | ajdodlarni o‘qish | read | 5.768 | 208.878 | 0.028 [0.022, 0.033] | MPTT tezroq |
| deep_chain | 1000 | oxiriga barg qo‘shish | write | 6.082 | 0.683 | 8.899 [7.565, 11.58] | CTE tezroq |
| deep_chain | 1000 | eng chapga barg qo‘shish | write | 9.312 | 0.685 | 13.593 [13.156, 14.151] | CTE tezroq |
| deep_chain | 1000 | shoxni ko‘chirish | write | 10.374 | 77.385 | 0.134 [0.131, 0.136] | MPTT tezroq |
| deep_chain | 1000 | shoxni o‘chirish | write | 172.102 | 187.507 | 0.918 [0.84, 1.196] | taqqoslanadigan |
| deep_chain | 10000 | shoxni o‘qish | read | 41.249 | 21418.404 | 0.002 [0.002, 0.003] | MPTT tezroq |
| deep_chain | 10000 | ajdodlarni o‘qish | read | 37.577 | 19814.207 | 0.002 [0.001, 0.003] | MPTT tezroq |
| deep_chain | 10000 | oxiriga barg qo‘shish | write | 36.989 | 0.764 | 48.415 [40.733, 54.618] | CTE tezroq |
| deep_chain | 10000 | eng chapga barg qo‘shish | write | 72.098 | 0.751 | 96.067 [84.098, 101.15] | CTE tezroq |
| deep_chain | 10000 | shoxni ko‘chirish | write | 79.956 | 7763.813 | 0.01 [0.009, 0.011] | MPTT tezroq |
| deep_chain | 10000 | shoxni o‘chirish | write | 2401.246 | 2801.424 | 0.857 [0.643, 0.971] | MPTT tezroq |
| deep_chain | 100000 | shoxni o‘qish | read | 559.153 | ishga tushirilmadi — xotira | — | ishga tushirilmadi — xotira |
| deep_chain | 100000 | ajdodlarni o‘qish | read | 422.51 | ishga tushirilmadi — xotira | — | ishga tushirilmadi — xotira |
| deep_chain | 100000 | oxiriga barg qo‘shish | write | 376.859 | 0.914 | 412.093 [283.968, 500.77] | CTE tezroq |
| deep_chain | 100000 | eng chapga barg qo‘shish | write | 877.302 | 0.708 | 1240.002 [1077.99, 1428.343] | CTE tezroq |
| deep_chain | 100000 | shoxni ko‘chirish | write | 975.499 | timeout | — | timeout |
| deep_chain | 100000 | shoxni o‘chirish | write | 22833.5 | 27894.668 | 0.819 [0.784, 0.88] | MPTT tezroq |
| random | 1000 | shoxni o‘qish | read | 1.062 | 3.974 | 0.267 [0.235, 0.302] | MPTT tezroq |
| random | 1000 | ajdodlarni o‘qish | read | 1.226 | 7.24 | 0.169 [0.164, 0.177] | MPTT tezroq |
| random | 1000 | oxiriga barg qo‘shish | write | 6.97 | 0.693 | 10.058 [7.295, 11.321] | CTE tezroq |
| random | 1000 | eng chapga barg qo‘shish | write | 7.199 | 0.704 | 10.225 [8.44, 12.178] | CTE tezroq |
| random | 1000 | shoxni ko‘chirish | write | 11.146 | 5.633 | 1.979 [1.87, 2.052] | CTE tezroq |
| random | 1000 | shoxni o‘chirish | write | 9.18 | 2.068 | 4.439 [3.546, 5.588] | CTE tezroq |
| random | 10000 | shoxni o‘qish | read | 1.541 | 34.594 | 0.045 [0.043, 0.047] | MPTT tezroq |
| random | 10000 | ajdodlarni o‘qish | read | 1.709 | 63.963 | 0.027 [0.026, 0.027] | MPTT tezroq |
| random | 10000 | oxiriga barg qo‘shish | write | 52.423 | 0.738 | 70.985 [50.386, 79.869] | CTE tezroq |
| random | 10000 | eng chapga barg qo‘shish | write | 51.974 | 0.732 | 70.954 [48.662, 87.409] | CTE tezroq |
| random | 10000 | shoxni ko‘chirish | write | 98.671 | 36.252 | 2.722 [2.639, 2.842] | CTE tezroq |
| random | 10000 | shoxni o‘chirish | write | 64.26 | 1.814 | 35.435 [23.573, 43.709] | CTE tezroq |
| random | 100000 | shoxni o‘qish | read | 6.9 | 1214.864 | 0.006 [0.006, 0.006] | MPTT tezroq |
| random | 100000 | ajdodlarni o‘qish | read | 6.275 | 2355.529 | 0.003 [0.003, 0.003] | MPTT tezroq |
| random | 100000 | oxiriga barg qo‘shish | write | 491.017 | 0.723 | 679.138 [522.693, 946.639] | CTE tezroq |
| random | 100000 | eng chapga barg qo‘shish | write | 544.479 | 0.712 | 764.18 [601.983, 1074.081] | CTE tezroq |
| random | 100000 | shoxni ko‘chirish | write | 1021.189 | 1347.456 | 0.758 [0.739, 0.768] | MPTT tezroq |
| random | 100000 | shoxni o‘chirish | write | 543.683 | 1.921 | 283.021 [224.615, 381.878] | CTE tezroq |

## 2. SQL so‘rovlar va o‘zgargan qatorlar

So‘rovlar soni — `CaptureQueriesContext`, har takrorda. O‘zgargan qatorlar
bitta qo‘shimcha, **o‘lchanmagan** takrorda sanaladi: amaldan oldin va keyin
ustunlar solishtiriladi. MPTT ning ko‘chirish qatori shu ustunda ko‘rinadi —
oraliqlar jadvalning katta qismida qayta yoziladi.

| Shakl | Hajm | Amal | MPTT SQL | CTE SQL | MPTT o‘zgargan | CTE o‘zgargan |
|---|---|---|---|---|---|---|
| course_like | 1000 | shoxni o‘qish | 2 | 2 | — | — |
| course_like | 1000 | ajdodlarni o‘qish | 2 | 3 | — | — |
| course_like | 1000 | oxiriga barg qo‘shish | 6 | 4 | 536 | 1 |
| course_like | 1000 | eng chapga barg qo‘shish | 6 | 4 | 546 | 1 |
| course_like | 1000 | shoxni ko‘chirish | 6 | 7 | 456 | 1 |
| course_like | 1000 | shoxni o‘chirish | 8 | 6 | 534 | 0 |
| course_like | 10000 | shoxni o‘qish | 2 | 2 | — | — |
| course_like | 10000 | ajdodlarni o‘qish | 2 | 3 | — | — |
| course_like | 10000 | oxiriga barg qo‘shish | 6 | 4 | 5785 | 1 |
| course_like | 10000 | eng chapga barg qo‘shish | 6 | 4 | 5807 | 1 |
| course_like | 10000 | shoxni ko‘chirish | 6 | 7 | 2716 | 1 |
| course_like | 10000 | shoxni o‘chirish | 8 | 6 | 5783 | 0 |
| course_like | 100000 | shoxni o‘qish | 2 | 2 | — | — |
| course_like | 100000 | ajdodlarni o‘qish | 2 | 3 | — | — |
| course_like | 100000 | oxiriga barg qo‘shish | 6 | 4 | 23793 | 1 |
| course_like | 100000 | eng chapga barg qo‘shish | 6 | 4 | 23840 | 1 |
| course_like | 100000 | shoxni ko‘chirish | 6 | 7 | 62639 | 1 |
| course_like | 100000 | shoxni o‘chirish | 8 | 6 | 23791 | 0 |
| deep_chain | 1000 | shoxni o‘qish | 2 | 2 | — | — |
| deep_chain | 1000 | ajdodlarni o‘qish | 2 | 3 | — | — |
| deep_chain | 1000 | oxiriga barg qo‘shish | 6 | 4 | 411 | 1 |
| deep_chain | 1000 | eng chapga barg qo‘shish | 6 | 4 | 1001 | 1 |
| deep_chain | 1000 | shoxni ko‘chirish | 6 | 7 | 878 | 1 |
| deep_chain | 1000 | shoxni o‘chirish | 0 | 0 | 409 | 0 |
| deep_chain | 10000 | shoxni o‘qish | 0 | 0 | — | — |
| deep_chain | 10000 | ajdodlarni o‘qish | 0 | 0 | — | — |
| deep_chain | 10000 | oxiriga barg qo‘shish | 0 | 0 | 6537 | 1 |
| deep_chain | 10000 | eng chapga barg qo‘shish | 0 | 0 | 10001 | 1 |
| deep_chain | 10000 | shoxni ko‘chirish | 0 | 0 | 8057 | 1 |
| deep_chain | 10000 | shoxni o‘chirish | 0 | 0 | 6535 | 0 |
| deep_chain | 100000 | shoxni o‘qish | 0 | — | — | — |
| deep_chain | 100000 | ajdodlarni o‘qish | 0 | — | — | — |
| deep_chain | 100000 | oxiriga barg qo‘shish | 0 | 0 | 52275 | 1 |
| deep_chain | 100000 | eng chapga barg qo‘shish | 0 | 0 | 100001 | 1 |
| deep_chain | 100000 | shoxni ko‘chirish | 0 | — | 84459 | — |
| deep_chain | 100000 | shoxni o‘chirish | 0 | 0 | 52273 | 0 |
| random | 1000 | shoxni o‘qish | 0 | 0 | — | — |
| random | 1000 | ajdodlarni o‘qish | 0 | 0 | — | — |
| random | 1000 | oxiriga barg qo‘shish | 0 | 0 | 60 | 1 |
| random | 1000 | eng chapga barg qo‘shish | 0 | 0 | 62 | 1 |
| random | 1000 | shoxni ko‘chirish | 0 | 0 | 869 | 1 |
| random | 1000 | shoxni o‘chirish | 0 | 0 | 58 | 0 |
| random | 10000 | shoxni o‘qish | 0 | 0 | — | — |
| random | 10000 | ajdodlarni o‘qish | 0 | 0 | — | — |
| random | 10000 | oxiriga barg qo‘shish | 0 | 0 | 8573 | 1 |
| random | 10000 | eng chapga barg qo‘shish | 0 | 0 | 8574 | 1 |
| random | 10000 | shoxni ko‘chirish | 0 | 0 | 1430 | 1 |
| random | 10000 | shoxni o‘chirish | 0 | 0 | 8571 | 0 |
| random | 100000 | shoxni o‘qish | 0 | 0 | — | — |
| random | 100000 | ajdodlarni o‘qish | 0 | 0 | — | — |
| random | 100000 | oxiriga barg qo‘shish | 0 | 0 | 94827 | 1 |
| random | 100000 | eng chapga barg qo‘shish | 0 | 0 | 94828 | 1 |
| random | 100000 | shoxni ko‘chirish | 0 | 0 | 52104 | 1 |
| random | 100000 | shoxni o‘chirish | 0 | 0 | 94825 | 0 |

## 3. Dumi (p95)

p95 da’voga kirmaydi (D63), lekin UI uchun eng yomon holat ham muhim.

| Shakl | Hajm | Amal | MPTT p95 (ms) | CTE p95 (ms) |
|---|---|---|---|---|
| course_like | 1000 | shoxni o‘qish | 1.633 | 3.807 |
| course_like | 1000 | ajdodlarni o‘qish | 1.273 | 5.993 |
| course_like | 1000 | oxiriga barg qo‘shish | 8.557 | 0.84 |
| course_like | 1000 | eng chapga barg qo‘shish | 8.324 | 0.81 |
| course_like | 1000 | shoxni ko‘chirish | 11.762 | 5.538 |
| course_like | 1000 | shoxni o‘chirish | 11.071 | 3.304 |
| course_like | 10000 | shoxni o‘qish | 2.053 | 25.904 |
| course_like | 10000 | ajdodlarni o‘qish | 2.046 | 48.444 |
| course_like | 10000 | oxiriga barg qo‘shish | 68.395 | 0.973 |
| course_like | 10000 | eng chapga barg qo‘shish | 71.592 | 1.085 |
| course_like | 10000 | shoxni ko‘chirish | 87.894 | 27.693 |
| course_like | 10000 | shoxni o‘chirish | 64.776 | 2.171 |
| course_like | 100000 | shoxni o‘qish | 8.632 | 433.06 |
| course_like | 100000 | ajdodlarni o‘qish | 5.252 | 1218.833 |
| course_like | 100000 | oxiriga barg qo‘shish | 559.035 | 1.115 |
| course_like | 100000 | eng chapga barg qo‘shish | 740.353 | 0.953 |
| course_like | 100000 | shoxni ko‘chirish | 1005.565 | 857.89 |
| course_like | 100000 | shoxni o‘chirish | 863.944 | 4.913 |
| deep_chain | 1000 | shoxni o‘qish | 6.574 | 226.784 |
| deep_chain | 1000 | ajdodlarni o‘qish | 12.836 | 328.026 |
| deep_chain | 1000 | oxiriga barg qo‘shish | 9.659 | 0.744 |
| deep_chain | 1000 | eng chapga barg qo‘shish | 10.818 | 0.713 |
| deep_chain | 1000 | shoxni ko‘chirish | 11.033 | 82.349 |
| deep_chain | 1000 | shoxni o‘chirish | 377.96 | 363.125 |
| deep_chain | 10000 | shoxni o‘qish | 105.587 | 28983.348 |
| deep_chain | 10000 | ajdodlarni o‘qish | 104.274 | 29400.77 |
| deep_chain | 10000 | oxiriga barg qo‘shish | 61.301 | 0.864 |
| deep_chain | 10000 | eng chapga barg qo‘shish | 77.384 | 0.953 |
| deep_chain | 10000 | shoxni ko‘chirish | 85.061 | 10490.922 |
| deep_chain | 10000 | shoxni o‘chirish | 4375.136 | 5018.789 |
| deep_chain | 100000 | shoxni o‘qish | 889.05 | — |
| deep_chain | 100000 | ajdodlarni o‘qish | 1013.652 | — |
| deep_chain | 100000 | oxiriga barg qo‘shish | 746.447 | 1.033 |
| deep_chain | 100000 | eng chapga barg qo‘shish | 1259.535 | 0.969 |
| deep_chain | 100000 | shoxni ko‘chirish | 1070.326 | — |
| deep_chain | 100000 | shoxni o‘chirish | 39249.092 | 49541.744 |
| random | 1000 | shoxni o‘qish | 1.348 | 4.097 |
| random | 1000 | ajdodlarni o‘qish | 1.599 | 10.382 |
| random | 1000 | oxiriga barg qo‘shish | 9.788 | 0.726 |
| random | 1000 | eng chapga barg qo‘shish | 10.743 | 0.749 |
| random | 1000 | shoxni ko‘chirish | 12.209 | 6.415 |
| random | 1000 | shoxni o‘chirish | 12.452 | 2.892 |
| random | 10000 | shoxni o‘qish | 1.834 | 35.809 |
| random | 10000 | ajdodlarni o‘qish | 1.762 | 65.76 |
| random | 10000 | oxiriga barg qo‘shish | 76.705 | 0.769 |
| random | 10000 | eng chapga barg qo‘shish | 87.803 | 0.788 |
| random | 10000 | shoxni ko‘chirish | 135.071 | 37.51 |
| random | 10000 | shoxni o‘chirish | 88.484 | 3.688 |
| random | 100000 | shoxni o‘qish | 7.592 | 1226.565 |
| random | 100000 | ajdodlarni o‘qish | 6.776 | 2385.907 |
| random | 100000 | oxiriga barg qo‘shish | 954.416 | 0.841 |
| random | 100000 | eng chapga barg qo‘shish | 1017.604 | 0.739 |
| random | 100000 | shoxni ko‘chirish | 1063.672 | 1374.711 |
| random | 100000 | shoxni o‘chirish | 914.28 | 4.846 |

## 4. Parallel yozish va yaxlitlik

Har bir jarayon o‘z ulanishi bilan, belgilangan vaqt davomida aralash
qo‘shish va ko‘chirish bajaradi. ρ — CTE ning o‘tkazuvchanligi MPTT ga
nisbatan (ρ > 1 — CTE tezroq). Yaxlitlik ustunlari parallel yozish
**tugagandan keyin** o‘qiladi: Y1 ikkala usulda, oraliqlar tekshiruvi
MPTT da.

Variant (D63a): `unlocked` — har bir usulning o‘z yozish yo‘li, qulfsiz;
`locked` — platformaning yo‘li, `pg_advisory_xact_lock` bilan. D63 ning
yaxlitlik sharti **qulfli** variantdan o‘qiladi; qulfsiz qatorlar
saqlash usulining o‘zi nimani kafolatlaganini ko‘rsatadi.

| Shakl | Hajm | Jarayon | Variant | CTE op/s | MPTT op/s | ρ CI | Xulosa | CTE yaxlit | MPTT yaxlit | CTE xato | MPTT xato |
|---|---|---|---|---|---|---|---|---|---|---|---|
| course_like | 1000 | 2 | unlocked | 207.5 | 135.956 | [1.193, 1.627] | CTE tezroq | ha | yo‘q | 102 | 1177 |
| course_like | 1000 | 4 | unlocked | 278.438 | 1.751 | [117.045, 202.5] | CTE tezroq | ha | yo‘q | 254 | 66 |
| course_like | 1000 | 8 | unlocked | 317.061 | 1.299 | [220.723, 335.514] | CTE tezroq | ha | yo‘q | 797 | 93 |
| course_like | 1000 | 8 | locked | 131.973 | 98.814 | [1.032, 1.391] | CTE tezroq | ha | ha | 51 | 29 |
| course_like | 10000 | 2 | unlocked | 115.078 | 3.514 | [32.748, 37] | CTE tezroq | ha | yo‘q | 3 | 45 |
| course_like | 10000 | 4 | unlocked | 199.409 | 2.58 | [72.974, 134.736] | CTE tezroq | ha | yo‘q | 4 | 52 |
| course_like | 10000 | 8 | unlocked | 265.974 | 0.86 | [206.689, 506.617] | CTE tezroq | ha | yo‘q | 4 | 81 |
| course_like | 10000 | 8 | locked | 65.547 | 9.939 | [6.017, 7.484] | CTE tezroq | ha | ha | 0 | 0 |
| course_like | 100000 | 2 | unlocked | 5.794 | 0.645 | [8.422, 11.499] | CTE tezroq | ha | yo‘q | 0 | 22 |
| course_like | 100000 | 4 | unlocked | 10.908 | 0.56 | [18.413, 45.554] | CTE tezroq | ha | yo‘q | 0 | 53 |
| course_like | 100000 | 8 | unlocked | 16.661 | 0.696 | [18.839, 29.879] | CTE tezroq | ha | yo‘q | 0 | 50 |
| course_like | 100000 | 8 | locked | 3.725 | 1.073 | [3.076, 4.091] | CTE tezroq | ha | yo‘q | 0 | 0 |
| deep_chain | 1000 | 2 | unlocked | 110.315 | 127.972 | [0.79, 1.095] | taqqoslanadigan | ha | yo‘q | 282 | 3433 |
| deep_chain | 1000 | 4 | unlocked | 194.146 | 1.613 | [49.124, 128.206] | CTE tezroq | ha | yo‘q | 515 | 148 |
| deep_chain | 1000 | 8 | unlocked | 283.343 | 0.939 | [279.004, 315.581] | CTE tezroq | yo‘q | yo‘q | 810 | 191 |
| deep_chain | 1000 | 8 | locked | 74.978 | 117.027 | [0.533, 0.718] | MPTT tezroq | ha | ha | 186 | 269 |
| deep_chain | 10000 | 2 | unlocked | 0.376 | 3.531 | [0.093, 0.116] | MPTT tezroq | ha | yo‘q | 3 | 100 |
| deep_chain | 10000 | 4 | unlocked | 0.664 | 1.705 | [0.269, 0.431] | MPTT tezroq | ha | yo‘q | 6 | 129 |
| deep_chain | 10000 | 8 | unlocked | 0.761 | 0.718 | [0.658, 1.112] | taqqoslanadigan | ha | yo‘q | 13 | 178 |
| deep_chain | 10000 | 8 | locked | 0.234 | 7.77 | [0.019, 0.053] | MPTT tezroq | ha | yo‘q | 7 | 41 |
| deep_chain | 100000 | 2 | unlocked | 0.017 | 0.777 | [0.022, 0.024] | MPTT tezroq | ha | yo‘q | 6 | 64 |
| deep_chain | 100000 | 4 | unlocked | 0.033 | 0.582 | [0.042, 0.059] | MPTT tezroq | ha | yo‘q | 12 | 105 |
| deep_chain | 100000 | 8 | unlocked | 0.066 | 0.398 | [0.156, 0.177] | MPTT tezroq | ha | yo‘q | 24 | 149 |
| deep_chain | 100000 | 8 | locked | 0.066 | 1.109 | [0.053, 0.06] | MPTT tezroq | ha | yo‘q | 24 | 28 |
| random | 1000 | 2 | unlocked | 196.813 | 151.815 | [1.263, 1.346] | CTE tezroq | ha | yo‘q | 158 | 2222 |
| random | 1000 | 4 | unlocked | 262.108 | 1.523 | [45.287, 239.875] | CTE tezroq | ha | yo‘q | 422 | 68 |
| random | 1000 | 8 | unlocked | 333.898 | 1.542 | [183.4, 302.385] | CTE tezroq | ha | yo‘q | 573 | 94 |
| random | 1000 | 8 | locked | 122.05 | 130.883 | [0.836, 1.025] | taqqoslanadigan | ha | ha | 82 | 89 |
| random | 10000 | 2 | unlocked | 91.265 | 3.132 | [27.153, 29.631] | CTE tezroq | ha | yo‘q | 6 | 47 |
| random | 10000 | 4 | unlocked | 122.64 | 1.279 | [42.851, 105.685] | CTE tezroq | ha | yo‘q | 10 | 53 |
| random | 10000 | 8 | unlocked | 168.437 | 1.001 | [135.727, 182.845] | CTE tezroq | ha | yo‘q | 14 | 91 |
| random | 10000 | 8 | locked | 48.502 | 11.44 | [4.234, 4.389] | CTE tezroq | ha | ha | 6 | 3 |
| random | 100000 | 2 | unlocked | 2.487 | 0.974 | [2.411, 3.261] | CTE tezroq | ha | yo‘q | 2 | 17 |
| random | 100000 | 4 | unlocked | 4.819 | 0.544 | [5.16, 9.875] | CTE tezroq | ha | yo‘q | 3 | 29 |
| random | 100000 | 8 | unlocked | 7.679 | 0.363 | [20.784, 21.94] | CTE tezroq | ha | yo‘q | 3 | 60 |
| random | 100000 | 8 | locked | 1.849 | 1.022 | [1.567, 2.05] | CTE tezroq | ha | yo‘q | 0 | 0 |

## 5. O‘lchangan daraxtlar

Benchmark'ning kirishi fayl emas, generator: uning izi — `parent_id`
ketma-ketligining sha256'si. Ikkala usul bir xil ketma-ketlikdan quriladi,
shuning uchun hash ikki qatorda bir xil bo‘ladi. Qurish vaqti amal emas va
o‘lchovga kirmaydi.

| Shakl | Hajm | Usul | Tugun | Maks chuqurlik | sha256 | Qurish (s) |
|---|---|---|---|---|---|---|
| course_like | 1000 | mptt | 1000 | 3 | `dee517a825db` | 0.049 |
| course_like | 1000 | cte | 1000 | 3 | `dee517a825db` | 0.023 |
| course_like | 10000 | mptt | 10000 | 3 | `6eb0b80090fe` | 0.458 |
| course_like | 10000 | cte | 10000 | 3 | `6eb0b80090fe` | 0.271 |
| course_like | 100000 | mptt | 100000 | 3 | `4cd38264057b` | 4.171 |
| course_like | 100000 | cte | 100000 | 3 | `4cd38264057b` | 2.608 |
| deep_chain | 1000 | mptt | 1000 | 999 | `2c7d91e72f6a` | 0.067 |
| deep_chain | 1000 | cte | 1000 | 999 | `2c7d91e72f6a` | 0.03 |
| deep_chain | 10000 | mptt | 10000 | 9999 | `71aa31b40fef` | 0.406 |
| deep_chain | 10000 | cte | 10000 | 9999 | `71aa31b40fef` | 0.245 |
| deep_chain | 100000 | mptt | 100000 | 99999 | `6cc718522da2` | 4.224 |
| deep_chain | 100000 | cte | 100000 | 99999 | `6cc718522da2` | 2.413 |
| random | 1000 | mptt | 1000 | 12 | `f92083ccb676` | 0.062 |
| random | 1000 | cte | 1000 | 12 | `f92083ccb676` | 0.027 |
| random | 10000 | mptt | 10000 | 17 | `bc4155b2e63d` | 0.331 |
| random | 10000 | cte | 10000 | 17 | `bc4155b2e63d` | 0.209 |
| random | 100000 | mptt | 100000 | 24 | `046e0183f27b` | 3.807 |
| random | 100000 | cte | 100000 | 24 | `046e0183f27b` | 2.184 |

## 6. O‘qish qoidasi (natijadan oldin yozilgan)

H4 qo‘llab-quvvatlandi: to‘rtta yozish amalining har birida, har bir shakl va hajmda “CTE tezroq”; o‘qishda hech bir katakda CTE 1,5 barobardan ko‘proq sekin emas; parallel yozishdan keyin CTE da yaxlitlik buzilishi yo‘q (D63)

**Xulosa: qo‘llab-quvvatlanmadi.**

| Shart | Buzilgan katak | Qaysi |
|---|---|---|
| yozish amallari | 6 | move_branch@deep_chain/1000, delete_branch@deep_chain/1000, move_branch@deep_chain/10000, delete_branch@deep_chain/10000, delete_branch@deep_chain/100000, move_branch@random/100000 |
| o‘qish amallari | 16 | read_branch@course_like/1000, read_ancestors@course_like/1000, read_branch@course_like/10000, read_ancestors@course_like/10000, read_branch@course_like/100000, read_ancestors@course_like/100000, read_branch@deep_chain/1000, read_ancestors@deep_chain/1000, read_branch@deep_chain/10000, read_ancestors@deep_chain/10000, read_branch@random/1000, read_ancestors@random/1000, read_branch@random/10000, read_ancestors@random/10000, read_branch@random/100000, read_ancestors@random/100000 |
| parallel yozishdagi yaxlitlik | 0 | — |
| son chiqmagan kataklar | 3 | read_branch@deep_chain/100000, read_ancestors@deep_chain/100000, move_branch@deep_chain/100000 |

## 7. Muhit

Vaqt o‘lchovlari mashinaga bog‘liq; nisbat va uning oralig‘i kamroq
bog‘liq, shuning uchun da’vo ular ustiga qurilgan.

- PostgreSQL: 16.15 (Debian 16.15-1.pgdg13+2), `shared_buffers` 128MB, `fsync` on, `synchronous_commit` on
- baza: `neurolearn_bench` (alias `benchmark`)
- CPU: 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz, mantiqiy yadro 16, governor powersave
- RAM: 15615900 kB, bo‘sh 7153264 kB
- yuklama (boshida): 0.99
- platforma: Linux-7.0.0-38-generic-x86_64-with-glibc2.43

Ishga tushirish paytida eng ko‘p CPU yegan jarayonlar:

| Jarayon | CPU % |
|---|---|
| `python` | 323 |
| `editors_helper` | 20.4 |
| `chrome` | 11.9 |
| `telegram-deskto` | 10.8 |
| `chrome` | 9.2 |

## 8. Manba va ishga tushirish (D48)

- kod commit'i: `b8d6b3a`
- buyruq: `python manage.py run_tree_benchmark --database benchmark --shapes course_like,deep_chain,random --warmups 5 --repeats 30 --timeout 120.0 --parallel-repeats 3 --seed 20261006 --memory-limit-gb 8.0`
- vaqt: 2026-10-16T09:39:16.486137+00:00
- python: 3.12.3, Linux-7.0.0-38-generic-x86_64-with-glibc2.43
- git holati boshida: `b8d6b3a`, toza (2026-10-16T03:51:58.940646+00:00)
- git holati oxirida: `b8d6b3a`, toza (2026-10-16T09:39:16.485981+00:00)
- seed: bootstrap = 20261006, targets = 20261006, trees = 20261006
- paketlar: django 6.0.5, django-mptt 0.18.0, django-tree-queries 0.24.0, psycopg 3.3.6

| Fayl | sha256 | Bayt |
|---|---|---|
| — | — | — |

