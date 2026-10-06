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

## 5. Trayektoriya (3.5)

| II bob | Kod | Test |
|---|---|---|
| Algoritm 2.5, A/B/C/D guruhlari | `neuro_model/trajectory.py` (`trajectory`) | `neuro_model/tests/test_trajectory.py::test_the_groups_come_in_order_a_b_c_d` |
| ta’sir(v) = \|{w ∈ Desc\*(v) : M = 0}\| | `neuro_model/trajectory.py` (`impact`) | `test_impact_counts_unmastered_descendants` |
| A guruhi tartibi: ta’sir ↓, so‘ng P ↑ | `trajectory()` ning A tarmog‘i | `assessments/tests/test_trajectory.py::test_review_priority_of_section_four` (t1 ta’sir 4, t3 ta’sir 3) |
| B/C/D topologik tartibda, `position` bo‘yicha emas | `order` — snapshot'ning G_L tartibi | `test_the_order_is_topological_not_by_position` |
| Tuzilmali sabab `{code, params}` | `Reason` | `test_every_item_has_a_code_and_numbers_not_a_sentence` |
| Need_s(g) va yo‘l | `neuro_model/trajectory.py` (`need`, `path_to`) | `test_need_of_t7_and_its_path` (Need(t7) = {t4, t6}, yo‘l t4 → t6 → t7) |
| `GET /api/learning/trajectory/?course=<id>` | `assessments/views/learning.py` (`TrajectoryView`), servis `assessments/services/trajectory.py` | `assessments/tests/test_trajectory.py` |
| `GET /api/learning/path-to/<id>/` | `PathToTopicView` | `test_need_of_t7_and_its_path` |
| Dashboard shu servisdan foydalanadi, to‘rtta evristika yo‘q | `analytics/views/dashboard.py` | `test_the_dashboard_reports_the_trajectory_not_four_heuristics` |
| So‘rovlar byudjeti (ES7) | bitta tayyorlik sinxronizatsiyasi + bitta nom so‘rovi | `test_the_trajectory_cost_does_not_grow_with_the_course` |

## 6. Addendum endpoint'lari (6-bosqich)

| Talab | Kod | Test |
|---|---|---|
| A4-9 `GET /api/learning/mistakes/` (D25) | `MistakesView`; “ko‘rib chiqilgan” belgisi `MistakeReview` da (ledger o‘zgarmas) | `test_mistakes_are_grouped_by_topic_with_both_choices`, `test_a_mistake_can_be_marked_reviewed_and_the_marking_is_idempotent` |
| A4-10 `GET /api/me/summary/` (D27) | `MeSummaryView` — kurs bo‘yicha k/n, θ, urinishlar, haftalik faollik javob vaqtlaridan | `test_the_summary_is_real_data_only` (XP/achievements/study_hours yo‘q) |
| A4-11 `GET /api/config/model/` (D29) | `ModelConfigView` — τ, δ va boshqa konstantalar | `test_the_model_config_is_the_single_source` |
| A4-12 `GET /api/learning/topics/<id>/history/` | `TopicHistoryView` — p̂, P(G), P(S), P(L) oldin→keyin, θ, b, natija, vaqt | `test_the_history_reports_what_the_model_used` |

## 7. Frontend qatlami (7-bosqich)

Interfeys modelni qayta hisoblamaydi: har bir son backend'dan keladi va faqat bir joyda matnga aylanadi.

