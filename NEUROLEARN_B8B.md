# NeuroLearn — 8a tuzatishlari va 8b (eksperimentlar quvuri)

Bu fayl `NEUROLEARN_REMEDIATION.md` (8-bosqich) va `NEUROLEARN_B8_PLAN.md` (4-bo‘lim) ga qo‘shimcha. Ziddiyat bo‘lsa, shu fayl ustun.

Yangi qarorlar: D46–D53.

---

## 0. 8a qabul qilinadi

D42–D45 qabul qilinadi. Alohida to‘g‘ri deb topilganlar saqlanadi:
- `research_consent_at = NULL` bilan "hech qachon bermagan" va "bekor qilgan" holatlarini ajratish;
- psevdonim migratsiyasining uch qadami (unique ustun va callable default muammosi);
- admin rozilikni faqat o‘qiy olishi.

Ikki tuzatish kerak (8b dan oldin, bitta kichik commit).

### D46 — Hisob o‘chirilganda javoblar taqdiri rozilik matnida aytilsin

D11 bo‘yicha rozilik bergan talaba hisobini o‘chirsa, javoblari psevdonim bilan qoladi. Bu siyosat o‘zgarmaydi, lekin hozirgi rozilik matni buni aytmaydi. Talaba "hisobimni o‘chirsam, hammasi o‘chadi" deb o‘ylashi mumkin.

- Rozilik matniga oltinchi fakt qo‘shilsin: "Rozilik faol bo‘lgan holda hisobingizni o‘chirsangiz, javoblaringiz ism va emailsiz tadqiqot uchun saqlanib qoladi. Buni istamasangiz, avval rozilikni bekor qiling."
- Matnni ushlab turuvchi test shu satrni ham tekshirsin.
- Har ikki tilda (uz/en).

### D47 — Tekshiruv to‘plami tozalansin

Tekshiruv natijasi 683 passed / 11 failed. Bu sonning ichida 7.1 dan oldin ham bo‘lgan uchta eskirgan test bor (`test_v_b4_removing_the_version_row_makes_get_snapshot_serve_a_stale_kb`, `test_v_b6_the_cache_follows_the_version`, `test_v_b6_update_weight_on_a_missing_relation_is_not_a_kb_error`). Ular eski xatti-harakatni talab qiladi.

- Bu ish implementatorniki emas, mustaqil tekshiruvchiniki (alohida sessiya). Implementator `verification/` ga tegmaydi.
- Tekshiruvchi: 11 ta FAIL ning har biri uchun turini yozadi — `stale` (yangilanadi), `na-signal` (ataylab, bosqich yozilganda yopiladi), `real` (nosozlik).
- E guruhining rozilik va eksport qismi (V-E1…) hozir yozilsin, 8b ni kutmasin: email/ism/`user_id` eksportda yo‘qligi, rozilik bermagan talaba chiqmasligi, `review_repeat`/`seed`/`simulated`/`legacy` chiqmasligi, `--include-simulated` belgisi, psevdonimning id/emaildan hosil qilinmasligi, D46 matni. Eksperiment qismi 8b dan keyin.

---

## 1. 8b uchun asosiy qoida

### D48 — Natija faqat haqiqiy ishga tushirishdan

Bu bosqichning eng muhim qoidasi.

- `tables.md` faqat `metrics.json` dan avtomatik yasaladi. Qo‘lda yozilgan son bo‘lmaydi.
- Har bir natija qatorida: dataset fayllarining sha256, kod commit'i, seed, buyruq.
- Dataset yo‘q bo‘lsa (masalan, DBE-KT22 to‘liq fayllari), jadvalda shu qator **"ishga tushirilmagan — ma’lumot yo‘q"** deb chiqadi. Hech qachon taxminiy yoki maqoladan olingan son qo‘yilmaydi.
- Simulyatsiya natijalari alohida papkada, "simulated — dissertatsiya natijasi emas" belgisi bilan (D13).
- Test: `tables.md` dagi har bir son `metrics.json` da bor; sha256'siz natija yozilmaydi.

---

## 2. Ma’lumot manbalari

### D49 — Qaysi ma’lumot bor, qaysi yo‘q

Hammasi foydalanuvchi tomonidan `git clone` bilan olinadi. Skriptlar internetdan o‘zi yuklamaydi, yo‘lni argument sifatida oladi.

| Manba | Qayerdan | Nima | Holat |
|---|---|---|---|
| ASSISTments 2009–2010 skill builder (asl versiya) | `github.com/CAHLR/pyBKT-examples`, `data/as.csv` | javoblar, 123 skill | **bor** |
| DBE-KT22 grafi | `github.com/ai-for-edu/Evaluating-Large-Language-Models-with-Educational-Knowledge-Graphs-on-Prerequisite-Relationships`, `data/DBE-KT22/DBE-KT22.graphml` (CC BY 4.0) | faqat graf | **bor** |
| Junyi grafi | o‘sha repo, `data/Junyi/Junyi-Prerequisites.graphml` | faqat graf | **bor** |
| WDKG graflari (2 ta) | o‘sha repo, `data/WDKG/` | faqat graf | **bor** |
| DBE-KT22 to‘liq (javoblar bilan) | ADA, doi:10.26193/6DZWOH | javoblar + graf | **yo‘q** (kirish olinmadi) |
| Mahalliy eksport | `export_research_data` | javoblar + graf | rozilik yig‘ilgach |

