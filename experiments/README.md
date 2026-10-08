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
| `splits.py` | 5 qism **talabalar bo'yicha**, har birida validatsiya ulushi | 8-bosqich |
| `metrics.py` | AUC, RMSE, aniqlik; dastlabki k ∈ {3, 5} alohida | 8-bosqich |
| `stats.py` | talabalar bo'yicha bootstrap, fast DeLong, Holm | 8-bosqich |
| `models/classical.py` | BKT, BKT+IRT (λ=0), BKT+IRT+Pre (bir kod, uch bayroq), Elo/Rasch, PFA | D53 |
| `models/neural.py` | DKT, AKT — pyKT ning arxitekturalari | D53 |
| `models/pybkt_check.py` | 5 mavzu bo'yicha pyBKT EM bilan o'zaro tekshiruv | D53 |
| `h2.py` | H2 ishga tushirish: `--quick` va to'liq | D53 |
| `h2_bounds.py` | H2 ning G_MAX/S_MAX ga sezgirligi: BKT va BKT+IRT (λ=0), uch sozlama | D55 |
| `reproduce.py` | ikki H2 natijasini solishtiradi: BKT, BKT+IRT, Elo/Rasch, PFA 1e-9 gacha teng bo'lishi kerak, DKT/AKT faqat ko'rsatiladi | muhit tiklanishi |
| `orders.py` | qator qaysi masalaga (`order_id`) tegishli; D57 bo'yicha bashorat faqat oldingi masalalardan | D57 |
| `default_coverage.py` | H2 natijasida standart BKT parametrlari bilan bashorat qilingan javoblar ulushi | D53 |

## Muhit

8b-1 (yuklovchilar va graf tahlili) standart kutubxona va `neuro_model` ustida
ishlaydi — Django venv'ida ham ishga tushadi. **8b-2 dan boshlab alohida
virtualenv kerak**: torch va pykt-toolkit ~1 GB va backend'ga keraksiz.

```sh
python -m venv experiments/.venv
experiments/.venv/bin/pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1
experiments/.venv/bin/pip install -r experiments/requirements.txt
```

`requirements.txt` da versiyalar natija olingan muhitdan o'qib yozilgan.
Ulardagi uchta pin tanlov emas, upstream nomuvofiqlik: pyBKT 1.4.3 numpy 2.x
bilan ham, scikit-learn ≥ 1.7 bilan ham ishlamaydi, shuning uchun numpy < 2
va unga mos scipy/pandas qotirilgan. Sabab fayl ichida yozilgan.

### Muhitni tiklash

Natijalar Python 3.12.3 da olingan (`.python-version`). Tizim Python'i boshqa
bo'lsa (masalan, Ubuntu 26.04 da 3.14), numpy 1.26.4, scipy 1.14.1,
scikit-learn 1.6.1 va torch 2.5.1 o'rnatilmaydi — ularning 3.14 uchun wheel'i
yo'q. Shuning uchun interpretator uv bilan olinadi, tizimnikiga tegilmaydi.
Ikkala venv `*.lock` fayllaridan quriladi: ularda har bir paket, tranzitivlari
ham, versiyasi va sha256'i bilan.

```sh
# 0. uv (tizimda bo'lmasa — istalgan vaqtinchalik venv'ga: python3 -m venv /tmp/uv && /tmp/uv/bin/pip install uv)
uv python install 3.12.3
PY=$(uv python find 3.12.3)

# 1. Django venv
$PY -m venv venv
venv/bin/pip install --require-hashes -r requirements.lock

# 2. Eksperiment venv (torch — CPU index'dan)
$PY -m venv experiments/.venv
experiments/.venv/bin/pip install --require-hashes \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    -r experiments/requirements.lock

# 3. Tekshiruv
venv/bin/pip check && experiments/.venv/bin/pip check
experiments/.venv/bin/python -m pytest experiments/tests -q -p no:cacheprovider
sha256sum experiments/data/assistments2009/as.csv experiments/data/kg/*.graphml   # data/README.md dagi qiymatlar bilan
```

Lock fayllar `pip freeze` dan `uv pip compile --generate-hashes` bilan
yasalgan va toza venv'ga `--require-hashes` bilan o'rnatilib, freeze bilan
solishtirilgan. `requirements.txt` fayllari to'g'ridan-to'g'ri pin'lar va
ularning sababi uchun qoladi; lock — ularning yopilishi.

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

