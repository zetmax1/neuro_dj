# verification/REPORT.md — yakuniy mustaqil tekshiruv, 2026-10-20

Tekshiruvchi sessiyasi (D54). Faqat `verification/` ga yozildi; implementatsiya
kodi, `experiments/`, `benchmarks/`, `docs/`, `REMEDIATION_*.md` ga tegilmadi;
`config/.env` va ildiz `.env` ochilmadi. Postgres buyruqlari `scripts/dj5433.sh`
orqali (DSN konteynerdan, env fayl o‘qilmaydi).

**Boshlang‘ich holat (0-qadam).** `systemctl --user list-units 'neurolearn-*'` →
`0 loaded units`; daraxt toza; `git log -5`: `740bb20` (QADAM 14), `4c44557`
(D70 kodi), `d894577` (D70 qarori), `9f940a1` (QADAM 13), `f7626ae`
(REMEDIATION_REPORT). Branch `thesis-model`.

Oldingi hisobot (2026-10-12, `e97261e`) shu fayl tarixida qoladi; bu versiya
uni almashtiradi.

## 1. Testlar (o‘lchangan sonlar)

| Suite | Muhit | Oldin (`740bb20`, tekshiruvchi o‘zgarishlaridan oldin) | Keyin |
|---|---|---|---|
| `verification/tests` | `venv` (Django 6.0.5), compose Postgres 5433, `--ds=verification.settings` | 824 passed, **6 failed, 1 error** (2 daq 46 s) | **936 passed, 1 failed, 1 xfailed** (6 daq 44 s) — 107 yangi test; FAIL — N-1 (V-E3, haqiqiy nuqson), xfail — N-2 (strict) |
| `verification/neural` | `experiments/.venv` (torch 2.5.1+cpu, pykt 0.0.38) | — | **62 passed, 3 skipped** (skip'lar — D57 izolyatsiyasi populyatsiya parametrli 3 model uchun ataylab, oldingi K-2) |
| Backend (`scripts/dj5433.sh venv/bin/python -m pytest`, `experiments/tests` va `benchmarks/tests` ichida) | `venv` | — | **1 289 passed, 51 skipped**, 13 subtests, 0 failed (9 daq 43 s) — QADAM 14 bilan aynan |
| `experiments/tests` | `experiments/.venv` | — | **409 passed, 2 skipped** (pytest: 10 daq 35 s; skip — Django tomoni bu venv'da yo‘q) |
| `benchmarks/tests` | `venv` | — | **90 passed** (27 s) |
| THESIS_MAPPING nomlagan 17 test fayli | `venv` | — | **637 passed**, 13 subtests (3 daq 12 s) |
| `report_values --check` | ikkala venv | — | 177 son, 9 bo‘lim, **0 farq**, rc = 0 |
| `run_tree_benchmark --quick` (o‘zim) | verification benchmark test bazasi | — | rc = 0, 3 daq 47 s (3 (b)) |
| `run_all --dataset junyi --quick` (o‘zim, `740bb20` ning toza kloni, `--workers 2`) | `experiments/.venv`, `NEUROLEARN_DATA` | — | rc = 0; h1 va h3 natijalari ikkala uchida toza provenance, `tables.verify` va pozitsion tekshiruv = []. Devor vaqti 165 daq — mashina shu orada band/uxlagan (bir vaqtda yugurgan experiments suite'ning devor vaqti 150 daq, pytest'ning o‘zi 10,6 daq dedi); implementatorning 18 daqiqasi bilan solishtirib bo‘lmaydi |

Seed: `verification.settings.VERIFICATION_SEED` = 20261003 (har case uchun
`SEED + offset`). `verification/tests` xdist'siz, `-p no:cacheprovider`.

## 2. `verification/` dagi xatolar — sabab va qaror

| # | Test | Sabab | Qaror |
|---|---|---|---|
| 1–3 | `test_na.py::test_pending_stages[8]`, `[9]`, `[10]` | N/A signali: 8, 9, 10-bosqichlar “Bajarildi” | **Yopildi.** `test_implemented_stages` endi 0–10 ni kuzatadi (8–10 katagida izoh bor, shuning uchun holat — birinchi so‘z); yangi `test_no_stage_is_pending`: jadvalda aynan 0–10 bosqich va hech birida “Kutilmoqda” yo‘q |
| 4 | `test_na.py::test_na_group_e_pipeline_run_all_is_not_implemented` | N/A signali: `run_all.py` paydo bo‘ldi | **V-E4 yozildi** — `test_e4_run_all.py` (10 test, 3-bo‘lim); signal o‘rnida “E guruhi yozilgan” testi |
| 5 | `test_na.py::test_na_group_h_benchmark_command_is_not_implemented` | N/A signali: `run_tree_benchmark` bor | **V-H1 va H4 yozildi** — `test_h_tree_benchmark.py`; signal o‘rnida “H guruhi yozilgan” testi |
| 6 | `test_e_experiments.py::test_d48_every_result_has_sha256_commit_seed_and_command` | Mezon ziddiyati: `tree-benchmark/*` (4) va `tree-benchmark-quick` da `sources` bo‘sh — kirish fayli yo‘q, daraxt generatsiya qilinadi | **Mezon aniqlandi.** Generatsiya qilingan natija (`report == tree_benchmark` yoki Locust) uchun sha256 o‘rniga **generator, seed va parametrlar** talab qilinadi: daraxt uchun `settings` (shakllar, hajmlar, takrorlar, timeout, parallel, seed), `seeds.trees == settings.seed`, buyruqda `--seed`, `benchmarks/generator.py` run commit'ida mavjud, har o‘lchangan (shakl, hajm) uchun `trees[]` yozuvi; generator run commit'idan beri o‘zgarmagani uchun **18 daraxtning har birining sha256'i (shakl, hajm, seed) dan qayta hosil qilindi va mos keldi**. Locust uchun `run` parametrlari, `seeds.seed_load_test`, generator fayllari `sources` da. `sources` dagi kod fayli endi bugungi fayl bilan emas, **run commit'idagi blob** bilan solishtiriladi (data fayli — avvalgidek). Har commit `git cat-file` bilan tekshiriladi. Yangi `test_d48_the_generated_criterion_still_catches_a_missing_seed_or_parameter`: seed, parametr, daraxt yozuvi yoki digest buzilsa — yiqiladi |
| 7 | `test_b2_rejections.py::test_v_b2_adding_a_topic_that_closes_a_cycle_is_rejected` (ERROR, setup) | Fixture bo‘sh bo‘limlar halqasi A → B → C → A ga tayangan — D70 aynan shuni taqiqlaydi | **Fixture almashtirildi**: A → B, B → C va c1 → A (c1 — C ning mavzusi). G = (N, E_P) siklsiz, shuning uchun D70 qabul qiladi; b1 qo‘shilgach E_L = {b1 → c1}; a1 qo‘shish G_L da a1 → b1 → c1 → a1 ni yopadi → `cycle`, versiya, tugunlar va relatsiyalar o‘zgarmaydi. Maqsad saqlandi. Qo‘shimcha test: eski halqaning uchinchi relatsiyasi endi `cycle` bilan rad etiladi |

Shuningdek `test_na_group_f_performance_is_still_unmeasured` (o‘tib turgan, lekin
eskirgan signal) — V-F1/V-F2 endi o‘lchandi (`test_f_performance.py`), signal
“F guruhi yozilgan” testiga almashtirildi.

`verification/settings.py` ga `benchmark` alias qo‘shildi: test bazasi
`neurolearn_verify_bench` (benchmark bazasining o‘zi ochilmaydi).

## 3. Mustaqil tekshiruvlar

Hammasi tekshiruvchining o‘z kodi: implementatsiya testlari ishlatilmadi;
implementatsiya funksiyalari faqat **tekshiriladigan obyekt** sifatida chaqirildi.

### (a) H1/H3, Junyi — `test_e_junyi_h1_h3.py` (16 test, hammasi PASS)

| Tekshiruv | Natija |
|---|---|
| D61 yo‘nalishi: mashqlar CSV'si `csv` bilan o‘qildi (fayl BOM bilan boshlanadi); A qatorida B ⇒ B ∈ Pre(A) (SCC birlashtirilgandan keyin) | ≥ 970 qirra, hammasi mos |
| D62-5/6: real grafning bo‘lagi (Pre(w) = 2 ta, SCC'dan tashqari) + 6 talabali sintetik log. Voqea, `answered_prerequisites`, prerekvizit aniqligi, `proficient_prerequisites`, `correct_after`, `failed(k)` (k = 1, 3, 5) oddiy sikl bilan qo‘lda; prerekvizit P(L) — `verification/oracle/model.observe` bilan qayta o‘ynab (θ talaba bo‘yicha, b va n savol bo‘yicha talabalararo) | Hammasi `h1.collect_events` bilan mos; P(L) 1e-9 da. Holatlar: w ga prerekvizitdan oldin kelgan talaba — voqea yo‘q; k = 3 da muvaffaqiyatsiz, k = 5 da emas (ulush aynan 0,5); javobsiz prerekvizit P(L) = 0 ⇒ r = min = 0 |
| D62a(c) perturbatsiya: voqea qatori va undan keyingi barcha qatorlarda `earned_proficiency` teskari qilindi | Hech bir voqea o‘zgarmadi; oldingi qatordagi bayroq olib tashlansa — bittaga kamaydi |
| D62-11: `randomise` (seed 20261006 va +13) | 976 qirra, takroriy qirra va o‘z-o‘ziga qirra yo‘q, **har tugunning kirish/chiqish darajasi** (o‘zim sanadim) saqlangan, qirralarning > 50 % i almashgan, bir xil seed — bir xil graf |
| Commit qilingan H3: 20 tasodifiy arm | seed'lar 20261006…20261025, hammasida `degree_preserved`, `distinct_from_original`, 9 760 / 9 760 almashtirish |
| Teskari graf | qirralar to‘plami aynan aylantirilgan, darajalar (kirish ↔ chiqish) almashgan; `arms()` tartibi asl, teskari, tasodifiy…, grafsiz; ω = 1 |
| Natija papkalari | `tables.verify` = [], `verify_h1_positions` / `verify_h3_positions` = []; H1 §2 dan va H3 §5 dan tasodifiy 5 tadan qiymat o‘z (qoida/arm, ustun) katagida; `code_commit`, `git_start`, `git_end` tarixda (`2500c77`) |
| D64: H3 ogohlantirishi | ikkala uchidagi yagona o‘zgarish `?? experiments/results/junyi-h1/`; H1 ikkala uchida toza |
| D64 `split_changes` | faqat `??` + `experiments/results/` ajratiladi; `M` natija fayli, `A` natija, `experiments/resultsX/`, kod fayli — dirty. Vaqtinchalik git repo'da: untracked natija ⇒ `dirty = False`; commit qilingan natijani tahrirlash yoki begona `.py` ⇒ `dirty = True` |

### (a′) V-E4 va V-E3 — `test_e4_run_all.py` (10 test, PASS), `test_e_consent_export.py`

- **V-E4.** `run_all.plan`: assist09 → faqat h2 (h1, h3 sabab bilan
  “ishga tushirilmadi”), junyi → h1 va h3 (h2 sabab bilan); `--dry-run` hech
  qanday natija papkasi yaratmaydi; noma’lum dataset/model/gipoteza → rc 2.
  Har gipotezaning `main` i spy bilan almashtirildi: `--quick` va `--workers`
  har ishga tushadigan gipotezaga, `--models` h2 ga uzatiladi; h1 rc ≠ 0
  bo‘lsa h3 ishga tushmaydi. Commit qilingan quick natijalari (h1, h2, h3):
  `quick = true`, `thesis_result = false`, jadvalda “`--quick` ishga tushirish —
  dissertatsiya natijasi emas”, buyruqda `--quick`, git'da kuzatiladi,
  `tables.verify` = []. Spetsifikatsiyadagi “simulyatsiya ma’lumotida” o‘rniga
  haqiqiy ma’lumot (D48) — 6-bo‘lim, 15-band; parametr tiklash testi
  `neuro_model/tests/test_calibrate.py` da bor. Junyi quick o‘zim yugurtirdim
  (1-bo‘lim).
- **V-E3.** Qatorlar soni (metadata = CSV = pyKT bloklari) avvaldan o‘tadi;
  **pyKT'ning o‘z o‘quvchisi bilan o‘qish — FAIL** (N-1).

### (b) H4 — `test_h_tree_benchmark.py` (23 test + 1 strict xfail)

| Tekshiruv | Natija |
|---|---|
| Mutatsiya (benchmark test bazasida, 60 tugunli tasodifiy daraxt): teskari oraliq, ota oralig‘idan tashqari, bo‘shliq (ildiz `rght` ↑), noto‘g‘ri `level`, takroriy chegara — har biri `rebuild()` yo‘li **va** qayta hisoblash yo‘li bilan | 10/10 ushlandi, har biri o‘z bayrog‘i bilan |
| Y1: bobo nevaraning farzandi qilinadi (3-sikl); ikkinchi ildiz — ikkala usulda | 4/4 ushlandi |
| D63g: kichik pk'li tugun `move_to(target, "last-child")` bilan ko‘chirildi | Ikkala yo‘lda `passed`, `differs_from_rebuild = 0`; **shu holatning o‘zida** eski (pk tartibli) qayta hisoblash farq ko‘rsatadi — tekshiruv bo‘sh emas |
| ρ va CI qo‘lda | MPTT = 2·CTE (juftlangan) ⇒ ρ = 2, CI [2; 2], “CTE tezroq”; 0,5 ⇒ “MPTT tezroq”; teng ⇒ “taqqoslanadigan”; mediana (1,2,3,4,100)/(1…) = 3; uzunlik teng emas ⇒ son yo‘q, “hisoblanmadi”; p95 (1…20) = 19,05. O‘z juftlangan bootstrap'im (boshqa RNG, 4 000 replika) bilan CI chegaralari 5 % ichida |
| ρ xom `measurements.csv` dan qayta hisoblandi | birinchi pass'ning 51 ta va `050428` ning 3 ta o‘lchangan katagida mediana va ρ `metrics.json` ga mos (CSV 1e-6 ga yaxlitlangani hisobga olindi) |
| Son chiqmagan kataklar | `deep_chain/100000`: birinchi pass'da 2 × “ishga tushirilmadi — xotira” + 1 × timeout, qayta o‘lchashda 3 × timeout — `metrics.json` da ρ yo‘q, CSV'da vaqt yo‘q (faqat holat), jadvalda xulosa matni |
| D63h birlashtirish (o‘zim qurdim) | 54 katak: yozishda “CTE tezroq” emas — **6**, o‘qishda 1,5× dan sekin — **16**, son yo‘q — **3**; `deep_chain/100000` o‘chirish — “taqqoslanadigan” (0,922); qayta o‘tkazilgan 72 parallel bosqich: qulfli 18/18 toza (ikkala usul), qulfsiz MPTT oraliqlari 27/27 buzilgan, qulfsiz CTE Y1 — 1/27 (`course_like/1000` ×8). REMEDIATION_REPORT §6 va QADAM 11 bilan aynan mos |
| V-H1, commit qilingan `--quick` | har shakl × amal × usul CSV'da; har katakda mediana, p95, `queries_median`, `rows_touched_median` (metrics.json'da); parallel yaxlitlik ikkala usul uchun |
| V-H1, **o‘zim ishga tushirdim**: `run_tree_benchmark --quick` (verification'ning benchmark test bazasida, `--out` tmp, `--no-checkpoint`) | rc = 0 (3 daq 47 s); `metrics.json`, `measurements.csv`, `tables.md`, `env.txt` yozildi; `tables.verify` va `verify_tree_benchmark_positions` = []; har shakl × 6 amal × 2 usul CSV'da, har katakda p95 > 0 va so‘rovlar ≥ 1; parallel qulfsiz bosqich ikkala usulda, har birida yaxlitlik natijasi |

### (c) D66a — `test_f_performance.py` (7 test, PASS)

| Tekshiruv | Natija |
|---|---|
| `submit_answer` SQL soni, mustaqil o‘lchov: 4-bo‘lim kursi, haqiqiy JWT, haqiqiy tranzaksiya, `CaptureQueriesContext` | oddiy javob **12**, M o‘zgarishi (voris ochiladi) **12**, `review_repeat` **8**, yangi talabaning birinchi so‘rovi 21 — D66a bilan aynan mos. Django 6 `BEGIN`/`COMMIT` ni ham yozadi; ular bilan +2 (14 / 14 / 10 / 23) — D66 ularni sanamaydi, men ham ajratdim |
| D66a'ning ikki xom SQL buyrug‘i haqiqatan ishlaydi | `WRITE_THETA_AND_B_SQL` va `INSERT_WITH_HISTORY_SQL` oddiy javobning so‘rovlari orasida |
| N+1: `learning/trajectory`, `curriculum/prerequisite-graph`, `learning_path/tree` — 8 mavzu va +30 mavzu | so‘rovlar soni o‘zgarmadi (uchala endpoint) |
| Oracle bilan tasodifiy javoblar: 3 talaba × 150 javob API orqali (ochiq mavzular, 10 % takror) | har bir takror bo‘lmagan ledger qatori (≥ 100) zanjirdan qayta o‘ynaldi: `p_before` (birinchi urinishda P(L0) — G_L dagi Pre(w), ω, talabaning P(L)), p̂, P(L)′, P(G), P(S), θ, b — 1e-9 da; `review_repeat` qatorlarida p_* NULL; yakuniy `irt_difficulty` va `n_answers` mos |
| V-D1 parallel javoblar xom SQL dan keyin | `test_d_parallel_answers.py` (3 test) HEAD'da — ya’ni xom SQL bilan — o‘tadi; xom SQL yo‘li ishlatilayotgani yuqorida isbotlangan |

### (d) D65a — `test_d65a_clamp.py` (3 test, PASS)

20 000 tasodifiy kirish (har 10-chisida P(L) = 1.0): `bkt.posterior` = clamp(oracle);
xom qiymat [0, 1] ichida bo‘lgan har holatda **bit-aniq** teng (clamp hech narsani
o‘zgartirmaydi); clamp ishlagan holatlar bor (xom − 1 < 1e-12). P(L) = 1.0 va
noto‘g‘ri javob: posterior va P(L)′ [0, 1] da. API orqali (t1, PT = 0,5): to‘g‘ri
javoblar bilan ledger P(L) aynan 1.0 ga yetdi, keyin 3 noto‘g‘ri javob — barcha
saqlangan ehtimolliklar [0, 1] da.

### (e) V-F1/V-F2

Locust jadvali (`locust/20261020-100901/tables.md`) `metrics.json` bilan katakma-katak
mos (so‘rovlar, xatolar, xato ulushi, p50, p95, RPS; `tables.verify` = []); uchala
endpoint p95 < 300 (190 / 210 / 280), xato 0; run parametrlari 50 foydalanuvchi,
120 s, gunicorn 8 worker, DEBUG yo‘q, kurs 500 / 1 500. REMEDIATION_REPORT §6 va
THESIS_MAPPING 10.2 dagi sonlar o‘sha. SQL sonlari (c) da.
**Locust takrori o‘tkazilmadi** — shart bajarilmadi (7-bo‘lim).

### (f) REMEDIATION_REPORT — `test_reports.py` (5 test, PASS)

- `experiments.report_values --check REMEDIATION_REPORT.md` (o‘zim ishga tushirdim,
  ikkala venv'da): **177 son, 9 bo‘lim, 0 farq**, rc = 0; nusxada bitta son
  (BKT AUC 0.707 → 0.708) o‘zgartirilsa — rc ≠ 0.
- Matritsa: hisobotdagi §2.2 PROGRESS'dagi bilan **qatorma-qator bir xil**
  (239 qator); 226 / 9 / 4 — qatorlardan sanaldi; “Kutilmoqda” yo‘q.
- **Kech “Bajarildi” ga o‘tgan qatorlar** (2026-10-12 dagi `e97261e` bilan
  solishtirib): **44 qator**. Har birining dalilidagi commit'lar backend yoki
  frontend tarixida bor, fayl yo‘llari mavjud (o‘chirilgani yozilgan
  `pages/Courses.tsx` — `c2bb542` da o‘chirilgan). 5 qatorda dalil boshqa qatorga
  havola (masalan “EX3, EX4 qatorlari”) — o‘sha qatorlarda dalil bor. Butun
  matritsa bo‘yicha “Bajarildi” qatorlaridagi 272 ta commit/yo‘l tokeni — hammasi
  mavjud.
- **“Qisman” (9) va “Kechiktirildi” (4) sabablari — baho:**
  - `.env` tokeni (1.3, 7.3, Q6 — bitta masala uch qatorda): sabab haqiqiy —
    bekor qilish faqat foydalanuvchida.
  - ES8 / “Simulyator generativ emas”: sabab asosli (D48: natija faqat haqiqiy
    ma’lumotdan; D13), lekin 8-bosqich spetsifikatsiyasidagi generativ simulyator
    va undagi “Pre dastlabki AUC ni oshiradi” sanity testi bajarilmagan — bu
    ochiq qarz, sabab bilan.
  - pyKT/…/DBE-KT22: DBE-KT22 manbasi ochilmadi — tashqi to‘siq, asosli.
  - 7.2 Bundle (850 kB chunk) va 2.8 Profil (o‘chirish/parol UI yo‘q): sabab
    “bu bosqichda qilinmadi” — texnik to‘siq emas, tanlov. Qisman holati to‘g‘ri,
    lekin “sabab” aslida “qilinmagan ish” tavsifi.
  - 2.11 skrinshotlar: brauzer va to‘ldirilgan baza foydalanuvchida — asosli.
  - Kechiktirildi: DBE-KT22 yuklovchisi, annotatsiya/κ (annotator yo‘q), D26 va
    LLM dizayni (D26 qarori) — to‘rttasi ham asosli va hujjatlashtirilgan.

### (g) THESIS_MAPPING — `test_thesis_mapping.py` (4 test, PASS)

Jadval hujjatning o‘zidan (backtick tokenlar) o‘qiladi. 10.1 (20 qator) va 10.1a
(2.1–2.6) dagi har bir `fayl:funksiya` (`kb.x`, `Class.a/b`, yo‘lsiz fayl nomi
ham) `ast` bilan topildi; qavs ichidagi tavsifiy tokenlar (`lev`,
`move_into_subtree`) o‘sha faylda so‘z sifatida bor. Har bir test fayli va nomlangan
test funksiyasi (`*` bilan) mavjud; F1, F3, F6, F7 ning “Test.” qatorlari ham.
Nomlangan **17 test faylini** backend muhitida ishga tushirdim
(`scripts/dj5433.sh venv/bin/python -m pytest <17 fayl>`): **637 passed**,
13 subtests, 0 failed (3 daq 12 s). F2 yopilgan, F4 va F5 da “Test.” qatori yo‘q
(5-bo‘lim, K-6).

### (h) — 6-bo‘limda.

### (i) D70 — `test_d70_node_cycles.py` (34 test, PASS)

30 ta tasodifiy holat (1–2 kurs, 3–6 bo‘lim, 0–4 mavzu — ko‘p tugun bo‘sh) ×
30 qadam: relatsiya (har qanday ikki tugun), yangi mavzu, ko‘chirish — hammasi
`kb.*` orqali. Kutilgan qaror ikki mustaqil qismdan: D70 dan oldingi qoida
(oracle: Y2, `networkx` bilan G_L asiklikligi, “duplicate”) va G da y ⇝ x yo‘li
(o‘zimning BFS). Natija:

- servis qarori har qadamda kutilganiga teng; har qabul qilingan holatda
  **G ham, G_L ham siklsiz** (`networkx`); rad etilganda versiya, tugunlar va
  relatsiyalar o‘zgarmagan;
- yig‘indi: 498 qabul, **11 faqat tugunlar darajasidagi sikl** (D70 rad etgan),
  46 G_L sikli, **2 yangi mavzu G_L siklini yopgani uchun rad**, 55 ko‘chirish rad;
  alohida sanoqda 133 tugun-darajasidagi va 85 G_L rad etish;
- **tuzatilgan 2.2**: x, y va y ⇝ x yo‘lidagi barcha tugunlarda mavzu bo‘lsa, D70
  dan oldingi qoida o‘zi “cycle” deydi — ya’ni mavzusi bor tugunlarda D70 hech
  narsani o‘zgartirmaydi (har qadamda tekshirildi; leaf-darajasidagi zanjir
  `[a1, b1]` avvalgidek);
- kontrmisollar: mavzusiz ikki kurs C0 ⇄ C1 — ikkinchisi `cycle`, zanjir tugunlar
  darajasida (C0 … C1); bo‘sh S1 ⇄ S2 — rad, keyin ikkala bo‘limga mavzu
  qo‘shiladi (D70 dan oldingi “yashirin sikl” Y3 xatosi yo‘q).

## 4. Nuqsonlar

**N-1 (FAIL, V-E3) — pyKT eksporti pyKT'ning o‘z o‘quvchisi bilan to‘g‘ri o‘qilmaydi.**
`assessments/management/commands/export_research_data.py:319-338` (`write_pykt`,
`PYKT_LINES`) har talaba uchun **5 qator** yozadi (uid; savollar; konseptlar;
javoblar; vaqt). pykt-toolkit 0.0.38 (`experiments/.venv`) ning
`pykt.preprocess.split_datasets.read_data` bloki **6 qator** (… timestamps;
**usetimes**, yo‘q bo‘lsa `NA`) deb o‘qiydi. Natija: ikkinchi talabaning sarlavhasi
birinchisining `usetimes` iga tushadi, keyingi blok siljiydi, pyKT
`error response in line: 9` deydi va talabalarni tashlab yuboradi.
Takrorlash:
`verification/tests/test_e_consent_export.py::test_v_e3_pykt_reads_the_exported_sequences_without_error`
(eksport → `experiments/.venv/bin/python -I -c "read_data(...)"`, 3 talaba → 1 qator).
Sun’iy 3 talabalik 5-qatorli faylda ham xuddi shu (1 qator, `badr = 1`). Eksport
metadata'sining o‘zi “Verify against the installed pykt-toolkit before training
(stage 8b)” deydi — bu tekshirilmagan. Tuzatish yo‘nalishi: har blokka oltinchi
qator (`NA` yoki foydalanish vaqti). Dissertatsiya natijalariga ta’siri yo‘q (H1–H3
eksportdan o‘qimaydi), lekin V-E3 talabi buzilgan va platforma ma’lumotini pyKT
bilan tahlil qilish yo‘li ishlamaydi. Bu test suite'da ataylab **FAIL** qoldirildi.

**N-2 (kichik, V-H1 shakli) — CSV'da xulosa ustunlari yo‘q.** V-H1: “Chiqish
CSV'sida barcha amallar, hajmlar, mediana, p95, so‘rovlar soni va o‘zgargan
qatorlar bor”. `benchmarks/runner.py:811` (`csv_rows`) faqat har takrorning xom
vaqtini (va parallel op/s) yozadi; mediana, p95, so‘rovlar soni va o‘zgargan
qatorlar faqat `metrics.json` va `tables.md` da. Ma’lumot yo‘qolmagan (xom
vaqtlardan mediana/p95 qayta hosil qilinadi — (b) da qilindi), lekin so‘rovlar
soni va o‘zgargan qatorlar CSV'dan tiklanmaydi. Takrorlash:
`test_h_tree_benchmark.py::test_v_h1_the_csv_itself_carries_the_summary_columns`
(`xfail(strict=True)` — tuzatilsa XPASS bo‘lib yiqiladi va olib tashlanadi).

## 5. Kuzatuvlar

**K-1 (muhim, H1 talqini) — `pass_mark` bilan taqqoslash teng qamrovda emas.**
r_s(w) = min P(L) (`neuro_model/readiness.py:79`) va javobsiz prerekvizit P(L) = 0
bilan kiradi (D62-4). Shuning uchun prerekviziti to‘liq ishlanmagan har voqeada
r = 0 (voqealarning 26,2 %), ya’ni ehtimoliy qoidaning qamrovi faqat 1,0 (τ = 0)
yoki ≤ 0,738 bo‘la oladi. O‘tish bali qoidasining qamrovi 0,956 — unga eng yaqini
1,0, va `tau_for_coverage` beshala fold'da **τ = 0** ni tanladi
(`junyi-h1/20261019-102526/metrics.json`: `tau_chosen.3.pass_mark = 0.0`,
`coverage_gap = 0.043978`). Ya’ni “o‘tish bali” kontrasti ehtimoliy qoidani emas,
**“hamma tayyor”** qoidasini (xato ulushi = bazaviy 0,169) o‘tish bali bilan
solishtiradi; “qo‘llab-quvvatlanmadi” xulosasi shu degenerat taqqoslashga tayanadi.
Bajarilganlik bilan kontrastda τ ≈ 0,006–0,028, ya’ni ehtimoliy qoida amalda
“hamma prerekvizit ishlangan” qoidasining o‘zi (farq −0,000023). D61 ning o‘qish
qoidasi “teng qamrovda” deydi; bu shart o‘tish bali uchun bajarilmagan.
Implementatsiya D62 ga to‘g‘ri amal qilgan — bu kod nuqsoni emas, dizayn
oqibati, lekin dissertatsiyada H1 xulosasi shu cheklov bilan yozilishi kerak;
H1 ning mazmunli o‘lchovi r_s(w) AUC = 0,5195 [0,5012; 0,5372] (tasodifiydan
deyarli farqsiz).

**K-2 (H3) — λ har doim gridning pastki chetida.** λ ∈ {0,25; 0,50; 0,75}
(D62-10) dan validatsiya har fold'da va asl, teskari, tasodifiy-1 arm'larida
**0,25** ni tanladi (QADAM 10). II bobning λ = 0,5 i hech qayerda tanlanmagan,
asl − grafsiz esa k = 5 da manfiy. Optimum gridning pastidan tashqarida bo‘lishi
mumkin (D59 dagi PT holatiga o‘xshash) — H3 xulosasi “λ ≥ 0,25 da” deb o‘qilishi
kerak.

**K-3 — P(L) = 1.0 “aynan yutuvchi” emas, amalda yutuvchi.** D65a/F6: P(L)
double'da 1.0 ga yetgach noto‘g‘ri javobda P(L)′ fl(1 − S) ning yaxlitlanishiga
qarab 1.0 yoki 1 − O(1e-15) bo‘ladi (o‘lchangan: 0,9999999999999982). Xavf
(REMEDIATION_REPORT §4.5) to‘g‘ri tasvirlangan; faqat “P(L) ni tushirmaydi”
emas, “sezilarli tushirmaydi”.

**K-4 — V-F2 ning “keshdagi graf” qismi o‘lchanmagan.** V-F2 graf, `trajectory`
va `submit_answer` p95 ni so‘raydi; Locust oqimi `next_question`, `submit_answer`,
`trajectory` (D68). Graf endpoint'i (`/api/curriculum/prerequisite-graph/`) yuk
ostida o‘lchanmagan; uning so‘rovlar soni mavzular soniga bog‘liq emasligi (c) da
tasdiqlandi.

**K-5 — V-F1 bir martalik holatlarda 12 dan yuqori.** Kursdagi birinchi javob 15,
yangi talabaning birinchi so‘rovi 21 (θ qatori va holat qatorlari yaratiladi).
D66a buni ochiq yozgan; V-F1 yumshoq chegara.

**K-6 — THESIS_MAPPING: F5 (kalibrlash grid'i) da “Test.” qatori yo‘q.** Grid
`neuro_model/tests/test_calibrate.py::test_the_p0_and_pt_grids_are_d59s` bilan
qotirilgan (mavjud, o‘tadi) — faqat hujjatda nomlanmagan. F4 ham testsiz (faqat
kesh manzili).

**K-7 — matritsada “Bajarildi (kod)” holati** (EX5, “Benchmark zaif”) legendada
yo‘q; 226 ga “Bajarildi” sifatida kiradi. H4 natijasi keyin qo‘shilgan (“H4
tayyorligi” qatori), shuning uchun “(kod)” izohi eskirgan.

**K-8 — H1 jadvalida “-0 [-0; 0]”.** `tables.fmt` 3 xonada −0,000023 ni “-0”
qilib ko‘rsatadi; D48 bo‘yicha to‘g‘ri (son metrics'da), lekin o‘quvchi uchun
belgi va kattalik yo‘qoladi. Dissertatsiya jadvalida 6 xona yoki ilmiy yozuv
tavsiya etiladi.

**K-9 — REMEDIATION_REPORT §8 va QADAM 14 dagi verification sonlari endi
eskirgan** (824 / 6 / 1). Bu hisobotdagi sonlar 1-bo‘limda; `REMEDIATION_*.md`
ga tegilmadi — yangilash implementatorning ishi.

**K-10 — muhit.** `scripts/dj5433.sh` ning standart `SECRET_KEY`
(“benchmark-local-only”, 20 bayt) PyJWT'ning `InsecureKeyLengthWarning` ini
beradi (faqat test/benchmark o‘rami; production kaliti env'dan). Ikki
`verification/tests` sessiyasi bir vaqtda ishga tushsa, ikkinchisi birinchisining
test bazasini o‘chirishga urinadi (qat’iy `TEST.NAME`) — README'ga yozildi.

## 6. II bob ta’riflari va kod orasidagi farqlar (faqat ro‘yxat)

II bob matni repoda yo‘q; solishtirish `NEUROLEARN_REMEDIATION.md` §3 (II bobdan
olingan model), 8-bosqich matni va qarorlar (D…) bo‘yicha. Faqat ro‘yxat.

| # | II bob / spetsifikatsiya | Kodda | Qayerda / qaror |
|---|---|---|---|
| 1 | H1: qoida “birinchi urinish”da tekshiriladi | Voqea — birinchi urinish, lekin muvaffaqiyatsizlik **dastlabki k = 3 javobda** to‘g‘rilar ulushi < 0,5 (k = 5 qo‘shimcha); k tadan kam javobli voqea bor javoblari bilan | `experiments/h1.py:153` (`Event.failed`), D62-5/6 |
| 2 | H1 bajarilganlik: “har bir prerekvizit **savoliga** ≥ 1 javob” | har bir prerekvizit **mashqiga (mavzuga)** ≥ 1 javob | `experiments/h1.py:172`, D61 |
| 3 | H1: ehtimoliy qoida r ≥ τ, teng qamrov | r = min P(L), javobsiz prerekvizit P(L) = 0 (P(L0) emas) — teng qamrov o‘tish bali uchun erishilmaydi (K-1) | D62-4, `readiness.py:79` |
| 4 | H1 qoidalari: 3 ta | + II bobning R (M, δ) va platformaning `earned_proficiency` (qo‘shimcha) | D61, D62a(c) |
| 5 | Ma’lumot: DBE-KT22 (javoblar + KC grafi) | **Junyi Academy (2015)** — H1/H3; ASSISTments 2009 — H2 (grafsiz) | D61, D53 |
| 6 | ω ∈ (0, 1] har relatsiyada | Junyi'da ω = 1 (vazn yo‘q); 3 tugunli SCC bitta mavzuga birlashtirildi (Y3) | D62-3, D61 |
| 7 | 2.2-tasdiq: G_L siklsiz ⇒ G siklsiz | **Shartli**: sikldagi har tugunda mavzu bo‘lsa; shartsiz ifoda bo‘sh tugunlarda noto‘g‘ri; teskarisi umuman noto‘g‘ri | D70, THESIS_MAPPING 10.1a |
| 8 | Algoritm 2.1: Y2 + G_L da BFS, O(n·d + m) | + G = (N, E_P) da y ⇝ x BFS, O(\|N\| + \|E_P\|) | `neuro_model/graph.py:find_node_cycle_chain`, F7 |
| 9 | θ, P(L) formulalari cheklovsiz | θ ±4 (F1); posterior va P(L)′ [0, 1] ga clamp (F6); P(L) = 1.0 amalda yutuvchi (K-3) | D6, D65a |
| 10 | Kalibrlash usuli belgilanmagan | chegaralangan grid (4 752 nomzod); G0 va S0 ning 77 % / 87 % i yuqori chetda | F5, D59 |
| 11 | Har javob yangi dalil | `review_repeat` oynasidagi takror ledger'ga yoziladi, modelni o‘zgartirmaydi | F3, D25 |
| 12 | H3: graf Pre(w) orqali yordam beradi (λ = 0,5) | λ validatsiyada {0,25; 0,50; 0,75} dan; har joyda 0,25 tanlandi (K-2); o‘lchov — mashqning dastlabki k ∈ {3, 5} urinishi AUC | D62-10, D61 |
| 13 | H2: bashorat — talabaning oldingi javoblaridan | D57: qat’iy oldingi **order**lardan; BKT+IRT (λ=0), Elo, PFA uchun boshqa talabalarning oldingi javoblari ham (b_q, PFA) | D57, oldingi hisobot K-2 |
| 14 | H4: “CTE yozishda tezroq, o‘qishda taqqoslanadigan” | “taqqoslanadigan” = ≤ 1,5× sekin (natijadan oldin tanlangan); o‘zgartiruvchi amallar orqaga qaytariladigan tranzaksiyada (fsync o‘lchanmaydi) | D63, D63a |
| 15 | V-E4: `run_all --quick` simulyatsiya ma’lumotida, “simulated” belgisi | haqiqiy ma’lumotda, “`--quick` — dissertatsiya natijasi emas” belgisi; parametr tiklash testi `test_calibrate.py` da | D48, D13 |
| 16 | V-F2: lokal, bitta server | gunicorn 8 sync worker (runserver 50 foydalanuvchida p95 6,3 s) | D68a |

## 7. N/A va bajarilmaganlar

| Tekshiruv | Holat | Sabab |
|---|---|---|
| (e) Locust'ning 2 daqiqalik gunicorn takrori | **o‘tkazilmadi** | Shart bajarilmadi (2026-10-20, o‘lchangan): MemAvailable **5 963 MB** (< 6 GB), swap ishlatilgani **2 784 MB** (≥ 200 MB); sessiya davomida swap bo‘shi 1,3 GB → 0,8 GB ga tushdi. Farq yozilmadi — taxmin yozilmaydi |
| V-G1, V-G2, V-G3, V-G5, V-G7 | **N/A** | Brauzer harness yo‘q (frontend'da Playwright va `e2e/` yo‘q — `test_na_group_g_browser_checks_have_no_harness` hamon o‘tadi); frontend repozitoriydan tashqarida |
| V-G6 | qisman PASS | statik qismi (`test_g_frontend_contract.py`); “har son API javobida” — brauzersiz emas |
| V-A4 (`mutmut`) | qo‘l mutantlari | o‘zgarmagan (7/7 ushlanadi) |
| CI masofada | **tasdiqlanmadi** | push yo‘q; men backend, experiments, verification suite'larini lokal yugurdim (1-bo‘lim); frontend CI (lint, tsc, vitest, build) bu topshiriq ro‘yxatida yo‘q va qayta yugurtirilmadi |
| `run_all --dataset assist09 --quick` | qayta yugurtirilmadi | 24 daqiqa; junyi quick (h1 + h3) va dispatcher (spy) yetarli deb olindi; assist09 quick'ning commit qilingan natijasi tekshirildi (`test_e4_run_all.py`) |
| Junyi per-skill parametrlari taqsimoti | N/A | saqlanmagan (implementatorning o‘zi yozgan) |

## 8. Yakuniy hukm — spetsifikatsiyaning 6-bo‘limi

`NEUROLEARN_REMEDIATION.md` §6: “Ish quyidagi barcha shartlar bajarilganda
tugallangan hisoblanadi”.

| Shart | Mustaqil hukm | Dalil (shu sessiyada) |
|---|---|---|
| 4-bo‘limdagi barcha etalon testlar o‘tadi | **bajarildi** | backend suite 1 289 passed, 0 failed; THESIS_MAPPING nomlagan 17 fayl 637 passed; verification'ning V-A1 (4-bo‘lim sonlari oracle bilan 1e-3 da) o‘tadi |
| CI ikkala repozitoriyda yashil | **tasdiqlanmadi** | CI masofada hech qachon ishga tushirilmagan (push yo‘q). Backend'ning lokal ekvivalenti yashil (1-bo‘lim); frontend CI'ni men qayta yugurtirmadim (implementator: lint 0 error, tsc 0, vitest 90/90, build). Shartning so‘zma-so‘z o‘qilishida bajarilmagan |
| “Kechiktirildi” qatorlarining sababi yozilgan | **bajarildi** | 4/4 qatorda sabab (va 9/9 “Qisman” da); matritsa hisobot bilan bir xil, 226 / 9 / 4 qatorlardan sanaldi; 272 dalil tokeni mavjud (3 (f)) |
| `run_all.py --quick` va `run_tree_benchmark --quick` toza muhitda xatosiz | **bajarildi** (bitta izoh bilan) | `run_tree_benchmark --quick` — verification'ning yangi benchmark test bazasida rc = 0, chiqish katakma-katak tekshirildi; `run_all --dataset junyi --quick` — `740bb20` ning toza klonida rc = 0, ikkala natija toza provenance bilan, `tables.verify` = []. Izoh: venv'lar yangidan lock fayllardan qurilmadi (repodagi `experiments/.venv` ishlatildi) va `--dataset assist09 --quick` qayta yugurtirilmadi |

**Yakuniy hukm: 6-bo‘limning tugallanganlik mezoni to‘liq bajarilmagan** — to‘rt
shartdan uchtasi mustaqil tasdiqlandi, “CI ikkala repozitoriyda yashil” sharti esa
faqat lokal ekvivalent bilan qoplangan (masofaviy CI yo‘q; bu push va CI ishga
tushirilishi bilan yopiladi, kod o‘zgarishi talab qilinmaydi). Implementatsiyaning
o‘zida II bob modeli bo‘yicha **mahsulot nuqsoni topilmadi**: A–D, H4, D65a, D66a,
D70 tekshiruvlarining hammasi o‘tdi. Mezondan tashqari, verification
spetsifikatsiyasi bo‘yicha bitta **FAIL** bor — **N-1 (V-E3)**: pyKT eksporti
pyKT 0.0.38 o‘quvchisi bilan to‘g‘ri o‘qilmaydi; va bitta kichik shakl
nomuvofiqligi — **N-2 (V-H1 CSV)**. Dissertatsiya natijalariga ikkalasining ham
ta’siri yo‘q; H1 talqini uchun K-1 muhim.

## 9. Qanday qayta ishga tushirish

```bash
docker compose --env-file config/.env up -d            # Postgres 5433, Redis 6380
scripts/dj5433.sh venv/bin/python -m pytest --ds=verification.settings verification/tests -q -p no:cacheprovider
experiments/.venv/bin/python -m pytest verification/neural -q -p no:cacheprovider
experiments/.venv/bin/python -m experiments.report_values --check REMEDIATION_REPORT.md
```

Bir vaqtda ikki `verification/tests` sessiyasi ishga tushirilmasin: test bazasi
nomi qat’iy (`neurolearn_verify`), ikkinchisi birinchisining bazasini o‘chirishga
urinadi.
