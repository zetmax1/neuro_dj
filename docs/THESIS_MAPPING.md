# THESIS_MAPPING — II bob ↔ kod

Dissertatsiyaning II bobidagi har bir tushuncha kodda qayerda yashaydi, va
koddagi nimalar II bobda **yo‘q**. Ikkinchi ro‘yxat muhimroq: unda yozilmagan
har qanday farq — nazorat qilinmagan farq.

Manba: `NEUROLEARN_REMEDIATION.md` 3-bo‘limi (spetsifikatsiya) va 4-bo‘limi
(etalon qiymatlar). Qoida 7: hisob-kitob `neuro_model/` da, Django'siz; Django
qatlami faqat holatni yuklaydi, chaqiradi va saqlaydi.

---

## 1. Bilimlar bazasi (3.1–3.2)

| II bob | Kod | Test |
|---|---|---|
| Daraxt, `kind` (course / section / topic), `pos` preorder (D4) | `neuro_model/graph.py` (`Tree`, `preorder_positions`), `curriculum/models.py` (`Topic`) | `neuro_model/tests/test_graph.py`, `curriculum/tests/test_tree.py` |
| Leaves(n) | `neuro_model/graph.py` (`leaf_sets`) | `curriculum/tests/test_tree.py::test_leaves_for_every_kind` |
| E_P, ω ∈ (0, 1] | `curriculum/models.py` (`TopicPrerequisite`) | `curriculum/tests/test_kb.py` |
| G_L (meros grafi), vazni — maksimum | `neuro_model/graph.py` (`expand`, `LeafEdge`) | `neuro_model/tests/test_graph.py` |
| Y1 (daraxt), Y2 (ajdod-avlod), Y3 (asiklik), Y4 (savollar faqat mavzularda) | `curriculum/services/kb.py` | `curriculum/tests/test_kb.py`, `verification/tests/test_b2_rejections.py` |
| Algoritm 2.1 (qirra qo‘shish, zanjir) | `neuro_model/graph.py` (`find_cycle_chain`) | `neuro_model/tests/test_graph.py`, `test_graph_random.py` |
| Algoritm 2.2 (`(pos, id)` kalitli tartib, `lev`) | `neuro_model/graph.py` (`topological_order`) | `neuro_model/tests/test_graph_random.py` |
| Desc\*, ortiqcha qirralar, κ | `neuro_model/graph.py` | `neuro_model/tests/test_graph.py` |
| Qulf va versiya | `curriculum/services/kb.py` (`_kb_change`), `curriculum/models.py` (`KnowledgeBaseVersion`) | `curriculum/tests/test_kb.py`, `verification/tests/test_b5_concurrency.py` |

## 2. Talaba modeli (3.3)

| II bob | Kod | Test |
|---|---|---|
| γ_G = ln(G0/(G_MAX−G0)), γ_S = ln(S0/(S_MAX−S0)) | `neuro_model/irt.py` (`gamma`) | `neuro_model/tests/test_student.py` |
| P(G) = G_MAX·σ(γ_G + a_q(θ−b)), P(S) = S_MAX·σ(γ_S − a_q(θ−b)) | `neuro_model/irt.py` (`guess`, `slip`) | `test_student.py::test_guess_slip_table` |
| p̂, Bayes yangilanishi, PT o‘tishi | `neuro_model/bkt.py` (`predict`, `posterior`, `transition`, `step`) | `test_student.py::test_bkt_sequence_of_four_correct_answers` |
| Elo: p = σ(θ−b), K(n) = α/(1+βn) | `neuro_model/elo.py` | `test_student.py::test_elo_step` |
| P(L0) prerekvizitlardan, m̄, c = τ − C_OFFSET | `neuro_model/init.py` (`initial_mastery`) | `test_student.py::test_initial_mastery_reference_values` |
| Algoritm 2.4 (qat’iy tartib) | `neuro_model/student.py` (`observe`) | `test_student.py::test_p_hat_uses_theta_before_not_theta_after` |
| 2.5-tasdiq | — (xossa) | `test_student.py::test_assertion_2_5_on_the_posterior` |
| Ablatsiya: `use_irt`, `use_prereq_init` | `neuro_model/student.py` (`Flags`), `settings.THESIS_FLAGS` | `test_student.py`, `assessments/tests/test_student_model.py` |
| Mavzu parametrlari P0, PT, G0, S0 | `assessments/models.py` (`TopicModelParams`) | `assessments/tests/test_student_model.py` |
| θ (talaba, kurs), n_s | `assessments/models.py` (`UserAbility`) | `test_student_model.py::test_theta_is_shared_by_every_topic_of_the_course` |
| b_q, n_q | `assessments/models.py` (`Question.irt_difficulty`, `n_answers`) | `test_student_model.py::test_elo_moves_the_learner_and_the_item` |
| Dvigatel (`thesis_hybrid`) | `assessments/services/student_model.py` | `assessments/tests/test_student_model.py` |
| Bitta tranzaksiya, `select_for_update` | `assessments/services/orchestrator.py`, `student_model.apply_answer` | `assessments/tests/test_ledger.py` |
| Savol tanlash: min \|b_q − θ_s\| | `assessments/services/question_selection.py` | `test_student_model.py::test_selection_picks_the_question_closest_to_theta` |
| Kalibrlash | `neuro_model/calibrate.py`, `assessments/management/commands/calibrate_bkt.py` | `neuro_model/tests/test_calibrate.py`, `test_student_model.py` |

