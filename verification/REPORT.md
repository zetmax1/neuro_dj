# verification/REPORT.md — yakuniy mustaqil tekshiruv, yopish sessiyasi, 2026-10-21

Tekshiruvchi sessiyasi (D54), yopish. Faqat `verification/` ga yozildi;
implementatsiya kodi, `experiments/`, `benchmarks/`, `docs/`, `REMEDIATION_*.md`
va commit qilingan natijalarga tegilmadi; `config/.env` va ildiz `.env`
ochilmadi. Postgres buyruqlari `scripts/dj5433.sh` orqali (DSN konteynerdan, env
fayl o‘qilmaydi). Push, amend, rebase, reset — yo‘q.

**Boshlang‘ich holat.** Branch `thesis-model`, HEAD `852e1e3` (QADAM 15), daraxt
toza, `systemctl --user list-units 'neurolearn-*'` → 0. Oldingi tekshiruvdan
(`85ac91e`, 2026-10-20) beri 7 commit: `cdd8826` (N-1 tuzatish), `3ed55e9` (N-2
tuzatish), `3614f27` (D71 qarori), `f88ded8` (D71 kodi), `c1ad4a9` (D71 quick
natijasi), `b0295da` (D71 to‘liq natijasi), `852e1e3` (hujjatlar).

Oldingi versiyalar (`e97261e`, `85ac91e`) shu fayl tarixida qoladi. 3 (a)–(i)
bo‘limlari `85ac91e` sessiyasidan (o‘sha kod bugun ham o‘zgarmagan — 0 (e));
0, 1, 2, 3 (j)–(k), 4, 5, 7, 8-bo‘limlar shu sessiyada yangilandi.

## 0. Yopish sessiyasi — topshiriqlar va natija

| # | Topshiriq | Natija |
|---|---|---|
| 1 | `test_e_consent_export.py:105` dagi `_pykt_blocks` ni pyKT 0.0.38 ning 6 qatorli blokiga moslashtirish | **Bajarildi.** Blok `PYKT_BLOCK` = (uid,seq_len; questions; concepts; responses; timestamps; usetimes) — `pykt/preprocess/split_datasets.py:9-79` dagi `read_data` ning `i % 6` qadami (o‘rnatilgan 0.0.38 ning o‘zidan o‘qildi). Sanash testi endi to‘rt qatorda n ta qiymat va pyKT “yo‘q ustun” deb oladigan `NA` yo‘qligini, oltinchi qatorda `NA` (yoki n qiymat) ni tekshiradi. 3 FAIL yo‘qoldi: modul **28 passed** (oldin 25 passed, 3 failed) |
| 2 | N-2 strict xfail → kichik yangi run | **Bajarildi.** `test_v_h1_the_csv_itself_carries_the_summary_columns` endi `tmp_path` ga `run_tree_benchmark --quick` ni kichik daraxtda yuguradi (`random`, 100 tugun, 3 takror, 1 warm-up, 2 worker × 0,5 s × 1) — **3,2 s**. Har takror qatorida `median`, `p95` = `metrics.json` dagi qiymat **va** o‘zim CSV vaqtlaridan hisoblagan mediana / p95 (`statistics.quantiles(..., method="inclusive")`, 1e-6); `queries` ≥ 1, ularning mediana / min / max = `queries_median` / `_min` / `_max`; `rows_touched` mediana = `rows_touched_median`, yozish amallarida ≥ 1; parallel qatorlarda to‘rt ustun bo‘sh; 6 amal × 2 usul. **Bo‘sh emasligi:** `3ed55e9^` dagi eski `csv_rows` scratch plagin bilan monkeypatch qilinsa — test yiqiladi (sarlavhada ustunlar yo‘q) |
| 3 | H2/D55/D60/H1/H3/D71 `export_research_data` ni ishlatmasligi | **Tasdiqlandi** — 3 (k). Yangi test `test_e_experiments.py::test_n1_no_experiment_reads_the_research_export` |
| 4 | D71: reja run'dan oldin, `tables.verify`, D48 pozitsion, post-hoc belgisi, D61/D62 hukmlari | **Tasdiqlandi** — 3 (j). Yangi modul `test_e_d71_posthoc.py` (12 test) |
| 5 | `852e1e3` diff'i: II bob konstantalari, `DEFAULT_GRID`, lock fayllar | **O‘zgarmagan** — 0 (e) |
| 6 | To‘liq suite'lar | 1-bo‘lim |
| 7 | Hisobot, faqat `verification/` commit | shu fayl |

### 0 (e). `852e1e3` va `85ac91e..852e1e3` diff'i

- `852e1e3` ning o‘zi faqat 3 hujjat faylini o‘zgartiradi: `REMEDIATION_PROGRESS.md`
  (faqat qo‘shilgan qatorlar, 0 o‘chirilgan), `REMEDIATION_REPORT.md`,
  `docs/THESIS_MAPPING.md`. Kod, konstanta, grid, lock fayl yo‘q.
