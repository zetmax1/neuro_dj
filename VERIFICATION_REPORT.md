# NeuroLearn — mustaqil tekshiruv hisoboti

> Topshiriq: `NEUROLEARN_VERIFICATION.md`. Tekshirilgan commit: `7825f2a` (branch `thesis-model`, 2026-10-03 14:01 +05).
> Tekshiruv sanasi: 2026-10-03. Prototip kodi o‘zgartirilmadi: yozilgan joylar — `verification/` va `VERIFICATION_REPORT.md`.
> Etalon (oracle) `NEUROLEARN_REMEDIATION.md` ning 3-bo‘limidagi formulalardan mustaqil yozildi; graf xossalari uchun `networkx` ishlatildi.

---

## 1. Qisqa xulosa

`REMEDIATION_PROGRESS.md` ga ko‘ra faqat **0, 1 va 2-bosqichlar** bajarilgan. Shuning uchun amalda tekshirilishi mumkin bo‘lgan guruh — **B (bilimlar bazasi va graf, 2-bosqich)**, qolganlari 5-qoida bo‘yicha N/A.

| Natija | Soni | ID'lar |
|---|---|---|
| **PASS** | 5 | V-B1, V-B2, V-B3, V-B5, V-B6 |
| **FAIL** | 1 | V-B4 |
| **N/A** | 31 | V-A1…V-A4, V-C1…V-C12, V-D1, V-E1…V-E4, V-F1, V-F2, V-G1…V-G7, V-H1 |

Qo‘shimcha (topshiriq ro‘yxatida yo‘q, lekin ayni shu kod bo‘yicha isbotlangan): **V-A4\*** (`neuro_model/graph.py` mutatsion tahlili) — PASS; **V-B6a** (`KnowledgeBaseVersion.updated_at`) — FAIL (past jiddiylik).

Testlar: **694 ta test, 689 PASS, 5 FAIL** (5 ta FAIL = 2 ta asosiy + 1 ta past jiddiylikdagi muammoning dalillari). Ishga tushirish vaqti ~35 s.

### Eng jiddiy 5 ta muammo

1. **Teskari FK manager (`parent.children.add/set`) KB guard'ini butunlay chetlab o‘tadi.** Tugunni ko‘chirish, Y2 ni va “topic — barg” qoidasini buzish mumkin; hech qanday validatsiya yo‘q va KB versiyasi oshmaydi. Sabab: `Topic._meta.base_manager_name` belgilanmagan, shuning uchun `Topic._base_manager` — guard'siz oddiy `Manager`, Django esa `add()`/`set()` da aynan shuni ishlatadi. Dalil: `verification/tests/test_b4_bypass.py::test_v_b4_reverse_manager_add_cannot_move_a_node`, `…::test_v_b4_reverse_manager_set_cannot_break_y2_and_the_kind_rules`.
2. **`KnowledgeBaseVersion` qatorini servisdan tashqarida o‘chirish mumkin** (`KnowledgeBaseVersionQuerySet` faqat `update` ni himoyalaydi). Natijada hisoblagich 1 ga qaytadi va `get_snapshot()` **avvalgi** bilimlar bazasining keshlangan nusxasini 24 soatgacha qaytaradi. Bu oqibat test bilan ko‘rsatilgan (10 qirra o‘rniga 9 kutilgan joyda 10 qaytdi). Dalil: `…::test_v_b4_kb_version_row_cannot_be_removed_or_replaced`, `…::test_v_b4_removing_the_version_row_makes_get_snapshot_serve_a_stale_kb`.
3. **`TopicPrerequisite._base_manager.all().delete()` butun E_P ni guard'siz o‘chiradi** — 1-muammo bilan bir xil ildiz sababga ega (`_base_manager`). `objects` orqali barcha yo‘llar to‘g‘ri rad etiladi, `_base_manager` orqali — yo‘q.
4. **`KnowledgeBaseVersion.updated_at` hech qachon yangilanmaydi.** Maydon `auto_now=True`, lekin `_bump_version()` `QuerySet.update()` bilan yozadi va `auto_now` ishlamaydi. “KB oxirgi marta qachon o‘zgardi” degan savolga javob beradigan yagona maydon doimo qator yaratilgan vaqtni ko‘rsatadi. Dalil: `verification/tests/test_b6_version.py::test_v_b6_updated_at_tracks_the_last_kb_change`.
5. **Dev muhiti ayni hozir 2-muammo yaratadigan holatda turadi:** dev bazada `version = 1`, dev Redis'da esa aynan bitta kalit — `:1:kb:snapshot:v1` (TTL ~23 soat). Hisoblagich 2-bosqich amallaridan keyin ham 1 (`updated_at = 2026-10-03 08:53:46`, ya’ni 2-bosqich migratsiyalaridan oldin). Shu sababli dump'dan tiklash hisoblagichni orqaga qaytarsa, eskirgan graf 24 soatgacha ko‘rsatiladi. Bu kod nuqsoni emas, lekin 2-muammoning real xavfi.

