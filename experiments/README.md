# experiments — dissertatsiyaning eksperimentlari (8b-bosqich)

Bu paket ikki qoida ustiga qurilgan. Ular bir-biriga yaqin, lekin har xil
narsadan saqlaydi.

**D48 — natija faqat haqiqiy ishga tushirishdan.** `tables.md` faqat
`metrics.json` dan yasaladi. Undagi har bir son — `metrics.json` da allaqachon
turgan skalyar: bu yerda hisoblanmaydi, boshqa sondan yaxlitlanmaydi,
maqoladan eslanmaydi. Har bir natija o'zi hisoblangan fayllarning sha256'si,
kod commit'i, seed va buyruq bilan birga yoziladi. Ma'lumoti yo'q to'plam
uchun qator **"ishga tushirilmagan — ma'lumot yo'q"** deb chiqadi.

Bu tekshiruv kod sifatida yozilgan (`experiments/tables.py`, `verify`) va test
bilan ushlanadi (`tests/test_tables.py`). U oldini oladigan nosozlik — xato
emas, jim turganidir: jadvalga hech qachon mashinada bo'lmagan to'plam uchun
ishonarli son kirib qolishi, yoki ishga tushirishdan keyin sonning
"to'g'rilanishi".

**D49 — hech narsa yuklab olinmaydi.** Har bir yuklovchi yo'lni argument
sifatida oladi. Ma'lumotni foydalanuvchi qo'lda oladi —
[`data/README.md`](data/README.md) da buyruqlar va sha256'lar bor.

II bobning hisob-kitoblari bu yerda **qayta yozilmaydi**: `graph_report`
`neuro_model.graph` va `neuro_model.readiness` ni chaqiradi, ya'ni o'lchanadigan
narsa — platformaning o'zi ishlatadigan kod (D52). II bobda ta'rifi yo'q
statistika — kuchsiz va kuchli bog'langan komponentlar — `components.py` da
turadi va networkx bilan tekshiriladi. networkx faqat testda ishlatiladi:
tekshirilayotgan kod bilan implementatsiyani bo'lishadigan oracle hech narsani
isbotlamaydi.

## Hozir nima bor

| Fayl | Nima qiladi | Qaror |
|---|---|---|
| `provenance.py` | sha256, commit, seed, buyruq, `env.txt`, natijalar papkasi | D48 |
| `tables.py` | `metrics.json` → `tables.md`, va `verify` | D48 |
| `components.py` | kuchsiz/kuchli bog'langan komponentlar, kondensatsiya | D52 |
| `datasets/assist09.py` | ASSISTments 2009 tozalash qoidalari va kutilgan sonlar | D50 |
| `datasets/graphs.py` | GraphML / CSV graf yuklovchisi, yo'nalish argument sifatida | D51 |
| `graph_report.py` | graf tahlili: o'lcham, Y3, ortiqcha qirralar, `lev`, tayyorlik benchmarki | D52 |

## Ishga tushirish

```sh
# To'rtta nashr etilgan graf (data/README.md bo'yicha joylashtirilgan)
venv/bin/python -m experiments.graph_report

# Bitta graf, yo'nalishi ko'rsatilgan holda
venv/bin/python -m experiments.graph_report \
    --graph experiments/data/kg/Junyi-Prerequisites.graphml \
    --edge-direction prereq_to_dependent

# Ikkala yo'nalishda (DBE-KT22 uchun standart, D51)
venv/bin/python -m experiments.graph_report --graph <fayl> --both-directions
```

Natija `experiments/results/graphs/<timestamp>/` ga yoziladi: `metrics.json`,
`tables.md`, `env.txt`.

## Testlar

```sh
venv/bin/python -m pytest experiments/tests -q                   # sintetik
NEUROLEARN_DATA=<yo'l> venv/bin/python -m pytest experiments/tests -q   # + haqiqiy
```

Sintetik testlar hamma joyda ishlaydi. Haqiqiy ma'lumot testlari D49, D50 va
D52 belgilagan sonlarni tasdiqlaydi va ma'lumot yo'q bo'lsa **skip** qiladi —
jim o'tmaydi. Fixture'lar `tests/fixtures/` da va hammasi sintetik; ulardan
hisoblangan son dissertatsiyaga kirmaydi.

Vaqt o'lchovlari testda tasdiqlanmaydi: ular mashinaga bog'liq. Tasdiqlanadigan
narsa — inkremental yo'l `|Succ(v)|` tugunni ko'radi, to'liq qayta hisoblash
hammasini.

## Keyingi qadamlar

| Ish | Bosqich | Holat |
|---|---|---|
| Yuklovchilar (D49–D51), graf tahlili (D52) | 8b-1 | bajarildi |
| H2: ASSISTments 2009 da BKT, BKT+IRT, Elo/Rasch, PFA, DKT, AKT (D53) | 8b-2 | kutilmoqda |
| H1/H3 kodi, DBE yuklovchisi, graf nazoratlari, annotatsiya vositasi | 8b-3 | kutilmoqda |

`requirements.txt` 8b-2 dan boshlab kerak bo'ladigan paketlarni sanaydi
(pandas, scikit-learn, pyKT, torch CPU); 8b-1 ularning hech biriga bog'liq
emas.
