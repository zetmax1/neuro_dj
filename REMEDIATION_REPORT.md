# NeuroLearn — tuzatish va II bob modelini amalga oshirish: yakuniy hisobot (REMEDIATION_REPORT)

Spetsifikatsiya: `NEUROLEARN_REMEDIATION.md` (10-bosqich, 6-bo‘lim). Audit:
`NEUROLEARN_AUDIT.md`. Jarayon jurnali, har bir qaror (D1–D71) va har bir
QADAM: `REMEDIATION_PROGRESS.md`. II bob ↔ kod ↔ test: `docs/THESIS_MAPPING.md`.

Repozitoriylar va branch: backend `~/Desktop/neuro_dj`, frontend
`~/Desktop/neuro/neuro`, ikkalasida `thesis-model`; push qilinmagan.

**Raqamlar haqida (D48).** 6-bo‘limdagi har bir son `experiments/report_values.py`
tomonidan commit qilingan natijaning `metrics.json` idan olinadi va
`tables.fmt` bilan yoziladi. Tekshirish:

```sh
experiments/.venv/bin/python -m experiments.report_values --check REMEDIATION_REPORT.md
```

U blokni natija fayllaridan qayta hosil qilib hujjat bilan belgima-belgi
solishtiradi va har bir sonni o‘z bo‘limining `metrics.json` iga qarshi
tekshiradi (natija 7-bo‘limda).

---

## 1. Holat qisqacha

| Bosqich | Holat |
|---|---|
| 0–7.1 | Bajarildi |
| 8a (rozilik, eksport) | Bajarildi |
| 8b (eksperimentlar: H1, H2, H3) | Bajarildi; DBE-KT22 yuklovchisi va annotatsiya vositasi kechiktirildi (D61) |
| 9 (H4 benchmark) | Bajarildi |
| 10 (sinovlar, samaradorlik, hisobot) | Bajarildi — QADAM 12 va 13 |

Bog‘liqlik matritsasi (2-bo‘lim): **226 Bajarildi, 9 Qisman, 4 Kechiktirildi**,
“Kutilmoqda” qolmadi; har bir Qisman/Kechiktirildi qatorida sabab yozilgan.

---

## 2. Bog‘liqlik matritsasi — yakuniy

Auditdagi har bir topilma bitta qatorda: `Topilma | Vazifa | Holat | Dalil`.
Matritsa `REMEDIATION_PROGRESS.md` dagi bilan bir xil (u yerda yuritiladi).

### 2.1 Bajarilmagan qatorlar va sabablari

| Topilma | Holat va sabab |
|---|---|
| 1.3, 7.3, Q6 — ildizdagi `.env` dagi token | Qisman — fayl gitignored ekani tekshirildi; tokenni bekor qilish faqat foydalanuvchida (3-qoida: fayl ochilmaydi) |
| ES8, “Simulyator generativ emas” | Qisman — natijalar faqat ochiq haqiqiy ma’lumotda (D48); platforma simulyatori generativga qayta yozilmadi, natija uchun ishlatilmaydi (D13); quvur testlari uchun generativ log bor |
| pyKT/pyBKT/DBE-KT22/ASSISTments | Qisman — DBE-KT22 ma’lumoti olinmadi (D61); qolgani bajarildi |
| 7.2 Bundle | Qisman — marshrutlar lazy, lekin `Hero3DBackground` chunk'i 850 kB (> 500 kB) |
| 2.8 Profil | Qisman — hisobni o‘chirish va parol almashtirish UI'si yo‘q (backend bor va testlangan) |
| 2.11 Umumiy UI | Qisman — skrinshot PNG'lari olinmagan (skript tayyor, brauzer va to‘ldirilgan baza foydalanuvchida) |
| DBE-KT22 yuklovchisi | Kechiktirildi — ma’lumot manbasi ochilmadi (ADA kirish so‘rovi javobsiz), o‘rniga Junyi (D61) |
| Annotatsiya vositasi, Cohen κ | Kechiktirildi — ikki mustaqil annotator yo‘q (D61) |
| D26 / 5 — LLM tushuntirishlari | Kechiktirildi — D26 bo‘yicha 10-bosqichdan keyingi alohida bosqich, flag ortida |

### 2.2 To‘liq matritsa

<!-- matrix:start (REMEDIATION_PROGRESS.md dan) -->

Holatlar: **Bajarildi**; **Qisman**; **Kutilmoqda (Bn)** — rejadagi n-bosqichda bajariladi; **Kechiktirildi — sababi**.
Commit qisqartmalari: backend `1d6f286` (repo), `b44df84` (config), `f620171` (auth), `332d56f` (data), `4067215` (docs/CI), `8bc4cea` (addendum), `888a96f` (ledger), `960ba2c` (arxiv); `5e5cb09` (neuro_model), `79b907c` (KB); frontend `a751538`, `6c5a0a7`, `7b549fd` (tutor flag), `2fa1d99` (1-bosqichga moslash), `c259646` (2-bosqichga moslash).

#### 0-bo‘lim (asosiy 5 muammo)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| #1 Test oqimi BKT'ni chetlab o‘tadi, 0–100 shkala | P0-1 (B5, B7) | Bajarildi | Backend: har bir test javobi `apply_one_answer` orqali Algoritm 2.4 dan o‘tadi. UI: mashq va test rejimlari aniq ajratildi, `useAdaptiveQuiz` ulandi, baho va P(L) alohida ko‘rsatiladi (`c2bb542`) |
| #2 KB modeli: MPTT, G_L yo‘q, Y2/Y3, qulf yo‘q | P0-4, P1-6, P1-7 (B2) | Bajarildi | `curriculum/services/kb.py`, `neuro_model/graph.py`, `5e5cb09`, `79b907c`; testlar `test_kb.py`, `test_kb_concurrency.py` |
| #3 Talaba modeli II bobga zid | P0-5 (B3) | Bajarildi | `neuro_model/` (bkt, irt, elo, init, student), `assessments/services/student_model.py`; testlar `neuro_model/tests/test_student.py`, `assessments/tests/test_student_model.py` |
| #4 Unlock 4 xil, global `is_unlocked`, cascade | P0-3, P0-6 (B4), P0-2 (B1) | Bajarildi | Cascade olib tashlandi (`888a96f`); `Topic.is_unlocked` va to‘rt implementatsiya o‘rniga bitta tayyorlik servisi, yopiq mavzu → 403 (D9, `0b15802`) |
| #5 Log yaroqsiz, sun’iy yozuvlar; maxfiy ma’lumotlar repoda | P0-2, P1-1 (B1); P2-1 (B0) | Bajarildi | Maxfiy qism: `config/settings.py:33-60`, README (B0). Log: `assessments/models.py` (`AssessmentAttempt`), `assessments/services/ledger.py`, `888a96f`; testlar `test_ledger.py` |

#### 1-bo‘lim (umumiy tuzilma)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| 1.1 `.idea/` git'da kuzatiladi | B0 repo tozaligi | Bajarildi | `.gitignore`, `1d6f286` |
| 1.1 Bo‘sh `views.py` paketlar bilan to‘sib qo‘yilgan | B0 | Bajarildi | `1d6f286` |
| 1.2 `requirements.txt` to‘liq emas, `Pipfile` nomuvofiq | P2-2, D18 | Bajarildi | `requirements.txt`, `requirements-dev.txt`, `1d6f286`; toza venv tekshiruvi |
| 1.2 django-tree-queries o‘rnatilgan, lekin ishlatilmaydi | P1-6 (B2) | Bajarildi | `curriculum/models.py` (`TreeNode`), migratsiya `0012_kb_enforce`, `79b907c` |
| 1.2 SQLite, PostgreSQL yo‘q | D1 | Bajarildi | `config/settings.py:153-156`, `docker-compose.yml`, `b44df84` |
| 1.2 Redis sozlangan, lekin hech narsa keshlanmaydi | GR1 (B2) | Bajarildi | KB snapshot versiya kaliti bilan keshlanadi: `curriculum/services/graph.py:get_snapshot`, `79b907c` |
| 1.3 Redis bo‘lmasa yozuvdan keyin 500 | B0 | Bajarildi | `config/settings.py:170-185`, `curriculum/views/instructor.py:72-75`; test `test_topic_writes_survive_cache_backend[redis-down]` |
| 1.3 Env o‘zgaruvchilari yo‘q, `.env` ishlatilmaydi | P2-1 | Bajarildi | `config/settings.py:22-27`, `config/.env.example` |
| 1.3 Ildizdagi `.env` da token | 3-qoida, 8.4-Q6 | Qisman — tokenni bekor qilish faqat foydalanuvchi qo‘lida (3-qoida: fayl ochilmaydi) | `.gitignore:13` da borligi tekshirildi |
| 1.3 `docker-compose` yo‘q | D1 | Bajarildi | `docker-compose.yml` |
| 1.3 `@supabase/supabase-js` `package.json` da yo‘q, client ishlatilmaydi | D17 (B7) | Bajarildi | `src/integrations/supabase/` butunlay o‘chirildi; `package.json` da supabase yo‘q (`c2bb542`) |
| 1.5 “updated” kabi commit xabarlari | B0 CI va hujjat | Bajarildi | Yangi commit'lar conventional formatda va ID'lar bilan |
| 1.5 Untracked `.agents/`, `graphify-out/` | 8.4-Q8 | Bajarildi | `.gitignore:23-24` |