**Nima isbotlandi.** 4-bo‘limdagi graf bo‘yicha barcha sonli qiymatlar (E_L = 10, tartib, lev, |Desc\*|, ortiqcha qirralar, κ = 0, FIFO tartibi) etalon bilan aynan mos. Algoritm 2.1 ning qabul/rad qarori 8 816 ta tasodifiy holatda `networkx.is_directed_acyclic_graph` bilan to‘liq mos. Algoritm 2.2 tartibi 560 ta tasodifiy grafda `(pos, id)` bo‘yicha leksikografik eng kichik ekani tasdiqlandi. Poyga testi 60 raundda (3 ssenariy × 20) aynan bitta g‘olib berdi.

---

## 2. Jadval

Dalil ustunida yo‘llar `verification/tests/` ga nisbatan.

### A. Sof funksiyalar (`neuro_model`) — 3-bosqich

| ID | Nima tekshirildi | Kutilgan | Amaldagi | Natija | Dalil |
|---|---|---|---|---|---|
| V-A1 | 4-bo‘limdagi BKT/Elo/P(L0)/tayyorlik qiymatlari 1e-3 aniqlikda | Hammasi mos | `neuro_model` da faqat `graph.py` bor; `bkt.py`, `irt.py`, `elo.py`, `init.py`, `readiness.py` yo‘q | **N/A (B3 bajarilmagan)** | `test_na.py::test_na_group_a_student_model_is_not_implemented` |
| V-A2 | Differensial test, ≥10 000 holat (Bayes, PT, P(G)/P(S), γ, Elo, K(n), P(L0), M) | Etalon bilan 1e-9 | Sanab o‘tilgan funksiyalarning hech biri mavjud emas | **N/A (B3)** | yuqoridagi |
| V-A3 | Xossalar: P(G)≤0.3, P(S)≤0.1, 2.5-tasdiq, [0,1], θ clamp, a=λ=0 → klassik BKT | Hammasi bajariladi | — | **N/A (B3)** | yuqoridagi |
| V-A4 | `mutmut` bilan `neuro_model` formulalarini mutatsiya | Mutatsiya balli | V-A4 nishonga oladigan formulalar (BKT/IRT/Elo) yo‘q | **N/A (B3)** | yuqoridagi |
| **V-A4\*** | *Qo‘shimcha:* mavjud yagona modul `neuro_model/graph.py` ning mutatsion tahlili (8 ta mutant qo‘lda) | Har bir xatti-harakatni o‘zgartiruvchi mutant ushlanadi | 6/6 ushlandi (100%). 2 ta mutant equivalent va isbotlandi: `pos` inyektiv ⇒ κ'da `<` va `<=` bir xil; DAG'da b ∉ Desc\*(b) ⇒ `w != b` guard'i ortiqcha | **PASS** | `test_mutation_graph.py` (10 test) |

### B. Bilimlar bazasi va graf — 2-bosqich (bajarilgan)

