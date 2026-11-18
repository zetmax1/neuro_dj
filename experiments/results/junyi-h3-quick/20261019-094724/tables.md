# H3 — Junyi Academy (2015): graf nazoratlari

Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.

Bitta model (BKT+IRT+Pre), to‘rt graf: asl, teskari, daraja saqlangan
tasodifiy va grafsiz (λ = 0). Teskari va tasodifiy graflar — null
modellar: ularning zichligi va daraja taqsimoti asl grafnikidek, demak
ulardan ustun kelgan natija grafning **munosabatlaridan** keladi,
shunchaki prior silliqligidan emas.

λ validatsiyada tanlanadi (grid: 0.25, 0.5, 0.75; II bobning qiymati 0.5), har bir arm uchun alohida. Tasodifiy graflar birinchisining λ sini qayta ishlatadi.

O‘lchov — mavzudagi dastlabki k = 3 urinish bo‘yicha AUC; butun to‘plam AUC'i yonida ustun sifatida turadi.

> **`--quick` ishga tushirish — dissertatsiya natijasi emas.** Bu quvurni
> sinash uchun: talabalarning kichik qismi va kam tasodifiy graf. To‘liq
> natija uchun `python -m experiments.h3` bayroqsiz ishga tushiriladi.

## 1. Arm'lar

AUC uchun 95 % ishonch oralig‘i — talabalar bo‘yicha bootstrap, 1000 replika. Tasodifiy graflarning faqat birinchisi uchun oraliq hisoblanadi (D61);
qolganlarining taqsimoti keyingi bo‘limda.

| Arm | Oila | Qirra | λ (1-fold) | AUC [CI] | Butun to‘plam AUC | Javob |
|---|---|---|---|---|---|---|
| asl | asl | 976 | 0.25 | 0.752 [0.732, 0.772] | 0.754 | 5563 |
| teskari | teskari | 976 | 0.25 | 0.749 [0.728, 0.77] | 0.751 | 5563 |
| tasodifiy-1 | tasodifiy | 976 | 0.25 | 0.747 [0.726, 0.766] | 0.75 | 5563 |
| tasodifiy-2 | tasodifiy | 976 | 0.25 | 0.749 | 0.75 | 5563 |
| tasodifiy-3 | tasodifiy | 976 | 0.25 | 0.744 | 0.749 | 5563 |
| grafsiz | grafsiz | 0 | 0 | 0.747 [0.726, 0.767] | 0.752 | 5563 |

## 2. Oilalar

| Oila | Arm | AUC min | AUC mediana | AUC max | AUC o‘rtacha |
|---|---|---|---|---|---|
| asl | 1 | 0.752 | 0.752 | 0.752 | 0.752 |
| teskari | 1 | 0.749 | 0.749 | 0.749 | 0.749 |
| tasodifiy | 3 | 0.744 | 0.747 | 0.749 | 0.746 |
| grafsiz | 1 | 0.747 | 0.747 | 0.747 | 0.747 |

## 3. Kontrastlar

Farq — asl grafning AUC'i minus taqqoslanadigan armning AUC'i; tasodifiy
oila uchun bu uning arm'lari bo‘yicha **o‘rtacha**. Ishonch oralig‘i —
talabalar bo‘yicha klasterlangan bootstrap. DeLong o‘rtachani ifodalay
olmaydi, shuning uchun u oilaning medianasi bo‘lgan armga qarshi
hisoblanadi va ustunda shu arm nomi turadi.

| Taqqoslash | Farq | CI | DeLong qarshi | DeLong p | Holm p |
|---|---|---|---|---|---|
| asl − teskari | 0.004 | [-0.001, 0.009] | teskari | 0.028 | 0.028 |
| asl − tasodifiy | 0.006 | [0.002, 0.01] | tasodifiy-1 | 0.001 | 0.002 |
| asl − grafsiz | 0.006 | [0.001, 0.011] | grafsiz | 0.001 | 0.002 |

## 4. O‘qish qoidasi (natijadan oldin yozilgan)

asl graf uchtasidan ham yuqori va har uch farqning 95 % CI si nolni kesib o‘tmasa — qo‘llab-quvvatlandi (D61)

natija shu graf uchun o‘qiladi — platformaning 2015-yil yanvardagi bilim xaritasi, bitta birlashtirilgan sikl va prerekvizitsiz mashqlar bilan (D61)

cheklov: Junyi platformasi mashqni uning prerekvizitlari o‘zlashtirilgach tavsiya qiladi (suggested), shuning uchun ta’sirning bir qismi grafning o‘zidan emas, platformaning shu graf bo‘yicha yo‘naltirishidan kelishi mumkin (D62a). Tanlangan namunada `suggested` ulushi: 0.249.

Holm oilasi: H3: uch kontrast, har k uchun alohida oila (D62a).

Qo‘shimcha (tavsifiy, D62a): asl grafning AUC'i 0.752, tasodifiy graflarning eng yuqorisi 0.749 — asl yuqorimi: ha; bootstrap replikatlarining 0.91 ulushida yuqori.