#### 2-bo‘lim (backend)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| 2.2 `TopicPrerequisite` da ω yo‘q | BB3 (B2) | Bajarildi | `weight` ∈ (0, 1] + CHECK (`prerequisite_weight_range`), `79b907c` |
| 2.2 `Choice` ≤4 cheklovi `bulk_create` da ishlamaydi | B2 (Y4, import servisi) | Bajarildi | `assessments/models.py:check_choice_limits` (`bulk_create` va `save`), `assessments/services/question_import.py`, `79b907c`; test `test_at_most_four_choices_on_bulk_paths` |
| 2.2 Daraxt MPTT'da | D3, P1-6 (B2) | Bajarildi | MPTT ustunlari olib tashlandi, `mptt` INSTALLED_APPS'dan chiqarildi, `79b907c` |
| 2.2 `orchestrator.py:23` noto‘g‘ri izoh | B0 | Bajarildi | `assessments/services/orchestrator.py:21-24`, `1d6f286` |
| 2.4 Prerekvizit uchun API yo‘q | B2 API | Bajarildi | `/api/curriculum/instructor/prerequisites/` (CRUD, `?expand=leaf`), `/api/curriculum/instructor/kb/warnings/`, `79b907c` |
| 2.4 Graf va shablon AllowAny | D15 | Bajarildi | `curriculum/views/graph.py:34`, `assessments/views/instructor.py:235`, `f620171` |
| 2.4 `learning_path/tree` dagi `mastery_percentage` aslida `score` | D5 (B4) | Bajarildi | Daraxt endi `p_mastery` (P(L)) va `accuracy` ni alohida qaytaradi; aralash shkalali ustun olib tashlandi |
| 2.5 JWT blacklist ishlamaydi | D16 | Bajarildi | `config/settings.py:86`; test `test_rotated_refresh_token_is_blacklisted` |
| 2.5 Rollar nomuvofiq (`Instructor` va `is_staff`) | D15, P2-5 | Bajarildi | Backend `accounts/permissions.py` (`f620171`), `get_role` va admin API (`81f745b`); frontend menyu va marshrutlar `user.role` bo‘yicha (D28, `c2bb542`); testlar `accounts/tests/test_accounts.py` (rollar jadvali, `fbf2f4d`) |
| 2.6 Advisory lock yo‘q | BB9 (B2) | Bajarildi | `pg_advisory_xact_lock(KB_LOCK_KEY)` — `curriculum/services/kb.py:_lock`, `79b907c`; mutatsion tekshiruvli poyga testi |
| 2.6 `SubmitTestSessionView` atomar emas | B5 | Bajarildi | Mantiq `assessments/services/test_session.py` ga ko‘chirildi, `@transaction.atomic`; read-modify-write olib tashlandi — hisoblagichlar `readiness.apply_answer` orqali `select_for_update` bilan siljiydi |
| 2.6 `dashboard.py:66` ortiqcha `atomic` | B5 | Bajarildi | Faqat o‘qiydigan endpoint'dan `@transaction.atomic` olib tashlandi (`analytics/views/dashboard.py`) |
| 2.6 SQLite `FOR UPDATE` ni e’tiborsiz qoldiradi | D1 | Bajarildi | Testlar PostgreSQL'da ishlaydi (`pytest.ini`, CI) |

#### 3-bo‘lim (frontend)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| 3.1 Talaba sahifasi o‘qituvchi endpoint'idan foydalanadi | D15 | Bajarildi | `src/pages/Course.tsx:63-66`, `6c5a0a7` |
| 3.1 `AdminRoute` faqat `is_staff` ni tekshiradi | P2-5 (B7) | Bajarildi | `AdminRoute` o‘rniga `RoleRoute allow={[...]}` — API qaytargan `role` bo‘yicha; `is_staff` bo‘lmagan o‘qituvchi konstruktorga kiradi (`c2bb542`) |
| 3.2 Tokenlar `localStorage` da | D16 (B7) | Bajarildi | Access token faqat xotirada (Zustand), refresh token httpOnly cookie'da; `localStorage` da token yo‘q (`c2bb542`, backend `81f745b`) |
| 3.2 react-query ishlatilmaydi | D19 (B7) | Bajarildi | Barcha data hook'lari `@tanstack/react-query` da (`src/hooks/useLearningData.ts`); bitta so‘rov kaliti — ikki sahifa bir xil javobni o‘qiydi (`c2bb542`) |
| 3.3 Prerekvizit muharriri yo‘q | B7 | Bajarildi | `src/components/instructor/PrerequisiteEditor.tsx` — `onConnect` qirra qo‘shadi, vazn tahrirlanadi, qirra o‘chiriladi, sikl zanjiri qizil, ogohlantirishlar paneli (`c2bb542`) |
| 3.3 `KnowledgeGraph.tsx` o‘lik kod | P2-6 (B7) | Bajarildi | `KnowledgeGraph.tsx`, `QuizEngine.tsx`, `sampleQuestions.ts`, supabase client va 11 ta eskirgan komponent o‘chirildi (`c2bb542`) |
| 3.4 3 ta holat (5 ta kerak) | TR1, TR5 (B7) | Bajarildi | 5 ta holat `src/lib/status.ts` palitrasidan; `CustomTopicNode` endi backend holatini o‘qiydi, `>= 70` taqqoslashi olib tashlandi (`c2bb542`) |
| 3.4 Bir tugun — ikki xil son | D5 (B4, B7) | Bajarildi | Bitta lug‘at: `p_mastery` va `accuracy` — ikkisi ham [0,1], `lib/format` orqali; test bir mavzu to‘rtta sahifada bir xil matn berishini tasdiqlaydi (`c2bb542`) |
| 3.4 Yopiq tugunda umumiy toast | TY4 (B4, B7) | Bajarildi | Yopiq mavzuda yetishmayotgan prerekvizitlar nomi va P(L) bilan ko‘rsatiladi (`MissingPrerequisites`), 403 tanasi shu ro‘yxatni beradi (`c2bb542`) |
| 3.4 Tavsiya sabablari frontend'da qattiq yozilgan | TR3 (B6, B7) | Bajarildi | Sabablar `{code, params}` sifatida keladi va `src/lib/reasons.ts` orqali `uz.json`/`en.json` dan matnga aylanadi (`c2bb542`) |
| 3.4 “0.8%” / “100%” shkala xatosi | D5, P0-1 (B5, B7) | Bajarildi | `lib/format.ts`: `formatProbability` ehtimollik uchun, `formatGrade` foiz uchun. Test “0.8%” va qayta ko‘paytirilgan “100%” xatolarini qotirib qo‘yadi (`c2bb542`) |
| 3.4 `useAdaptiveQuiz` ulanmagan | P0-1 (B7) | Bajarildi | `useAdaptiveQuiz` qayta yozildi va QuizSession'ning mashq rejimiga ulandi; javobdan keyin tushuntirish ekranda qoladi (`c2bb542`) |

#### 4-bo‘lim (algoritmlar)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| 4.1 Sikl tugunlar grafida DFS bilan | BB7, ES1 (B2) | Bajarildi | BFS G_L bo‘yicha (Algoritm 2.1): `neuro_model/graph.py:find_cycle_chain`, `5e5cb09` |
| 4.1 Sikl zanjiri qaytarilmaydi | BB7 (B2) | Bajarildi | 400 javobida `chain`, `chain_names`, `edge`; test `test_cycle_t8_to_t3_is_rejected_with_its_chain` |
| 4.1 Y2 tekshirilmaydi | BB6 (B2) | Bajarildi | `kb.add_prerequisite` va tree o‘zgarishlarida `_check_nesting`, `79b907c`; test `test_b3_to_t6_violates_y2` |
| 4.1 TOCTOU poyga holati | BB9 (B2) | Bajarildi | Advisory lock + lock ostida qayta o‘qish, `79b907c`; `test_kb_concurrency.py` (10 raund) |
| 4.1 `bulk_create`/`update` chetlab o‘tadi | B2 (guard) | Bajarildi | `curriculum/kb_guard.py` + model/queryset guard'lari, `79b907c`; test `test_structural_writes_outside_the_service_are_refused` |
| 4.1 Har bir tugun uchun SQL (N+1) | B2 | Bajarildi | KB bir marta o‘qiladi (2 so‘rov) va xotirada hisoblanadi: `build_snapshot`, `79b907c` |
| 4.2 `InvalidMove` → 500 | BB5, P2-3 (B2) | Bajarildi | Y1 servisda (`move_into_subtree`), `KBError` → 400 (`KBErrorMixin`), `79b907c`; test `test_y1_node_cannot_move_into_its_subtree` |
| 4.2 Tugun o‘chirilsa javoblar CASCADE bilan o‘chadi | D11, P2-8 (B1) | Bajarildi | `PROTECT` (`assessments/models.py`), arxivlash `curriculum/views/instructor.py` (`destroy`), `960ba2c`; test `test_orm_refuses_to_drop_answers`, `test_deleting_an_answered_subtree_archives_it` |
| 4.2 Daraxt o‘zgarganda Y2/Y3 tekshirilmaydi | BB8 (B2) | Bajarildi | `update_node`/`create_node` dan keyin Algoritm 2.2 va Y2, `79b907c`; test `test_moving_t4_into_b3_violates_y2` |
| 4.3 Unlock 4 xil implementatsiya | P0-6 (B4) | Bajarildi | Yagona `assessments/services/readiness.py`; `is_unlocked_dag`, `_unlock_child_topics`, view ichidagi hisoblash va test-sessiya kaskadi olib tashlandi |
| 4.3 Global `Topic.is_unlocked` | D9 (B4) | Bajarildi | `Topic.is_unlocked` ustuni olib tashlandi, migratsiya `curriculum 0014_drop_topic_is_unlocked` |
| 4.3 Ochiq mavzu qayta yopiladi | TY5 (B4) | Bajarildi | TY5 `next_status` dagi `started` tarmog‘i va `state_started_matches_status` DB cheklovi bilan; test `test_ty5_*` |
| 4.3 Yopiq mavzuga javob berish mumkin | D9 (B4) | Bajarildi | `next_question`, `submit_answer`, `test_session` 403 `{missing: [...]}` qaytaradi; test `test_*_refuses_a_closed_topic` |
| 4.3 Chegara 3 joyda har xil | TY1, D6 (B4) | Bajarildi | D6 konstantalari faqat `settings.THESIS_MODEL` da; `MASTERY_THRESHOLD` va eski chegaralar B4 da olib tashlandi (`0b15802`, `config/settings.py:298` izohi) |
| 4.4 BKT parametrlari global | TM1 (B3) | Bajarildi | `TopicModelParams` (P0, PT, G0, S0, `source`); qatori yo‘q mavzu `settings.THESIS_MODEL` standartlarini oladi |
| 4.4 `_retrieve_prior` `algorithm_used` ni filtrlamaydi | B1 | Bajarildi | `_retrieve_prior` o‘chirildi, prior holatdan: `assessments/services/engines/bayesian.py:prior_from_state`, `888a96f`; test `test_hybrid_trace_is_stored_and_prior_comes_from_state` |
| 4.4 Test sessiyasi tarixga yozmaydi | D7 (B5) | Bajarildi | Har bir test javobi `UserKnowledgeHistory` yozadi va `AssessmentAttempt.session` orqali sessiyaga bog‘lanadi |
| 4.4 Tarix attempt'ga FK'siz | B1 | Bajarildi | `UserKnowledgeHistory.attempt` (OneToOne), `888a96f`; eski qatorlar bog‘lanmagan (Q1-10) |
| 4.5 Chiziqli G/S | TM2, ES4 (B3) | Bajarildi | `neuro_model/irt.py` — P(G)=G_MAX·σ(γ_G+a(θ−b)), P(S)=S_MAX·σ(γ_S−a(θ−b)); chiziqli modifier'lar olib tashlandi |
| 4.5 P(G) 0.5 gacha chiqadi | TM2 (B3) | Bajarildi | P(G) < `G_MAX`=0.30 har qanday kirishda; test `test_guess_and_slip_never_exceed_their_bounds` |
| 4.6 θ talaba×mavzu uchun | TM3, ES5 (B3) | Bajarildi | `UserAbility` endi `(user, course)`; eski 6 qator o‘chirildi (D33, migratsiya `0009_student_model`) |
| 4.6 b yangilanmaydi | TM4 (B3) | Bajarildi | `Question.irt_difficulty` har javobda Elo bilan siljiydi; test `test_elo_moves_the_learner_and_the_item` |
| 4.6 K o‘zgarmas | TM4, ES6 (B3) | Bajarildi | `neuro_model/elo.py::k_factor` — K(n)=ELO_ALPHA/(1+ELO_BETA·n); `n_answers` talaba va savol uchun alohida |
| 4.6 θ cheklanmagan | D6 `THETA_CLAMP` (B3) | Bajarildi | `neuro_model/elo.py` θ ni ±`THETA_CLAMP` bilan cheklaydi; farq sifatida `docs/THESIS_MAPPING.md` F1 da qayd etildi |
| 4.6 Tanlash va yangilashda θ nomuvofiq | B3 savol tanlash | Bajarildi | `question_selection.ability_of()` θ ni kursdan oladi — tanlash va Elo bir xil qatorni o‘qiydi |
| 4.6 p̂ saqlanmaydi | TM6, TM7 (B1, B3) | Bajarildi | `AssessmentAttempt.p_hat` va trace maydonlari (`888a96f`); II bob formulasi bilan to‘ldiriladi (B3, `b1d3a08`) |
| 4.7 P(L0) o‘zgarmas 0.15 | TM5 (B3) | Bajarildi | `neuro_model/init.py::initial_mastery` — (1−λ)P0 + λm̄, c = τ − C_OFFSET |
| 4.7 Avlodlarga P=1.0 cascade | P0-2, D8 (B1) | Bajarildi | `_cascade_mastery_to_descendants` o‘chirildi (`888a96f`); test `test_mastering_a_section_does_not_touch_descendants` |
| 4.8 Kahn FIFO, lev yo‘q | GR2 (B2) | Bajarildi | `neuro_model/graph.py:topological_order` (heap, `(pos, id)`, lev), `5e5cb09` |
| 4.8 Sikl qoldig‘i jim qo‘shiladi | GR2 (B2) | Bajarildi | `CycleError(remaining)`, `5e5cb09`; test `test_cycle_error_lists_unordered_topics` |
| 4.8 Tugunlar grafida, G_L'da emas | GR2 (B2) | Bajarildi | `neuro_model/graph.py:expand`, `5e5cb09` |
| 4.8 Faqat testlarda ishlatiladi | B2, B6 | Bajarildi | Snapshot daraxt/graf API, savol tanlash, ledger (`79b907c`) va trayektoriyada (`3add9ef`) |
| 4.9 To‘rtta alohida evristika | TR2, ES7 (B6) | Bajarildi | To‘rtta evristika olib tashlandi; dashboard `trajectory.for_learner` dan foydalanadi, test `test_the_dashboard_reports_the_trajectory_not_four_heuristics` |
| 4.9 Sabablar yo‘q | TR3 (B6) | Bajarildi | Har bir element `{code, params}` qaytaradi (`review_impact`, `in_progress`, `ready`, `blocked`); matn frontend lug‘atida (D20) |
| 4.9 Tartib `position` bo‘yicha | D4 (B2, B6) | Bajarildi | Global `pos` (D4) — snapshot, daraxt API, admin (`79b907c`) va trayektoriya (Algoritm 2.5, `3add9ef`) |
| 4.9 Easy-skip sun’iy yozuvlar | P0-2, D8 (B1) | Bajarildi | `_maybe_skip_easy_questions` o‘chirildi (`888a96f`); testlar `test_easy_skip_probe_writes_only_real_answers`, `test_only_the_ledger_creates_attempts` |