### H2 — ASSISTments 2009 (D53)

```sh
# Avval quvurni sinash: 500 talaba, 3 epoch. Natija alohida papkada va
# "dissertatsiya natijasi emas" belgisi bilan.
experiments/.venv/bin/python -m experiments.h2 --quick

# To'liq ishga tushirish. DKT va AKT CPU'da sekin: 338 001 qator, 5 qism —
# bir necha soat ketishi mumkin.
experiments/.venv/bin/python -m experiments.h2

# Uzoq ishga tushirish — alohida systemd user unit'da (terminal yoki agent
# yopilsa ham, browser OOM'ga uchrasa ham o'lmaydi). Log: experiments/.runs/
experiments/run_h2.sh both
```

**D57 — masala darajasidagi baholash.** ASSISTments'da bir nechta skill'li
masala har skill uchun alohida qator, bir xil `correct` bilan va yonma-yon.
Shuning uchun har bir qator faqat talabaning oldingi masalalaridagi javoblardan
bashorat qilinadi; masalaning barcha qatorlari bir xil holatdan, yangilanish
masaladan keyin (`orders.py`; xulq testi — `tests/test_order_protocol.py`).
O'qitish o'zgarmaydi. `tables.md` §10 — masalaning faqat birinchi qatorlari
bo'yicha AUC (sezgirlik).

Ishga tushirish paytida ishchi daraxtga tegilmaydi (D54). Provenance git
holatini boshida va oxirida yozadi; boshida toza bo'lmasa yoki ikkalasi farq
qilsa, `tables.md` ning eng yuqorisida ogohlantirish chiqadi.

Oltita model: BKT, BKT+IRT (λ=0), Elo/Rasch, PFA, DKT, AKT. **BKT+IRT+Pre
ishga tushirilmaydi** — ASSISTments'da prerekvizit grafi yo'q, shuning uchun
jadvalda "graf yo'q" deb chiqadi, tashlab ketilmaydi (D48).

Birinchi uchtasi — bitta kod, uch xil bayroq
(`models/classical.py::BKTFamily`), ya'ni baholanadigan model prototipda
ishlaydigan modelning o'zi.

### Chegaralar sezgirligi (D55)

```sh
experiments/.venv/bin/python -m experiments.h2_bounds --quick
experiments/run_h2.sh bounds-both     # quick, keyin to'liq; log: experiments/.runs/h2-bounds-*.log
```

Faqat BKT va BKT+IRT (λ=0), uch sozlama: (0,30; 0,10) — II bob, asosiy natija;
(0,40; 0,20) va (0,49; 0,30) — faqat eksperiment parametri. Platformaning
konstantalari o'zgarmaydi. Grid har sozlamada chegaraga nisbatan quriladi
(asosiysida H2 ning grid'i aynan), va fold'lar moslanishidan oldin 5 ta eng
ko'p javobli mavzuda L-BFGS-B bilan solishtiriladi: nisbiy farq 1 % dan oshsa,
ishga tushirish hech narsa yozmasdan to'xtaydi (chiqish kodi 3). Grid search'lar
(sozlama × fold) parallel jarayonlarda (`--workers`); natija bunga bog'liq emas.

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
| H2: ASSISTments 2009 da BKT, BKT+IRT, Elo/Rasch, PFA, DKT, AKT (D53) | 8b-2 | bajarildi |
| H1/H3 kodi, DBE yuklovchisi, graf nazoratlari, annotatsiya vositasi | 8b-3 | kutilmoqda |

## Testlar qaysi muhitda

| Fayl | Django venv | `experiments/.venv` |
|---|---|---|
| `test_tables.py`, `test_graphs.py`, `test_graph_report.py`, `test_assist09.py`, `test_splits.py` | ishlaydi | ishlaydi |
| `test_metrics_stats.py` | numpy yo'qligi uchun skip | ishlaydi |
| `test_models.py` | sklearn/torch yo'qligi uchun qisman skip | ishlaydi |

Ildiz `conftest.py` Django'ning fixture'larini faqat Django o'rnatilgan
muhitda qo'llaydi, shuning uchun bir xil test fayllari ikki muhitda ham
ishlaydi.
