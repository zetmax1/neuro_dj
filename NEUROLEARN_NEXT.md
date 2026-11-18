# NeuroLearn — keyingi sessiyalar uchun buyruqlar

Ikkita alohida sessiya uchun ikkita prompt. Ularni **bir vaqtda bitta implementator** ishlaydigan qilib bering: 1-prompt — implementator, 2-prompt — mustaqil tekshiruvchi (faqat `verification/` ga yozadi).

---

## 1-prompt — implementator (yangi Claude Code sessiyasi)

```
Sen NeuroLearn loyihasida ishlayapsan (Django + DRF + React, branch thesis-model). Bu davom etayotgan ish; oldingi sessiyalar to'xtagan joydan davom etasan.

Avval o'qi, keyin boshqa hech narsa qilma:
1. NEUROLEARN_REMEDIATION.md — 1-bo'lim (ish qoidalari), 3-bo'lim (model), 8-bosqich.
2. NEUROLEARN_B8_PLAN.md — 4-bo'lim.
3. NEUROLEARN_B8B.md — D46–D53 (8b ning asosiy hujjati).
4. REMEDIATION_PROGRESS.md va docs/THESIS_MAPPING.md — joriy holat.
5. git log --oneline -15 va experiments/README.md.

Joriy holat (tekshir, ishonma):
- 8b-1 bajarilgan. 8b-2 kodi bajarilgan, grid kengaytirilgan (P0 0,90 gacha, G0 0,29, S0 0,097).
- To'liq H2 ishga tushirish experiments/run_h2.sh both orqali 1eeca40 commit'ida ajratilgan holda boshlangan. Log: experiments/.runs/h2-*.log. Natija: experiments/results/assist09*/.

Qo'shimcha qoidalar (D54):
- Bu branch'da bir vaqtda faqat bitta implementator sessiyasi ishlaydi. Boshqa sessiyaning commit qilinmagan o'zgarishini ko'rsang — tegma, to'xta va menga ayt.
- git commit --amend, rebase, reset --hard — taqiqlangan, push qilinmagan commit'lar uchun ham. Xato commit xabari keyingi commit'da tuzatiladi. (c142506 da amend qilingan — buni REMEDIATION_PROGRESS.md ga bir qator bilan qayd et, tarixni o'zgartirma.)
- provenance git holatini ishga tushirish BOSHIDA ham, OXIRIDA ham yozsin; ikkalasi farq qilsa yoki daraxt boshida "dirty" bo'lsa, metadata va tables.md da ochiq belgilansin. Uzoq ishga tushirish paytida ishchi daraxtga tegilmaydi.

Vazifa 1 — H2 to'liq natijasi.
- Ishga tushirish holatini tekshir (pgrep, log). Tugamagan bo'lsa, Monitor bilan kut; to'xtagan yoki yiqilgan bo'lsa, sababini top, tuzat, test qo'sh, toza commit'dan qayta boshla.
- Tugagach menga quyidagilarni ber, izohsiz va tanlamasdan:
  a) to'liq tables.md (barcha bo'limlar);
  b) DKT AUC va D53 oralig'i (0,70–0,80), Xiong 2016 (0,73–0,75) bilan;
  c) BKT+IRT (λ=0) va BKT farqi: AUC, 95% CI, DeLong p va Holm p;
  d) grid_check: har bir parametr bo'yicha chegarada qolgan mavzular soni va foizi; standart parametrlarni saqlagan mavzular soni va ular qamragan javoblar ulushi;
  e) ishga tushirish vaqti va provenance (commit, dirty holati).
- Natija qanday chiqsa ham kodni "yaxshilash" uchun o'zgartirma. Natijadagi gap bo'lsa — menga ayt.

Vazifa 2 — D55: chegaralar sezgirligi (H2 natijasidan keyin, alohida commit).
To'liq ma'lumotda G0 taxminan 78% va S0 88% mavzularda II bob chegarasiga tiralgan. II bob qarori (G_MAX = 0,30, S_MAX = 0,10) O'ZGARMAYDI va asosiy natija shu bilan qoladi. Lekin xulosa chegaralarga qanchalik bog'liqligi ko'rsatilishi kerak.
- experiments/h2_bounds.py: faqat BKT va BKT+IRT (λ=0), uchta sozlama: (0,30; 0,10) asosiy, (0,40; 0,20), (0,49; 0,30). Hammasida G_MAX < 0,5 va G_MAX + S_MAX < 1.
- Grid har sozlamada chegaraga nisbatan quriladi (yuqori G0/S0 chegaraning ~97%), va o'sha 5 mavzuda L-BFGS-B bilan farq < 1% ekani avtomatik tekshiriladi; bo'lmasa ishga tushirish to'xtaydi.
- Bir xil split va seed'lar. Bootstrap 200 replikat (metadata'da yozilsin).
- Chiqish: har sozlama uchun AUC [CI], RMSE, umumiy log-likelihood, chegarada qolgan mavzular foizi, BKT+IRT − BKT farqi. tables.md D48 qoidasi bilan.
- neuro_model va Django sozlamalaridagi konstantalar o'zgarmaydi; sezgirlik faqat eksperiment parametri.

Vazifa 3 — 8b-3 (NEUROLEARN_B8B.md 3-bo'limi, "H1 va H3" qismi).
- h1.py va h3.py — "javoblar + graf" juftligi bo'yicha, datasetga bog'lanmagan.
- H1 qoidalari: ehtimoliy (r ≥ τ), bajarilganlik, o'tish bali va ASSISTments uchun "ketma-ket 3 ta to'g'ri". τ/δ sezgirligi shu yerda (τ ∈ {0,70; 0,80; 0,90; 0,95}, δ ∈ {0,05; 0,10; 0,15}).
- H3: asl graf, teskari graf, daraja taqsimoti saqlangan tasodifiy graf (networkx.directed_edge_swap, 20 seed), grafsiz (λ=0). Dastlabki k ∈ {3, 5} urinish bo'yicha AUC.
- DBE-KT22 yuklovchisi: DBE_SCHEMA lug'ati, sintetik fixture (README'da "sintetik, haqiqiy DBE-KT22 emas"). Fayl yo'q bo'lsa — "ishga tushirilmagan".
- experiments/graphs/annotate.py: ikki annotator ustuni, Cohen κ, yakuniy graf va sha256; h3.py sha256 mos kelmasa ishlamaydi. Bitta annotator bo'lsa κ o'rniga "hisoblanmadi — bitta annotator" yoziladi.
- Simulyatsiya faqat kodni sinash uchun: parametrlarni tiklash, prerekvizit ta'siri bor generatorda Pre ning ustunligi. Natijalar "simulated — dissertatsiya natijasi emas" belgisi bilan alohida papkada (D13, D48).
- Hozir haqiqiy H1/H3 ma'lumoti yo'q. Shuning uchun jadvallarda ular "kod tayyor, ma'lumot yo'q" holatida chiqadi. Bu to'g'ri natija — uni simulyatsiya sonlari bilan to'ldirma.
- Har bir jadvalning har bir shartli bloki uchun test (1eeca40 dagi saboq).

Ish tartibi: Vazifa 1 → hisobot → to'xta. Men "davom" desam: Vazifa 2 → hisobot → to'xta. Keyin Vazifa 3 → hisobot → to'xta.
Har vazifa oxirida: testlar (experiments/.venv va Django venv), REMEDIATION_PROGRESS.md, docs/THESIS_MAPPING.md (gipoteza → skript → natija fayli → holat), commit, qisqa hisobot o'zbek tilida.
verification/ ga tegma.
```