#### 5-bo‘lim (II bob talablari)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| BB1 Kurs→bo‘lim→mavzu, `kind`, pos | B2 | Bajarildi | `TopicKind`, `topic_course_is_root`, `pos`, `79b907c` |
| BB2 Qo‘shni ro‘yxat + CTE | D3, B2 | Bajarildi | django-tree-queries (CTE), `79b907c` |
| BB3 ω vazni | B2 | Bajarildi | `TopicPrerequisite.weight`, G_L vazni = max, `5e5cb09`, `79b907c` |
| BB4 Meros G_L | B2 | Bajarildi | `neuro_model/graph.py:expand`, `?expand=leaf`, `5e5cb09`, `79b907c` |
| BB5 Y1 | B2 | Bajarildi | `kb.update_node` (Y1), `79b907c` |
| BB6 Y2 | B2 | Bajarildi | `neuro_model/graph.py:is_nested`, `5e5cb09` |
| BB7 Y3 BFS + zanjir | B2 | Bajarildi | `find_cycle_chain`, `5e5cb09`; 300 ta tasodifiy brute-force taqqoslash |
| BB8 Daraxt o‘zgarganda tekshiruv | B2 | Bajarildi | Tree o‘zgarishidan keyin Algoritm 2.2 + Y2, `79b907c` |
| BB9 Advisory lock | B2 | Bajarildi | `kb._lock`, `79b907c`; `test_kb_concurrency.py` |
| BB10 Y4 | B2 | Bajarildi | Serializer, import, admin (`Question.clean`), model guard (topic qatori qulflanadi), `79b907c`; test `test_questions_only_on_topics` |
| GR1 Versiyaga bog‘langan kesh | B2 | Bajarildi | `get_snapshot` (versiya kaliti, ikki marta versiya o‘qish), `79b907c` |
| GR2 Kahn + ustuvor navbat + lev + CycleError | B2 | Bajarildi | `topological_order`, `5e5cb09` |
| GR3 Desc*, ortiqcha qirralar, κ | B2 | Bajarildi | `descendant_bitsets`, `redundant_edges`, `order_conflicts`, `5e5cb09`; warnings endpoint `79b907c` |
| TM1 Mavzu bo‘yicha BKT parametrlari | B3 | Bajarildi | `TopicModelParams` + `calibrate_bkt`; standartlar `config/settings.py` |
| TM2 Sigmoid G/S | B3 | Bajarildi | `neuro_model/irt.py`; a_q=0 da P(G)=G0, P(S)=S0 aynan |
| TM3 θ_s kurs bo‘yicha, b_q savol bo‘yicha | B3 | Bajarildi | `UserAbility(user, course)` va `Question.irt_difficulty` |
| TM4 Elo K(n) | B3 | Bajarildi | `neuro_model/elo.py`; `UserAbility.n_answers`, `Question.n_answers` |
| TM5 Prerekvizitli P(L0) | B3 | Bajarildi | `neuro_model/init.py`; etalon 0.636 va 0.35 test sifatida |
| TM6 Algoritm 2.4 tartibi | B3 | Bajarildi | `neuro_model/student.py::observe`; test `test_p_hat_uses_theta_before_not_theta_after` |
| TM7 Log maydonlari | B1 | Bajarildi | Maydonlar va yozish yo‘li (`888a96f`), `kb_version` (B2), II bob qiymatlari (B3, `b1d3a08`), `readiness_score`/`was_ready` (B4, `0b15802`) |
| TY1 Histerezis M (τ, δ) | B4 | Bajarildi | `neuro_model/readiness.py::mastered_flag`; M saqlanadi, chunki band ichida avvalgi qiymatga bog‘liq |
| TY2 R faqat G_L orqali, fallback'siz | B4 | Bajarildi | `Pre(w)` snapshot'ning G_L'idan; ota tugunga fallback yo‘q, test `test_a_mastered_parent_does_not_open_its_child` |
| TY3 `missing_count` hisoblagichi | B4 | Bajarildi | `StudentTopicState.missing_count`, inkremental `propagate`, TY6 uchun `recompute_counters` |
| TY4 r_s(w) + tushuntirish | B4, B7 | Bajarildi | Backend `readiness.readiness_at`, ledger'da `readiness_score`/`was_ready`, 403 tanasi (`0b15802`); UI tushuntirishi (`c2bb542`) |
| TY5 Boshlangan mavzu yopilmaydi | B4 | Bajarildi | `next_status` + DB cheklovi; test `test_ty5_a_new_prerequisite_does_not_close_a_started_topic` |
| TY6 KB versiyasi bo‘yicha qayta hisoblash | B4 | Bajarildi | `StudentTopicState.kb_version` va `readiness.resync` (O(n+m)); test `test_ty6_*` |
| TR1 5 ta holat | B4, B7 | Bajarildi | `TopicStatus` va o‘tishlar (B4, `0b15802`), UI nishonlari `StatusBadge.tsx` (B7, `c2bb542`) |
| TR2 A–D guruhlari | B6 | Bajarildi | `neuro_model/trajectory.py::trajectory`; A — ta’sir ↓ va P ↑, B/C/D topologik tartibda |
| TR3 Sabablar | B6 | Bajarildi | `Reason(code, params)`; test sabab matn emas, kod va sonlar ekanini tasdiqlaydi |
| TR4 Need_s(g) | B6 | Bajarildi | `need` va `path_to`; etalon Need(t7) = {t4, t6}, yo‘l t4 → t6 → t7 |
| TR5 Frontend'da ko‘rsatish | B7 | Bajarildi | `NextStepCard` va `TrajectoryGroups` — A–D guruhlari sabablari bilan bosh sahifada va O‘quv yo‘lida (`c2bb542`) |
| EX1 Anonim pyKT eksporti | B8 | Bajarildi | `manage.py export_research_data` — faqat rozilik bergan, faqat psevdonim, pyKT formati (D42–D45, `dc3c35c`) |
| EX2 Oflayn baholash | B8 | Bajarildi | `experiments/h2.py` va D57 protokoli; natija `assist09/20261010-060005` (8b-2) |
| EX3 Metrikalar | B8 | Bajarildi | `experiments/metrics.py` (AUC, RMSE, accuracy, first-k), 8b |
| EX4 Statistika | B8 | Bajarildi | `experiments/stats.py` — o‘quvchi bo‘yicha klasterlangan bootstrap, DeLong, Holm (8b) |
| EX5 Benchmark | B9 | Bajarildi (kod) | `benchmarks/` app'i: `MpttNode` va `CteNode`, uchta shakl, 10³–10⁵, oltita amal, parallel yozish (qulfsiz va qulfli), Y1 va oraliq tekshiruvlari, `manage.py run_tree_benchmark` (D63, D63a). Natija alohida bazada, D48 verify bilan |
| EX6 Rozilik va anonimlashtirish | B8 | Bajarildi | Rozilik, qaytarib bo‘lmaydigan psevdonim, D11 o‘chirish siyosati (`dc3c35c`); `accounts` testlari (`fbf2f4d`) |
| SN1 Unit testlar | B2–B6, B10 | Bajarildi | II bob algoritmlari uchun unit va etalon testlar (B2–B6), B10 da xossa testlari (`8f1f36f`), `accounts` (`fbf2f4d`), SQL byudjeti (`601cea3`), Locust vositalari (`5ab628e`, `0e424d7`); backend 1 270 test, coverage `neuro_model` 99 %, servislar 97 %, umumiy 90 % (QADAM 12) |
| SN2 Hypothesis | B10 | Bajarildi | `neuro_model/tests/test_properties.py`, `curriculum/tests/test_kb_properties.py` — state machine'lar, 6 ta invariant + rad etilgan amal holatni o‘zgartirmaydi; kiritilgan xatolar 4/4 va 6/6 ushlandi (`8f1f36f`, D65) |
| SN3 Locust | B10 | Bajarildi | `benchmarks/locustfile.py`, `load_test.py`, `seed_load_test` (`5ab628e`, D68); natija `experiments/results/locust/20261020-085406` (50 foydalanuvchi, 0 xato) va post-hoc `085659` (5 foydalanuvchi) (`e836b2f`, `4aee869`). V-F2 mo‘ljali 50 foydalanuvchida bajarilmadi — QADAM 12 |

