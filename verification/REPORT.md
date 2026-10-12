# verification/REPORT.md — mustaqil tekshiruv, 2026-10-12

Tekshiruvchi sessiyasi (D54). Faqat `verification/` ga yozildi; `experiments/`,
`neuro_model/`, backend kodi, `REMEDIATION_PROGRESS.md` va `docs/` ga tegilmadi.
`config/.env` va ildiz `.env` ochilmadi. Uzoq run yo'q edi:
`systemctl --user list-units 'neurolearn-*'` → `0 loaded units`.

Tekshirilgan holat: `e97261e` (branch `thesis-model`), daraxt toza.
Natijalar: H2 `experiments/results/assist09/20261010-060005`,
D55 `experiments/results/assist09-bounds/20261011-183756`.

## 1. Testlar (o'lchangan sonlar)

| Suite | Muhit | Oldin | Keyin |
|---|---|---|---|
| `verification/tests` | `venv` (Django 6.0.5), compose Postgres 5433, `--ds=verification.settings` | 730 passed, **10 failed** | **831 passed, 0 failed** |
| `verification/neural` | `experiments/.venv` (torch 2.5.1+cpu, pykt 0.0.38) | 15 passed | **62 passed, 3 skipped** |
| Backend suite | `venv`, `dj5433` o'rami | 1024 passed / 38 skipped | **1025 passed, 38 skipped**, 13 subtests |

Seed: `verification.settings.VERIFICATION_SEED` = 20261003. `verification/tests`
xdist'siz va `-p no:cacheprovider` bilan ishga tushirildi.

**Ishga tushirish shartlari (yangi, muhim).** `config/settings.py` da
`DEBUG=False` bo'lganda `SECURE_SSL_REDIRECT` sukut bo'yicha yoqiladi, shuning
uchun DRF test client HTTP so'rovlari 301 oladi va `test_e_consent_export.py`
ning 23 testi `setup` da xato beradi. Bu mahsulot nuqsoni emas — CI uslubidagi
o'ram `SECURE_SSL_REDIRECT=False` ni ham qo'yishi kerak. `verification/README.md`
ga yozildi.

## 2. O'nta FAIL: sabab va qaror

| # | Test | Turi | Sabab | Qaror |
|---|---|---|---|---|
| 1 | `test_e_experiments.py::test_d48_the_checker_catches_a_hand_written_number[edit1]` | **stale** | Test `0.684` ni "hech bir metrikaning yaxlitlanmasi emas" deb qattiq yozgan. D59 quick natijasida 0.683667 / 0.683778 / 0.684393 bor, ya'ni 0.684 endi haqiqiy qiymatning yaxlitlanmasi | **Test tuzatildi.** Ekilgan son endi qattiq yozilmaydi: `_unbacked_token()` tekshirilayotgan `metrics.json` ga qarab shu shakldagi (xona soni bir xil) eng birinchi *backing qilinmagan* qiymatni topadi. Parametrlar `graphs`, `assist09-quick`, `assist09`, `assist09-bounds` ga kengaytirildi |
| 2 | `test_e_consent_export.py::test_v_e2_include_simulated_exports_what_the_simulator_wrote` | **stale** (testning o'z xatosi) | Test eksportni `tmp/sim` ga yo'naltirib `tmp/sim/attempts.csv` ni o'qiydi. D44 bo'yicha `--out` berilganda ham papka nomiga `-simulated` qo'shiladi, demak fayl `tmp/sim-simulated/` da. Shu sababli test R2 mezoni (`…with_an_explicit_out_still_marks_the_directory`) bilan ziddiyatda edi — ikkisi bir vaqtda o'tolmasdi | **Test tuzatildi.** Endi yozilgan papka topiladi va nomi aynan `sim-simulated` ekani, `tmp/sim` yaratilmagani tasdiqlanadi; qo'shimcha: haqiqiy hisobning `simulated` qatori hamon eksportda yo'q |
| 3 | `test_e_experiments.py::test_d48_h2_tables_show_each_models_own_numbers` | **stale** | `_h2_results()` ning `assist09*/*/metrics.json` glob'i D55 natijalarini (`assist09-bounds*`) ham oladi; ularda `pooled` bloki yo'q → `KeyError` | **Test tuzatildi va kengaytirildi.** Natijalar `metrics["report"]` bo'yicha ajratiladi (`_results_of("h2")` / `_results_of("h2_bounds")`). D55 uchun **yangi pozitsion tekshiruv** yozildi: §2 (sozlama×model), §3 (farqlar), §4 (DKT/Elo), §5 (darvozalar), §6 (chegaradagi ulushlar) — har katak o'z sozlamasi va modelining yozuviga solishtiriladi |
| 4–8 | `test_na.py::test_pending_stages[3]` … `[7]` | **na-signal** | 3–7-bosqichlar `REMEDIATION_PROGRESS.md` da endi "Bajarildi"; signal aynan shu uchun yoqilgan | **Signal yopildi.** 3–7 `test_implemented_stages` ga ko'chirildi, `test_pending_stages` endi 8, 9, 10 ni kuzatadi. Guruhlar yozildi (3-bo'lim) |
| 9 | `test_na.py::test_na_group_a_student_model_is_not_implemented` | **na-signal** | `neuro_model` da endi `bkt.py`, `irt.py`, `elo.py`, `init.py`, `readiness.py`, `trajectory.py` bor | **A guruhi yozildi** (`test_a_student_model.py`, `test_a_mutation_model.py`); signal o'rniga "A yozilgan" testi (modullar ham, tekshiruv fayllari ham bor) |
| 10 | `test_na.py::test_na_group_c_and_d_readiness_and_trajectory_are_not_implemented` | **na-signal** | `StudentTopicState`, `p_mastery`/`missing_count`/`status` maydonlari va `trajectory`/`path-to` endpoint'lari bor | **C va D guruhlari yozildi** (`test_c_api_scenarios.py`, `test_d_parallel_answers.py`) |