- Butun oraliq `85ac91e..852e1e3` da `git diff --stat` **bo‘sh**:
  `config/settings.py` (`THESIS_MODEL`), `experiments/models/` (`classical.py:44`
  `CONSTANTS`: G_MAX 0,30, S_MAX 0,10, a 1, Elo α 0,8 / β 0,05, λ 0,5, τ 0,95,
  c 0,05, θ ±4), `neuro_model/` (`calibrate.py:93` `DEFAULT_GRID`, 4 752 nomzod),
  `requirements.lock`, `experiments/requirements.lock`, `requirements*.txt`,
  `experiments/requirements.txt`, `experiments/h1.py`, `h2.py`, `h3.py`,
  `experiments/datasets/`. Oraliqdagi o‘zgargan kod: `export_research_data.py`
  (N-1), `benchmarks/runner.py` (N-2), yangi `experiments/d71.py`, `run_h2.sh` ga
  3 ta `d71-*` maqsad, testlar.
- `experiments/results/` da oraliqda 12 fayl, hammasi `A` (qo‘shilgan) — commit
  qilingan natija o‘zgartirilmagan yoki o‘chirilmagan.

## 1. Testlar (o‘lchangan sonlar)

| Suite | Muhit | `85ac91e` (oldingi hisobot) | `852e1e3` + shu sessiyaning `verification/` o‘zgarishlari |
|---|---|---|---|
| `verification/tests` | `venv` (Django 6.0.5), compose Postgres 5433, `--ds=verification.settings` | 936 passed, 1 failed (N-1), 1 xfailed (N-2) | **951 passed**, 0 failed, 0 xfailed, 0 skipped (7 daq 48 s) |
| `verification/neural` | `experiments/.venv` (torch 2.5.1+cpu, pykt 0.0.38) | 62 passed, 3 skipped | **62 passed, 3 skipped** (4 s; skip'lar — D57 izolyatsiyasi populyatsiya parametrli 3 model uchun ataylab) |
| Backend (`scripts/dj5433.sh venv/bin/python -m pytest`; `experiments/tests` va `benchmarks/tests` ichida) | `venv` | 1 289 passed, 51 skipped, 13 subtests | **1 298 passed, 51 skipped**, 13 subtests, 0 failed (12 daq 22 s); 51 skip — hammasi torch talab qiladigan `experiments/tests` (`test_h2_bounds` 19, `test_h2_frozen` 13, `test_order_protocol` 13, `test_models` 6), ular `experiments/.venv` da yuguradi. QADAM 15 dagi son bilan aynan |
| `experiments/tests` | `experiments/.venv` | 409 passed, 2 skipped | **415 passed, 2 skipped** (14 daq 0 s, boshqa suite bilan bir vaqtda; skip — Django tomoni bu venv'da yo‘q) |
| `benchmarks/tests` | `venv` | 90 passed | **92 passed** (27 s; +2 — `3ed55e9` ning testlari) |
| `report_values --check REMEDIATION_REPORT.md` | ikkala venv | 177 son, 9 bo‘lim, 0 farq | **177 son, 9 bo‘lim, 0 farq**, rc = 0 (ikkala venv'da) |
| `run_tree_benchmark --quick` (to‘liq quick, o‘zim) | verification benchmark test bazasi | rc = 0, 3 daq 47 s | `test_v_h1_run_tree_benchmark_quick_runs_here` ichida HEAD'da (N-2 dan keyin) qayta yugurdi — PASS |

`verification/tests` ning o‘sishi: 938 → 951 test (+12 `test_e_d71_posthoc.py`,
+1 N-1 qamrovi; N-2 xfail oddiy testga aylandi, son o‘zgarmadi).

Seed: `verification.settings.VERIFICATION_SEED` = 20261003. `verification/tests`
xdist'siz, `-p no:cacheprovider`. Bu sessiyada `verification/tests` va
`experiments/tests` bir vaqtda, keyin backend va `verification/neural` (har biri
o‘z test bazasi bilan) yugurdi — devor vaqtlari shuning uchun taqqoslanmaydi.

## 2. `verification/` dagi xatolar — sabab va qaror

`85ac91e` dagi 7 ta xato (N/A signallari, D48 mezoni, D70 fixture'i) o‘sha
sessiyada yopilgan (shu fayl tarixida, `85ac91e`). Shu sessiyada:

| # | Test | Sabab | Qaror |
|---|---|---|---|
| 8–10 | `test_e_consent_export.py::test_v_e1_the_only_learner_identifier_is_the_pseudonym`, `::test_v_e2_sources_and_archived_topic_in_every_file`, `::test_v_e2_counts_agree_across_the_files` | Tekshiruvchining yordamchisi `_pykt_blocks` (`:105`) N-1 dan oldingi 5 qatorli blokni taxmin qilardi; `cdd8826` dan keyin fayl 6 qatorli (`… "NA"`) — N-1 tuzatishining kutilgan oqibati | **Yopildi** (0-bo‘lim, 1). Blok uzunligi endi spetsifikatsiyadan emas, pyKT 0.0.38 ning o‘z o‘quvchisidan |
| 11 | `test_h_tree_benchmark.py::test_v_h1_the_csv_itself_carries_the_summary_columns` (strict xfail) | Commit qilingan eski quick CSV'ni o‘qirdi — N-2 dan oldin yozilgan, qayta yozilmaydi | **Yopildi** (0-bo‘lim, 2): yangi kichik run'ning CSV'si tekshiriladi, xfail olib tashlandi |

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

### (a′) V-E4 va V-E3 — `test_e4_run_all.py` (10 test, PASS), `test_e_consent_export.py` (28 test, PASS)

- **V-E4.** `run_all.plan`: assist09 → faqat h2 (h1, h3 sabab bilan
  “ishga tushirilmadi”), junyi → h1 va h3 (h2 sabab bilan); `--dry-run` hech
  qanday natija papkasi yaratmaydi; noma’lum dataset/model/gipoteza → rc 2.
  Har gipotezaning `main` i spy bilan almashtirildi: `--quick` va `--workers`
  har ishga tushadigan gipotezaga, `--models` h2 ga uzatiladi; h1 rc ≠ 0
  bo‘lsa h3 ishga tushmaydi. Commit qilingan quick natijalari (h1, h2, h3):
  `quick = true`, `thesis_result = false`, jadvalda “`--quick` ishga tushirish —
  dissertatsiya natijasi emas”, buyruqda `--quick`, git'da kuzatiladi,
  `tables.verify` = []. Spetsifikatsiyadagi “simulyatsiya ma’lumotida” o‘rniga
  haqiqiy ma’lumot (D48) — 6-bo‘lim, 15-band. Junyi quick `85ac91e` sessiyasida
  o‘zim yugurtirdim; o‘shandan beri `run_all.py`, `h1.py`, `h2.py`, `h3.py` va
  `datasets/` o‘zgarmagan (0 (e)).
- **V-E3.** Qatorlar soni (metadata = CSV = pyKT bloklari) o‘tadi; **pyKT'ning
  o‘z o‘quvchisi** (`experiments/.venv`, `read_data`, `-I`) bilan o‘qish — endi
  **PASS**: xato qatori yo‘q, `uid` lar = CSV psevdonimlari, talabalar va
  javoblar soni metadata bilan teng (N-1 yopildi, 4-bo‘lim).

### (b) H4 — `test_h_tree_benchmark.py` (24 test, PASS)

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
| V-H1, **o‘zim ishga tushirdim**: `run_tree_benchmark --quick` (verification'ning benchmark test bazasida, `--out` tmp, `--no-checkpoint`) | rc = 0; `metrics.json`, `measurements.csv`, `tables.md`, `env.txt` yozildi; `tables.verify` va `verify_tree_benchmark_positions` = []; har shakl × 6 amal × 2 usul CSV'da, har katakda p95 > 0 va so‘rovlar ≥ 1; parallel qulfsiz bosqich ikkala usulda, har birida yaxlitlik natijasi |
| V-H1, CSV'ning o‘zida to‘rt ustun (N-2) — kichik yangi run | 0-bo‘lim, 2: PASS (3,2 s); eski `csv_rows` bilan — FAIL |

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
**Locust takrori o‘tkazilmadi** (7-bo‘lim).

### (f) REMEDIATION_REPORT — `test_reports.py` (5 test, PASS)

- `experiments.report_values --check REMEDIATION_REPORT.md` (shu sessiyada,
  ikkala venv'da): **177 son, 9 bo‘lim, 0 farq**, rc = 0; nusxada bitta son
  (BKT AUC 0.707 → 0.708) o‘zgartirilsa — rc ≠ 0. `852e1e3` qo‘shgan D71 matni
  `report_values` qamrovida emas (son o‘sha 177) — uning da’volarini qo‘lda
  tekshirdim (3 (j), oxirgi band).
- Matritsa: hisobotdagi §2.2 PROGRESS'dagi bilan **qatorma-qator bir xil**
  (239 qator); 226 / 9 / 4 — qatorlardan sanaldi; “Kutilmoqda” yo‘q.
- **Kech “Bajarildi” ga o‘tgan qatorlar** (2026-10-12 dagi `e97261e` bilan
  solishtirib): **44 qator**, dalillaridagi commit'lar va yo‘llar mavjud; butun
  matritsa bo‘yicha “Bajarildi” qatorlaridagi 272 ta commit/yo‘l tokeni mavjud.
- **“Qisman” (9) va “Kechiktirildi” (4) sabablari — baho** (`85ac91e` dagidek):
  `.env` tokeni (1.3, 7.3, Q6) — bekor qilish faqat foydalanuvchida; ES8 /
  “Simulyator generativ emas” — asosli (D48, D13), lekin generativ simulyator va
  uning sanity testi ochiq qarz; DBE-KT22 — tashqi to‘siq; 7.2 Bundle va 2.8
  Profil — “qilinmagan ish”, texnik to‘siq emas; 2.11 skrinshotlar — asosli;
  4 “Kechiktirildi” — asosli va hujjatlashtirilgan.

### (g) THESIS_MAPPING — `test_thesis_mapping.py` (4 test, PASS)

10.1 (20 qator) va 10.1a dagi har bir `fayl:funksiya` `ast` bilan topildi; har
test fayli va nomlangan test funksiyasi mavjud. `852e1e3` qo‘shgan D71 jadvalidagi
`experiments/d71.py:subset_rules`, `subset_equal_coverage`, `h1_part`, `curve`,
`h3_part`, `gate`, `fit`, `fit_checkpoint` va uchta `test_d71.py::…` nomi ham
mavjud (qo‘lda). F4 va F5 da “Test.” qatori yo‘q (K-6).

### (h) — 6-bo‘limda.

### (i) D70 — `test_d70_node_cycles.py` (34 test, PASS)

30 ta tasodifiy holat × 30 qadam: relatsiya, yangi mavzu, ko‘chirish — hammasi
`kb.*` orqali; kutilgan qaror ikki mustaqil qismdan (D70 dan oldingi qoida —
oracle, `networkx`; G da y ⇝ x — o‘z BFS'im). Servis qarori har qadamda kutilganiga
teng; har qabul qilingan holatda **G ham, G_L ham siklsiz**; rad etilganda
versiya, tugunlar va relatsiyalar o‘zgarmagan; yig‘indi: 498 qabul, 11 faqat
tugunlar darajasidagi sikl, 46 G_L sikli, 2 yangi mavzu G_L siklini yopgani
uchun rad, 55 ko‘chirish rad. Tuzatilgan 2.2 va kontrmisollar — `85ac91e` dagidek.

### (j) D71 — `test_e_d71_posthoc.py` (12 test, PASS)

| Tekshiruv | Natija |
|---|---|
| Reja run'dan oldin | `## D71 — …` sarlavhasi `3614f27^` da yo‘q, `3614f27` da bor; `3614f27` da `experiments/d71.py` yo‘q. To‘rt papkaning (`junyi-h1-posthoc[-quick]`, `junyi-h3-lambda[-quick]`) `code_commit` i — quick `f88ded8`, to‘liq `c1ad4a9`; ikkalasi ham `3614f27` ning avlodi (`merge-base --is-ancestor`); `git_start.at` (17:02:40 va 17:15:23 UTC) > reja commit vaqti (16:43:25 UTC); ikkala uchida toza, `git_start` = `git_end` = `code_commit`. `git diff 3614f27 HEAD -- REMEDIATION_PROGRESS.md` da **o‘chirilgan qator yo‘q** — reja keyin tahrirlanmagan |
| `tables.verify` | to‘rt papkada **[]** |
| D48 pozitsion (o‘zimniki; D71 uchun implementatsiyada pozitsion tekshiruvchi yo‘q) | `metrics.json` dan har qiymat ma’nosi bo‘yicha olinadi va **o‘z jadvali (bo‘lim / k), o‘z qatori (qoida yoki τ / λ soni bo‘yicha), o‘z ustuni (sarlavha nomi bilan) va katak ichidagi o‘rni** (“0.784 [0.776; 0.791]” da baho / quyi / yuqori) da qidiriladi: H1 papkalarida **170**, H3 da **48** qiymat — hammasi o‘z katagida. Bo‘sh emasligi: τ = 0,5 qatorida ikki katak almashtirilsa — 2 ta xato; λ = 0,5 va 0,75 qatorlari almashtirilsa — xato. Scratch'da qo‘shimcha: har papkada 200 tasodifiy bitta-katak mutatsiyasi — **800 / 800 ushlandi** |
| Post-hoc belgisi, hukm yo‘q | to‘rt papkada `spec = D71`, `posthoc = true`, `descriptive = true`, `status_note` “post-hoc, tavsifiy — D61/D62 ning o‘qish qoidasi va hukmi o‘zgarmaydi”; `tables.md` banneri xuddi shu; `reading` / `verdict` kaliti yo‘q, “qo‘llab-quvvatlandi / qo‘llab-quvvatlanmadi / aniqlanmadi” so‘zlari na jadvalda, na metrics'da yo‘q. Quick papkalarda `quick = true`, `thesis_result = false` va “dissertatsiya natijasi emas”; to‘liqlarida aksincha |
| Takrorlanish darvozasi — **o‘zim, asl natijalardan** | split seed / fold'lar, N = 2 000, log sha256, 1 000 replika — asl H1/H3 bilan bir xil. H1: voqealar 9 664, S = 7 136 (`with_every_prerequisite_answered`), to‘liq to‘plamdagi 5 qoidaning (belgilangan, muvaffaqiyatsiz) — asl `rules` bilan aynan. H3: asl run'da λ beshala fold'da 0,25 (fold yozuvlaridan); D71 ning λ = 0,25 va λ = 0 AUC'i (k = 3, 5) asl `asl` va `grafsiz` arm'lari bilan 1e-9 da, javoblar soni teng. λ to‘plami {0; 0,1; 0,25; 0,5; 0,75; 1} va τ egri chizig‘i 15 nuqtasi — rejadagidek. D71 ning o‘z `reproduction_gate` i (15/15) ham `equal` |
| D61/D62 hukmlari o‘zgarmagan | `junyi-h1/20261019-102526` va `junyi-h3/20261019-122423` — har biri tarixda bitta commit (`abc8c5a`, `ac632d3`), `3614f27..HEAD` diff'i bo‘sh, ishchi daraxtda o‘zgarish yo‘q. Asl hukmlar: H1 “qo‘llab-quvvatlanmadi”, H3 k = 3 “aniqlanmadi”, k = 5 “qo‘llab-quvvatlanmadi” — THESIS_MAPPING qatorlaridagi qalin hukm aynan shular. `852e1e3` H1/H3 qatorlarida hukmni o‘zgartirmagan, faqat D71 izohini qo‘shgan |
| `852e1e3` dagi D71 da’volari (qo‘lda) | “S da ehtimoliy qoida o‘tish bali va `earned_proficiency` dan farq qilmaydi” — to‘rt farqning (k = 3, 5) CI'si nolni kesadi: to‘g‘ri. “H3 da AUC λ oshgan sari kamayadi, eng yuqorisi λ = 0” — k = 3 va k = 5 da baholar qat’iy kamayadi: to‘g‘ri. “r_s(w) AUC'i tasodifiyga yaqin” — k = 3 da 0,523 [0,496; 0,549], k = 5 da 0,540 [0,515; 0,565]: kattalik bo‘yicha to‘g‘ri, lekin k = 5 da CI 0,5 ni o‘z ichiga olmaydi (K-11) |

### (k) N-1 natijalarga ta’sir qilmagani — `test_e_experiments.py::test_n1_no_experiment_reads_the_research_export` (PASS)

`export_research_data` — Django management buyrug‘i
(`assessments/management/commands/export_research_data.py`). Pipeline'lar uni
ishlatmaydi:

| Pipeline | Ma’lumotga kirish (fayl:qator) | Manba yozuvi |
|---|---|---|
| H2 | `experiments/h2.py:127` `assist09.load(...)` → `experiments/datasets/assist09.py:48` (`assistments2009/as.csv`), `:170` `load`, `:207` `open` | `h2.py:499` `Source.of("assistments2009", dataset.path)` |
| D55 (`h2_bounds`) | `experiments/h2_bounds.py:562` `h2.prepare(...)` (H2 ning o‘sha yo‘li) | `h2_bounds.py:753` |
| D60 (`h2_frozen`) | `experiments/h2_frozen.py:504` `h2.prepare(...)` | `h2_frozen.py:606` |
| H1 | `experiments/h1.py:555` `junyi.load(...)` → `experiments/datasets/junyi.py:80-81` (`junyi_Exercise_table.csv`, `junyi_ProblemLog_original.csv`), `:848` `load` | `h1.py:660-662` |
| H3 | `experiments/h3.py:673` `junyi.load(...)` | `h3.py:770-772` |
| D71 | `experiments/d71.py:372` `junyi.load(...)` | `d71.py:435-437` |

- `experiments/`, `benchmarks/`, `neuro_model/` da (`.venv` dan tashqari)
  `export_research_data`, `pykt_sequences`, `attempts.csv`, `knowledge_base.json`
  — **0 ta moslik** (grep; testda git kuzatadigan har `experiments/**.py` bo‘yicha).
- `experiments/.venv` da Django yo‘q (`import django` → `ModuleNotFoundError`) —
  pipeline'lar buyruqni hatto chaqira olmaydi; ma’lumot ildizi
  `experiments/datasets/__init__.py:18` `data_root()` (`experiments/data/` yoki
  `NEUROLEARN_DATA`).
- Commit qilingan 28 natija papkasining `provenance.sources` i: `as.csv` (11),
  Junyi ikki fayli (8 + 8), 4 GraphML, Locust generatorlari (3 + 3); daraxt
  benchmark'larida bo‘sh (generatsiya). Eksport papkasidan yoki uning faylidan
  birorta ham manba yo‘q.
- `cdd8826` faqat ikki fayl: eksport buyrug‘i va uning testi.

**Xulosa:** N-1 dissertatsiya natijalarining (H1–H4, D55, D60, D71) hech biriga
ta’sir qilmagan.

## 4. Nuqsonlar

**N-1 (V-E3) — YOPILDI (`cdd8826`), mustaqil tasdiqlandi.** Eksport har talaba
uchun 6 qator yozadi (`PYKT_LINES` + `PYKT_MISSING = "NA"`). Tekshiruvchining
V-E3 testi faylni pyKT 0.0.38 ning o‘z `read_data` si bilan o‘qiydi: xato qatori
yo‘q, talabalar, psevdonimlar va javoblar soni metadata / CSV bilan teng — PASS.
6 qatorli blokka moslashtirilgan tekshiruvchi testlari ham PASS (0-bo‘lim, 1).
Natijalarga ta’siri yo‘q — 3 (k).

**N-2 (V-H1 CSV) — YOPILDI (`3ed55e9`), mustaqil tasdiqlandi.** `measurements.csv`
da `median`, `p95` (katak qiymati, `metrics.json` dagidek), `queries`,
`rows_touched` (har takrorniki). Yangi kichik run'da qiymatlar o‘zim hisoblagan
statistikalarga va `metrics.json` ga mos; eski `csv_rows` bilan test yiqiladi
(0-bo‘lim, 2). Commit qilingan eski natijalar (masalan
`tree-benchmark-quick/20261012-131931`) qayta yozilmagan — ularning CSV'sida
ustunlar yo‘q, bu to‘g‘ri (D48: natija qayta yozilmaydi).

**Ochiq mahsulot nuqsoni: yo‘q.**

## 5. Kuzatuvlar

K-1…K-8 va K-10 `85ac91e` dagidek (fayl tarixida); qisqacha:

- **K-1 (muhim, H1 talqini)** — `pass_mark` bilan taqqoslash teng qamrovda emas
  (τ = 0, “hamma tayyor” qoidasi bilan solishtirish). D71 buni tavsifiy tahlil
  qildi (3 (j)); hukm o‘zgarmagan, dissertatsiyada cheklov sifatida yozilishi kerak.
- **K-2 (H3)** — validatsiya λ ni har joyda gridning pastki cheti 0,25 da tanladi.
  D71 egri chizig‘i: AUC λ bo‘yicha kamayadi, eng yuqorisi λ = 0 (grafsiz); ya’ni
  optimum haqiqatan gridning pastidan tashqarida edi.
- K-3 P(L) = 1.0 amalda yutuvchi; K-4 V-F2 da graf endpoint'i yuk ostida
  o‘lchanmagan; K-5 V-F1 bir martalik holatlarda 12 dan yuqori; K-6 F4/F5 da
  “Test.” qatori yo‘q; K-7 “Bajarildi (kod)” legendada yo‘q; K-8 jadvalda “-0”;
  K-10 muhit (`SECRET_KEY` uzunligi ogohlantirishi, parallel verification
  sessiyalari).

**K-8 (davomi).** D71 H1 jadvalida ham “-0 [-0.002; 0.002]” (k = 5, o‘tish bali;
baho −0,000164) va “0 [-0.002; 0.003]” — D48 bo‘yicha to‘g‘ri, o‘quvchi uchun
belgi va kattalik yo‘qoladi.

**K-9 (yangilandi).** `REMEDIATION_REPORT.md` §8 va QADAM 15 dagi “tuzatishlardan
keyin” verification sonlari (934 passed, 3 failed, 1 xfailed) shu sessiyadan
keyin eskirdi; joriy sonlar 1-bo‘limda. `REMEDIATION_*.md` ga tegilmadi —
yangilash implementatorning ishi.

**K-11 (yangi, D71 matni).** `852e1e3` dagi “r_s(w) AUC'i tasodifiyga yaqin”
k = 3 uchun aniq (CI 0,5 ni o‘z ichiga oladi), k = 5 da CI [0,515; 0,565] 0,5 dan
yuqori — kuchsiz, lekin tasodifiydan farqli. H3 λ egri chizig‘ida λ = 0, 0,1,
0,25 baholari orasidagi farq 0,0001–0,0012, CI'lar to‘liq ustma-ust (bular
juftlanmagan CI'lar, farq CI'si emas): “eng yuqorisi λ = 0” — nuqtaviy baho
bo‘yicha. Ikkalasi ham tavsifiy da’vo, hukm emas; dissertatsiyada shu aniqlik
bilan yozilsin.

**K-12 (yangi).** To‘liq D71 natijalarida `thesis_result = true` — post-hoc
belgisi bilan birga. Rejaga zid emas (reja faqat quick'ni “dissertatsiya natijasi
emas” deydi), lekin o‘quvchi `thesis_result` ni “tasdiqlovchi natija” deb
o‘qimasligi kerak; ma’nosi — “quick emas”.

## 6. II bob ta’riflari va kod orasidagi farqlar (faqat ro‘yxat)

II bob matni repoda yo‘q; solishtirish `NEUROLEARN_REMEDIATION.md` §3, 8-bosqich
matni va qarorlar (D…) bo‘yicha. `85ac91e` dan beri ro‘yxatga ta’sir qiluvchi kod
o‘zgarmagan (0 (e)); D71 yangi farq kiritmaydi (λ egri chizig‘i — tavsifiy,
λ = 0,5 konstantasi o‘zgarmagan).

| # | II bob / spetsifikatsiya | Kodda | Qayerda / qaror |
|---|---|---|---|
| 1 | H1: qoida “birinchi urinish”da tekshiriladi | Voqea — birinchi urinish, lekin muvaffaqiyatsizlik **dastlabki k = 3 javobda** to‘g‘rilar ulushi < 0,5 (k = 5 qo‘shimcha) | `experiments/h1.py:153` (`Event.failed`), D62-5/6 |
| 2 | H1 bajarilganlik: “har bir prerekvizit **savoliga** ≥ 1 javob” | har bir prerekvizit **mashqiga (mavzuga)** ≥ 1 javob | `experiments/h1.py:172`, D61 |
| 3 | H1: ehtimoliy qoida r ≥ τ, teng qamrov | r = min P(L), javobsiz prerekvizit P(L) = 0 — teng qamrov o‘tish bali uchun erishilmaydi (K-1) | D62-4, `readiness.py:79` |
| 4 | H1 qoidalari: 3 ta | + II bobning R (M, δ) va platformaning `earned_proficiency` | D61, D62a(c) |
| 5 | Ma’lumot: DBE-KT22 | **Junyi Academy (2015)** — H1/H3; ASSISTments 2009 — H2 | D61, D53 |
| 6 | ω ∈ (0, 1] har relatsiyada | Junyi'da ω = 1; 3 tugunli SCC bitta mavzuga birlashtirildi | D62-3, D61 |
| 7 | 2.2-tasdiq: G_L siklsiz ⇒ G siklsiz | **Shartli**: sikldagi har tugunda mavzu bo‘lsa | D70, THESIS_MAPPING 10.1a |
| 8 | Algoritm 2.1: Y2 + G_L da BFS | + G = (N, E_P) da y ⇝ x BFS | `neuro_model/graph.py:find_node_cycle_chain`, F7 |
| 9 | θ, P(L) formulalari cheklovsiz | θ ±4 (F1); posterior va P(L)′ clamp (F6) | D6, D65a |
| 10 | Kalibrlash usuli belgilanmagan | chegaralangan grid (4 752 nomzod) | F5, D59 |
| 11 | Har javob yangi dalil | `review_repeat` oynasidagi takror modelni o‘zgartirmaydi | F3, D25 |
| 12 | H3: λ = 0,5 | λ validatsiyada {0,25; 0,50; 0,75} dan; hamma joyda 0,25 (K-2); D71: λ = 0 eng yuqori | D62-10, D61, D71 |
| 13 | H2: talabaning oldingi javoblaridan | D57: qat’iy oldingi **order**lardan; ba’zi modellarda boshqa talabalarning oldingi javoblari ham | D57 |
| 14 | H4: “CTE yozishda tezroq, o‘qishda taqqoslanadigan” | “taqqoslanadigan” = ≤ 1,5× sekin; o‘zgartiruvchi amallar orqaga qaytariladi | D63, D63a |
| 15 | V-E4: `--quick` simulyatsiya ma’lumotida | haqiqiy ma’lumotda, “dissertatsiya natijasi emas” belgisi | D48, D13 |
| 16 | V-F2: lokal, bitta server | gunicorn 8 sync worker | D68a |

## 7. Cheklovlar, N/A va bajarilmaganlar

| Tekshiruv | Holat | Sabab |
|---|---|---|
| **CI masofada** | **ishga tushmagan, tasdiqlanmadi** | Push yo‘q — masofaviy CI bu repo uchun hech qachon ishlamagan. Lokal ekvivalent (backend, experiments, benchmarks, verification, `report_values`) — 1-bo‘lim. Frontend CI (lint, tsc, vitest, build) bu topshiriq ro‘yxatida yo‘q va qayta yugurtirilmadi |
| **Tarixdagi kalit** | ochiq (faqat foydalanuvchi yopadi) | `config/settings.py` dagi literal `SECRET_KEY` `bb80ec4` da (dastlabki commit) qo‘shilgan, `b44df84` da olib tashlangan — git tarixida qoladi, buzilgan deb hisoblanishi kerak. **Qiymat bu hisobotga yozilmadi va ko‘rsatilmadi** (faqat `git log -G` hash'lari va qo‘shilgan / o‘chirilgan qatorlar soni sanaldi). `.env` va `config/.env` hech bir commit'da yo‘q (`git log --all` bo‘sh). Ildiz `.env` dagi token — ochilmadi; bekor qilish foydalanuvchida |
| Locust'ning 2 daqiqalik gunicorn takrori | o‘tkazilmadi | `85ac91e` dagi shart (MemAvailable ≥ 6 GB va swap < 200 MB) bu sessiyada ham bajarilmadi (swap ~0,5 GB ishlatilgan); serverlarga oid kod `85ac91e` dan beri o‘zgarmagan |
| `run_all --quick` (assist09, junyi) | qayta yugurtirilmadi | `run_all.py`, `h1.py`, `h2.py`, `h3.py`, `datasets/` `85ac91e` dan beri o‘zgarmagan (0 (e)); junyi quick o‘sha sessiyada toza klonda rc = 0 |
| Venv'larni lock fayllardan yangidan qurish | qilinmadi | repodagi `venv` va `experiments/.venv` ishlatildi; lock fayllar o‘zgarmagan |
| V-G1, V-G2, V-G3, V-G5, V-G7 | **N/A** | brauzer harness yo‘q; frontend repozitoriydan tashqarida |
| V-G6 | qisman PASS | statik qismi (`test_g_frontend_contract.py`) |
| V-A4 (`mutmut`) | qo‘l mutantlari | 7/7 ushlanadi |
| D71 ni qayta yugurtirish | qilinmadi | ~70 daqiqa; o‘rniga reproduction gate asl natijalardan qayta hisoblandi va pozitsion tekshiruv (3 (j)) |

## 8. Yakuniy hukm — spetsifikatsiyaning 6-bo‘limi

`NEUROLEARN_REMEDIATION.md` §6: “Ish quyidagi barcha shartlar bajarilganda
tugallangan hisoblanadi”.

| Shart | Mustaqil hukm | Dalil (shu sessiyada) |
|---|---|---|
| 4-bo‘limdagi barcha etalon testlar o‘tadi | **bajarildi** | backend suite 1 298 passed, 0 failed; THESIS_MAPPING nomlagan test fayllari uning ichida; verification'ning V-A1 (4-bo‘lim sonlari oracle bilan 1e-3 da) o‘tadi |
| CI ikkala repozitoriyda yashil | **tasdiqlanmadi** | masofaviy CI hech qachon ishga tushmagan (push yo‘q); lokal ekvivalent yashil (1-bo‘lim); frontend CI qayta yugurtirilmadi. So‘zma-so‘z o‘qilishida bajarilmagan |
| “Kechiktirildi” qatorlarining sababi yozilgan | **bajarildi** | 4/4 (va 9/9 “Qisman”); matritsa hisobot bilan bir xil (3 (f)) |
| `run_all.py --quick` va `run_tree_benchmark --quick` toza muhitda xatosiz | **bajarildi** (izoh bilan) | `run_tree_benchmark --quick` — HEAD'da (N-2 dan keyin) verification benchmark test bazasida qayta yugurdi, chiqish katakma-katak tekshirildi; `run_all --dataset junyi --quick` — `85ac91e` sessiyasida toza klonda rc = 0, pipeline kodi o‘shandan beri o‘zgarmagan. Izoh: venv'lar lock fayllardan yangidan qurilmadi; assist09 quick qayta yugurtirilmadi |

**Yakuniy hukm.** Verification spetsifikatsiyasi bo‘yicha **ochiq nuqson yo‘q**:
oldingi hisobotning ikki nuqsoni — N-1 (V-E3, pyKT eksporti) va N-2 (V-H1 CSV) —
tuzatildi va mustaqil tasdiqlandi; ikkalasi ham dissertatsiya natijalariga
ta’sir qilmagan (N-1 uchun fayl:qator bilan — 3 (k); N-2 faqat chiqish shakli).
D71 post-hoc tahlili rejaga muvofiq: reja kod va run'dan oldin commit qilingan,
keyin tahrirlanmagan; natijalar asl H1/H3 ni aynan takrorlaydi, har qiymat o‘z
katagida, post-hoc belgisi bor va hukm yo‘q; D61/D62 hukmlari o‘zgarmagan.
II bob konstantalari, `DEFAULT_GRID` va lock fayllar o‘zgarmagan. Barcha lokal
suite'lar yashil (verification 951 / 0, neural 62 / 0, backend 1 298 / 0, experiments 415 / 0, benchmarks 92 / 0, `report_values` 0 farq).

**6-bo‘limning tugallanganlik mezoni to‘liq bajarilmagan** — to‘rt shartdan
uchtasi mustaqil tasdiqlandi; “CI ikkala repozitoriyda yashil” sharti faqat
lokal ekvivalent bilan qoplangan. Bu push va CI ishga tushirilishi bilan
yopiladi, kod o‘zgarishi talab qilinmaydi. Ikkinchi ochiq masala — tarixdagi
eski `SECRET_KEY` (`bb80ec4`…`b44df84`) va ildiz `.env` dagi token — faqat
foydalanuvchi tomonidan kalitlarni bekor qilish bilan yopiladi. H1 talqini uchun
K-1 va K-11, H3 uchun K-2 muhim.

## 9. Qanday qayta ishga tushirish

```bash
docker compose --env-file config/.env up -d            # Postgres 5433, Redis 6380
scripts/dj5433.sh venv/bin/python -m pytest --ds=verification.settings verification/tests -q -p no:cacheprovider
experiments/.venv/bin/python -m pytest verification/neural -q -p no:cacheprovider
scripts/dj5433.sh venv/bin/python -m pytest -q                       # backend (+ experiments/, benchmarks/ testlari)
experiments/.venv/bin/python -m pytest experiments/tests -q -p no:cacheprovider
experiments/.venv/bin/python -m experiments.report_values --check REMEDIATION_REPORT.md
```

Bir vaqtda ikki `verification/tests` sessiyasi ishga tushirilmasin: test bazasi
nomi qat’iy (`neurolearn_verify`), ikkinchisi birinchisining bazasini o‘chirishga
urinadi.
