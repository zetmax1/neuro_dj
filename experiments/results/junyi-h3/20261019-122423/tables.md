# H3 — Junyi Academy (2015): graf nazoratlari

Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q.

> **Ogohlantirish (D54):** ishchi daraxt ishga tushirish boshida toza emas edi.
> Tafsilot — “Manba va ishga tushirish” bo‘limida.

Bitta model (BKT+IRT+Pre), to‘rt graf: asl, teskari, daraja saqlangan
tasodifiy va grafsiz (λ = 0). Teskari va tasodifiy graflar — null
modellar: ularning zichligi va daraja taqsimoti asl grafnikidek, demak
ulardan ustun kelgan natija grafning **munosabatlaridan** keladi,
shunchaki prior silliqligidan emas.

λ validatsiyada tanlanadi (grid: 0.25, 0.5, 0.75; II bobning qiymati 0.5), har bir arm uchun alohida. Tasodifiy graflar birinchisining λ sini qayta ishlatadi.

O‘lchov — mavzudagi dastlabki k = 3 urinish bo‘yicha AUC; butun to‘plam AUC'i yonida ustun sifatida turadi.

## 1. Arm'lar

AUC uchun 95 % ishonch oralig‘i — talabalar bo‘yicha bootstrap, 1000 replika. Tasodifiy graflarning faqat birinchisi uchun oraliq hisoblanadi (D61);
qolganlarining taqsimoti keyingi bo‘limda.

| Arm | Oila | Qirra | λ (1-fold) | AUC [CI] | Butun to‘plam AUC | Javob |
|---|---|---|---|---|---|---|
| asl | asl | 976 | 0.25 | 0.782 [0.776, 0.789] | 0.772 | 54798 |
| teskari | teskari | 976 | 0.25 | 0.782 [0.774, 0.789] | 0.77 | 54798 |
| tasodifiy-1 | tasodifiy | 976 | 0.25 | 0.776 [0.768, 0.783] | 0.768 | 54798 |
| tasodifiy-2 | tasodifiy | 976 | 0.25 | 0.776 | 0.768 | 54798 |
| tasodifiy-3 | tasodifiy | 976 | 0.25 | 0.776 | 0.768 | 54798 |
| tasodifiy-4 | tasodifiy | 976 | 0.25 | 0.777 | 0.768 | 54798 |
| tasodifiy-5 | tasodifiy | 976 | 0.25 | 0.778 | 0.769 | 54798 |
| tasodifiy-6 | tasodifiy | 976 | 0.25 | 0.778 | 0.769 | 54798 |
| tasodifiy-7 | tasodifiy | 976 | 0.25 | 0.777 | 0.768 | 54798 |
| tasodifiy-8 | tasodifiy | 976 | 0.25 | 0.778 | 0.768 | 54798 |
| tasodifiy-9 | tasodifiy | 976 | 0.25 | 0.779 | 0.769 | 54798 |
| tasodifiy-10 | tasodifiy | 976 | 0.25 | 0.777 | 0.768 | 54798 |
| tasodifiy-11 | tasodifiy | 976 | 0.25 | 0.778 | 0.769 | 54798 |
| tasodifiy-12 | tasodifiy | 976 | 0.25 | 0.779 | 0.769 | 54798 |
| tasodifiy-13 | tasodifiy | 976 | 0.25 | 0.777 | 0.768 | 54798 |
| tasodifiy-14 | tasodifiy | 976 | 0.25 | 0.777 | 0.768 | 54798 |
| tasodifiy-15 | tasodifiy | 976 | 0.25 | 0.778 | 0.769 | 54798 |
| tasodifiy-16 | tasodifiy | 976 | 0.25 | 0.777 | 0.768 | 54798 |
| tasodifiy-17 | tasodifiy | 976 | 0.25 | 0.778 | 0.769 | 54798 |
| tasodifiy-18 | tasodifiy | 976 | 0.25 | 0.778 | 0.769 | 54798 |
| tasodifiy-19 | tasodifiy | 976 | 0.25 | 0.776 | 0.768 | 54798 |
| tasodifiy-20 | tasodifiy | 976 | 0.25 | 0.776 | 0.768 | 54798 |
| grafsiz | grafsiz | 0 | 0 | 0.784 [0.776, 0.791] | 0.772 | 54798 |

## 2. Oilalar

| Oila | Arm | AUC min | AUC mediana | AUC max | AUC o‘rtacha |
|---|---|---|---|---|---|
| asl | 1 | 0.782 | 0.782 | 0.782 | 0.782 |
| teskari | 1 | 0.782 | 0.782 | 0.782 | 0.782 |
| tasodifiy | 20 | 0.776 | 0.777 | 0.779 | 0.777 |
| grafsiz | 1 | 0.784 | 0.784 | 0.784 | 0.784 |

## 3. Kontrastlar

Farq — asl grafning AUC'i minus taqqoslanadigan armning AUC'i; tasodifiy
oila uchun bu uning arm'lari bo‘yicha **o‘rtacha**. Ishonch oralig‘i —
talabalar bo‘yicha klasterlangan bootstrap. DeLong o‘rtachani ifodalay
olmaydi, shuning uchun u oilaning medianasi bo‘lgan armga qarshi
hisoblanadi va ustunda shu arm nomi turadi.

