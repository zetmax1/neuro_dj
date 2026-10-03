# NeuroLearn — holat auditi (faqat o‘qish)

Audit sanasi: 2026-10-02. Backend: `~/Desktop/neuro_dj` (commit `f1f4dde`). Frontend: `~/Desktop/neuro/neuro` (alohida git repozitoriy, commit `bd3d917`).
Audit davomida kod, migratsiyalar va sozlamalar o‘zgartirilmadi. Yagona yozilgan fayl — shu hisobot.

---

## 0. Qisqa xulosa

- **Umumiy holat.** Ishlaydigan LMS prototipi bor: JWT auth, MPTT daraxti, `TopicPrerequisite` grafi, BKT / IRT / gibrid dvigatellar, dashboard va React Flow vizualizatsiyasi. Backend testlari 49/49 o‘tadi, coverage 68%. Frontend build o‘tadi. Biroq II bobdagi model (G_L, meros, sigmoid G/S, Elo K(n), prerekvizitli P(L0), ikki chegarali tayyorlik, A–D trayektoriya) kodda deyarli yo‘q yoki boshqa usulda yozilgan. Eksperiment infratuzilmasi (eksport, pyKT, metrikalar, statistika) umuman yo‘q.
- **40 ta talab bo‘yicha:** Bor — **0**, Qisman — **9**, Farqli — **11**, Yo‘q — **20**. ES1–ES7 hali bor, ES8 aniq emas (5-bo‘lim).
- **Eng muhim 5 muammo:**
  1. Frontend'dagi yagona test oqimi (`QuizSession` → `submit_test_session`) BKT/IRT'ni chetlab o‘tadi. U `mastery_percentage` ga 0–100 shkaladagi bahoni yozadi (probe'da P(L)=100.0 saqlandi) va tarix yozmaydi. BKT yo‘li (`useAdaptiveQuiz`) hech qayerda ishlatilmaydi (`assessments/views/assessment.py:187-188`, `src/pages/QuizSession.tsx:47,83`).
  2. Bilimlar bazasi modeli boshqacha: daraxt MPTT'da saqlanadi, G_L va meros yo‘q, Y2 tekshirilmaydi, sikl tugunlar grafida DFS bilan izlanadi. Probe'da mavzular darajasidagi sikl qabul qilindi. Umumiy qulf ham yo‘q (`curriculum/models.py:20,188-207`).
  3. Talaba modeli II bobga zid: G/S chiziqli, θ talaba×mavzu juftligi uchun saqlanadi, K=0.3 o‘zgarmas, b yangilanmaydi, P(L0)=0.15 o‘zgarmas, p̂ saqlanmaydi. Shu sababli H2 va H3 ni tekshirib bo‘lmaydi (`assessments/services/engines/hybrid_bkt_irt.py:77-115`, `irt.py:40,90`).
  4. Ochish/tayyorlik mantig‘i 4 xil joyda 4 xil yozilgan. Chegara bitta (0.70) va ota tugunga fallback bor. Global `Topic.is_unlocked` bitta talabaning natijasi bilan hamma uchun o‘zgaradi. Bo‘lim o‘zlashtirilganda barcha avlodlarga dalilsiz P=1.0 yoziladi (`orchestrator.py:228-240,296-337`).
  5. Javoblar logi eksperimentga yaroqsiz: unda `topic`, urinish raqami va p̂ yo‘q. “Easy skip” sun’iy to‘g‘ri javoblarni qo‘shadi (probe'da 3 ta real javobdan keyin 7 ta yozuv paydo bo‘ldi). Eksport va anonimlashtirish yo‘q. Bundan tashqari repoda `SECRET_KEY` va demo parollar ochiq turibdi (`orchestrator.py:404-419`, `config/settings.py:11`).

---

## 1. Umumiy tuzilma

### 1.1 Papkalar daraxti

```
neuro_dj/                          # backend (git: main ↔ origin/main)
├── config/            settings.py, urls.py, celery.py, asgi.py, wsgi.py
├── accounts/          models.py (CustomUser), views.py, serializers.py, tasks.py, forms.py, admin.py
│   └── management/commands/setup_roles.py
├── curriculum/        models.py, admin.py, urls.py, views.py (bo‘sh, views/ paketi bilan to‘sib qo‘yilgan)
│   ├── services/      graph.py, path.py
│   ├── views/         topic.py, graph.py, instructor.py
│   ├── serializers/   topic.py, graph.py, instructor.py
│   ├── management/commands/  seed_data.py, seed_thesis_demo.py, benchmark_tree.py, fix_demo_resource_titles.py
│   ├── migrations/    (0001–0008)
│   └── tests/         test_dag.py, test_mptt_tree.py, test_seed_thesis_demo.py, test_fix_demo_resources.py
├── assessments/       models.py, admin.py, urls.py, views.py (bo‘sh, to‘sib qo‘yilgan)
│   ├── services/      orchestrator.py, question_selection.py, base.py
│   │   └── engines/   bayesian.py, hybrid_bkt_irt.py, irt.py, streak.py
│   ├── views/         assessment.py, knowledge.py, instructor.py
│   ├── serializers/   assessment.py, knowledge.py, instructor.py
│   ├── management/commands/simulate_bkt_data.py
│   ├── migrations/    (0001–0005)
│   └── tests/         test_bayesian.py, test_irt_hybrid.py, test_test_session.py
├── analytics/         views/{dashboard,learning_curve,diagnostics}.py, serializers/, tests/test_diagnostics.py
├── static/css/admin_custom.css
├── media/  venv/  db.sqlite3  .env      # .gitignore'da
├── .agents/  graphify-out/              # untracked (graphify vositasining chiqishi)
└── readme.Md  requirements.txt  Pipfile  Pipfile.lock  pytest.ini  manage.py  .idea/ (git'da kuzatiladi)

~/Desktop/neuro/neuro/              # frontend (alohida git repo: main ↔ origin/main)
├── src/
│   ├── api/           client.ts, auth/curriculum/assessment/analytics/instructor.api.ts
│   ├── pages/         14 ta sahifa + instructor/{CurriculumManager,CurriculumBuilder}.tsx + admin/UserManagement.tsx
│   ├── components/    learning-path/, dashboard/, assessment/, instructor/, quiz/, tutor/, landing/, ui/ (shadcn)
│   ├── hooks/         useLearningPath, usePrerequisiteGraph, useAdaptiveQuiz, useDashboardData, useAITutor, …
│   ├── store/authStore.ts, contexts/AuthContext.tsx, lib/mistakeStorage.ts
│   ├── integrations/supabase/   (client.ts, types.ts)
│   └── test/example.test.ts
├── dist/ (gitignored)  node_modules/  arms_cache/ (git'da kuzatiladi)
└── package.json  vite.config.ts  vitest.config.ts  eslint.config.js  tailwind.config.ts
```

### 1.2 Texnologiyalar va versiyalar

| Qatlam | Texnologiya | Versiya / dalil |
|---|---|---|
| Python | CPython | 3.12.3 (`venv/bin/python --version`) |
| Framework | Django / DRF | 6.0.5 / 3.17.1 (`requirements.txt:2,4`) |
| Auth | djangorestframework-simplejwt | 5.5.1 (venv); `requirements.txt` da yo‘q |
| API hujjat | drf-spectacular | 0.30.0 (venv); `requirements.txt` da yo‘q |
| Daraxt | django-mptt | 0.18.0 (`requirements.txt:3`, `settings.py:34`) |
| Daraxt (ishlatilmaydi) | django-tree-queries | 0.24.0 venv'da o‘rnatilgan, lekin `INSTALLED_APPS` da ham, kodda ham yo‘q |
| MB | SQLite | `config/settings.py:99-104`. PostgreSQL ishlatilmaydi |
| Kesh | Redis (django-redis 7.0.0) | `settings.py:106-114`. Kodda hech narsa keshlanmaydi (7.6-bo‘lim) |
| Fon vazifalari | Celery 5.6.3 + Redis broker | `settings.py:187-189`, `config/celery.py:21-26` (faqat GDPR o‘chirish vazifasi) |
| Admin | django-unfold 0.100.0 | `settings.py:22` |
| Fayl importi | openpyxl 3.1.5, python-docx 1.2.0 | venv; `requirements.txt` da yo‘q |
| Frontend | React 18.3.1, Vite 8.0.0, TypeScript 5.8.3 | `node_modules/*/package.json` |
| Holat boshqaruvi | zustand 5.0.14 (auth). @tanstack/react-query 5.83.0 provider bor, lekin `useQuery` 0 marta ishlatilgan | `src/App.tsx:26-29`, grep |
| Graf vizualizatsiyasi | @xyflow/react 12.11.2 + dagre 0.8.5 | `src/hooks/usePrerequisiteGraph.ts:1-10` |
| Grafiklar | recharts 2.15.4 | `src/components/DiagnosticsPanel.tsx` |
| HTTP | axios 1.18.1 | `src/api/client.ts` |

**Bog‘liqliklar nomuvofiqligi:** `requirements.txt` da 8 ta paket bor. Undagi yo‘q, lekin import qilinadigan paketlar: simplejwt, drf-spectacular, django-redis, celery, openpyxl, python-docx, Faker, pytest-django. `Pipfile` da hatto `django-unfold` ham yo‘q. Shu sababli toza muhitda `pip install -r requirements.txt` dan keyin loyiha ishga tushmaydi.

### 1.3 Ishga tushirish va muhit o‘zgaruvchilari

- Backend (`readme.Md:3-13`): `source venv/bin/activate` → `python manage.py migrate` → `python manage.py seed_thesis_demo` → `runserver`. Redis kerak: o‘qituvchi tugun yaratganda yoki o‘zgartirganda `cache.delete_pattern` chaqiriladi (`curriculum/views/instructor.py:91`). `DJANGO_REDIS_IGNORE_EXCEPTIONS` o‘rnatilmagan, shuning uchun Redis bo‘lmasa yozuv saqlanadi-yu, javob 500 bo‘ladi.
- Backend muhit o‘zgaruvchilari: **topilmadi.** `settings.py` `os.environ` o‘qimaydi, barcha qiymatlar kodda yozilgan. Ildizdagi `.env` (gitignored) hech qayerda o‘qilmaydi. Uning ichida `KEY=VALUE` emas, GitHub personal access token ko‘rinishidagi bitta qator turibdi (qiymat hisobotga yozilmadi).
- Frontend: `npm install` → `npm run dev`. O‘zgaruvchilar: `VITE_API_URL` (`src/api/client.ts:6`), `VITE_SUPABASE_URL` va `VITE_SUPABASE_PUBLISHABLE_KEY` (`src/hooks/useAITutor.ts:14,32`, AI tutor Supabase edge function orqali ishlaydi). `.env` faqat `VITE_API_URL` ni o‘z ichiga oladi. `@supabase/supabase-js` `package.json` da yo‘q, `src/integrations/supabase/client.ts` esa hech qayerdan import qilinmaydi.
- `docker-compose`: topilmadi.

### 1.4 Hajm

| Ko‘rsatkich | Qiymat |
|---|---|
| Django app'lar | 4 (`accounts`, `curriculum`, `assessments`, `analytics`) + `config` |
| Modellar | 10: CustomUser; Topic, TopicResource, TopicPrerequisite; Question, Choice, UserKnowledgeState, AssessmentAttempt, UserAbility, UserKnowledgeHistory |
| API URL'lar | 28 (25 ta biznes + 3 ta schema/docs), 2.4-bo‘limga qarang |
| Backend testlari | 49 (8 fayl, ~1 080 qator) |
| Frontend testlari | 1 (`src/test/example.test.ts`, trivial) |
| Backend Python | 8 236 qator (migratsiyalarsiz, testlar bilan) |
| Frontend | 135 ta `.ts/.tsx` fayl. `components/ui` siz 12 627 qator |
| `cloc` | o‘rnatilmagan, shuning uchun `wc -l` ishlatildi |

### 1.5 Git holati

- Backend: faqat `main` va `remotes/origin/main` bor, jami 9 commit. Oxirgilari: `f1f4dde` streak + admin CSS, `ddc43d4` env/IDE sozlamalari, `123a243` Word/Excel'dan test importi, `8257d1a` test sessiyasi va vaznli baholash, `18447be` daraxtni MPTT'ga ko‘chirish va DAG. Commit qilinmagan o‘zgarish yo‘q, faqat untracked `.agents/` va `graphify-out/`.
- Frontend: `main`, 16 commit, ishchi papka toza. Oxirgisi `bd3d917 updated`. Bir nechta commit nomi shunchaki “updated”.

---

## 2. Backend

### 2.1 App'lar

| App | Vazifasi | Asosiy fayllar |
|---|---|---|
| accounts | Email orqali login qilinadigan `CustomUser`, soft-delete, JWT, Admin/Instructor/Student guruhlari, 30 kundan keyin hard-delete (Celery) | `models.py`, `views.py`, `serializers.py`, `tasks.py`, `management/commands/setup_roles.py` |
| curriculum | Topic daraxti (MPTT), resurslar, prerekvizitlar, daraxt/graf API, demo seed, benchmark | `models.py`, `services/graph.py`, `views/topic.py`, `views/graph.py`, `views/instructor.py` |
| assessments | Savollar, javob qabul qilish, BKT/IRT/gibrid/streak dvigatellari, test sessiyasi, savol importi | `services/orchestrator.py`, `services/engines/*`, `services/question_selection.py`, `views/assessment.py` |
| analytics | Dashboard, o‘rganish egri chizig‘i, diagnostika (θ, P(L) trendi) | `views/dashboard.py`, `views/learning_curve.py`, `views/diagnostics.py` |

### 2.2 Modellar

| Model | Maydonlar | Aloqalar | Constraint / Index |
|---|---|---|---|
| `Topic` (`curriculum/models.py:20-100`) | name, slug(unique), description, position, is_unlocked (global, default True), pass_mark_percentage, test_question_count, created/updated_at + MPTT `lft/rght/tree_id/level` | parent→self (CASCADE), instructor→User (SET_NULL) | slug unique; position index; `order_insertion_by=['position']` (`:91-92`) |
| `TopicResource` (`:103-153`) | title, resource_type, file, external_url, content, duration_minutes | topic (CASCADE) | — |
| `TopicPrerequisite` (`:156-214`) | created_at. **ω vazni yo‘q** | topic, prerequisite → Topic (CASCADE) | `unique_together(topic, prerequisite)` (`:178`); `save()` ichida `full_clean()` (`:209-211`) |
| `Question` (`assessments/models.py:44-111`) | text, explanation, difficulty(1–3), irt_discrimination(a), irt_difficulty(b), image, time_limit_seconds, is_active | topic → istalgan Topic (CASCADE) | `idx_q_topic_diff_active` |
| `Choice` (`:114-149`) | text, is_correct | question (CASCADE) | `clean()` ≤4 variant (bulk_create'da chaqirilmaydi) |
| `UserKnowledgeState` (`:156-220`) | mastery_level(0–4), mastery_percentage(float), score(%), total/correct_attempts, streak | user, topic | `uniq_user_topic_state`, `idx_user_mastery` |
| `AssessmentAttempt` (`:227-265`) | is_correct, answered_at | user, question, selected_choice (hammasi CASCADE) | `idx_attempt_user_question` |
| `UserAbility` (`:268-302`) | theta | user, **topic** | `uniq_user_topic_ability` |
| `UserKnowledgeHistory` (`:317-373`) | calculated_mastery, algorithm_used, created_at | user, topic | `idx_history_user_topic_ts` |
| `CustomUser` (`accounts/models.py:38-70`) | email(unique), first/last_name, is_active, is_staff, is_deleted, deleted_at | groups | — |

Daraxt kutubxonasi — **django-mptt** (`curriculum/models.py:17,20`, migratsiyalar `0005_migrate_to_mptt`, `0006_rebuild_mptt_tree`). django-tree-queries venv'da bor, lekin ishlatilmaydi. `orchestrator.py:23` dagi izohda “django-tree-queries' get_children() CTE” deyilgan, amalda esa MPTT ishlatiladi (`:276`).

### 2.3 Biznes mantiq qayerda

| Qatlam | Joy |
|---|---|
| Services | `assessments/services/orchestrator.py` (javobni qayta ishlash, unlock, cascade, easy-skip), `question_selection.py`, `engines/*.py`; `curriculum/services/graph.py` (DFS yopilma, Kahn, unlock), `path.py` |
| Views (mantiq ichida) | `curriculum/views/topic.py:94-119` va `views/graph.py:62-67` (unlock), `analytics/views/dashboard.py:118-208` (unlock + tavsiyalar), `assessments/views/assessment.py:85-213` (test sessiyasini baholash va mastery yangilash) |
| Models | `TopicPrerequisite.clean()` — sikl tekshiruvi (`curriculum/models.py:182-207`) |
| Serializers | `InstructorQuestionSerializer` — 2–4 variant, aynan 1 ta to‘g‘ri javob (`assessments/serializers/instructor.py:22-37`) |
| Signals / managers | Signal topilmadi. `ActiveUserManager` — soft-delete filtri (`accounts/models.py:26-29`) |

Algoritmlar yozilgan fayllar: `curriculum/models.py`, `curriculum/services/graph.py`, `assessments/services/orchestrator.py`, `assessments/services/engines/{bayesian,hybrid_bkt_irt,irt,streak}.py`, `assessments/services/question_selection.py`, `analytics/views/dashboard.py`, `curriculum/views/topic.py`, `curriculum/views/graph.py`.

### 2.4 API endpoint'lar

`python` orqali URL resolver'dan olindi. Ruxsat: global `IsAuthenticated` (`settings.py:49-51`).

| Metod | URL | View | Permission | Vazifasi |
|---|---|---|---|---|
| POST | `/api/accounts/register/` | UserRegistrationView | AllowAny | Ro‘yxatdan o‘tish, foydalanuvchini `Student` guruhiga qo‘shadi |
| GET/PATCH/DELETE | `/api/accounts/profile/` | UserProfileView | IsAuthenticated | Profil, soft-delete |
| GET | `/api/accounts/users/` | UserListView | IsAdminUser | Foydalanuvchilar ro‘yxati |
| GET/DELETE | `/api/accounts/users/<pk>/` | UserDetailView | IsAdminUser | Ko‘rish / soft-delete |
| POST | `/api/accounts/token/`, `token/refresh/` | SimpleJWT | AllowAny (login uchun 5/min throttle) | JWT |
| GET | `/api/learning_path/tree/` | LearningPathTreeView | IsAuthenticated | Daraxt + `mastery_percentage` (aslida `score`!) + is_unlocked |
| GET | `/api/curriculum/prerequisite-graph/` | PrerequisiteGraphView | **AllowAny** | React Flow uchun tugun va qirralar |
| CRUD | `/api/curriculum/instructor/topics/[<pk>/]` | InstructorTopicViewSet | IsInstructorOrAdminOrReadOnly | Tugun CRUD (talaba ham o‘qiy oladi) |
| CRUD | `/api/curriculum/instructor/resources/[<pk>/]` | InstructorResourceViewSet | IsInstructorOrAdminOrReadOnly | Resurslar |
| GET | `/api/assessments/tests/` | TestsListView | IsAuthenticated | Testlar ro‘yxati |
| GET | `/api/assessments/test_session/?topic_id=` | TestSessionView | IsAuthenticated | Stratifikatsiyalangan test (40/30/30) |
| POST | `/api/assessments/submit_test_session/` | SubmitTestSessionView | IsAuthenticated | Vaznli baholash, BKT'siz mastery yangilash |
| GET | `/api/assessments/next_question/?topic_id=` | NextQuestionView | IsAuthenticated | Adaptiv savol |
| POST | `/api/assessments/submit_answer/` | SubmitAnswerView | IsAuthenticated | BKT/IRT bilan javobni qayta ishlash |
| GET | `/api/knowledge_states/` | UserKnowledgeStateListView | IsAuthenticated | Holatlar |
| POST | `/api/assessments/instructor/questions_import/` | ImportQuestionsView | IsAdminUser | Excel/CSV/Word/TXT import |
| GET | `/api/assessments/instructor/templates/questions/` | DownloadQuestionTemplateView | **AllowAny** | Shablon fayl |
| CRUD | `/api/assessments/instructor/questions/[<pk>/]` | InstructorQuestionViewSet | IsAdminUser | Savollar banki |
| GET | `/api/analytics/learning_curve/?topic_id=` | LearningCurveView | IsAuthenticated | P(L) tarixi |
| GET | `/api/analytics/overview/` | DashboardOverviewView | IsAuthenticated | Dashboard va 4 ta tavsiya |
| GET | `/api/analytics/topic/<id>/diagnostics/` | TopicDiagnosticsView | IsAuthenticated | P(L) trendi, θ, oxirgi savollar |
| GET | `/api/schema/`, `/api/docs/`, `/api/redoc/` | drf-spectacular | AllowAny | OpenAPI |

**Prerekvizit (`TopicPrerequisite`) uchun API yo‘q.** Uni faqat Django admin'dagi inline va ModelAdmin orqali boshqarish mumkin (`curriculum/admin.py:24-29,61-65`).

### 2.5 Autentifikatsiya va rollar

- JWT (SimpleJWT): access tokeni 1 soat, refresh tokeni 7 kun, rotatsiya va blacklist yoqilgan (`settings.py:180-185`). Lekin `rest_framework_simplejwt.token_blacklist` `INSTALLED_APPS` da yo‘q, shuning uchun blacklist ishlamaydi. Kutubxona `blacklist()` metodini faqat shu app o‘rnatilganda qo‘shadi (`venv/.../rest_framework_simplejwt/tokens.py:265`), refresh serializer esa `AttributeError` ni jim yutadi (`serializers.py:129-134`).
- Rollar Django guruhlari orqali (`setup_roles.py:14-16`), `role` maydoni esa hisoblanadi (`accounts/serializers.py:84-89`).
- **Nomuvofiqlik:** Topic/Resource yozuvi `Instructor` guruhiga ruxsat beradi (`curriculum/views/instructor.py:30-37`). Savollar va import esa faqat `is_staff` ga ruxsat beradi (`assessments/views/instructor.py:22,163`). Frontend'dagi `AdminRoute` ham faqat `is_staff` ni tekshiradi (`src/components/AdminRoute.tsx:10,29`). Natijada `is_staff=False` bo‘lgan o‘qituvchi o‘qituvchi panelini ocha olmaydi.

### 2.6 Tranzaksiyalar va qulflar

| Mexanizm | Joy | Izoh |
|---|---|---|
| `@transaction.atomic` | `orchestrator.py:119` (process_submission), `:296` (cascade) | Javob qayta ishlanishi atomar |
| `select_for_update` | `orchestrator.py:161-176` | `UserKnowledgeState` qatori. SQLite'da `FOR UPDATE` e’tiborsiz qoldiriladi, ketma-ketlikni butun bazaga qo‘yiladigan yozish qulfi ta’minlaydi |
| `transaction.atomic` | `assessments/views/instructor.py:202` (import), `serializers/instructor.py:39,52`, `analytics/views/dashboard.py:66` (faqat o‘qish uchun — ortiqcha), seed buyruqlari | — |
| **Advisory lock** | **topilmadi** | BB9 bajarilmagan |
| Daraxt/graf yozuvlari | `InstructorTopicViewSet`, `TopicPrerequisite.save` | Tranzaksiya ham, qulf ham yo‘q. `ATOMIC_REQUESTS` yoqilmagan |
| `SubmitTestSessionView` | `assessments/views/assessment.py:85-213` | Atomar emas, qulf yo‘q, read-modify-write (`:179-193`) |

---

## 3. Frontend

Frontend alohida repozitoriyda: `~/Desktop/neuro/neuro` (README'da nomi “Knowledge Bloom”, Lovable/Supabase shablonidan boshlangan).

### 3.1 Sahifalar va marshrutlar (`src/App.tsx:36-63`)

| Marshrut | Sahifa | Rol | Backend |
|---|---|---|---|
| `/`, `/auth` | Index/Landing, Auth | ochiq | token, register |
| `/dashboard` | Dashboard | talaba | `/api/analytics/overview/` |
| `/learning-path` | LearningPath (daraxt yoki DAG rejimi) | talaba | tree + prerequisite-graph |
| `/topic/:id`, `/course` | Course (resurslar + DiagnosticsPanel) | talaba | `instructor/topics/<id>`, resources, diagnostics |
| `/assessment` | Assessment (testlar ro‘yxati) | talaba | `/api/assessments/tests/` |
| `/topic/:id/assessment` | QuizSession | talaba | **test_session / submit_test_session** |
| `/courses`, `/search`, `/mistakes`, `/profile`, `/tutor` | yordamchi sahifalar | talaba | Mistakes — `localStorage` (`src/lib/mistakeStorage.ts`); Tutor — Supabase |
| `/instructor/curriculum` | CurriculumManager | `is_staff` | topics/questions/resources CRUD, import |
| `/instructor/curriculum-builder` | CurriculumBuilder | `is_staff` | xuddi shu |
| `/admin/users` | UserManagement | `is_staff` | users |

### 3.2 API qatlami va holat boshqaruvi

- `src/api/client.ts`: axios, `Bearer` interceptor, 401 kelganda refresh qilinadi, keyin logout. Tokenlar `localStorage` da saqlanadi (`src/api/auth.api.ts:16-17`).
- Holat: auth uchun zustand (`src/store/authStore.ts`). Ma’lumotlar har bir hook'da `useState/useEffect` bilan olinadi. React Query provider ulangan, lekin ishlatilmaydi.

### 3.3 Kurs daraxti va prerekvizitlar grafi

- `LearningPath.tsx:39-48`: `viewMode` `tree` yoki `dag` bo‘ladi. Daraxt rejimida qirralar `parent_id` bo‘yicha quriladi (`useLearningPath.ts:151-167`). DAG rejimida qirralar `TopicPrerequisite` dan olinadi (`usePrerequisiteGraph.ts:115-122`). Joylashuvni dagre hisoblaydi.
- **Tahrirlash:** graf faqat o‘qish uchun. `onConnect` yoki prerekvizit qo‘shish UI'si yo‘q, o‘qituvchi sahifalarida “prereq” bo‘yicha grep 0 natija berdi. Daraxtni tahrirlash formada `parent` va `position` maydonlari orqali qilinadi (`CurriculumManager.tsx:44-45,181-192`), drag-and-drop yo‘q.
- `components/learning-path/KnowledgeGraph.tsx` hech qayerda ishlatilmaydi (o‘lik kod).

### 3.4 Talabaga holatlar, tavsiyalar va tushuntirishlar

- Tugun holati 3 xil: Locked, Mastered (`mastery_percentage >= 70`), In Progress (`CustomTopicNode.tsx:15`). Talab qilingan 5 holat yo‘q.
- **Bir xil tugun ikki rejimda ikki xil son ko‘rsatadi.** Daraxt rejimida `mastery_percentage` = javoblar aniqligi `score` (`curriculum/services/path.py:29-34`). DAG rejimida = `round(P(L)·100)` (`curriculum/views/graph.py:78`).
- Yopiq tugun bosilganda faqat umumiy “Prerequisites not met” xabari chiqadi (`LearningPath.tsx:68-72`). Qaysi prerekvizit yetishmayotgani ko‘rsatilmaydi.
- Tavsiyalar: dashboard'da 4 ta karta bor (`Dashboard.tsx:236-240`). Sabab matni frontend'da qattiq yozilgan (`:374`), backend sabab qaytarmaydi.
- `Assessment.tsx:207-226` `mastery_percentage` ni “%” bilan ko‘rsatadi va `>= 70` bilan solishtiradi. Backend esa BKT yo‘lida 0–1, test sessiyasidan keyin 0–100 shkalani qaytaradi (`assessments/views/assessment.py:240,187`). Natijada UI'da “0.8%” yoki “100%” chiqadi.
- **BKT/IRT oqimi UI'ga ulanmagan:** `useAdaptiveQuiz` (`src/hooks/useAdaptiveQuiz.ts`) va `QuizEngine` hech bir sahifada ishlatilmaydi. Yagona test oqimi `QuizSession` → `submit_test_session` (`src/pages/QuizSession.tsx:47,83`).

---

## 4. Joriy algoritmlar

### 4.1 Prerekvizit qo‘shishdagi sikl tekshiruvi

- **Joy:** `curriculum/models.py:182-207` (`TopicPrerequisite.clean`). U `save()` ichidan chaqiriladi (`:209-211`).

```python
visited, stack = set(), [self.prerequisite_id]
while stack:
    curr_id = stack.pop()
    if curr_id == self.topic_id:
        raise ValidationError("... creates a cycle ...")
    if curr_id in visited: continue
    visited.add(curr_id)
    qs = TopicPrerequisite.objects.filter(topic_id=curr_id)
    stack.extend(qs.values_list("prerequisite_id", flat=True))
```

- **Qachon chaqiriladi:** har bir `save()` da (admin, seed). REST API yo‘q.
- **Murakkabligi:** O(V+E), lekin har bir ko‘rilgan tugun uchun 1 ta SQL so‘rov bor, ya’ni O(V) round-trip.
- **Mantiqiy xatolar:**
  - Tekshiruv tugunlar grafida bajariladi, G_L'da emas (ES1). Probe: `B requires A` va `a1 requires b1` (a1∈A, b1∈B) qabul qilindi, garchi G_L'da a1→b1→a1 sikli hosil bo‘lsa ham.
  - Sikl zanjiri qaytarilmaydi, faqat matnli xabar beriladi.
  - Y2 tekshirilmaydi: probe'da ajdod→avlod prerekviziti qabul qilindi.
  - Poyga holati (TOCTOU): tekshiruv va INSERT orasida qulf yo‘q. Ikkita parallel so‘rov birgalikda sikl yaratishi mumkin.
  - `QuerySet.bulk_create` yoki `update()` orqali yozilsa, `clean()` umuman chaqirilmaydi.

### 4.2 Daraxtni o‘zgartirish

- **Joy:** `InstructorTopicViewSet.perform_create/update/destroy` (`curriculum/views/instructor.py:76-91`), admin'dagi `DraggableMPTTAdmin` (`curriculum/admin.py:33`). Saqlash MPTT'ga topshiriladi.
- **Tekshiruvlar:** serializer'da parent bo‘yicha validatsiya yo‘q. Y1 ni faqat MPTT kutubxonasi `InvalidMove` bilan tekshiradi (`venv/.../mptt/managers.py:1164-1169`). Probe: serializer `is_valid()=True` qaytardi, keyin `save()` da `mptt.exceptions.InvalidMove` chiqdi. Bu ushlanmaydi, demak API **HTTP 500** qaytaradi.
- **O‘chirish:** `parent` CASCADE (`curriculum/models.py:44-50`) butun shoxni o‘chiradi. Undan keyin `Question` → `AssessmentAttempt` ham CASCADE bilan o‘chadi (`assessments/models.py:55-60,241-245`), ya’ni tugun o‘chsa javoblar logi ham yo‘qoladi.
- **Murakkabligi:** MPTT'da qo‘shish yoki ko‘chirish O(n) qatorni yangilaydi (`lft/rght` siljishi). Global qulf yo‘q.
- **Xatolar:** Y2/Y3 qayta tekshirilmaydi (BB8). Redis bo‘lmasa yozuv saqlanadi, lekin javob 500 bo‘ladi (`:91`). `_invalidate_tree_cache` hech narsa keshlanmagan joyni tozalaydi.

### 4.3 Mavzuni ochish (unlock) qoidasi

To‘rt xil joyda, to‘rt xil semantika bilan yozilgan:

| Joy | Prerekvizit bo‘lsa | Prerekvizit bo‘lmasa (fallback) |
|---|---|---|
| `curriculum/services/graph.py:108-156` (`is_unlocked_dag`) | barcha prereq `mastery_percentage ≥ 0.70` | ildiz bo‘lsa True. Ota holati **yo‘q** bo‘lsa True (`:154-156`), aks holda ota ≥ 0.70 |
| `curriculum/views/topic.py:112-119` (daraxt API) | xuddi shu | ildiz yoki ota ≥ 0.70 (holat yo‘q bo‘lsa — yopiq) |
| `curriculum/views/graph.py:62-67` (DAG API) | xuddi shu | ildiz yoki ota `mastery_level ≥ 1` (P ≥ 0.20) yoki ota ≥ 0.70 |
| `analytics/views/dashboard.py:118-126` | xuddi shu | `graph.py` bilan bir xil (`parent_lvl >= 1`) |

Bundan tashqari, global `Topic.is_unlocked` maydonini ikki joy o‘zgartiradi: `orchestrator.py:264-293` (P ≥ 0.70 bo‘lganda) va `assessments/views/assessment.py:197` (test o‘tilganda). Bu maydon barcha talabalar uchun umumiy. `TestsListView` (`:255`) va `Course.tsx` aynan shu global maydonni ko‘rsatadi.

- **Chegara:** `settings.MASTERY_THRESHOLD = 0.70` (`settings.py:176`), `orchestrator.MASTERY_THRESHOLD = 70` (`orchestrator.py:60`), `CustomTopicNode` da `>= 70`. Histerezis yo‘q.
- **Murakkabligi:** daraxt va DAG API'lari O(V+E), har so‘rovda qaytadan hisoblanadi.
- **Xatolar:**
  - Meros yo‘q. Probe: `B requires A`, A o‘zlashtirilmagan, lekin b1 ∈ B ochiq (`is_unlocked_dag(b1)=True`), chunki b1 ning o‘z prerekviziti yo‘q va u ota tugunga fallback qiladi.
  - Ochiq mavzu keyin qayta yopilishi mumkin: yangi prerekvizit qo‘shilsa yoki P pasaysa, holat har safar qaytadan hisoblanadi (TY5 buzilgan).
  - Backend yopiq mavzuga javob berishni taqiqlamaydi: `NextQuestionView`, `SubmitAnswerView` va `TestSessionView` unlock'ni tekshirmaydi.

### 4.4 Talaba bilimini yangilash (BKT)

- **Joy:** faol dvigatel `hybrid_bkt_irt` (`settings.py:175`) → `HybridBKTIRTEngine.calculate_new_mastery` (`assessments/services/engines/hybrid_bkt_irt.py:65-133`). Oddiy BKT: `bayesian.py:104-223`.
- **Parametrlar:** modul darajasidagi global konstantalar — P(L0)=0.15, P(T)=0.20, P(G)=0.25, P(S)=0.10 (`bayesian.py:66-69`). Mavzuga bog‘liq parametr yo‘q.
- **Prior:** `UserKnowledgeHistory` dagi oxirgi `calculated_mastery` (`bayesian.py:229-248`).

```python
theta_new = self.irt_engine.update_ability(user, question, is_correct)   # 1) θ birinchi
p_learned_prior = self.bkt_engine._retrieve_prior(user, topic)          # 2) prior
modifier = (question.irt_difficulty - theta_new) * 0.05                 # 3) chiziqli
p_slip_adj  = max(0.01, min(0.40, 0.10 + modifier))
p_guess_adj = max(0.05, min(0.50, 0.25 - modifier))
num = prior*(1-S) if correct else prior*S                               # 4) Bayes
den = num + (1-prior)*(G if correct else 1-G)
post = num/den
p = post + (1-post)*0.20                                                # 5) P(T)
return max(0.0, min(1.0, p))
```

- **Qachon chaqiriladi:** `process_submission` ichida (`orchestrator.py:188-194`), faqat `/submit_answer/` orqali. Test sessiyasi bu yerdan o‘tmaydi.
- **Murakkabligi:** O(1). Javob uchun SQL so‘rovlar soni 7.6-bo‘limda.
- **Chegaraviy holatlar (probe):**
  - 3 ta ketma-ket to‘g‘ri javob: 0.15 → 0.507 → 0.824 → 0.953.
  - 6 ta ketma-ket xato javob: P(L) 0.15 → 0.220 → … → 0.242 tomon *o‘sadi* (P(T)=0.2 sababli). Bu klassik BKT xatti-harakati, lekin baholashda e’tiborga olish kerak.
  - G < 1−S doim bajariladi (max G=0.5, min 1−S=0.6), shuning uchun to‘g‘ri javob posteriorni kamaytirmaydi.
- **Xatolar:**
  - `_retrieve_prior` `algorithm_used` bo‘yicha filtrlamaydi (`bayesian.py:237-243`). Dvigatel `streak` dan almashtirilsa, prior 0–4 oralig‘ida bo‘ladi, `den` manfiy chiqishi mumkin, natija esa faqat oxiridagi clamp tufayli [0,1] da qoladi.
  - Test sessiyasi `state.mastery_percentage` ni o‘zgartiradi, tarixga esa yozmaydi. Shu sababli BKT prior'i va ko‘rsatilayotgan P bir-biridan ajralib ketadi.
  - Tarix yozuvi javob logiga FK orqali bog‘lanmagan.

### 4.5 Guess va slip

- **Joy:** gibrid uchun `hybrid_bkt_irt.py:83-88`, oddiy BKT uchun `bayesian.py:141-145` (qiyinlik bo‘yicha: `(d−1)·0.05`, P(S) ≤ 0.40, P(G) ≥ 0.05).
- **Formula:** chiziqli, P(S)=clip(0.10+0.05(b−θ), 0.01, 0.40), P(G)=clip(0.25−0.05(b−θ), 0.05, 0.50). Bu II bobdagi sigmoid formula emas (TM2 → Farqli).
- **Chegara:** clamp tufayli P(S) manfiy bo‘lmaydi. P(G) 0.5 gacha chiqadi, II bobda esa yuqori chegara 0.3. Gradient |b−θ| > 3 bo‘lganda to‘yinadi.

### 4.6 θ va b ni yangilash

- **Joy:** `IRTEngine.update_ability` (`assessments/services/engines/irt.py:66-108`).

```python
ability_obj, _ = UserAbility.objects.get_or_create(user=user, topic=question.topic)
p_hat = 1/(1+exp(-a*(theta_old-b)))          # 2PL, a = question.irt_discrimination
theta_new = theta_old + 0.3*(y - p_hat)      # K = const 0.3 (irt.py:40)
ability_obj.theta = theta_new; ability_obj.save()
```

- **Qachon chaqiriladi:** gibrid dvigatelda BKT'dan **oldin** (TM6 tartibiga zid).
- **Xatolar:**
  - θ talaba×mavzu juftligi uchun saqlanadi (`assessments/models.py:268-299`, ES5).
  - b hech qachon yangilanmaydi: kodda `irt_difficulty` ga yozuv topilmadi, b faqat seed'da beriladi.
  - K(n) kamaymaydi (ES6). θ cheklanmagan (docstring'da [−3, 3] deyilgan, lekin clamp yo‘q).
  - Bo‘lim bo‘yicha test topshirilganda savol tanlash `UserAbility(user, bo‘lim)` dan foydalanadi (`question_selection.py:66`), yangilash esa `UserAbility(user, question.topic=barg)` ga yoziladi. Natijada tanlovdagi θ doim 0 bo‘lib qoladi.
  - Hisoblangan `p_hat` faqat log'ga chiqariladi va saqlanmaydi.

### 4.7 Yangi mavzu uchun P(L0)

- **Joy:** `bayesian.py:66` (`DEFAULT_P_INIT = 0.15`), `:245-248` (tarix bo‘lmasa).
- **Mantiq:** barcha talaba va mavzular uchun bir xil o‘zgarmas son. Prerekvizitlarga, λ ga, c=τ−0.05 ga bog‘liqlik yo‘q (TM5 → Yo‘q).
- **Xato:** `_cascade_mastery_to_descendants` (`orchestrator.py:296-337`) bo‘lim o‘zlashtirilganda barcha avlod mavzularga `mastery_percentage=1.0`, `score=100`, `total_attempts=0` yozadi. Probe: S bo‘limida 2 ta to‘g‘ri javobdan keyin (P=0.824) l1 va l2 → `(1.0, 0 urinish)`. Bu talaba hali ko‘rmagan mavzuga dalilsiz P=1 berish demak.

### 4.8 Topologik saralash

- **Joy:** `curriculum/services/graph.py:47-105` (`topological_order`). **Faqat testlarda chaqiriladi** (`curriculum/tests/test_dag.py:121`). Ishlab chiqarish kodida, jumladan tavsiyalarda, ishlatilmaydi.
- **Mantiq:** Kahn algoritmi, `deque` (FIFO). Boshlang‘ich navbat va har bir tugunning qo‘shnilari `(position, id)` bo‘yicha saralanadi (`:77-95`), lekin bu global ustuvor navbat emas.
- **Murakkabligi:** O(V log V + E log E), 1 ta SQL so‘rov.
- **Xatolar:**
  - Sikl bo‘lsa yoki tugunlar soni n dan kam chiqsa, xato qaytmaydi: qolgan tugunlar oxiriga jim qo‘shib qo‘yiladi (`:97-103`).
  - `lev(v)` hisoblanmaydi.
  - Tugunlar grafida ishlaydi, G_L'da emas. Probe tartibi `['A','b1','B','a1']` G_L'dagi a1→b1 qirrasini buzadi.
  - `position` faqat aka-ukalar orasidagi tartib, shuning uchun turli shoxlardagi tugunlarni u bo‘yicha solishtirish ma’nosiz.

### 4.9 Tavsiyalar va o‘quv trayektoriyasi

- **Joy:** `analytics/views/dashboard.py:172-208`. To‘rt xil alohida evristika:

| Kalit | Qoida | Qator |
|---|---|---|
| `recommended_next` | `position,id` bo‘yicha birinchi ochiq barg, `level < 4` | `:172-176` |
| `needs_revision` | urinishi bor va P < 0.70 bo‘lgan ochiq barglar orasida **argmin P** | `:179-183` |
| `ready_to_advance` | urinishi yo‘q birinchi ochiq tugun (fallback bilan) | `:186-195` |
| `coming_soon` | birinchi yopiq bo‘lim yoki tugun | `:198-208` |

- **Xatolar:**
  - A/B/C/D guruhlari, ta’sir(v), topologik tartib va Need_s(g) yo‘q.
  - Sabablar qaytarilmaydi.
  - `all_topics` `position,id` bo‘yicha saralangan (`:142`), ya’ni turli shoxlardagi tugunlarning tartibi tasodifiy.
  - Har bir so‘rovda barcha tugunlar uchun unlock qaytadan hisoblanadi.
- **Qo‘shimcha:** `_maybe_skip_easy_questions` (`orchestrator.py:345-424`) M+H aniqligi ≥70% bo‘lsa, javob berilmagan barcha Easy savollar uchun **sun’iy to‘g‘ri `AssessmentAttempt`** yaratadi. Probe: 3 ta real javobdan keyin logda 7 ta yozuv bo‘ldi. Yozuvlar belgilanmagan, tarix qatori yozilmaydi va bu dashboard aniqligini sun’iy oshiradi.

---

## 5. II bob talablariga moslik jadvali

| ID | Talab | Holat | Dalil | Izoh |
|---|---|---|---|---|
| BB1 | kurs→bo‘lim→mavzu, ichma-ich bo‘lim, mavzu = barg, pos | Qisman | `curriculum/models.py:20-95` | Bitta `Topic` modeli, tugun turi yo‘q, barg ekanligi majburiy emas. `position` bor |
| BB2 | Qo‘shni ro‘yxat + rekursiv CTE (tree-queries), mptt faqat benchmark'da | Farqli | `curriculum/models.py:17,20`, `settings.py:34` | MPTT (lft/rght) ishlatiladi. tree-queries o‘rnatilgan, lekin ulanmagan |
| BB3 | Istalgan ikki tugun orasida prerekvizit, ω ∈ (0,1] (standart 1) | Qisman | `curriculum/models.py:156-178` | Istalgan tugunlar orasida qo‘yish mumkin. ω maydoni yo‘q |
| BB4 | Bo‘lim prerekviziti barglarga meros bo‘ladi (G_L) | Yo‘q | `graph.py:141-156`, probe | Meros o‘rniga ota tugunga fallback ishlaydi. G_L qurilmaydi |
| BB5 | Y1: yangi ota tugun avlod bo‘lmasin | Qisman | `mptt/managers.py:1164-1169`, `views/instructor.py:81-83` | MPTT `InvalidMove` chiqaradi, u ushlanmaydi va 500 qaytadi. Validatsiya yo‘q |
| BB6 | Y2: o‘zi, ajdodi yoki avlodi bilan bog‘lanmaydi | Yo‘q | `models.py:184-186`, probe | Faqat o‘ziga bog‘lanish tekshiriladi. Ajdod→avlod qabul qilindi |
| BB7 | Y3: G_L'da Leaves(y) dan BFS, sikl zanjiri qaytariladi | Farqli | `models.py:188-207`, probe | Tugunlar grafida DFS. Barg darajasidagi sikl qabul qilindi. Zanjir qaytarilmaydi |
| BB8 | Daraxt o‘zgarganda Y2/Y3 tranzaksiyada tekshiriladi, buzilsa rollback | Yo‘q | `views/instructor.py:76-87` | Hech qanday tekshiruv yo‘q |
| BB9 | Umumiy qulf (advisory lock) | Yo‘q | grep: `advisory` 0 natija | SQLite, qulf yo‘q |
| BB10 | Savol aynan 1 ta barg mavzuga tegishli | Qisman | `assessments/models.py:55-60` | FK bitta mavzuni ta’minlaydi, lekin u barg bo‘lishi shart emas. Import ham tekshirmaydi |
| GR1 | G_L, topologik tartib va ko‘rsatkichlar KB versiyasiga bog‘langan keshda | Yo‘q | grep: `cache.set/get` 0 natija; `views/instructor.py:91` | Faqat `delete_pattern` bor. Versiya tushunchasi yo‘q |
| GR2 | Kahn + pos ustuvor navbat, lev(v), n dan kam bo‘lsa xato | Farqli | `graph.py:47-105` | FIFO + lokal saralash, lev yo‘q, qoldiq jim qo‘shiladi. Faqat testlarda ishlatiladi |
| GR3 | Desc*, ortiqcha qirralar, κ, o‘qituvchiga ogohlantirish | Yo‘q | `graph.py:23-44` | Faqat Anc* (`get_all_prerequisites`), u ham faqat testlarda |
| TM1 | Har bir mavzu uchun P0, P(T), G0, S0 | Qisman | `bayesian.py:66-69` | To‘rt parametr bor, lekin global konstanta |
| TM2 | Sigmoid G/S formulasi, chiziqli tuzatish bo‘lmasligi kerak | Farqli | `hybrid_bkt_irt.py:83-88`, `bayesian.py:141-145` | Chiziqli Δ·0.05, P(S) ≤ 0.40, P(G) ≥ 0.05 — taqiqlangan variantning o‘zi |
| TM3 | θ_s talaba uchun bitta, b_q savol uchun | Farqli | `assessments/models.py:268-299,77-80` | θ talaba×mavzu uchun. b savolda bor, lekin statik |
| TM4 | Elo: p=σ(θ−b), θ+=K(n)(x−p), b−=K(n)(x−p), K(n)=α/(1+βn) | Farqli | `irt.py:40,86-90` | Faqat θ yangilanadi, K=0.3 o‘zgarmas, 2PL'dagi a ishlatiladi |
| TM5 | P(L0)=min{(1−λ)P0+λ·m̄, c} | Yo‘q | `bayesian.py:66,245-248` | P(L0)=0.15 o‘zgarmas |
| TM6 | Tartib: P(L0)→G,S→p̂ saqlash→Bayes→P(T)→Elo→tayyorlik | Farqli | `hybrid_bkt_irt.py:77-115`, `orchestrator.py:152-247` | θ birinchi yangilanadi, p̂ yo‘q, tayyorlik o‘rniga global unlock va cascade |
| TM7 | Logda: talaba, savol, mavzu, natija, vaqt, p̂, keyingi P(L) | Qisman | `assessments/models.py:235-252,333-356` | `topic`, p̂ yo‘q. P(L) alohida jadvalda, FK'siz |
| TY1 | Ikki chegarali M: τ=0.95, δ=0.1, sozlanadigan | Farqli | `settings.py:176`, `orchestrator.py:60,228-240` | Bitta chegara 0.70, 3 joyda har xil yozilgan, histerezis yo‘q |
| TY2 | R=1 ⇔ barcha bevosita prereq'lar uchun M=1, fallback yo‘q | Farqli | `graph.py:126-156`, `views/topic.py:112-119` | AND mantiq bor, lekin ota tugunga fallback ham bor (ES2) |
| TY3 | `yetishmaydi_s(w)` hisoblagichi, Succ faqat M o‘zgarsa yangilanadi | Yo‘q | — | Topilmadi. Har so‘rovda to‘liq qayta hisoblanadi |
| TY4 | r_s(w) = min P(L) + yetishmayotgan prereq'larni tushuntirish | Yo‘q | `LearningPath.tsx:68-72` | Faqat umumiy toast chiqadi |
| TY5 | Boshlangan mavzu qayta yopilmaydi | Yo‘q | `views/topic.py:112-119` | Holat saqlanmaydi, shuning uchun qayta yopilish mumkin |
| TY6 | KB versiyasi o‘zgarsa, keyingi so‘rovda qayta hisoblash | Yo‘q | — | Versiya yo‘q |
| TR1 | 5 holat: yopiq, ochiq, o‘rganilmoqda, o‘zlashtirilgan, takrorlash kerak | Farqli | `CustomTopicNode.tsx:15-31`, `assessments/models.py:31-37` | UI'da 3 holat. `MasteryLevel` — bu daraja, holat emas |
| TR2 | A–D guruhlari tartib bilan | Farqli | `dashboard.py:172-208` | 4 ta alohida yagona tavsiya |
| TR3 | Har bir tavsiya sababi bilan | Yo‘q | `dashboard.py:210-239` | Sabab maydoni yo‘q |
| TR4 | Need_s(g) maqsadli yo‘l | Yo‘q | — | Topilmadi (`get_all_prerequisites` P(L) ni hisobga olmaydi va ishlatilmaydi) |
| TR5 | Frontend'da holatlar, tavsiyalar va maqsadli yo‘l | Qisman | `LearningPath.tsx`, `Dashboard.tsx:236-376` | Holat va tavsiyalar bor, maqsadli yo‘l yo‘q |
| EX1 | Anonimlashtirilgan, pyKT bilan mos eksport | Yo‘q | grep: `pykt`, `export` 0 natija | — |
| EX2 | Oflayn baholash (BKT, Elo, PFA, …, DKT, AKT), 5-fold | Yo‘q | — | Topilmadi |
| EX3 | AUC, RMSE, accuracy; 3/5 urinish; H1 metrikalari | Yo‘q | — | Topilmadi |
| EX4 | Bootstrap CI, DeLong, Holm | Yo‘q | — | Topilmadi |
| EX5 | mptt va tree-queries benchmarki (shakllar, 10³–10⁵, yozish, parallel, 30×, p95) | Qisman | `curriculum/management/commands/benchmark_tree.py` | Faqat descendants'ni mavjud ma’lumotda o‘qiydi. CTE xom SQL'da yozilgan, faqat o‘rtacha vaqt, yozish va p95 yo‘q |
| EX6 | Rozilik va anonimlashtirish (O‘RQ-547) | Yo‘q | `accounts/tasks.py:12-37` | Faqat 30 kunlik hard-delete bor. Rozilik va anonimlashtirish yo‘q |
| SN1 | Algoritmlar uchun unit testlar | Qisman | `curriculum/tests/test_dag.py`, `assessments/tests/*` | Joriy algoritmlar uchun bor (DFS, Kahn, BKT chegaralari, θ yo‘nalishi), II bob algoritmlari uchun yo‘q |
| SN2 | Hypothesis xossa testlari | Yo‘q | venv'da `hypothesis` yo‘q | — |
| SN3 | Locust yuklama testi | Yo‘q | — | Topilmadi |

### ES: eski muammolar

| ID | Muammo | Holat | Dalil | Izoh |
|---|---|---|---|---|
| ES1 | Sikl tugunlar grafida DFS bilan izlanadi | Hali bor | `curriculum/models.py:188-207` | Probe tasdiqladi |
| ES2 | θ=0.70 chegara + ota tugunga fallback | Hali bor | `settings.py:176`, `orchestrator.py:60`, `graph.py:141-156`, `views/topic.py:117-119` | — |
| ES3 | Daraxt django-mptt'da | Hali bor | `curriculum/models.py:17-27`, migratsiya 0005/0006 | — |
| ES4 | Chiziqli G/S, P(S) manfiy bo‘lishi mumkin | Hali bor (qisman tuzatilgan) | `hybrid_bkt_irt.py:85-88`, `bayesian.py:141-145` | Chiziqli formula qolgan. Clamp tufayli P(S) ≥ 0.01, manfiy bo‘lmaydi |
| ES5 | θ talaba×mavzu juftligi uchun | Hali bor | `assessments/models.py:268-299` | — |
| ES6 | Elo qadami o‘zgarmas η=0.3 | Hali bor | `irt.py:40` | — |
| ES7 | Uchta alohida tavsiya funksiyasi (argmin bilan) | Hali bor | `dashboard.py:172-208` | Endi 4 ta. `needs_revision` = argmin P |
| ES8 | Simulyatsiya ma’lumotlari baholashda ishlatilgan | Aniq emas | `assessments/management/commands/simulate_bkt_data.py`, `seed_thesis_demo.py:352-397` | Simulyatsiya generatorlari bor, baholash kodi yo‘q. Dissertatsiya natijalari qaysi ma’lumotdan olingani repodan aniqlanmaydi |

---

## 6. Eksperimentlarga tayyorlik

**Javoblar logi.** U `AssessmentAttempt` (`assessments/models.py:227-265`) va unga bog‘lanmagan `UserKnowledgeHistory` (`:317-373`) ga bo‘lingan.

| Kerakli maydon | Holat |
|---|---|
| talaba | `AssessmentAttempt.user` |
| savol | `AssessmentAttempt.question` |
| mavzu | **yo‘q**, faqat `question.topic` orqali (savol ko‘chirilsa, tarix ham o‘zgaradi) |
| natija | `is_correct` |
| vaqt | `answered_at` |
| urinish raqami | **yo‘q**, tartibdan hisoblash mumkin |
| model bashorati p̂ | **yo‘q** |
| keyingi P(L) | `UserKnowledgeHistory.calculated_mastery`, lekin attempt'ga FK yo‘q |

Ma’lumotlar sifatiga xavflar:

- Easy-skip sun’iy yozuvlari belgilanmagan (`orchestrator.py:404-419`).
- Test sessiyasi yozuvlarida tarix qatori yo‘q (`assessments/views/assessment.py:156`).
- Seed vaqt tamg‘alarini qayta yozadi (`seed_thesis_demo.py:387-397`).
- Tugun o‘chirilsa javoblar CASCADE bilan o‘chadi. Foydalanuvchi 30 kundan keyin hard-delete qilinadi (`accounts/tasks.py:22-32`).
- `seed_data` buyrug‘i so‘ramasdan barcha mavzu, savol, javob va tarixni o‘chiradi (`curriculum/management/commands/seed_data.py:28-34`). `simulate_bkt_data --clear` barcha `is_staff=False` foydalanuvchilarni `QuerySet.delete()` bilan *hard* o‘chiradi (`simulate_bkt_data.py:63-70`).

| Savol | Javob |
|---|---|
| Anonimlashtirib eksport qilish | Topilmadi |
| pyKT / pyBKT / DBE-KT22 / ASSISTments 2009 | Topilmadi (kod, notebook va skriptlar yo‘q) |
| AUC, RMSE, statistik testlar | Topilmadi |
| mptt va tree-queries benchmarki | Qisman: `benchmark_tree.py` faqat `get_descendants` ni joriy bazada 3 ta tugun uchun o‘lchaydi. CTE xom SQL'da, natija — o‘rtacha vaqt va so‘rovlar soni. Yozish, parallellik, yaxlitlik, daraxt shakllari, 10³–10⁵ hajmlar va p95 yo‘q. SQLite'da ishlaydi |
| Simulyatsiya qilingan ma’lumotlar | `simulate_bkt_data.py:173-203`: to‘g‘ri javob ehtimoli faqat qiyinlikka bog‘liq (0.8 / 0.5 / 0.2), bilim holati generativ jarayonda yo‘q. `seed_thesis_demo.py:352-397`: deterministik naqshlar, demo egri chiziqlar uchun. `seed_data.py:290-354`: qo‘lda yozilgan P qiymatlari. Maqsadi — demo va o‘rganish egri chiziqlari, baholash kodi yo‘q |

H1–H4 bo‘yicha tayyorlik:

- **H1:** ehtimoliy va bajarilganlik qoidalarini almashtirish mexanizmi yo‘q. “Tayyor bo‘lmagan holda o‘tish” logda belgilanmaydi.
- **H2:** taqqoslanadigan modellar yo‘q, p̂ saqlanmaydi.
- **H3:** prerekvizitli P(L0) yo‘q.
- **H4:** CTE implementatsiyasi va yozish benchmarki yo‘q.

---

## 7. Testlar va sifat

### 7.1 Mavjud testlar

| Fayl | Testlar | Nimani tekshiradi |
|---|---|---|
| `analytics/tests/test_diagnostics.py` | 2 | Diagnostika endpoint'i: 401 va javob shakli |
| `assessments/tests/test_bayesian.py` | 2 | P(L) ∈ [0,1] (50 ta to‘g‘ri / 50 ta xato javob, mock bilan); parallel javoblar (SQLite'da `OperationalError` kelsa, javob jim tashlab yuboriladi) |
| `assessments/tests/test_irt_hybrid.py` | 5 | 2PL formulasi, θ yo‘nalishi, gibrid ≠ BKT, eng yaqin b ni tanlash |
| `assessments/tests/test_test_session.py` | 3 | 40/30/30 taqsimot, sessiya endpoint'i, vaznli baholash. Test `mastery_percentage == 100.0` ni tasdiqlaydi, ya’ni shkala xatosini “to‘g‘ri” deb qotirib qo‘yadi (`:140`) |
| `curriculum/tests/test_dag.py` | 7 | O‘ziga, to‘g‘ridan-to‘g‘ri va tranzitiv sikl; Kahn; tranzitiv yopilma; AND-unlock; graf API |
| `curriculum/tests/test_mptt_tree.py` | 25 | MPTT descendants, ancestors, children, lft/rght, global `is_unlocked` |
| `curriculum/tests/test_seed_thesis_demo.py` | 2 | Seed va idempotentlik |
| `curriculum/tests/test_fix_demo_resources.py` | 2 | Resurs nomlarini tozalash |
| `accounts/tests.py` | 0 | Bo‘sh |
| Frontend `src/test/example.test.ts` | 1 | Trivial misol |

### 7.2 Ishga tushirish natijalari

| Buyruq | Natija |
|---|---|
| `pytest -p no:cacheprovider` (in-memory SQLite test bazasi) | **49 passed**, 0 failed (8.6 s) |
| Coverage (`coverage` paketi scratchpad'ga o‘rnatildi, venv o‘zgartirilmadi) | **68%** (2 083 ta statement, 672 tasi qamrab olinmagan). Eng pastlari: `assessments/views/instructor.py` 16%, `analytics/views/dashboard.py` 25%, `simulate_bkt_data.py` 0%, `accounts/tasks.py` 0%, `streak.py` 44%. `benchmark_tree.py` va `seed_data.py` import qilinmaydi (0%) |
| `python manage.py check` | `System check identified no issues (0 silenced).` |
| `python manage.py makemigrations --check --dry-run` | `No changes detected` |
| Frontend `npm run lint` (`eslint .`) | **Yiqildi:** 83 muammo (71 error, 12 warning), asosan `no-explicit-any` |
| Frontend `tsc --noEmit -p tsconfig.app.json` | **18 xato** (masalan, `Course.tsx:303` `duration_minutes`, `LearningPath.tsx:252` NodeTypes, `Profile.tsx:63-71`) |
| Frontend `vite build` (`--outDir` scratchpad'ga) | O‘tdi. JS bundle 2.36 MB (gzip 659 kB), 500 kB chegarasi haqida ogohlantirish |
| Frontend `vitest run` | 1 passed |

Qo‘shimcha probe testlar scratchpad'da yozildi (repozitoriyga yozilmagan) va in-memory test bazasida ishga tushirildi. Natijalari 4-bo‘limda keltirilgan.

**Ishga tushirilmagan narsalar:** lokal Redis (6379) va PostgreSQL (5432) portlari ochiq, lekin loyiha SQLite'dan foydalanadi. Haqiqiy `db.sqlite3` va Redis'ga ulanilmadi. Testlar Redis'ga tegmaydi. `benchmark_tree`, `seed_*` va `simulate_bkt_data` haqiqiy bazani o‘zgartirgani uchun ishga tushirilmadi.

### 7.3 Xavfsizlik va sozlamalar

| Masala | Dalil |
|---|---|
| `SECRET_KEY` git'da kuzatiladigan faylda ochiq turibdi | `config/settings.py:11` (qiymat yozilmadi) |
| `DEBUG = True` | `settings.py:14` |
| `ALLOWED_HOSTS = ["*"]` | `settings.py:16` |
| `CORS_ALLOW_ALL_ORIGINS = True` + `CORS_ALLOW_CREDENTIALS = True` | `settings.py:200-201` |
| `X_FRAME_OPTIONS = "ALLOWALL"` (standart bo‘lmagan qiymat, clickjacking himoyasi amalda o‘chadi) | `settings.py:203` |
| Demo hisoblar parollari bilan git'da | `readme.Md:15-18`, `seed_thesis_demo.py:342-343,422-425`, `simulate_bkt_data.py` (`create_user` paroli) |
| Backend `.env` da GitHub token ko‘rinishidagi satr (gitignored, kodda ishlatilmaydi). Agar u haqiqiy token bo‘lsa, bekor qilish tavsiya etiladi | `.env` (1 qator) |
| JWT tokenlari `localStorage` da (XSS bo‘lsa o‘g‘irlanishi mumkin) | `src/api/auth.api.ts:16-17` |
| `PrerequisiteGraphView`, `DownloadQuestionTemplateView` — AllowAny | `curriculum/views/graph.py:34`, `assessments/views/instructor.py:234` |
| Talaba `/api/curriculum/instructor/topics/` ni o‘qiy oladi (Course sahifasi shundan foydalanadi) | `curriculum/views/instructor.py:33-34`, `Course.tsx:64` |
| Talaba yopiq mavzu savollariga javob bera oladi | `assessments/views/assessment.py` (unlock tekshiruvi yo‘q) |
| Frontend `arms_cache/...` trace fayli git'da kuzatiladi | `git ls-files` |
| `db.sqlite3`, `media/`, `.env`, `venv/` gitignored | `.gitignore:1-3,16` |

### 7.4 Samaradorlik

- **N+1:**
  - `TestsListView` har bir tugun uchun `get_descendants` + `count` + `exists` + iteratsiya qiladi, ya’ni bir tugunga ~4 so‘rov (`assessments/views/assessment.py:234-247`).
  - Sikl tekshiruvi va `get_all_prerequisites` ko‘rilgan har bir tugun uchun 1 so‘rov yuboradi (`models.py:203-206`, `graph.py:35-37`).
  - Easy-skip har bir savol uchun `choices.filter(...)` chaqiradi (`orchestrator.py:406-407`).
  - `SubmitTestSessionView` har bir javob uchun 3 ta so‘rov yuboradi (`assessments/views/assessment.py:120-173`).
- **Keshlanmagan qayta hisoblashlar:** daraxt, DAG va dashboard endpoint'lari har so‘rovda barcha tugunlar va qirralar uchun unlock'ni qaytadan hisoblaydi (`views/topic.py:94-119`, `views/graph.py:37-67`, `dashboard.py:135-167`). Redis sozlangan, lekin hech narsa keshlanmaydi.
- **Har bir javobdan keyin:** butun graf qayta hisoblanmaydi. Biroq ~12–20 ta SQL bajariladi: attempt, state lock, history prior, ability get/save, state save, history insert, ixtiyoriy children unlock + cascade bulk upsert, easy-skip (3+ so‘rov), keyingi savol (3 so‘rov). Cascade bo‘lim kattaligiga proporsional sonda qator yozadi.

---

## 8. Claude Code xulosasi

### 8.1 Kuchli tomonlar

1. Toza qatlamlarga ajratilgan arxitektura: Strategy pattern'dagi dvigatellar (`assessments/services/engines/__init__.py:25-30`), yupqa view'lar, service qatlami. Yangi model qo‘shish oson.
2. Javobni qayta ishlash atomar, holat qatori qulflanadi (`orchestrator.py:119,161-176`), tarix ledger'i bor (`UserKnowledgeHistory`).
3. Ishlaydigan to‘liq stek: JWT, rollar, o‘qituvchi CRUD, Excel/Word import, React Flow orqali daraxt va DAG vizualizatsiyasi, θ va P(L) trendi diagnostikasi.
4. Bazaviy test to‘plami (49 test, 68% coverage), migratsiyalar sinxron, `manage.py check` toza.
5. `parent_id` allaqachon mavjud (MPTT ham shu maydonni saqlaydi), shuning uchun tree-queries'ga o‘tishda ma’lumot migratsiyasi oddiy bo‘ladi.

### 8.2 Eng katta xavflar (himoya nuqtai nazaridan)

- **Model va kod nomuvofiq:** II bobda sigmoid G/S, Elo K(n), G_L, prerekvizitli P(L0), ikki chegarali tayyorlik tasvirlangan. Kodda ularning birortasi yo‘q. Komissiya kodni ko‘rsa, “prototip modelni amalga oshiradi” degan da’vo tasdiqlanmaydi.
- **Demo yo‘li modelni chetlab o‘tadi:** frontend'dagi yagona test oqimi BKT'ni ishlatmaydi. P(L) o‘rniga 0–100 baho yoziladi, UI'da esa “0.8%” yoki “100%” chiqadi.
- **Ma’lumotlar ifloslangan:** sun’iy to‘g‘ri javoblar, avlodlarga dalilsiz P=1.0, global `is_unlocked`, logda p̂ yo‘q. Bu ma’lumotdan olingan har qanday AUC/RMSE yoki H1 natijasi ishonchsiz bo‘ladi.
- **Eksperiment kodi umuman yo‘q:** EX1–EX4 va H1–H4 natijalarini repodan qayta hosil qilib bo‘lmaydi.
- **Benchmark metodologiyasi zaif:** faqat o‘qish, faqat o‘rtacha vaqt, SQLite, tree-queries o‘rniga xom SQL. H4 yozish va parallellik qismini tekshirmaydi.
- **Maxfiy ma’lumotlar repoda** (`SECRET_KEY`, demo parollar) va O‘RQ-547 bo‘yicha rozilik mexanizmi yo‘q.

### 8.3 Ustuvorliklar ro‘yxati

**P0 — II bob modeliga zid yoki natijani buzadi**

| # | Kamchilik | Talab / gipoteza | Hajm | Fayllar |
|---|---|---|---|---|
| P0-1 | Test sessiyasi BKT'ni chetlab o‘tadi, P ni 0–100 shkalada yozadi, global unlock qiladi. UI BKT yo‘liga ulanmagan | TM6, TM7, H1–H3 | M | `assessments/views/assessment.py:85-213`, `tests/test_test_session.py`, `src/pages/QuizSession.tsx`, `src/hooks/useAdaptiveQuiz.ts`, `src/pages/Assessment.tsx` |
| P0-2 | Avlodlarga P=1.0 cascade va sun’iy Easy-skip yozuvlarini olib tashlash | TM6, TM7, EX1, H1–H3 | S | `assessments/services/orchestrator.py:240-244,296-424` |
| P0-3 | Global `Topic.is_unlocked` o‘rniga talabaga xos tayyorlik (M histerezis, R, hisoblagichlar, qayta yopilmaslik) | TY1–TY6, H1 | L | `curriculum/models.py`, `orchestrator.py`, `curriculum/services/graph.py`, `views/topic.py`, `views/graph.py`, `analytics/views/dashboard.py`, yangi model va migratsiya |
| P0-4 | G_L, meros, Y2, G_L'da BFS bilan Y3 va sikl zanjiri, daraxt o‘zgarganda tekshiruv, advisory lock (PostgreSQL talab qilinadi) | BB4, BB6–BB9 | L | `curriculum/models.py`, yangi `curriculum/services/kb.py`, `views/instructor.py`, `settings.py` (DATABASES) |
| P0-5 | Talaba modeli: sigmoid G/S, kurs bo‘yicha bitta θ_s, b_q yangilanishi, K(n), prerekvizitli P(L0), p̂ ni yangilashdan oldin saqlash, TM6 tartibi, mavzu bo‘yicha parametrlar | TM1–TM6, H2, H3 | L | `assessments/services/engines/*`, `assessments/models.py` (UserAbility, Question, yangi BKT parametrlari), `orchestrator.py`, `question_selection.py` |
| P0-6 | Unlock mantig‘ini 4 ta joydan bitta service'ga yig‘ish, ota tugunga fallback'ni olib tashlash, chegarani bir joyda sozlanadigan qilish | TY1, TY2, ES2 | M | `graph.py`, `views/topic.py`, `views/graph.py`, `dashboard.py`, `settings.py`, `CustomTopicNode.tsx` |

**P1 — eksperimentlar uchun zarur**

| # | Kamchilik | Talab / gipoteza | Hajm | Fayllar |
|---|---|---|---|---|
| P1-1 | Logni kengaytirish: `topic`, `attempt_no`, `p_hat`, `p_after`, `source` (real/test/seed), dvigatel versiyasi | TM7, EX1, H2, H3 | M | `assessments/models.py`, `orchestrator.py`, migratsiya |
| P1-2 | Anonimlashtirilgan pyKT eksporti (management command), rozilik maydoni | EX1, EX6 | M | yangi `analytics/management/commands/export_pykt.py`, `accounts/models.py` |
| P1-3 | Oflayn baholash pipeline'i: BKT, Elo, PFA, BKT+IRT(λ=0), BKT+IRT+Pre, DKT/AKT (pyKT), talabalar bo‘yicha 5-fold | EX2, H2, H3 | L | yangi `experiments/` papkasi |
| P1-4 | Metrikalar (AUC, RMSE, acc, 3/5 urinish, teng qamrovdagi xato ulushi) va statistika (bootstrap, DeLong, Holm) | EX3, EX4, H1–H3 | M | `experiments/metrics.py`, `experiments/stats.py` |
| P1-5 | Benchmark'ni qayta yozish: mptt va tree-queries modellari, 3 ta shakl, 10³–10⁵ hajm, yozish, parallel yozish + yaxlitlik, 30×, mediana/p95, PostgreSQL | EX5, H4 | L | `curriculum/management/commands/benchmark_tree.py`, alohida benchmark app |
| P1-6 | Daraxtni tree-queries'ga ko‘chirish, mptt'ni faqat benchmark'da qoldirish | BB2, ES3, H4 | M | `curriculum/models.py`, migratsiyalar, `orchestrator.py`, `question_selection.py`, `admin.py` |
| P1-7 | Kahn (ustuvor navbat, lev, n dan kam bo‘lsa xato), Desc*, ortiqcha qirralar, κ, versiyalangan kesh | GR1–GR3 | M | `curriculum/services/graph.py` |
| P1-8 | A–D trayektoriya, sabablar, Need_s(g) API + frontend | TR1–TR5 | M | `analytics/views/dashboard.py` (yoki yangi endpoint), `Dashboard.tsx`, `LearningPath.tsx`, `CustomTopicNode.tsx` |
| P1-9 | Hypothesis xossa testlari va Locust yuklama testi | SN2, SN3 | M | `*/tests/`, `locustfile.py` |

**P2 — sifat va qulaylik**

| # | Kamchilik | Talab | Hajm | Fayllar |
|---|---|---|---|---|
| P2-1 | Maxfiy qiymatlarni env'ga o‘tkazish, DEBUG/ALLOWED_HOSTS/CORS/X_FRAME_OPTIONS ni tuzatish, demo parollarni README'dan olib tashlash, `.env` dagi tokenni bekor qilish | — | S | `config/settings.py`, `readme.Md`, `seed_thesis_demo.py` |
| P2-2 | `requirements.txt` va `Pipfile` ni venv bilan sinxronlash | — | S | `requirements.txt`, `Pipfile` |
| P2-3 | `InvalidMove` → 400, Redis xatosiga chidamlilik, prerekvizit CRUD API va UI | BB5, BB3 | M | `curriculum/serializers/instructor.py`, `views/instructor.py`, frontend instructor sahifalari |
| P2-4 | N+1 larni tuzatish (TestsListView, cycle DFS, easy-skip) | — | S | `assessments/views/assessment.py`, `curriculum/models.py` |
| P2-5 | Rollarni bir xil qilish (Instructor guruhi va `is_staff`) | — | S | `assessments/views/instructor.py`, `src/components/AdminRoute.tsx` |
| P2-6 | Frontend: lint (71 error) va tsc (18 xato) ni tuzatish, o‘lik kodni olib tashlash (`KnowledgeGraph`, `QuizEngine`, supabase client) | TR5 | M | `~/Desktop/neuro/neuro/src/**` |
| P2-7 | Xavfli seed buyruqlariga himoya qo‘shish (`seed_data` hamma narsani o‘chiradi, `simulate --clear` hard delete qiladi) | EX6 | S | `curriculum/management/commands/seed_data.py`, `assessments/management/commands/simulate_bkt_data.py` |
| P2-8 | `QuerySet.delete` va hard-delete ning javoblar logini o‘chirishini nazorat qilish (CASCADE → PROTECT yoki arxiv) | EX1 | S | `assessments/models.py` |

### 8.4 Javob topilmagan savollar

1. Dissertatsiya natijalari (agar mavjud bo‘lsa) qaysi ma’lumotdan olingan: real talabalardanmi yoki `simulate_bkt_data` danmi? Repoda baholash kodi yo‘q (ES8).
2. `db.sqlite3` da real talabalar ma’lumoti bormi? Baza ataylab ochilmadi.
3. Prodakshen yoki eksperiment muhiti PostgreSQL'dami? Port 5432 ochiq, lekin loyiha SQLite'ga sozlangan. BB9 (advisory lock) va H4 uchun PostgreSQL kerak.
4. Kurs uchun alohida model nazarda tutilganmi (TM3: “θ_s kurs bo‘yicha”)? Hozir kurs = ildiz `Topic`.
5. II bobdagi α, β (K(n)), λ va mavzu bo‘yicha P0/P(T)/G0/S0 qiymatlari qayerdan olinadi (kalibratsiya qilinadimi yoki qo‘lda kiritiladimi)?
6. Backend `.env` dagi token haqiqiymi va u nima uchun saqlanadi?
7. `rest_framework_simplejwt.token_blacklist` app'i ataylab qo‘shilmaganmi? `BLACKLIST_AFTER_ROTATION=True` usiz ishlamaydi.
8. `graphify-out/` va `.agents/` repoga qo‘shilishi kerakmi?