| Talab | Kod (`neuro/src/`) | Test |
|---|---|---|
| Sonlar matnga aylanadigan yagona joy (audit 3.4) | `lib/format.ts` — ehtimollik [0,1] foizga, baho allaqachon foiz | `lib/format.test.ts` |
| Holat palitrasi, 2.3–2.4-rasmlar (D21) | `lib/status.ts` — 5 holat, `LEGEND_ORDER`, hex qiymatlar SVG uchun | `lib/status.test.ts` |
| Sabablar kod sifatida, matn lug‘atda (TR3, D20) | `lib/reasons.ts` — `{code, params}` → i18n kalit | `lib/reasons.test.ts` |
| KB xatolari (sikl zanjiri, yopiq mavzu) | `lib/kbError.ts` — `cycleTopics(error)` grafda qizil zanjir | `lib/kbError.test.ts` |
| Ikki qatlamli graf, `lev` ustunlari (2.2–2.3-rasmlar) | `hooks/useGraphLayout.ts` — `twoLayer()`, `lev` standart, dagre ixtiyoriy | — (vizual) |
| Mavzu tuguni holatni backend'dan oladi | `components/learning-path/CustomTopicNode.tsx` | `test/one-vocabulary.test.tsx` |
| Prerekvizit muharriri, Algoritm 2.1 UI'da | `components/instructor/PrerequisiteEditor.tsx` — `onConnect`, ω, κ paneli | — |
| Kurs konstruktori ikki rejimda: yaratish (wizard) va tahrirlash (daraxt + tugun muharriri) (D39) | `pages/instructor/CurriculumBuilder.tsx` (rejim tugmasi), `components/instructor/CourseStructureEditor.tsx` | `components/instructor/CourseStructureEditor.test.tsx` |
| Qidiruv paneli — haqiqiy tugunlar, holat va P(L) (D40) | `components/layout/TopicSearch.tsx`, `components/layout/Header.tsx`; `?topic=<id>` → `pages/LearningPath.tsx` | `components/layout/TopicSearch.test.tsx` |
| Interfeys skrinshotlari, 3.1-bo‘lim (D41, addendum 2.11) | `scripts/screenshots.mjs`, `docs/ui/README.md` (backend) | — (skript `--list` va argument tekshiruvi; rasmlar foydalanuvchi mashinasida) |
| “Qanday hisoblandi” (D28) | `components/topic/DiagnosticsPanel.tsx` — τ chizig‘i, p̂/P(G)/P(S)/P(L) jadvali | — |
| Trayektoriya A–D guruhlarda sabablari bilan | `components/common/TrajectoryList.tsx` | `components/common/TrajectoryList.test.tsx` |
| Mashq rejimi: natija va tushuntirish ekranda qoladi | `hooks/useAdaptiveQuiz.ts` — `advance()` gacha turadi | — |
| Refresh token httpOnly cookie'da (D16) | `api/client.ts` — `withCredentials`, `ensureCsrfToken()`, 401 da bitta qayta urinish; `store/authStore.ts` hech narsa saqlamaydi | `accounts/tests/test_auth_cookies.py` (backend) |
| Soxta ma’lumot yo‘q (D23) | olib tashlangan: `KnowledgeSearch`, `mistakeStorage`, `sampleQuestions`, `Profile` massivlari | `test/one-vocabulary.test.tsx` |
| O‘zbek/ingliz pariteti (D20) | `locales/uz.json`, `locales/en.json` — 321 kalit | `locales/locales.test.ts` |
| Bitta mavzu barcha sahifalarda bir xil holat (qabul sharti) | — | `test/one-vocabulary.test.tsx` |

Backend tomoni: `accounts/auth_cookies.py` (cookie va CSRF), `accounts/permissions.py` (`IsAdminRole` — `is_staff` emas, API qaytargan rol), `accounts/serializers.py` (`UserAdminUpdateSerializer`).

7.1 bosqichida qo‘shilgan backend qismlari:

| Talab | Kod | Test |
|---|---|---|
| Qo‘shnilar orasidagi tartib — bitta KB o‘zgarishi, bitta versiya (D39) | `curriculum/services/kb.py` (`reorder_sibling`), `curriculum/views/instructor.py` (`InstructorTopicViewSet.reorder`) | `curriculum/tests/test_structure_editor.py` |
| Tur o‘zgarishi mumkinligini oldindan aytadigan hisoblagichlar (D39, Y4) | `curriculum/views/instructor.py` (`question_count`, `child_count`, `_duration_subquery`), `curriculum/serializers/instructor.py` | `test_structure_editor.py::test_the_counters_say_which_kind_changes_are_possible`, `::test_the_counters_do_not_distort_the_duration` |
| `GET /api/learning/search/?q=` — nom bo‘yicha, arxivsiz, 20 ta, `pos` tartibida (D40) | `assessments/views/learning.py` (`TopicSearchView`, `SEARCH_LIMIT`) | `assessments/tests/test_topic_search.py` |

## 8. Rozilik, anonimlashtirish va eksport (8a-bosqich)

Himoyada etika savoliga javob shu jadvalda: har bir da’vo qaysi faylda
amalga oshirilgan va qaysi test uni ushlab turadi.