#### ES (eski muammolar)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| ES1 DFS tugunlar grafida | B2 | Bajarildi | G_L bo‘yicha BFS, `5e5cb09` |
| ES2 θ=0.70 + fallback | B4 | Bajarildi | Qat’iy chegara va fallback olib tashlandi: M — τ/δ gisterezis, meros faqat G_L orqali |
| ES3 MPTT | B2 | Bajarildi | tree-queries, `79b907c` |
| ES4 Chiziqli G/S | B3 | Bajarildi | chiziqli G/S olib tashlandi, o‘rniga chegaralangan sigmoid |
| ES5 θ talaba×mavzu | B3 | Bajarildi | θ endi kurs bo‘yicha (D33) |
| ES6 η=0.3 | B3 | Bajarildi | K(n) = ELO_ALPHA/(1+ELO_BETA·n), o‘zgarmas η emas |
| ES7 Alohida tavsiya funksiyalari | B6 | Bajarildi | Bitta servis (`assessments/services/trajectory.py`); so‘rovlar byudjeti testi har qo‘shimcha mavzuga <0.5 so‘rov |
| ES8 Simulyatsiya va baholash | D13 (B0, B1, B8) | Qisman — eksperimentlar faqat ochiq haqiqiy ma’lumotda (D48); platformadagi `simulate_bkt_data` generativ simulyatorga qayta yozilmadi, natija uchun ishlatilmaydi (D13) | `is_simulated`, `sim-` daraxti (`332d56f`), `source=simulated` (`888a96f`); quvur testlari uchun generativ log `experiments/tests/conftest.py::write_junyi_log` (8b-3) |

#### 6-bo‘lim (eksperimentlarga tayyorlik)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| Logda `topic`, `attempt_no`, p̂ yo‘q | P1-1 (B1) | Bajarildi | `assessments/models.py` (`AssessmentAttempt`), migratsiyalar `0006`–`0008`, `888a96f`; test `test_legacy_rows_are_numbered_and_labelled` |
| Easy-skip yozuvlari belgilanmagan | D8, D10 (B1) | Bajarildi | Mavjud qatorlar `source=legacy` (eksperimentdan chiqariladi), yangi sun’iy yozuvlar yo‘q (`888a96f`) |
| Test sessiyasi yozuvlarida tarix yo‘q | D7 (B5) | Bajarildi | `apply_one_answer` moslashuvchan yo‘l bilan bir xil: trace, tarix va `session` FK |
| Seed vaqt tamg‘alarini qayta yozadi | B1 | Bajarildi | `seed_thesis_demo.py`, `seed_data.py` vaqtni yaratishda beradi, `update()` yo‘q; ledger `update` ni bloklaydi (`888a96f`); test `test_seed_thesis_demo_writes_seed_rows_and_leaves_others_alone` |
| Tugun o‘chirilsa javoblar CASCADE bilan o‘chadi | D11 (B1) | Bajarildi | `960ba2c`; `test_archive.py` |
| Foydalanuvchi hard-delete javoblarni o‘chiradi | D11 (B8) | Bajarildi | D11: `accounts/tasks.py::gdpr_hard_delete_users` — rozilik bor → anonimlashtiriladi, javoblar qoladi; yo‘q → o‘chiriladi (`dc3c35c`, testlar) |
| `seed_data` so‘ramasdan hammasini o‘chiradi | P2-7 | Bajarildi | `curriculum/management/commands/seed_data.py:20-45`; testlar `test_seed_safety.py` |
| `simulate --clear` real akkauntlarni hard-delete qiladi | P2-7, P2-8 | Bajarildi | `assessments/management/commands/simulate_bkt_data.py:52-57` |
| Anonim eksport yo‘q | EX1 (B8) | Bajarildi | EX1 qatori (`dc3c35c`) |
| pyKT/pyBKT/DBE-KT22/ASSISTments yo‘q | EX2 (B8) | Qisman — DBE-KT22 ma’lumoti olinmadi (D61, quyidagi qator); qolgani bajarildi | ASSISTments 2009 (`datasets/assist09.py`, D50), pyKT DKT/AKT/AKT-R va pyBKT cross-check (D53, D59), Junyi (`datasets/junyi.py`, D61) |
| DBE-KT22 yuklovchisi (javoblar bilan) | 8b-3 | **Kechiktirildi — ma’lumot manbasi ochilmadi (D61)** | ADA kirish so‘rovi javobsiz qoldi; o‘rniga Junyi Academy (2015) ishlatiladi (D61, foydalanuvchi ruxsati bilan). DBE-KT22 **grafi** bor va ishlatilgan (`datasets/graphs.py`, D51; `graph_report` ikkala yo‘nalishda). Kod yozilmadi: ma’lumoti yo‘q yuklovchi son chiqarmaydi (D48) |
| Annotatsiya vositasi (`experiments/graphs/annotate.py`), Cohen κ | 8b-3 | **Kechiktirildi — annotator yo‘q (D61)** | Ikki mustaqil annotator yo‘q, shuning uchun κ “hisoblanmadi — annotator yo‘q” bo‘lib qoladi (D13). O‘rniga Junyi ning o‘z annotatsiya fayllari bilan **tavsifiy** moslik yozildi (D61: 1 131 juftlik, AUC 0,6824 / 0,5595) |
| AUC/RMSE/statistika yo‘q | EX3, EX4 (B8) | Bajarildi | EX3, EX4 qatorlari |
| Benchmark zaif | EX5 (B9) | Bajarildi (kod) | Eski `benchmark_tree.py` o‘chirilgan (`5e5cb09`); o‘rniga `benchmarks/` — PostgreSQL, yozish va parallel yozish, mediana va p95, uchta shakl, 10³–10⁵, yaxlitlik tekshiruvlari (D63) |
| Simulyator generativ emas | B8 | Qisman — ES8 qatoridagi sabab: natijalar ochiq ma’lumotda, platforma simulyatori qayta yozilmadi | Generativ log faqat quvur testlari uchun (`experiments/tests/conftest.py::write_junyi_log`) |
| H1 tayyorligi | B1, B4, B8 | Bajarildi | `experiments/h1.py` (8b-3); natija `experiments/results/junyi-h1/20261019-102526` — qo‘llab-quvvatlanmadi (QADAM 10) |
| H2 tayyorligi | B3, B8 | Bajarildi | `experiments/h2.py`, to‘liq natija `experiments/results/assist09/20261010-060005/` (D53, D57, D59); sezgirliklar D55 va D60 |
| H3 tayyorligi | B3, B8 | Bajarildi | `experiments/h3.py` (8b-3); natija `experiments/results/junyi-h3/20261019-122423` — k=3 aniqlanmadi, k=5 qo‘llab-quvvatlanmadi (QADAM 10) |
| H4 tayyorligi | B2, B9 | Bajarildi | `benchmarks/` va `run_tree_benchmark` (D63); to‘liq pass `tree-benchmark/20261016-093916` + D63h qayta o‘lchash — qo‘llab-quvvatlanmadi (QADAM 9, 11) |

#### 7-bo‘lim (testlar va sifat)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| 7.1 `test_test_session.py:140` 100.0 ni tasdiqlaydi | B5 | Bajarildi | Test endi `p_mastery` ∈ [0,1] ni, bahodan farqli bo‘lishini va `rebuild_student_states` natijasiga teng bo‘lishini tekshiradi |
| 7.1 Parallellik testi `OperationalError` ni yutadi | B10 | Bajarildi | Xatoni yutadigan test olib tashlangan (B1); PostgreSQL'da haqiqiy parallellik: `assessments/tests/test_ledger.py:423` (10 ta parallel `process_submission`, V-D1) va `:462`, `curriculum/tests/test_kb_concurrency.py:48`; ular B10 dagi qulf o‘zgarishidan keyin ham o‘tadi (`601cea3`) |
| 7.1 `accounts` testlari yo‘q | B10 | Bajarildi | `accounts/tests/test_accounts.py` (27 test: ro‘yxatdan o‘tish, D15/Q0-6 rollar, rozilik maydonlari, D11, JWT cookie, blacklist, CSRF) + mavjud 60 test = 87; topilgan 500 xatosi tuzatildi (`fbf2f4d`) |
| 7.1 Frontend testi trivial | B7 | Bajarildi | vitest 90 test, 14 fayl (7, 7.1, 8a bosqichlari: `c2bb542`, `02e3b2f`, `3345a52`); QADAM 12 da qayta tekshirildi |
| 7.2 Coverage 68% | B10 | Bajarildi | `.coveragerc` (D67), CI da majburiy: `neuro_model` 99 % (≥ 95), servislar 97 % (≥ 85), umumiy 90 % (≥ 80) (`3e71a32`, QADAM 12) |
| 7.2 Lint 71 error | P2-6 (B7) | Bajarildi | lint: 71 error → **0 error** (8 ogohlantirish qoldi: 7 tasi shadcn `ui/` fayllarida, 1 tasi `AuthContext`) (`c2bb542`) |
| 7.2 tsc 18 xato | P2-6 (B7) | Bajarildi | tsc: 16 xato → **0** (`c2bb542`) |
| 7.2 Bundle 2.36 MB | B7 | Qisman — marshrutlar `React.lazy` da, lekin `Hero3DBackground` chunk'i 850 kB (> 500 kB ogohlantirish); bo‘lish frontend ishi, bu bosqichda tuzatilmadi | Tutor lazy chunk'da (`7b549fd`), `React.lazy` barcha marshrutlarda (`c2bb542`); build natijasi QADAM 12 |
| 7.3 `SECRET_KEY` git'da | P2-1 | Bajarildi | `config/settings.py:35-40`; eski kalit tarixda qoldi (buzilgan deb hisoblanadi) |
| 7.3 `DEBUG=True` | P2-1 | Bajarildi | `config/settings.py:33` |
| 7.3 `ALLOWED_HOSTS=["*"]` | P2-1 | Bajarildi | `config/settings.py:42-45` |
| 7.3 CORS hammaga + credentials | P2-1 | Bajarildi | `config/settings.py:49-51` |
| 7.3 `X_FRAME_OPTIONS="ALLOWALL"` | P2-1 | Bajarildi | `config/settings.py:54`, `config/media.py` |
| 7.3 Demo parollar git'da | P2-1 | Bajarildi | `README.md`, `accounts/demo.py`, `332d56f` |
| 7.3 `.env` dagi token | 3-qoida | Qisman — tokenni bekor qilish faqat foydalanuvchi qo‘lida (3-qoida) | gitignored ekani tekshirildi |
| 7.3 JWT `localStorage` da | D16 (B7) | Bajarildi | D16 bajarildi: refresh token httpOnly cookie'da, access token xotirada, CSRF har bir xavfli so‘rovda (`c2bb542`, backend `81f745b`) |
| 7.3 AllowAny endpoint'lar | D15 | Bajarildi | `f620171`; test `test_anonymous_access_is_rejected` |
| 7.3 Talaba o‘qituvchi endpoint'larini o‘qiydi | D15 | Bajarildi | test `test_student_cannot_read_instructor_endpoints` |
| 7.3 Talaba yopiq mavzuga javob beradi | D9 (B4) | Bajarildi | 403 `{missing: [...]}` uchta endpoint'da; servis `TopicClosed` beradi |
| 7.3 `arms_cache` git'da | B0 | Bajarildi | frontend `a751538` |
| 7.4 `TestsListView` N+1 | P2-4 (B5) | Bajarildi | Bitta agregat so‘rov (`Count`, `Sum` mavzu bo‘yicha) + `select_related("parent")`; test `TestsListQueryBudget` har bir qo‘shimcha mavzuga <1 so‘rov ekanini tasdiqlaydi |
| 7.4 Sikl DFS N+1 | P2-4 (B2) | Bajarildi | Tekshiruv xotiradagi snapshot ustida, `5e5cb09`, `79b907c` |
| 7.4 Easy-skip N+1 | D8 (B1) | Bajarildi | Funksiya o‘chirildi (`888a96f`) |
| 7.4 `SubmitTestSession` N+1 | P2-4 (B5) | Bajarildi | `resolve_paper` butun varaqni 2 so‘rovda yuklaydi; test `test_loading_the_paper_is_two_queries_whatever_its_length` |
| 7.4 Keshlanmagan qayta hisoblashlar | GR1 (B2) | Bajarildi | Versiya kaliti bilan kesh, `79b907c` |
| 7.4 Bir javobga 12–20 SQL | B10 (byudjet ≤ 12) | Bajarildi | Oddiy javob 25 → 12, M o‘zgarishi 26 → 12, `review_repeat` 16 → 8; byudjet testda qat’iy (`assessments/tests/test_query_budget.py`, `601cea3`, `eae1025`, D66, D66a) |