## 3. Tayyorlik va holatlar (3.4)

| II bob | Kod | Test |
|---|---|---|
| M belgisi, τ/δ gisterezis | `neuro_model/readiness.py` (`mastered_flag`) | `neuro_model/tests/test_readiness.py::test_mastered_flag_hysteresis` |
| R_s(w) — barcha u ∈ Pre(w) uchun M = 1 | `neuro_model/readiness.py` (`is_ready`) | `test_readiness.py::test_readiness_needs_every_predecessor` |
| r_s(w) = min P(L) | `neuro_model/readiness.py` (`readiness_score`) | `test_readiness.py::test_readiness_score_is_the_weakest_prerequisite`; ledger'da `readiness_score` |
| `missing_count_s(w)` | `neuro_model/readiness.py` (`missing_count`, `recompute_counters`) | `test_readiness.py::test_a_new_learner_starts_at_the_size_of_pre` |
| Algoritm 2.3 (1–5 qadam) | `neuro_model/readiness.py` (`propagate`), `assessments/services/readiness.py` (`apply_answer`) | `assessments/tests/test_readiness.py::test_the_readiness_example_of_section_four` |
| Holatlar va o‘tishlar | `neuro_model/readiness.py` (`next_status`), `assessments/models.py` (`TopicStatus`) | `neuro_model/tests/test_readiness.py::test_status_transitions` |
| TY5 — boshlangan mavzu yopilmaydi | `next_status` dagi `started` tarmog‘i + `StudentTopicState` DB cheklovi `state_started_matches_status` | `assessments/tests/test_readiness.py::test_ty5_*` |
| TY6 — `kb_version` mos kelmasa O(n+m) qayta hisoblash | `assessments/services/readiness.py` (`resync`) | `assessments/tests/test_readiness.py::test_ty6_*` |
| Talaba holati | `assessments/models.py` (`StudentTopicState`) | `assessments/tests/test_readiness.py` |
| Yopiq mavzuga 403 `{missing: [...]}` | `readiness.check_open`, `orchestrator.TopicClosed`, `assessments/views/assessment.py` | `test_readiness.py::test_*_refuses_a_closed_topic` |
| Bir xil `p_mastery` / `accuracy` / `status` barcha API'larda | `curriculum/services/path.py`, daraxt/graf/dashboard/testlar serializerlari | `test_readiness.py::test_every_student_endpoint_reports_the_same_state` |

## 4. Test sessiyasi (D7)