| Talab | Kod | Test |
|---|---|---|
| Rozilik standart holatda yo‘q, faqat talabaning aniq harakati bilan beriladi (D42) | `accounts/models.py` (`research_consent`, standart `False`), `accounts/migrations/0005_research_consent.py` | `accounts/tests/test_research_consent.py::test_a_new_account_has_not_consented` |
| Rozilik ro‘yxatdan o‘tishda ixtiyoriy belgi (D42) | `accounts/serializers.py` (`UserRegistrationSerializer.research_consent`), `neuro/src/pages/Auth.tsx` | `::test_registration_works_without_the_checkbox`, `::test_registration_can_carry_the_checkbox` |
| Rozilik profil sahifasida boshqariladi (D42, addendum 2.8) | `neuro/src/pages/Profile.tsx` (`ConsentCard`), `neuro/src/api/auth.api.ts` (`consentApi`) | `neuro/src/pages/Profile.consent.test.tsx` |
| `PATCH /api/me/consent/` (A4-13); `false` — bekor qilish | `accounts/views.py` (`ResearchConsentView`), `config/urls.py` | `::test_consent_is_given_and_withdrawn_through_the_endpoint` |
| Rozilik o‘zgarishi `research_consent_at` bilan qayd etiladi, ikki tomonga ham | `accounts/serializers.py` (`ResearchConsentSerializer.update`) | `::test_consent_is_given_and_withdrawn_through_the_endpoint` |
| Rozilik majburiy emas: bermagan talaba tizimdan to‘liq foydalanadi (D42) | — (hech bir endpoint rozilikka bog‘lanmagan) | `::test_consent_is_not_a_condition_of_using_the_platform` |
| Rozilikni profil tahriri orqali o‘zgartirib bo‘lmaydi | Alohida serializer va endpoint | `::test_the_profile_update_path_cannot_flip_consent` |
| Psevdonim tasodifiy va qaytarib bo‘lmaydi, id/email/ismdan hosil qilinmaydi (D43) | `accounts/models.py` (`new_pseudonym`, `secrets.token_hex(8)`) | `::test_a_pseudonym_is_not_derived_from_the_account`, `::test_pseudonyms_differ_between_accounts` |
| Psevdonim foydalanuvchi qatori yaratilganda beriladi, har biriga o‘zi (D43) | Maydon `default=new_pseudonym`; migratsiya uch qadamda to‘ldiradi | `::test_a_pseudonym_is_assigned_when_the_row_is_created`, `::test_every_existing_account_got_its_own_pseudonym` |
| Psevdonim interfeysga va API'ga chiqmaydi | `UserDetailSerializer` va `ResearchConsentSerializer` uni o‘z ichiga olmaydi | `::test_the_endpoint_never_leaks_the_pseudonym` |
| Eksportda faqat psevdonim; email, ism va ichki `user_id` yo‘q (D43, D45) | `assessments/management/commands/export_research_data.py` (`CSV_COLUMNS`) | `assessments/tests/test_research_export.py::test_no_email_no_name_and_no_user_id_appear_anywhere` |
| Rozilik bermagan talaba eksportda yo‘q (D44, D45) | Buyruqning `consented` filtri | `::test_a_learner_without_consent_is_not_in_the_export` |
| `review_repeat` qatorlari eksportda yo‘q (D44, D45) | `EXPERIMENT_SOURCES` | `::test_review_repeat_rows_are_not_exported` |
| `legacy`, `seed`, `simulated` chiqarib tashlanadi; `--include-simulated` faqat quvurni sinash uchun (D13, D44) | Buyruqning `eligible()` va `--include-simulated` bayrog‘i | `::test_seed_simulated_and_legacy_rows_are_excluded`, `::test_include_simulated_is_marked_as_not_a_thesis_result` |
| Arxivlangan mavzu eksportdan chiqadi (D44) | `topic__is_archived=False` | `::test_an_archived_topic_leaves_the_export` |
| Chiqish fayllari: pyKT, xom CSV, KB grafi JSON, `metadata.json` (D44) | `write_pykt`, `write_csv`, `write_graph`, `write_metadata` | `::test_the_pykt_file_is_one_block_per_learner`, `::test_the_csv_carries_the_numbers_the_model_used`, `::test_the_graph_file_holds_the_tree_e_p_and_g_l`, `::test_the_metadata_says_which_data_the_results_came_from` |
| `--dry-run` faqat sonlarni chop etadi; eksport qilinganlar va rozilik bermaganlar alohida (D45) | Buyruqning `report()` va `--dry-run` | `::test_dry_run_reports_the_numbers_and_writes_nothing` |
| Hard-delete: rozilik bo‘lsa javoblar psevdonim bilan qoladi, aks holda o‘chiriladi (D11) | `accounts/tasks.py` (`gdpr_hard_delete_users`), `accounts/models.py` (`anonymise`) | `::test_a_consenting_learner_is_anonymised_and_their_answers_survive`, `::test_a_learner_without_consent_is_deleted_with_their_answers`, `::test_withdrawing_consent_before_deletion_removes_the_answers` |
| Rozilik ustuni va filtri foydalanuvchilar sahifasida, faqat o‘qish uchun (addendum 2.7) | `accounts/views.py` (`?consent=`), `neuro/src/pages/admin/UserManagement.tsx` | `::test_an_admin_can_filter_the_user_list_by_consent` |