Hech biri **real** turiga kirmadi: o'ntasining ham sababi test tomonida.

## 3. Yangi testlar

| Fayl | Muhit | Testlar | Qamrov |
|---|---|---|---|
| `verification/oracle/model.py` | — | — | §3.3-3.4 formulalarining mustaqil oracle'i (σ, γ, P(G)/P(S), p̂, Bayes, PT, Elo, K(n), P(L0), M, r, Algoritm 2.4) — `neuro_model` dan emas, spetsifikatsiyadan yozilgan |
| `test_a_student_model.py` | `venv` | 15 | **V-A1** 4-bo'limning barcha sonlari 1e-3 da (BKT ketma-ketligi, qiyin/oson/a=0, Elo, P(L0), 0.8921→0.9764 va M ning τ/δ bilan burilishi); **V-A2** 10 000 tasodifiy kirish 1e-9 da + leaf formulalar alohida; **V-A3** chegaralar, 2.5-tasdiq (o'tishdan oldingi posterior), [0,1], θ clamp, a_q=0 ∧ λ=0 ⇒ klassik BKT |
| `test_a_mutation_model.py` | `venv` | 9 | **V-A4** mutatsion test `mutmut` siz: 7 mutant (p̂ yangilanishdan keyin, (1−P(S)) tushib qolgan, PT Bayes'dan oldin, P(S) belgisi, K(n) dagi n, γ ning komplementi, P(L0) cap'i) — hammasi ushlandi; mutatsiya balli **7/7** |
| `test_c_api_scenarios.py` | `venv` + Postgres | 32 | **V-C2** boshlang'ich holatlar va `missing`; **V-C3** ledger'ning har bir ustuni oracle qayta o'ynashi bilan 1e-9 da + p̂ yangilanishdan oldin; **V-C4** 403 va t6 ning uchinchi prerekvizitdan keyin ochilishi; **V-C5** TY5; **V-C6** TY6 (E_L bo'yicha mustaqil sanoq); **V-C7** guruhlar, sabab kodlari, ta'sir 4/3, Need(t7)={t4,t6}; **V-C8** test sessiyasi (`source=test_session`, baho alohida); **V-C9** sun'iy yozuv yo'q; **V-C10** bitta shkala — 6 endpoint bir xil son; **V-C11** 401/403/200; **V-C12** `review_repeat` |
| `test_d_parallel_answers.py` | `venv` + Postgres (`transactional_db`) | 3 | **V-D1** 10 parallel javob: `attempt_no` 1..10 bo'shliqsiz, yakuniy P(L) = ketma-ket qayta o'ynash (oracle bilan), M belgisi, va bir xil savolga 10 parallel javob (1 `adaptive` + 9 `review_repeat`, P(L) bir marta) |
| `test_g_frontend_contract.py` | `venv` | 10 | **V-G6** ning statik qismi: locale fayllari va JSX'da "2PL"/"PROOF"/"70%" yo'q (izohlar hisobga olinmaydi), AI tutor `TUTOR_ENABLED` ortida va sukut bo'yicha o'chiq, komponentlarda o'z τ chegarasi yo'q, 0.95 qattiq yozilmagan; V-G1/G2/G4 uchun kerak `data-testid` hooklar bor; `TopicStatus` aynan API ning 5 holati; `GROUP_ORDER` = A,B,C,D |
| `test_e_results_d58_d59.py` | `venv` | 18 | **D58**: `load_reference` 9 xil buzilgan reference'ni (bounds natijasi, boshqa protokol, quick, boshqa ma'lumot fayli, boshqa seed/fold, commit'siz, iflos daraxt, eski grid) va yo'q papkani rad etadi; commit qilingan D55 run'ining reference'i bugun ham o'tadi. **Natijalar**: `tables.verify` va pozitsion tekshiruv ikkala papkada tekshiruvchi tomonidan chaqirildi (`[]`); `metrics.json` dan tasodifiy 5 qiymat o'z model/sozlama qatorida topildi; barcha provenance commit'lari (`code_commit`, `git_start`, `git_end`, D55 ning reference commit'i) git tarixida `cat-file -t` = commit; papkalar commit qilingan va o'zgarmagan; `env.txt` va `metrics.json` bir xil commit/buyruq/sha256/paketlarni ko'rsatadi |
| `test_d57_order_protocol.py` | `experiments/.venv` | 42 | **D57** 7 modelning har biri uchun perturbatsiya: (a) bir order ichidagi keyingi qatorning javobi o'zgarsa, shu order qatorlarining bashorati bit-aniqligida o'zgarmaydi; (b) oldingi order javobi o'zgarsa, keyingi bashoratlardan kamida bittasi o'zgaradi; (c) oqimdagi oxirgi order o'zgarsa, undan oldingi birorta bashorat o'zgarmaydi (global kauzallik); (d) BKT/DKT/AKT/AKT-R uchun boshqa talabaning javobi hech qachon ta'sir qilmaydi; (e) order'lari uzilgan kirish `OrderSplit` bilan rad etiladi |
| `test_d59_grid_and_akt_r.py` | `experiments/.venv` | 8 | **D59**: `DEFAULT_GRID` aynan D59 yozgan qiymatlar (P0 ga 0.01 va 0.95, PT ga 0.005/0.01/0.02/0.03/0.5; P(G)/P(S) o'zgarmagan; 4752 nomzod), nomzodlar II bob chegaralari ichida, `CONSTANTS` (G_MAX 0.3, S_MAX 0.1, a_q 1, Elo 0.8/0.05, τ 0.95, cap 0.90) o'zgarmagan, kengroq chegarada nomzod soni o'zgarmaydi; **AKT-R** `n_pid > 0` va AKT `n_pid = 0`; `problem_id` almashtirilsa AKT-R bashorati o'zgaradi (max |Δ| > 1e-6), AKT niki bit-aniqligida o'zgarmaydi; ko'rilmagan `problem_id` bitta "noma'lum" indeks (ikki xil yangi item bir xil ball, ma'lum item'dan farqli); AKT-R ning qolgan sozlamalari AKT niki |

## 4. Topilmalar

**Mahsulot nuqsoni topilmadi.** A, C, D guruhlarining barcha yangi tekshiruvlari
va D57/D58/D59 tekshiruvlari implementatsiyaga qarshi o'tdi. Quyidagilar —
kuzatishlar (FAIL emas), ikkitasi hujjatga tegishli.

**K-1 (kuzatuv, test tomonida — tuzatildi).** `test_na.py` ning F guruhi
signali bo'sh edi: u `str(get_resolver().url_patterns)` ichida `"trajectory"`
yo'qligini talab qilardi, lekin yuqori darajada faqat `include()` obyektlari
bo'ladi va ichki marshrut nomi o'sha satrda hech qachon chiqmaydi — shuning
uchun 6-bosqich bajarilgandan keyin ham signal "o'tib" turdi (vacuous).
`verification/tests/test_na.py::test_na_group_f_performance_is_still_unmeasured`
qilib qayta yozildi: endi `reverse("assessments:trajectory")` ishlashini va
`test_f_performance.py` hali yo'qligini tekshiradi. **V-F1/V-F2 hamon
o'lchanmagan** (bu sessiyaning qamrovi A, C/D, G edi), shuning uchun samaradorlik
bo'yicha hech qanday son hisobotga kirmaydi.

**K-2 (kuzatuv, spetsifikatsiya tiliga tegishli).** D57 ning "qator faqat
talabaning oldingi order'laridan bashorat qilinadi" formulasi 7 modelning
4 tasi uchun to'liq to'g'ri (BKT, DKT, AKT, AKT-R), qolgan 3 tasi uchun esa —
BKT+IRT (λ=0), Elo/Rasch, PFA — bashorat **boshqa talabalarning oldingi
javoblariga ham** bog'liq: `b_q` (II bob, §3.3: `b_q −= K(n_q)(x − p)`, bu yerda
`n_q` barcha talabalarning shu item'ga javoblari soni) va PFA ning per-skill
regressiyasi populyatsiya parametrlari. Bu nuqson emas — model aynan shunday
ta'riflangan — lekin "faqat o'z tarixidan" iborasi shu uch model uchun noto'g'ri
o'qiladi. Perturbatsiya testida bu ajratildi: 3 model uchun faqat **global
kauzallik** (keyingi qatorlar ta'sir qilmasligi) talab qilinadi, 4 modeldan esa
to'liq izolyatsiya. Dissertatsiyada protokol tavsifiga shu farq bir jumla bilan
qo'shilsa, da'vo aniq bo'ladi.

**K-3 (kuzatuv, kichik).** `test_na.py` ning eski A signali
`settings.STUDENT_MODEL_ENGINE` ga tayangan edi; bunday sozlama hech qachon
bo'lmagan (dvigatel nomi `assessments/services/student_model.py:50`,
`ENGINE_NAME = "thesis_hybrid"`). Signalning oldingi assert'lari undan oldin
yiqilgani uchun bu ko'rinmay qolgan. Yangi test dvigatel nomini xizmat
modulidan oladi.

**K-4 (kuzatuv, ishga tushirish).** Yuqoridagi `SECURE_SSL_REDIRECT` sharti:
`DEBUG=False` bilan `verification/tests` ning 23 testi 301 sababli xato beradi.
`verification/README.md` ga yozildi.

## 5. Hamon N/A

| Tekshiruv | Holat | Sabab |
|---|---|---|
| V-G1, V-G2, V-G3, V-G5, V-G7 | **N/A** | Brauzer kerak. Frontend checkout'ida (`~/Desktop/neuro/neuro`) Playwright ham, `e2e/` ham yo'q; checkout bu repozitoriydan tashqarida va tekshiruvchi unga yozmaydi. `test_na.py::test_na_group_g_browser_checks_have_no_harness` — harness paydo bo'lganda yiqiladigan signal |
| V-G6 | **qisman PASS** | Statik o'qish bilan qamrab olingani yozildi (3-bo'lim); "profil va xatolar sahifasidagi har bir son API javobida bor" degan qismi brauzersiz to'liq tekshirilmaydi |
| V-F1, V-F2 | **o'lchanmagan** | 6-bosqich bajarilgan, demak endi to'siq yo'q; bu sessiyaning qamrovida emas (K-1) |
| V-A4 (`mutmut`) | **o'rniga qo'l mutantlari** | `mutmut` ning to'liq yugurishi V-A4 bergan 30 daqiqadan uzun; 7 nishonli mutant yozildi, hammasi ushlandi |
| V-E3, V-E4 | **N/A** | 8-bosqich: `experiments/run_all.py` hali yo'q (`test_na_group_e_pipeline_run_all_is_not_implemented`) |
| V-H1 | **N/A** | 9-bosqich: `run_tree_benchmark` buyrug'i yo'q |

## 6. Qanday qayta ishga tushirish

```bash
docker compose --env-file config/.env up -d            # Postgres 5433, Redis 6380
# CI uslubi: env fayl o'qilmaydi, DSN konteyner env'idan
DJANGO_ENV_FILE="" SECRET_KEY=... SECURE_SSL_REDIRECT=False \
  DATABASE_URL="postgres://<user>:<pw>@127.0.0.1:5433/<db>" \
  venv/bin/pytest --ds=verification.settings verification/tests -q -p no:cacheprovider
experiments/.venv/bin/python -m pytest verification/neural -q -p no:cacheprovider
```