Tekshirilgan ma’lumot (oracle sifatida ishlatiladi, networkx bilan hisoblangan):

`as.csv`:
- sha256 `f22e3fb7872c1784ce93b0f9ebabbe0cbcac4f896fd8b4a11667b9715d77dbdc` (repo commit `fc59290`);
- 525 534 qator, 4 217 talaba, 123 skill; `skill_id` bo‘sh qatorlar 66 326.

### D50 — ASSISTments 2009 ni tozalash

Asl versiyada takroriy qatorlar bor. Xiong va boshq. (EDM 2016) ularning DKT natijasini sun’iy oshirganini ko‘rsatgan (AUC 0,86 → takrorsiz 0,73–0,75). Shuning uchun tozalash qoidalari ochiq va qotirilgan:

1. `skill_id` bo‘sh qatorlar olib tashlanadi.
2. Takror: `(order_id, skill_id)` bo‘yicha birinchisi qoladi. **Faqat `order_id` bo‘yicha emas** — bir nechta skill'li savollar 2.2-bo‘limdagi qoida bo‘yicha har bir skill uchun alohida yozuv bo‘ladi.
3. Tartib: `user_id`, so‘ng `order_id`.
4. `original` bo‘yicha filtr bayroq bilan (`--original-only`), standart holatda yo‘q; ikkala variant ham `metadata` ga yoziladi.

Kutilgan sonlar (test):
- 1–3-qoidadan keyin: 338 001 qator, 4 163 talaba, 123 skill; 47 037 ta `order_id` bir nechta skill'ga ega;
- `--original-only` bilan: 312 232 qator, 4 163 talaba.

Bu sonlar mos kelmasa, quvur to‘xtaydi.

### D51 — Graf yuklovchi va yo‘nalish

- Umumiy yuklovchi: graphml yoki CSV (`src,dst`), `--edge-direction {prereq_to_dependent, dependent_to_prereq}`.
- Junyi: `prereq_to_dependent` (masalan, `recognizing_conic_sections → parabola_intuition_1`).
- DBE-KT22: yo‘nalish aralash (`DML → SELECT` umumiydan xususiyga, `ALTER TABLE → DDL` aksincha). Shuning uchun DBE-KT22 bo‘yicha har bir graf natijasi **ikkala yo‘nalishda** beriladi va bu metadata'da qayd etiladi.
- O‘z-o‘ziga qirralar Y2 buzilishi sifatida hisoblanadi, olib tashlanadi va soni yoziladi.

---

## 3. Nima ishga tushiriladi

### D52 — Graf tahlili (real graflarda, hozir)

`experiments/graph_report.py`. Kirish — graf fayli. Chiqish — har bir graf uchun:
- tugunlar, qirralar, o‘z-o‘ziga qirralar, izolyatsiyalangan tugunlar, kuchsiz bog‘langan komponentlar;
- Y3: sikl bormi, SCC'lar (bo‘lsa, birlashtirish natijasi);
- tranzitiv ortiqcha qirralar (soni va ro‘yxati);
- Kahn tartibi va `lev`, eng uzun yo‘l;
- inkremental tayyorlik yangilanishi: bitta javobdan keyin qayta hisoblangan tugunlar soni (|Succ(v)|) va vaqt, to‘liq qayta hisoblash bilan solishtirib (median, p95, 30 takror).

Kod `neuro_model/` dagi o‘sha funksiyalarni chaqiradi — alohida implementatsiya yozilmaydi.

Kutilgan qiymatlar (test, o‘z-o‘ziga qirralar olib tashlangandan keyin):

| Graf | Tugun | Qirra | O‘z-o‘ziga | DAG | Kuchsiz komp. | Ortiqcha | Eng uzun yo‘l |
|---|---|---|---|---|---|---|---|
| DBE-KT22 | 98 | 101 | 0 | ha | 8 | 9 | 5 |
| Junyi | 1004 | 740 (+2 o‘z-o‘ziga) | 2 | ha | — | 0 | 9 |
| WDKG-Course | 46 | 73 (+1 o‘z-o‘ziga) | 1 | ha | 3 | 12 | 6 |
| WDKG-KnowledgePoints | 121 | 285 | 0 | ha | 88 | 0 | 1 |

DBE-KT22 ortiqcha qirralari (oracle): `Transactions→ACID Properties`, `Database Security→Access Control`, `Role-Based Access Control (RBAC)→Access Control`, `Entity-Relationship Model→Data Model`, `Entity-Relationship Model→Entity`, `Discretionary access control (DAC)→REVOKE`, `Discretionary access control (DAC)→Specifying Privileges - Views`, `Participation constraints→Relationship`, `Superkey→Relational data model`.