**Xulosa: aniqlanmadi.**

| Taqqoslash | Farq | CI | Xulosa |
|---|---|---|---|
| teskari | 0.004 | [-0.001, 0.009] | aniqlanmadi |
| tasodifiy | 0.006 | [0.002, 0.01] | qo‘llab-quvvatlandi |
| grafsiz | 0.006 | [0.001, 0.011] | qo‘llab-quvvatlandi |

## 5. Dastlabki k bo‘yicha

Har bir k uchun mavzudagi dastlabki k urinish. Tasodifiy oiladan faqat
birinchi graf ko‘rsatiladi; oilaning taqsimoti ikkinchi bo‘limda.

| k | Arm | AUC | RMSE | Aniqlik | Javob |
|---|---|---|---|---|---|
| 3 | asl | 0.752 | 0.404 | 0.763 | 5563 |
| 3 | teskari | 0.749 | 0.411 | 0.748 | 5563 |
| 3 | tasodifiy-1 | 0.747 | 0.411 | 0.747 | 5563 |
| 3 | grafsiz | 0.747 | 0.414 | 0.747 | 5563 |
| 5 | asl | 0.771 | 0.379 | 0.796 | 8455 |
| 5 | teskari | 0.768 | 0.385 | 0.786 | 8455 |
| 5 | tasodifiy-1 | 0.766 | 0.385 | 0.785 | 8455 |
| 5 | grafsiz | 0.767 | 0.387 | 0.785 | 8455 |

## 6. Qismlar

| Fold (indeks) | Train | Validatsiya | Test | Test javob |
|---|---|---|---|---|
| 0 | 128 | 32 | 40 | 4508 |
| 1 | 128 | 32 | 40 | 6476 |
| 2 | 128 | 32 | 40 | 4329 |
| 3 | 128 | 32 | 40 | 7064 |
| 4 | 128 | 32 | 40 | 861 |

## 7. Ma'lumot

- to‘plam: Junyi Academy (2015)
- litsenziya: Any form of commercial usage is not allowed! (junyi/README.md)
- iqtibos: Haw-Shiuan Chang, Hwai-Jung Hsu and Kuan-Ta Chen, “Modeling Exercise Relationships in E-Learning: A Unified Approach”, EDM 2015

| Ko‘rsatkich | Qiymat |
|---|---|
| mashqlar jadvalidagi qator | 837 |
| noyob mashq | 835 |
| area | 9 |
| topic | 41 |
| o‘qilgan prerekvizit yozuvi | 984 |
| noyob qirra | 979 |
| o‘z-o‘ziga qirra (Y2, tashlangan) | 2 |
| takroriy qirra | 3 |
| nomi topilmagan prerekvizit | 0 |
| birlashtirilgan SCC | 1 |
| birlashtirilgan tugun | 3 |
| mavzu (birlashtirilgandan keyin) | 833 |
| qirra (birlashtirilgandan keyin) | 976 |
| eng uzun yo‘l | 65 |
| prerekvizitsiz mavzu | 97 |
| logdagi qator (butun fayl) | 25925992 |
| logdagi talaba (butun fayl) | 247606 |
| tanlangan talaba | 200 |
| ishlatilgan javob | 23238 |
| ishlatilgan mavzu | 345 |

Tozalash qoidalari (D61):

- keep only exercises present in the exercise table
- correct is the published first-attempt column; nothing is recomputed
- order by learner, then time_done (µs), then problem_number, then file order
- one answer is one order: order_id is per row (D57)
- review_mode answers are kept; topic_mode and suggested are metadata only
- live is metadata, not a filter

## 8. Manba va ishga tushirish (D48)

- kod commit'i: `a0b3480`
- buyruq: `python -m experiments.h3 --quick --workers 4`
- vaqt: 2026-10-19T09:47:24.879568+00:00
- python: 3.12.3, Linux-7.0.0-38-generic-x86_64-with-glibc2.43
- git holati boshida: `a0b3480`, toza (2026-10-19T09:37:21.391808+00:00)
- git holati oxirida: `a0b3480`, toza (2026-10-19T09:47:24.879548+00:00)
- seed: bootstrap = 20261006, graphs = 20261006, sample = 20261006, split = 20261006
- paketlar: numpy 1.26.4, pandas 2.3.3, pyBKT 1.4.3, pykt 0.0.38, scipy 1.14.1, sklearn 1.6.1, torch 2.5.1+cpu

| Fayl | sha256 | Bayt |
|---|---|---|
| `junyi-exercise-table` | `13292cc2c809985abbacedaba434e39aeb02a7fcb2a32f17b60c4d3f4d769546` | 139957 |
| `junyi-problem-log` | `a7c99ede1f9b19648fdcd953b6ca0b0282bd31f2f913bd9d26b23aa9fcb36a25` | 2668566436 |