| II bob / qaror | Kod | Test |
|---|---|---|
| Har bir javob Algoritm 2.4 orqali, ketma-ket | `assessments/services/orchestrator.py` (`apply_one_answer`) — moslashuvchan endpoint ham, test sessiyasi ham shu yagona yo‘ldan o‘tadi | `assessments/tests/test_test_session.py::TestSessionGoesThroughTheModel::test_the_rows_are_a_chain_in_submission_order` |
| `source=test_session`, `session` FK | `assessments/services/test_session.py` (`submit`) | `test_the_rows_are_a_chain_in_submission_order` |
| Imtihon bahosi alohida: vaznli ball, o‘tdi/o‘tmadi | `assessments/services/test_session.py` (`grade_paper`, sof), `TestSessionResult` | `TestSessionGrading` (5 ta test) |
| Baho `p_mastery` ga yozilmaydi va tayyorlikka ta’sir qilmaydi | Baho faqat `TestSessionResult` ga; holat `readiness.apply_answer` dan keladi | `test_submit_test_session_weighted_grading` (p_mastery ∈ [0,1], bahodan farqli, qayta o‘ynash natijasiga teng) |
| Atomarlik va qulflar | `submit` `@transaction.atomic`; barcha mavzular uchun advisory lock bir marta, tartiblangan holda | `test_the_whole_submission_is_atomic` |
| Yopiq mavzuga 403 | `submit` `TopicClosed` beradi | `TestSessionRespectsReadiness` |

## 5. Keyingi bosqichlar

| II bob | Bosqich |
|---|---|
| 3.5 Trayektoriya, Need(g) | 6 |

---

## 6. Farqlar — koddagi, II bobda yo‘q narsalar

Har biri ataylab qo‘shilgan va shu yerda qayd etiladi.

### F1 — θ ±`THETA_CLAMP` bilan cheklanadi (D6)

- **Nima.** `neuro_model/elo.py` dagi `update()` θ ni `[−THETA_CLAMP, +THETA_CLAMP]`
  oralig‘ida ushlaydi (standart 4.0).
- **Nega.** Raqamli xavfsizlik chorasi. Cheklovsiz, ketma-ket bir xil javoblarda
  θ cheksiz o‘sadi va σ to‘yinib qoladi: `|b_q − θ|` barcha savollar uchun
  amalda teng bo‘lib, savol tanlash ma’nosini yo‘qotadi.
- **Ta’siri.** Normal diapazonda (|θ| < 4) hech qanday ta’sir yo‘q — chegaraga
  faqat ketma-ket ~15+ bir xil javobda yetiladi. Chegara `b_q` ga qo‘llanmaydi.
- **Test.** `neuro_model/tests/test_student.py::test_theta_is_clamped`.

### F2 — Diskret `MasteryLevel` darajalari — **yopildi (4-bosqich)**

`MasteryLevel` enum'i, `mastery_level_for()` va aralash shkalali
`mastery_percentage` ustuni olib tashlandi. O‘rniga 3.4-bo‘limning M belgisi
(τ/δ gisterezis) va beshta holati keldi. Bu farq endi mavjud emas.

### F3 — `review_repeat` siyosati (D25)

- **Nima.** `REVIEW_REPEAT_HOURS` ichida takrorlangan savol ledger'ga yoziladi,
  lekin θ, b_q, P(L) va hisoblagichlarni o‘zgartirmaydi.
- **Nega.** Ma’lumot siyosati: xuddi shu savolni qayta ko‘rish yangi dalil emas.
- **Ta’siri.** Bunday qatorlarda `p_*`, `theta_*`, `b_*` NULL bo‘ladi va
  `rebuild_student_states` ularni qayta o‘ynamaydi.
- **Test.** `assessments/tests/test_ledger.py::test_repeat_within_window_is_logged_but_changes_nothing`.

### F4 — Kesh kalitida `instance_token` (D31)

- **Nima.** KB snapshot keshi `kb:snapshot:<instance_token>:v<version>` kaliti
  bilan saqlanadi.
- **Nega.** GR1: hisoblagich biror sabab bilan orqaga qaytsa, eski yozuv joriy
  KB sifatida xizmat qilmasligi kerak.
- **Ta’siri.** Faqat kesh adreslash; model qiymatlariga ta’siri yo‘q.

### F5 — Kalibrlashda chegaralangan grid search

- **Nima.** `calibrate_bkt` standart holatda `neuro_model/calibrate.py` dagi
  grid search'ni ishlatadi; pyBKT EM faqat `--method=pybkt` bilan.
- **Nega.** II bob usulni belgilamaydi. Grid search tashqi bog‘liqlik
  talab qilmaydi va deterministik.
- **Ta’siri.** Topilgan parametrlar grid tugunlarida bo‘ladi, uzluksiz
  optimumda emas. `G0 < G_MAX` va `S0 < S_MAX` chegaralari majburiy, chunki
  γ chegarada aniqlanmagan.