Junyi'da 73 ta izolyatsiyalangan tugun bor (o‘z-o‘ziga qirralar olib tashlangandan keyin).

### D53 — H2 (ASSISTments 2009, hozir)

- Modellar: BKT, BKT+IRT (λ=0), Elo/Rasch, PFA — `neuro_model` orqali; DKT, AKT — pyKT orqali. BKT+IRT+Pre bu yerda **ishga tushirilmaydi** (grafi yo‘q) — jadvalda "graf yo‘q" deb chiqadi.
- pyBKT bilan 5 ta skill bo‘yicha o‘zaro tekshiruv.
- Ajratish, metrikalar, statistika — `NEUROLEARN_REMEDIATION.md` 8-bosqich bo‘yicha.
- Aqlga muvofiqlik chegarasi (test emas, ogohlantirish): takrorsiz ma’lumotda DKT AUC 0,70–0,80 oralig‘idan tashqarida chiqsa, `metadata` da ogohlantirish yoziladi va tozalash qayta tekshiriladi.
- `--quick` rejimi (500 talaba) CI uchun.

### H1 va H3 — kod tayyor, ishga tushirish ma’lumotga bog‘liq

`h1.py` va `h3.py` "javoblar + graf" juftligini qabul qiladi va hech qanday dataset'ga bog‘lanmaydi. Ular quyidagi juftliklardan biri bilan ishlaydi:
1. DBE-KT22 to‘liq fayllari (`--dbe-path`), agar keyinroq olinsa;
2. ASSISTments 2009 + o‘qituvchilar tuzgan graf (`--graph experiments/graphs/assist09_prereq.csv`), agar tuzilsa;
3. mahalliy eksport.

Hozir ulardan hech biri yo‘q. Shuning uchun:
- **DBE-KT22 yuklovchisi** CRKT repozitoriysidagi fayl nomlari bo‘yicha yoziladi (`Transaction.csv`, `Questions.csv`, `KCs.csv`, `Question_KC_Relationships.csv`, `KC_Relationships.csv`). Ustun nomlari haqiqiy fayl bilan tekshirilmagani uchun ular bitta joyda, `DBE_SCHEMA` lug‘atida yoziladi. Yuklovchi xuddi shu sxemadagi kichik sintetik fixture bilan test qilinadi. Fixture `tests/fixtures/dbe_schema_fixture/` da, README'da "sintetik, haqiqiy DBE-KT22 emas" deb yoziladi.
- **H1 ga qo‘shimcha qoida:** ASSISTments uchun skill builder'ning o‘z tugatish qoidasi — "ketma-ket 3 ta to‘g‘ri". U boshqa qoidalar (bajarilganlik, o‘tish bali) qatorida qo‘shiladi.
- **Graf nazoratlari** (H3 uchun, graf kelganda ishlaydi): asl graf, teskari graf, daraja taqsimoti saqlangan tasodifiy graf (`networkx.directed_edge_swap`, 20 seed), grafsiz (λ=0).
- **Annotatsiya vositasi:** `experiments/graphs/annotate.py`. Kirish — skill nomlari va nomzod qirralar CSV. Ikki annotator ustuni, Cohen κ, yakuniy graf (ikkalasi kelishgan qirralar) va uning sha256. Graf fayli eksperimentdan oldin commit qilinadi; `h3.py` sha256'si `metadata` dagi bilan mos kelmasa ishlamaydi. Nomzod qirralarni tashqi LLM taklif qilishi mumkin, unga faqat skill nomlari yuboriladi.
- Simulyatsiya bilan H1/H3 kodining o‘zi sinaladi (parametrlarni tiklash, prerekvizit ta’siri bor generatorda Pre ning ustunligi) — natija emas, D48.

---

## 4. Ish tartibi

1. **D46** — bir kichik commit.
2. **8b-1:** ma’lumot yuklovchilari (D49–D51), graf tahlili (D52). Commit. Hisobot: D52 jadvalining haqiqiy chiqishi.
3. **8b-2:** H2 (D53) — `--quick` va to‘liq ishga tushirish. Commit. Hisobot: `tables.md` ning o‘zi.
4. **8b-3:** H1/H3 kodi, DBE yuklovchisi, nazoratlar, annotatsiya vositasi — fixture va simulyatsiya testlari bilan. Commit.
5. Har bosqich oxirida: testlar, `REMEDIATION_PROGRESS.md`, `docs/THESIS_MAPPING.md`, qisqa hisobot. Tugagach to‘xta.

`docs/THESIS_MAPPING.md` ga yangi bo‘lim: har bir gipoteza → skript → natija fayli → holat (`ishga tushirilgan` / `kod tayyor, ma’lumot yo‘q`).

Mustaqil tekshiruvchi (alohida sessiya): D47, keyin 8b-1 va 8b-2 dan so‘ng E guruhining eksperiment qismi — D50 sonlari, D52 jadvali va D48 qoidasi (qo‘lda yozilgan son yo‘qligi).

Addendum 2.8 ning qolgan bandlari (hisobni o‘chirish va parolni almashtirish interfeysi) 10-bosqichga o‘tkaziladi.