| ID | Nima tekshirildi | Kutilgan | Amaldagi | Natija | Dalil |
|---|---|---|---|---|---|
| V-B1 | Etalon kurs: E_L, topologik tartib, lev, \|Desc\*\|, ortiqcha qirralar, κ, FIFO tartibi | 4-bo‘lim jadvali | E_L = 10 (meros: t4→t6, t4→t7, t4→t8); tartib t1…t8; lev 0,0,1,1,1,2,3,3; \|Desc\*\| 5,4,3,3,3,2,0,0; ortiqcha t4→t7, t4→t8; κ = 0; FIFO t1,t2,t3,t5,t4,t6,t7,t8 — barchasi etalon va `networkx` bilan mos | **PASS** | `test_b1_reference_course.py` (18 test) |
| V-B1 (davomi) | `pos` (D4), `depth`, Leaves(n), qirra vazni = max ω, ω ∈ (0,1] | Spetsifikatsiya 3.1 | `pos` = preorder indeks; Leaves har bir tugun uchun mos; bitta E_L qirrasini ikki munosabat hosil qilganda vazn = max (0.8 va 0.3 → 0.8, keyin 1.0 → 1.0); ω ∈ {0, −0.1, 1.000001, 2.0, "abc", None} rad etiladi (`reason="weight"`) | **PASS** | `test_b1_reference_course.py::test_v_b1_two_relations_on_one_edge_take_the_maximum_weight`, `…weight_inside_the_allowed_interval`, `…weight_outside_the_interval_is_refused` |
| V-B2 | Rad etilishi kerak bo‘lgan holatlar va sabablari | `cycle`/`nested`, zanjir bilan | (t8,t3) → `cycle`, zanjir **t3 → t6 → t8**, `chain_names` = mavzu nomlari, `edge` = [t8, t3]; (B3,t6) → `nested`; t4 → B3 ko‘chirish → `nested`; o‘z-o‘ziga → `self`; dublikat → `duplicate`. Har bir rad etishdan keyin qatorlar soni va versiya o‘zgarmagan | **PASS** | `test_b2_rejections.py` (12 test) |
| V-B2 (probe'lar) | Audit probe'lari 1 va 2 | Sikl va ajdod→avlod rad etiladi | Probe 1: `B requires A`, so‘ng `a1 requires b1` → `cycle`, zanjir [a1, b1]; Probe 2: (A,a1), (a1,A), (course,b1) → uchalasi `nested`. **Probe 3** (A o‘zlashtirilmagan → b1 yopiq) — talaba holatiga tegishli, N/A (B4) | **PASS** (1–2) | `test_b2_rejections.py::test_v_b2_audit_probe_1_section_cycle`, `…probe_2_ancestor_to_descendant` |
| V-B2 (daraxt o‘zgarishi) | “G_L ni qayta qur va Algoritm 2.2 bilan tekshir” (3.1) | Sikl hosil qiluvchi qo‘shish/ko‘chirish rad etiladi | Bo‘sh bo‘limlar halqasi (A→B→C→A, qirra yo‘q) uchun **uchinchi mavzu qo‘shish** → `cycle`, qator yozilmaydi; c1 ni A ga ko‘chirish → `cycle`, daraxt va E_L o‘zgarmaydi; Y4: savollari bor mavzu `section` ga aylanmaydi (`has_questions`), savol `section`/`course` ga biriktirilmaydi (`ValidationError`) | **PASS** | `test_b2_rejections.py::test_v_b2_adding_a_topic_that_closes_a_cycle_is_rejected`, `…a_move_that_closes_a_cycle_is_rejected`, `…y4_*` |
| V-B3 | ≥500 tasodifiy o‘rmon va prerekvizit to‘plami `networkx` bilan solishtirildi | G_L, qo‘shishga ruxsat, tartib, lev, Desc\*, ortiqcha qirralar | 500 kichik (4–14 tugun) + 60 katta (25–60 tugun) holat. **8 816 ta qabul/rad qarori** `is_directed_acyclic_graph` bilan mos, **3 889** ruxsat berilgan munosabat; har bir `cycle` zanjiri real G_L yo‘li ekani tekshirildi; tartib `lexicographical_topological_sort((pos,id))` bilan aynan teng; lev = eng uzun yo‘l; Desc\* = `descendants`; ortiqcha qirralar = `E_L \ transitive_reduction(G_L)`; κ mos. `CycleError` tartibga tushmagan mavzularni nomlaydi | **PASS** | `test_b3_random_graphs.py` (561 test) |
| V-B3 (servis darajasi) | Tasodifiy daraxt mutatsiyalari servis orqali | Qaror etalon bilan mos, rad etilganda iz qolmaydi | 40 holat × 8 amal (ko‘chirish/qo‘shish): qaror `move_rejections`/`add_topic_rejections` etaloni bilan mos; rad etilganda `(tree, prereqs, version)` uchligi bitta ham o‘zgarmadi; qabul qilinganda versiya aniq +1 va natija DAG hamda Y2 ga mos | **PASS** | `test_b3_random_service.py` (40 test) |
| **V-B4** | **`bulk_create`, `QuerySet.update`, admin orqali yozish yaxlitlikni buza olmaydi** | **Hech bir chetlab o‘tish ishlamaydi** | **Topshiriqda sanalgan uch yo‘l to‘g‘ri himoyalangan** (`bulk_create`, `bulk_update`, strukturali `update`, `save()`, `delete()`, `create()`, `update_or_create()`, `children.clear()`, admin — hammasi `KBWriteError` yoki `KBError`; admin siklni rad etadi, Y1 ni rad etadi, DELETE arxivlaydi va versiyani +1 qiladi). **Lekin ikkita yo‘l chetlab o‘tadi:** `parent.children.add()/set()` va `KnowledgeBaseVersion.objects.filter(pk=1).delete()` | **FAIL** | `test_b4_bypass.py` (20 test, 4 FAIL) |
| V-B5 | Parallel sikl, 20 marta | Aynan bitta tranzaksiya muvaffaqiyatli | 3 ssenariy × 20 raund = 60 raund, hammasida aynan bitta `committed` + bitta `KBError(reason="cycle")`: (a) x→y va y→x; (b) a→b mavjud, b→c va c→a; (c) versiya ham faqat g‘olib uchun +1. 4-ssenariy (parallel ko‘chirish + prerekvizit) 20 raundda Y2 ni buzmagan holat qoldirdi. Advisory lock o‘chirilganda test yiqiladi: o‘lchangan yugurishda 20 raundning 10 tasi `OperationalError` (deadlock) berdi, demak test lock'ni haqiqatan o‘lchaydi | **PASS** | `test_b5_concurrency.py` (5 test) |
| V-B6 | Versiya: muvaffaqiyatdan keyin +1, rad etilgandan keyin o‘zgarmaydi | Aniq +1 / o‘zgarmaydi | 8 ta amal (`create_node`, `add_prerequisite`, `update_weight`, `remove_prerequisite`, `move_node`, `update_node(position)`, `archive_node`, `delete_node`) — har biri aniq +1. `delete_node` PROTECT sababli arxivlaganda ham aniq +1 (4 tugun arxivlandi). 8 ta rad etish — versiya o‘zgarmadi. Nomni o‘zgartirish versiyani oshirmaydi (3.2 bo‘yicha to‘g‘ri: nomlar keshda yo‘q). Kesh versiya bilan birga yangilanadi; versiya o‘qishlar orasida siljisa, snapshot keshga yozilmaydi | **PASS** | `test_b6_version.py` (9 test, 1 FAIL = V-B6a) |
| **V-B6a** | *Qo‘shimcha:* `KnowledgeBaseVersion.updated_at` oxirgi o‘zgarishni ko‘rsatadi | Versiya oshganda vaqt ham yangilanadi | `auto_now=True`, lekin `_bump_version()` `QuerySet.update()` ishlatadi ⇒ vaqt hech qachon siljimaydi | **FAIL** (past jiddiylik) | `test_b6_version.py::test_v_b6_updated_at_tracks_the_last_kb_change` |

### C–H. Bajarilmagan bosqichlar

| ID | Nima tekshirilishi kerak edi | Qaysi bosqich | Natija | N/A asosi (dalil) |
|---|---|---|---|---|
| V-C1 | O‘qituvchi etalon kursni API orqali quradi, 400 + sabab + zanjir | 4–6 | **N/A (B4–B6)** | `test_na.py::test_pending_stages`, `…group_c_and_d_readiness_and_trajectory_are_not_implemented` |
| V-C2 | Boshlang‘ich holatlar: t1, t2 ochiq; `missing` ro‘yxati | 4 | **N/A (B4)** | yuqoridagi |
| V-C3 | `p_hat`, `p_before`, `p_after`, `guess_used`, `slip_used`, θ, b qayta o‘ynash bilan mos | 4–6 | **N/A (B3–B4)** | yuqoridagi |
| V-C4 | t6 kutilgan javobdan keyin ochiladi; undan oldin 403 | 4 | **N/A (B4)** | yuqoridagi |
| V-C5 | TY5 — boshlangan mavzu yopilmaydi | 4 | **N/A (B4)** | yuqoridagi |
| V-C6 | TY6 — KB versiyasi o‘zgargach hisoblagichlar qayta hisoblanadi | 4 | **N/A (B4)** | yuqoridagi |
| V-C7 | Trayektoriya guruhlari, sabab kodlari, Need(t7) = {t4, t6} | 6 | **N/A (B6)** | yuqoridagi |
| V-C8 | Test sessiyasi dvigateldan `source=test_session` bilan o‘tadi | 5 | **N/A (B5)** | yuqoridagi |
| V-C9 | Sun’iy yozuvlar yo‘q, `attempt_no` bo‘shliqsiz | 4–6 | **N/A (B4–B6)** | yuqoridagi |
| V-C10 | Yagona shkala: `p_mastery` ∈ [0,1] barcha endpoint'larda | 4 | **N/A (B4)** | `UserKnowledgeState` da `p_mastery`, `status`, `missing_count` maydonlari yo‘q |
| V-C11 | Ruxsatlar: 401 / 403 / `is_staff=False` o‘qituvchi | 4–6 | **N/A (B4–B6)** | yuqoridagi |
| V-C12 | D25 `review_repeat` P(L) ni o‘zgartirmaydi | 4–6 | **N/A (B4–B6)** | yuqoridagi (1-bosqichda `source=review_repeat` yozilishi bor, lekin P(L) II bob modeli bilan hali hisoblanmaydi) |
| V-D1 | Bitta talabadan 10 parallel javob; `attempt_no` bo‘shliqsiz, P(L) qayta o‘ynashga teng | 3–4 | **N/A (B3–B4)** | `test_na.py::test_na_group_a_student_model_is_not_implemented` |
| V-E1 | Eksportda email/ism/`user_id` yo‘q | 8 | **N/A (B8)** | `test_na.py::test_na_group_e_experiments_and_consent_are_not_implemented` (`experiments/` yo‘q, `consent` maydoni yo‘q) |
| V-E2 | Rozilik bermaganlar va `legacy`/`seed`/`simulated`/`review_repeat` eksportga kirmaydi | 8 | **N/A (B8)** | yuqoridagi |
| V-E3 | pyKT formatidagi fayl pyKT preprocess bilan o‘qiladi | 8 | **N/A (B8)** | yuqoridagi |
| V-E4 | `experiments/run_all.py --quick` | 8 | **N/A (B8)** | yuqoridagi |
| V-F1 | `submit_answer` ≤ 12 SQL; `trajectory` va grafda N+1 yo‘q | 6 | **N/A (B6)** | `trajectory` endpoint'i yo‘q (`test_na.py::test_na_group_f_performance_targets_depend_on_stage_6`). 1-bosqich hisoboti joriy qiymatni 25/20/15 deb yozgan; u hali eski dvigatelga tegishli |
| V-F2 | 500 mavzu / 1500 prerekvizit uchun p95 < 300 ms | 6 | **N/A (B6)** | yuqoridagi |
| V-G1 | O‘quv yo‘li tugunlari holati/rangi API bilan mos | 7 | **N/A (B7)** | `test_na.py::test_na_group_g_frontend_e2e_is_not_implemented` (frontend'da `e2e/`, `playwright.config.ts` yo‘q, `package.json` da Playwright yo‘q) |
| V-G2 | Yopiq tugun → yetishmayotgan prerekvizitlar; “Shu mavzugacha yo‘l” | 7 | **N/A (B7)** | yuqoridagi |
| V-G3 | Mashq rejimi: o‘zlashtirish va bog‘liq mavzuning ochilishi | 7 | **N/A (B7)** | yuqoridagi |
| V-G4 | “Keyingi qadam” = trayektoriya API'sining 1-elementi | 7 | **N/A (B7)** | yuqoridagi |
| V-G5 | Prerekvizit muharririda sikl zanjiri grafda ajratiladi | 7 | **N/A (B7)** | yuqoridagi |
| V-G6 | Profil/xatolar sahifasi; “2PL”, “PROOF”, “70%” matnlari yo‘q; tutor menyuda yo‘q | 7 | **N/A (B7)** | yuqoridagi |
| V-G7 | Konsolda xato yo‘q; 1280/768 px skrinshotlar | 7 | **N/A (B7)** | yuqoridagi |
| V-H1 | `run_tree_benchmark --quick`, CSV ustunlari, parallel yozishdan keyingi yaxlitlik | 9 | **N/A (B9)** | `test_na.py::test_na_group_h_benchmark_command_is_not_implemented` (buyruq ro‘yxatda yo‘q) |

`e2e/` papkasi yaratilmadi: G guruhi to‘liq N/A (7-bosqich bajarilmagan), shuning uchun yoziladigan Playwright testi yo‘q.

---

## 3. FAIL'lar

### V-B4 / 1-muammo — `parent.children.add()` va `.set()` KB guard'ini chetlab o‘tadi

**Jiddiylik:** yuqori. **Buzilgan talab:** BB5–BB9 (“bitta validatsiya qilingan servis”), spetsifikatsiya 3.1 (Y1, Y2, Y4, “daraxt o‘zgarishi” tartibi) va “Qulf va versiya”.

**Minimal takrorlash:**

```bash
venv/bin/pytest --ds=verification.settings \
  verification/tests/test_b4_bypass.py::test_v_b4_reverse_manager_add_cannot_move_a_node \
  verification/tests/test_b4_bypass.py::test_v_b4_reverse_manager_set_cannot_break_y2_and_the_kind_rules
```

Kod bilan (etalon kurs qurilgandan keyin, servisdan tashqarida):

```python
Topic.objects.get(slug="B1").children.add(Topic.objects.get(slug="t6"))
# -> xato yo‘q. t6 endi B1 ning farzandi, KB versiyasi o‘zgarmagan.

Topic.objects.get(slug="t6").children.set([Topic.objects.get(slug="t3")])
# -> xato yo‘q. t6 (kind="topic") farzandga ega bo‘ldi (Y4 buzildi) va
#    mavjud (t3, t6) munosabati endi tugun bilan uning ajdodini bog‘laydi (Y2 buzildi).
```

Ikkinchi holatdan keyin test o‘sha holatning haqiqatan buzilganini tasdiqlaydi: `_check_nesting(build_snapshot(version=0))` endi `KBError` beradi, ya’ni servis o‘zi ham bu holatni noto‘g‘ri deb biladi — lekin unga shu yo‘l bilan tushib qolindi.

**Ehtimoliy sabab:** guard'lar faqat `objects` managerida o‘rnatilgan — [curriculum/models.py:41-61](curriculum/models.py#L41-L61) (`TopicQuerySet`) va [curriculum/models.py:139](curriculum/models.py#L139). Django teskari FK managerining `add()`/`set()` metodlari esa `self.model._base_manager` orqali yozadi, `Topic._meta.base_manager_name` belgilanmagani uchun u guard'siz oddiy `Manager`/`QuerySet`. Shu sababli `children.clear()` (u `objects` ga tayanadi) to‘g‘ri rad etiladi, `children.add()`/`set()` esa yo‘q — himoya nomuvofiq.

**Oqibat.** Strukturali o‘zgarish validatsiyadan ham, versiyadan ham o‘tmaydi. Agar hosil bo‘lgan holat siklli bo‘lsa, `build_snapshot` `g.CycleError` beradi va `get_snapshot()` ni chaqiradigan har bir o‘quvchi (daraxt, graf, dashboard, admin changelist) 500 oladi. Versiya oshmagani uchun eski keshlangan snapshot ham xizmat qilishda davom etadi.

**Qaysi yo‘llar aynan chetlab o‘tadi (`_base_manager` sababli):**

| Yo‘l | Holat |
|---|---|
| `parent.children.add(node)` | **chetlab o‘tadi** |
| `parent.children.set([...])` | **chetlab o‘tadi** |
| `TopicPrerequisite._base_manager.all().delete()` | **chetlab o‘tadi** (butun E_P o‘chadi) |
| `Topic._base_manager.filter(...).update(parent_id=...)` | DB cheklovi (`topic_course_is_root`) tasodifan to‘xtatdi, guard emas |
| `parent.children.clear()` | to‘g‘ri rad etiladi |
| `bulk_create`, `bulk_update`, `update`, `save`, `delete`, `create`, `update_or_create` | to‘g‘ri rad etiladi |

### V-B4 / 2-muammo — `KnowledgeBaseVersion` qatorini o‘chirish mumkin, natijada eskirgan snapshot xizmat qiladi

**Jiddiylik:** yuqori. **Buzilgan talab:** GR1 (“eskirgan yozuv o‘qilmaydi”), spetsifikatsiya 3.1 “Qulf va versiya”, 3.2 “Kesh”.

**Minimal takrorlash:**

```bash
venv/bin/pytest --ds=verification.settings \
  verification/tests/test_b4_bypass.py::test_v_b4_kb_version_row_cannot_be_removed_or_replaced \
  verification/tests/test_b4_bypass.py::test_v_b4_removing_the_version_row_makes_get_snapshot_serve_a_stale_kb
```

Kod bilan:

```python
KnowledgeBaseVersion.objects.filter(pk=1).delete()   # xato yo‘q
KnowledgeBaseVersion.current()                       # -> 1 (chunki `... .first() or 1`)
get_snapshot()                                       # kb:snapshot:v1 kaliti bilan keshlanadi

kb.remove_prerequisite(<t6 -> t7 munosabati>)        # haqiqiy o‘zgarish; versiya 0 -> 1 bo‘ladi
get_snapshot()                                       # -> yana v1: 10 qirra (9 bo‘lishi kerak)
```

Amaldagi natija: `AssertionError: get_snapshot served a cached snapshot of the previous knowledge base (version 1, 10 edges)`.

**Ehtimoliy sabab:**

- [curriculum/models.py:325-329](curriculum/models.py#L325-L329) — `KnowledgeBaseVersionQuerySet` faqat `update` ni himoyalaydi; `delete` va `bulk_create` ochiq.
- [curriculum/models.py:354](curriculum/models.py#L354) — `current()` qator yo‘q bo‘lsa `1` qaytaradi, ya’ni yo‘qolgan hisoblagichni jim ravishda “birinchi versiya” deb o‘qiydi.
- [curriculum/services/kb.py:85-88](curriculum/services/kb.py#L85-L88) — `_bump_version()` qatorni `defaults={"version": 0}` bilan qayta yaratadi va 1 ga oshiradi, demak o‘chirilgandan keyingi birinchi o‘zgarish ham 1 ni beradi. Hisoblagich monotonligi yo‘qoladi.
- [curriculum/services/graph.py:179-194](curriculum/services/graph.py#L179-L194) — kesh faqat versiya raqamiga ishonadi; raqam qaytganda eski yozuv to‘liq haqiqiy ko‘rinadi. TTL 24 soat ([curriculum/services/graph.py:33](curriculum/services/graph.py#L33)).

**Tavsiya qilinadigan yo‘nalish (tuzatish qilinmadi):** `delete`/`bulk_create` ni ham guard'lash yoki hisoblabni DB sekvensiga ko‘chirish; `current()` da qator yo‘qligini jim yutmaslik; kesh kalitiga versiyadan tashqari tarkib xeshini ham qo‘shish.

### V-B6a / 4-muammo — `KnowledgeBaseVersion.updated_at` siljimaydi

**Jiddiylik:** past. **Buzilgan talab:** to‘g‘ridan-to‘g‘ri yo‘q (spetsifikatsiya bu maydonni nomlamaydi), lekin maydon o‘z e’lon qilgan ma’nosini bajarmaydi.

**Minimal takrorlash:**

```bash
venv/bin/pytest --ds=verification.settings \
  verification/tests/test_b6_version.py::test_v_b6_updated_at_tracks_the_last_kb_change
```

**Ehtimoliy sabab:** [curriculum/models.py:339](curriculum/models.py#L339) maydonni `auto_now=True` bilan e’lon qiladi, [curriculum/services/kb.py:87](curriculum/services/kb.py#L87) esa `QuerySet.update(version=F("version") + 1)` bilan yozadi — `auto_now` faqat `Model.save()` da ishlaydi. Dev bazada bu kuzatiladi: `version = 1`, `updated_at = 2026-10-03 08:53:46`, ya’ni 2-bosqich migratsiyalaridan oldingi vaqt.

### Qo‘shimcha kuzatishlar (FAIL emas, 6-bosqich uchun)

1. `kb.update_weight(<mavjud bo‘lmagan id>, 0.5)` → `TopicPrerequisite.DoesNotExist`, `KBError` emas. `kb.create_node(..., slug=<takrorlanuvchi>)` → `IntegrityError`, `KBError` emas. V-C1 javobda `{reason, detail}` bilan 400 talab qiladi, demak bu yo‘llar view qatlamida alohida ushlanishi kerak. Dalil: `test_b6_version.py::test_v_b6_update_weight_on_a_missing_relation_is_not_a_kb_error`.
2. `delete_node` qaytargan `size` arxivlangan avlodlarni ham sanaydi (`descendants(include_self=True).count()` o‘chirishdan oldin olinadi). V-B6 testi faol tugunlar sonini kutgan joyda mos keldi, lekin aralash daraxtda son ko‘proq bo‘lishi mumkin.
3. Dev muhiti: Redis'da aynan bitta kalit — `:1:kb:snapshot:v1`, TTL ~23 soat; dev baza versiyasi 1. 2-muammoning real xavfi shu holatda eng yuqori.

---

## 4. Muhit

| Narsa | Qiymat |
|---|---|
| Tekshirilgan commit | `7825f2a` (`thesis-model`), ishchi daraxt toza (faqat `verification/` qo‘shildi) |
| OS | `Linux-7.0.0-38-generic-x86_64-with-glibc2.39` |
| Python | 3.12.3 (loyiha `venv`'i) |
| Django | 6.0.5 |
| pytest | 9.1.1 (+ pytest-django 4.12.0) |
| PostgreSQL | 16.11 (Debian), compose servisi `127.0.0.1:5433` |
| Etalon kutubxona | `networkx` 3.4.2 — faqat `verification/requirements.txt` da |
| Tekshiruv bazasi | `neurolearn_verify` (xuddi shu compose servisida; pytest-django yaratadi va o‘chiradi). Dev bazasi `neurolearn` ochilmadi |
| Kesh | LocMem (`neurolearn-verification` / `neurolearn-tests`); dev Redis'ga ulanmadi |
| **Seed** | **20261003** (`verification.settings.VERIFICATION_SEED`). Holat bo‘yicha: `Random(SEED + case)` (kichik graflar), `Random(SEED + 10_000 + case)` (katta graflar), `Random(SEED + 20_000 + case)` (servis mutatsiyalari) |
| Natija | **694 test: 689 PASS, 5 FAIL**, ~35 s |

### Buyruqlar

```bash
# 1. Etalon kutubxona (prototip requirements'iga tegmaydi)
venv/bin/pip install -r verification/requirements.txt

# 2. Servislar
docker compose --env-file config/.env up -d        # postgres + redis "healthy"

# 3. To‘liq tekshiruv
venv/bin/pytest --ds=verification.settings verification/tests -q

# 4. Faqat bitta guruh, masalan V-B3
venv/bin/pytest --ds=verification.settings verification/tests/test_b3_random_graphs.py -q
```

`--ds` ildizdagi `pytest.ini` dagi `DJANGO_SETTINGS_MODULE` dan ustun turadi, shuning uchun suite har doim `verification/settings.py` ni oladi. `test_env.py::test_isolated_database` baza nomi `neurolearn_verify` emasligini aniqlasa, suite to‘xtaydi.

### Tekshiruvning o‘z yaxlitligi

- Dev ma’lumotlari o‘zgarmadi: `curriculum_topic` = 16, `curriculum_topicprerequisite` = 2, `assessments_assessmentattempt` = 36, `kb_version` = 1 — tekshiruvdan oldin ham, keyin ham. `db.sqlite3` sha256 = `5c33c7d272b63c0411d6824917c321e0f0d67efb28138f08c73fac5a458d8fbf` (o‘zgarmadi).
- `git status`: faqat `verification/` (yangi) va `NEUROLEARN_VERIFICATION.md` (topshiriq fayli) kuzatilmagan; prototipning birorta fayli o‘zgartirilmadi.
- Suite'ning o‘zi ham tekshirildi: V-B5 uchun advisory lock olib tashlanganda test yiqiladi (o‘lchangan yugurishda 20 raundning 10 tasida deadlock); V-B3/V-B1 uchun 8 ta mutant qo‘lda kiritilib, xatti-harakatni o‘zgartiruvchi 6 tasining hammasi ushlandi, qolgan 2 tasining equivalent ekani isbotlandi.

### Fayllar

| Fayl | Mazmuni |
|---|---|
| `verification/README.md` | O‘rnatish, ishga tushirish, tuzilma |
| `verification/settings.py` | Alohida baza va kesh |
| `verification/requirements.txt` | `networkx==3.4.2` |
| `verification/oracle/tree.py` | Daraxt etaloni: `pos` (D4), Anc, Leaves, Y1, Y2 |
| `verification/oracle/graph.py` | G_L, Algoritm 2.1/2.2, lev, Desc\*, ortiqcha qirralar, κ, daraxt o‘zgarishi — `networkx` bilan |
| `verification/oracle/reference.py` | 4-bo‘lim etalon kursi va kutilgan qiymatlari |
| `verification/tests/` | `test_b1…b6` (guruh B), `test_mutation_graph.py` (V-A4\*), `test_na.py` (N/A yozuvi va qo‘riqchilari), `test_env.py` (muhit) |