#### 8.3 (ustuvorliklar ro‘yxati)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| P0-1 Test sessiyasi BKT'ni chetlab o‘tadi | B5, B7 | Bajarildi | Backend D7: javoblar model orqali, baho `TestSessionResult` da (`620d4e1`); UI `assessment.api.ts` orqali (`c2bb542`) |
| P0-2 Cascade va easy-skip | B1 | Bajarildi | `888a96f`; `test_ledger.py` |
| P0-3 Talabaga xos tayyorlik | B4 | Bajarildi | `StudentTopicState` (user, topic) va `assessments/services/readiness.py` |
| P0-4 G_L, Y2, Y3, qulf | B2 | Bajarildi | `5e5cb09`, `79b907c` |
| P0-5 Talaba modeli | B3 | Bajarildi | `neuro_model/` + `assessments/services/student_model.py`, yagona dvigatel `thesis_hybrid/1` |
| P0-6 Yagona unlock servisi | B4 | Bajarildi | Yagona servis; to‘rtta eski implementatsiya olib tashlandi |
| P1-1 Logni kengaytirish | B1 | Bajarildi | `888a96f`; `test_ledger.py`, `test_ledger_migration.py` |
| P1-2 pyKT eksporti, rozilik | B8 | Bajarildi | EX1, EX6 qatorlari (`dc3c35c`) |
| P1-3 Oflayn baholash | B8 | Bajarildi | EX2 qatori |
| P1-4 Metrikalar va statistika | B8 | Bajarildi | EX3, EX4 qatorlari |
| P1-5 Benchmark | B9 | Bajarildi | H4 tayyorligi qatori (`68acf4e` … `ed45931`) |
| P1-6 tree-queries'ga ko‘chirish | B2 | Bajarildi | `79b907c` |
| P1-7 Kahn, Desc*, κ, kesh | B2 | Bajarildi | `5e5cb09`, `79b907c` |
| P1-8 Trayektoriya | B6, B7 | Bajarildi | Algoritm 2.5 va API (`3add9ef`), UI (`c2bb542`) |
| P1-9 Hypothesis va Locust | B10 | Bajarildi | SN2 va SN3 qatorlari (`8f1f36f`, `5ab628e`, `e836b2f`) |
| P2-1 Maxfiy qiymatlar va xavfsizlik sozlamalari | B0 | Bajarildi | `b44df84`, `332d56f` |
| P2-2 Requirements sinxronligi | B0 | Bajarildi | `1d6f286` |
| P2-3 `InvalidMove` → 400, Redis chidamliligi, prerekvizit API | B0 (Redis), B2 | Bajarildi | Redis (`b44df84`, `f620171`); Y1/400 va prerekvizit API (`79b907c`) |
| P2-4 N+1 | B2, B5, B10 | Bajarildi | Sikl tekshiruvi N+1 yo‘q (`79b907c`); `TestsListView`, `SubmitTestSession` — B5; `trajectory` so‘rovlari mavzu soniga bog‘liq emas (`test_trajectory.py`), `submit_answer` dagi qayta o‘qishlar olib tashlandi va sonlar qotirildi (`601cea3`) |
| P2-5 Rollarni bir xil qilish | B0 (backend), B7 (frontend) | Bajarildi | `accounts/permissions.py` (`f620171`), frontend D28 (`c2bb542`), rollar jadvali testi (`fbf2f4d`) |
| P2-6 Frontend lint/tsc, o‘lik kod | B7 | Bajarildi | lint 0 error, tsc 0 (`c2bb542`; QADAM 12 da qayta tekshirildi) |
| P2-7 Xavfli seed buyruqlari | B0 | Bajarildi | `332d56f` |
| P2-8 CASCADE va hard-delete | B0 (simulator), B1, 8a | Bajarildi | `simulate --clear` cheklandi (`332d56f`); PROTECT va arxivlash (`888a96f`, `960ba2c`); hard-delete siyosati D11 bo‘yicha: rozilik bo‘lsa javoblar psevdonim bilan qoladi, aks holda o‘chiriladi (`accounts/tasks.py`, `CustomUser.anonymise`, `dc3c35c`) |

#### 8.4 (javob topilmagan savollar)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| Q1 Natijalar qaysi ma’lumotdan? | D13 | Bajarildi (qaror) | D13: simulyatsiya hech qachon natija uchun ishlatilmaydi |
| Q2 `db.sqlite3` da real ma’lumot bormi? | 2-qoida | Bajarildi (qaror) | Bor deb hisoblanadi; zaxira olindi, hisobotga faqat qatorlar soni chiqarildi |
| Q3 PostgreSQL | D1 | Bajarildi | `docker-compose.yml`, `b44df84` |
| Q4 Kurs modeli | D2 (B2) | Bajarildi | Kurs = ildiz (`kind=course`), `79b907c`; θ kurs bo‘yicha — B3 |
| Q5 α, β, λ va parametrlar manbasi | D6, `calibrate_bkt` (B3) | Bajarildi | Konstantalar `config/settings.py` `THESIS_MODEL`; kalibrlash `calibrate_bkt` (grid search, ixtiyoriy pyBKT) |
| Q6 `.env` dagi token | 3-qoida | Qisman — tokenni bekor qilish faqat foydalanuvchi qo‘lida (3-qoida) | Fayl gitignored |
| Q7 `token_blacklist` | D16 | Bajarildi | `config/settings.py:86`, test |
| Q8 `graphify-out/`, `.agents/` | B0 | Bajarildi | `.gitignore` (kuzatilmaydi) |

#### UI qo‘shimchasi (`NEUROLEARN_UI_ADDENDUM.md`, D20–D29)

Addendum `NEUROLEARN_REMEDIATION.md` ning bir qismi (`8bc4cea`). UI masalalarida u ustun; model, formulalar va algoritmlar (3–4-bo‘limlar) o‘zgarmaydi.

**4-bo‘lim: backend ishlari bosqichlar bo‘yicha**

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| A4-1 `source` enum'ida `review_repeat` | B1 | Bajarildi | `assessments/models.py` (`AttemptSource`), `assessments/services/ledger.py:classify_source`, `888a96f`; testlar `test_repeat_within_window_is_logged_but_changes_nothing`, `test_repeat_after_window_is_a_normal_answer` |
| A4-2 Graf API: daraxt (`kind`, `pos`, `lev`) | B2 | Bajarildi | `curriculum/views/graph.py` (`nodes[].data.kind/pos/lev`, `leaf_edges`, `edges`, `warnings`), `79b907c`; test `test_graph_endpoint_response_format` |
| A4-3 Graf API: G_L qirralari `inherited` belgisi va ularni hosil qilgan E_P id'si bilan | B2 | Bajarildi | `curriculum/views/graph.py` (`nodes[].data.kind/pos/lev`, `leaf_edges`, `edges`, `warnings`), `79b907c`; test `test_graph_endpoint_response_format` |
| A4-4 Graf API: o‘qituvchi kiritgan E_P qirralari alohida | B2 | Bajarildi | `curriculum/views/graph.py` (`nodes[].data.kind/pos/lev`, `leaf_edges`, `edges`, `warnings`), `79b907c`; test `test_graph_endpoint_response_format` |
| A4-5 Graf API: ogohlantirishlar (ortiqcha qirralar, κ) | B2 | Bajarildi | `curriculum/views/graph.py` (`nodes[].data.kind/pos/lev`, `leaf_edges`, `edges`, `warnings`), `79b907c`; test `test_graph_endpoint_response_format` |
| A4-6 Mavzu holatlari va P(L) | B4 | Bajarildi | Daraxt, DAG, dashboard, testlar ro‘yxati va `knowledge_states` bir xil `p_mastery`/`accuracy`/`status` qaytaradi |
| A4-7 Bo‘lim va kurslar uchun `mastered/total` (D22) | B4 | Bajarildi | Backend: bo‘lim/kursda holat qatori yo‘q (D22, `0b15802`); UI `MasteryRatio.tsx` — `k / n` (`c2bb542`) |
| A4-8 Yopiq mavzuning yetishmayotgan prerekvizitlari | B4 | Bajarildi | 403 tanasi `{missing: [{topic_id, name, p_mastery}]}`, `pos` bo‘yicha tartiblangan |
| A4-9 `GET /api/learning/mistakes/` (D25) | B6 | Bajarildi | `MistakesView` — mavzular bo‘yicha guruhlangan, tanlangan va to‘g‘ri variant, tushuntirish, sana, keyinroq to‘g‘ri yechilgani; “ko‘rib chiqilgan” belgisi `MistakeReview` da (ledger o‘zgarmas), o‘chirish yo‘q |
| A4-10 `GET /api/me/summary/` (D27) | B6 | Bajarildi | `MeSummaryView` — kurs bo‘yicha k/n va θ, urinishlar, aniqlik, takrorlash soni, haftalik faollik javob vaqtlaridan. XP/achievements/study_hours yo‘q (D27) |
| A4-11 `GET /api/config/model/` (D29) | B6 | Bajarildi | `ModelConfigView` — τ, δ, G_MAX, S_MAX, a_q, Elo, λ, c, clamp, standartlar, holatlar va trayektoriya guruhlari |
| A4-12 `GET /api/learning/topics/<id>/history/` — p̂, P(G), P(S), p_before, p_after, natija, vaqt | B6 | Bajarildi | `TopicHistoryView` — har bir urinish uchun p̂, P(G), P(S), P(L) oldin→keyin, θ va b oldin→keyin, tayyorlik, natija, vaqt; qiymatlar ledger'dan (qayta hisoblanmaydi) |
| A4-13 `PATCH /api/me/consent/` | B8 → 8a | Bajarildi | `accounts/views.py` (`ResearchConsentView`), `config/urls.py`; alohida endpoint — rozilik profil tahririning yon ta'siri bo'lmasligi uchun; `research_consent_at` ikki tomonga ham qo'yiladi (`dc3c35c`); test `accounts/tests/test_research_consent.py` |