| Taqqoslash | Farq | CI | DeLong qarshi | DeLong p | Holm p |
|---|---|---|---|---|---|
| asl − teskari | 0.001 | [-0, 0.002] | teskari | 0.075 | 0.075 |
| asl − tasodifiy | 0.005 | [0.004, 0.006] | tasodifiy-13 | 0 | 0 |
| asl − grafsiz | -0.001 | [-0.002, 0] | grafsiz | 0.007 | 0.015 |

## 4. O‘qish qoidasi (natijadan oldin yozilgan)

asl graf uchtasidan ham yuqori va har uch farqning 95 % CI si nolni kesib o‘tmasa — qo‘llab-quvvatlandi (D61)

natija shu graf uchun o‘qiladi — platformaning 2015-yil yanvardagi bilim xaritasi, bitta birlashtirilgan sikl va prerekvizitsiz mashqlar bilan (D61)

cheklov: Junyi platformasi mashqni uning prerekvizitlari o‘zlashtirilgach tavsiya qiladi (suggested), shuning uchun ta’sirning bir qismi grafning o‘zidan emas, platformaning shu graf bo‘yicha yo‘naltirishidan kelishi mumkin (D62a). Tanlangan namunada `suggested` ulushi: 0.218.

Holm oilasi: H3: uch kontrast, har k uchun alohida oila (D62a).

Qo‘shimcha (tavsifiy, D62a): asl grafning AUC'i 0.782, tasodifiy graflarning eng yuqorisi 0.779 — asl yuqorimi: ha; bootstrap replikatlarining 1 ulushida yuqori.

**Xulosa: aniqlanmadi.**

| Taqqoslash | Farq | CI | Xulosa |
|---|---|---|---|
| teskari | 0.001 | [-0, 0.002] | aniqlanmadi |
| tasodifiy | 0.005 | [0.004, 0.006] | qo‘llab-quvvatlandi |
| grafsiz | -0.001 | [-0.002, 0] | aniqlanmadi |

## 5. Dastlabki k bo‘yicha

Har bir k uchun mavzudagi dastlabki k urinish. Tasodifiy oiladan faqat
birinchi graf ko‘rsatiladi; oilaning taqsimoti ikkinchi bo‘limda.

| k | Arm | AUC | RMSE | Aniqlik | Javob |
|---|---|---|---|---|---|
| 3 | asl | 0.782 | 0.387 | 0.782 | 54798 |
| 3 | teskari | 0.782 | 0.387 | 0.78 | 54798 |
| 3 | tasodifiy-1 | 0.776 | 0.389 | 0.78 | 54798 |
| 3 | grafsiz | 0.784 | 0.388 | 0.781 | 54798 |
| 5 | asl | 0.792 | 0.368 | 0.808 | 84143 |
| 5 | teskari | 0.792 | 0.369 | 0.806 | 84143 |
| 5 | tasodifiy-1 | 0.787 | 0.37 | 0.805 | 84143 |
| 5 | grafsiz | 0.794 | 0.369 | 0.806 | 84143 |

## 6. Qismlar

| Fold (indeks) | Train | Validatsiya | Test | Test javob |
|---|---|---|---|---|
| 0 | 1280 | 320 | 400 | 46539 |
| 1 | 1280 | 320 | 400 | 54545 |
| 2 | 1280 | 320 | 400 | 37800 |
| 3 | 1280 | 320 | 400 | 54386 |
| 4 | 1280 | 320 | 400 | 59467 |

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
| tanlangan talaba | 2000 |
| ishlatilgan javob | 252737 |
| ishlatilgan mavzu | 619 |

Tozalash qoidalari (D61):

- keep only exercises present in the exercise table
- correct is the published first-attempt column; nothing is recomputed
- order by learner, then time_done (µs), then problem_number, then file order
- one answer is one order: order_id is per row (D57)
- review_mode answers are kept; topic_mode and suggested are metadata only
- live is metadata, not a filter

## 8. Manba va ishga tushirish (D48)

- kod commit'i: `2500c77` (kuzatilmagan o‘zgarishlar bilan)
- buyruq: `python -m experiments.h3 --workers 5`
- vaqt: 2026-10-19T12:24:22.789476+00:00
- python: 3.12.3, Linux-7.0.0-38-generic-x86_64-with-glibc2.43
- git holati boshida: `2500c77`, toza emas (2026-10-19T10:25:26.389200+00:00)
  - `?? experiments/results/junyi-h1/`
- git holati oxirida: `2500c77`, toza emas (2026-10-19T12:24:22.789442+00:00)
  - `?? experiments/results/junyi-h1/`
- seed: bootstrap = 20261006, graphs = 20261006, sample = 20261006, split = 20261006
- paketlar: numpy 1.26.4, pandas 2.3.3, pyBKT 1.4.3, pykt 0.0.38, scipy 1.14.1, sklearn 1.6.1, torch 2.5.1+cpu

| Fayl | sha256 | Bayt |
|---|---|---|
| `junyi-exercise-table` | `13292cc2c809985abbacedaba434e39aeb02a7fcb2a32f17b60c4d3f4d769546` | 139957 |
| `junyi-problem-log` | `a7c99ede1f9b19648fdcd953b6ca0b0282bd31f2f913bd9d26b23aa9fcb36a25` | 2668566436 |