Bekor qilish haqida matnda ochiq aytiladigan narsa: u **keyingi** eksportlardan
chiqaradi, allaqachon olingan fayllar o‘zgarmaydi (D42). Buni backend bajara
olmaydi, shuning uchun interfeys ham shunday deydi va test shu satrni
tekshiradi (`Profile.consent.test.tsx`).

## 9. Gipotezalar va eksperimentlar (8b-bosqich)

Har bir gipoteza → skript → natija fayli → holat. “Kod tayyor, ma’lumot yo‘q”
degan holat jadvalda **son emas**, aynan shu gap bilan chiqadi (D48).

| Gipoteza / ish | Skript | Natija fayli | Holat |
|---|---|---|---|
| Graf tahlili: o‘lcham, Y2 (o‘z-o‘ziga qirralar), Y3 (sikl, SCC), tranzitiv ortiqcha qirralar, Algoritm 2.2 tartibi va `lev`, eng uzun yo‘l (D52) | `experiments/graph_report.py` | `experiments/results/graphs/20261006-052348/{metrics.json, tables.md, env.txt}` | **ishga tushirilgan** — to‘rtta nashr etilgan grafda, D52 jadvaliga aynan mos |
| Tayyorlik yangilanishi: Algoritm 2.3 inkremental, TY6 ning to‘liq qayta hisoblashiga nisbatan (D52) | `experiments/graph_report.py` (`benchmark_readiness`) | o‘sha papka, `tables.md` 4-bo‘lim | **ishga tushirilgan** — 14×…283× (vaqtlar mashinaga bog‘liq) |
| H2 — BKT, BKT+IRT (λ=0), Elo/Rasch, PFA, DKT, AKT ASSISTments 2009 da (D53) | `experiments/h2.py` | `experiments/results/assist09/<timestamp>/` | kutilmoqda (8b-2). Ma’lumot va tozalash tayyor |
| H2 — BKT+IRT+Pre ASSISTments 2009 da | — | — | **ishga tushirilmaydi: graf yo‘q** (D53). ASSISTments uchun prerekvizit grafi mavjud emas |
| H1 — tayyorlik qoidalari (ehtimoliy r ≥ τ, bajarilganlik, o‘tish bali, skill builder'ning “ketma-ket 3 ta to‘g‘ri”) | `experiments/h1.py` | `experiments/results/<dataset>/<timestamp>/` | kutilmoqda (8b-3). Kod “javoblar + graf” juftligini oladi; hozir bunday juftlik yo‘q |
| H3 — graf nazoratlari: asl, teskari, daraja saqlangan tasodifiy (20 seed), grafsiz (λ=0) | `experiments/h3.py` | o‘sha | kutilmoqda (8b-3). Graf fayli sha256 bilan oldin commit qilinadi |
| Annotatsiya: nomzod qirralar → ikki annotator → Cohen κ → yakuniy graf | `experiments/graphs/annotate.py` | `experiments/graphs/*.csv` + sha256 | kutilmoqda (8b-3) |
| Simulyatsiya — faqat quvurni sinash (parametrlarni tiklash, Pre ning ustunligi) | `assessments/management/commands/simulate_bkt_data.py` + 8b-3 | `experiments/results/simulated/<dataset>/<timestamp>/` | kutilmoqda (8b-3). Natija papkasi alohida va “dissertatsiya natijasi emas” belgisi bilan (D13, D48) |

### Ma’lumot manbalari (D49)

| Manba | Holat | sha256 tekshirildi |
|---|---|---|
| ASSISTments 2009–2010 skill builder (`as.csv`) | bor | `f22e3fb7…d77dbdc` |
| DBE-KT22 grafi | bor | `79ece343…961307` |
| Junyi grafi | bor | `6272d524…e61d2` |
| WDKG-Course, WDKG-KnowledgePoints graflari | bor | `a6475f00…dae01`, `469032f4…86906` |
| DBE-KT22 to‘liq (javoblar bilan) | **yo‘q** (ADA kirish so‘rovi) | — |
| ASSISTments uchun o‘qituvchilar grafi | **yo‘q** (tuzilmagan) | — |
| Mahalliy eksport | rozilik yig‘ilgach | — |

### D48 — natija faqat haqiqiy ishga tushirishdan

| Talab | Kod | Test |
|---|---|---|
| `tables.md` faqat `metrics.json` dan; qo‘lda yozilgan son yo‘q | `experiments/tables.py` (`render_graph_report`, `verify`) | `test_tables.py::test_every_number_in_the_table_comes_from_the_metrics`, `::test_a_number_that_is_not_in_the_metrics_is_caught`, `::test_an_edited_result_is_caught` |
| Prozadagi raqamlar faqat e’lon qilingan havolalar | `tables.CITATIONS` | `::test_only_chapter_references_may_be_numbers_in_the_prose` |
| Har bir natija qatorida sha256, commit, seed, buyruq | `experiments/provenance.py` (`Provenance`, `Source`) | `::test_the_table_carries_the_hash_the_commit_the_seed_and_the_command` |
| sha256'siz natija yozilmaydi | `tables.require_sources` | `::test_a_result_without_a_source_hash_is_refused` |
| Ma’lumot yo‘q bo‘lsa — “ishga tushirilmagan — ma’lumot yo‘q” | `graph_report.run`, `tables.NOT_RUN` | `::test_an_absent_dataset_gets_a_sentence_not_a_number`, `test_graph_report.py::test_an_absent_graph_is_reported_as_not_run` |
| Yomon ishga tushirish yarim natija qoldirmaydi | `tables.write` | `::test_writing_is_refused_when_a_number_cannot_be_traced` |
| Simulyatsiya natijalari alohida papkada (D13) | `provenance.results_dir(simulated=True)` | `::test_the_simulated_tree_is_separate` |

### D49–D52 — yuklovchilar va graf tahlili

| Talab | Kod | Test |
|---|---|---|
| Hech narsa yuklab olinmaydi; yo‘l argument sifatida (D49) | `experiments/datasets/` (hamma yuklovchi), `data/README.md` | `test_assist09.py::test_a_missing_file_says_so_and_does_not_download`, `test_graphs.py::test_a_missing_file_is_a_missing_dataset_not_a_crash` |
| ASSISTments tozalash: bo‘sh `skill_id`, `(order_id, skill_id)` takrori, tartib, `original` bayrog‘i (D50) | `experiments/datasets/assist09.py` | `test_assist09.py` (4 ta qoida uchun 4 ta test) |
| Bir nechta skill'li savollar saqlanadi (D50, 2-qoida) | `(order_id, skill_id)` kaliti | `::test_a_question_with_two_skills_stays_two_records`, `::test_the_real_file_keeps_the_multi_skill_questions` |
| D50 sonlari mos kelmasa quvur to‘xtaydi | `assist09._verify`, `DatasetMismatch` | `::test_a_file_that_is_not_the_specified_one_stops_the_pipeline`, `::test_the_real_file_has_the_shape_d50_specifies` |
| Graf yuklovchi: graphml va CSV, `--edge-direction` (D51) | `experiments/datasets/graphs.py` | `test_graphs.py` |
| O‘z-o‘ziga qirra — Y2 buzilishi, olib tashlanadi va sanaladi (D51) | `graphs.load_graph` | `::test_a_self_loop_is_removed_and_counted` |
| DBE-KT22 ikkala yo‘nalishda (D51) | `graph_report.PUBLISHED`, `--both-directions` | `test_graph_report.py::test_the_table_is_the_same_in_both_directions`, `::test_both_directions_produces_two_entries` |
| Tartib, `lev`, Desc\*, ortiqcha qirralar — `neuro_model` dan, qayta yozilmaydi (D52) | `graph_report.analyse` → `neuro_model.graph` | `::test_the_model_and_networkx_agree_on_the_published_graphs` |
| II bobda ta’rifi yo‘q statistika (kuchsiz/kuchli komponentlar) | `experiments/components.py` | `::test_the_component_helpers_agree_with_networkx` |
| Sikl topilsa SCC'lar birlashtiriladi va qayd etiladi (D52) | `components.strongly_connected`, `condense` | `::test_a_cyclic_graph_is_merged_by_its_components_and_recorded` |
| Inkremental tayyorlik `|Succ(v)|`, to‘liq — hammasi (D52) | `graph_report.benchmark_readiness` → `neuro_model.readiness` | `::test_the_incremental_update_touches_the_successors_and_the_rebuild_all_of_them` |

## 10. Keyingi bosqichlar

| Ish | Bosqich |
|---|---|
| H2 — ASSISTments 2009 (D53) | 8b-2 |
| H1/H3 kodi, DBE yuklovchisi, graf nazoratlari, annotatsiya vositasi | 8b-3 |
| Saqlash usullari benchmarki | 9 |
| Yakuniy sinovlar va hisobot | 10 |

---

## 11. Farqlar — koddagi, II bobda yo‘q narsalar

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