**1-bo‘lim: qarorlar**

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| D20 Til: o‘zbek (lotin) asosiy, `react-i18next`, `uz.json`/`en.json`, atamalar va bosh harf qoidasi | B7 | Bajarildi | `react-i18next`, `src/locales/uz.json` va `en.json` — 321 kalit, parite test bilan majburlangan; gap ichida faqat birinchi harf katta qoidasi ham test bilan (`c2bb542`) |
| D21 Holatlar palitrasi `src/lib/status.ts`, WCAG AA | B7 | Bajarildi | `src/lib/status.ts` — yagona palitra; yopiq matn slate-700 (WCAG AA), avval o‘qilmas darajada och edi (`c2bb542`) |
| D22 Holat faqat `topic` turida, bo‘lim/kurs — `k / n` | B2 (`kind`), B4 (backend), B7 (UI) | Bajarildi | `kind` (`79b907c`), holatlar (`0b15802`), UI `StatusBadge.tsx`/`MasteryRatio.tsx` (`c2bb542`) |
| D23 Soxta ma’lumot yo‘q, har bir son API'dan | B6 (endpoint'lar), B7 (grep), 7.1 (D40) | Bajarildi | Profil, xatolar, heatmap va qidiruv sahifasidagi soxta massivlar olib tashlandi; `grep` toza, buni test ham tekshiradi (`c2bb542`). Qidiruv `GET /api/learning/search/` ustida qaytdi: nomlar bilimlar bazasidan, holat va P(L) talaba holatidan, bo‘lmagan qiymat `null` (D40, `f7bd3af`, `02e3b2f`) |
| D24 `VITE_ENABLE_TUTOR=false`, menyuda yo‘q | B7 | Bajarildi | `src/lib/features.ts`, `src/App.tsx`, `src/components/layout/Header.tsx`, `7b549fd`; test `src/lib/features.test.ts` |
| D25 Xatolar backend'dan, “Qayta yechish”, `review_repeat` | B1 (ledger), B6 (endpoint), B7 (UI, `mistakeStorage` olib tashlash) | Bajarildi | Ledger va `review_repeat` (`888a96f`), `GET /api/learning/mistakes/` (`3add9ef`), UI (`c2bb542`); oynadagi savollar oxirida (`question_selection.py`) |
| D26 LLM tushuntirishlari hozir amalga oshirilmaydi, faqat `Question.explanation` | — | Kechiktirildi — D26 bo‘yicha 8–10-bosqichlardan keyingi alohida bosqich (dizayn 5-bo‘limda) | Hozir tushuntirish manbai faqat `Question.explanation` |
| D27 Profil haqiqiy ma’lumotda (`/api/me/summary/`) | B6, B7 | Bajarildi | Profil `GET /api/me/summary/` dan; XP, achievements va “study hours” olib tashlandi — ularni haqiqiy ma’lumotdan hisoblab bo‘lmaydi (`c2bb542`) |
| D28 Menyu rolga qarab | B7 | Bajarildi | Menyu `user.role` bo‘yicha: talaba 4 band, o‘qituvchi + konstruktor, admin + foydalanuvchilar. “Kurslar” va “Qidiruv” sahifalari olib tashlandi (`c2bb542`); qidiruv 7.1 da yuqori panelga panel sifatida qaytdi, sahifa sifatida emas (D40) |
| D29 Noto‘g‘ri da’volar olib tashlanadi, konstantalar `GET /api/config/model/` dan | B6, B7 | Bajarildi | “2PL”, “PROOF”, “70%”, “dynamically match” yo‘q (test tekshiradi); τ `GET /api/config/model/` dan; savol modeli “Rasch (a = 1)” (`c2bb542`) |

**2–3-bo‘limlar: sahifalar va qabul shartlari (7-bosqich)**

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| 2.1 Bosh sahifa: KPI'lar, “Keyingi qadam” (A–D), holatlar issiqlik xaritasi | B6, B7 | Bajarildi | 4 ta KPI (o‘zlashtirilgan k/n, takrorlash, ochiq, 7 kundagi javoblar); streak va “weekly goal” olib tashlandi; “Keyingi qadam” A–D; heatmap holatlar to‘ri (`c2bb542`) |
| 2.2 O‘quv yo‘li: “Ikki qatlam” rejimi, `lev`/`pos` joylashuvi, yon panel, Need(g) yo‘li, legenda | B2, B4, B6, B7 | Bajarildi | “Ikki qatlam” standart rejim (ramkalar + ichidagi mavzular), DAG `lev` ustunlari `pos` tartibida, yon panel, Need(g) ajratib ko‘rsatish, legenda (`c2bb542`) |
| 2.3 Mashq va testlar: ikki rejim, yopiq karta va 403, qiyinlik o‘rtacha b dan | B4, B7 | Bajarildi | Ikki rejim alohida kartada; yopiq karta faol emas va yetishmayotganini aytadi; doimiy “Medium” nishoni olib tashlandi, qiyinlik o‘rtacha b dan; filtr holat bo‘yicha (`c2bb542`) |
| 2.4 Kurslar sahifasi O‘quv yo‘liga birlashadi | B7 | Bajarildi | `pages/Courses.tsx` o‘chirildi, menyudan olib tashlandi; kurslar ro‘yxati O‘quv yo‘lida va bosh sahifadagi bilim xaritasida (`c2bb542`) |
| 2.5 Mavzu sahifasi: “Qanday hisoblandi” paneli (τ, urinishlar jadvali, Rasch) | B6 (history), B7 | Bajarildi | `components/topic/DiagnosticsPanel.tsx` — τ chizig‘i, urinishlar jadvali (p̂, P(G), P(S), P(L) oldin→keyin), θ kurs bo‘yicha, “Rasch (a = 1)” (`c2bb542`) |
| 2.6 Kurs konstruktori: outline + muharrir, prerekvizit muharriri, sikl/Y2/κ ko‘rsatish | B2, B7, 7.1 (D39) | Bajarildi | Prerekvizit muharriri: konstruktorning 5-qadami — React Flow, meros qirralari uzuq va faqat o‘qish, sikl zanjiri qizil, κ va ortiqcha qirralar paneli (`c2bb542`). Outline + muharrir: `CourseStructureEditor` — chapda daraxt, o‘ngda tugun muharriri, tur va tartib, prerekvizitlar alohida yorliq (D39, `02e3b2f`); backend — `kb.reorder_sibling`, `topics/<id>/reorder/`, `question_count`/`child_count` (`f7bd3af`) |
| 2.7 Foydalanuvchilar: email prefiksi, rol filtri, simulyatsiya nishoni, faolsizlantirish, rozilik ustuni | B7, 8a | Bajarildi | Email prefiksi, rol filtri va berish, simulyatsiya nishoni va yashirish, faolsizlantirish (`c2bb542`). Rozilik ustuni va `?consent=` filtri — faqat o'qish uchun, chunki boshqa birov nomidan belgilanadigan rozilik rozilik emas (`dc3c35c`, `3345a52`) |
| 2.8 Profil: real ma’lumot, rozilik, hisobni o‘chirish, parol | B6, B7, 8a | Qisman — hisobni o‘chirish va parolni almashtirish interfeysi yo‘q (D42–D45 ga kirmaydi); backend `DELETE /api/accounts/profile/` bor va testlangan (`fbf2f4d`) | Real ma'lumot `GET /api/me/summary/` (`c2bb542`); rozilik kartasi (`3345a52`) |
| 2.9 Quiz: test natijasi (P(L) oldin → keyin, ochilgan mavzular), mashq rejimi, klaviatura | B5, B7 | Bajarildi | Test natijasida baho va model holati alohida; mashq rejimi bir vaqtda bitta savol, darhol tushuntirish, holat o‘zgarsa toast; klaviatura A–D va Enter (`c2bb542`) |
| 2.10 Xatolar ustida ishlash: `GET /api/learning/mistakes/`, guruhlash, “ko‘rib chiqilgan” belgisi | B6, B7 | Bajarildi | `MistakesView` va `MistakeReview` (`3add9ef`); sahifa mavzular bo‘yicha guruhlangan, “tozalash” tugmasi yo‘q, faqat “ko‘rib chiqildi” belgisi (`c2bb542`) |
| 2.11 Umumiy: loading/bo‘sh/xato holatlari, konsol, responsive, `React.lazy`, `data-testid`, `docs/ui/` skrinshotlari | B7, 7.1 (D41) | Qisman — skrinshot PNG'lari olinmagan: brauzer va to‘ldirilgan baza foydalanuvchi mashinasida (`scripts/screenshots.mjs` tayyor) | loading/bo‘sh/xato holatlari, `React.lazy`, `data-testid` (`c2bb542`); `scripts/screenshots.mjs`, `docs/ui/README.md` (D41, `02e3b2f`, `f7bd3af`) |
| 3 Qabul: mock massivlar yo‘q; bir mavzu barcha sahifalarda bir xil holat va P(L) (vitest/Playwright); “2PL”, “PROOF”, “70%”, “dynamically match” matnlari yo‘q | B7 | Bajarildi | Mock massivlar yo‘q; bir mavzu to‘rtta sahifada bir xil holat va P(L) — `src/test/one-vocabulary.test.tsx`; taqiqlangan matnlar yo‘q (`c2bb542`) |
| 5 LLM tushuntirishlari dizayni (o‘qituvchi tasdiqlaydi, kesh, eksperimentga ta’sir nazorati) | — | Kechiktirildi — D26: 8–10-bosqichlardan keyin, flag ortida | — |