---

## 2-prompt — mustaqil tekshiruvchi (alohida sessiya, implementator bilan parallel bo'lishi mumkin)

```
Sen NeuroLearn loyihasining mustaqil tekshiruvchisisan. Implementator kodini o'zgartirmaysan: faqat verification/ papkasiga yozasan va hisobot berasan. Implementator sessiyasi parallel ishlayotgan bo'lishi mumkin — uning fayllariga, experiments/.runs/ ga va ishlab turgan jarayonlarga tegma; commit qilishdan oldin git status da faqat verification/ dagi fayllar borligini tekshir.

O'qi: NEUROLEARN_VERIFICATION.md, NEUROLEARN_B8B.md (D46–D53, ayniqsa D47), REMEDIATION_PROGRESS.md, verification/ dagi mavjud testlar va VERIFICATION_REPORT.md.

Vazifa 1 — D47: verification/tests ni ishga tushir. Har bir FAIL uchun turini yoz:
- stale — test eski, endi to'g'ri bo'lgan xatti-harakatni talab qiladi (masalan, test_v_b4_removing_the_version_row_makes_get_snapshot_serve_a_stale_kb, test_v_b6_the_cache_follows_the_version, test_v_b6_update_weight_on_a_missing_relation_is_not_a_kb_error). Ularni yangi xatti-harakatga moslab qayta yoz va nima uchun o'zgargani docstring'da bo'lsin.
- na-signal — test_na.py ning ataylab qo'yilgan signali. Tegishli guruh yozilganda yopiladi.
- real — haqiqiy nosozlik. Tuzatma: hisobotga yoz, qayta ishlab chiqarish qadamlari bilan.

Vazifa 2 — E guruhining rozilik va eksport qismi (V-E1…), mustaqil, implementator testlariga qaramasdan:
- eksport fayllarida email, ism, user_id yo'q (barcha to'rt faylda, metadata.json ham);
- rozilik bermagan va rozilikni bekor qilgan talaba chiqmaydi;
- review_repeat, seed, simulated, legacy qatorlari chiqmaydi; arxivlangan mavzu chiqmaydi;
- --include-simulated uch joyda belgilangan (ogohlantirish, thesis_result: false, papka nomi);
- psevdonim id/email'dan hosil qilinmagan va API javoblarida chiqmaydi;
- admin boshqa foydalanuvchi rozilikni o'zgartira olmaydi;
- D46: rozilik matnida hisob o'chirilganda javoblar saqlanishi aytilgan (uz va en);
- D11: 30 kundan keyin hard-delete — rozilik bor/yo'q ikkala holat.

Vazifa 3 — E guruhining eksperiment qismi (8b-1 va 8b-2 uchun):
- D50 sonlari: 525 534 → 338 001 qator, 4 163 talaba, 123 skill, 47 037 ko'p-skill'li order_id, --original-only 312 232 (ma'lumot bo'lmasa skip, jim o'tmasin);
- D52 graf jadvali networkx oracle bilan (DBE-KT22 ning 9 ta ortiqcha qirrasi nomi bilan);
- D48: experiments/results/ dagi har bir tables.md da metrics.json da yo'q son yo'q; har bir natijada sha256 va commit bor;
- split talabalar bo'yicha: bitta talaba ikki qismda uchramaydi;
- DKT/AKT oqim testi mustaqil qayta yozilgan.

test_na.py dagi E guruhi signalini faqat tegishli testlar yozilgach yop.
Oxirida: VERIFICATION_REPORT.md ga yangi bo'lim (PASS/FAIL jadvali, stale/na-signal/real bo'yicha), commit (faqat verification/), qisqa hisobot o'zbek tilida.
```