<!-- matrix:end -->

---

## 3. Natijalarni qayta hosil qilish

Har bir natija o‘z `env.txt`/`metrics.json` idagi commit va buyruq bilan
qayta hosil qilinadi: `git checkout <commit>`, so‘ng buyruq. Ma’lumot fayllari
repoda yo‘q (D49): `experiments/data/` (yoki `NEUROLEARN_DATA`), sha256'lari
`metrics.json` ning `sources` / `dataset` qismida. Muhit: `experiments/README.md`
“Muhitni tiklash” (lock fayllar). Postgres buyruqlari `scripts/dj5433.sh`
orqali (`config/.env` ochilmaydi).

| Natija papkasi (`experiments/results/`) | Commit | Toza | Buyruq |
|---|---|---|---|
| `assist09/20261010-060005` (H2) | `66ff452` | ha | `experiments/.venv/bin/python -m experiments.h2` |
| `assist09-bounds/20261011-183756` (D55) | `30ad4e4` | ha | `experiments/.venv/bin/python -m experiments.h2_bounds --reference experiments/results/assist09/20261010-060005 --workers 4` |
| `assist09-frozen/20261012-063439` (D60) | `244f046` | ha | `experiments/.venv/bin/python -m experiments.h2_frozen --reference experiments/results/assist09/20261010-060005 --workers 4` |
| `junyi-h1/20261019-102526` (H1) | `2500c77` | ha | `experiments/.venv/bin/python -m experiments.h1 --workers 5` |
| `junyi-h3/20261019-122423` (H3) | `2500c77` | boshida commit qilinmagan H1 papkasi bor edi (D64 bilan qabul qilingan) | `experiments/.venv/bin/python -m experiments.h3 --workers 5` |
| `junyi-h1-posthoc/20261020-180934` (D71, post-hoc) | `c1ad4a9` | ha | `experiments/.venv/bin/python -m experiments.d71 --workers 5` (bitta buyruq ikkala papkani yozadi) |
| `junyi-h3-lambda/20261020-180934` (D71, post-hoc) | `c1ad4a9` | ha | o‘sha |
| `graphs/20261006-052348` (D52) | `c1a683b` | ha | `experiments/.venv/bin/python -m experiments.graph_report` |
| `tree-benchmark/20261016-093916` (H4) | `b8d6b3a` | ha | `scripts/dj5433.sh venv/bin/python manage.py run_tree_benchmark --database benchmark --shapes course_like,deep_chain,random --warmups 5 --repeats 30 --timeout 120.0 --parallel-repeats 3 --seed 20261006 --memory-limit-gb 8.0` |
| `tree-benchmark/20261019-161430` (D63h) | `9f97aa7` | ha | o‘sha, `--only-parallel --shapes course_like,random` |
| `tree-benchmark/20261019-163435` (D63h) | `9f97aa7` | ha | o‘sha, `--only-parallel --shapes deep_chain --sizes 1000,10000` |
| `tree-benchmark/20261020-050428` (D63h) | `9f97aa7` | ha | o‘sha, `--shapes deep_chain --sizes 100000` |
| `locust/20261020-100901` (V-F2, asosiy) | `8f58a42` | ha | `scripts/dj5433.sh venv/bin/python -m benchmarks.load_test --workers 8` |
| `locust/20261020-085406` (runserver, qo‘shimcha) | `0e424d7` | ha | `scripts/dj5433.sh venv/bin/python -m benchmarks.load_test` (o‘sha commit'da standart server `runserver` edi; hozir `--server runserver`) |
| `locust/20261020-085659` (runserver, post-hoc) | `e836b2f` | ha | o‘sha, `--users 5` |

Tekshiruvlar (natija emas): `experiments/.venv/bin/python -m experiments.clamp_count`
(D65a, bit-aniq), `scripts/dj5433.sh venv/bin/python -m pytest assessments/tests/test_answer_path_golden.py`
(D66a oltin eksport), `scripts/dj5433.sh venv/bin/python -m pytest assessments/tests/test_query_budget.py`
(V-F1).

---

## 4. Qolgan xavflar

1. **O‘lchovlar bitta mashinada.** H4 va Locust vaqtlari i7-11800H,
   `powersave` governor, lokal Postgres; boshqa mashinada absolyut sonlar
   o‘zgaradi. Da’volar nisbat (ρ) va CI ga qurilgan; Locust uchun ikki server
   (runserver/gunicorn) orasidagi farq qayd etilgan.
2. **H2 da Elo/Rasch hammadan yuqori** (6-bo‘lim). BKT+IRT ning da’volari
   (D53, D56) bajarilgan, lekin eng oddiy θ/b modeli undan yaxshi — talqinda
   hisobga olinishi kerak.
3. **H1 va H3 qo‘llab-quvvatlanmadi / aniqlanmadi.** Junyi platformasi mashqni
   prerekvizitlardan keyin tavsiya qiladi (`suggested`), shuning uchun
   graf ta’sirining bir qismi platforma yo‘naltirishidan bo‘lishi mumkin (D62a).
   **D71 (post-hoc, tavsifiy; hukmlar o‘zgarmaydi):** H1 da o‘tish bali bilan
   taqqoslash teng qamrovda emas edi (javobsiz prerekvizit r = 0 ⇒ τ = 0);
   barcha prerekvizitlari ishlangan voqealarda ehtimoliy qoida o‘tish bali va
   `earned_proficiency` dan farq qilmaydi, r_s(w) ning AUC'i tasodifiyga yaqin.
   H3 da asl graf bilan AUC λ oshgan sari kamayadi, eng yuqorisi λ = 0 da.
   Jadvallar — `junyi-h1-posthoc/20261020-180934` va `junyi-h3-lambda/20261020-180934`
   ning `tables.md` sida.
4. **Junyi parametrlari saqlanmagan** — taqsimotni berib bo‘lmaydi, D65a
   bo‘yicha qayta o‘ynalmadi (analitik chegara bilan).
5. **P(L) = 1.0 yutuvchi holat** (D65a): 1 − ε chegarasi qo‘shilmadi;
   uzoq to‘g‘ri javoblar seriyasidan keyin noto‘g‘ri javob P(L) ni tushirmaydi.
6. **2.2-tasdiq tuzatildi (D70):** shartsiz ifoda bo‘sh tugunlarda noto‘g‘ri;
   dissertatsiyada shartli ifoda (sikldagi har tugunda mavzu bor) va Algoritm 2.1
   ning tugunlar grafidagi tekshiruvi (F7) yozilishi kerak. 2.1–2.6 xaritasi —
   `docs/THESIS_MAPPING.md` 10.1a.
7. **Xom SQL** (D66a, ikki buyruq) — literal va testlangan, lekin model
   o‘zgarsa qo‘lda yangilanadi (`test_raw_sql_names_the_models_columns_and_tables`
   yiqiladi).
8. **CI masofada ishga tushirilmagan** (push yo‘q) — lokal ekvivalent 7-bo‘limda.
9. **`verification/`** — tekshiruvchining yakuniy hisoboti (`85ac91e`) ikki
   nuqson topdi, ikkalasi tuzatildi (N-1, N-2; 8-bo‘lim); uning bu tuzatishlarga
   bog‘liq testlarini yangilash tekshiruvchining ishi.
10. **Root `.env` dagi token** bekor qilinishi foydalanuvchiga bog‘liq.
11. Frontend: 850 kB chunk, skrinshotlar, profil o‘chirish UI'si (2.1).

---

## 5. Cheklovlar (dissertatsiya uchun)

- ASSISTments 2009 da prerekvizit grafi yo‘q — BKT+IRT+Pre faqat Junyi'da (D53).
- Bashorat faqat talabaning qat’iy oldingi masalalaridan (D57); D60 da test
  vaqtida b muzlatilsa ham xulosalar o‘zgarmaydi.
- Kalibrlash chegaralangan grid'da (F5, D59): parametrlar grid tugunlarida;
  G0 va S0 ning katta qismi II bob chegarasi yonida (6-bo‘lim) — D55 bu
  chegaralarni kengaytirib sezgirlikni ko‘rsatadi.
- θ ±4 bilan va posterior/P(L)′ [0, 1] bilan cheklanadi (F1, F6) — natijaga
  ta’siri o‘lchangan (F6: bit-aniq).
- V-F2 sintetik kursda (500 mavzu, 1 500 prerekvizit), simulyatsiya qilingan
  o‘quvchilar bilan (D13), bitta mashinada; real o‘quvchilar oqimi emas.
- H4 sintetik daraxtlarda (uch shakl), bitta Postgres sozlamasida (D63).
- H1/H3 xulosalari “shu graf bilan” o‘qiladi (D61); DBE-KT22 va annotatsiya yo‘q.

---

## 6. Dissertatsiyaga kiritiladigan qiymatlar

<!-- report-values:start (experiments/report_values.py; do not edit by hand) -->

#### H2 — ASSISTments 2009, 7 model (D57, D59)

Manba: `experiments/results/assist09/20261010-060005`

| Model | AUC [95 % CI] |
|---|---|
| BKT | 0.707 [0.701; 0.714] |
| BKT+IRT (λ=0) | 0.724 [0.718; 0.73] |
| Elo/Rasch | 0.762 [0.757; 0.767] |
| PFA | 0.704 [0.698; 0.71] |
| DKT | 0.727 [0.721; 0.733] |
| AKT | 0.708 [0.701; 0.715] |
| AKT-R | 0.719 [0.712; 0.725] |

| Kontrast | Qaror | Farq [95 % CI] | p (Holm) |
|---|---|---|---|
| BKT+IRT (λ=0) − BKT | D53 | 0.016 [0.016; 0.017] | 0 |
| BKT+IRT (λ=0) − DKT | D56 | -0.003 [-0.005; -0.001] | 0 |
| BKT+IRT (λ=0) − AKT-R | D59 | 0.005 [0.002; 0.008] | 0 |

DKT sanity: AUC 0.727, kutilgan oraliqda: ha.

#### D55 — chegaralar sezgirligi (ASSISTments)

Manba: `experiments/results/assist09-bounds/20261011-183756`

| Sozlama | G_MAX | S_MAX | BKT+IRT − BKT [95 % CI] | BKT+IRT − DKT [95 % CI] |
|---|---|---|---|---|
| asosiy | 0.3 | 0.1 | 0.016 [0.016; 0.017] | -0.003 [-0.005; -0.001] |
| kengroq | 0.4 | 0.2 | 0.02 [0.019; 0.022] | 0.009 [0.007; 0.011] |
| eng keng | 0.49 | 0.3 | 0.031 [0.029; 0.033] | 0.02 [0.018; 0.022] |

#### D60 — test vaqtida qiyinlik muzlatilganda

Manba: `experiments/results/assist09-frozen/20261012-063439`

| Da’vo | current [95 % CI] | frozen [95 % CI] | Barqaror |
|---|---|---|---|
| D53: BKT+IRT (λ=0) − BKT > 0 | 0.016 [0.016; 0.017] | 0.016 [0.015; 0.017] | ha |
| D56: BKT+IRT (λ=0) − DKT, CI lower end ≥ −0.01 | -0.003 [-0.005; -0.001] | -0.004 [-0.006; -0.002] | ha |

#### H1 — Junyi, tayyorlik qoidasi

Manba: `experiments/results/junyi-h1/20261019-102526`

Holat: **qo‘llab-quvvatlanmadi**.

| Qoida | Farq [95 % CI] | Xulosa |
|---|---|---|
| completeness | -0 [-0; 0] | aniqlanmadi |
| pass_mark | 0.017 [0.012; 0.022] | qo‘llab-quvvatlanmadi |

#### H3 — Junyi, graf (BKT+IRT+Pre)

Manba: `experiments/results/junyi-h3/20261019-122423`

| k | Kontrast | Farq [95 % CI] | Holat |
|---|---|---|---|
| 3 | asl − teskari | 0.001 [-0; 0.002] | aniqlanmadi |
| 3 | asl − tasodifiy | 0.005 [0.004; 0.006] | aniqlanmadi |
| 3 | asl − grafsiz | -0.001 [-0.002; 0] | aniqlanmadi |
| 5 | asl − teskari | 0.001 [-0; 0.002] | qo‘llab-quvvatlanmadi |
| 5 | asl − tasodifiy | 0.004 [0.004; 0.005] | qo‘llab-quvvatlanmadi |
| 5 | asl − grafsiz | -0.001 [-0.002; -0] | qo‘llab-quvvatlanmadi |

Asosiy k = 3.

#### H4 — saqlash usullari (D63)

Manba: `experiments/results/tree-benchmark/20261016-093916`, `experiments/results/tree-benchmark/20261020-050428`

Holat: **qo‘llab-quvvatlanmadi**. Yozish kataklari 36, “CTE tezroq” emas: 6; o‘qish kataklari 18, 1.5 barobardan sekin: 16; yaxlitlik buzilishi: 0; hisoblanmagan: 3.

`deep_chain/100000`, qayta o‘lchangan (D63h):

| Amal | ρ = MPTT / CTE [95 % CI] | Xulosa |
|---|---|---|
| shoxni o‘qish | — | timeout |
| ajdodlarni o‘qish | — | timeout |
| oxiriga barg qo‘shish | 281.427 [235.169; 365.018] | CTE tezroq |
| eng chapga barg qo‘shish | 422.457 [381.918; 452.996] | CTE tezroq |
| shoxni ko‘chirish | — | timeout |
| shoxni o‘chirish | 0.922 [0.796; 1.033] | taqqoslanadigan |

#### Locust — V-F2 (asosiy, D68a)

Manba: `experiments/results/locust/20261020-100901`

gunicorn 26.2.0, 8 sync workers, 50 foydalanuvchi, 120 s, DEBUG=yo‘q.

| Endpoint | So‘rovlar | Xato ulushi | p50, ms | p95, ms | RPS |
|---|---|---|---|---|---|
| next_question | 3902 | 0 | 120 | 190 | 32.689 |
| submit_answer | 3868 | 0 | 140 | 210 | 32.404 |
| trajectory | 3942 | 0 | 190 | 280 | 33.024 |
| Aggregated | 11812 | 0 | 150 | 250 | 98.954 |

V-F2 mo‘ljali: p95 < 300 ms.

#### Locust — runserver (qo‘shimcha, D68)

Manba: `experiments/results/locust/20261020-085406`, `experiments/results/locust/20261020-085659`

| Natija | Server | Foydalanuvchi | p95 (jami), ms | RPS |
|---|---|---|---|---|
| `locust/20261020-085406` | django runserver (threaded, one process, --noreload) | 50 | 6300 | 13.902 |
| `locust/20261020-085659` | django runserver (threaded, one process, --noreload) | 5 | 300 | 9.854 |

#### Kalibrlangan BKT parametrlari — ASSISTments (H2, 5 fold)

Manba: `experiments/results/assist09/20261010-060005`

| Parametr | Grid | Fit'lar | Q1 | Mediana | Q3 | Pastki chetda | Yuqori chetda |
|---|---|---|---|---|---|---|---|
| p0 | 0.01…0.95 | 555 | 0.3 | 0.5 | 0.7 | 0.065 | 0.058 |
| pt | 0.005…0.5 | 555 | 0.1 | 0.1 | 0.2 | 0.016 | 0.106 |
| g0 | 0.05…0.29 | 555 | 0.29 | 0.29 | 0.29 | 0.047 | 0.766 |
| s0 | 0.01…0.097 | 555 | 0.097 | 0.097 | 0.097 | 0.043 | 0.874 |

Junyi (H1, H3): per-skill parametrlar `metrics.json` da saqlanmagan (`folds[].parameters` bo‘sh), taqsimotni qayta yugurishsiz berib bo‘lmaydi.

<!-- report-values:end -->

---

## 7. Tugallanganlik mezoni (spetsifikatsiya 6-bo‘lim)

| Mezon | Bajarildimi | Dalil |
|---|---|---|
| 4-bo‘limdagi barcha etalon testlar o‘tadi | **ha** | `neuro_model/tests`, `assessments/tests/test_student_model.py`, `test_readiness.py`, `test_trajectory.py` — backend suite'ida (CI ekvivalenti: 1 262 passed, 0 failed; asosiy repoda 1 273 passed) |
| Toza muhit: lock fayllardan yangi venv'lar, yangi test bazasi | **ha** | Scratchpad'da `git clone` (`c7a6037`), uv'ning Python 3.12.3 i bilan `venv` (`requirements.lock`) va `experiments/.venv` (`experiments/requirements.lock`, CPU torch) — ikkalasida `pip check`: “No broken requirements”; yangi bazalar `neurolearn_clean`, `neurolearn_clean_bench` (migratsiya), `neurolearn_ci` (test bazasi `test_neurolearn_ci`) |
| `experiments/run_all.py --quick` xatosiz | **ha** | rc=0 (assist09, 24 daq) va `--dataset junyi --quick` rc=0 (18 daq); natijalar toza klonda, provenance toza, D54 ogohlantirishi yo‘q. Ma’lumot `NEUROLEARN_DATA` orqali (repoda yo‘q, D49) |
| `manage.py run_tree_benchmark --quick` xatosiz | **ha** | rc=0 (3,5 daq), `neurolearn_clean_bench` da |
| CI ikkala repoda yashil | **lokal ekvivalent yashil; masofada ishga tushirilmadi** (push yo‘q) | Backend (`.github/workflows/ci.yml` qadamlari, `f7626ae` ning toza kloni, CI muhit o‘zgaruvchilari): `check` toza, `makemigrations --check` — “No changes detected”, `coverage run -m pytest`: 1 262 passed, 67 skipped (ma’lumot fayllari yo‘q — CI'dagi kabi), coverage umumiy 90 % (≥ 80), `neuro_model` 99 % (≥ 95), servislar 97 % (≥ 85). Frontend (`ci.yml`: `npm ci`, lint, `tsc --noEmit -p tsconfig.app.json`, `vitest run`, build; `5251c45` ning toza kloni): hammasi rc=0 — lint 0 error (8 ogohlantirish), tsc 0, vitest 90/90, build (> 500 kB chunk ogohlantirishi). Farq: lokal Node 22.22.1, CI'da 20 |
| “Kechiktirildi” qatorlarining hammasida sabab bor | **ha** | 4 qator (DBE-KT22, annotatsiya — D61; D26 va LLM dizayni — D26), har birida sabab; 9 ta “Qisman” ham sababi bilan (2.1) |

`run_all`/`run_tree_benchmark` yugurishlari `c7a6037` dan; undan keyingi
commit'lar faqat hujjatlar, `experiments/report_values.py` va testlar — bu
ikki buyruq ishlatadigan kodga tegmaydi.


---

## 8. `verification/` — tekshiruvchining yakuniy hisoboti va undan keyin

`verification/` ga tegilmadi; faqat ishga tushirildi
(`scripts/dj5433.sh venv/bin/python -m pytest --ds=verification.settings verification/tests`).

**Tekshiruvchining yopish sonlari** (`verification/REPORT.md`, `c60d00e`,
2026-10-21): `verification/tests` **951 passed, 0 failed, 0 xfailed, 0 skipped**;
`verification/neural` **62 passed, 3 skipped** (skip'lar — D57 izolyatsiyasi,
populyatsiya parametrli 3 model uchun ataylab). Test soni 938 → 951
(+12 `test_e_d71_posthoc.py`, +1 N-1 qamrovi).

**Oldingi tekshiruv** (`85ac91e`): oldingi 7 ta xatoni (N/A signallari, D48
mezoni, D70 fixture'i) tekshiruvchi yopdi; `verification/tests` 936 passed,
1 failed, 1 xfailed, `verification/neural` 62 passed, 3 skipped. Ikki nuqson:

| Nuqson | Holat | Tuzatish |
|---|---|---|
| N-1 (V-E3): pyKT eksporti 5 qator yozadi, pyKT 0.0.38 `read_data` 6 qator o‘qiydi | **tuzatildi** (`cdd8826`) | oltinchi qator `NA`; test eksportni pyKT'ning o‘z o‘quvchisi bilan o‘qiydi |
| N-2 (V-H1): `measurements.csv` da mediana, p95, SQL soni, o‘zgargan qatorlar yo‘q | **tuzatildi** (`3ed55e9`) | to‘rt ustun; per-takror SQL soni va o‘zgargan qatorlar saqlanadi |

**Tuzatishlardan keyin, yopishgacha** (`852e1e3`, eskirgan oraliq holat):
`verification/tests` 934 passed, 3 failed, 1 xfailed edi. Uchala FAIL —
tekshiruvchining yordamchi funksiyasi `_pykt_blocks`
(`verification/tests/test_e_consent_export.py:105`) N-1 dan oldingi 5 qatorli
blokni taxmin qilgani; N-2 ning strict xfail testi commit qilingan eski
`tree-benchmark-quick/20261012-131931` CSV'sini o‘qigani. Yopish tekshiruvida
(`c60d00e`) tekshiruvchi ikkalasini o‘zi yopdi: `_pykt_blocks` pyKT 0.0.38 ning
6 qatorli blokiga moslashtirildi (modul 28 passed), N-2 testi esa `tmp_path` da
kichik yangi `run_tree_benchmark --quick` run'ini tekshiradigan oddiy testga
aylandi va o‘tadi.

Qolgan suite'lar (`c60d00e` hisobotidagi sonlar): backend **1 298 passed**,
51 skipped, 13 subtests, 0 failed; `experiments/.venv` — `experiments/tests`
**415 passed**, 2 skipped; `benchmarks/tests` **92 passed**;
`report_values --check` — 177 son, 9 bo‘lim, 0 farq.
