# NeuroLearn — tuzatish jarayoni (REMEDIATION_PROGRESS)

> **Foydalanuvchi ko‘rsatmasi (asl matn):** Backend ildizida ikkita fayl bor: NEUROLEARN_REMEDIATION.md (topshiriq) va NEUROLEARN_AUDIT.md (audit). Avval ikkalasini to‘liq o‘qi. Keyin topshiriqdagi "Ish qoidalari"ga amal qilib, 0-bosqichdan boshla. Har bir bosqich oxirida REMEDIATION_PROGRESS.md ni yangila, commit qil va menga qisqa hisobot ber. Keyingi bosqichga men "davom et" deganimdan keyin o‘t. Agar REMEDIATION_PROGRESS.md allaqachon mavjud bo‘lsa, ishni u yerda to‘xtagan joydan davom ettir.

> **Foydalanuvchi ko‘rsatmasi, 8b (asl matn):** davom et shuningdek, men NEROLEARN_B8B.md file qo‘shdim uni ham tahlil qilib bajar. Qo‘shimcha: har safar testlarni o‘tqizib chiqib tahlil qilish shart emas.

> **Foydalanuvchi ko‘rsatmasi, 7.1 va 8-bosqich (asl matn):** Backend ildiziga NEUROLEARN_B8_PLAN.md faylini qo‘shdim. Uni to‘liq o‘qi: D39–D45 qarorlari endi topshiriqning bir qismi. 0–7-bosqichlarni qabul qilaman, barcha Q qarorlari tasdiqlanadi. Avval fayldagi 2-bo‘limni — 7.1 ni — bajar (D39 kurs konstruktorining tuzilmasi, D40 haqiqiy qidiruv, D41 skrinshot skripti). Tugagach to‘xta. Keyin “davom et” deganimdan so‘ng 8a ni (D42–D45: rozilik va eksport) boshla. 8b ni alohida boshlaymiz.

> **Foydalanuvchi ko‘rsatmasi, 2-bosqich (asl matn):** davom et. Keyin: qolgan joyidan davom etilsin. Aniqlashtirish savollariga javoblar: “Algorithm” kursidagi 31 ta savol — “Savollarni o‘chirish”; savoli yo‘q barglar — “topic”.

> **Foydalanuvchi ko‘rsatmasi, 1-bosqich frontend (asl matn):** frontendni ham yuqorida aytilgani kabi o'zgartir. Desktop/neuro/neuro --> location. Aniqlashtirish savoliga javob: “1-bosqichga moslash” va tutor uchun “D24 bo‘yicha flag ortiga”.

> **Foydalanuvchi ko‘rsatmasi, 1-bosqich (asl matn):** Backend ildiziga NEUROLEARN_UI_ADDENDUM.md faylini qo‘shdim. Uni to‘liq o‘qi: undagi D20–D29 qarorlari endi NEUROLEARN_REMEDIATION.md ning bir qismi. Fayldagi 4-bo‘lim jadvalida qaysi backend qismi qaysi bosqichda kerakligi yozilgan: ularni o‘sha bosqichlarda bajar va REMEDIATION_PROGRESS.md dagi bog‘liqlik matritsasiga qo‘sh. 0-bosqichdagi Q0-5, Q0-6, Q0-7 qarorlarini tasdiqlayman. Endi 1-bosqichni boshla.

Branch: `thesis-model` (backend `~/Desktop/neuro_dj`, frontend `~/Desktop/neuro/neuro`). Push qilinmagan.

## Bosqichlar holati

| Bosqich | Holat | Backend commit'lari | Frontend commit'lari |
|---|---|---|---|
| 0 — Xavfsizlik, infratuzilma, ma’lumotlarni himoyalash | **Bajarildi** | `1d6f286`, `b44df84`, `f620171`, `332d56f`, `4067215` | `a751538`, `6c5a0a7` |
| 1 — Ma’lumot ifloslanishini to‘xtatish, javoblar logi | **Bajarildi** | `8bc4cea` (addendum), `888a96f`, `960ba2c` | `7b549fd`, `2fa1d99` |
| 2 — Bilimlar bazasi modeli | **Bajarildi** | `5e5cb09`, `79b907c` | `c259646` |
| 2.1 — Tekshiruvdagi FAIL'larni tuzatish (D30–D32, D37, D38) | **Bajarildi** | `cb41a67` | — |
| 3 — Talaba modeli | **Bajarildi** | `b1d3a08` | — |
| 4 — Tayyorlik va holatlar | **Bajarildi** | `0b15802` | — |
| 5 — Test sessiyasi modeldan o‘tadi | **Bajarildi** | `620d4e1` | — |
| 6 — Trayektoriya va API | **Bajarildi** | `3add9ef` | — |
| 7 — Frontend | **Bajarildi** | `81f745b` (D16, foydalanuvchilar) | `c2bb542` |
| 7.1 — Konstruktor tuzilmasi, qidiruv, skrinshot skripti (D39–D41) | **Bajarildi** | `f7bd3af` | `02e3b2f` |
| 8 — Eksperimentlar va rozilik (8a + 8b) | Kutilmoqda | — | — |
| 8a — Rozilik va eksport (D42–D45) | **Bajarildi** | `dc3c35c` | `3345a52` |
| 8b — Eksperimentlar quvuri (ochiq ma’lumotlar birinchi) | Qisman | — | — |
| 8b-1 — Yuklovchilar (D49–D51) va graf tahlili (D52) | **Bajarildi** | `c1a683b` | — |
| 8b-2 — H2: ASSISTments 2009 (D53, D56, D57) | **Bajarildi** — to‘liq natija `experiments/results/assist09/20261009-055443/` (D57); D55 D57 bilan hali ishga tushirilmagan | `7ff7ae2` … `e97621c`, natija `abb1fe4` | — |
| 8b-3 — H1/H3 kodi, Junyi yuklovchisi, graf nazoratlari, `run_all.py` | **Bajarildi** — H1 `junyi-h1/20261019-102526` (qo‘llab-quvvatlanmadi), H3 `junyi-h3/20261019-122423` (k=3 aniqlanmadi, k=5 qo‘llab-quvvatlanmadi); DBE-KT22 yuklovchisi va annotatsiya vositasi kechiktirildi (D62) | `056f17d` … `ac632d3` | — |
| 9 — Saqlash usullari benchmarki (H4, D63) | **Bajarildi** — to‘liq pass `20261016-093916` + D63h qayta o‘lchashi (`20261019-161430`, `20261019-163435`, `20261020-050428`); H4 qo‘llab-quvvatlanmadi | `68acf4e` … `ed45931` | — |
| 10 — Sinovlar, samaradorlik, yakuniy hisobot | **Qisman** — 1-qism bajarildi (QADAM 12: Hypothesis, `accounts`, SQL byudjeti, coverage, Locust, frontend tekshiruvi); SQL ≤ 12 va V-F2 50 foydalanuvchida bajarilmadi (D66, QADAM 12); 2-qism — `REMEDIATION_REPORT.md`, `THESIS_MAPPING.md` | `8f1f36f` … `4aee869` | — |

---

## 0-bosqich hisoboti

### Nima qilindi

- **Branch va zaxira.** Ikkala repoda `thesis-model` ochildi. `db.sqlite3` → `backups/db-20261003-0854.sqlite3` (sha256 bir xil). `db.sqlite3` o‘zgartirilmadi: sha256 ish oxirida ham `5c33c7d2…8fbf`.
- **Repo tozaligi.** `.gitignore` ga `.idea/`, `.agents/`, `graphify-out/`, `backups/`, `config/.env` qo‘shildi. `.idea/` (6 fayl) va frontend `arms_cache/` indeksdan chiqarildi. Bo‘sh `curriculum/views.py` va `assessments/views.py` o‘chirildi. `orchestrator.py` docstring'i tuzatildi.
- **Bog‘liqliklar (D18).** `requirements.txt` (18 ta qotirilgan paket, jumladan psycopg 3.3.6, django-environ 0.14.0, django-tree-queries 0.24.0) va `requirements-dev.txt` (pytest, pytest-django, Faker, hypothesis, coverage, locust) yozildi. `Pipfile` va `Pipfile.lock` o‘chirildi. Scratchpad'dagi toza venv'da `pip install -r requirements.txt -r requirements-dev.txt` → `pip check`: “No broken requirements”.
- **Sozlamalar.**
  - Barcha qiymatlar env'dan o‘qiladi (`config/settings.py`). Namuna — `config/.env.example`, lokal fayl — `config/.env` (gitignored, `chmod 600`). Lokal faylda yangi `SECRET_KEY` va Postgres paroli generatsiya qilindi, ular chop etilmadi.
  - `DEBUG` standart holatda `False`. `DEBUG=False` bo‘lganda `SECRET_KEY` majburiy. `ALLOWED_HOSTS`, `FRONTEND_ORIGINS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` env'dan olinadi. `CORS_ALLOW_ALL_ORIGINS` olib tashlandi.
  - `X_FRAME_OPTIONS="DENY"`. `DEBUG=False` da secure cookie, SSL redirect va HSTS (env orqali) yoqiladi.
  - `token_blacklist` yoqildi, migratsiyalari qo‘llandi.
  - Redis ixtiyoriy: `REDIS_URL` bo‘sh bo‘lsa LocMem ishlatiladi. `DJANGO_REDIS_IGNORE_EXCEPTIONS=True`.
  - `THESIS_MODEL` (D6) — `config/settings.py:266-285`.
- **PostgreSQL (D1).**
  - `docker-compose.yml`: `postgres:16` → `127.0.0.1:5433`, `redis:7` → `127.0.0.1:6380`. Ikkala servis “healthy”.
  - `scripts/sqlite_to_postgres.sh` ishga tushirildi. 14 ta modelning qatorlar soni SQLite va PostgreSQL'da bir xil, `db.sqlite3` o‘zgarmadi. Qayta ishga tushirilganda skript bo‘sh bo‘lmagan bazaga yuklashni rad etadi (`exit 3`).

    | Model | SQLite | PostgreSQL |
    |---|---|---|
    | accounts.customuser | 57 | 57 |
    | admin.logentry | 15 | 15 |
    | assessments.assessmentattempt | 36 | 36 |
    | assessments.choice | 149 | 149 |
    | assessments.question | 38 | 38 |
    | assessments.userability | 6 | 6 |
    | assessments.userknowledgehistory | 36 | 36 |
    | assessments.userknowledgestate | 6 | 6 |
    | auth.group | 3 | 3 |
    | curriculum.topic | 16 | 16 |
    | curriculum.topicprerequisite | 2 | 2 |
    | curriculum.topicresource | 20 | 20 |
    | token_blacklist.* | 0 | 0 |

- **Ruxsatlar (D15).**
  - `accounts/permissions.py`: `is_instructor`, `get_role`, `IsInstructor`.
  - O‘qituvchi topics/resources/questions/import/template endpoint'lari → `IsInstructor`. Talaba ularga 403 oladi.
  - `PrerequisiteGraphView` → `IsAuthenticated`.
  - Talaba uchun yangi endpoint'lar: `GET /api/curriculum/topics/<id>/` va `GET /api/curriculum/topics/<id>/resources/`.
  - `role` profil maydoni `get_role` bilan hisoblanadi.
- **Ma’lumotlarni himoyalash.**
  - `seed_data` endi `--yes-delete-all` talab qiladi va demo bo‘lmagan akkaunt bo‘lsa ishlamaydi.
  - `CustomUser.is_simulated` qo‘shildi (migratsiya `accounts/0004`). `simulate_bkt_data` simulyatsiya akkauntlarini parolsiz yaratadi va alohida `sim-` daraxtidan foydalanadi. `--clear` faqat `is_simulated=True` akkauntlarni o‘chiradi.
  - Demo parollar kod va README'dan olib tashlandi: parol `DEMO_PASSWORD` dan olinadi yoki generatsiya qilinib, bir marta chop etiladi.
- **Frontend (minimal).** `Course.tsx` talaba endpoint'lariga o‘tdi. Shablonni yuklab olish endi auth header bilan ishlaydi (qarang: Q0-7).
- **CI va hujjat.**
  - Backend `.github/workflows/ci.yml`: Postgres va Redis servislari, `check`, `makemigrations --check`, `pytest` + coverage.
  - Frontend `.github/workflows/ci.yml`: lint, tsc, vitest, build.
  - `readme.Md` → `README.md` ga qayta yozildi (parolsiz).

### Tekshiruv natijalari

| Tekshiruv | Natija |
|---|---|
| `pytest` (PostgreSQL 16, loyiha venv'i) | **66 passed** (avvalgi 49 + 17 yangi) |
| `pytest` toza venv'da, CI'ga o‘xshash muhit (`DJANGO_ENV_FILE=""`, `DEBUG=False`) | **66 passed**, `check` toza, `makemigrations --check` → “No changes detected” |
| `manage.py check` | 0 issues |
| `manage.py makemigrations --check --dry-run` | No changes detected |
| `manage.py check --deploy` (`DEBUG=False`, HSTS sozlanmagan) | 13 ogohlantirish: `security.W004` (HSTS — env orqali yoqiladi; `SECURE_HSTS_SECONDS=31536000` bilan yo‘qoladi) + 12 ta drf-spectacular sxema ogohlantirishi (`W001` 1 ta, `W002` 11 ta: APIView'larda serializer yo‘q). Boshqa Django xavfsizlik ogohlantirishlari yo‘q |
| Frontend `eslint .` | 71 error, 12 warning — o‘zgarmadi, yangi xato qo‘shilmadi (7-bosqich) |
| Frontend `tsc --noEmit` | 16 xato (avval 18; `Course.tsx` dagi `duration_minutes` xatolari yo‘qoldi) |
| Frontend `vitest` / `build` | 1 passed / build o‘tdi |
| Maxfiy qiymatlar grep'i (kuzatiladigan va yangi fayllar, ikkala repo) | Topilmadi: `django-insecure`, `ghp_`, `password123`, demo parollar, JWT/API kalit naqshlari, lokal `SECRET_KEY` va Postgres paroli yo‘q. Faqat CI'dagi vaqtinchalik konteyner qiymatlari (`ci-only-*`) bor, ular hech qayerda ishlatilmaydi |

Yangi testlar:

- `accounts/tests/test_permissions.py` — rollar qoidasi, Instructor guruhidagi (staff emas) foydalanuvchi, talaba uchun 403, talaba endpoint'lari, anonim 401.
- `accounts/tests/test_security_settings.py` — `SECRET_KEY` majburiyligi (subprocess), xavfsizlik bayroqlari, D6 konstantalari, Redis uzilganda 201/200/204, refresh token blacklist'i, media `frame-ancestors`.
- `curriculum/tests/test_seed_safety.py` — `seed_data` himoyasi, `simulate --clear`, `DEMO_PASSWORD` va bir martalik parol.

### Foydalanuvchi bajarishi kerak bo‘lgan ishlar

- Ildizdagi `.env` (gitignored) ichidagi tokenni GitHub'da bekor qilish. Fayl ochilmadi va o‘qilmadi.
- Eski `SECRET_KEY` git tarixida qoldi (tarix qayta yozilmaydi). U buzilgan hisoblanadi, lokal `config/.env` da yangisi ishlatiladi.

---

## 1-bosqich hisoboti

### Nima qilindi

- **Spetsifikatsiya.** `NEUROLEARN_UI_ADDENDUM.md` commit qilindi (`8bc4cea`). Uning 4-bo‘limidagi backend ishlari bosqichlar bo‘yicha matritsaga qo‘shildi (pastdagi “UI qo‘shimchasi” bo‘limi). 1-bosqichga tegishli qismi (`review_repeat`) bajarildi.
- **Sun’iy yozuvlar to‘xtatildi (P0-2, D8).** `_maybe_skip_easy_questions` va `_cascade_mastery_to_descendants` o‘chirildi. Endi `AssessmentAttempt` qatorini faqat `assessments/services/ledger.py:record_attempt` yaratadi. Buni ikki test tekshiradi:
  - `test_only_the_ledger_creates_attempts` — kod bazasini skan qiladi. Eski kodda u 5 ta yozish yo‘lini topadi;
  - audit probe'lari: 3 ta real javob → 3 ta qator; bo‘limni o‘zlashtirish avlodlarga holat yozmaydi.
- **Javoblar logi (P1-1, TM7, D10).** `AssessmentAttempt` ga qo‘shilgan maydonlar: `topic`, `course` (javob paytidagi snapshot), `attempt_no`, `source`, `session`, `p_before`, `p_hat`, `p_after`, `guess_used`, `slip_used`, `theta_before`/`after`, `b_before`/`after`, `readiness_score`, `was_ready`, `engine_version`, `kb_version`.
  - DB cheklovlari: `UNIQUE(user, topic, attempt_no)`, `attempt_no ≥ 1`, `source` ruxsat etilgan qiymatlardan biri, barcha ehtimolliklar [0, 1] oralig‘ida.
  - Qatorlar o‘zgarmas: `save()` (mavjud qator uchun), `QuerySet.update/bulk_update/bulk_create` → `ImmutableLedgerError`. Admin faqat o‘qish rejimida.
  - `attempt_no` har bir (talaba, mavzu) uchun advisory lock ostida beriladi. 10 ta parallel yozuvda raqamlar 1..10 bo‘ldi. Lock o‘chirilganda shu test 9 ta `IntegrityError` bilan yiqiladi (mutatsion tekshiruv).
  - Javob paytidagi model qiymatlari yoziladi. Hozircha bular eski `hybrid_bkt_irt/0` dvigatelining qiymatlari (Q1-9); II bob formulalari 3-bosqichda keladi.
- **Migratsiyalar.** `curriculum/0009` (`is_archived`), `assessments/0006` (nullable maydonlar, `TestSessionResult`, `history.attempt`), `0007` (legacy to‘ldirish), `0008` (NOT NULL va cheklovlar). Uchalasi alohida tranzaksiyada (PostgreSQL “pending trigger events”).
  - Mavjud qatorlarga `source=legacy` beriladi, `topic = question.topic`, `course` = daraxt ildizi. `attempt_no` `(answered_at, id)` bo‘yicha hisoblanadi. Hech qaysi qator o‘chirilmaydi va vaqti o‘zgartirilmaydi.
  - Dev PostgreSQL: migratsiyadan oldin `backups/pg-20261003-1027.dump` olindi (gitignored, `chmod 600`). Barcha jadvallarda qatorlar soni o‘zgarmadi (javoblar 36 → 36). 36 ta qatorning hammasi `legacy`, 6 ta (talaba, mavzu) juftligida raqamlar bo‘shliqsiz. `db.sqlite3` sha256 hali ham `5c33c7d2…`.
- **Prior va tarix (audit 4.4).** BKT prior endi `UserKnowledgeHistory` dan emas, joriy holat qatoridan olinadi (`prior_from_state`). Shu bilan `_retrieve_prior` dagi `algorithm_used` xatosi yo‘qoldi. Har bir tarix qatori `attempt` ga bog‘langan (OneToOne). Eski tarix qatorlari bog‘lanmagan (Q1-10).
- **D25 — `review_repeat`.** Talaba aynan bir xil savolga `THESIS_REVIEW_REPEAT_HOURS` (24 soat) ichida qayta javob bersa, javob `source=review_repeat` bilan yoziladi. Bunday javob holatni, θ ni va tarixni o‘zgartirmaydi. Savol tanlashda bunday savollar oxirgi navbatga qo‘yiladi. `submit_answer` javobida `source` va `attempt_no` maydonlari qaytadi.
- **Test sessiyasi (D7, qisman P0-1).** Vaznli baho endi `TestSessionResult` ga yoziladi. Har bir javob ledger'ga `source=test_session` (yoki D25 bo‘yicha `review_repeat`) va `session` FK bilan tushadi. Baho endi `mastery_percentage` ga yozilmaydi (`test_test_session.py:140` shunga moslab tuzatildi). Yozuvlar atomar, holat qatori qulflanadi. Javobga `session_id` qo‘shildi. Javoblarni Algoritm 2.4 orqali o‘tkazish 5-bosqichda.
- **O‘chirish siyosati (D11).**
  - `AssessmentAttempt.question`, `selected_choice`, `topic`, `course` — `PROTECT`; `session` — `RESTRICT`.
  - Javoblari bor mavzu (yoki uning shoxi) DELETE qilinsa, butun shox arxivlanadi (200, `archived: true`). Javoblari yo‘q mavzu oddiy o‘chiriladi (204).
  - Javoblari bor savol DELETE qilinsa, `is_active=False` bo‘ladi.
  - Savolni tahrirlashda variantlar `id` bo‘yicha joyida yangilanadi. Oldin variantlar o‘chirilib qayta yaratilardi va bu javoblarni CASCADE bilan o‘chirardi. Talaba tanlagan variantni olib tashlash 400 qaytaradi.
  - Arxivlangan mavzular daraxt, graf, dashboard, testlar ro‘yxati, talaba sahifasi va instruktor ro‘yxatlarida ko‘rinmaydi (`?include_archived=true` bundan mustasno). Ularga javob berib ham bo‘lmaydi.
- **Seed'lar.**
  - `seed_data` → `source=seed`. Vaqt yozuv yaratilganda beriladi, keyin hech bir qatorning vaqti qayta yozilmaydi.
  - `seed_thesis_demo` → `source=seed` va `answered_at` `process_submission` orqali beriladi. Oldin “oxirgi qatorni” `update()` bilan qayta vaqtlardi. Demo akkauntlarda seed yozmagan javoblar bo‘lsa, `--reset-demo-answers` bayrog‘isiz to‘xtaydi (Q1-11).
  - `simulate_bkt_data` → `source=simulated`.
- **Frontend (1-bosqichga moslash, Q1-18).**
  - `deleteTopic`/`deleteQuestion` endi `{archived}` qaytaradi. Instruktor interfeysi “o‘chirildi” o‘rniga “arxivlandi / faolsizlantirildi” deb xabar beradi. Tasdiqlash oynasidagi “qaytarib bo‘lmaydi” matni ham tuzatildi.
  - Backend rad etgan tahrirlarda (masalan, talaba tanlagan variantni olib tashlash) backend xabari ko‘rsatiladi: `src/lib/apiError.ts`.
  - Tiplarga qo‘shildi: `submit_answer` → `source`, `attempt_no`; test natijasi → `session_id`; `is_archived`, `is_active`. `useAdaptiveQuiz` `isReviewRepeat` ni qaytaradi (7-bosqichda UI'da ishlatiladi).
  - Mavzu sahifasi 404 bo‘lsa (arxivlangan mavzu), “mavzu endi mavjud emas” deb ko‘rsatadi.
  - D24: tutor kodi qaytarildi va `VITE_ENABLE_TUTOR` (standart holatda o‘chiq) ortiga o‘tkazildi. Marshrut ham, menyu bandi ham faqat flag yoqilganda bor; sahifa lazy chunk sifatida yuklanadi (Q1-15).

### Tekshiruv natijalari

| Tekshiruv | Natija |
|---|---|
| `pytest` (PostgreSQL 16, loyiha venv'i) | **98 passed** (avval 66, +32 yangi) |
| `pytest` toza venv'da, CI env bilan (`DJANGO_ENV_FILE=""`, `DEBUG=False`, `SECURE_SSL_REDIRECT=False`, Redis) | **98 passed**; `pip check` toza |
| Birinchi commit (`888a96f`) alohida worktree'da | 92 passed (arxiv testlari ikkinchi commit'da) |
| `manage.py check` | 0 issues |
| `makemigrations --check --dry-run` | No changes detected |
| `grep`: `AssessmentAttempt` yaratadigan joylar (testlar va migratsiyalardan tashqari) | Faqat `assessments/services/ledger.py:149` |
| `grep`: `_maybe_skip_easy_questions`, `_cascade_mastery_to_descendants`, `_retrieve_prior`, `update(answered_at` / `update(created_at` | Prototip kodida yo‘q (faqat ularning yo‘qligini tekshiradigan testlarda bor) |
| `submit_answer` SQL soni (birinchi / keyingi / `review_repeat`) | 22 / 19 → **25 / 20 / 15**. Qo‘shilganlari: advisory lock, D25 tekshiruvi, `max(attempt_no)`, ildiz so‘rovi. Easy-skip so‘rovlari yo‘qoldi. ≤ 12 byudjet — B10 |
| Frontend `eslint .` | 71 error, 12 warning — o‘zgarmadi. Yangi fayllar lint'dan toza o‘tdi |
| Frontend `tsc --noEmit -p tsconfig.app.json` | 16 xato — o‘zgarmadi. Tahrirlangan fayllardagi xatolar oldindan bor edi (stash bilan solishtirildi) |
| Frontend `vitest` | **10 passed** (avval 1; +9: `apiError`, delete natijalari, tutor flag) |
| Frontend `vite build` | O‘tdi. Asosiy bundle 2.36 → 2.22 MB, tutor alohida `Tutor-*.js` (140 kB) chunk'ida |

Yangi testlar:

- `assessments/tests/test_ledger.py` (21 ta): faqat ledger yozishi (statik skan), audit probe'lari 4.7/4.9, `attempt_no`, topic snapshot, hybrid trace va prior zanjiri, legacy holatlarda P(L0), API maydonlari, D25 (oyna ichida/tashqarisida, seed'lar), savol tanlash, o‘zgarmaslik himoyasi, noto‘g‘ri so‘rovlar, DB cheklovlari, ikkita parallel test (orchestrator va ledger).
- `assessments/tests/test_ledger_migration.py` — 0005 holatiga qaytib, eski qatorlar yaratiladi va oldinga migratsiya qilinadi.
- `curriculum/tests/test_archive.py` (6 ta) — D11 bo‘yicha arxivlash, faolsizlantirish, variantlarni joyida tahrirlash, ORM'ning PROTECT bilan rad etishi.
- `curriculum/tests/test_seed_ledger.py` (4 ta) — seed va simulyator manbalari, boshqa qatorlar vaqtining saqlanishi, `--reset-demo-answers`.
- O‘zgartirilgan testlar: `test_bayesian.py` (prior holatdan; parallellik testi endi xatoni yutmaydi va har xil savollar bilan ishlaydi, Q1-13), `test_test_session.py:140` (D7).

### Foydalanuvchi bajarishi kerak bo‘lgan ishlar

- `seed_thesis_demo` endi dev bazada `--reset-demo-answers` bayrog‘isiz ishlamasligi mumkin: demo akkauntlarda `legacy` javoblar bo‘lishi mumkin. Ularni o‘chirish yoki saqlash — sizning qaroringiz.

---

## 2-bosqich hisoboti

### Nima qilindi

- **Sof algoritmlar (7-qoida).** `neuro_model/graph.py` (Django'siz):
  - preorder `pos` (D4), Leaves, G_L (vazni — max), Y2;
  - Algoritm 2.1 (BFS + zanjir);
  - Algoritm 2.2 (`(pos, id)` kalitli heap, `lev`, `CycleError`);
  - Desc\* bitset, ortiqcha qirralar, κ.
- **Daraxt (D3, BB1, BB2).**
  - `Topic` django-tree-queries'ga ko‘chirildi: MPTT ustunlari olib tashlandi, `mptt` INSTALLED_APPS'dan chiqarildi. Paket eski migratsiyalar va 9-bosqich benchmarki uchun qoladi.
  - `kind` qo‘shildi: `course` / `section` / `topic`. Qo‘shimcha DB cheklovi: kurs ⇔ ildiz.
  - Aka-uka tugunlar `(position, id)` bo‘yicha tartiblanadi.
- **Migratsiyalar `0010`–`0012`.**
  - `kind` qiymatlari: ildiz → course, bolasi bor tugun → section, barg → topic (Q2-2).
  - Data qadami kurs yoki bo‘limda savol topsa (Y4), shuningdek mavjud Y2/Y3 buzilishini topsa, taxmin qilmay to‘xtaydi.
  - `TopicPrerequisite` ga ω ∈ (0, 1], self-loop va unique cheklovlari qo‘shildi. `KnowledgeBaseVersion` singleton yaratildi.
- **Yagona KB servisi (`curriculum/services/kb.py`).**
  - Amallar: `create_node`, `update_node`, `move_node`, `archive_node`, `delete_node`, `add_prerequisite`, `update_weight`, `remove_prerequisite`.
  - Har bir amal advisory lock oladi, KB'ni keshdan emas, bazadan qayta o‘qiydi va Y1–Y3 hamda tur qoidalarini tekshiradi. Algoritm 2.1 zanjir bilan ishlaydi; daraxt o‘zgarganda Algoritm 2.2 va Y2 qayta tekshiriladi.
  - Muvaffaqiyatli amal versiyani aniq bittaga oshiradi. Rad etilgan amal hamma narsani, versiyani ham, orqaga qaytaradi.
- **Chetlab o‘tishga qarshi guard'lar.** `Topic` (parent/kind/position/is_archived), `TopicPrerequisite` va `KnowledgeBaseVersion` uchun `save`, `delete`, `update`, `bulk_create`, `bulk_update` servisdan tashqarida `KBWriteError` beradi. Nostruktur tahrirlar (nom, `is_unlocked`) ruxsat etiladi. Admin servis orqali yozadi.
- **Kesh (GR1).** `KBSnapshot` tarkibi: pos, depth, Leaves, G_L, tartib, lev, Pre/Succ, Desc\*, ortiqcha qirralar, κ. U KB versiyasi kaliti bilan keshlanadi va eskirgan yozuv o‘qilmaydi. Versiya ma’lumotdan oldin ham, keyin ham o‘qiladi; ular teng bo‘lmasa, natija keshga yozilmaydi.
- **Olib tashlanganlar.** Eski `topological_order`, `get_all_prerequisites`, `_invalidate_tree_cache`, `TopicPrerequisite.clean` (DFS) va MPTT benchmark buyrug‘i.
- **API.**
  - Instruktor prerekvizitlari CRUD: `/api/curriculum/instructor/prerequisites/`; G_L uchun `?expand=leaf`.
  - Ogohlantirishlar: `/api/curriculum/instructor/kb/warnings/`.
  - Rad javobi — 400 `{reason, detail, chain, chain_names, edge}`.
  - Graf API (addendum A4-2…A4-5): `kind`, `pos`, `depth`, `lev`; G_L qirralari (`inherited`, `via`); E_P qirralari ω bilan; instruktorlarga `warnings`.
  - O‘quv yo‘li daraxti `pos` tartibida va `kind`/`pos`/`lev` bilan qaytadi.
- **Y4 va import.**
  - Savol faqat faol `topic` ga biriktiriladi. Bu serializer, import, admin (`Question.clean`) va model guard'ida tekshiriladi; guard tur o‘zgarishi bilan poygaga qarshi topic qatorini qulflaydi.
  - Import endi alohida servis: 2–4 variant va bitta to‘g‘ri javob tekshiriladi, xatolar savol bo‘yicha qaytadi va hech narsa qisman yozilmaydi.
  - ≤4 variant qoidasi `bulk_create` yo‘lida ham ishlaydi.
- **Ledger.** Endi `kb_version` yoziladi; `course` snapshot'dan olinadi.
- **Seed'lar va simulyator** daraxtni servis orqali quradi. `Demo Topic` CS kursining mavzusi bo‘ldi, chunki u ildiz bo‘lib, savollari bor edi.
- **Dev baza.**
  - 31 ta javobsiz savol va ularning 124 ta varianti foydalanuvchi qarori bilan o‘chirildi (Q2-1). Oldin `backups/pg-20261003-1106-before-b2.dump` olindi.
  - Migratsiyadan keyin barcha jadvallarda qatorlar soni o‘zgarmadi. Natija: 3 kurs, 4 bo‘lim, 9 mavzu; G_L da 5 qirra, κ = 0, ortiqcha qirra yo‘q.
  - Docker volume yo‘qolgani tufayli baza zaxiradan tiklandi (Q2-8).
- **Frontend (`c259646`).** Tur tanlovi (Topic/Section), savollar faqat topic'larga, topic'lar ota tugun sifatida taklif qilinmaydi, KB va import xatolari ko‘rsatiladi, graf tiplari kengaytirildi.

### Tekshiruv natijalari

| Tekshiruv | Natija |
|---|---|
| `pytest` (PostgreSQL 16) | **440 passed** (140 ta Django testi + 300 ta tasodifiy `neuro_model` holati; 3 subtest) |
| `pytest` toza venv'da, CI env bilan | **440 passed**; `check` toza; `makemigrations --check` → No changes |
| 4-bo‘lim etalon qiymatlari (API va sof funksiyalar) | Hammasi mos: E_L = 10 (meros: t4→t6, t4→t7, t4→t8), tartib t1…t8, lev 0,0,1,1,1,2,3,3, FIFO t1,t2,t3,t5,t4,…, \|Desc\*\| 5,4,3,3,3,2,0,0, ortiqcha t4→t7, t4→t8, κ = 0; (t8,t3) → `cycle` [t3,t6,t8]; (B3,t6) → `nested`; t4 → B3 → `nested`; audit probe'lari 1–2 |
| Poyga testi (V-B5) | 10/10 raundda aynan bitta relatsiya o‘tadi. Advisory lock o‘chirilganda 10/10 yiqiladi (mutatsion tekshiruv) |
| Tasodifiy taqqoslash (seed `20261003`, 300 holat) | Algoritm 2.1 qarori va zanjiri, Algoritm 2.2 tartibi (leksikografik eng kichik), lev, Desc\*, ortiqcha qirralar — brute-force bilan mos |
| Frontend | lint 71 / 12 va tsc 16 — o‘zgarmadi; vitest 10 passed; build o‘tdi |

### Foydalanuvchi bajarishi kerak bo‘lgan ishlar

- Docker snap orqali o‘rnatilgan. Qayta yuklangandan keyin `neurolearn_pgdata` volume'i yo‘qolgan edi (Q2-8). Dev ma’lumotlarini muntazam `pg_dump` bilan saqlang yoki Docker'ni snap'siz o‘rnatishni ko‘rib chiqing.

---

## 2.1-bosqich hisoboti (B2.1 — tekshiruvdagi FAIL'larni tuzatish)

Manba: `VERIFICATION_REPORT.md` (commit `7825f2a`) va `NEUROLEARN_B2FIX_B3.md` 1-bo‘limi (D30–D32, D37, D38).

### Nima qilindi

- **D30 — teskari FK manageri guard ostiga olindi.**
  - `Topic.Meta` va `TopicPrerequisite.Meta` ga `base_manager_name = "objects"` qo‘shildi. Shart bajariladi: `objects` o‘qishda hech narsani filtrlamaydi, guard'lar faqat yozish metodlarida. Shuning uchun D30 dagi `all_objects` varianti kerak bo‘lmadi.
  - Bu `Topic._base_manager.filter(...).update(parent_id=...)`, `Topic._base_manager.bulk_create([...])` va `TopicPrerequisite._base_manager.all().delete()` yo‘llarini yopdi.
  - Qo‘shimcha: `parent` maydoni `GuardedTreeNodeForeignKey` ga o‘zgartirildi va teskari manager (`node.children`) ning `add`, `set`, `remove`, `clear` metodlari guard ostiga olindi (`curriculum/models.py`). **Sabab:** `base_manager_name` yolg‘iz `children.set([...])` ni ham rad etadi, lekin Django `set()` ni `transaction.atomic(savepoint=False)` ichida bajaradi — guard ichkarida ishga tushganda butun tranzaksiya `needs_rollback` holatiga o‘tadi va rad etilgandan keyin hech narsa o‘qib bo‘lmaydi (V-B4 testi aynan shundan yiqilgan edi). Manager chegarasida rad etish `atomic` ochilishidan oldin sodir bo‘ladi, shuning uchun rad etilgan yozuv atrofdagi tranzaksiyani buzmaydi. O‘qish yo‘llari tegilmagan.
  - Migratsiya talab qilinmadi: `TreeNodeForeignKey.deconstruct()` `django.db.models.ForeignKey` yo‘lini qaytaradi, shuning uchun sinfni almashtirish sxemaga ta’sir qilmaydi (`makemigrations --check` toza).
- **D31 — KB versiyasi yaxlitligi.**
  - `KnowledgeBaseVersionQuerySet` endi `delete` va `bulk_create` ni ham bloklaydi (`update` avvaldan bor edi).
  - `KnowledgeBaseVersion.current()` qator yo‘q bo‘lsa `KBError(reason="version_missing")` beradi. Jim `or 1` fallback olib tashlandi.
  - `_bump_version()` qatorni qayta yaratmaydi: `get_or_create` olib tashlandi, `update(...)` natijasi `rowcount != 1` bo‘lsa `version_missing` beradi. Qator faqat `0011_kb_data` migratsiyasi orqali yaratiladi.
  - `instance_token` (UUID) maydoni qo‘shildi (`0013_kb_version_instance_token`). Kesh kaliti `kb:snapshot:<instance_token>:v<version>` bo‘ldi, shuning uchun hisoblagich orqaga qaytsa ham eski yozuv o‘qilmaydi.
  - `updated_at` har bir versiya oshishida `timezone.now()` bilan aniq yoziladi (`auto_now` `QuerySet.update()` da ishlamaydi — V-B6a).
- **D32 — servis chegarasida xatolar o‘raldi.**
  - `kb.update_weight(<yo‘q id>, …)` → `KBError(reason="not_found")`.
  - `kb.create_node(..., slug=<takrorlanuvchi>)` → `KBError(reason="duplicate_slug")`. Tekshiruv KB qulfi ostida bajariladi; `IntegrityError` ham ushlanadi (advisory lock'siz backend'lar uchun). `update_node(slug=…)` ham shu yo‘ldan o‘tadi.
  - `delete_node` qaytaradigan `size` endi faqat shu amal olib tashlagan faol tugunlarni sanaydi; oldindan arxivlangan avlodlar sanalmaydi.
  - `KBError` sinfi `curriculum/kb_guard.py` ga ko‘chirildi va `curriculum/services/kb.py` dan qayta eksport qilinadi (`kb.KBError` nomi o‘zgarmadi). Sabab: `curriculum/models.py` ham uni beradi (`current()`), lekin modellar servisni import qila olmaydi.
  - **Istisno:** noma’lum maydon nomi bilan chaqirilganda servis hamon `TypeError` beradi (`create_node`/`update_node`). Bu foydalanuvchi kiritmasi emas, server kodidagi xato (serializer maydonlarni validatsiya qiladi), shuning uchun 400 ga aylantirilmadi.
- **D37 — o‘chirilgan daraxt testlari qayta yozildi.** `curriculum/tests/test_tree.py` 26 ta testdan 45 ta testga to‘ldirildi. Qo‘shilganlari: `Leaves(n)` har bir tur uchun (kurs, bo‘lim, mavzu); arxivlangan tugunlarning `order`/`pos`/`depth`/`Leaves` dan chiqib ketishi va `pos` dagi bo‘shliqning yopilishi; ko‘chirishdan keyin ajdod zanjiri, ikki ota-onaning avlodlar to‘plami, `depth` va `Leaves`; chuqurligi 7 bo‘lgan zanjirda shu o‘qishlarning hammasi va pastdan ko‘chirish.
- **D38 — dev muhiti tozalandi.** Buyruq:
  ```bash
  redis-cli --scan --pattern '*kb:snapshot*' | xargs -r redis-cli del
  ```
  Tekshirilganda (0, 1, 2-bazalar) dev Redis'da birorta kalit qolmagan edi (`dbsize` = 0) — hisobotdagi `:1:kb:snapshot:v1` kaliti TTL bo‘yicha o‘chib ketgan. D31 dagi `instance_token` bu muammoni kelajak uchun yopadi.

### Qo‘shilgan testlar (prototip tomonida)

- `curriculum/tests/test_kb.py`: chetlab o‘tish ro‘yxatiga `children.add/set/remove/clear`, `Topic._base_manager.update/bulk_create`, `TopicPrerequisite._base_manager.all().delete()` va `KnowledgeBaseVersion...delete()` qo‘shildi; yangi testlar — `version_missing` invarianti, `updated_at` siljishi, kesh kalitining token bilan chegaralanishi, `not_found`/`duplicate_slug`, `delete_node` sanog‘i.
- `conftest.py`: `transaction=True` testlari har bir testdan keyin barcha jadvallarni truncate qiladi va migratsiya yaratgan versiya qatorini ham olib tashlaydi. Endi prod kodi qatorni qayta yaratmagani uchun (D31) invariantni test harness'i tiklaydi. Bu `verification/` dan tashqarida, root `conftest.py` da — V-B5 ham shu bilan ishlaydi.
- `pytest.ini`: standart `pytest` ishga tushganda `verification/` o‘tkazib yuboriladi (`--ignore=verification`). U o‘zining `--ds=verification.settings` sozlamasi bilan ishlaydi, shuning uchun standart `--ds` ostida yig‘ilganda `VERIFICATION_SEED` yo‘qligidan collection error bergan edi.

### Natijalar

| Tekshiruv | Natija |
|---|---|
| `venv/bin/pytest` (prototip) | **464 passed**, 13 subtests (B2.1 dan oldin 458) |
| `venv/bin/python manage.py check` | toza (0 silenced) |
| `venv/bin/python manage.py makemigrations --check --dry-run` | No changes detected |
| `venv/bin/pytest --ds=verification.settings verification/tests -q` | **691 passed, 3 failed** (B2.1 dan oldin: 689 passed, 5 failed) |

Tekshiruv suite'iga tegilmadi (`verification/` o‘zgarmagan).

**Tuzatilgan FAIL'lar (5 tadan 3 tasi + 1 ta qo‘shimcha):**

| Test | Holat |
|---|---|
| `test_v_b4_reverse_manager_add_cannot_move_a_node` | FAIL → **PASS** |
| `test_v_b4_reverse_manager_set_cannot_break_y2_and_the_kind_rules` | FAIL → **PASS** |
| `test_v_b4_kb_version_row_cannot_be_removed_or_replaced` | FAIL → **PASS** |
| `test_v_b6_updated_at_tracks_the_last_kb_change` (V-B6a) | FAIL → **PASS** |
| `test_v_b4_integrity_after_every_attempt` | PASS (saqlandi) |

### Qolgan 3 ta FAIL — nega tuzatilmadi

Uchalasi ham tuzatishdan **oldingi** xatti-harakatni tasdiqlaydigan testlar: D30–D32 aynan shu xatti-harakatni o‘zgartirgani uchun ular endi yiqiladi. Tekshiruv kodi o‘zgartirilmadi (topshiriq talabi), shuning uchun asos shu yerda yozilgan.

1. **`test_b4_bypass.py::test_v_b4_removing_the_version_row_makes_get_snapshot_serve_a_stale_kb`**
   Test teshikni *namoyish qiladi*: `KnowledgeBaseVersion.objects.filter(pk=1).delete()` ni `pytest.raises` siz bajaradi va keyin eskirgan snapshot xizmat qilishini kutadi. D31 bu `delete` ni guard ostiga oldi, shuning uchun test birinchi qatorda `KBWriteError: Deleting the KB version row must go through curriculum.services.kb.` oladi. Teshik yopilgandan keyin bu test yozilgan holida o‘ta olmaydi — uning juftligi, `test_v_b4_kb_version_row_cannot_be_removed_or_replaced` (aynan shu `delete` rad etilishini kutadi), endi PASS. Ya’ni talab bajarilgan, faqat namoyish testi eskirgan.

2. **`test_b6_version.py::test_v_b6_the_cache_follows_the_version`**
   Oxirgi qatori kesh kalitining formatini qattiq yozadi: `assert cache.get(f"kb:snapshot:v{version}") is not None` (izoh: “eski yozuv hamon murojaat qilinadi, ya’ni hech narsa invalidatsiya qilinmadi”). D31 kalitni `kb:snapshot:<instance_token>:v<version>` ga o‘zgartirdi, shuning uchun bu aniq satr `None` qaytaradi. Testning *maqsadi* — “yangi versiya yangi kalit yozadi, eski yozuv invalidatsiya qilinmaydi” — hamon bajariladi; faqat kalit satri boshqa. Buni `curriculum/tests/test_kb.py::test_cache_entries_are_scoped_to_the_version_row` tasdiqlaydi: eski kalit (`_cache_key(first.version)`) o‘zgarishdan keyin ham `is not None`, yangi kalit ham yozilgan, va kalitsiz `kb:snapshot:v<version>` yozilmaydi. Testning qolgan barcha assert'lari (versiya +1, 7 qirra, ortiqcha qirralar yo‘q) o‘tadi.
   *Agar V-B6 ni butunlay yashil ko‘rish muhimroq bo‘lsa:* token kesh kalitida emas, keshlangan qiymat ichida saqlanib, o‘qishda tekshirilsa, D31 ning maqsadi bajariladi va kalit formati o‘zgarmaydi. Bu bir joyda o‘zgarish (`curriculum/services/graph.py`), lekin D31 kalit formatini aniq yozgani uchun hozir spetsifikatsiya bo‘yicha bajarildi.

3. **`test_b6_version.py::test_v_b6_update_weight_on_a_missing_relation_is_not_a_kb_error`**
   Test nomi ham, mazmuni ham tuzatishdan oldingi kuzatishni qayd etadi: `with pytest.raises(TopicPrerequisite.DoesNotExist): kb.update_weight(10**9, 0.5)`. D32 bu yo‘lni `KBError(reason="not_found")` ga aylantirishni talab qiladi, shuning uchun test yiqiladi. Hisobotning o‘zi (“Qo‘shimcha kuzatishlar”, 1-band) bu holatni V-C1 uchun tuzatilishi kerak deb belgilagan edi; tuzatilgandan keyin kuzatishni qayd etuvchi test eskiradi.

**Xulosa:** V-B4 va V-B6 bo‘yicha talablar bajarildi (guard'lar yopildi, versiya invarianti va `updated_at` tuzatildi), lekin shu uchta test o‘zgartirilmagan holida PASS bo‘la olmaydi, chunki ular eski xatti-harakatning dalili edi. Boshqa B tekshiruvlari (V-B1, V-B2, V-B3, V-B5) regressiyaga uchramadi: 691 passed.
---

## 3-bosqich hisoboti (talaba modeli)

Qamradi: P0-5, TM1–TM6, ES4–ES6; audit 4.4–4.7 va savol tanlashdagi θ nomuvofiqligi. Oldindan berilgan qarorlar: D33–D36 va `NEUROLEARN_B2FIX_B3.md` ning “Qo‘shimcha aniqlik” bo‘limi.

### Nima qilindi

- **Sof model (7-qoida).** `neuro_model/` ga Django'siz modullar qo‘shildi:
  - `irt.py` — σ, γ_G, γ_S, chegaralangan P(G)/P(S);
  - `bkt.py` — p̂, Bayes posteriori, PT o‘tishi (`posterior` alohida qaytariladi, chunki 2.5-tasdiq aynan unga tegishli);
  - `elo.py` — p = σ(θ−b), K(n) = α/(1+βn), θ va b yangilanishi, θ clamp;
  - `init.py` — P(L0): ω vaznli m̄, (1−λ)P0 + λm̄, c = τ − C_OFFSET;
  - `student.py` — Algoritm 2.4 bitta sof funksiyada (`observe`), ablatsiya bayroqlari bilan;
  - `calibrate.py` — chegaralangan grid search va log-likelihood.
  - Statik skan: `neuro_model/tests/test_purity.py` har bir modulni `ast` bilan tahlil qiladi va `django`/`curriculum`/`assessments`/… importi yo‘qligini tasdiqlaydi (matn izlash emas, shuning uchun izohdagi “django” so‘zi soxta ogohlantirish bermaydi).
- **a_q = 0 aniq klassik BKT beradi.** σ(γ_G) = G0/G_MAX bo‘lgani uchun a_q = 0 da P(G) = G0 va P(S) = S0 **aynan** chiqadi. Shuning uchun klassik BKT alohida dvigatel emas, bayroq bilan hosil bo‘ladi (D34) va buni test taqqoslab tasdiqlaydi.
- **Modellar.**
  - `TopicModelParams` (P0, PT, G0, S0, `source`, `fitted_at`). Qatori yo‘q mavzu `settings.THESIS_MODEL` standartlarini ishlatadi, shuning uchun jadvalda faqat haqiqatan moslangan qiymatlar turadi. `G0 < G_MAX` va `S0 < S_MAX` `clean()` da tekshiriladi (chegaralar env orqali o‘zgarishi mumkin, shuning uchun DB cheklovi emas); parametrdan mustaqil oraliqlar DB cheklovlarida.
  - `UserAbility` endi `(user, course)` va `n_answers` bilan. Mavjud 6 ta `(user, topic)` qatori **ko‘chirilmadi, o‘chirildi** (D33) — migratsiya o‘chirilgan qatorlar sonini chop etadi.
  - `Question.n_answers` qo‘shildi, 0 dan boshlanadi; legacy javoblar bo‘yicha backfill qilinmadi.
  - `AlgorithmChoice` ga `thesis_hybrid` qo‘shildi; eski qiymatlar o‘zgarmas tahliliy ledger'dagi mavjud qatorlar uchun ro‘yxatda qoldirildi.
- **Yagona dvigatel (D34).** `assessments/services/engines/` paketi va `services/base.py` olib tashlandi (`bayesian`, `irt`, `hybrid_bkt_irt`, `streak` va chiziqli modifier'lar bilan birga). O‘rniga `assessments/services/student_model.py` — `neuro_model.student` ning Django tomoni. `STUDENT_MODEL_ENGINE` sozlamasi olib tashlandi; `settings.THESIS_FLAGS` (`use_irt`, `use_prereq_init`) qo‘shildi.
- **P(L) manbai — ledger.** Dvigatel P(L) ni holat qatoridan emas, javoblar logidan o‘qiydi: `engine_version` `thesis_hybrid` bilan boshlanadigan oxirgi qator. Sabab: holat qatorlarida olib tashlangan dvigatellarning va legacy importlarning qiymatlari bor; ledger esa append-only va har qatorda qaysi dvigatel yozganini saqlaydi. Shu tanlov `rebuild_student_states` ni jonli yo‘l bilan bir xil natija berishini ta’minlaydi.
- **Orchestrator.** Algoritm 2.4 ning tartibi dvigatelning o‘zida: P(G)/P(S) **eski** θ va b dan, p̂ bashorat qilingan holida yoziladi, Elo faqat keyin harakatlanadi. Bitta snapshot butun submission uchun olinadi, shuning uchun qobiliyat qatorining kursi, P(L0) ning prerekvizitlari va ledger'ning `kb_version` i bir-biriga qarama-qarshi bo‘lishi mumkin emas. `streak` hisoblagichi endi orchestrator'da yuritiladi (faqat ko‘rsatish uchun).
- **Savol tanlash.** `|b_q − θ_s|` eng kichik, tenglikda `id`. θ_s mavzuni saqlagan **kursdan** olinadi — tanlash va Elo yangilanishi bir xil qatorni o‘qiydi (audit `question_selection.py:66`). Yaqinda javob berilganlar oxirgi navbatda (D25), to‘g‘ri javob berilganlar qayta berilmaydi.
- **Buyruqlar.**
  - `rebuild_student_states` (D35): ledger'ni `(answered_at, id)` bo‘yicha xronologik qayta o‘ynab, P(L), θ va b_q ni tiklaydi. Standart qamrov `adaptive` + `test_session`; `--include-legacy` `seed`/`simulated`/`legacy` ni qo‘shadi; `review_repeat` hech qachon o‘ynatilmaydi. Boshlang‘ich nuqta ledger'dan olinadi (eng erta qatorning `theta_before` va `b_before` qiymatlari), hisoblagichlar 0 dan. P(L0) joriy KB va joriy parametrlar bilan qayta hisoblanadi, prerekvizitlarning P(L) qiymati esa o‘sha nuqtadagi qayta o‘ynalgan qiymat — ya’ni jonli dvigatel ko‘rgan kirishning aynan o‘zi. `--dry-run` va `--user` bor. Ledger'ga yozmaydi.
  - `calibrate_bkt` (D36): standart — `neuro_model/calibrate.py` dagi chegaralangan grid search (`G0 < G_MAX`, `S0 < S_MAX`), tashqi bog‘liqliksiz va deterministik. `--method=pybkt` pyBKT EM'ni ishlatadi; pyBKT faqat `requirements-dev.txt` da, o‘rnatilmagan bo‘lsa buyruq tushunarli xabar bilan grid search'ga qaytadi. Faqat `adaptive` + `test_session` javoblarida o‘qiydi; `--min-answers` (standart 30) dan kam javobli mavzu standart holatda qoldiriladi va sababi chop etiladi. `--dry-run`, `--topic`, `--include-generated` bor.
- **`docs/THESIS_MAPPING.md` yaratildi.** II bobning har bir tushunchasi uchun kod va test manzili, hamda **farqlar** ro‘yxati: F1 θ clamp (D6), F2 diskret `MasteryLevel` (4-bosqichda yopiladi), F3 `review_repeat` siyosati (D25), F4 kesh kalitidagi `instance_token` (D31), F5 grid search.

### 4-bo‘lim etalon qiymatlari

Hammasi 1e-3 aniqlikda o‘tadi — sof funksiyalarda (`neuro_model/tests/test_student.py`) va ledger orqali uchidan-uchiga (`assessments/tests/test_student_model.py`):

| Tekshiruv | Kutilgan | Natija |
|---|---|---|
| BKT ketma-ketligi (P0=0.3, G=0.2, S=0.1, T=0.1) | 0.6927 / 0.9192 / 0.9828 / 0.9965 | mos |
| Qiyin savol, b=1.5 | 0.1272 / 0.0731 / 0.6070 / 0.9246 / 0.2005 | mos |
| Oson savol, b=−0.5 | 0.2534 / 0.0269 / 0.6852 / 0.8669 / 0.1461 | mos |
| a=0 (klassik BKT) | 0.20 / 0.05 / 0.65 / 0.8892 / 0.1771 | mos |
| Elo (θ=0.5, b=1.5, K=0.4) | 0.2689 / 0.7924 / 1.2076 | mos |
| P(L0) prerekvizitlardan | 0.636 va 0.35 | mos |
| 2.5-tasdiq (xossa testi) | P(G)+P(S) < 1 ⇒ P(L\|1) > P(L) > P(L\|0) | o‘tdi (posterior uchun, 28 ta kombinatsiya) |

Qo‘shimcha tasdiqlangan xossalar: `a_q = 0` da P(G) = G0 va P(S) = S0 aynan; chegaralangan P(G)/P(S) hech qachon G_MAX/S_MAX dan oshmaydi, shuning uchun 2.5 har qanday savol uchun bajariladi; PT o‘tishidan keyin noto‘g‘ri javobda ham P(L) o‘sishi mumkin (klassik BKT xatti-harakati, test hujjatlashtiradi); p̂ `theta_before` dan hisoblanadi va `theta_after` bilan hisoblangan qiymatdan farq qiladi.

### Natijalar

| Tekshiruv | Natija |
|---|---|
| `venv/bin/pytest` (prototip) | **566 passed**, 13 subtests (3-bosqichdan oldin 523) |
| `venv/bin/python manage.py check` | toza (0 silenced) |
| `venv/bin/python manage.py makemigrations --check --dry-run` | No changes detected |
| `neuro_model` yolg‘iz | 395 passed (shu jumladan 300 ta tasodifiy graf holati) |
| `venv/bin/pytest --ds=verification.settings verification/tests -q` | **689 passed, 5 failed** |

Tekshiruv suite'iga tegilmadi.

### Tekshiruvdagi FAIL'lar

Uchtasi B2.1 dan qolgan va o‘sha bo‘limda asoslangan (`test_v_b4_removing_the_version_row_...`, `test_v_b6_the_cache_follows_the_version`, `test_v_b6_update_weight_on_a_missing_relation_is_not_a_kb_error`).

Qolgan ikkitasi — **yangi va kutilgan**: `test_na.py::test_na_group_a_student_model_is_not_implemented` va `test_na.py::test_pending_stages[3]`. `verification/tests/test_na.py` ning o‘z izohida yozilgani kabi: “these tests start failing the moment a stage lands, which is the signal that the matching verification group must be written instead of skipped.” U `neuro_model` da `graph.py` dan boshqa fayl yo‘qligini va `STUDENT_MODEL_ENGINE != "thesis_hybrid"` ni tasdiqlardi; ikkalasi ham endi noto‘g‘ri. Ikkinchisi 3-bosqich “Kutilmoqda” bo‘lib turishini talab qiladi, u esa yuqoridagi jadvalda endi “Bajarildi”.

**Demak V guruhlari qayta yozilishi kerak:** V-A1…V-A4 (sof talaba modeli) va V-D1. Bu mustaqil tekshiruvchi sessiyaning vazifasi; prototip tomonida kutilgan qiymatlar allaqachon test sifatida yozilgan (yuqoridagi jadval).

### Ataylab qilingan tanlovlar (spetsifikatsiyada ochiq qolgan joylar)

- **`S0 < S_MAX` qat’iy.** 4-bo‘limdagi BKT ketma-ketligi S = 0.1 ni ishlatadi, bu esa `S_MAX` ning o‘zi; γ_S chegarada aniqlanmagan. Uchidan-uchiga testda S0 chegaraga pastdan yaqinlashtirildi (`0.099999`), sof testda esa `bkt.step` to‘g‘ridan-to‘g‘ri S = 0.1 bilan chaqiriladi. Natija ikkalasida ham etalon qiymatlarga mos.
- **`n_answers` bayroqlardan qat’i nazar o‘sadi.** `use_irt=False` bo‘lganda θ va b qotib turadi, lekin hisoblagichlar harakatlanadi: K(n) berilgan javoblar bo‘yicha kichrayishi kerak, aks holda bayroqni yoqqanda qadam noto‘g‘ri kattalikdan boshlanadi.
- **Rebuild qamrovdan tashqaridagi holatni o‘chirmaydi.** `seed` javobi berilganda jonli yo‘l holat yozadi; standart rebuild uni qayta o‘ynamaydi va **o‘chirmaydi** ham — faqat qamrovdagisini qayta quradi. Buni test hujjatlashtiradi.
- **Diskret `MasteryLevel` saqlandi.** Hozirgi interfeys shu maydonni ko‘rsatadi; 4-bosqich uni τ/δ gisterezisi bilan almashtiradi (F2).
- **Diagnostika endpoint'i yaxshilandi.** `theta_at_time` endi ledger'dagi haqiqiy `theta_after` dan olinadi (ilgari har bir qator uchun joriy θ qaytarilardi). Bu 3-bosqich ochgan imkoniyat.

### Foydalanuvchi bajarishi kerak bo‘lgan ishlar

- **Dev bazasiga migratsiya.** `venv/bin/python manage.py migrate` — `assessments.0009_student_model` dev bazadagi 6 ta `(user, topic)` `UserAbility` qatorini o‘chiradi (D33) va sonini chop etadi. Bu qaytarib bo‘lmaydigan amal, shuning uchun sizning muhitingizda bajarilmadi.
- **Dev demo ma’lumotini qayta qurish (ixtiyoriy).** Migratsiyadan keyin `venv/bin/python manage.py rebuild_student_states --include-legacy` demo holatlarini yangi model bilan tiklaydi.
- **pyBKT (ixtiyoriy).** `calibrate_bkt --method=pybkt` kerak bo‘lsa: `venv/bin/pip install -r requirements-dev.txt`. Standart grid search uchun hech narsa kerak emas.
---

## 4-bosqich hisoboti (tayyorlik va holatlar)

Qamradi: P0-3, P0-6, TY1–TY6, ES2; audit 4.3 (to‘rtta implementatsiya, global `is_unlocked`, qayta yopilish, yopiq mavzuga javob berish), 3.4 (ikki xil son), 2.4 (`learning_path/tree` dagi `mastery_percentage` aslida `score` edi).

### Nima qilindi

- **Sof tayyorlik (7-qoida).** `neuro_model/readiness.py`: M belgisi τ/δ gisterezis bilan, R_s(w), r_s(w), `missing_count`, Algoritm 2.3 ning tarqalishi (`propagate`), TY6 uchun O(n+m) qayta hisoblash (`recompute_counters`) va holatlar o‘tish jadvali (`next_status`). Django importi yo‘q — buni `test_purity.py` tekshiradi.
- **Gisterezis saqlanadigan qiymat.** M `p_mastery >= τ` emas: τ va τ−δ orasida u avvalgi qiymatini saqlaydi, shuning uchun hisoblanmaydi, balki `mastered_flag` ustunida saqlanadi. Aks holda τ atrofida turgan talaba har bir javobda o‘ziga bog‘liq mavzularni ochib-yopib turardi.
- **`StudentTopicState`.** `UserKnowledgeState` butunlay almashtirildi. Maydonlar: `p_mastery`, `mastered_flag`, `status`, `missing_count`, `started_at`, `kb_version`, `attempts`, `correct`, `accuracy`. Eski `mastery_percentage` bitta ustunda ikki shkalani saqlardi (ehtimollik va 0–100 baho) — bu qiymatlar **ko‘chirilmadi**, jadval tashlandi va holatlar `rebuild_student_states` bilan qayta quriladi. Yangi ustunda bu strukturaviy jihatdan imkonsiz: `p_mastery` [0,1] DB cheklovi bilan.
- **TY5 DB darajasida.** `state_started_matches_status` cheklovi: `started_at` to‘lgan qator faqat `in_progress`/`mastered`/`review` bo‘lishi mumkin, bo‘sh qator faqat `closed`/`open`. Ya’ni “boshlangan” va “yopiq emas” — bir xil narsa, va TY5 ni kod ham, baza ham buzolmaydi.
- **Yagona tayyorlik servisi.** `assessments/services/readiness.py`. U to‘rtta eski implementatsiyani almashtirdi:
  1. `Topic.is_unlocked` global bayrog‘i va `orchestrator._unlock_child_topics` ota→farzand kaskadi;
  2. `curriculum.services.graph.is_unlocked_dag` (ota tugunga fallback bilan);
  3. `curriculum/views/graph.py` ichidagi har bir so‘rovda qayta hisoblangan `is_unlocked`;
  4. `submit_test_session` ning o‘tgan bahoda farzandlarni ochishi.
  Endi bitta joy qaror qiladi. Vazifalari: yangi talaba uchun boshlang‘ich holat (`missing_count` = |Pre(w)|), Algoritm 2.3 (`apply_answer`), TY6 (`resync`), va `check_open` — yopiq mavzu uchun yetishmayotgan prerekvizitlar ro‘yxati.
- **Meros faqat G_L orqali.** Ota tugun o‘zlashtirilgani mavzuni ochmaydi; faqat `Pre(w)` dagi barcha tugunlarda M = 1 bo‘lishi ochadi. Bu audit 4.3 ning asosiy topilmasi edi va alohida test bilan yopilgan (`test_a_mastered_parent_does_not_open_its_child`).
- **Olib tashlanganlar.** `Topic.is_unlocked` (migratsiya `curriculum 0014`), `is_unlocked_dag`, `_unlock_child_topics`, `MasteryLevel` enum'i, `mastery_level_for()`, `settings.MASTERY_THRESHOLD`, `orchestrator.MASTERY_THRESHOLD`, `UserKnowledgeState`, holat qatoridagi `streak` ustuni.
- **`streak` ledger'dan.** Dashboard'dagi “streak” endi holat qatoridan emas, javoblar logidan o‘qiladi (`_trailing_streak`). U model miqdori emas, append-only ledger esa javoblarni tartibda saqlaydi.
- **Orchestrator.** Algoritm 2.4 ning 7-qadami qo‘shildi: javobdan keyin `readiness.apply_answer` M ni qayta hisoblaydi va o‘zgargan bo‘lsa Succ(v) hisoblagichlarini siljitadi. Yopiq mavzu `TopicClosed` bilan rad etiladi (3-qadam, yozuvdan oldin). `readiness_score` va `was_ready` endi ledger'ga **javob berilgan paytdagi** qiymat sifatida yoziladi (ilgari NULL edi).
- **Endpoint'lar.** `next_question`, `submit_answer` va `test_session` yopiq mavzuga **403** qaytaradi, tanasi `{"missing": [{"topic_id", "name", "p_mastery"}]}` va u programme order (`pos`) bo‘yicha tartiblangan. Daraxt, DAG, dashboard, testlar ro‘yxati va `knowledge_states` bir xil `p_mastery`, `accuracy`, `status` (+ `mastered`, `missing_count`) maydonlarini qaytaradi — buni bitta test to‘rtta endpoint'ni taqqoslab tasdiqlaydi.
- **D22 bo‘yicha.** Holat faqat `topic` turida bo‘ladi: bo‘lim va kurs uchun holat qatori yaratilmaydi (ularda savol yo‘q, Y4), DAG ularni standart qiymatlar bilan ko‘rsatadi. UI ular uchun `k / n` ko‘rsatadi (7-bosqich).
- **`rebuild_student_states` kengaytirildi.** Endi P(L), θ, b_q dan tashqari M, `status` va `missing_count` ni ham tiklaydi — **Algoritm 2.3 ni qayta o‘ynab**, oxirida qayta hisoblamay. Sabab: holatlar yo‘lga bog‘liq (`mastered → review` ni `open → in_progress` dan faqat oldingi holat ajratadi), M ning o‘zi ham gisterezisli, ya’ni javoblar tartibiga bog‘liq.
- **Soxta holat olib tashlandi.** `seed_data` ilgari 7 ta `UserKnowledgeState` qatorini qo‘lda yozardi (0.95, 0.68, …) — bu D8 ga qarshi edi. Endi u faqat haqiqiy `seed` javoblarini yozadi va oxirida `rebuild_student_states --include-legacy` chaqiradi, ya’ni holatlar javoblardan kelib chiqadi.
- **`seed_thesis_demo` qoidaga bo‘ysunadi.** Demo talabasi ham haqiqiy o‘quvchi kabi tayyorlik darvozasidan o‘tadi: mavzular programme order bo‘yicha javoblanadi va hali yopiq bo‘lgani o‘tkazib yuboriladi hamda hisobotda aytiladi. Ilgari u yopiq mavzularga ham javob berardi.

### 4-bo‘lim etalon qiymatlari (tayyorlik)

τ=0.95, δ=0.10. Boshlang‘ich holat: t1=0.97, t2=0.96, t3=0.98, t5=0.96 (M=1); t4=0.62 (`in_progress`).

| Tekshiruv | Kutilgan | Natija |
|---|---|---|
| Yangi talaba hisoblagichlari | t3=1, t4=1, t5=1, t6=3, t7=2, t8=2 | mos |
| Boshlang‘ich holatda hisoblagichlar | t6=1, t7=2, t8=2 | mos |
| t4 ga 1-to‘g‘ri javob: P(L) 0.62 → 0.8921 | hisoblagichlar o‘zgarmaydi (M band ichida) | mos |
| t4 ga 2-to‘g‘ri javob: P(L) → 0.9764 | t6 ochiladi; t7, t8 2 → 1 | mos |
| M 1 dan 0 ga tushsa | t4 `review`, t6 qayta yopiladi (boshlanmagan) | mos |
| Meros probe'i | o‘zlashtirilgan ota mavzuni ochmaydi | mos |
| TY5 | boshlangan mavzuga yangi prerekvizit qo‘shilsa hisoblagich o‘sadi, lekin holat `in_progress` qoladi va 403 bermaydi | mos |
| TY6 | `kb_version` orqada qolgan qator hisoblagichlari M belgilaridan qayta hisoblanadi | mos |

### Natijalar

| Tekshiruv | Natija |
|---|---|
| `venv/bin/pytest` (prototip) | **627 passed**, 13 subtests (4-bosqichdan oldin 566) |
| `venv/bin/python manage.py check` | toza (0 silenced) |
| `venv/bin/python manage.py makemigrations --check --dry-run` | No changes detected |
| `neuro_model` yolg‘iz | 433 passed |
| `venv/bin/pytest --ds=verification.settings verification/tests -q` | **687 passed, 7 failed** |

Tekshiruv suite'iga tegilmadi.

### Tekshiruvdagi FAIL'lar

Uchtasi B2.1 dan qolgan va o‘sha bo‘limda asoslangan. Qolgan to‘rttasi — `test_na.py` ning o‘z signali (“these tests start failing the moment a stage lands”):

| Test | Nega |
|---|---|
| `test_pending_stages[3]` | 3-bosqich endi “Bajarildi” |
| `test_pending_stages[4]` | 4-bosqich endi “Bajarildi” |
| `test_na_group_a_student_model_is_not_implemented` | `neuro_model` da `graph.py` dan boshqa fayllar bor, `STUDENT_MODEL_ENGINE` yo‘q |
| `test_na_group_c_and_d_readiness_and_trajectory_are_not_implemented` | `StudentTopicState` modeli endi mavjud; `p_mastery`/`missing_count`/`status` maydonlari bor |

**Demak qayta yozilishi kerak:** V-A1…V-A4 (sof model), V-C1…V-C12 ning 4-bosqichga tegishli qismi va V-D1. Trayektoriya endpoint'lari (`trajectory`, `path-to`) hamon yo‘q — ular 6-bosqichda.

### API o‘zgarishlari (buzuvchi)

7-bosqichda frontend shu maydonlarga moslanadi (D20–D29). Hozircha backend API shakli o‘zgardi:

| Endpoint | Olib tashlandi | Qo‘shildi |
|---|---|---|
| `GET /api/learning_path/tree/` | `mastery_percentage` (aslida `score` edi), `mastery_level`, `mastery_level_display`, `is_unlocked` | `p_mastery`, `accuracy`, `status`, `mastered`, `missing_count`, `attempts` |
| `GET /api/curriculum/prerequisite-graph/` | `data.is_unlocked`, `data.mastery_pct` | `data.p_mastery`, `data.accuracy`, `data.status`, `data.mastered`, `data.missing_count` |
| `POST /api/assessments/submit_answer/` | `mastery_level`, `mastery_display`, `mastery_percentage`, `streak` | `p_mastery`, `status`, `mastered`, `accuracy`, `attempts`, `opened_topics`; yopiq mavzuga **403** |
| `GET /api/assessments/next_question/`, `GET /api/assessments/test_session/` | — | yopiq mavzuga **403** `{missing: [...]}` |
| `GET /api/assessments/tests/` | `is_unlocked`, `mastery_percentage` | `p_mastery`, `accuracy`, `status`, `mastered`, `missing_count` |
| `GET /api/knowledge_states/` | `mastery_level`, `mastery_display`, `score`, `total_attempts`, `correct_attempts`, `streak` | `status`, `status_display`, `p_mastery`, `mastered_flag`, `missing_count`, `accuracy`, `attempts`, `correct`, `started_at` |
| `GET /api/analytics/overview/` | `heatmap`/tavsiyalarda `mastery_percentage`, `strongest/weakest.mastery_pct` | `p_mastery` va `status`; `topics_unlocked` = holati `closed` bo‘lmaganlar, `topics_mastered` = M belgisi |
| Topic serializerlari (student, instructor) | `is_unlocked` | — |

### Ataylab qilingan tanlovlar

- **`UserKnowledgeState` qayta tuzilmadi, almashtirildi.** Spetsifikatsiya ikkisini ham ruxsat beradi. Yangi maydon to‘plami butunlay boshqa (M, holat, hisoblagich, `kb_version`), eski nom esa endi mazmunni ifodalamaydi, shuning uchun toza almashtirish tanlandi — aralash shkalali ustunlarni ortidan tortib yurmaslik uchun.
- **Holat qatorlari o‘qishda materializatsiya qilinadi.** `states_for` yo‘q qatorlarni `bulk_create(ignore_conflicts=True)` bilan yaratadi va `kb_version` orqada bo‘lsa `resync` qiladi. Barqaror holatda bu bitta SELECT va hech qanday yozuv emas. Shu sababli daraxt/DAG/dashboard GET'lari birinchi murojaatda yozishi mumkin — bu idempotent va tranzaksiya ichida.
- **`readiness_score` javob berilgan paytdan olinadi.** Algoritm 2.4 da tayyorlik 7-qadam, lekin ledger ustunining ma’nosi “r_s(w) at answer time”, shuning uchun u yangilashdan **oldin** hisoblanadi va shundan keyin Algoritm 2.3 bajariladi.
- **Prerekvizit o‘zlashtirilmagan bo‘lsa, unga javob berib bo‘lmaydi — shuning uchun P(L0) dagi “javob berilmagan prerekvizit” tarmog‘i endpoint orqali yetib bo‘lmaydigan bo‘ldi.** U hamon jonli: `rebuild_student_states` va seed buyruqlari mavzularga o‘z tartibida javob beradi. Shu sababli bu tarmoq dvigatelga to‘g‘ridan-to‘g‘ri chaqiruv bilan test qilinadi va buning sababi testda yozilgan.
- **`submit_test_session` P(L) ni o‘zgartirmaydi.** D7: baho imtihon natijasi. Endi u faqat `attempts`/`correct`/`accuracy` ni siljitadi va hech narsani ochmaydi. Test javoblarini model orqali o‘tkazish — 5-bosqich.
- **Diskret `MasteryLevel` olib tashlandi** (`docs/THESIS_MAPPING.md` F2 farqi yopildi).
- **Bog‘liqlik qoidasi saqlandi.** `curriculum/models.py` dagi “curriculum NEVER imports from assessments” qoidasi bo‘yicha daraxt va DAG ko‘rinishlarida `readiness` importi modul darajasida emas, metod ichida qilinadi — xuddi `curriculum/services/path.py` modelni `apps.get_model` bilan kech aniqlagani kabi. `curriculum/management/commands/` dagi buyruqlar avvaldan ikkala appni birlashtiradi, ular o‘zgartirilmadi.

### Foydalanuvchi bajarishi kerak bo‘lgan ishlar

- **Dev bazasiga migratsiya.** `venv/bin/python manage.py migrate` — `assessments.0010_student_topic_state` `UserKnowledgeState` jadvalini **tashlaydi** (qiymatlar ko‘chirilmaydi, spetsifikatsiya talabi), `curriculum.0014_drop_topic_is_unlocked` esa `Topic.is_unlocked` ustunini olib tashlaydi. Qaytarib bo‘lmaydi, shuning uchun sizning muhitingizda bajarilmadi. 3-bosqichning `assessments.0009` migratsiyasi ham hali qo‘llanmagan bo‘lsa, ikkisi birga qo‘llanadi.
- **Keyin holatlarni qayta qurish.** `venv/bin/python manage.py rebuild_student_states --include-legacy` — dev bazadagi holatlar, M belgilari va hisoblagichlar javoblar logidan tiklanadi.
- **Frontend.** API shakli o‘zgardi (yuqoridagi jadval). Moslashtirish 7-bosqichda, D20–D29 bo‘yicha.
---

## 5-bosqich hisoboti (test sessiyasi modeldan o‘tadi)

Qamradi: P0-1 (backend qismi), D7; audit 2.6 (`SubmitTestSessionView` atomar emas va read-modify-write), 7.1 (`test_test_session.py:140` dagi 100.0), 7.4 (`TestsListView` va `SubmitTestSession` N+1).

### Nima qilindi

- **Bitta javob yo‘li ikkala endpoint uchun.** `orchestrator.apply_one_answer` ajratib olindi: u D25 tasnifini, javob berilgan paytdagi tayyorlikni, Algoritm 2.4 ni, Algoritm 2.3 ni, ledger'ni va tarixni bajaradi. `submit_answer` ham, test sessiyasi ham aynan shu funksiyani chaqiradi. Ya’ni test javobi “xuddi shunday” emas, balki **bir xil kod** orqali model kuzatuviga aylanadi (D7).
- **`assessments/services/test_session.py`.** View'dan butun mantiq ko‘chirildi. Servis `@transaction.atomic`, barcha tegishli mavzular uchun advisory lock bir marta va tartiblangan holda olinadi (`process_submission` bilan bir xil tartib, shuning uchun ikkisi o‘zaro deadlock bo‘lmaydi). Read-modify-write (`state.total_attempts += len(...)`) olib tashlandi — hisoblagichlar har bir javobda `readiness.apply_answer` orqali `select_for_update` bilan siljiydi.
- **Baho va model ajratildi.** `grade_paper` — sof funksiya: vaznli ball (oson 1, o‘rta 2, qiyin 3), foiz, o‘tdi/o‘tmadi, taqsimot. U faqat `TestSessionResult` ga yoziladi. `p_mastery`, M va tayyorlik esa javoblarning o‘zidan keladi. Javob berilmagan satr ham `total_points` ga qo‘shiladi (imtihonda bo‘sh qoldirilgan savol — xato javob), lekin ledger'ga yozilmaydi.
- **N+1 yopildi.**
  - `resolve_paper` butun varaqni **2 so‘rovda** yuklaydi (savollar va variantlar), varaq uzunligidan qat’i nazar. Ilgari har bir javob uchun 3 so‘rov ketardi. Buni `assertNumQueries(2)` bilan test tasdiqlaydi — 1 satr uchun ham, 4 satr uchun ham, 20 ta mavjud bo‘lmagan satr uchun ham.
  - `TestsListView` har bir mavzu uchun ~4 so‘rov yuborardi. Endi savol soni va qiyinlik yig‘indisi bitta agregat so‘rovda olinadi, ota tugun `select_related("parent")` bilan, qolgani xotirada yig‘iladi. Test har bir qo‘shimcha mavzuga **1 dan kam** so‘rov tushishini tasdiqlaydi.
  - `readiness.apply_answer` endi `states` ni parametr sifatida qabul qiladi, shuning uchun test sessiyasi har bir javobda holatlarni qayta o‘qimaydi.
- **Ortiqcha `atomic` olib tashlandi.** `analytics/views/dashboard.py` faqat o‘qiydi (audit 2.6).
- **Yopiq mavzu imtihon ham bo‘lmaydi.** `submit_test_session` ham `TopicClosed` → **403** `{missing: [...]}` qaytaradi, `test_session` GET'i kabi.
- **Javob shakli.** `submit_test_session` endi bahodan tashqari holatni ham qaytaradi: `p_mastery`, `accuracy`, `status`, `mastered`, `opened_topics`. `answers_summary` har bir satr uchun `source` ni ham beradi (`test_session`, `review_repeat` yoki javob berilmagan bo‘lsa `null`).

### Audit 7.1 — shkala xatosi testdan chiqarildi

Eski test `mastery_percentage == 100.0` ni tasdiqlardi, ya’ni bahoni o‘zlashtirish ehtimoli deb qotirib qo‘ygan edi. Endi test spetsifikatsiya talab qilganini tekshiradi:

- `p_mastery` ∈ [0, 1];
- `p_mastery` bahodan (`grade_percentage`) **farq qiladi** — ular turli shkalalar;
- `p_mastery` `rebuild_student_states` qayta o‘ynash natijasiga **1e-12 aniqlikda teng** — ya’ni test javoblari haqiqatan shu Algoritm 2.4 dan o‘tgan.

### Natijalar

| Tekshiruv | Natija |
|---|---|
| `venv/bin/pytest` (prototip) | **645 passed**, 13 subtests (5-bosqichdan oldin 627) |
| `venv/bin/python manage.py check` | toza (0 silenced) |
| `venv/bin/python manage.py makemigrations --check --dry-run` | No changes detected |
| `venv/bin/pytest --ds=verification.settings verification/tests -q` | **686 passed, 8 failed** |

Migratsiya talab qilinmadi: 5-bosqich sxemani o‘zgartirmaydi.

### Tekshiruvdagi FAIL'lar

Uchtasi B2.1 dan (asoslangan), beshtasi `test_na.py` ning o‘z signali: `test_pending_stages[3]`, `[4]`, `[5]`, `test_na_group_a_student_model_is_not_implemented` va `test_na_group_c_and_d_readiness_and_trajectory_are_not_implemented`.

### Ataylab qilingan tanlovlar

- **Sessiya davomiyligi o‘ylab topilmadi.** Bosqich tavsifida `TestSessionResult` uchun “vaqtlar” deyilgan. Hozir modelda `submitted_at` bor, har bir javobning vaqti esa ledger'da (`answered_at`). “Talaba qancha vaqt sarfladi” degan son uchun klient varaqni qachon ochganini aytishi kerak — bu 7-bosqich ishi. Server tomonidagi insert vaqtlaridan davomiylik chiqarish mumkin edi, lekin ular bitta tranzaksiyada yozilgani uchun natija millisekundlar bo‘lardi va soxta son bo‘lib qolardi (D8/D23 ruhi). Shuning uchun qo‘shilmadi.
- **Baho barcha javoblar bo‘yicha hisoblanadi, ledger esa faqat javob berilganlarni oladi.** `review_repeat` bo‘lgan javob ham bahoga kiradi (bu imtihon), lekin modelni siljitmaydi (D25). Ikkinchi marta bir xil varaqni topshirganda baho yana hisoblanadi va saqlanadi, P(L) esa o‘zgarmaydi — buni test tasdiqlaydi.
- **Boshqa savolga tegishli `choice_id`** savolni saqlab, javob berilmagan deb hisoblanadi va ledger'ga yozilmaydi; 400 qaytarilmaydi, chunki imtihon varag‘ining bitta satri xato bo‘lsa ham qolganlari baholanishi kerak.
- **Har bir javobga tushadigan so‘rovlar soni chiziqli qoladi** — bu Algoritm 2.4 ning har javobda bir marta bajarilishi, ya’ni tabiiy narx. Test varaqni **qayta yuklash** yo‘qligini tekshiradi, umumiy so‘rov sonini emas.
---

## 6-bosqich hisoboti (trayektoriya va API)

Qamradi: P1-8 (backend), TR1–TR4, ES7; audit 4.9. Addendum bo‘yicha A4-9…A4-12 endpoint'lari ham shu bosqichda.

### Nima qilindi

- **Sof trayektoriya (7-qoida).** `neuro_model/trajectory.py`: Algoritm 2.5 (A/B/C/D guruhlari), `impact(v) = |{w ∈ Desc*(v) : M_s(w) = 0}|`, `need(g)` va `path_to(g)`. Django importi yo‘q.
- **Tartib topologik.** Guruhlar G_L ning topologik tartibini (`snapshot.order`, Algoritm 2.2) ishlatadi, `position` ni emas. Audit 4.9 ning asosiy e’tirozi shu edi: `position, id` bo‘yicha saralangan ro‘yxatda turli shoxlardagi tugunlarning tartibi tasodifiy bo‘lardi.
- **A guruhi tartibi.** ta’sir kamayishi, so‘ng P o‘sishi: eng ko‘p ishni to‘sib turgan va eng zaif mavzu birinchi. Etalon holat (t1 ta’sir 4, t3 ta’sir 3) test bilan tasdiqlangan.
- **Sabablar tuzilmali.** Har bir element `{code, params}` qaytaradi — `review_impact`, `in_progress`, `ready`, `blocked`. Matn yo‘q: so‘zlar frontend'ning bitta lug‘at faylida (D20). Test har bir sabab kodining matn emasligini va `params` dagi barcha qiymatlarning son ekanini tekshiradi.
- **`assessments/services/trajectory.py`.** Django tomoni: holatlarni va snapshot'ni yuklaydi, sof funksiyani chaqiradi, nomlarni qo‘shadi. `?course=<id>` bo‘yicha bitta kursga chegaralanadi (Leaves(n)). Byudjet: bitta tayyorlik sinxronizatsiyasi + bitta nom so‘rovi, kurs hajmidan qat’i nazar — test har qo‘shimcha mavzuga **0.5 dan kam** so‘rov tushishini tasdiqlaydi (ES7).
- **Need_s(g) va yo‘l.** Yopiq g dan orqaga qarab yuriladi: Pre(node) dagi M = 0 bo‘lgan har bir u olinadi, va u ning o‘zi yopiq bo‘lsa qidiruv davom etadi. O‘zlashtirilgan tugun kerak emas, ochiq tugun kerak lekin undan orqaga yurilmaydi. Yo‘l — Need topologik tartibda, oxirida g. Etalon: Need(t7) = {t4, t6}, yo‘l t4 → t6 → t7.
- **Dashboard servisdan foydalanadi.** To‘rtta evristika (`recommended_next`, `needs_revision`, `ready_to_advance`, `coming_soon`) olib tashlandi. Ularning har birining o‘z tartibi va “ochiq” degan tushunchasi bor edi va bir-biriga qarama-qarshi chiqishi mumkin edi. Endi dashboard `trajectory.for_learner` ni chaqiradi va `trajectory: {groups, next}` qaytaradi. Test dashboard va endpoint **aynan bir xil** natija berishini tasdiqlaydi.

### Endpoint'lar

| Endpoint | Nima |
|---|---|
| `GET /api/learning/trajectory/?course=<id>` | Algoritm 2.5: `groups` (A, B, C, D), `items`, `next`, `kb_version` |
| `GET /api/learning/path-to/<topic_id>/` | `need`, `path`, `reachable` — topologik tartibda, oxirida maqsad |
| `GET /api/learning/mistakes/` | Xato javoblar, mavzular bo‘yicha guruhlangan (D25) |
| `POST /api/learning/mistakes/<attempt_id>/reviewed/` | “Ko‘rib chiqilgan” belgisi, idempotent |
| `GET /api/learning/topics/<topic_id>/history/` | Har bir urinish: p̂, P(G), P(S), P(L) oldin→keyin, θ, b, tayyorlik, natija, vaqt |
| `GET /api/me/summary/` | Profil, faqat haqiqiy ma’lumot (D27) |
| `GET /api/config/model/` | II bob konstantalari (D29) |

Ikki qoida hammasida: **hech narsa o‘ylab topilmaydi** — har bir son ledger'dan, talaba holatidan yoki `settings.THESIS_MODEL` dan o‘qiladi, backend hisoblab bera olmaydigan ko‘rsatkich esa taxmin qilinmaydi, yo‘q bo‘ladi (D23). Va **hech narsa so‘zlashtirilmaydi** — sabablar kod va sonlar (D20).

### Tanlovlar va tafsilotlar

- **“Ko‘rib chiqilgan” belgisi alohida jadvalda.** Ledger append-only, shuning uchun `AssessmentAttempt` ga ustun qo‘shib bo‘lmaydi. Yangi `MistakeReview` modeli (migratsiya `assessments 0011_mistake_review`). O‘chirish yo‘q: “Tozalash” tugmasi olib tashlanadi, faqat belgilash mumkin (addendum 2.10). Test belgilash ledger qatorini o‘zgartirmasligini tasdiqlaydi, va boshqa talabaning xatosini belgilab bo‘lmasligini ham.
- **`corrected_later`** aynan shu savolga keyinroq to‘g‘ri javob berilganmi degan savolga javob beradi va bitta qo‘shimcha so‘rovda hisoblanadi.
- **Profilda XP, achievements va study_hours yo‘q** (D27): ularni haqiqiy ma’lumotdan hisoblab bo‘lmaydi, shuning uchun qaytarilmaydi. Buni test alohida tekshiradi. Haftalik faollik javob vaqtlaridan sanaladi. Foydalanuvchi ismi bo‘sh bo‘lsa `null` qaytadi — “Learner” degan to‘qima nom yo‘q.
- **Tarix ledger'dan o‘qiladi, qayta hisoblanmaydi.** Bu panel himoyada modelni ko‘rsatish uchun asosiy vosita (addendum 2.5), shuning uchun u javob berilgan paytda **ishlatilgan** qiymatlarni beradi, bugungi parametrlar bilan chiqadigan qiymatlarni emas.
- **`config/model` holatlar va guruhlar ro‘yxatini ham beradi**, shunda UI `closed`/`open`/… va A/B/C/D ni qattiq yozmaydi.
- **Bo‘lim va kurs trayektoriyada yo‘q.** Holat faqat `topic` turida (D22), shuning uchun `path-to` bo‘lim uchun 404 qaytaradi va trayektoriya faqat mavzulardan iborat.

### Natijalar

| Tekshiruv | Natija |
|---|---|
| `venv/bin/pytest` (prototip) | **706 passed**, 13 subtests (6-bosqichdan oldin 645) |
| `venv/bin/python manage.py check` | toza (0 silenced) |
| `venv/bin/python manage.py makemigrations --check --dry-run` | No changes detected |
| `neuro_model` yolg‘iz | 461 passed |
| `venv/bin/pytest --ds=verification.settings verification/tests -q` | **685 passed, 9 failed** |

### Tekshiruvdagi FAIL'lar

Uchtasi B2.1 dan (asoslangan), oltitasi `test_na.py` ning o‘z signali: `test_pending_stages[3]`, `[4]`, `[5]`, `[6]`, `test_na_group_a_student_model_is_not_implemented`, `test_na_group_c_and_d_readiness_and_trajectory_are_not_implemented`.

**Diqqat:** `test_na_group_c_and_d` trayektoriya endpoint'ini `reverse("trajectory")` bilan qidiradi, bizning URL'lar esa `assessments` namespace'ida (`assessments:trajectory`), shuning uchun u endpoint mavjudligini **sezmaydi** — test boshqa sababdan (`StudentTopicState` paydo bo‘lgani) yiqiladi. `test_na_group_f` ham shu sababdan hamon o‘tadi. Bu V-D1 qayta yozilganda hisobga olinishi kerak: endpoint nomlari namespace bilan `assessments:trajectory` va `assessments:path-to`.

### API o‘zgarishi (buzuvchi)

| Endpoint | Olib tashlandi | Qo‘shildi |
|---|---|---|
| `GET /api/analytics/overview/` | `recommendations` (`recommended_next`, `needs_revision`, `ready_to_advance`, `coming_soon`) | `trajectory` — `{groups: {A, B, C, D}, next}` |
---

## 7-bosqich hisoboti (frontend)

Qamradi: P0-1 (UI), TR5, P2-5, P2-6, D16, D17, D19; audit 3.2–3.4, 7.2, 7.3. Addendum: D20–D29 va 2.1–2.11 sahifa talablari.

Backend commit: `81f745b` (D16 va foydalanuvchi boshqaruvi API). Frontend commit: `c2bb542` (99 fayl).

### Backend tomoni (D16 va foydalanuvchilar)

- **Refresh token httpOnly cookie'da.** Audit 7.3: ikkala JWT `localStorage` da edi — sahifadagi har qanday skript o‘qiy olardi. Endi access token javob tanasida (SPA xotirada saqlaydi), refresh token esa `HttpOnly` cookie'da: `/api/accounts/token/` yo‘liga chegaralangan, DEBUG tashqarisida `Secure`, standart `SameSite=Lax`.
- **CSRF.** Brauzer cookie'ni o‘zi yuborgani uchun `login`, `refresh` va `logout` Django'ning CSRF tekshiruvidan o‘tadi. Login ham: aks holda hujumchi o‘z sessiyasini qurbon brauzeriga o‘rnatishi mumkin (login CSRF). SPA tokenni `GET /api/accounts/csrf/` dan oladi.
- **Rotatsiya va blacklist.** Har bir `refresh` yangi cookie beradi va eskisini bloklaydi; `logout` joriy tokenni bloklab, cookie'ni tozalaydi va idempotent.
- **Foydalanuvchi boshqaruvi (addendum 2.7).** Ruxsat endi `is_staff` emas, API qaytargan `admin` roli (`IsAdminRole`) — eski `IsAdminUser` `Admin` guruhidagi, lekin xodim bo‘lmagan adminni kiritmasdi va xodim o‘qituvchini kiritardi. `PATCH` rolni `Instructor`/`Admin` guruhlari orqali beradi va `is_active` ni almashtiradi. Guruh mexanizmi ifodalay olmaydigan holatlar yarim bajarilmaydi, rad etiladi: superfoydalanuvchi har doim admin, xodim kamida o‘qituvchi, admin o‘z rolini o‘zgartira olmaydi. Ro‘yxat `is_simulated` ni qaytaradi va rol/simulyatsiya bo‘yicha filtrlanadi (D13).

### Frontend: uchta “yagona manba”

- **Sonlar matnga aylanadigan bitta joy** — `src/lib/format.ts`. Ikki shkala aniq ajratildi: `p_mastery`, `accuracy`, p̂ — [0,1] dagi ehtimolliklar, foiz sifatida ko‘rsatiladi; test bahosi esa allaqachon foiz. Audit 3.4 topgan ikki xato aynan shu aralashuvdan kelib chiqqan edi: ehtimollikni o‘z soni sifatida chop etish (“0.8%”) va bahoni qayta ko‘paytirish (“100%”).
- **Holat palitrasi** — `src/lib/status.ts` (D21). 2.3 va 2.4-rasmlardagi ranglar; graf tugunlari, kartalar, heatmap va legenda bir xil manbadan oladi. `CustomTopicNode` ilgari `mastery_percentage >= 70` deb taqqoslardi — ehtimollikni 70 bilan — va 3 ta holati bor edi. Endi 5 ta holat backend'dan keladi. Yopiq matn `slate-700`: avval o‘qib bo‘lmas darajada och edi (audit topilmasi).
- **Sabablar** — `src/lib/reasons.ts` (TR3, D20). Backend `{code, params}` qaytaradi, matn esa `uz.json`/`en.json` da. Test sabab kodining interfeysga chiqib ketmasligini tasdiqlaydi.

### Sahifalar

| Sahifa | Nima qilindi |
|---|---|
| **Bosh sahifa** | 4 ta KPI: o‘zlashtirilgan k/n, takrorlash kerak, ochiq, oxirgi 7 kundagi javoblar. Streak va “weekly goal” olib tashlandi (tezisga aloqasi yo‘q), P(L) o‘rtachasi ham (mazmunsiz). “Keyingi qadam” trayektoriya API'sidan: birinchi element katta tugma, qolganlari A–D guruhlarida sabablari bilan. Kurs ildizi endi tavsiya sifatida chiqmaydi — servis faqat mavzu qaytaradi. Heatmap D21 palitrasidagi holatlar to‘ri. |
| **O‘quv yo‘li** | **“Ikki qatlam” standart rejim** (2.2 va 2.3-rasmlar): kurs va bo‘limlar — ramka, mavzular ularning ichida. DAG rejimi mavzularni `lev` ustunlariga, ustun ichida `pos` bo‘yicha joylashtiradi — deterministik. dagre ixtiyoriy rejim sifatida qoldi, lekin standart emas: u aloqasiz tugun qo‘shilganda ham siljiydi, ya’ni bir grafning ikki skrinshoti bir-biriga mos kelmaydi. Meros G_L qirralari uzuq chiziqda, tugma ortida. Tugunni bosganda yon panel: holat, P(L), yetishmayotgan prerekvizitlar o‘z P(L) bilan, “Mashq qilish” va “Shu mavzugacha yo‘l”. Yo‘l Need(g) ni ajratib ko‘rsatadi, qolganini xiralashtiradi. |
| **Mashq va testlar** | Ikki rejim alohida kartada tushuntirildi. Yopiq mavzu kartasi faol emas: qulf va nimasi yetishmayotgani. Doimiy “Medium” nishoni olib tashlandi; qiyinlik, ko‘rsatilsa, savollarning o‘rtacha b qiymatidan. Easy/Medium/Hard filtri o‘rniga holat bo‘yicha filtr. |
| **Quiz** | **Mashq rejimi** (`useAdaptiveQuiz`): bir vaqtda bitta savol, javobdan keyin natija va `Question.explanation` ekranda **qoladi** — eski hook 1.5 soniyada avtomatik o‘tib, o‘zi olgan tushuntirishni yashirardi. Holat o‘zgarsa va yangi mavzu ochilsa toast. Qiyinlik nishoni yo‘q: savol `|b_q − θ_s|` bo‘yicha tanlangan, bucket yorlig‘i uni noto‘g‘ri tasvirlaydi. Klaviatura: A–D tanlaydi, Enter tasdiqlaydi. **Test rejimi** natijasida baho va model holati alohida bo‘limlarda (D7). |
| **Mavzu sahifasi** | Kontent kengligi boshqa sahifalar bilan bir xil. “Qanday hisoblandi” paneli: τ chizig‘i (`config/model` dan), P(L) grafigi (to‘g‘ri javob — to‘ldirilgan nuqta, xato — bo‘sh), urinishlar jadvali (p̂, P(G), P(S), P(L) oldin→keyin, vaqt), θ kurs bo‘yicha, “Rasch (a = 1)”. “BKT + IRT PROOF” kartasi va “2PL” yorlig‘i yo‘q. |
| **Xatolar ustida ishlash** | `GET /api/learning/mistakes/` dan: mavzular bo‘yicha guruhlangan, har xato uchun savol, talaba javobi, to‘g‘ri javob, o‘qituvchi tushuntirishi, sana va keyinroq to‘g‘ri yechilganmi. “Tozalash” tugmasi yo‘q — faqat “ko‘rib chiqildi” belgisi. `lib/mistakeStorage.ts` o‘chirildi. |
| **Profil** | `GET /api/me/summary/` dan: kurs bo‘yicha k/n va θ, urinishlar, aniqlik, takrorlash soni, haftalik faollik. Qo‘lda yozilgan `weeklyActivity`, `masteryData`, `achievements`, `recentHistory` massivlari va ular bilan birga XP, achievements, “study hours” olib tashlandi — ularni haqiqiy ma’lumotdan hisoblab bo‘lmaydi (D27). Ismi bo‘lmasa “Learner” emas, “ism kiritilmagan” deyiladi. |
| **Kurs konstruktori** | **5-qadam “Prerekvizitlar”** qo‘shildi — dissertatsiyaning markaziy qismi, UI'da umuman yo‘q edi. React Flow muharriri: `onConnect` Algoritm 2.1 orqali qirra qo‘shadi, ω tahrirlanadi, qirra o‘chiriladi. Rad etilganda `reason` kodidan tushunarli xabar, sikl bo‘lsa `chain` grafda **qizil** chiziladi — o‘qituvchi sikl qayerda yopilganini ko‘radi. Meros qirralari uzuq va faqat o‘qish uchun. Ortiqcha qirralar va κ alohida panelda, avtomatik tuzatilmaydi (GR3). |
| **Foydalanuvchilar** | Email prefiksi “Unnamed User” o‘rniga, rol filtri va rol berish, simulyatsiya nishoni va ularni yashirish filtri, faolsizlantirish (qaytariladigan). |
| **Landing** | Matni modelga mos qayta yozildi: “Dynamic quizzes adjust difficulty in real-time” kabi da’volar va `/features`, `/pricing`, `/about`, `/privacy` havolalari (mavjud bo‘lmagan sahifalar) olib tashlandi. |
| **Kurslar va Qidiruv** | `pages/Courses.tsx` olib tashlandi (addendum 2.4: O‘quv yo‘li va bilim xaritasini takrorlardi). `pages/KnowledgeSearch.tsx` ham — u 12 ta soxta tushunchani qattiq yozib qo‘ygan edi (D23). |

### Soxta ma’lumot yo‘q (D23)

`grep` bilan tekshirildi va test bilan majburlanadi. Olib tashlangan massivlar: `KnowledgeSearch` (12 ta tushuncha + `didYouMeanMap` + trendlar), `MasteryHeatmap.masteryData`, `Profile` (4 ta massiv), `mistakeStorage`, `sampleQuestions.ts`, landing'dagi marketing matni.

### Til (D20)

`react-i18next`, `src/locales/uz.json` va `en.json` — **321 kalit, ikki tilda bir xil**. Testlar: kalit pariteti, bo‘sh satr yo‘qligi, gap ichida faqat birinchi harf katta (atamalar va model belgilaridan tashqari), taqiqlangan matnlar yo‘qligi. Atamalar D20 bo‘yicha: o‘zlashtirilgan, o‘rganilmoqda, ochiq, yopiq, takrorlash kerak, prerekvizit, mashq, test.

### Sifat va hajm

| Ko‘rsatkich | Oldin | Keyin |
|---|---|---|
| lint | 71 error, 12 warning | **0 error**, 8 warning |
| tsc (`tsconfig.app.json`) | 16 xato | **0** |
| vitest | 4 fayl, 10 test | **11 fayl, 71 test** |
| Kirish chunk (`index-*.js`) | 2 219.5 kB (gzip 617.8) | **182.7 kB (gzip 58.7)** |
| Landing chunk | — (kirishda edi) | 3.7 kB (gzip 1.4) |
| CSS | 123.3 kB (gzip 20.7) | 90.4 kB (gzip 15.8) |
| Chunk soni | 3 | 66 |

Eng katta chunk endi `Hero3DBackground` (850 kB): u landing sahifasining dekorativ three.js foni va **matndan keyin** yuklanadi. Qolganlari: `Course` (recharts), `useGraphLayout` (React Flow + dagre) — ikkisi ham faqat kerakli sahifada.

8 ta lint ogohlantirishi: 7 tasi shadcn `ui/` fayllarida (komponent va variantlarini bir faylda eksport qiladi — vendor kodi), 1 tasi avvaldan bor `AuthContext`.

### Ataylab qilingan tanlovlar

- **dagre standart emas.** `lev` joylashuvi deterministik: bir xil graf har doim bir xil ko‘rinadi, bu esa dissertatsiyaga skrinshot olish uchun zarur. dagre ixtiyoriy rejim sifatida qoldi.
- **three.js saqlandi, lekin lazy.** 850 kB faqat fon uchun ko‘p, lekin dizaynni buzmaslik uchun olib tashlanmadi — matndan keyin yuklanadi, ya’ni birinchi tashrif o‘qiladigan sahifani oladi, WebGL runtime'ni emas.
- **`any` emas, `unknown`.** `catch (err: any)` larning hammasi `unknown` ga o‘tkazildi va xato tanasi `getApiErrorMessage` / `kbErrorMessage` orqali o‘qiladi — ya’ni xato shakli bitta joyda tasvirlangan.
- **Playwright qo‘shilmadi.** Spetsifikatsiya “vitest yoki Playwright” deydi; qabul sharti (bir mavzu barcha sahifalarda bir xil holat) vitest bilan `src/test/one-vocabulary.test.tsx` da yozildi. Playwright brauzer binary'lari va CI sozlamasini talab qiladi.
- **`AuthContext` tipi `ReturnType<typeof useAuth>` ga aylantirildi** — `logout` endi async (cookie'ni serverda bloklash kerak), qo‘lda yozilgan interfeys esa undan ajralib qolardi.

### Natijalar

| Tekshiruv | Natija |
|---|---|
| Frontend: `npx eslint .` | **0 error**, 8 warning |
| Frontend: `npx tsc -p tsconfig.app.json --noEmit` | **0 xato** |
| Frontend: `npm test` | **71 passed** (11 fayl) |
| Frontend: `npm run build` | o‘tdi; kirish chunk 182.7 kB |
| Backend: `venv/bin/pytest` | **735 passed**, 13 subtests (7-bosqichdan oldin 706) |
| Backend: `check` / `makemigrations --check` | toza / No changes |
| `venv/bin/pytest --ds=verification.settings verification/tests -q` | **685 passed, 9 failed** (o‘zgarmadi) |

Tekshiruvdagi 9 ta FAIL 6-bosqichdagi bilan bir xil: 3 tasi B2.1 dan, 6 tasi `test_na.py` signali. Frontend o‘zgarishlari backend tekshiruviga ta’sir qilmadi.

### Bajarilmagani

- **`docs/ui/` skrinshotlari** (addendum 2.11): har bir sahifaning 1440 px, o‘zbek tilidagi skrinshoti. Buning uchun ishlaydigan brauzer va to‘ldirilgan dev bazasi kerak — bu muhitda bajarilmadi. 1280/768 px responsive tekshiruvi ham shunday.
- **Konsolda xato yo‘qligi** brauzerda tekshirilmadi; vitest ichida React Router'ning v7 future-flag ogohlantirishlari chiqadi (xato emas).

### Foydalanuvchi bajarishi kerak bo‘lgan ishlar

- **Backend migratsiyalari.** 3-, 4- va 6-bosqich migratsiyalari hali qo‘llanmagan bo‘lsa: `venv/bin/python manage.py migrate`. D16 sxemani o‘zgartirmaydi.
- **Frontend env.** `cp .env.example .env` va kerak bo‘lsa `VITE_API_URL` ni to‘g‘rilash. Backend `config/.env` da `FRONTEND_ORIGINS` frontend manzilini o‘z ichiga olishi kerak — cookie va CSRF shunga bog‘liq.
- **`npm install`** — `i18next` va `react-i18next` qo‘shildi.
- **Skrinshotlar.** Dev server va to‘ldirilgan baza bilan `docs/ui/` ga sahifa skrinshotlarini oling (addendum 2.11, dissertatsiyaning 3.1-bo‘limi uchun).
---

## 7.1-bosqich hisoboti (konstruktor tuzilmasi, qidiruv, skrinshot skripti)

Qamradi: `NEUROLEARN_B8_PLAN.md` 2-bo‘limi — D39, D40, D41. Addendum 2.6 ning qolgan yarmi va 2.11.

Backend commit: `f7bd3af`. Frontend commit: `02e3b2f`.

### D39 — Kurs konstruktorining tuzilmasi

Addendum 2.6 ikki narsani talab qilgan: prerekvizit muharriri (7-bosqichda bajarildi) va “outline + muharrir” tuzilmasi (bajarilmagan edi). Sabab oddiy: konstruktorda ikki xil ish bor va ularning shakli bir-biriga qarama-qarshi. **Yangi kurs yaratish** — ketma-ketlik: kurs, keyin ichidagi tugunlar, keyin materiallar, keyin savollar. **Mavjud kursni tuzatish** — ketma-ketlik emas: bitta tugunga borib, bitta maydonni o‘zgartirish. Shuning uchun sahifa tepasida ikki rejim tugmasi paydo bo‘ldi; wizard o‘zgarmadi, yonига tuzilma muharriri qo‘shildi.

**Tahrirlash rejimi** (`components/instructor/CourseStructureEditor.tsx`): chapda kurs daraxti, o‘ngda tanlangan tugun muharriri, tepada ikki yorliq — “Tuzilma” va “Prerekvizitlar”. Tahrirlanadigan maydonlar KB servisi qabul qiladiganlarning o‘zi: nom, slug, tavsif, ota tugun, tur, o‘tish bali, testdagi savollar soni. Drag-and-drop yo‘q (D39): tartib ikki tugma bilan, ota tugun esa ro‘yxatdan tanlanadi.

**Tartib — bitta so‘rov, bitta versiya.** Yangi `POST /api/curriculum/instructor/topics/<id>/reorder/ {"direction": "up"|"down"}` va uning ortidagi `kb.reorder_sibling()`. Bu alohida endpoint, chunki `position` ni ikkita `PATCH` bilan almashtirish ikki muammo tug‘diradi: so‘rovlar orasida ikki qo‘shni bir xil `position` da qoladi (tartib `(position, id)` bo‘yicha, ya’ni natija id ga qarab hal bo‘ladi) va bitta ko‘chirish uchun KB versiyasi ikki marta oshadi. Servis butun qatorni bitta KB o‘zgarishida 0..n−1 ga qayta raqamlaydi, shuning uchun seed qoldirgan bo‘shliqlar ham tozalanadi. Chetdagi tugun `at_edge` sababi bilan 400 oladi; interfeys tugmani o‘chirib qo‘yadi, lekin boshqa o‘qituvchi bir vaqtda tartibni o‘zgartirsa xabar ko‘rinadi.

**Tur o‘zgarishi faqat servis ruxsat berganda.** `section ↔ topic` o‘zgarishi `kb.update_node` da allaqachon tekshirilardi, lekin interfeys buni oldindan bila olmasdi va o‘qituvchi 400 olardi. Endi instruktor ro‘yxati har bir tugun uchun `question_count` va `child_count` qaytaradi: ichida tugun bor bo‘lim barg bo‘la olmaydi, savoli bor mavzu bo‘lim bo‘la olmaydi (Y4). Tur tanlagich bunday hollarda o‘chirilgan va ostida sababi yozilgan — matn rad etishning o‘z matni, ya’ni bitta qoida uchun bitta ibora (D20). Kurs turi hech qachon o‘zgarmaydi: kurs — har doim ildiz.

Bu ikki hisoblagich `Count(..., distinct=True)` bilan olinadi, `total_duration_minutes` esa subquery'ga ko‘chirildi. Sababi texnik, lekin jiddiy: bitta `Sum` va ikkita `Count` bir queryset'da uchta JOIN hosil qiladi va `Sum` savollar sonига ko‘payib ketadi. Test shuni tekshiradi (`test_the_counters_do_not_distort_the_duration`).

### D40 — Haqiqiy mavzu qidiruvi

`GET /api/learning/search/?q=` — faol tugunlar orasidan nom bo‘yicha `icontains`, natija `pos` tartibida, 20 ta bilan cheklangan. Arxivlangan tugun ham, arxivlangan ajdodi bor tugun ham chiqmaydi: so‘rov snapshot'dagi id'lar bo‘yicha filtrlanadi, snapshot esa aynan faol va ildizga ulangan tugunlardan iborat. Mavzu uchun shu talabaning holati va P(L) qaytadi, bo‘lim va kurs uchun ikkisi ham `null` (D22) — bo‘lmagan qiymat taxmin qilinmaydi (D23).

Interfeysda bu — sahifa emas, yuqori paneldagi panel (`components/layout/TopicSearch.tsx`). Natijani bosganda `/learning-path?topic=<id>` ga o‘tiladi va O‘quv yo‘li o‘sha tugunni tanlaydi: mavzu o‘z grafida, prerekvizitlari va unga olib boradigan yo‘l bilan birga o‘qiladi. Parametr bir marta ishlatiladi va URL'dan olib tashlanadi, aks holda “orqaga” tugmasi va keyingi tanlov bir-biri bilan kurashadi.

Olib tashlangan `KnowledgeSearch` sahifasi 12 ta soxta tushunchani qattiq yozib qo‘ygan edi. Qidiruvning o‘zi foydali edi, soxta ma’lumot esa muammo edi — shuning uchun qidiruv qaytdi, ma’lumot esa bilimlar bazasidan keladi.

### D41 — Skrinshot skripti

`neuro/neuro/scripts/screenshots.mjs` (Playwright) — 13 sahifa × 3 kenglik (1440, 1280, 768), o‘zbek tilida. Skript 7.1 ning natijasi; rasmlarni foydalanuvchi oladi, chunki ishlaydigan brauzer, frontend, backend va `seed_thesis_demo` bilan to‘ldirilgan baza kerak.

Skript deterministik bo‘lishga qurilgan, chunki dissertatsiyadagi rasmni himoyada qayta olish mumkin bo‘lishi kerak: viewport va piksel zichligi qotirilgan, mavzu har doim yorug‘ (mashinaning sozlamasi ta’sir qilmaydi), animatsiya va o‘tishlar o‘chirilgan, kursor va fokus halqasi yashirilgan, har kadrdan oldin tarmoq **va** ilovaning yuklash indikatori kutiladi. Graf sahifalari `lev` joylashuvida — 7-bosqichdagi tanlov aynan shu uchun qilingan edi.

Rol bilan bog‘liq joy ochiq aytilgan: o‘qituvchi va admin sahifalari rolni talab qiladi (D15), talaba akkaunti bilan ular `/dashboard` ga qaytariladi. Skript bunday sahifani rasmga olmaydi — `manifest.json` ga sababi bilan “skipped” deb yozadi, ya’ni skript ikki marta ishga tushiriladi. `manifest.json` da yana: sana, kengliklar, piksel zichligi, mavzu id'si, frontend commit'i va har bir faylning sahifasi — 3.1-bo‘limdagi rasm qaysi ishga tushirishdan kelganini aytadigan yagona manba.

Playwright ilovaning bog‘liqligi emas: u brauzer binary'larini yuklab oladi va CI'da keraksiz. Skript uni dinamik import qiladi va yo‘q bo‘lsa o‘rnatish buyrug‘ini chiqaradi. `docs/ui/README.md` — to‘liq ketma-ketlik (baza, server, frontend, skript) va kutilayotgan fayl ro‘yxati.

### Testlar

Backend, 21 yangi test:

- `curriculum/tests/test_structure_editor.py` (11) — tartib ikki tomonga va orqaga, bitta versiya oshishi, bo‘shliqli `position` larning qayta raqamlanishi, `at_edge` va noto‘g‘ri yo‘nalish, bo‘lim/kurs/ildiz darajasidagi tartib, arxivlangan qo‘shni slot egallamasligi, talabaga 403; hisoblagichlar va ular `total_duration_minutes` ni buzmasligi.
- `assessments/tests/test_topic_search.py` (10) — katta-kichik harfga bog‘liq bo‘lmagan qismiy moslik, bo‘sh so‘rov hamma narsani qaytarmasligi, mavzuda holat va P(L), bo‘lim va kursda yo‘qligi, yangi talabada yopiq mavzu, arxivlangan tugun va arxivlangan ost-daraxt, `pos` tartibi va 20 ta cheklov, bir xil so‘rovning bir xil javobi, anonimga 401, so‘rovlar byudjeti moslik soniga qarab o‘smasligi (ES7).

Frontend, 14 yangi test (2 yangi fayl):

- `components/instructor/CourseStructureEditor.test.tsx` (8) — daraxt qo‘shnilar tartibida, tartib tugmalari aynan chetlarda o‘chirilgan, bitta so‘rov, bitta tugunni wizard'siz tahrirlash, servis rad etadigan tur o‘zgarishi taklif qilinmasligi va sababi, kursga tur va ota tugun taklif qilinmasligi, prerekvizit muharriri yorliq sifatida, kurs yo‘qligi holati.
- `components/layout/TopicSearch.test.tsx` (6) — nom, kurs, holat nishoni va P(L) foiz sifatida; bo‘limda holat yo‘qligi; natijani bosganda `?topic=7`; moslik yo‘qligi haqida xabar; yozilmagunicha so‘rov yuborilmasligi; xato holatida bo‘sh ro‘yxat emas, xato xabari.

### Natijalar

| Tekshiruv | Natija |
|---|---|
| Backend: `venv/bin/pytest` | **756 passed**, 13 subtests (7-bosqichda 735) |
| Backend: `manage.py check` | 0 issues |
| Backend: `manage.py makemigrations --check --dry-run` | No changes detected (migratsiya qo‘shilmadi) |
| `pytest --ds=verification.settings verification/tests` | **684 passed, 10 failed** — o‘zgarishdan oldin ham aynan shunday |
| Frontend: `npx tsc --noEmit` | **0 xato** |
| Frontend: `npx eslint .` | **0 error**, 8 warning (o‘zgarmadi; hammasi vendor `ui/` va `AuthContext`) |
| Frontend: `npm test` | **85 passed** (13 fayl; 7-bosqichda 71/11) |
| Frontend: `npm run build` | o‘tdi |
| `node scripts/screenshots.mjs --list` / argument tekshiruvi | sahifalar ro‘yxati; noto‘g‘ri sahifa, akkauntsiz ishga tushirish va Playwright yo‘qligi tushunarli xabar bilan to‘xtaydi |

Tekshiruvdagi 10 ta FAIL: 3 tasi B2.1 dan qolgan, 7 tasi `test_na.py` signali (bosqich bajarilgach bu testlar ataylab buziladi — 5-qoida). 7.1 dan oldin ham 684/10 edi, ya’ni o‘zgarish ularga ta’sir qilmadi.

### Migratsiya yo‘q

7.1 sxemani o‘zgartirmaydi: `reorder` mavjud `position` ustunini yozadi, hisoblagichlar — annotatsiya, qidiruv — o‘qish. `makemigrations --check` toza.

### Ataylab qilingan tanlovlar

- **Tartib uchun alohida endpoint, `PATCH position` emas.** Yuqorida sababi: ikki so‘rov oralig‘ida tartib aniqlanmagan holatga tushadi va versiya ikki marta oshadi. Atomar amal bitta so‘rov bo‘lishi kerak.
- **Hisoblagichlar barcha savollarni sanaydi, faqat faollarini emas.** `kb._has_questions()` ham shunday qiladi; interfeysning taxmini servisning qaroriga aynan mos kelishi kerak, aks holda tanlagich yoqilgan bo‘lib, so‘rov 400 qaytaradi.
- **Qidiruv barcha turlarni qaytaradi.** Faqat mavzularni qaytarish osonroq bo‘lardi, lekin o‘qituvchi ham, talaba ham bo‘lim nomi bo‘yicha qidiradi; bo‘lim esa O‘quv yo‘lidagi ramka sifatida tanlanadi. Holat va P(L) esa faqat mavzuda bo‘ladi (D22).
- **Bo‘sh so‘rov — bo‘sh natija.** `q` bo‘sh bo‘lganda birinchi 20 tugunni qaytarish qidiruvni ro‘yxatga aylantiradi; panel esa qidiruv.
- **Playwright devDependency emas.** U brauzer binary'larini postinstall'da yuklab oladi; CI va `npm ci` uchun bu keraksiz. Skript uni dinamik import qiladi.
- **Rasmlar repoga qo‘shilmadi.** Ularni olish uchun brauzer kerak va ular demo bazasi holatiga bog‘liq; `docs/ui/README.md` nima qilish kerakligini yozadi.

### Bajarilmagani

- **`docs/ui/` dagi PNG fayllar.** Skript tayyor, rasmlar yo‘q — ular foydalanuvchi mashinasida olinadi (D41 shunday deydi).
- **Wizard matni ingliz tilida qoldi.** D39 “hozirgi wizard o‘zgarishsiz qoladi” deydi, shuning uchun faqat sahifa sarlavhasi lug‘atga o‘tkazildi. Tuzilma muharriri va qidiruv to‘liq o‘zbek tilida.

### Foydalanuvchi bajarishi kerak bo‘lgan ishlar

- **Dev bazasida kurs ma’lumoti yo‘q.** Tekshirganda `neurolearn` bazasida 0 mavzu va 1 foydalanuvchi bor. 7.1 ni brauzerda ko‘rish uchun: `venv/bin/python manage.py seed_thesis_demo` (demo akkauntlarning seed'dan tashqari javoblari bo‘lsa, buyruq `--reset-demo-answers` talab qiladi). `db.sqlite3` va `backups/` tegilmadi.
- **Skrinshotlar.** `docs/ui/README.md` dagi ketma-ketlik: Playwright o‘rnatish, backend va frontend'ni ishga tushirish, skriptni talaba va staff akkaunti bilan ikki marta ishga tushirish.
- **`npm install` kerak emas** — yangi runtime bog‘liqligi qo‘shilmadi. Playwright faqat skrinshot uchun va ixtiyoriy.
---

## 8a-bosqich hisoboti (rozilik va eksport)

Qamradi: `NEUROLEARN_B8_PLAN.md` 3-bo‘limi — D42, D43, D44, D45. Shuningdek `NEUROLEARN_REMEDIATION.md` 8-bosqichining “Rozilik” va “Eksport” bloklari, D11 ning hard-delete qismi, addendum A4-13 va 2.7/2.8 ning rozilik qismlari.

Backend commit: `dc3c35c`. Frontend commit: `3345a52`.

### Nega 8a birinchi

Bu kichik ish, lekin u haqiqiy talaba ma’lumotini yig‘ishni ochadi. Yig‘ish haftalar davom etadi va uni tezlashtirib bo‘lmaydi, shuning uchun u imkon qadar erta boshlanishi kerak. 8b esa ochiq ma’lumotlarda mahalliy ma’lumotsiz ham ishlay oladi.

### D42 — Rozilik

Uchta maydon (`accounts/migrations/0005_research_consent.py`): `research_consent` (standart `False`), `research_consent_at`, `research_pseudonym`.

- **Standart holatda yo‘q.** Rozilik faqat talabaning aniq harakati bilan beriladi: ro‘yxatdan o‘tishdagi ixtiyoriy belgi yoki profil sahifasidagi tugma. Hech bir endpoint rozilikka bog‘lanmagan — buni test ham tekshiradi (`test_consent_is_not_a_condition_of_using_the_platform`).
- **`PATCH /api/me/consent/`** (addendum A4-13) — alohida endpoint, profil tahriridan ajratilgan. Sababi aniq: rozilik — talabaning o‘z ma’lumoti haqidagi qarori, va u ismni saqlashning yon ta’siri sifatida o‘zgarishi mumkin emas. Yo‘lda id yo‘q, shuning uchun bu endpoint bilan boshqa birov nomidan rozilik berib bo‘lmaydi.
- **`research_consent_at` ikki tomonga ham qo‘yiladi.** Bekor qilish ham fakt. Ro‘yxatdan o‘tishda belgilanmasa, maydon `NULL` qoladi: “hech qachon rozilik bermagan” bilan “soat 10:04 da bekor qilgan” bir narsa emas.
- **Matn beshta gapdan iborat** (`consent.*` lug‘atda): qanday ma’lumot (javoblar va ularning vaqti), nima uchun (magistrlik dissertatsiyasi), ism va email chiqmasligi, majburiy emasligi va bekor qilish mumkinligi. Oxirgi gapda ochiq aytiladi: bekor qilish **keyingi** eksportlardan chiqaradi, allaqachon olingan fayllar o‘zgarmaydi. Backend ularni qayta yozolmaydi, shuning uchun boshqa narsa aytish yolg‘on bo‘lardi; test aynan shu satrni tekshiradi.
- **Foydalanuvchilar sahifasida** rozilik ustuni va filtri bor (addendum 2.7), lekin **faqat o‘qish uchun**: rozilikni boshqa birov nomidan belgilay oladigan administrator uni ma’nosiz qilib qo‘yadi.

### D43 — Psevdonim

`secrets.token_hex(8)` — 16 ta hex belgi, foydalanuvchi qatori yaratilganda beriladi, unique.

- **Id, email yoki ismdan hosil qilinmaydi.** Ulardan hisoblanadigan psevdonim foydalanuvchilar ro‘yxati oqib ketganda qayta hisoblanishi mumkin — bu esa psevdonim oldini olishi kerak bo‘lgan yagona narsa.
- **Hammaga beriladi**, rozilik berilgan-berilmaganidan qat’i nazar: psevdonimning o‘zi oshkor qilish emas, va keyinroq berilgan rozilik yangi identifikator talab qilmaydi.
- **Interfeysga ham, API'ga ham chiqmaydi.** `UserDetailSerializer` va rozilik serializeri uni o‘z ichiga olmaydi.
- **Migratsiya uch qadamda.** Callable default'li maydon qo‘shilganda Django uni **bir marta** hisoblab, barcha qatorlarga bir xil qiymat yozadi — unique ustun uchun bu xato, va unique bo‘lmasa ham noto‘g‘ri. Shuning uchun: ustun `null` bo‘lib keladi, `RunPython` har bir qatorga o‘zining qiymatini yozadi, keyin ustun unique va `NOT NULL` bo‘ladi. Test buni ham tekshiradi (`test_every_existing_account_got_its_own_pseudonym`).

### D11 — Hard-delete nimani bildiradi

30 kundan keyin o‘chirilayotgan hisob ikki tarmoqqa bo‘linadi (`accounts/tasks.py`):

- **Rozilik yo‘q** → qator butunlay o‘chiriladi. `AssessmentAttempt.user` CASCADE, ya’ni javoblar ham ketadi. Bu ataylab: bu ma’lumot hech qachon tadqiqot ma’lumoti bo‘lmagan.
- **Rozilik bor** → shaxs ma’lumoti olib tashlanadi, qator qoladi (`CustomUser.anonymise()`). Qatorni o‘chirish talaba ishlatishga rozi bo‘lgan javoblarni ham olib ketardi, eksport esa psevdonimdan boshqa hech narsa olib chiqmagan edi. Ya’ni bu yerda olib tashlanadigan narsa — aynan eksport allaqachon chiqarmagan narsa: email va ism. Email `anon-<psevdonim>@removed.invalid` ga aylanadi (`.invalid` — RFC 2606 bo‘yicha zahiralangan, hech qayerga yetib bormaydi), parol ishlatib bo‘lmaydigan qilinadi.

Buning o‘tkir cheti ochiq aytiladi va test bilan yozilgan: **rozilikni bekor qilib, keyin hisobni o‘chirgan talabaning javoblari o‘chiriladi** (`test_withdrawing_consent_before_deletion_removes_the_answers`). Anonimlashtirilgan qator keyingi tunda qayta ishlanmaydi.

Vazifa endi bitta son emas, ikkita qaytaradi (`{"anonymised": n, "deleted": m}`): bular turli hodisalar va umumiy son qaysi biri bo‘lganini yashiradi.

### D44 — Eksport qamrovi

`export_research_data` — bitta buyruq, bitta papka, to‘rtta fayl.

Qabul qilinadigan javob: `source ∈ {adaptive, test_session}`, `engine_version` `thesis_hybrid` bilan boshlanadi, foydalanuvchida `research_consent=True` va `is_simulated=False`, mavzu arxivlanmagan. Chiqarib tashlanadi: `legacy`, `seed`, `simulated`, `review_repeat`.

`--include-simulated` faqat quvurni sinash uchun: u simulyatsiya hisoblarini roziligidan qat’i nazar kiritadi, buyruq ogohlantirish chop etadi, `metadata.json` da `thesis_result: false` turadi va papka nomiga `-simulated` qo‘shiladi. D13 bo‘yicha bunday natija dissertatsiya natijasi emas, shuning uchun uni fayl nomidan ham adashtirib bo‘lmaydi.

Fayllar:

| Fayl | Nima bor |
|---|---|
| `pykt_sequences.txt` | Har bir talaba uchun besh satr: `psevdonim,uzunlik` / savol id'lari / tushuncha id'lari / javoblar (0/1) / vaqtlar (ms). Bu modelda tushuncha — mavzu, shuning uchun “concepts” mavzu id'lari |
| `attempts.csv` | Ledger ustunlari: p̂, P(G), P(S), P(L) oldin→keyin, θ oldin→keyin, b oldin→keyin, `attempt_no`, `readiness_score`, `was_ready`, manba, versiyalar. Qiymatlar ledger'dan, qayta hisoblanmaydi |
| `knowledge_base.json` | Daraxt (`kind`, `parent`, `position`, `pos`, `depth`, `lev`), E_P (ω bilan), G_L (`inherited`, `via`) |
| `metadata.json` | Eksport sanasi, filtrlar, qatorlar va talabalar soni, rozilik bermagani uchun chiqarib tashlanganlar soni, `kb_version`, `engine_version`, kod commit'i, identifikator izohi, pyKT fayl shartnomasi |

**Fayllarda faqat psevdonim.** Ichki `user_id` ham yo‘q: u bazadagi har bir jadval bilan bog‘lanadi, ya’ni uni chiqarish psevdonimni bekor qiladi.

`metadata.json` — dissertatsiyada “natijalar qaysi ma’lumotdan olingan” degan savolga javob beradigan fayl, shuning uchun u filtrlarni ham, sonlarni ham, versiyalarni ham, commit'ni ham yozadi.

### D45 — Nazorat

- `--dry-run` faqat sonlarni chop etadi va hech narsa yozmaydi.
- Eksport qilingan talabalar soni va rozilik bermagani uchun chiqarib tashlanganlar soni **alohida** ko‘rsatiladi. Ikkalasi bir xil bazaga nisbatan o‘lchanadi: rozilikdan boshqa barcha filtrlardan o‘tgan javoblar.
- Bo‘sh eksport bo‘sh papka emas, xato: `--dry-run` bilan sonlarni ko‘rish taklif qilinadi.
- `exports/` `.gitignore` ga qo‘shildi — tadqiqot ma’lumoti commit qilinmaydi.

### Testlar

Backend, 33 yangi test:

- `accounts/tests/test_research_consent.py` (19) — rozilik standart holatda yo‘qligi; ro‘yxatdan o‘tish belgi bilan va belgisiz; endpoint orqali berish va bekor qilish, `research_consent_at` ikki tomonga; psevdonim API'ga chiqmasligi; boshqa hisobga rozilik qo‘yib bo‘lmasligi; profil tahriri rozilikni o‘zgartirmasligi; rozilik majburiy emasligi; anonimga 401; admin uchun rozilik filtri; psevdonimning shakli, hosil qilinmasligi, yagonaligi va har bir mavjud qatorda borligi; D11 ning ikki tarmog‘i, retention oynasi, qayta ishlanmaslik va bekor qilgandan keyin o‘chirish.
- `assessments/tests/test_research_export.py` (14) — D45 nomlagan uchta tekshiruv (email/ism/`user_id` yo‘qligi, rozilik bermagan talaba yo‘qligi, `review_repeat` yo‘qligi); `seed`/`simulated`/`legacy` chiqarilishi; `--include-simulated` belgilanishi; arxivlangan mavzu; kurs filtri; `--dry-run`; bo‘sh eksport xatosi; to‘rtta faylning mazmuni; test sessiyasi javobi ham eksport qilinishi.

Frontend, 5 yangi test (`src/pages/Profile.consent.test.tsx`): kartadagi to‘rt fakt va bekor qilish haqidagi gap; rozilik berish va bekor qilish tugmalari; sana; psevdonim ko‘rsatilmasligi; rozilik o‘qilmaganda profilning qolgan qismi ishlashi.

### Natijalar

| Tekshiruv | Natija |
|---|---|
| Backend: `venv/bin/pytest` | **789 passed**, 13 subtests (7.1 da 756) |
| Backend: `manage.py check` | 0 issues |
| Backend: `manage.py makemigrations --check --dry-run` | No changes detected (migratsiya `0005_research_consent`) |
| `pytest --ds=verification.settings verification/tests` | **683 passed, 11 failed** — 7.1 da 684/10. Yangi FAIL: `test_na_group_e_experiments_and_consent_are_not_implemented` |
| Frontend: `npx tsc --noEmit` | **0 xato** |
| Frontend: `npx eslint .` | **0 error**, 8 warning (o‘zgarmadi) |
| Frontend: `npm test` | **90 passed** (14 fayl; 7.1 da 85/13) |
| Frontend: `npm run build` | o‘tdi |
| `manage.py export_research_data --dry-run` | sonlarni chop etadi, hech narsa yozmaydi |

Tekshiruvdagi yangi FAIL — harnessning o‘z signali, nosozlik emas. `test_na.py` 5-qoida bo‘yicha yozilgan: bosqich qo‘lga tushganda N/A testi ataylab buziladi va bu “endi shu guruh uchun haqiqiy tekshiruv yozilishi kerak” degani. E guruhi rozilik (8a) va eksperimentlarni (8b) birga qamraydi, shuning uchun u 8b bilan birga yoziladi. Qolgan 10 ta FAIL 7.1 dagi bilan bir xil.

### Ataylab qilingan tanlovlar

- **Rozilik uchun alohida endpoint.** Profil tahririga qo‘shish osonroq bo‘lardi, lekin unda rozilik ismni saqlashning yon ta’siri bo‘lib qolardi. Test shu yo‘lni yopadi.
- **Psevdonim hammaga, yaratilishda beriladi.** Faqat rozilik berganlarga berish mantiqli ko‘rinadi, lekin unda psevdonim mavjudligining o‘zi rozilik belgisi bo‘lib qolardi, va keyinroq berilgan rozilik yangi identifikator talab qilardi.
- **Psevdonim API'ga chiqmaydi.** Shaffoflik uchun uni talabaga ko‘rsatish mumkin edi, lekin unda talaba o‘zini eksport qatori bilan bog‘lay oladi — va bu bog‘lanishni boshqa birov bilan ulashishi ham mumkin.
- **Anonimlashtirish, o‘chirish emas (rozilik bo‘lganda).** Qatorni o‘chirish javoblarni ham olib ketardi. Shu bilan birga, rozilikni bekor qilish o‘chirishga yo‘l ochadi — bu ataylab va matnda aytilgan.
- **Rozilik ustuni admin uchun faqat o‘qish.** Boshqa birov nomidan belgilanadigan rozilik — rozilik emas.
- **pyKT formati aniq yozilgan va metadata'da hujjatlashtirilgan.** Fayl shartnomasi (besh satr, nima qayerda) `metadata.json` da turadi va 8b dagi yuklovchi uni o‘rnatilgan `pykt-toolkit` versiyasiga nisbatan tekshiradi. Bu yerda taxmin qilib qo‘yish emas, shartnomani yozib qo‘yish tanlandi.
- **Auth sahifasi lug‘atga ulandi.** `auth.*` kalitlari 7-bosqichda yozilgan edi, lekin sahifa ularni ishlatmagan. Rozilik matni o‘zbek tilida, uning atrofidagi forma ingliz tilida bo‘lishi mantiqsiz bo‘lardi, shuning uchun 15 ga yaqin satr mavjud kalitlarga ulandi. Bu D42 ning harfidan tashqari kichik qo‘shimcha.

### Bajarilmagani

- **Addendum 2.8 ning qolgan ikki bandi** — hisobni o‘chirish va parolni almashtirish. Ular D42–D45 ga kirmaydi, shuning uchun qilinmadi. Hisobni o‘chirish uchun backend allaqachon bor (`DELETE /api/accounts/profile/`), interfeys yo‘q.
- **pyKT formatining pyKT kutubxonasiga nisbatan tekshirilishi** — 8b dagi yuklovchining ishi, chunki u o‘rnatilgan versiyaga bog‘liq. Hozir shartnoma `metadata.json` da yozilgan.
- **Haqiqiy eksport olinmadi.** Dev bazasida rozilik bergan talaba va javoblar yo‘q; buyruq `--dry-run` bilan 0/0 qaytaradi, bu to‘g‘ri.

### Foydalanuvchi bajarishi kerak bo‘lgan ishlar

- **Migratsiya.** `venv/bin/python manage.py migrate accounts` — `0005_research_consent` mavjud hisoblarga psevdonim beradi. Ishga tushirildi: dev bazasida qo‘llandi.
- **Ma’lumot yig‘ishni boshlash.** Rozilik oqimi tayyor. Talabalar ro‘yxatdan o‘tganda yoki profil sahifasida rozilik berishlari kerak; `GET /api/accounts/users/?consent=true` kimlar bergani ko‘rsatadi.
- **Eksport.** `venv/bin/python manage.py export_research_data --dry-run` sonlarni ko‘rsatadi, keyin bayroqsiz ishga tushirilsa `exports/research-<sana>/` ga yoziladi. Bu papka gitignored.
---

## D46 hisoboti (rozilik matniga oltinchi fakt)

Frontend commit: `5251c45`.

D11 bo‘yicha rozilik bergan talaba hisobini o‘chirsa, javoblari psevdonim bilan, ism va emailsiz saqlanib qoladi. Siyosat to‘g‘ri va o‘zgarmadi. Lekin rozilik matni buni aytmasdi, ya’ni “hisobimni o‘chirsam hammasi o‘chadi” degan taxmin to‘liq asosli bo‘lib qolardi — va bu aynan rozilik matni qoldirmasligi kerak bo‘lgan yagona taxmin.

Shuning uchun kartaga va ro‘yxatdan o‘tish blokiga oltinchi fakt qo‘shildi: javoblar tadqiqot uchun ism va emailsiz saqlanadi, buni istamaslik yo‘li — avval rozilikni bekor qilish. Ikki tilda; qolgan besh satrni ushlab turgan test shu satrni ham tekshiradi.

---

## 8b-1 hisoboti (yuklovchilar va graf tahlili)

Qamradi: `NEUROLEARN_B8B.md` — D48, D49, D50, D51, D52.

Backend commit: `c1a683b`.

### D48 — bu bosqichning asosiy qoidasi

`tables.md` faqat `metrics.json` dan yasaladi. Bu niyat emas, kod: `experiments/tables.py` dagi `verify()` markdown'dagi har bir raqamli tokenni oladi va uning `metrics.json` da skalyar sifatida borligini talab qiladi. Metrics'dagi satrlar (yo‘llar, hash'lar, buyruq, nomlar) skanerdan oldin olib tashlanadi, shuning uchun sha256 ichidagi raqamlar “qo‘lda yozilgan son” bo‘lib ko‘rinmaydi.

Prozadagi yagona ruxsat — uchta havola: `2.2`, `2.3`, `3.3`. Ular `CITATIONS` to‘plamida ochiq e’lon qilingan va **test uning tarkibini qotiradi**: ro‘yxat o‘sса test buziladi. Ya’ni natija sonini ro‘yxatga qo‘shib jadvalga kiritib bo‘lmaydi.

Yana uch qoida kod bilan majburlanadi:

- **Manbasiz natija yozilmaydi.** `status=ok` bo‘lgan har bir yozuvda `source.sha256` bo‘lishi shart, aks holda `require_sources()` rad etadi.
- **Avval tekshiriladi, keyin yoziladi.** `tables.write()` markdown'ni yasaydi, `verify` qiladi va faqat natija toza bo‘lsa papka yaratadi. Ya’ni yomon ishga tushirish yarim natija qoldirmaydi.
- **Ma’lumoti yo‘q to‘plam — gap, son emas.** Qator “ishga tushirilmagan — ma’ulumot yo‘q” deb chiqadi, o‘lcham ham, hash ham, vaqt ham bo‘lmaydi.

Test bu tekshiruvning **buzila olishini** ham tasdiqlaydi: jadvalga `0.863` qo‘shilsa yoki mavjud son `999` ga o‘zgartirilsa, `verify` aynan shu tokenni qaytaradi. Ishga tushirishdan keyin “to‘g‘rilangan” son — bu oldini olinadigan narsa.

Har bir natija to‘rtta faktni ko‘taradi (D48): fayllarning sha256'si, kod commit'i (va ishchi daraxt toza bo‘lmaganini belgisi), seed va buyruq. Buyruq modul chaqiruvi sifatida yoziladi (`python -m experiments.graph_report …`), ya’ni natijadagi satr qayta ishga tushirish uchun yaroqli. `NEUROLEARN_DATA` o‘rnatilgan bo‘lsa, u ham yoziladi — buyruq satri yolg‘iz o‘zi ishga tushirishni tiklay olmaydi.

### D49 — nima bor, nima yo‘q

Hech narsa yuklab olinmaydi: har bir yuklovchi yo‘lni argument sifatida oladi. Sabab texnik emas — o‘zi qayta yuklab oladigan skript ikki ishga tushirish bir xil baytlarni ko‘rganini kafolatlay olmaydi. Buni sha256 kafolatlaydi.

`experiments/data/README.md` — `git clone` buyruqlari, kutilgan joylashuv, tekshirilgan sha256'lar va litsenziyalar. Fayllar gitignored.

Ishga tushirilgan nusxalar D49 dagi qiymatlarga mos keldi: `as.csv` sha256 `f22e3fb7…d77dbdc` (pyBKT-examples commit `fc59290`), to‘rtta graf KC4EDU commit `ac0b6e0` dan.

### D50 — ASSISTments 2009 tozalash

Tozalash qoidalari koddagi bitta joyda va ochiq. Eng muhimi ikkinchi qoidaning yarmi: takror `(order_id, skill_id)` bo‘yicha olinadi, **`order_id` yolg‘iz o‘zi bo‘yicha emas**. Aks holda bir nechta skill'li har bir savolning qolgan skill'lari jim yo‘qolardi — haqiqiy ma’lumotda bu 47 037 ta savol.

Sonlar spetsifikatsiyaning bir qismi, shuning uchun ular test emas, **yuklovchining o‘zida**: mos kelmasa `DatasetMismatch` ko‘tariladi va quvur to‘xtaydi. Haqiqiy faylda hammasi aynan mos keldi:

| | Kutilgan | Olingan |
|---|---|---|
| Xom qatorlar | 525 534 | 525 534 |
| Xom talabalar | 4 217 | 4 217 |
| Bo‘sh `skill_id` | 66 326 | 66 326 |
| Tozalangandan keyin qatorlar | 338 001 | 338 001 |
| Tozalangandan keyin talabalar | 4 163 | 4 163 |
| Skill'lar | 123 | 123 |
| Bir nechta skill'li `order_id` | 47 037 | 47 037 |
| `--original-only` qatorlar | 312 232 | 312 232 |
| `--original-only` talabalar | 4 163 | 4 163 |

Olib tashlangan takrorlar: 121 207 qator. `original` bayrog‘i qaysi variant yuklanganidan qat’i nazar ikkala variantning sonini metadata'ga yozadi (D50, 4-qoida).

Fayl UTF-8 emas, shuning uchun latin-1 bilan o‘qiladi: bu moslik baytni baytga qaytaradi va xato bermaydi, ishlatiladigan har bir ustun esa ASCII.

### D51 — graf yuklovchi va yo‘nalish

Bitta yuklovchi: GraphML yoki `src,dst` CSV. Yo‘nalish — argument, taxmin emas. Nashr etilgan graflar bir-biriga mos kelmaydi: Junyi prerekvizit → qaram, DBE-KT22 esa aralash (`DML → SELECT` umumiydan xususiyga, `ALTER TABLE → DDL` aksincha), ya’ni bu faylning **birorta ham** o‘qilishi to‘g‘ri emas. D51 ning javobi taxmin qilmaslik: `--edge-direction` ochiq, va DBE-KT22 har doim ikkala yo‘nalishda ishga tushiriladi.

GraphML standart kutubxona bilan o‘qiladi — ataylab. networkx testdagi oracle, va tekshirilayotgan kod bilan implementatsiyani bo‘lishadigan oracle hech narsani isbotlamaydi.

Yo‘lda uchragan ikki narsa jim qoldirilmadi:

- **O‘z-o‘ziga qirra — Y2 buzilishi.** Olib tashlanadi va sanaladi (Junyi 2, WDKG-Course 1).
- **Tugun nomlari bo‘sh joydan tozalanadi.** DBE-KT22 ikkita tugunni `"Total "` va `"weak entity "` deb nashr etgan; faqat orqa bo‘shliq bilan farq qiladigan yorliq ikkinchi tushunchaga o‘xshab ko‘rinadi. Tozalash to‘rtta grafda bitta ham to‘qnashuv hosil qilmaydi — WDKG-Course da bir nomni ikkita tugun ko‘taradi, lekin ular faylda ham shunday, shuning uchun bu birlashtirilmaydi, `duplicate_names` bilan **qayd etiladi**. Tugunlar tahlilda alohida qoladi; noaniq bo‘lib qolishi mumkin bo‘lgan narsa — o‘quvchi ko‘radigan qirralar ro‘yxati.

Parallel qirralar bittaga keltiriladi: `(x, y)` ikki marta yozilgani bitta munosabat. Bu networkx bilan solishtirishda ham hisobga olinadi (u parallel qirrali faylni MultiDiGraph qilib o‘qiydi).

### D52 — graf tahlili, haqiqiy graflarda

II bobning hisob-kitoblari qayta yozilmadi: tartib, `lev`, Desc\*, ortiqcha qirralar va Algoritm 2.3 — `neuro_model` dan. Ya’ni o‘lchanadigan narsa platformaning o‘zi ishlatadigan kod. II bobda ta’rifi yo‘q ikki statistika (kuchsiz va kuchli bog‘langan komponentlar) `experiments/components.py` da va networkx bilan tekshiriladi.

**Haqiqiy chiqish** (`experiments/results/graphs/20261006-052348/tables.md`, commit `c1a683b`, ishchi daraxt toza):

| Graf | Tugun | Fayldagi qirra | Qirra | O‘z-o‘ziga | Izolyatsiyalangan | DAG | Kuchsiz komp. | Ortiqcha | Eng uzun yo‘l |
|---|---|---|---|---|---|---|---|---|---|
| DBE-KT22 | 98 | 101 | 101 | 0 | 0 | ha | 8 | 9 | 5 |
| Junyi | 1004 | 740 | 738 | 2 | 73 | ha | 266 | 0 | 9 |
| WDKG-Course | 46 | 73 | 72 | 1 | 0 | ha | 3 | 12 | 6 |
| WDKG-KnowledgePoints | 121 | 285 | 285 | 0 | 87 | ha | 88 | 0 | 1 |

**D52 ning har bir ko‘rsatilgan qiymati mos keldi** — tugunlar, qirralar (fayldagi va tozalangandan keyingi), o‘z-o‘ziga qirralar, asiklik, kuchsiz komponentlar, ortiqcha qirralar, eng uzun yo‘l va Junyi'ning 73 ta izolyatsiyalangan tuguni. DBE-KT22 ning to‘qqizta ortiqcha qirrasi ham nomlari bilan aynan mos keldi (`Transactions→ACID Properties`, `Database Security→Access Control`, `Role-Based Access Control (RBAC)→Access Control`, `Entity-Relationship Model→Data Model`, `Entity-Relationship Model→Entity`, `Discretionary access control (DAC)→REVOKE`, `Discretionary access control (DAC)→Specifying Privileges - Views`, `Participation constraints→Relationship`, `Superkey→Relational data model`).

Jadval yo‘nalishga bog‘liq emas: grafni teskari aylantirish o‘lchamni, o‘z-o‘ziga qirralarni, izolyatsiyalangan tugunlarni, asiklikni, komponentlarni, ortiqcha qirralar sonini va eng uzun yo‘lni o‘zgartirmaydi. Shuning uchun DBE-KT22 ning ikki yo‘nalishi bir xil qator beradi; yo‘nalish H3 da ahamiyatli bo‘ladi, bu hisobotda emas. Buni test ham tasdiqlaydi.

**Tayyorlik yangilanishi** (D52, 30 takror):

| Graf | Namuna | Inkremental tugun (median) | To‘liq tugun | Inkremental µs (median / p95) | To‘liq µs (median / p95) | Tezlashish |
|---|---|---|---|---|---|---|
| DBE-KT22 | 50 | 1 | 98 | 0,928 / 1,614 | 39,06 / 39,985 | 42× |
| Junyi | 50 | 3 | 1004 | 1,401 / 2,059 | 396,6 / 401,2 | 283× |
| WDKG-Course | 27 | 2 | 46 | 1,11 / 2,145 | 19,8 / 20,07 | 18× |
| WDKG-KnowledgePoints | 19 | 15 | 121 | 3,647 / 3,77 | 51,99 / 52,72 | 14× |

Namuna tasodifiy emas: eng ko‘p vorisi bor tugunlar olinadi, ya’ni inkremental yo‘l uchun eng yomon holat. Tasodifiy tanlov ko‘pincha umuman vorisi yo‘q tugunni o‘lchardi. Tanlov deterministik.

Vaqtlar mashinaga bog‘liq, shuning uchun **testda tasdiqlanmaydi**. Tasdiqlanadigan narsa — inkremental yo‘l `|Succ(v)|` tugunni ko‘radi va bu to‘liq qayta hisoblashdan kichik yoki teng.

**Y3 tarmog‘i** (sikl topilsa SCC'lar birlashtiriladi) to‘rtta nashr etilgan grafda ishga tushmaydi — hammasi asiklik. Shuning uchun u sintetik fixture bilan test qilinadi: `b ⇄ c ⇄ d` komponenti birlashtiriladi, kondensatsiya tartiblanadi va natija metadata'ga yoziladi.

### Testlar

49 ta test (ma’lumot bilan), 40 passed + 9 skipped (ma’lumotsiz). Haqiqiy ma’lumot testlari **skip** qiladi, jim o‘tmaydi — ma’lumotsiz checkout'da ham suite yashil bo‘lishi kerak, ma’lumot bor bo‘lsa esa spetsifikatsiya aynan tiklanishi kerak.

| Fayl | Nima tekshiradi |
|---|---|
| `test_tables.py` (14) | D48: jadvaldagi har bir son metrics'dan; tekshiruvning buzila olishi; tahrirlangan natija ushlanishi; `CITATIONS` tarkibi qotirilgani; manbasiz natija rad etilishi; yozishdan oldin tekshirilishi; ma’lumoti yo‘q qator; to‘rtta faktning faylga yetishi; formatlash |
| `test_graphs.py` (10) | D51: nomlar va qirralar fayl tartibida; o‘z-o‘ziga qirra olib tashlanishi va sanalishi; yo‘nalish bayrog‘i; CSV shakli; noto‘g‘ri sarlavha va yo‘nalish rad etilishi; parser networkx bilan mos (fixture va haqiqiy fayllar); nom tozalash va to‘qnashuvning qayd etilishi |
| `test_graph_report.py` (12) | D52: statistika networkx bilan mos (fixture va haqiqiy); nashr etilgan graflarning D52 jadvaliga mosligi; DBE-KT22 ning to‘qqiz qirrasi; jadval yo‘nalishga bog‘liq emasligi; sikl tarmog‘i; komponent yordamchilari; inkremental va to‘liq yo‘lning tugunlar soni; qirrasiz graf; ma’lumoti yo‘q graf; manba hash'i; ikki yo‘nalish |
| `test_assist09.py` (13) | D50: to‘rtta qoidaning har biri sintetik fixture'da; sonlar; boshqa fayl quvurni to‘xtatishi; yo‘q ustun va noto‘g‘ri `correct`; yo‘q fayl; haqiqiy faylning D50 sonlari va sha256; bir nechta skill'li savollarning saqlanishi |

Fixture'lar `experiments/tests/fixtures/` da, hammasi sintetik va README'da shunday yozilgan. Ular ikkita yo‘lni qoplaydi: hech bir nashr etilgan graf siklik emas, va D50 ning to‘rt holati 500 ming qatorda emas, sakkiz qatorda ko‘rinadi.

### Natijalar

| Tekshiruv | Natija |
|---|---|
| Backend: `venv/bin/pytest` | **829 passed**, 9 skipped, 13 subtests (8a da 789) |
| Backend: `pytest experiments/tests` (haqiqiy ma’lumot bilan) | **49 passed** |
| Backend: `manage.py check` | 0 issues |
| `pytest --ds=verification.settings verification/tests` | 683 passed, 11 failed — 8a dagi bilan bir xil |
| `python -m experiments.graph_report` | D52 jadvalining haqiqiy chiqishi, yuqorida |

### Ataylab qilingan tanlovlar

- **GraphML standart kutubxona bilan o‘qiladi.** networkx bilan o‘qish osonroq bo‘lardi, lekin unda oracle va kod bir xil parserni bo‘lishardi.
- **networkx `requirements-dev.txt` ga e’lon qilindi.** U avval ham o‘rnatilgan edi, lekin tranzitiv bog‘liqlik sifatida — hech kim nomini aytmagan test bog‘liqligi versiya yangilanishida yo‘qolishi mumkin.
- **D50 sonlari testda emas, yuklovchida.** “Quvur to‘xtaydi” degan talab testda bo‘lsa, quvur ishga tushishda emas, CI'da to‘xtaydi.
- **Fayldagi qirra va tozalangan qirra alohida ustun.** D52 “740 (+2 o‘z-o‘ziga)” deb yozadi; ikki ustun bu yozuvni ikkiga ajratadi, ya’ni jadvalni o‘qiyotgan odam ayirishni o‘zi qilmaydi.
- **Namuna eng ko‘p vorisli tugunlar.** Tasodifiy tanlov inkremental yo‘lni haqiqiydan yaxshi ko‘rsatardi.
- **Natijalar repoga qo‘shiladi, ma’lumot qo‘shilmaydi.** `tables.md` va `metrics.json` — dissektasiyaning dalili; ma’lumot fayllari litsenziya va hajm masalasi.
- **`experiments/requirements.txt` hozir ishlatilmaydi.** 8b-1 standart kutubxona va `neuro_model` ustida ishlaydi; pandas, pyKT va torch 8b-2 dan boshlab kerak va alohida virtualenv'da o‘rnatiladi.

### Bajarilmagani (ataylab)

- **D47 — tekshiruv to‘plamini tozalash.** Bu ish B8B planida ochiq ravishda implementatorning emas, mustaqil tekshiruvchining ishi (alohida sessiya). `verification/` ga tegilmadi.
- **D53 (H2), H1/H3, DBE yuklovchisi, annotatsiya vositasi** — 8b-2 va 8b-3.

### Foydalanuvchi bajarishi kerak bo‘lgan ishlar

- **Ma’lumotni joylashtirish.** `experiments/data/README.md` dagi ikki `git clone` buyrug‘i. Men ularni tekshirish uchun scratchpad'ga oldim; repoda yo‘q.
- **`pip install -r requirements-dev.txt`** — `networkx==3.4.2` e’lon qilindi (allaqachon o‘rnatilgan bo‘lishi mumkin).
- **8b-2 uchun alohida virtualenv** — `experiments/requirements.txt` (torch va pykt-toolkit katta, Django tomoniga keraksiz).
---

## 8b-2: H2 ishga tushirishi yiqildi — sabab va tuzatish (D54)

**Nima bo‘ldi.** `1eeca40` dan `experiments/run_h2.sh both` bilan boshlangan ishga tushirish 2026-10-06 15:48:57 da to‘xtagan: `h2-quick.log` `--quick` ning 2-qismida, AKT o‘qitilayotganda tugaydi, “finished” qatori yo‘q, `full` umuman boshlanmagan, `experiments/results/assist09*/` yo‘q.

**Sabab** (`journalctl -k`): global OOM. Kernel OOM-killer `python` ni o‘ldirgan (anon-rss ≈ 3 GB — AKT ning bitta batch'idagi attention tensorlari; ma’lumot hajmiga emas, batch'ga bog‘liq). Ikki narsa buni yiqilishga aylantirdi:

- `setsid` jarayonni ishga tushirgan ilovaning cgroup'idan chiqarmaydi. Run browser'ning scope'ida (`app-org.chromium.Chromium-….scope`) qolgan va uning `oom_score_adj = 200` ini meros qilgan — ya’ni birinchi qurbon.
- OOM'dan keyin systemd butun scope'ni yopgan (`Failed with result 'oom-kill'`), bash o‘rami ham birga o‘lgan — shuning uchun logda chiqish holati yo‘q.

Ya’ni xato kodning xotirasida emas, ishga tushirish usulida. Model, batch yoki boshqa parametr o‘zgartirilmadi.

**Tuzatish.**

- `run_h2.sh` endi `systemd-run --user` bilan alohida transient unit'da ishga tushadi: o‘z cgroup'i, `OOMScoreAdjust=100` (foydalanuvchi menejerining eng past ruxsat etilgan qiymati), `OOMPolicy=continue` — python o‘ldirilsa ham o‘ram tirik qoladi va `finished (exit 137)` ni yozadi. User systemd bo‘lmasa, `setsid` ga qaytadi va buni ochiq aytadi.
- **D54 — provenance boshida ham, oxirida ham.** `GitState`: commit, dirty va `git status --porcelain` qatorlari (nima dirty ekani ham). `Provenance.capture(git_start=…)` oxirgi holatni o‘zi oladi. Hisobotdagi commit — **boshlang‘ich** (ishlagan kod shu). Boshida dirty bo‘lsa yoki boshi va oxiri farq qilsa: `metrics.json` da `tree_warnings`, `env.txt` da `WARNING`, `tables.md` ning **eng yuqorisida** “Ogohlantirish (D54)” bloki va manba bo‘limida ikki holat qatorlari bilan. `h2.py` va `graph_report.py` ikkalasi ham boshlang‘ich holatni ish boshlanishidan oldin oladi.
- Testlar (`experiments/tests/test_provenance.py`, 19): toza / kuzatilmagan fayl / o‘zgartirilgan fayl / repo tashqarisi; toza run, boshida dirty, davomida o‘zgargan, davomida commit qilingan (commit boshlang‘ichi qoladi), ikkala ogohlantirish; `tables.md` ning har bir shartli bloki (ogohlantirish yo‘q / boshida dirty / o‘zgargan / holat noma’lum / D54 dan oldingi natija) — har birida `verify == []`; graf hisobotida ham ogohlantirish; launcher: SIGKILL bilan o‘ldirilgan python → `exit 137` yoziladi va `full` boshlanmaydi; muvaffaqiyatli `quick` dan keyin `full`.

**Qayta ishga tushirish** shu tuzatish commit'idan. Ishchi daraxtda bitta kuzatilmagan fayl bor — `NEUROLEARN_NEXT.md` (foydalanuvchining prompt fayli; D54 bo‘yicha boshqa birovning commit qilinmagan fayliga tegilmaydi). Shuning uchun natija “boshida toza emas” deb belgilanadi va `?? NEUROLEARN_NEXT.md` qatori ko‘rsatiladi — bu yashirilmaydi.

---

## Tekshiruv topilmalari R1–R3, K1–K2 (tuzatish)

Manba: `VERIFICATION_REPORT.md` 5-bo‘limi (tekshiruv commit'i `59663e2`). Alohida kichik commit, D55 dan oldin. `verification/` ga tegilmadi — uning testlari mezon. Modelning sonlari o‘zgarmaydi, hech bir natija qayta hisoblanmadi.

**Ishga tushirish holati (tuzatishdan oldin tekshirildi).** `systemctl --user list-units --all 'neurolearn-*'` — 0 unit, `experiments.h2` jarayoni yo‘q. `005f30d` dan boshlangan `run_h2.sh both` ning `--quick` qismi tugagan (`experiments/results/assist09-quick/20261006-112922/`, `418e41d` da commit qilingan). **To‘liq qism tugamagan**: `h2-full.log` 1-fold'ning DKT qatorida (16:53) uziladi, “finished” qatori yo‘q, `experiments/results/assist09/` yo‘q. `journalctl --user`: 16:55:01 da Chrome scope'i OOM bilan yopilgan, 16:55:56 da foydalanuvchining systemd menejeri `neurolearn-h2-both-20261006-160748.service` ni **to‘xtatgan** (“Stopping … Stopped”, sessiya yopilishi bilan birga) — OOM-killer python'ni emas, sessiya unit'ni to‘xtatgan, shuning uchun `OOMPolicy=continue` ham yordam bermagan va chiqish holati yozilmagan. Ya’ni `005f30d` ga bog‘langan to‘liq H2 natijasi **mavjud emas**; qayta ishga tushirish bu commit'ning ishi emas.

### R1 — `--include-simulated` simulyator javoblarini chiqarmasdi

Simulyator har bir javobni `source=simulated` bilan yozadi, eksport esa simulyatsiya hisoblarini ham `source IN (adaptive, test_session)` filtri orqali olardi — bayroq simulyator ma’lumotida 0 qator berardi.

- `SIMULATED_ACCOUNT_SOURCES = EXPERIMENT_SOURCES ∪ {simulated}` — faqat `is_simulated=True` hisoblar uchun va faqat bayroq bilan. Haqiqiy hisobning `simulated` qatori bayroq bilan ham chiqmaydi; bayroqsiz hech qanday `simulated` qator chiqmaydi.
- `metadata.filters.sources_simulated_accounts` (faqat bayroq bilan) va konsoldagi “Source 'simulated' is exported for simulator accounts only.”
- Implementatorning `test_include_simulated_is_marked_as_not_a_thesis_result` testi aynan nuqsonni talab qilardi (“the simulator's own source is never exported”) — yangi xatti-harakatga moslandi, docstring'da sababi. Yangi test: `test_include_simulated_never_exports_a_real_accounts_simulated_rows`.

### R2 — `--out` bilan papka nomida belgi yo‘q edi

`directory()`: `--include-simulated` bilan `--out X` → `X-simulated` (nom allaqachon `-simulated` bilan tugasa — o‘zgarmaydi). Konsolda ogohlantirish: “--out X is written as X-simulated”. Uch belgi — ogohlantirish, `thesis_result: false`, papka nomi — endi har doim.

**Mezonlar o‘rtasidagi ziddiyat (tekshiruvchiga).** `verification/tests/test_e_consent_export.py::test_v_e2_include_simulated_exports_what_the_simulator_wrote` eksportni `tmp/sim` ga yo‘naltiradi va `tmp/sim/attempts.csv` ni o‘qiydi, ya’ni `--out` so‘zma-so‘z olinadi deb hisoblaydi — R2 ning mezoni (`…with_an_explicit_out_still_marks_the_directory`) esa aynan buni taqiqlaydi. Ikkalasi bir vaqtda o‘tolmaydi. `verification/` ga tegilmadi; R1 shu testning mantiqi bilan, `tmp/sim-simulated/attempts.csv` ni o‘qiydigan scratch nusxa orqali tasdiqlandi (simulyator qatori bor, haqiqiy hisobning `simulated` qatori yo‘q, `tmp/sim` yaratilmagan) va R1 ning ikkinchi mezoni (`…on_simulator_only_data_is_not_empty`, 3/3) o‘tadi. Testni tuzatish — tekshiruvchining ishi.

### R3 — o‘qitishda yo‘q skill DKT/AKT ga 0-skill sifatida kirardi

`neural._SequenceModel._windows`: skill'i o‘qitishda bo‘lmagan qator ketma-ketlikka kiritilmaydi — model uni bashorat qilmaydi, keyingi javoblar tarixida ham turmaydi; `predict` uni base rate'da qoldiradi. Avval `max(0, -1)` uni birinchi o‘qitish skill'i qilib berardi (`neural.py` dagi izohga zid). Soni `unseen_rows` sifatida qayd etiladi va `h2.run_fold` uni model yozuviga qo‘shadi (`cold_rows` dan alohida: sabab boshqa). `fit` da hamma skill ma’lum, o‘qitish o‘zgarmaydi.

**Tuzatishdan oldingi kod bilan olingan natijalar:** `experiments/results/assist09-quick/20261006-112922/` (`005f30d`) — 53 652 test qatordan **29** tasi ta’sirlangan (0,054 %). `005f30d` dagi to‘liq ishga tushirish tugaganida **10 / 338 001** qator ta’sirlangan bo‘lardi (5 fold, seed 20261006; o‘lchov tekshiruv hisobotida) — lekin u tugamagan (yuqoriga qarang). Natijalar qayta hisoblanmadi.

Yangi test: `test_models.py::test_a_skill_absent_from_training_is_left_out_of_the_sequence` (DKT, AKT).

### K1 — H2 jadvallari uchun pozitsion tekshiruv

“Son `metrics.json` ning qaysidir joyida bormi” AUC uchun zaif: `--quick` natijasida 0.650–0.759 dagi 110 ta uch xonali qiymatdan 95 tasi metrics'da bor, ya’ni BKT AUC'ini boshqa modelnikiga almashtirish o‘tib ketardi. `tables.verify_h2_positions` (`verify` ichida, `report == "h2"` bo‘lsa) markdown'ni qayta o‘qiydi — renderer'ni chaqirmaydi — va §1 (pooled), §2 (dastlabki k), §3 (juftliklar), §4 (fold'lar), §5 (aqlga muvofiqlik qatorlari), §6 (grid), §7 (pyBKT) ning har bir katagini o‘z (model, ko‘rsatkich) kaliti bilan solishtiradi; tushib qolgan yoki ortiqcha model qatori ham xato. `tables.write` uni ham talab qiladi — noto‘g‘ri joylashgan katakli jadval yozilmaydi.

Yo‘l-yo‘lakay: metrics'da yo‘q RMSE/aniqlik/javoblar soni, `cold_rows` va grid hisoblari endi “—” bo‘lib chiqadi, `0` emas (avval `fmt(x.get(..., 0))` — ishga tushirish bermagan son). Haqiqiy natijalarda bu qiymatlar doim bor, shuning uchun mavjud `tables.md` lar o‘zgarmaydi: ikkala chop etilgan natija (graflar, H2 `--quick`) yangi `verify` dan `[]` bilan o‘tadi.

Testlar: `test_a_cell_holding_another_keys_number_is_caught` (har bir bo‘lim uchun, 8 ta almashtirish — har birini oddiy skaner o‘tkazib yuboradi), `test_a_dropped_model_row_is_caught`, `test_a_missing_value_is_a_dash_not_a_zero`, `test_writing_an_h2_table_with_a_misplaced_cell_is_refused`, `test_the_published_results_verify_cell_by_cell`.

### K2 — `CITATIONS` — son emas, ibora

8b-1 hisobotida “uchta havola, test qotiradi” deyilgan, lekin to‘plam qarorsiz beshtaga o‘sgan edi (`2.4`, `2016`). Endi `CITATIONS` — ibora → qaror: `"3.3-bo‘limga": D52`, `"Algoritm 2.3": D52`, `"EDM 2016": D53` (`MappingProxyType`, o‘zgarmas). `verify` iboralarni skanerdan oldin olib tashlaydi; ibora tashqarisidagi `2016` yoki `3.3` — begona son. `2.2` va `2.4` olib tashlandi: generatsiya qilingan prozada ishlatilmaydi. Test mappingni qotiradi va har bir qaror `NEUROLEARN_B8B.md` da `### Dnn` sarlavhasi sifatida borligini tekshiradi — yangi ibora uchun yangi D-qaror shart.

### Natijalar

| Tekshiruv | Natija |
|---|---|
| Backend: `venv/bin/pytest` | **912 passed**, 10 skipped, 13 subtests |
| `experiments/.venv/bin/python -m pytest experiments/tests` | **144 passed**, 1 skipped (Django tomoni) |
| `manage.py check` / `makemigrations --check` | 0 issues / No changes detected |
| `verification/tests` | 731 passed, **8 failed**, 1 skipped — 7 ta na-signal (A, C, D, G guruhlari) va R1/R2 ziddiyatidagi test (yuqorida). R1 (`…on_simulator_only_data_is_not_empty`), R2 (`…explicit_out…`), K1 (`test_d48_h2_tables_show_each_models_own_numbers`) — o‘tadi |
| `verification/neural` (`experiments/.venv`) | **15 passed** (R3 ning ikki testi ham) |

---

## Muhit tiklanishi (Ubuntu 26.04) va ikki uzilishning sababi — 2026-10-08

Kompyuterga Ubuntu 26.04 qayta o‘rnatildi. `/var/log/installer` bo‘yicha bu yangilash emas, toza o‘rnatish (2026-10-07 11:52–12:07). Repo saqlangan, muhit va tizim loglari yo‘qolgan.

### A1 — fayl rejimlari

Backend'da 251 ta, frontend'da 167 ta fayl `100644 → 100755` bo‘lgan. `git diff --numstat` bo‘yicha mazmun farqi 0 qator. Frontend'dagi yagona binar fayl `public/image.png` ning blob hash'i HEAD bilan bir xil (`1983e535…`). Har bir faylga eski rejim `chmod 644` bilan qaytarildi, ro‘yxat `git diff --raw` dan olindi. `core.fileMode` ga tegilmadi. Ikkala repoda `git status` toza.

### A2–A3 — Python 3.12.3 va lock fayllar

Tizimda faqat Python 3.14.4 bor. numpy 1.26.4, scipy 1.14.1, scikit-learn 1.6.1 va torch 2.5.1 ning 3.14 uchun wheel'i yo‘q, pyBKT esa numpy < 2 ni talab qiladi. Shuning uchun natijalar olingan interpretator — CPython 3.12.3 — uv bilan olindi (`~/.local/share/uv/python`). uv tizimda o‘rnatilmagan ekan, u scratchpad'dagi vaqtinchalik venv'ga o‘rnatildi. Ikkala venv shu interpretator bilan qayta yaratildi, 3.14 dagi `venv/` ning `pip freeze` i o‘chirishdan oldin saqlandi. Paket versiyalari o‘zgartirilmadi. Yagona istisno: `experiments/.venv` da networkx'ni torch versiyasiz tortgan (3.6.1). U `requirements-dev.txt` dagi e’lon qilingan 3.4.2 ga tushirildi; faqat test oracle'i sifatida ishlatiladi. `505ff0c`: `.python-version`, `requirements.lock`, `experiments/requirements.lock` (sha256 hash'lari bilan; toza venv'ga `--require-hashes` bilan o‘rnatilib, freeze bilan solishtirilgan) va `experiments/README.md` dagi “Muhitni tiklash” bo‘limi.

### A4 — ma’lumot fayllari

`as.csv` va to‘rtta graf fayli (DBE-KT22, Junyi, WDKG-Course, WDKG-KnowledgePoints) — sha256 qayd qilingan qiymatlarga (D49, `experiments/results/graphs/20261006-052348/metrics.json`) mos.

### B — ikki uzilish

Dalillar:

| Log | Oxirgi yozuv (mtime) | Oxirgi qator | “finished” |
|---|---|---|---|
| `h2-full.log` (`005f30d`) | 2026-10-06 16:53:40 | 1-fold, `DKT auc=0.8220` | yo‘q |
| `h2-bounds-quick.log` (`944681d`) | 2026-10-06 22:55:40 | `fitted kengroq / fold 2 in 317s` (15 tadan 8-fit) | yo‘q |

- `last` buyrug‘i o‘rnatilmagan. `/var/log/wtmp` 2026-10-07 12:08 dan boshlanadi (4 ta login yozuvi). `journalctl --list-boots` ham 2026-10-07 12:08 dan boshlanadi.
- `/var/log/kern.log` va `syslog` 2026-10-07 12:08 dan boshlanadi, rotatsiya qilingan fayllar yo‘q. Ulardagi `OOM killer disabled/enabled` qatorlari suspend/resume belgilari, o‘ldirish emas; `Killed process` qatori yo‘q.
- `loginctl show-user zokhidjon -p Linger` → `Linger=no`.

Xulosa:

- **`h2-full` — sessiya yopilishi.** Birlamchi dalil (journal) yo‘qolgan. Ikkilamchi dalil — o‘sha paytda journal'dan yozib olingan qayd (yuqorida, “Tekshiruv topilmalari R1–R3” bo‘limi): 16:55:01 da Chrome scope'i OOM bilan yopilgan, 16:55:56 da foydalanuvchining systemd menejeri unit'ni sessiya bilan birga to‘xtatgan. Linger o‘chiq bo‘lsa, user unit sessiya tugashi bilan to‘xtaydi. OOM python'ni o‘ldirgani isbotlanmagan.
- **`h2-bounds-quick` — aniqlanmadi.** O‘ram ham “finished” yozmagan, ya’ni unit to‘xtatilgan yoki mashina o‘chgan. Lekin 2026-10-06 ga oid hech qanday tizim logi qolmagan. Repo ichida 22:55:40 dan keyin o‘zgargan fayl yo‘q, ammo uy papkasi faqat qisman tiklangani uchun bu dalil emas.

Keyingi ishga tushirishlar uchun sabab logning o‘zida qoladi: `run_h2.sh` har 60 soniyada xotira qatorini, `ExecStopPost` esa unit qanday tugaganini yozadi (C2).

### D55 ketma-ketligi

D55 to‘liq H2 natijasidan oldin commit qilingan (ketma-ketlikdan chetga chiqish), tarix o‘zgartirilmagan. `944681d` `neuro_model/` va `config/settings.py` ga tegmagan (`git diff 005f30d HEAD -- neuro_model config/settings.py` bo‘sh). `test_the_platforms_constants_do_not_move` `CONSTANTS` ni (0,30; 0,10) da qotiradi. “Parametr berilmaganda natija `944681d` dan oldingi kod bilan bitma-bit bir xil” degan test yo‘q: `test_the_main_setting_reproduces_h2s_bkt_and_bkt_irt` HEAD dagi ikki yo‘lni o‘zaro solishtiradi. Bu dalil eski `--quick` natijasini qayta tiklash orqali olinadi (C4).

---

## D57 — masala darajasidagi baholash protokoli (2026-10-08, natijadan oldin)

### To‘xtatilgan run

`13edf82` dan boshlangan to‘liq H2 run (`neurolearn-h2-full-20261008-193717`) 2026-10-08 20:00:00 da `systemctl --user stop` bilan to‘xtatildi (`ExecStopPost`: `SERVICE_RESULT=success EXIT_CODE=killed EXIT_STATUS=TERM; Result=success ExecMainStatus=15`). **D57 sababli to‘xtatildi, qisman natijalar ishlatilmaydi.** Qisman sonlar dalil sifatida qoladi (`experiments/.runs/h2-full.log`, 1-fold, `005f30d` dagi run bilan bir xil):

| Model | AUC (1-fold, `005f30d`) | AUC (1-fold, `13edf82`) |
|---|---|---|
| BKT | 0.7116 | 0.7116 |
| BKT+IRT (λ=0) | 0.7292 | 0.7292 |
| Elo/Rasch | 0.7784 | 0.7784 |
| PFA | 0.7106 | 0.7106 |
| DKT | 0.8220 | 0.8220 |
| AKT | — (uzilgan) | — (to‘xtatilgan) |

### Muammo

D50 `(order_id, skill_id)` bo‘yicha takrorni oladi, lekin bir nechta skill'li masalani (47 037 `order_id`) har skill uchun alohida qator qilib qoldiradi. Bu qatorlarda `correct` bir xil va ular talaba ketma-ketligida yonma-yon turadi. Masalaning keyingi qatorini bashorat qilayotgan model shu masalaning javobini allaqachon ko‘rgan bo‘ladi. Bu ketma-ketlikdan foydalanadigan modellarga ta’sir qiladi: DKT, AKT, Elo/Rasch, BKT+IRT (θ va b har javobdan keyin yangilanadi).

### QADAM 1 dalillari

Skript: scratchpad'dagi `order_leak.py` (faqat o‘qish). D50 bilan tozalangan ma’lumot (sha256 `f22e3fb7…`), H2 bo‘linishi (seed 20261006, 5 fold, validatsiya 0,2).

| To‘plam | Qatorlar | (a) order'ning birinchi qatori emas | (a) % | (b) `correct` oldingi qator bilan bir xil | (b) % | (c) oldingi qatorga darhol ergashadi % | (d) nusxa AUC, (a) qatorlar | (d) nusxa AUC, butun test |
|---|---|---|---|---|---|---|---|---|
| Butun to‘plam | 338 001 | 54 896 | 16,24 | 54 896 | 100 | 100 | — | — |
| 1-fold test | 65 597 | 11 044 | 16,84 | 11 044 | 100 | 100 | 1,0 | 0,657301 |
| 2-fold test | 63 804 | 10 252 | 16,07 | 10 252 | 100 | 100 | 1,0 | 0,650239 |
| 3-fold test | 66 442 | 10 375 | 15,62 | 10 375 | 100 | 100 | 1,0 | 0,644160 |
| 4-fold test | 74 065 | 12 373 | 16,71 | 12 373 | 100 | 100 | 1,0 | 0,656325 |
| 5-fold test | 68 093 | 10 852 | 15,94 | 10 852 | 100 | 100 | 1,0 | 0,649338 |

(d) “nusxa” modeli: order'da oldingi qator bo‘lsa — uning javobi, bo‘lmasa — fold'ning o‘qitish qismidagi o‘rtacha to‘g‘rilik (0,648735; 0,660520; 0,646016; 0,649601; 0,652905). Qaror qoidasi ((a) ≥ 5 % va (b) ≥ 95 %) — **sizish tasdiqlangan**.

### Qoida

Talabaning har bir qatori uchun bashorat faqat shu talabaning **qat’iy oldingi** `order_id`'laridagi javoblardan foydalanadi. Bir order'ning barcha qatorlari bir xil holatdan bashorat qilinadi. Holat yangilanishi order'ning barcha qatorlari bashorat qilingandan keyin qo‘llanadi.

- Qoida oltita modelning hammasiga bir xil qo‘llanadi. Order — bir talabaning ketma-ket kelgan, bir xil `order_id` li qatorlari. `order_id` si yo‘q ma’lumotda har bir qator o‘z order'i bo‘ladi (avvalgi xatti-harakat). Bir order'ning qatorlari ketma-ketlikda uzilgan bo‘lsa, harness to‘xtaydi.
- `neuro_model` (engine, `observe`) o‘zgarmaydi. Faqat eksperiment harness'idagi bashorat va yangilanish tartibi o‘zgaradi.
- **BKT, BKT+IRT, Elo/Rasch:** order'ning har bir qatori uchun p̂ order boshidagi holatdan (θ, b, P(L), n) hisoblanadi. Keyin yangilanishlar avvalgidek, qator-qator qo‘llanadi, ya’ni holat traektoriyasi o‘zgarmaydi — faqat order'ning 2-, 3-… qatorlari bashorati.
- **PFA:** bashorat paytidagi muvaffaqiyat/muvaffaqiyatsizlik hisoblari order boshidagi qiymat. D50 dan keyin order ichida skill takrorlanmaydi, shuning uchun bu ASSISTments'da hech narsani o‘zgartirmaydi.
- **O‘qitish o‘zgarmaydi:** DKT/AKT o‘qitish ketma-ketligi, BKT+IRT va Elo'ning o‘qitish fold'idagi b isitishi, PFA'ning o‘qitish matritsasi avvalgidek. DKT/AKT ning early stopping'i uchun validatsiya AUC'i esa D57 bilan hisoblanadi: test bilan bir xil protokol.

### DKT/AKT tanlovi

pykt-toolkit 0.0.38 dagi savol darajasidagi baholash (`pykt.models.evaluate_model.evaluate_question`, Liu va boshq., NeurIPS 2022) ishlatilmaydi. Sabab: u pyKT'ning o‘z `DataLoader` formatini (`qseqs`, `cseqs`, `qidxs`, `rests`, `orirow`) talab qiladi va bir savolning KC bashoratlarini bitta savol bashoratiga birlashtiradi (late fusion: mean/vote/all; AKT uchun early fusion). Bu yerda esa oltita model bir xil qatorlarda juftlanadi (DeLong), shuning uchun har (order, skill) qatori o‘z bashoratini oladi. Tarixni cheklash pyKT'nikiga mos: joriy savolning javoblari ko‘rinmaydi.

- **DKT:** order'ning har bir qatori oldingi order'ning oxirgi qatoridagi yashirin holatdan (o‘sha qadam chiqishidan) o‘z konsepti bo‘yicha o‘qiladi. Oynaning birinchi order'idagi qatorlar oldin hech narsa bo‘lmagani uchun base rate oladi (avval faqat 0-pozitsiya shunday edi).
- **AKT:** Knowledge Retriever (pyKT'da `mask=0` bloklar) maskasi `j < start(t)` ga almashtiriladi: t pozitsiyasi o‘z order'idagi kalitlarni ko‘rmaydi. Ruxsat etilgan kaliti yo‘q qatorlar pyKT'ning `zero_pad` i kabi nolga tenglanadi. pyKT'da bu niqob ichkarida qotirilgan (`np.triu`), shuning uchun retriever bloki va attention funksiyasi harness'da qayta yozilgan; har bir qator alohida order bo‘lganda natija pyKT forward'i bilan bitma-bit bir xil ekani test bilan ko‘rsatiladi. Savol enkoderi (`mask=1`, faqat savollar) o‘zgarmaydi: joriy order'ning savollari ko‘rinadi, javoblari ko‘rinmaydi.

### Kutilgan ta’sir doirasi

- BKT va PFA: o‘zgarmaydi (1e-9). `--quick` `13edf82` bilan `experiments.reproduce --checked BKT PFA` orqali solishtiriladi.
- Elo/Rasch, BKT+IRT (λ=0), DKT, AKT: order'ning 2-, 3-… qatorlarida bashorat o‘zgaradi; to‘liq ma’lumotda bu test qatorlarining ~16 % i.
- Qo‘shimcha (sezgirlik, asosiy emas): har model uchun faqat order'ning birinchi qatorlari bo‘yicha AUC — `tables.md` §10.
- D53 sanity oralig‘i (0,70–0,80) va Xiong qatori (0,73–0,75) o‘zgarmaydi.

---

## QADAM 3 — D57 bilan H2: quick, to‘liq run, tekshiruvlar (2026-10-08/09)

### Ishga tushirishlar

| Run | Commit | Boshlangan | Yakun qatori (`ExecStopPost`) | Holat |
|---|---|---|---|---|
| `--quick` | `2f7365b` | 2026-10-08 20:10:00 | `EXIT_CODE=exited EXIT_STATUS=0` | natija `assist09-quick/20261008-153338/` (`fdfde29`) |
| to‘liq, 1-urinish | `e97621c` | 2026-10-08 21:11:14 | 23:03:49 `SERVICE_RESULT=success EXIT_CODE=killed EXIT_STATUS=TERM; Result=success ExecMainStatus=15` | **kompyuter batareyasi tugab o‘chgani uchun TERM bilan to‘xtagan**; 2-fold'gacha yetgan, natija yozilmagan, ishlatilmaydi. Oxirgi xotira namunasi 23:03:07: rss 2 420 252 kB, MemAvailable 7 999 192 kB |
| to‘liq, 2-urinish | `e97621c` | 2026-10-09 08:38:25 | 10:54:44 `EXIT_CODE=exited EXIT_STATUS=0; Result=success ExecMainStatus=0` | natija `assist09/20261009-055443/` (`abb1fe4`); `git_start`/`git_end` `e97621c`, toza; `tables.verify` = [] |

To‘liq run: 2 soat 16 daqiqa; namunalangan eng yuqori tree RSS 3 832 148 kB, python VmHWM 4 654 416 kB. 1- va 2-fold sonlari ikkala urinishda bir xil.

### Quick solishtiruvi

`python -m experiments.reproduce assist09-quick/20261008-143642 assist09-quick/20261008-153338 --checked BKT PFA`: 800 qiymat, mos kelmaganlari 0.

| Model | Pooled AUC, D57 dan oldin | Pooled AUC, D57 | Farq | §10 AUC (masalaning birinchi qatorlari) |
|---|---|---|---|---|
| BKT | 0.696762 | 0.696762 | 0 | 0.694416 |
| BKT+IRT (λ=0) | 0.714395 | 0.710037 | −0.004358 | 0.707731 |
| Elo/Rasch | 0.729126 | 0.696066 | −0.033060 | 0.697352 |
| PFA | 0.699776 | 0.699776 | 0 | 0.696197 |
| DKT | 0.692844 | 0.645664 | −0.047180 | 0.645306 |
| AKT | 0.698991 | 0.669318 | −0.029673 | 0.667016 |

### 1-fold: D57 dan oldin va keyin (to‘liq ma’lumot, log sonlari)

| Model | `005f30d` / `13edf82` (D57 dan oldin) | `e97621c` (D57) |
|---|---|---|
| BKT | 0.7116 | 0.7116 |
| BKT+IRT (λ=0) | 0.7292 | 0.7277 |
| Elo/Rasch | 0.7784 | 0.7645 |
| PFA | 0.7106 | 0.7106 |
| DKT | 0.8220 | 0.7321 |
| AKT | — | 0.7077 |

### default_coverage (`experiments/default_coverage.py`, to‘liq natija)

| Fold | Standart parametrli mavzular | Test javoblari | Standart parametr bilan | Ulush | O‘sha mavzularning moslash javoblari |
|---|---|---|---|---|---|
| 1 | 12 | 65 597 | 36 | 0.000549 | 211 / 272 404 |
| 2 | 11 | 63 804 | 51 | 0.000799 | 196 / 274 197 |
| 3 | 12 | 66 442 | 60 | 0.000903 | 187 / 271 559 |
| 4 | 12 | 74 065 | 72 | 0.000972 | 175 / 263 936 |
| 5 | 12 | 68 093 | 28 | 0.000411 | 219 / 269 908 |
| pooled | — | 338 001 | 247 | 0.000731 | 988 / 1 352 004 (0.000731) |

### Testlar

| Suite | Natija |
|---|---|
| `experiments/.venv`: `pytest experiments/tests` (`e97621c` gacha) | 239 passed, 1 skipped |
| Django venv, 5433: `pytest` (`e97621c`) | **1018 passed, 14 skipped**, 13 subtests, 0 failed |
| `manage.py check` / `makemigrations --check` | 0 issues / No changes detected |
| `verification/tests` (2026-10-08, D57 quick commit qilingandan keyin) | 730 passed, 9 failed, 1 skipped |
| `verification/neural` | 15 passed |

Backend kutilgan soni endi **1018 passed / 14 skipped** (Django venv). Avval yozilgan 912 / 10 dan farq:

| Manba | passed | skipped |
|---|---|---|
| Yozilgan (`f9bf7a7`, eski muhit) | 912 | 10 |
| `test_metrics_stats.py` endi yig‘iladi: Django venv'da numpy bor (pyBKT 1.4.1 tortadi), avval modul darajasida 1 skip | +16 | −1 |
| `test_models.py`: sklearn/scipy talab qiladigan 3 test (PFA ×2, sparse matritsa) | +3 | −3 |
| = `f9bf7a7` yangi muhitda | 931 | 6 |
| `944681d` (D55): `test_h2_bounds.py` 26, `test_metrics_stats.py` 4, `test_provenance.py` 1 | +31 | 0 |
| `fe0374b`: kontrastlar (4 + 8), launcher (5) | +17 | 0 |
| `e3bafd2`: `test_reproduce.py` | +9 | 0 |
| = D57 dan oldin | 988 | 6 |
| `f23d63b`…`e97621c`: `test_order_protocol.py` 23 (15 o‘tadi, 8 torch/sklearn kerak — skip), §10 jadvali 7, `analyse_pooled` 2, `reproduce --checked` 2, `default_coverage` 4 | +30 | +8 |
| = hozir | 1018 | 14 |

`verification/tests` dagi 9 FAIL: 7 ta na-signal (`test_na.py`), `test_v_e2_include_simulated_exports_what_the_simulator_wrote` (R1/R2 mezon ziddiyati, yuqorida hujjatlangan) va **`test_d48_the_checker_catches_a_hand_written_number[edit1]`**. Oxirgisi eng so‘nggi `assist09-quick` natijasidagi `| 0.697 [` ni `| 0.684 [` ga almashtiradi va 0.684 hech bir metrikaning yaxlitlanmasi emas deb hisoblaydi. D57 quick (`20261008-153338`) da esa 0.683667 (BKT+IRT, 3-fold AUC), 0.683778 va 0.684393 bor. `verification/` ga tegilmadi.

### Muhit holati (2026-10-09)

- `config/.env`: mtime 2026-10-05 09:26; `5433` 0 marta, `5432` 2 marta uchraydi; Django o‘ramsiz `127.0.0.1:5432` ga ulanadi. Fayl ochilmadi va o‘zgartirilmadi. Backend va verification testlari scratchpad'dagi `dj5433.sh` orqali ishga tushirildi (`DJANGO_ENV_FILE=""`, CI usuli; DSN konteyner env'idan olinadi va chop etilmaydi).
- 2026-10-09 08:28 dagi qayta yoqilishdan keyin: docker socket ACL (`setfacl`) qayta tiklanmagan, compose konteynerlari ko‘tarilmagan (5433 tinglanmaydi). Shuning uchun backend va verification bu sanada qayta ishga tushirilmadi.
- Linger yoqilgan (`loginctl enable-linger zokhidjon`, 2026-10-08).

---

## D58 — D55 (chegaralar sezgirligi) D57 protokolida: savollar va darvozalar (2026-10-09, natijadan oldin)

**D55 tavsifiy.** Asosiy natija II bobning (G_MAX; S_MAX) = (0,30; 0,10) sozlamasi bo‘lib qoladi. Sezgirlik natijasi uni almashtirmaydi va sozlama AUC bo‘yicha tanlanmaydi. Kengroq sozlamalar (0,40; 0,20) va (0,49; 0,30) faqat eksperiment parametri; `neuro_model` va Django sozlamalaridagi konstantalar o‘zgarmaydi.

**Uchta savol** (natijani ko‘rgach o‘zgartirilmaydi):

1. BKT+IRT(λ=0) − BKT AUC farqining 95% CI si (talabalar bo‘yicha juftlangan bootstrap) har uch sozlamada 0 dan yuqorimi?
2. BKT+IRT(λ=0) − DKT AUC farqining 95% CI pastki chegarasi har sozlamada ≥ −0,01 (D56) mi?
3. G0 va S0 sozlama chegarasida (grid'ning eng yuqori qiymatida) to‘planish ulushi har sozlamada qancha?

Qo‘shimcha, faqat nuqtaviy: BKT+IRT(λ=0) va Elo/Rasch orasidagi AUC farqi (Elo/Rasch — H2 natijasidagi 0,762142, qayta ishga tushirilmaydi) sozlamalar bo‘yicha qanchaga kamayadi.

**Bitta baholash yo‘li.** `h2_bounds` H2 ning o‘z funksiyalari orqali ishlaydi (`h2.prepare`, `h2.fold_sets`, `h2.fit_predict`, `h2.dkt_model`; D57, D50 tozalashi, bo‘linish, seed'lar), nusxa emas (`88b9749`).

**Darvozalar.**

- Takrorlanish: asosiy sozlamaning 1-fold BKT va BKT+IRT AUC'lari, 6 xonaga yaxlitlanganda, H2 natijasidagiga (`experiments/results/assist09/20261009-055443`: 0.711614 va 0.727693) aynan teng bo‘lishi shart. Oxirida pooled (0.707077; 0.7234) ham shunday tekshiriladi. Teng bo‘lmasa ishga tushirish nolmas kod (5) bilan to‘xtaydi va hech narsa yozilmaydi.
- DKT: H2 sozlamasi, seed'i va protokoli bilan qayta o‘qitiladi. Pooled AUC'i H2 dagi 0.727307 dan |Δ| ≤ 5e-4 bo‘lishi kerak. **5e-4 — metodik tanlov, manbadan olinmagan.** Oshsa, BKT+IRT − DKT farqi son emas, “hisoblanmadi — DKT qayta tiklanmadi” deb chiqadi.
- Bootstrap: 200 replikat (D55), H2 ning seed'i.

---

## D59 — P0/PT grid kengaytmasi va AKT-R (2026-10-09, kod o‘zgarishidan oldin)

**Sabab.** D55 to‘liq run'i (`neurolearn-h2-bounds-full-20261009-152102`, `8e933ad`) L-BFGS-B tekshiruvida 2 sozlamada to‘xtadi (exit 3): kengroq 0,011495, eng keng 0,011346 (chegara 0,01), asosiy 0,009816. Ikkalasida ham skill 277: grid'ning eng yaxshisi PT = 0,05 da (eng past qiymat), L-BFGS-B optimumi PT ≈ 0,0076. H2 (`20261009-055443`) grid_check: PT — 555 moslashdan 133 tasi (24 %) pastki, 84 tasi (15 %) yuqori chetda; P0 — 48 (9 %) pastki, 61 (11 %) yuqori. Nuqson P0/PT grid'ida, G/S da emas.

**Yangi `calibrate.DEFAULT_GRID`** (ilova ham shu grid bilan ishlaydi):

- P0 = mavjud + 0,01 va 0,95: (0,01; 0,05; 0,10; 0,20; …; 0,90; 0,95);
- PT = mavjud + 0,005; 0,01; 0,02; 0,03; 0,5: (0,005; 0,01; 0,02; 0,03; 0,05; 0,10; 0,15; 0,20; 0,30; 0,40; 0,50);
- P(G) va P(S) grid'lari o‘zgarmaydi; G_MAX/S_MAX va II bob konstantalari o‘zgarmaydi.

**AKT-R** — AKT, `n_pid > 0` bilan (pyKT'dagi Rasch item qismi, `problem_id`), qo‘shimcha model. Sabab: BKT+IRT va Elo/Rasch `problem_id` ni ko‘radi, DKT/AKT ko‘rmaydi. D57 maskasi o‘sha. O‘qitishda bo‘lmagan `problem_id` — bitta “noma’lum” indeks. D56 (BKT+IRT − DKT) o‘zgarmaydi; BKT+IRT − AKT-R faqat qo‘shimcha kontrast (CI bilan).

**Natijalar.** Eski H2 (`experiments/results/assist09/20261009-055443`) tarixiy yozuv bo‘lib qoladi; yangi grid bilan olingan H2 asosiy natija bo‘ladi. D55 darvozalari qattiq yozilgan sonlarni emas, `--reference` bilan berilgan H2 papkasining `metrics.json` ini (provenance tekshirilib) o‘qiydi.

**L-BFGS-B chegarasi 1 % qoladi.** Yangi grid bilan ham o‘tmasa, run to‘xtaydi va grid bu qadamda qayta kengaytirilmaydi. Grid chetlaridagi ulushlar natijadan qat’i nazar yoziladi.

### D59 bajarilishi (2026-10-09)

- H2 `--quick`: `20261009-124538`, `8f35bbe`.
- D55 `--quick`, 1-urinish (`neurolearn-h2-bounds-quick-20261009-174602`): 18:02:36 da `EXIT_CODE=killed EXIT_STATUS=TERM` — kompyuter qayta yoqildi. 15 fitdan 8 tasi checkpoint'da (`h2-bounds-a3694827cc18bd15`) qolgan, natija papkasi yozilmagan.
- 2-urinish (`…-210255`, o‘sha `8f35bbe`, `--reference experiments/results/assist09-quick/20261009-124538`): 8 fit checkpoint'dan tiklandi, 7 tasi moslandi; exit 0. Natija `assist09-bounds-quick/20261009-162635` (`43c2424`): darvozalar 6 xonagacha teng, DKT |Δ| 0, L-BFGS-B 0,005666 / 0,004255 / 0,00435, `tables.verify` [].
- Testlar (qayta yoqilgandan keyin, compose 5433, `dj5433.sh` qayta yozildi): backend avval 1024 passed / 19 skipped / **19 error** — `test_h2_bounds.py` dagi `reference` fixture'i (`88b9749`, D58) H2 orqali DKT o‘qitadi, Django venv'da torch yo‘q (`KeyError: 'DKT'`). Fixture'ga `importorskip("torch")` qo‘shildi → **1024 passed / 38 skipped**. `experiments/.venv` da shu fayl 48 passed.
- `verification/tests`: 730 passed, **10 failed** (avvalgi 9 + `test_d48_h2_tables_show_each_models_own_numbers`: `assist09*/*/metrics.json` glob'i `assist09-bounds-quick` natijalarini ham oladi, ularda `pooled` yo‘q → `KeyError`; `8e933ad` dan beri). `verification/neural`: 15 passed (`experiments/.venv`). `verification/` ga tegilmadi.
- H2 full (`neurolearn-h2-full-20261009-213644`, `bdbc7d8`, 21:36:44 da boshlangan): yakun qatori `[2026-10-09T23:42:46+05:00] unit … ended: SERVICE_RESULT=success EXIT_CODE=killed EXIT_STATUS=TERM; Result=success ExecMainStatus=15`, `finished` qatori yo‘q. Sabab — kompyuter o‘chirildi: journal (boot −1) 23:42:40 GNOME `endSessionDialog`, 23:42:45 `systemd-logind: The system will power off now!`; xotira bosimi yo‘q (oxirgi namuna `mem_available_kb=9534456`). Run 5 fold'ni tugatib `pooled 338001 answers from 4163 learners` qatorigacha yetgan, natija papkasi yozilmagan (yarim papka yo‘q). Fold parametrlari ~3450–3570 s (5 worker parallel), eng yuqori `tree_rss_kb=3828700`. H2 da checkpoint yo‘q — qayta ishga tushirish noldan (~2 soat 6 daqiqa). Qayta ishga tushirilmadi; D55 full ham ishga tushirilmadi (shart: H2 full exit 0).

---

## QADAM 5 — D59 bilan H2 to‘liq run (2026-10-10)

### Ishga tushirishlar

| Run | Commit | Boshlangan | Yakun qatori (`ExecStopPost`) | Holat |
|---|---|---|---|---|
| to‘liq, 1-urinish (`neurolearn-h2-full-20261009-213644`) | `bdbc7d8` | 2026-10-09 21:36:44 | 23:42:46 `SERVICE_RESULT=success EXIT_CODE=killed EXIT_STATUS=TERM; Result=success ExecMainStatus=15` | **kompyuter o‘chirilgani uchun TERM bilan to‘xtagan** (journal: 23:42:45 `The system will power off now!`); 5 fold tugagan, bootstrap bosqichida uzilgan, natija papkasi yozilmagan, ishlatilmaydi. Xotira bosimi yo‘q: oxirgi namuna `mem_available_kb=9534456` |
| to‘liq, 2-urinish (`neurolearn-h2-full-20261010-083717`) | `66ff452` | 2026-10-10 08:37:17 | 11:00:06 `SERVICE_RESULT=success EXIT_CODE=exited EXIT_STATUS=0; Result=success ExecMainStatus=0` | natija `assist09/20261010-060005/` (`1c23fa9`); `git_start`/`git_end` `66ff452`, ikkala uchida toza, `tree_changed=False`; `tables.verify` = [], `tables.verify_h2_positions` = [] |

To‘liq run 2 soat 22 daqiqa 49 sekund. Fold parametrlari 2936–3029 s (5 worker parallel, fit bosqichi 08:37:17–09:27 ichida), AKT 150–476 s, AKT-R 143–490 s, DKT 19–27 s. Fitlar: har foldda 111 mavzu, 11–12 tasi standart parametrda, jami 555 fit.

### 7 model: pooled AUC [95 % CI] va §10 AUC

1000 bootstrap replikasi, o‘quvchi bo‘yicha klasterlangan; §10 — faqat masalaning birinchi qatorlari (D57).

| Model | Pooled AUC, D59 (yangi) | 95 % CI | §10 AUC | Pooled AUC, eski (`20261009-055443`) | §10 AUC, eski |
|---|---|---|---|---|---|
| BKT | 0.707479 | [0.701003, 0.713817] | 0.704270 | 0.707077 | 0.703867 |
| BKT+IRT (λ=0) | 0.723898 | [0.717699, 0.730044] | 0.721564 | 0.723400 | 0.721129 |
| Elo/Rasch | 0.762142 | [0.756818, 0.767435] | 0.763628 | 0.762142 | 0.763628 |
| PFA | 0.704193 | [0.698334, 0.709959] | 0.700309 | 0.704193 | 0.700309 |
| DKT | 0.727307 | [0.721100, 0.733392] | 0.736579 | 0.727307 | 0.736579 |
| AKT | 0.708038 | [0.701088, 0.715093] | 0.711256 | 0.708038 | 0.711256 |
| AKT-R | 0.718586 | [0.711952, 0.725309] | 0.724970 | — (modelsiz) | — |

Grid kengaytmasi faqat BKT oilasiga tegadi: Elo/Rasch, PFA, DKT, AKT sonlari eski run bilan aynan bir xil. Sovuq qatorlar: DKT/AKT/AKT-R uchun 6010. BKT+IRT+Pre — “graf yo‘q” qatori (D53).

### Fold AUC‘lari

| Model | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| BKT | 0.7119 | 0.7171 | 0.6970 | 0.7119 | 0.6984 |
| BKT+IRT (λ=0) | 0.7282 | 0.7327 | 0.7140 | 0.7277 | 0.7157 |
| Elo/Rasch | 0.7645 | 0.7670 | 0.7563 | 0.7632 | 0.7585 |
| PFA | 0.7106 | 0.7127 | 0.6962 | 0.7073 | 0.6937 |
| DKT | 0.7321 | 0.7345 | 0.7179 | 0.7319 | 0.7190 |
| AKT | 0.7077 | 0.7283 | 0.6895 | 0.7057 | 0.7172 |
| AKT-R | 0.7077 | 0.7533 | 0.6930 | 0.7474 | 0.6918 |

Eski run'da BKT 0.7116 / 0.7175 / 0.6964 / 0.7111 / 0.6978, BKT+IRT (λ=0) 0.7277 / 0.7329 / 0.7132 / 0.7270 / 0.7151; qolgan to‘rt model fold bo‘yicha ham aynan bir xil.

### Kontrastlar

| Kontrast | Farq | 95 % CI | DeLong p | Holm p | Qaror | Eski run |
|---|---|---|---|---|---|---|
| BKT+IRT (λ=0) − BKT | +0.016420 | [0.015539, 0.017361] | 0.0 | 0.0 | D53 | +0.016323 [0.015417, 0.017315], p = 0.0 / 0.0 |
| BKT+IRT (λ=0) − DKT | −0.003409 | [−0.005372, −0.001425] | 2.94e-06 | 8.82e-06 | D56 | −0.003907 [−0.005856, −0.001927], p = 1.1e-07 / 4.3e-07 |
| BKT+IRT (λ=0) − AKT-R | +0.005312 | [0.002465, 0.008377] | 0.0 | 0.0 | D59 | — |

D56 darvozasi (CI pastki chegarasi ≥ −0,01): −0,005372 ≥ −0,01 — bajarildi.

### DKT sanity (D53)

DKT pooled AUC 0.727307; D53 oralig‘i [0,70; 0,80] — ichida (`within_range=True`); adabiyot oralig‘i [0,73; 0,75] (Xiong va boshq., EDM 2016, dublikatlar olib tashlangan) — undan 0,0027 pastda. Eski run bilan bir xil (0.727307).

### grid_check: grid chetlaridagi ulushlar (555 fit)

| Parametr | Eng past qiymat | Ulush, D59 | Ulush, eski | Eng yuqori qiymat | Ulush, D59 | Ulush, eski |
|---|---|---|---|---|---|---|
| P0 | 0,01 (eski 0,05) | 0.0649 (36) | 0.0865 (48) | 0,95 (eski 0,9) | 0.0577 (32) | 0.1099 (61) |
| PT | 0,005 (eski 0,05) | 0.0162 (9) | 0.2396 (133) | 0,5 (eski 0,4) | 0.1063 (59) | 0.1514 (84) |
| P(G) | 0,05 | 0.0468 (26) | 0.0288 (16) | 0,29 (= II bob chegarasi) | 0.7658 (425) | 0.7820 (434) |
| P(S) | 0,01 | 0.0432 (24) | 0.0216 (12) | 0,097 (= II bob chegarasi) | 0.8739 (485) | 0.8775 (487) |

P0/PT endi chetga yopishmaydi (PT pastki cheti 24 % → 1,6 %); P(G)/P(S) hamon II bob chegarasida — bu D55 ning savoli.

### default_coverage (to‘liq natija)

| Fold | Standart parametrli mavzular | Test javoblari | Standart parametr bilan | Ulush | O‘sha mavzularning moslash javoblari |
|---|---|---|---|---|---|
| 1 | 12 | 65 597 | 36 | 0.000549 | 211 / 272 404 |
| 2 | 11 | 63 804 | 51 | 0.000799 | 196 / 274 197 |
| 3 | 12 | 66 442 | 60 | 0.000903 | 187 / 271 559 |
| 4 | 12 | 74 065 | 72 | 0.000972 | 175 / 263 936 |
| 5 | 12 | 68 093 | 28 | 0.000411 | 219 / 269 908 |
| pooled | — | 338 001 | 247 | 0.000731 | 988 / 1 352 004 (0.000731) |

QADAM 3 dagi sonlar bilan aynan bir xil (bo‘linish va standart parametrlar o‘zgarmagan).

### pyBKT cross-check

5 mavzu solishtirildi, 5 tasi II bob chegaralaridan tashqarida (`g_max=0,3`, `s_max=0,1`); har beshtasida ham P(G) ham P(S) chetda. 400 o‘quvchi (3330 dan), bitta fit, logL ta’rifi ikkala fitter uchun `neuro_model.calibrate.log_likelihood`.

| Mavzu | grid logL | pyBKT logL | Farq (pyBKT − grid) | Javoblar |
|---|---|---|---|---|
| 311 | −1670.2318 | −1587.9659 | +82.2659 | 2813 |
| 47 | −1689.8157 | −1563.9756 | +125.8401 | 2700 |
| 75 | −865.2384 | −827.4882 | +37.7502 | 1617 |
| 50 | −736.7751 | −724.8523 | +11.9228 | 1564 |
| 85 | −526.2438 | −523.4162 | +2.8276 | 1309 |

Eski run bilan aynan bir xil: kengaytirilgan P0/PT grid bu beshta mavzuning optimumini o‘zgartirmadi.

### Xotira (log namunalari, 60 s oralig‘ida, 143 namuna)

Mashina: `MemTotal` 15 615 900 kB, `SwapTotal` 4 194 300 kB.

| Bosqich | Eng yuqori `tree_rss_kb` | Eng past `mem_available_kb` | Eng past `swap_free_kb` |
|---|---|---|---|
| Fit bosqichi (5 worker, 08:37:17–09:27, 50 namuna) | 1 444 204 | 4 307 948 | 4 142 304 |
| Butun run | 19 413 208 (10:59:23, pyBKT cross-check) | 4 307 948 | 4 046 812 |

Swap to‘lmadi: eng past `swap_free_kb` 4 046 812 — 4 194 300 dan ~144 MB kam. 19,4 GB li namuna `ps -o rss= --ppid` yig‘indisi: pyBKT ning fork qilingan jarayonlari bir xil sahifalarni sanaydi — o‘sha namunada `mem_available_kb` 6 076 912 bo‘lgan, ya’ni haqiqiy bosim ~0,4 GB. Parent jarayonning o‘zi: `rss` 2 541 612, `VmHWM` 4 883 324.

### D55 full uchun worker soni

Fit bosqichi namunalaridan har bir worker uchun xotira:

- `mem_available_kb` run boshida 6 797 900 → 5 worker ishga tushgandan keyingi birinchi namunada 5 483 704; kamayish 1 314 196 kB / 5 = **262 839 kB (~0,25 GiB) bir worker**;
- shu paytdagi `tree_rss_kb` 1 444 148, parent `rss` 234 560 → (1 444 148 − 234 560) / 5 = 241 918 kB — xuddi shu tartib.

Shart: fit bosqichida `MemAvailable` ≥ 2 GB. Hisob bo‘sh xotira qancha ekanidan boshlanadi: D55 ni ishga tushirish paytida `MemAvailable` 3 182 084 kB (3,04 GiB) — ertalabki H2 run'idagi 6 797 900 kB emas (orada ochilgan ish stoli ilovalari). Chegaraga qadar bo‘sh joy 3,04 − 2,0 = 1,04 GiB; 1,04 / 0,25 = **4 worker**. 5 worker 1,25 GiB olib ~1,9 GiB qoldirardi — chegaradan past. 8 ishlatilmaydi. 15 (sozlama, fold) juftligi 4 to‘lqinga bo‘linadi (4+4+4+3), fit bosqichi ~3 soat 20 daqiqa.

`experiments/run_h2.sh` ga `H2_WORKERS` qo‘shildi — ilgari worker sonini faqat modulning o‘zi (`--workers` standart qiymati: `min(8, cpu/2)` = 8) tanlardi.

### D55 full ishga tushirildi

Shartlar bajarildi: H2 full exit 0, `tables.verify` va pozitsion tekshiruv [], provenance ikkala uchida toza, DKT 0.727307 D53 oralig‘ida. Buyruq: `H2_REFERENCE=experiments/results/assist09/20261010-060005 H2_WORKERS=4 experiments/run_h2.sh bounds-full`, toza daraxtdan, transient user unit sifatida. Birinchi ishga tushirish (`neurolearn-h2-bounds-full-20261010-143846`, 14:38:46) `H2_WORKERS=5` bilan boshlangan va 14:39:30 da qo‘lda to‘xtatilgan (`EXIT_CODE=killed EXIT_STATUS=TERM`, log'dagi shu qator) — o‘sha paytdagi bo‘sh xotira 5 worker uchun yetmasligi ko‘rinib qoldi; to‘xtatish L-BFGS-B tekshiruvining birinchi sozlamasida bo‘lgan, birorta fit boshlanmagan, natija yozilmagan. O‘sha ishga tushirish 2026-10-10 16:35:59 da kompyuter o‘chirilgani uchun to‘xtadi; natija 2026-10-11 dagi ikkinchi urinishdan olindi — QADAM 6 ga qarang.

---

## QADAM 6 — D55 to‘liq run (chegaralar sezgirligi, 2026-10-11)

### Ishga tushirishlar

| Run | Commit | Boshlangan | Yakun qatori (`ExecStopPost`) | Holat |
|---|---|---|---|---|
| 1-urinish (`neurolearn-h2-bounds-full-20261010-144010`) | `30ad4e4` | 2026-10-10 14:40:10 | 16:35:59 `SERVICE_RESULT=success EXIT_CODE=killed EXIT_STATUS=TERM; Result=success ExecMainStatus=15`, `finished` qatori yo‘q | **kompyuter GNOME sessiya dialogidan o‘chirilgani uchun TERM bilan to‘xtagan**: journal 16:35:57 `gnome-shell: endSessionDialog`, 16:35:58 `systemd-logind: The system will power off now!` / `System is powering down.`, boot −1 16:36:02 da tugaydi (`systemd-inhibit --what=sleep:idle` ataylab o‘chirishni to‘smaydi). Xotira bosimi yo‘q (oxirgi namuna `mem_available_kb=3684620`, `swap_free_kb=2204796`). L-BFGS-B tekshiruvi (3/3) va 1-fold darvozasi o‘tgan, 15 fitdan 4 tasi (asosiy fold 1–4) tugab checkpoint'ga yozilgan; 2-to‘lqin (asosiy fold 5 + kengroq fold 1–3) ~36 daqiqa ishlab yo‘qolgan. Natija yozilmagan |
| 2-urinish (`neurolearn-h2-bounds-full-20261011-203541`) | `30ad4e4` | 2026-10-11 20:35:42 | 23:37:57 `SERVICE_RESULT=success EXIT_CODE=exited EXIT_STATUS=0; Result=success ExecMainStatus=0`, oldidan `finished bounds-full (exit 0); peak sampled tree_rss_kb=1370892` | natija `assist09-bounds/20261011-183756/` (`9db6276`); `git_start`/`git_end` `30ad4e4`, ikkala uchida toza, `tree_changed=False`; `tables.verify` = [] va `tables.verify_h2_bounds_positions` = [] |

2-urinish 3 soat 2 daqiqa 15 sekund. Checkpoint `h2-bounds-99bb9f9117e5e296` (kalitda `commit: 30ad4e4`, shu sababli ikki urinish bir kalitga tushdi): **4 fit tiklandi** (`resumed_items: 4`, asosiy fold 1–4), qolgan **11 fit** 4 worker bilan moslandi (2412–3030 s). Xotira: eng yuqori `tree_rss_kb` 1 370 892, eng past `mem_available_kb` 7 017 728, `swap_free_kb` 4 193 684 (183 namuna) — swap tegilmagan. DKT 5 fold, har biri 10 epoch, 30–34 s.

### Darvozalar (D58)

| Darvoza | Bu run | H2 (`20261010-060005`) | Natija |
|---|---|---|---|
| 1-fold, BKT | 0.711909 | 0.711909 | o‘tdi (6 xonaga teng) |
| 1-fold, BKT+IRT (λ=0) | 0.728172 | 0.728172 | o‘tdi |
| pooled, BKT | 0.707479 | 0.707479 | o‘tdi |
| pooled, BKT+IRT (λ=0) | 0.723898 | 0.723898 | o‘tdi |
| pooled, DKT | 0.727307 | 0.727307 | **\|Δ\| = 0.0** (chegara 5e-4) |

Reference provenance: `experiments/results/assist09/20261010-060005`, commit `66ff452`, 4163 o‘quvchi.

L-BFGS-B tekshiruvi (5 mavzu: 311, 47, 277, 280, 70; 1-fold train+validation; chegara 0.01, uchchalasi o‘tdi):

| Sozlama | Eng katta nisbiy farq | Mavzu | Grid cheti |
|---|---|---|---|
| asosiy | 0.006702 | **311** | g0=max, s0=max |
| kengroq | 0.002235 | **70** | s0=max |
| eng keng | 0.001676 | **280** | g0=min |

D59 dan oldin (eski P0/PT grid, `20261009-152102`) kengroq 0.011495 va eng keng 0.011346 bilan yiqilgan edi, ikkisida ham mavzu 277; endi 277 ning farqi 0.000142 (kengroq) va 0.001439 (eng keng).

### Uch sozlama

| Ko‘rsatkich | asosiy (0,30; 0,10) | kengroq (0,40; 0,20) | eng keng (0,49; 0,30) |
|---|---|---|---|
| BKT pooled AUC [95 % CI] | 0.707479 [0.701801, 0.714096] | 0.715568 [0.709755, 0.722006] | 0.715626 [0.709771, 0.722024] |
| BKT+IRT (λ=0) pooled AUC [95 % CI] | 0.723898 [0.717988, 0.730260] | 0.735939 [0.730382, 0.741909] | 0.746815 [0.741650, 0.752298] |
| §10 AUC (masalaning birinchi qatorlari) | — | — | — |
| BKT+IRT − BKT [95 % CI] | +0.016420 [0.015536, 0.017368] | +0.020371 [0.019311, 0.021532] | +0.031188 [0.029420, 0.032600] |
| … DeLong z, p, Holm p | 92.002777; 0; 0 | 79.367296; 0; 0 | 83.683109; 0; 0 |
| BKT+IRT − DKT [95 % CI] | −0.003409 [−0.005350, −0.001424] | +0.008632 [0.006869, 0.010959] | +0.019507 [0.017772, 0.022179] |
| D56 (CI pastki ≥ −0,01) | **bajarildi** | bajarildi | bajarildi |
| P0 cheti (eng past / eng yuqori) | 0.0649 / 0.0577 | 0.0559 / 0.0631 | 0.0739 / 0.0901 |
| PT cheti | 0.0162 / 0.1063 | 0.0252 / 0.1297 | 0.0505 / 0.1423 |
| P(G) cheti | 0.0468 / **0.7658** | 0.0991 / **0.3928** | 0.3099 / **0.1495** |
| P(S) cheti | 0.0432 / **0.8739** | 0.0667 / **0.6036** | 0.0865 / **0.2757** |
| Test log-likelihood (BKT / BKT+IRT) | −201 910.9638 / −199 849.3698 | −194 522.7950 / −190 710.6381 | −193 757.5989 / −188 005.8888 |
| O‘qitish log-likelihood (jami) | −804 830.3537 | −774 410.2007 | −771 203.0794 |
| BKT+IRT − Elo/Rasch (nuqtaviy) | −0.038244 | −0.026203 | −0.015327 |

Har sozlamada 555 fit (5 fold × 111 mavzu), standart parametrda qolgan mavzular 12/11/12/12/12, grid 4752 nomzod; har sozlamaning eng yuqori qiymati chegaraning bir xil ulushida (G 0.9667, S 0.97). Elo/Rasch H2 dagi 0.762142 (qayta ishga tushirilmaydi). `h2_bounds` masalaning birinchi qatorlari bo‘yicha (§10) AUC hisoblamaydi — u faqat H2 jadvallarida bor.

### D58 ning uch savoliga javob

1. BKT+IRT(λ=0) − BKT ning CI si har uch sozlamada 0 dan yuqorimi? — **ha**: pastki chegaralar 0.015536 / 0.019311 / 0.029420.
2. BKT+IRT(λ=0) − DKT ning CI pastki chegarasi har sozlamada ≥ −0,01 mi? — **ha**: −0.005350 / +0.006869 / +0.017772.
3. G0 va S0 ning chegaradagi to‘planish ulushi? — **G0: 0.7658 / 0.3928 / 0.1495; S0: 0.8739 / 0.6036 / 0.2757** (asosiy / kengroq / eng keng).

Qo‘shimcha (nuqtaviy): BKT+IRT − Elo/Rasch farqi −0.038244 → −0.026203 → −0.015327, ya’ni asosiydan eng kengga 0.022917 ga kamayadi.

**II bob qarori o‘zgarmaydi**: asosiy natija (G_MAX; S_MAX) = (0,30; 0,10), sozlama AUC bo‘yicha tanlanmaydi (D55, D58).

---

## D60 — test vaqtida masala qiyinligini muzlatish (sezgirlik, 2026-10-12, kod va natijadan oldin)

**Sabab.** `verification/REPORT.md` ning K-2 kuzatuvi: BKT+IRT (λ=0) va Elo/Rasch test oqimida `b_q` ni (va `n_q` ni) oqimdagi har bir javob bilan yangilaydi, ya’ni bitta test talabasining bashorati boshqa test talabalarining javoblariga bog‘liq bo‘lib qoladi. Oqim `user_id` bo‘yicha tartiblangan, shuning uchun bu “boshqa talaba” vaqt bo‘yicha keyinroq javob bergan bo‘lishi ham mumkin. II bob bo‘yicha bu model ta’rifining o‘zi (`b_q −= K(n_q)(x − p)`, `n_q` — barcha talabalarning shu masalaga javoblari soni) va D57 ni buzmaydi: D57 talabaning o‘z tarixi haqida, `b_q` esa masalaning parametri. Lekin D53/D56 da’volari shu oqim tartibiga qanchalik bog‘liqligi o‘lchanishi kerak. DKT, AKT va AKT-R da bunday savol yo‘q: ular o‘qitishdan keyin qotiriladi va bashorat paytida vazn o‘zgarmaydi.

**PFA — tekshirildi, frozen variantga kirmaydi.** Regressiya koeffitsiyentlari (β_k, γ_k, ρ_k) faqat o‘qitish to‘plamida baholanadi: `experiments/models/classical.py:445–459` (`PFA.fit`, `LogisticRegression.fit` o‘qitish matritsasida), bashorat esa `predict` da o‘sha qotirilgan modelni chaqiradi (`classical.py:471–477`). Bashorat paytidagi yagona o‘zgaruvchi — hisoblagichlar, va ular `(user_id, skill_id)` kaliti bilan, ya’ni har talabaning **o‘z** oldingi order’laridan sanaladi (`classical.py:510–540`; `successes`/`failures` lug‘atlari har bir `_design` chaqiruvida nolda boshlanadi). Boshqa talabaning javobi PFA bashoratiga kirmaydi, shuning uchun PFA uchun “frozen” varianti yo‘q.

**“Frozen” variantining ta’rifi.**

- `b_q` va `n_q` faqat o‘qitish to‘plamida isitiladi — bu hozirgi `_warm_items` / `EloRasch.fit` qadami, o‘zgarmaydi — va **test oqimida yangilanmaydi**;
- θ (va `n_s`) talabaning o‘z tarixi bilan yangilanishda davom etadi, chunki bu D57 ruxsat bergan yagona ma’lumot;
- P(L) va BKT parametrlari (P0, PT, G0, S0) o‘zgarmaydi; `calibrate.DEFAULT_GRID` va II bob konstantalari (G_MAX 0,30, S_MAX 0,10, a_q, Elo α/β, τ, δ, c) **o‘zgarmaydi**;
- faqat asosiy sozlama (G_MAX; S_MAX) = (0,30; 0,10). D55 ning kengroq sozlamalari bu yerda takrorlanmaydi.

**Modellar.** BKT (nazorat: `use_irt=False`, demak `b_q` umuman ishlatilmaydi — natijasi muzlatishdan **o‘zgarmasligi kerak**), BKT+IRT (λ=0), Elo/Rasch. DKT H2 ning sozlamasi, seed’i va protokoli bilan qayta o‘qitiladi va D58 darvozasi bilan tekshiriladi: pooled AUC H2 dagi qiymatdan |Δ| ≤ 5e-4. AKT/AKT-R qayta o‘qitilmaydi (muzlatish ularga tegishli emas), PFA ham (yuqoriga qarang).

**Kontrastlar.** H2 bilan bir xil: talabalar bo‘yicha juftlik bootstrap, 1000 replika, H2 ning seed’i; DeLong p va sozlamalar oilasi uchun Holm. Uchtasi: BKT+IRT (λ=0) − BKT, BKT+IRT (λ=0) − DKT (D56), Elo/Rasch − DKT. Ikkala variant uchun ham (hozirgi va frozen) bir xil usulda hisoblanadi.

**Darvozalar (natijadan oldin).**

1. `freeze_items=False` bilan BKT va BKT+IRT pooled AUC’i H2 (`assist09/20261010-060005`) dagi qiymatga **6 xonada teng** bo‘lishi shart. Teng bo‘lsa, D55 ning asosiy sozlamasidagi checkpoint fit’lari (`experiments/.runs/checkpoints/h2-bounds-*/fit-0-*`) BKT parametrlari sifatida ishlatiladi; teng bo‘lmasa yoki checkpoint bo‘lmasa, parametrlar qaytadan moslanadi.
2. DKT darvozasi: |Δ| ≤ 5e-4 (D58). O‘tmasa, DKT bilan bog‘liq ikki kontrast son emas, “hisoblanmadi” deb yoziladi.
3. `tables.verify` = [] va pozitsion tekshiruv = [] (D48).

**O‘qish qoidasi (natijadan oldin yoziladi).** Dissertatsiyada H2 ning D53 (BKT+IRT > BKT) va D56 (BKT+IRT DKT bilan taqqoslanadigan) da’volari **faqat hozirgi va frozen variantlarning ikkalasida ham bajarilgan bo‘lsa** “mustahkam” deb yoziladi. Aks holda ikkala son ham, farqning sababi ham yoziladi va da’vo shartli qilib ifodalanadi. Asosiy H2 jadvali **almashtirilmaydi**: frozen natija sezgirlik tahlili bo‘lib qoladi (D55 kabi), chunki II bob modeli `b_q` ni online yangilaydi.

**Natija qayerga.** `experiments/results/assist09-frozen/<timestamp>/` (`metrics.json`, `tables.md`, `env.txt`), hisobot nomi `h2_frozen`.

---

## QADAM 7 — D60 to‘liq run (test vaqtida qiyinlik muzlatilganda, 2026-10-12)

### Ishga tushirishlar

| Run | Commit | Boshlangan | Yakun qatori | Holat |
|---|---|---|---|---|
| `--quick` (`neurolearn`siz, qo‘lda) | `6e0278c` | 2026-10-12 10:18 | exit 0 (10:29) | natija `assist09-frozen-quick/20261012-052856/` (`6f647dc`); uchala darvoza o‘tdi, `tables.verify` [] |
| to‘liq (`neurolearn-h2-frozen-full-20261012-103039`) | `244f046` | 2026-10-12 10:30:39 | 11:34:40 `finished frozen-full (exit 0); peak sampled tree_rss_kb=335240`, `SERVICE_RESULT=success EXIT_CODE=exited EXIT_STATUS=0` | natija `assist09-frozen/20261012-063439/` (`1fee77a`); `git_start`/`git_end` `244f046`, ikkala uchida toza; `tables.verify` = [] va `tables.verify_h2_frozen_positions` = [] |

To‘liq run 1 soat 4 daqiqa 1 sekund; eng yuqori `tree_rss_kb` 335 240 (parametrlar va DKT checkpoint’dan olingani uchun fit ham, o‘qitish ham bo‘lmadi — vaqtning deyarli hammasi 2 × 1 000 replikali bootstrap).

**Qayta ishlatilgani va darvozalari.** BKT parametrlari va DKT ballari D55 ning to‘liq checkpoint’idan (`h2-bounds-99bb9f9117e5e296`, `fit-0-*`, `dkt-*`). Darvozalar: (1) muzlatilmagan ustun H2 ni 6 xonada takrorladi — BKT 0.707479 = 0.707479, BKT+IRT 0.723898 = 0.723898; (2) DKT 0.727307, H2 dagi 0.727307 dan |Δ| = 0 (chegara 5e-4); (3) nazorat — BKT ning ikki ustundagi bashoratlari 338 001 javobda **aynan bir xil** (eng katta farq 0.0).

### Natija: hozirgi va frozen yonma-yon

| Model | hozirgi AUC [95 % CI] | frozen AUC [95 % CI] | Δ (frozen − hozirgi) |
|---|---|---|---|
| BKT | 0.707479 [0.701003, 0.713817] | 0.707479 [0.701003, 0.713817] | 0.000000 |
| BKT+IRT (λ=0) | 0.723898 [0.717699, 0.730044] | 0.723646 [0.717500, 0.729784] | −0.000252 |
| Elo/Rasch | 0.762142 [0.756818, 0.767435] | 0.760567 [0.755131, 0.766044] | −0.001575 |
| DKT | 0.727307 [0.721100, 0.733392] | 0.727307 [0.721100, 0.733392] | 0.000000 |

| Kontrast | Variant | Farq [95 % CI] | DeLong p | Holm p |
|---|---|---|---|---|
| BKT+IRT (λ=0) − BKT (D53) | hozirgi | +0.016420 [+0.015539, +0.017361] | 0 | 0 |
| BKT+IRT (λ=0) − BKT (D53) | frozen | +0.016167 [+0.015279, +0.017097] | 0 | 0 |
| BKT+IRT (λ=0) − DKT (D56) | hozirgi | −0.003409 [−0.005372, −0.001425] | 2.94e-06 | 2.94e-06 |
| BKT+IRT (λ=0) − DKT (D56) | frozen | −0.003661 [−0.005569, −0.001607] | 5.2e-07 | 5.2e-07 |
| Elo/Rasch − DKT (D60) | hozirgi | +0.034835 [+0.030856, +0.039029] | 0 | 0 |
| Elo/Rasch − DKT (D60) | frozen | +0.033260 [+0.029317, +0.037600] | 0 | 0 |

### D60 ning o‘qish qoidasi bo‘yicha xulosa

| Da’vo | hozirgi | frozen | Mustahkam? |
|---|---|---|---|
| **D53** (BKT+IRT − BKT > 0) | **ha** — CI pastki chegarasi +0.015539 | **ha** — +0.015279 | **ha** |
| **D56** (BKT+IRT − DKT CI pastki chegarasi ≥ −0,01) | **ha** — −0.005372 | **ha** — −0.005569 | **ha** |

Ikkala da’vo ham ikkala variantda bajarildi, shuning uchun D60 ning natijadan oldin yozilgan qoidasi bo‘yicha ular dissertatsiyada **“mustahkam”** deb yozilishi mumkin. Asosiy H2 jadvali almashtirilmaydi: frozen ustun sezgirlik tahlili bo‘lib qoladi (II bob modelida `b_q` online yangilanadi).

Muzlatishning ta’siri kattaligi: BKT+IRT uchun −0.000252, Elo/Rasch uchun −0.001575 AUC — ya’ni oqim tartibidan keladigan ustunlik ikki modelda ham bor, lekin D53/D56 ning yo‘nalishini ham, muhimligini ham o‘zgartirmaydi. PFA frozen variantga kirmaydi (D60; `classical.py:445–459`, `471–477`, `510–540`).

---

## D61 — Junyi Academy (2015) ma'lumoti, H1 va H3 uchun (2026-10-12, kod va natijadan oldin)

**Manba va ruxsat.** `http://base.ustc.edu.cn/data/JunyiAcademy_Math_Practicing_Log/junyi.rar` (USTC BASE oynasi, 1 295 551 222 bayt, `Last-Modified` 2021-01-22); dataset hujjati — o‘sha papkadagi `README.md` (9 599 bayt, sha256 `597d3ae8…7857b7`), u asl manbani `https://pslcdatashop.web.cmu.edu/Files?datasetId=1198` deb ko‘rsatadi. Hujjatdagi shartlar: **“Any form of commercial usage is not allowed!”** va iqtibos:

> Haw-Shiuan Chang, Hwai-Jung Hsu and Kuan-Ta Chen, “Modeling Exercise Relationships in E-Learning: A Unified Approach,” International Conference on Educational Data Mining (EDM), 2015.

Hujjat ma’lumot 2015-yil yanvarda Junyi Academy platformasidan olinganini, maqoladagi to‘plam esa 2014-yil iyulda olinganini yozadi. DBE-KT22 o‘rniga shu to‘plam ishlatiladi (foydalanuvchi ruxsat berdi).

**Inventarizatsiya (o‘lchangan).** `junyi_Exercise_table.csv` 837 qator (**835 noyob nom**; `matrix_mul_two` va `matrix_app_fruit_oil` ikki marta, ikkisi ham `live=FALSE`), `relationship_annotation_training.csv` 1 131 juftlik, `relationship_annotation_testing.csv` 823 juftlik. Hujjatdagi 837 mashq va 1 131 annotatsiya juftligi mos keladi; 25 925 992 log yozuvi va 247 606 talaba hamda log fayli bo‘yicha sonlar **hali tekshirilmagan** (fayl yuklanmoqda, pastga qarang).

**Daraxt va E_P.** 9 area (`arithmetic` 301, `algebra` 258, `geometry` 161, `probability-statistics` 40, `analytic-geometry` 30, `N/A` 20, `biology` 12, `calculus` 10, `logics` 5), 41 topic, har topic aynan bitta area ichida, bo‘sh katak yo‘q. Modelga moslash: **kurs** — bitta `Junyi Academy` ildizi; **bo‘lim** — area; **ichki bo‘lim** — topic; **mavzu (barg)** — mashq. `area=N/A` va `topic=N/A` bo‘lgan 20 mashq “N/A” bo‘limi ostida qoladi va hisobotda shunday belgilanadi.

`prerequisites` ustuni — vergul bilan ajratilgan mashq nomlari (189 katakda vergul bor). **Yo‘nalish:** hujjat bu ustunni “Indicate its prerequisite exercise (**parent shown in its knowledge map**)” deb ta’riflaydi, ya’ni A qatorida B turса B — A ning bilim xaritasidagi otasi va A dan oldin keladi ⇒ qirra **B → A**. Ma’lumot ham shuni ko‘rsatadi: 979 noyob qirraning 885 tasida (90,40 %) `h_position(B) < h_position(A)`, teskarisi 33 tada (3,37 %), tengi 61 tada; `creation_date` bo‘yicha dalil kuchsiz (57,94 % oldin). Shu ikki dalil bilan yo‘nalish aniq.

E_P ning holati: 986 qirra o‘qiladi, 979 tasi noyob (3 juftlik ikki marta yozilgan), **nomi topilmagan prerekvizit yo‘q (0)**, **2 o‘z-o‘ziga qirra** (`proportions_1`, `number_sense_length_l1`) — Y2 bo‘yicha tashlanadi. Prerekvizitsiz mashqlar: 95 (11,35 %); hech qanday qirrasi yo‘q mashqlar: 59. `live=FALSE`: 61 mashq. Eng katta kiruvchi daraja 7, chiquvchi 14. Qirralarning 83,86 % i bitta topic ichida, 94,79 % i bitta area ichida.

**Sikl.** Graf DAG emas: bitta SCC (3 tugun) — `simplifying_radicals` → `adding_and_subtracting_radicals` → `radical_multiplication_and_division` → birinchisiga. Boshqa sikl yo‘q. **Qoida:** Tarjan bilan topilgan har bir SCC bitta mavzuga birlashtiriladi (spetsifikatsiyaning 8-bosqichi, DBE-KT22 uchun yozilgan qoida), birlashtirilgan mavzu nomi a’zolarining alifbo tartibidagi birinchisi bo‘ladi va metadata’ga a’zolar ro‘yxati yoziladi. Birlashtirilgandan keyin graf DAG: 833 tugun, 976 qirra, **eng uzun yo‘l 65 qirra** (`count_one_by_one_1` … `quotient_rule`).

**Bitta javob = bitta order (D57).** Junyi log’ida har qator bitta mashqqa bitta urinish to‘plamidir va bir qatorda bitta mashq bo‘ladi, ya’ni ko‘p-skill’li order yo‘q: `order_id` har qator uchun alohida beriladi (javob tartibida), `problem_id` — `exercise` + `problem_type`, `skill_id` — mashq (SCC birlashtirilgandan keyingi nomi).

**Tozalash.**
- **Javob ta’rifi:** `correct` ustuni hujjat bo‘yicha “whether the student’s **first attempt** is correct, and the field would be false if any hint is requested” — ya’ni birinchi urinish to‘g‘riligi allaqachon shu ustunda. Qo‘shimcha hisob-kitob qilinmaydi; `count_attempts` va `count_hints` faqat metadata’ga yoziladi.
- **Tartib:** `time_done` — Unix vaqti **mikrosekundda**; javoblar (talaba, `time_done`) bo‘yicha o‘sish tartibida o‘qiladi. Bir xil `time_done` bo‘lsa, `problem_number` bo‘yicha, keyin fayl tartibi bo‘yicha.
- **Filtr:** faqat `exercise` nomi mashqlar jadvalida bor qatorlar; `live` qiymati filtrga kirmaydi (2015-yil yanvardagi holat javobning o‘zini bekor qilmaydi), lekin `live=FALSE` mashqlar soni va ularning javoblari ulushi metadata’ga yoziladi. `review_mode=true` qatorlar **kiritiladi**, chunki ular ham haqiqiy javob; `topic_mode` va `suggested` faqat metadata.
- `problem_number = 1` bo‘lgan qatorlar dastlabki k urinish tahlili (H3) uchun alohida belgilanadi.

**Talabalar tanlovi.** Seed `20261006` bilan tasodifiy N talaba (talaba darajasida, javoblari butun olinadi). N ning hisobi H2 ning o‘lchangan fit vaqtidan: D59/D55 to‘liq run’larida bitta fold uchun `fit_skill_params` 2 936–3 029 s (o‘rtacha ≈ 2 980 s) oldi, fold’ning moslash to‘plami 338 001 × 0,8 ≈ 270 400 javob va grid 4 752 nomzod; demak ≈ 2 980 / (270 400 × 4 752) ≈ **2,3 µs** bitta (javob × nomzod) uchun, ya’ni fold uchun ≈ 0,011 s × javoblar soni. Junyi’da grid o‘sha (DEFAULT_GRID o‘zgarmaydi), shuning uchun H2 bilan bir xil fit vaqtini (fold uchun ~50 daqiqa) saqlash uchun moslash to‘plami ≈ 270 000 javob bo‘lishi kerak. Hujjatdagi namunada (50 000 session) talaba boshiga javoblar o‘rtachasi 167,8 (mediana 19), demak N × 167,8 × 0,8 ≈ 270 000 ⇒ **N = 2 000 talaba** (≈ 336 000 javob). Bu son log inventarizatsiyasi (B4) tugagach qayta tekshiriladi: tanlangan talabalarning haqiqiy javoblari soni 270 000 ± 30 % dan chiqsa, N shu nisbatda o‘zgartiriladi va o‘zgartirish H1/H3 ishga tushirilishidan **oldin** shu yerga yoziladi.

**H1 — tayyorlik qoidalari.** Qoidalar: (1) ehtimoliy — r_s(w) ≥ τ; (2) bajarilganlik — har bir prerekvizitga ≥ 1 javob; (3) o‘tish bali — prerekvizitlar bo‘yicha aniqlik ≥ `pass_mark`; (4) **qo‘shimcha, platformaning o‘zi** — `earned_proficiency` (hujjat Khan Academy ning o‘zlashtirish algoritmiga havola qiladi: `http://david-hu.com/2011/11/02/how-khan-academy-is-using-machine-learning-to-assess-student-mastery.html`): mashq w ning barcha prerekvizitlari uchun talaba `earned_proficiency=true` ga yetgan bo‘lsa, w tayyor deb hisoblanadi. Bu qoida platformaning amaldagi qarori bo‘lgani uchun qo‘shimcha taqqoslash sifatida kiradi, II bob qoidasi emas.
Teng qamrov: qoidalar har xil qamrovda turgani uchun τ qidirib boshqa qoidalarning qamroviga tenglashtiriladi. O‘lchovlar: xato ulushi (tayyor deb belgilangan, lekin keyingi k javobda muvaffaqiyatsiz), qamrov va r_s(w) bo‘yicha AUC. Sezgirlik: τ ∈ {0,70; 0,80; 0,90; 0,95}, δ ∈ {0,05; 0,10; 0,15}.

**H3 — graf nazoratlari.** BKT+IRT+Pre (λ validatsiyada tanlanadi) to‘rtta graf bilan: asl graf; teskari graf (barcha qirralar aylantirilgan); daraja taqsimoti saqlangan tasodifiy graf (`networkx.directed_edge_swap`, 20 seed); grafsiz (λ = 0). O‘lchov: dastlabki k ∈ {3, 5} urinish bo‘yicha AUC (va butun to‘plam bo‘yicha AUC qo‘shimcha ustun sifatida).

**Split va statistika.** Talabalar bo‘yicha 5 qism, o‘qitish qismining 20 % i validatsiya, seed `20261006` (H2 bilan bir xil). Bootstrap talaba bo‘yicha klasterlangan: asosiy to‘rt taqqoslash (asl, teskari, tasodifiy grafларning o‘rtachasi, grafsiz) uchun 1 000 replika; 20 tasodifiy seed alohida bootstrap qilinmaydi — ularning nuqtaviy AUC taqsimoti (min, mediana, max) beriladi, aks holda hisob vaqti bir necha baravar oshadi. DeLong va Holm H2 dagidek.

**O‘qish qoidasi (natijadan oldin).**
- **H1 “qo‘llab-quvvatlandi”**: teng qamrovda ehtimoliy qoidaning xato ulushi bajarilganlik va o‘tish bali qoidalarining har ikkisidan past va bu farqning 95 % CI si nolni kesib o‘tmasa. “Qo‘llab-quvvatlanmadi”: farqning CI si teskari tomonda nolni kesmasa. Aks holda **“aniqlanmadi”**.
- **H3 “qo‘llab-quvvatlandi”**: asl graf bilan dastlabki k AUC teskari grafdan ham, tasodifiy graflarning o‘rtachasidan ham, grafsiz variantdan ham yuqori va har uch farqning 95 % CI si nolni kesib o‘tmasa. “Qo‘llab-quvvatlanmadi”: biror farqning CI si teskari tomonda nolni kesmasa. Aks holda **“aniqlanmadi”**.
- Har ikkisida ham son chiqmasa (masalan, ma’lumot yetmasa) “ishga tushirilmadi” deb yoziladi, taxmin yozilmaydi.

**Graf sifati.** Annotatorlar yo‘q, shuning uchun Cohen κ **“hisoblanmadi — annotator yo‘q”** deb qoladi (D13/8b-3 qoidasi). Uning o‘rniga platformaning grafi bilan dataset annotatsiyasining mosligi **tavsifiy** ko‘rsatkich sifatida yoziladi (o‘lchangan): 1 131 juftlikning 414 tasida (36,60 %) platformada qirra bor (A→B 169, B→A 245, ikkisi ham yo‘q 717); `Prerequisite_avg` ning “qirra bor” ni ajratish AUC’i **0,6824**, faqat A→B yo‘nalishi uchun **0,5595**; qirra bor juftliklarda o‘rtacha baho 5,5770, yo‘qlarida 4,3531 (`Prerequisite_avg`: min 1,1667, mediana 4,7778, max 8,8000; har juftlikni 5–15 ta ishchi baholagan). **Cheklovlar:** graf platformaning o‘z bilim xaritasi (ekspertlar qo‘lda qurgan, 2015-yil yanvar holati), mustaqil annotatsiya emas; 2 o‘z-o‘ziga qirra va 3 takroriy qirra bor; bitta uch tugunli sikl bor; 11,35 % mashqda prerekvizit yo‘q; annotatsiyaning yo‘nalishi platforma qirrasining yo‘nalishi bilan kuchsiz mos (yuqoridagi 0,5595). Shu sababli H3 natijasi “bu graf bilan” deb o‘qiladi, “prerekvizit grafi umuman” deb emas.

**Taxminiy hisob vaqti va xotira.** Parametr fit: 5 fold × ~50 daqiqa (4 worker bilan parallel ≈ 1 soat 15 daqiqa; grid va javoblar soni yuqoridagi hisob bo‘yicha). Graf arm’lari: 23 variant × 5 fold × bashorat (~5 s) ≈ 10 daqiqa. Bootstrap: asosiy to‘rt taqqoslash uchun 1 000 replika ≈ 35–40 daqiqa (D60 da 338 001 javob va 4 model uchun o‘lchangan). Jami ≈ **2–2,5 soat**. Xotira: javoblar soni H2 bilan bir xil tartibda, D60/D55 run’larida daraxt RSS 1,4 GB dan oshmagan; log faylini bo‘laklab (chunk) o‘qib faqat tanlangan talabalarning qatorlari saqlanadi, shuning uchun fit bosqichida `MemAvailable` ≥ 2 GB qoladi (worker soni avvalgi xotira qoidasi bo‘yicha hisoblanadi).

**Hali bajarilmagani.** `junyi_ProblemLog_original.csv` (hujjat bo‘yicha siqilmagan holda ≈ 2,6 GB) yuklanmoqda: 1 295 551 222 baytdan 2026-10-12 11:10 da 37 125 568 bayt (2,9 %), o‘lchangan tezlik ≈ 39 KB/s, qolgan vaqt ≈ 8 soat.

**Yuklanish to‘xtab qolgan (2026-10-12 15:32 da o‘lchangan).** `experiments/data/junyi.rar` 219 740 079 bayt (1 295 551 222 dan **17,0 %**), oxirgi yozilish 12:48:24; 15:32 da fayl o‘smagan va yuklovchi jarayon yo‘q (`ps`: wget/curl/aria2 yo‘q). Arxiv RAR5 (`Rar!\x1a\x07\x01\x00`) va chala, shuning uchun `junyi_ProblemLog_original.csv` ni ajratib bo‘lmaydi — faqat arxiv boshidagi kichik fayllar (mashqlar jadvali, ikkita annotatsiya fayli, README) allaqachon ajratilgan va ishlatilmoqda. Shu sababli B4 ning log'dan olinadigan sonlari, N ning tasdiqlanishi (D61a), H1/H3 ning `--quick` va to‘liq run'lari **boshlanmadi**. Davom ettirish: `wget -c` bilan o‘sha URL'ga (yoki yuklab, `sha256sum` bilan tekshirib), keyin `unar`/`7z` bilan faqat `junyi_ProblemLog_original.csv` ajratiladi (PSLC fayli — 9,1 GB — ochilmaydi). Shu sababli B4 ning **ma’lumotdan olinadigan** sonlari (talaba boshiga va mashq boshiga javoblar taqsimoti, loglarning necha foizi graf mashqlariga tegishli, 25 925 992 / 247 606 ni tasdiqlash) hali yo‘q; ustunlarning **ma’nosi** yuqorida hujjatdan ko‘chirilgan. H1/H3 kodi yozilishidan oldin shu sonlar qo‘shiladi va N qayta tekshiriladi.

---

## D62 — 8b-3 implementatsiyasi: D61 ochiq qoldirgan qarorlar (2026-10-12, kod va natijadan oldin)

D61 Junyi to‘plamini, grafni, tozalashni, H1/H3 ning o‘lchovlarini va o‘qish
qoidasini belgilaydi. Kodni yozish uchun yetmaydigan qarorlar shu yerda, hammasi
natijadan oldin. Hech biri II bob konstantalarini, `DEFAULT_GRID` ni yoki
`experiments/.venv` lock fayllarini o‘zgartirmaydi.

**1. Yuklovchining joyi.** `experiments/loaders/` papkasi yo‘q: D49–D51 ning
yuklovchilari `experiments/datasets/` da (`assist09.py`, `graphs.py`). Junyi
yuklovchisi ham shu yerda — `experiments/datasets/junyi.py`, bitta modulda graf
(mashqlar jadvali) va log.

**2. SCC birlashtirishdagi nom.** `components.condense` komponentni eng kichik
tugun indeksiga birlashtiradi. D61 esa birlashtirilgan mavzuning nomi
a’zolarining alifbo tartibidagi birinchisi bo‘lishini talab qiladi, shuning
uchun komponentlar `condense` ga alifbo bo‘yicha birinchi a’zosi boshida
turgan holda beriladi; `condense` ning o‘zi o‘zgarmaydi.

**3. BKT+IRT+Pre uchun graf argumenti.** `BKTFamily` ga ixtiyoriy `graph`
argumenti qo‘shiladi (mavzu → ((prerekvizit, ω), …)). Graf berilmasa, model
avvalgidek `Unavailable` deb e’lon qiladi, ya’ni H2 ning yo‘li va natijalari
o‘zgarmaydi. Junyi grafida qirra vazni yo‘q, shuning uchun **ω = 1,0** (II
bobning ta’rifida ω ∈ (0, 1], og‘irliklarsiz graf uchun teng vazn).
Prerekvizitning P(L) si — talabaning shu mavzudagi oxirgi P(L) si, javob
bermagan bo‘lsa `Prerequisite.p_l = None` va o‘rniga prerekvizitning o‘z P0 si
(`neuro_model.init`, 3.3-bo‘lim).

**4. H1 da P(L) qaydan.** Tayyorlik qoidalari P(L) ni talab qiladi, demak
oqimda bitta model turishi kerak: **BKT+IRT (λ=0)** — H2 ning asosiy modeli,
parametrlari fitting (train+validatsiya) to‘plamida moslangan, `b_q` o‘sha
to‘plamda isitilgan. r_s(w), R_s(w) va M `neuro_model.readiness` ning
funksiyalari bilan hisoblanadi (`readiness_score`, `is_ready`,
`mastered_flag`) — platformaning `assessments/services/readiness.readiness_at`
bilan bir xil kod. Javob berilmagan prerekvizit platformadagidek P(L) = 0 va
M = False bilan kiradi.

**5. H1 voqeasi.** Test qismidagi talabaning w mashqiga **birinchi** urinishi,
Pre(w) ≠ ∅ va w ning kamida bitta prerekvizitiga oldin javob bergan bo‘lishi
sharti bilan. Qoida qiymatlari voqeadan **oldingi** holatdan olinadi.

**6. Muvaffaqiyatsizlik.** Voqeadan boshlab talabaning w dagi dastlabki k
javobida to‘g‘rilar ulushi < 0,5 bo‘lsa — muvaffaqiyatsiz. Asosiy k = 3,
qo‘shimcha ustun k = 5 (H2 ning dastlabki k ∈ {3, 5} ko‘rsatkichi bilan bir
xil). k ta javobi yo‘q voqealar mavjud javoblari bo‘yicha baholanadi.

**7. `pass_mark`.** 0,60 — platformaning `Topic.pass_mark_percentage` standart
qiymati (`curriculum/models.py`, 60 %). Qoida: prerekvizitlarga berilgan barcha
oldingi javoblar bo‘yicha aniqlik ≥ 0,60.

**8. Teng qamrov.** τ **validatsiya** qismida qidiriladi: nomzodlar —
validatsiyadagi voqealarning r qiymatlari, tanlangan τ taqqoslanadigan
qoidaning validatsiyadagi qamroviga eng yaqin qamrovni beradi. O‘lchov test
qismida. Shunday qilib τ test natijasiga moslanmaydi.

**9. H1 statistikasi.** Xato ulushlari farqining 95 % CI si talabalar bo‘yicha
klasterlangan bootstrap bilan (1 000 replika, seed `20261006`) —
`stats.bootstrap_statistic`, `bootstrap_auc` bilan bir xil klasterlash. AUC
oralig‘i — `bootstrap_auc`. DeLong H1 da ishlatilmaydi: o‘lchov AUC emas,
ulushlar farqi.

**10. H3 da λ.** λ grid {0,25; 0,50; 0,75}, har bir fold uchun validatsiyadagi
AUC bo‘yicha tanlanadi; II bobning qiymati (0,50) grid ichida va o‘zgarmaydi.
λ = 0 — alohida “grafsiz” arm, tanlovga kirmaydi.

**11. H3 da tasodifiy graf.** `networkx.directed_edge_swap` (networkx 3.4.2
`experiments/requirements.lock` da allaqachon bor — yangi bog‘liqlik emas), 20
seed, har bir tugunning kiruvchi va chiquvchi darajasi saqlanadi. networkx bu
yerda II bobning hisobini qayta yozmaydi, faqat null-model yasaydi.

**12. `run_all.py`.** Faqat dispatcher: `--dataset`, `--models`, `--quick` ni
oladi va h1/h2/h3 ni chaqiradi, o‘z natija turini yaratmaydi (V-E4 uchun
`--quick`). **Diqqat:** `verification/tests/test_na.py::test_na_group_e_pipeline_run_all_is_not_implemented`
aynan shu fayl paydo bo‘lganda yiqilishi uchun yozilgan (“This fails when it
lands”). `verification/` ga tegilmaydi; V-E3/V-E4 ni qayta baholash
tekshiruvchining ishi.

**13. Kechiktirilganlar.** DBE-KT22 yuklovchisi — ma’lumot manbasi ochilmadi
(ADA kirish so‘rovi javobsiz), annotatsiya vositasi (`annotate.py`) — annotator
yo‘q. Ikkisi ham bog‘liqlik matritsasida “Kechiktirildi” sababi bilan yoziladi,
kod yozilmaydi (D48: yo‘q narsa son chiqarmaydi).

---

## 8b-3 kodi — Junyi yuklovchisi, H1, H3, `run_all.py` (2026-10-12, natijadan oldin)

D61 va D62 ga ko‘ra yozildi; **natija yo‘q**: Junyi log fayli hali yuklanmagan
(pastda). Shu bo‘lim kodning nimadan iboratligini va o‘lchangan graf sonlarini
qayd etadi.

### Yangi modullar

| Fayl | Nima qiladi |
|---|---|
| `experiments/datasets/junyi.py` | Mashqlar jadvalidan graf (B→A), Y2 (o‘z-o‘ziga qirra) va Y3 (SCC birlashtirish, Tarjan), area→topic→mashq daraxti; logni bo‘laklab o‘qish, D61 tozalashi, inventarizatsiya, seed bilan N talaba tanlash |
| `experiments/h1.py` | To‘rtta tayyorlik qoidasi + II bobning R si, teng qamrov uchun τ qidirish (validatsiyada), xato ulushi / qamrov / r_s(w) AUC, τ×δ sezgirligi, D61 ning o‘qish qoidasi |
| `experiments/h3.py` | BKT+IRT+Pre to‘rt graf arm'i bilan (asl, teskari, daraja saqlangan tasodifiy ×20 seed, grafsiz λ=0), λ validatsiyada, dastlabki k ∈ {3,5} AUC, uch kontrast (bootstrap + DeLong + Holm) |
| `experiments/run_all.py` | `--dataset ... --models ... [--quick]` dispatcher (8-bosqich; V-E3/V-E4) |

O‘zgargan: `models/classical.py` (`BKTFamily(graph=…)`, `item_state`, `stream`),
`stats.py` (`bootstrap_statistic` — klasterlangan bootstrap ixtiyoriy
statistika uchun), `tables.py` (`render_h1_report`, `render_h3_report` va
ularning pozitsion tekshiruvlari), `h2.py` (`--models`), `run_h2.sh`
(`h1-*`, `h3-*`, `junyi-*` rejimlari).

**H2 ga ta’siri yo‘q.** `BKTFamily` ning uchinchi varianti graf berilmaganda
avvalgidek `Unavailable` deb e’lon qiladi, `--models` ning standart qiymati —
hammasi, va `experiments/.venv` ga yangi paket qo‘shilmadi (networkx lock
faylida bor edi).

### D61 dagi ikki sonning tuzatilishi (kod bilan o‘lchangan)

D61 ba’zi sonlarni 837 **qator**, ba’zilarini 835 **noyob mashq** darajasida
hisoblagan. Kod ikkisini ajratadi va ikkala qiymatni ham yozadi:

| Ko‘rsatkich | D61 da | O‘lchangan | Sabab |
|---|---|---|---|
| o‘qilgan prerekvizit yozuvi | 986 | **984** | takrorlangan ikki qator o‘qilmaydi (birinchi nusxa qoladi); 984 = 979 noyob + 3 takroriy + 2 o‘z-o‘ziga |
| `live=FALSE` | 61 | **59** mashq / **61** qator | ikkala takroriy qator ham `live=FALSE` |
| `algebra` / `N/A` mashqlari | 258 / 20 | **257 / 19** | o‘sha ikki qator (`matrix_app_fruit_oil` — algebra, `matrix_mul_two` — N/A) |

Boshqa hammasi D61 dagidek chiqdi va yuklovchining `verify=True` darvozasiga
yozildi: 979 noyob qirra, 2 o‘z-o‘ziga qirra, 3 takroriy, 0 nomi topilmagan
prerekvizit, 1 SCC (3 tugun), birlashtirilgandan keyin 833 mavzu / 976 qirra,
eng uzun yo‘l 65, prerekvizitsiz 95 mashq (mavzu darajasida 97), qirrasiz 59.
Mashqlar jadvalining sha256'i `13292cc2…769546`.

### Testlar

`experiments/.venv` da butun paket: **391 passed, 2 skipped** (7 daq 37 s).
Yangi testlar 81 ta: `test_junyi.py` (27), `test_h1.py` (19), `test_h3.py`
(18), `test_run_all.py` (13), `test_metrics_stats.py` ga 2 (`bootstrap_statistic`),
`test_provenance.py` ga 2 (launcher'ning `junyi-*` va `h3-*` rejimlari).
Skip ikkitasi: Django sozlanmagan muhitda τ/δ ni `settings.THESIS_MODEL` bilan
solishtirish, va oldindan bor pyBKT skip'i.

Graf testlari **haqiqiy** `junyi_Exercise_table.csv` da ishlaydi (yuqoridagi
sonlar), log testlari sintetik fixture'da: `junyi_problem_log_tiny.csv` (har
bir tozalash qoidasi uchun bitta qator) va `conftest.write_junyi_log` —
prerekvizit ta’siri qo‘shilgan generativ log, 12 mashqli fixture graf bilan.
H1 va H3 ning quvuri shu log'da uchidan-uchiga ishga tushadi va `tables.md`
katak-katak tekshiriladi (D48). **Bu sonlar dissertatsiya natijasi emas.**

### Tekshiruvga ta’siri

`verification/tests/test_na.py::test_na_group_e_pipeline_run_all_is_not_implemented`
aynan `experiments/run_all.py` paydo bo‘lganda yiqilishi uchun yozilgan edi
(“This fails when it lands”), shuning uchun u endi yiqiladi. `verification/`
ga tegilmadi (D54): V-E3/V-E4 ni qayta baholash va `REPORT.md` ni yangilash
tekshiruvchining ishi.

---

## D63 — H4: saqlash usullari benchmarki (9-bosqich, 2026-10-12, kod va natijadan oldin)

**H4 ning ifodasi.** Dissertatsiyada daraxt qo‘shni ro‘yxat (`parent_id`) va
rekursiv CTE bilan saqlanadi (D3, `django-tree-queries`); muqobil — MPTT ning
oraliq kodlashi (`lft`/`rght`). H4 shu tanlov haqida:

> Bilimlar bazasining daraxti uchun qo‘shni ro‘yxat + rekursiv CTE (CTE usuli)
> **yozish** amallarida (barg qo‘shish, shoxni ko‘chirish, shoxni o‘chirish va
> parallel yozish) MPTT dan tez va parallel yozishda yaxlitligini saqlaydi;
> **o‘qish** amallarida (shoxni o‘qish, ajdodlarni o‘qish) MPTT bilan
> taqqoslanadigan bo‘lib qoladi.

Ya’ni H4 bitta tezlik da’vosi emas, ikkita: yozishda ustunlik va o‘qishda
“yomonlashmaslik”. Audit (`NEUROLEARN_AUDIT.md`, EX5/P1-5) eski
`benchmark_tree.py` ning faqat o‘qishni, faqat o‘rtacha vaqtni va SQLite'ni
o‘lchaganini topgan edi; shu sababli u olib tashlandi (`5e5cb09`) va o‘rniga
`benchmarks` app'i yoziladi.

**O‘qish qoidasi (natijadan oldin).** Har bir (shakl, hajm, amal) katagi
uchun nisbat **ρ = mediana(MPTT) / mediana(CTE)** hisoblanadi; ρ > 1 — CTE
tezroq. Takrorlar **juftlashtirilgan** (pastga qarang), shuning uchun ρ ning
95 % ishonch oralig‘i juftlikni saqlagan bootstrap bilan (1 000 replika,
seed `20261006`) olinadi.

- **“CTE tezroq”**: ρ > 1 va CI ning pastki chegarasi > 1.
- **“MPTT tezroq”**: ρ < 1 va CI ning yuqori chegarasi < 1.
- **“taqqoslanadigan”**: CI 1 ni kesib o‘tadi.

H4 **qo‘llab-quvvatlandi** deb yoziladi, agar: (1) to‘rtta yozish amalining
har birida, **har bir** shakl va hajmda natija “CTE tezroq” bo‘lsa; (2) ikkita
o‘qish amalida hech bir katakda “MPTT tezroq” **va** ρ < 1/1,5 bo‘lmasa
(ya’ni CTE o‘qishda 1,5 barobardan ko‘proq yomonlashmasa — bu “taqqoslanadigan”
so‘zining shu yerdagi ta’rifi va u natijadan oldin tanlandi); (3) parallel
yozishdan keyin CTE da yaxlitlik buzilishi topilmasa. Shartlarning biri
bajarilmasa — **“qo‘llab-quvvatlanmadi”**, va qaysi katakda nima bo‘lgani
yoziladi; biror katakda son chiqmasa (timeout) — o‘sha katak uchun
**“hisoblanmadi — timeout”**, taxmin yozilmaydi. p95 ham har katak uchun
beriladi va u da’voga kirmaydi: u dumni ko‘rsatadi, chunki UI uchun eng yomon
holat ham muhim.

**Daraxtlar (seed bilan, `20261006`).** Uchta shakl:

- **kursga o‘xshash** — 4 daraja (kurs → bo‘lim → ichki bo‘lim → mavzu),
  keng: har bir tugunning shoxlanishi hajmdan hisoblanadi (3–5 daraja
  talabining ichida);
- **chuqur zanjir** — har bir tugunning bitta farzandi, ya’ni chuqurlik = n;
- **tasodifiy** — ota tugun mavjud tugunlar orasidan tasodifiy tanlanadi.

Hajmlar: **10³, 10⁴, 10⁵** tugun. Daraxt ikkala jadvalga **bir xil**
`parent_id` ketma-ketligi bilan quriladi (`bulk_create`, keyin MPTT uchun bir
marta `rebuild()`), shuning uchun ikki usul bir xil daraxtni o‘lchaydi.
Qurish vaqti o‘lchovga **kirmaydi** — u amal emas; lekin metrics'ga yoziladi.
Daraxtning o‘zi `parent_id` ketma-ketligining sha256'si bilan qayd etiladi:
benchmark'ning kirishi fayl emas, generator, va uning izi shu (D48 ruhida).

**Amallar (har biri bitta tugundan boshlanadi).**

| Amal | Tur | CTE | MPTT |
|---|---|---|---|
| shoxni o‘qish | o‘qish | `descendants()` | `get_descendants()` |
| ajdodlarni o‘qish | o‘qish | `ancestors()` | `get_ancestors()` |
| oxiriga barg qo‘shish | yozish | `parent=…` bilan `create` | `create` (`order_insertion_by` yo‘q) |
| eng chapga barg qo‘shish | yozish | `position` bilan `create` | `insert_at(..., 'first-child')` |
| shoxni ko‘chirish | yozish | `parent` ni o‘zgartirib `save` | `move_to(target, 'last-child')` |
| shoxni o‘chirish | yozish | `delete()` (CASCADE) | `delete()` |
| parallel yozish | yozish | 2 / 4 / 8 jarayon | 2 / 4 / 8 jarayon |

Nishon tugunlar har takror uchun seed bilan oldindan tanlanadi va **ikkala
usulda bir xil** bo‘ladi (juftlashtirish shundan keladi). O‘chirish va
ko‘chirish uchun nishon “o‘rtacha” shox bo‘lishi uchun daraxtning ichki
tugunlari orasidan tanlanadi.

**O‘zgartiruvchi amallar tranzaksiyada o‘lchanadi va orqaga qaytariladi**
(`transaction.atomic` + `set_rollback`), shuning uchun har bir takror aynan
bir xil daraxtdan boshlanadi va ikki usul bir xil holatni ko‘radi. Buning
narxi: commit'ning fsync'i o‘lchovga kirmaydi — bu **ikkala usulga teng**
ta’sir qiladi va shu yerda yozib qo‘yiladi. Parallel yozish esa, aksincha,
haqiqiy **commit** qiladi (maqsadi shu), shundan keyin daraxt qayta quriladi.

**O‘lchash tartibi.** Har bir (shakl, hajm, usul, amal) uchun **5 qizdirish +
30 takror**. Yoziladi: mediana, p95, min, max, SQL so‘rovlar soni
(`CaptureQueriesContext`, har takrorda) va o‘zgargan qatorlar soni (amaldan
oldin/keyin `COUNT(*)` va MPTT uchun o‘zgargan `lft`/`rght` lar soni).
Yagona takror `--timeout` (standart 120 s) dan oshsa, katak **“timeout”**
bo‘ladi, qolgan takrorlari bajarilmaydi va son yozilmaydi.

**Parallel yozish.** 2, 4 va 8 jarayon, har biri o‘z ulanishi bilan
(`connections.close_all()` fork'dan keyin), belgilangan vaqt davomida
(standart 20 s) aralash **qo‘shish + ko‘chirish** bajaradi. Takror 3 marta
(har biri 20 s). Yoziladi: o‘tgan amallar soni (throughput, op/s) ning
medianasi, min va max'i, har amalning kechikish medianasi va p95'i, xatolar
soni turlari bo‘yicha (deadlock, `InvalidMove`, boshqa). Throughput uchun
nisbat va CI — yuqoridagidek, 3 takror juftlashtirilgan holda.

**Yaxlitlik (har parallel yozishdan keyin, ikkala usulda).**

- **Y1**: ota zanjirida sikl yo‘q (har tugundan ildizgacha yurish cheklangan),
  har bir daraxtda bitta ildiz, `parent_id` yo‘q tugun aynan bitta;
- **MPTT uchun qo‘shimcha**: har tugunda `lft < rght`, bir daraxt ichida
  oraliqlar to‘qnashmaydi (faqat to‘liq ichma-ich joylashadi), `level` ota
  zanjiri uzunligiga teng, va `rebuild()` dan **keyin**gi `lft`/`rght`
  qiymatlari oldingisi bilan solishtiriladi — farq bo‘lsa, oraliqlar
  parallel yozishda buzilgan.
- Buzilish topilsa, u **natija** sifatida yoziladi (nechta tugun, qaysi
  tekshiruv), ishga tushirish to‘xtamaydi va buzilish yashirilmaydi.

**Muhit.** Natijaga yoziladi: Postgres versiyasi (`SHOW server_version`),
`shared_buffers`, `fsync`, CPU modeli va mantiqiy yadrolar soni, RAM,
CPU governor (`/sys/devices/system/cpu/cpu*/cpufreq/scaling_governor`),
yuklama (`/proc/loadavg`) ishga tushirishning boshida va oxirida, hamda
fonda og‘ir jarayon yo‘qligi haqidagi tekshiruv (ishga tushirish paytidagi
eng ko‘p CPU yegan 5 jarayon). Vaqt o‘lchovlari mashinaga bog‘liq va buni
jadval o‘zi aytadi.

**Baza.** Benchmark **alohida bazada** ishlaydi: `DATABASES["benchmark"]` —
`BENCHMARK_DATABASE_URL` bo‘lsa shundan, aks holda `default` ning
sozlamalaridan `NAME` ga `_bench` qo‘shib olinadi (5433 dagi o‘sha Postgres).
Router (`benchmarks.routers.BenchmarkRouter`) `benchmarks` app'ini faqat shu
alias'ga, qolgan hamma narsani esa faqat `default` ga yo‘naltiradi. Buyruq
ishga tushishidan oldin alias'ning `NAME` i `default` ning `NAME` i bilan bir
xil emasligini tekshiradi va bir xil bo‘lsa **to‘xtaydi**: dev bazasidagi
jadvallarga tegilmaydi, o‘chirilmaydi, tozalanmaydi. Benchmark o‘z ikki
jadvalini (`benchmarks_mpttnode`, `benchmarks_ctenode`) har katakdan oldin
`TRUNCATE` qiladi — faqat o‘zining jadvallarini.

**Natija qayerga.** `experiments/results/tree-benchmark/<timestamp>/`:
`metrics.json`, `measurements.csv` (har takrorning xom vaqti), `tables.md`
(`experiments.tables` orqali, D48 verify va pozitsion tekshiruv bilan),
`env.txt`. Hisobot nomi `tree_benchmark`. Har bir (shakl, hajm, usul) uchun
checkpoint `experiments/.runs/checkpoints/tree-bench-<digest>/` ga yoziladi
(kalit: commit, seed, hajmlar, takrorlar, timeout), shuning uchun uzilgan run
o‘sha joydan davom etadi. `--quick`: 10³ hajm, 5 takror, parallel 5 s —
natija `tree-benchmark-quick/` ga va “dissertatsiya natijasi emas” belgisi
bilan.

**Ishga tushirish.** Uzoq run `experiments/run_h2.sh bench-full` bilan (shu
launcher'ning `systemd-run` + `systemd-inhibit` + xotira namunalari yo‘li;
`manage.py` uchun unga skript rejimi qo‘shiladi va Django venv'i ishlatiladi).

**Nima o‘zgarmaydi.** II bob konstantalari, `DEFAULT_GRID`, lock fayllar
(mptt 0.18.0 va tree-queries 0.24.0 allaqachon `requirements.lock` da),
`curriculum` modellari va migratsiyalari, `verification/`. `INSTALLED_APPS`
ga `mptt` va `benchmarks` qo‘shiladi — D3 aynan shuni nazarda tutgan: mptt
faqat benchmark app'ida qoladi.

### D63a — nimani o‘lchash to‘g‘ri: yozish yo‘li va qulf (2026-10-12, natijadan oldin)

**Sabab (300 tugunli sinov ishga tushirishi, natija emas, tashlab yuborildi).**
D63 ning kodi birinchi marta ishga tushirilganda ikki narsa ko‘rindi:

1. `move_to` **o‘zi tekshiradi**: ko‘chirish tugunni o‘z shoxi ichiga
   qo‘yadigan bo‘lsa, mptt `InvalidMove` chiqaradi. Xom CTE yo‘li
   (`node.parent_id = target; save()`) hech narsa tekshirmaydi. Shu ikkisini
   yonma-yon qo‘yish tezlikni emas, **tekshiruvning yo‘qligini** o‘lchaydi.
   Platformaning o‘z CTE yo‘li esa tekshiradi:
   `curriculum/services/kb.py` da Y1 aynan
   `Topic.objects.ancestors(new_parent, include_self=True).filter(pk=current).exists()`
   bilan tekshiriladi va struktura yozuvlari advisory lock ostida ketadi.
2. Parallel yozishda **ikkala** usulda Y1 buzildi: CTE da 1 885 tugun siklga
   tushdi (tekshiruv yo‘q), mptt da esa `InvalidMove` borligiga qaramay 26
   tugun siklga tushdi va oraliqlar buzildi (494 tugun `rebuild` bilan farq
   qildi) — ya’ni mptt ning tekshiruvi ham o‘qish va yozish orasida
   poygaga uchraydi.

**Qaror 1 — o‘lchanadigan yo‘l platformaning yo‘li.** CTE ning ko‘chirish
amali endi Y1 tekshiruvini **o‘z ichiga oladi** (`ancestors(...).exists()`,
`kb.py` dagi bilan bir xil ifoda), chunki taqqoslanadigan mptt amali ham
tekshiradi. Bu bitta qo‘shimcha so‘rov turadi va u SQL ustunida ko‘rinadi;
tekshiruv muvaffaqiyatsiz bo‘lsa, amal (mptt dagidek) xato bilan tugaydi va
xato sifatida sanaladi.

**Qaror 2 — parallel yozish ikki variantda.**

- **qulfsiz** (`unlocked`) — har bir usulning o‘z yozish yo‘li, qulfsiz:
  2, 4, 8 jarayon, 3 takror. Bu **saqlash usulining o‘zi** nimani
  kafolatlaydi degan savolga javob beradi.
- **qulfli** (`locked`) — platformaning yo‘li: tranzaksiya ichida
  `pg_advisory_xact_lock` olinadi (BB9/D30 dagidek), keyin Y1 tekshiruvi va
  yozuv. Vaqtni tejash uchun faqat **eng ko‘p jarayon soni** (8) bilan, 3
  takror, ikkala usulda.

**Qaror 3 — o‘qish qoidasidagi yaxlitlik sharti qulfli variantga tegishli.**
D63 ning uchinchi sharti (“parallel yozishdan keyin CTE da yaxlitlik
buzilishi yo‘q”) endi aniq: u **qulfli** variantda baholanadi, chunki
platforma struktura yozuvlarini aynan shunday bajaradi. Qulfsiz variantning
natijasi jadvalda qoladi va tavsifiy o‘qiladi: “qulfsiz holda ikkala usul ham
Y1 ni buzadi” — bu ham natija, yashirilmaydi. Tezlik shartlari (yozishda CTE
tezroq, o‘qishda 1,5 barobardan ko‘proq sekin emas) **o‘zgarmadi**, chegaralar
ham o‘zgarmadi.

Bu tuzatish natija **ko‘rilgandan keyin** yozildi, lekin sinov ishga
tushirishining sonlari ishlatilmaydi va chegaralar siljimadi: o‘zgargani —
nimani o‘lchash to‘g‘ri ekani.


### D63b — chuqur zanjirda o‘chirish: Django ning kollektori (2026-10-12, to‘liq run'dan oldin)

**Sabab.** `--quick` (10³ tugun) ishga tushirishida `deep_chain` shaklining
`delete_branch` katagi **ikkala usulda ham** `RecursionError` bilan tugadi.
Sabab saqlash usuli emas: Django ning `CASCADE` kollektori o‘ziga havola
qiluvchi daraxtni har bir daraja uchun bitta freym bilan yuradi, standart
chegara esa 1 000. Ya’ni bu Django ning xossasi va ikki usulga teng tegishli.

**Qaror.** `delete_branch` amali o‘z davomida Python ning rekursiya
chegarasini **400 000** ga ko‘taradi va keyin qaytaradi (`sys.setrecursionlimit`,
ikkala usulda bir xil joyda). CPython 3.11+ da Python→Python chaqiruvlari C
stack'ni o‘stirmaydi, shuning uchun chegarani ko‘tarish xavfsiz; qiymat
benchmark quradigan eng katta daraxtdan ancha yuqori. Chegara `metrics.json`
ning `settings.deep_recursion_limit` iga yoziladi.

**O‘lchangan feasibility (natija emas, imkoniyat tekshiruvi).** 100 000
tugunli chuqur zanjirda bitta `delete_branch` ≈ 51 s (CTE), ya’ni D63 ning
bitta takror uchun 120 s chegarasidan past. Demak katak “timeout” bo‘lmaydi,
lekin 30 takror shu yerda ~30 daqiqa oladi; `deep_chain/100000` bloki eng
qimmat blok bo‘ladi. To‘liq run bir necha soat ketishi mumkin va u blok
bo‘yicha checkpoint qiladi.

**O‘zgarmagani.** Takrorlar soni, chegaralar, nisbat va o‘qish qoidasi
o‘zgarmadi. Chegaradan oshgan katak avvalgidek “timeout”, xato bilan tugagan
katak “hisoblanmadi” bo‘lib qoladi va taxmin yozilmaydi.


---

**Qo‘shimcha (2026-10-14 12:10, natijani ko‘rmasdan).** Log'dagi namunalar
bo‘yicha bosim 11:40 dan beri uzluksiz edi, ya’ni **har bir blok** belgi
ostida qolardi va joriy run baribir to‘liq qayta o‘lchanishi kerak edi.
Shuning uchun u to‘xtatildi:

- unit `neurolearn-h2-bench-full-20261014-113251`, yakun qatori
  `SERVICE_RESULT=success EXIT_CODE=killed EXIT_STATUS=TERM; Result=success
  ExecMainStatus=15` (12:09:59) — wrapper unit bilan birga to‘xtadi, shuning
  uchun `finished bench-full` qatori yo‘q;
- **natija yozilmadi**: natija papkasi faqat oxirgi blokdan keyin yoziladi,
  demak yarim natija yo‘q;
- tugagan bloklar: `course_like/1000`, `course_like/10000`,
  `course_like/100000` (checkpoint `tree-bench-68b96862614e0a11`),
  `deep_chain/1000` yarim qolgan. Bosim namunalari soni: 1, 10, 6 va 5 —
  **hammasi “bosim ostida o‘lchangan”**;
- bu run **asosiy natija emas**. Checkpoint o‘chirilmaydi va solishtirish
  uchun saqlanadi; yangi run yangi commit'dan boshlanadi, ya’ni checkpoint
  kaliti ham yangi bo‘ladi va eski bloklar ishlatilmaydi.

**Yangi run boshlanish sharti.** Ishga tushirishdan **oldin**
`MemAvailable ≥ 6 GB` **va** ishlatilgan swap `< 200 MB` bo‘lishi shart.
Bajarilmasa, run boshlanmaydi va shart buzilgani yoziladi. O‘lchangan
(2026-10-14 12:15): `MemAvailable` 9,09 GB, ishlatilgan swap 0 MB — shart
bajarildi.

**Shart buzilgan urinish (2026-10-14 15:28:48).** D63d ning tuzatishidan keyin
run ishga tushirildi, lekin boshlash sharti **bajarilmagan** edi:
`MemAvailable` 7,69 GB (shart bajarildi), ishlatilgan swap esa **1 737 MB**
(shart: < 200 MB) — bu oldingi pass'dan qolgan sahifalar (uning eng yuqori
`tree_rss_kb` i 4 509 296, ya’ni 4,3 GB edi). Unit
`neurolearn-h2-bench-full-20261014-152848` 49 sekunddan keyin, 15:29:37 da
to‘xtatildi (`EXIT_STATUS=TERM`, `ExecMainStatus=15`); birorta blok
checkpoint'ga yozilmadi va natija yozilmadi. Keyingi urinish swap tozalangandan
(`swapoff -a && swapon -a`, root huquqi kerak) keyin, shart qayta o‘lchanib
qilinadi.

---

### D63d — chuqur daraxtda mptt'ning `rebuild()` i ishlatilmaydi (2026-10-14, natijadan oldin)

**Sabab.** Toza mashinada ishga tushirilgan to‘liq run (`…-140928`) beshinchi
blokda, `deep_chain/10000` ning parallel bosqichidan keyingi yaxlitlik
tekshiruvida yiqildi: `mptt.managers._rebuild_helper` o‘zini **har bir daraja
uchun** chaqiradi, 10 000 chuqur zanjirda esa interpretatorning freymlari
tugaydi (`RecursionError`, traceback'da “Previous line repeated 983 more
times”). Chiqish kodi 1, **natija yozilmadi** (natija faqat oxirgi blokdan
keyin yoziladi). Shu paytgacha to‘rt blok tugagan edi
(`course_like/1000`, `/10000`, `/100000`, `deep_chain/1000`) va **birortasida
ham D63c belgisi yo‘q** (eng past `MemAvailable` 3,28 GB, eng past `SwapFree`
2 399 MB).

**Qaror.** Oraliqlarni solishtirishda mptt ning `rebuild()` i faqat
**sayoz** daraxtda ishlatiladi: tugunlar soni ≤ 20 000 **va** chuqurlik
≤ **500**. Ikkisidan biri oshsa, iterativ qayta hisoblash ishlatiladi
(`recompute_intervals`), u `test_generator.py` da mptt ning o‘z `rebuild()` i
bilan uchta shaklda tengligi tasdiqlangan. Qo‘shimcha sug‘urta: `rebuild()`
chaqiruvi atrofida rekursiya chegarasi D63b dagi qiymatga ko‘tariladi va
qaytariladi. Natijada `rebuild_source` ustuni qaysi yo‘l ishlatilganini
(“mptt rebuild()” yoki “recomputed … too deep / too many nodes”) aytadi.

**O‘zgarmagani.** Tekshiruvning **mazmuni** o‘zgarmadi: saqlangan
`lft`/`rght`/`level` lar parent havolalaridan kelib chiqadigan qiymatlar bilan
solishtiriladi. O‘lchov tartibi, takrorlar, chegaralar, seed va o‘qish qoidasi
ham o‘zgarmadi.

**Checkpoint.** Tuzatish commit qilinadi, demak checkpoint kaliti yangilanadi
va to‘rtta tugagan blok qayta o‘lchanadi (≈ 40 daqiqa). Eski bloklar
(`tree-bench-d77747c9b1b0eb00`) o‘chirilmaydi, lekin ishlatilmaydi: ular
tekshiruvning eski yo‘li bilan o‘lchangan.


---

### D63e — uzilish bilan o‘lchangan blok ham qayta o‘lchanadi (2026-10-15, natijadan oldin)

**Sabab.** Toza mashinada, shart bajarilgan holda boshlangan run
(`…-165416`, 2026-10-14 16:54) **noutbuk uxlab qolgani** uchun uzildi:
log'dagi `memory:` namunalari 16:56:16 dan 08:31:34 gacha, ya’ni **15,59
soat** yo‘q, holbuki sampler har 60 sekundda yozadi; `uptime -s` o‘sha-o‘sha
(14:04), demak qayta yuklanish bo‘lmagan — tizim suspend bo‘lgan.
`systemd-inhibit --what=sleep:idle` qopqoqni yopishni to‘smaydi: u alohida
inhibitor (`handle-lid-switch`).

Uzilish o‘lchovni ikki joyda buzadi: (1) uyqudan keyin kesh sovuq, Postgres
ulanishlari yangi, CPU chastotasi boshqa holatda; (2) `CLOCK_MONOTONIC` uyqu
vaqtini hisoblamaydi, shuning uchun uyqu paytida “to‘xtab turgan” parallel
bosqich uyg‘ongandan keyin qolgan sekundlarini davom ettiradi, ya’ni bitta
bosqich ikki xil mashina holatida o‘lchanadi.

**Belgi va qoida.** Blok **“uzilish bilan o‘lchangan”** deb belgilanadi, agar
uning oynasidagi ketma-ket `memory:` namunalari orasida **3 × namuna
oralig‘idan** (standart 60 s da, ya’ni 180 s dan) katta tanaffus bo‘lsa.
Bunday blok, D63c dagi “bosim ostida” bloklar kabi, **qayta o‘lchanadi**;
jadvalda asosiy son qayta o‘lchangan qiymat bo‘ladi.

**Launcher tuzatildi.** `experiments/run_h2.sh` endi
`systemd-inhibit --what=sleep:idle:handle-lid-switch` bilan ishga tushiradi,
ya’ni qopqoq yopilishi ham to‘siladi (`test_provenance.py` shu qatorni
tekshiradi). Bu to‘siq “foydalanuvchi ataylab suspend qilsa” ham ishlaydi,
lekin uzilish baribir bo‘lsa, yuqoridagi belgi uni ushlaydi.

**Hozirgi holat.** `…-165416` run'i 08:39:02 da to‘xtatildi
(`EXIT_STATUS=TERM`, `ExecMainStatus=15`), **natija yozilmadi**; uning yagona
tugagan bloki (`course_like/1000`) uzilish bilan o‘lchangan, shuning uchun
ishlatilmaydi. Tuzatish commit qilinadi (checkpoint kaliti yangilanadi) va
run noldan, kun davomida qayta boshlanadi.


---

### D63f — xotira: nima to‘ldiradi, nima qilinadi (2026-10-16, ishga tushirishdan oldin)

**Raqamlash.** Foydalanuvchining topshirig‘ida bu qaror “D63d” deb atalgan;
D63d (mptt `rebuild()` rekursiyasi) va D63e (suspend) allaqachon band, shuning
uchun bu qaror **D63f** nomini oladi. Mazmuni o‘zgarmagan.

**Diagnostika (o‘qishdan olingan).** 2026-10-14 dan beri oltita urinish:

| # | Unit | Qayerda to‘xtadi | Yakun qatori | Peak tree_rss |
|---|---|---|---|---|
| 1 | `…-113251` | `deep_chain/1000` (4-blok) | TERM (qo‘lda, D63c) | 1,77 GB |
| 2 | `…-140826` | hech qayerda | exit 1 — Postgres o‘chiq edi | 0,01 GB |
| 3 | `…-140928` | `deep_chain/10000` (5-blok) | exit 1 — `RecursionError` (D63d) | 4,30 GB |
| 4 | `…-152848` | `course_like/1000` | TERM (shart buzilgan, D63c) | 0,01 GB |
| 5 | `…-165416` | `course_like/10000` | TERM (suspend, D63e) | 0,96 GB |
| 6 | `…-084605` | `deep_chain/100000` (6-blok) | **exit 137 (SIGKILL — OOM)** | **11,43 GB** |

6-urinishda bloklar bo‘yicha: `course_like` 1000/10000/100000 → peak 0,98 /
1,51 / 1,76 GB; `deep_chain/1000` → 1,78 GB; **`deep_chain/10000` → 11,43 GB**
(eng past `mem_available` 2,48 GB, `swap_free` 661 MB);
`deep_chain/100000` → 8,04 GB (eng past 1,75 GB / 0 MB, D63c belgisi).
O‘ldirilishdan oldingi namunalar: 10:57 da 1,35 GB → 10:58 da 2,65 GB →
10:59 da **8,43 GB**, va `tree_rss == rss`, ya’ni **bola jarayonlar yo‘q
edi** — demak sabab 8 jarayonli fork emas. Kernel journal'i root'siz
o‘qilmaydi; user journal'ida `app.slice: … 11.3G memory peak, 1.6G memory
swap peak` — bu transient unit'ning o‘zi.

**Sabab (o‘lchangan).** Xotirani **ish stoli dasturlari emas, benchmark'ning
o‘zi** to‘ldiradi, aniqrog‘i `deep_chain` shaklida CTE ning `descendants()`
amali: `django-tree-queries` rekursiv CTE'si har bir qator uchun ajdodlar
massivini (`tree_path`) olib yuradi, shuning uchun n tugunli zanjirda
materializatsiya ~n²/2 element bo‘ladi. O‘lchangan (toza probe):
chuqurlik 2 000 → 0,86 s va 0,25 GB; chuqurlik 10 000 → **22,3 s va 4,50 GB**
(MPTT: 0,01 s va 0,07 s). 10⁵ da bu ~2 200 s va ~450 GB, ya’ni bu mashinada
**jismonan sig‘maydi**. 6-urinish aynan shu yerda — `deep_chain/100000`
blokining birinchi o‘lchanadigan amalida — o‘ldirilgan (blok sarlavhasidan
keyin birorta katak qatori chiqmagan).

Bu H4 uchun **natija**, nosozlik emas: CTE usulining chuqur zanjirdagi o‘qishi
yo‘l materiali bo‘yicha kvadratik. Lekin u butun run'ni o‘ldirmasligi kerak.

**Qarorlar.**

**(a) Ishga tushirish.** Run transient user unit sifatida ishlaydi va
Claude Code/Antigravity/terminal yopiq bo‘lsa ham davom etadi (`systemd-run
--user`, `systemd-inhibit --what=sleep:idle:handle-lid-switch`). Boshlanish
sharti D63c dagidek: `MemAvailable ≥ 6 GB` va ishlatilgan swap `< 200 MB`.

**(b) Xotira izini kamaytirish — o‘lchanadigan amallar o‘zgarmaydi.**
1. Har bir benchmark ulanishida `statement_timeout` = bitta takror uchun
   berilgan vaqt chegarasi (standart 120 000 ms): D63 ning chegarasi endi
   **serverda** ham qo‘llanadi, ya’ni sig‘maydigan so‘rov natijani
   materializatsiya qilishdan oldin to‘xtatiladi. Bunday xato katakda
   “timeout” deb yoziladi (son emas).
2. Jarayonning o‘ziga **manzil maydoni chegarasi** (`RLIMIT_AS`, standart
   8 GB, `--memory-limit-gb` bilan o‘zgaradi): chegaradan oshgan ajratish
   `MemoryError` beradi va katak “ishga tushirilmadi — xotira” bo‘lib
   yoziladi, OOM-killer butun run'ni o‘ldirmaydi.
3. Gigiyena: har katakdan keyin katta tuzilmalar bo‘shatiladi va
   `gc.collect()` chaqiriladi; parallel bosqich **fork'dan oldin** ham
   shunday qilinadi, ya’ni bola jarayonlar kichik ota uyumidan nusxa oladi.
   SQL va natija o‘zgarmaydi — buni testlar tekshiradi (so‘rovlar soni va
   qaytarilgan qatorlar bir xil).

**(c) Sig‘masa — son emas, gap.** Parallel bosqichdan oldin bo‘sh xotira
tekshiriladi: `MemAvailable ≥ jarayonlar × 400 MB + 2 GB` bo‘lmasa, o‘sha
bosqich **“ishga tushirilmadi — xotira”** deb yoziladi (D48: son emas) va
2/4 jarayonli variantlar qoladi. Shakl va hajmlar **olib tashlanmaydi**,
jumladan `deep_chain/100000`: jismonan sig‘magan kataklar ham xuddi shu gap
bilan chiqadi. **Natijaga qarab blok tanlash taqiqlanadi**: tanlov faqat
xotira chegarasiga asoslanadi va chegara natijadan oldin yozilgan.

**(d) Checkpoint.** Kod o‘zgargani uchun kalit yangilanadi va **hamma blok
qaytadan o‘lchanadi**; eski checkpoint'lar (`tree-bench-b8676f6351044db6` va
oldingilari) o‘chirilmaydi, lekin ishlatilmaydi. Ularning hech biri baribir
ishlatilmas edi: 6-urinishning birinchi besh bloki D63c/D63e bo‘yicha toza
bo‘lsa ham, kod o‘zgarishi (statement_timeout va xotira chegarasi) o‘lchov
shartini o‘zgartiradi.


---

### D63g — oraliqlarni solishtirish tartibdan mustaqil bo‘lishi kerak (2026-10-16, qayta o‘lchashdan oldin)

**Sabab.** To‘liq run (`…-085158`, natija `20261016-093916`) qulfli variantda
to‘rtta bosqichda “MPTT yaxlitligi buzildi” dedi. Tekshirilganda: o‘sha
to‘rttasida **faqat** `differs_from_rebuild` nolmas, tartibdan mustaqil uchta
invariant (`lft < rght`, ota oralig‘i ichida, takroriy chegara, `level`) esa
**toza**, va hammasi `REBUILD_LIMIT`/`REBUILD_DEPTH_LIMIT` dan oshgani uchun
**qayta hisoblash** yo‘li bilan tekshirilgan.

Sabab — tekshiruvning o‘zida: `recompute_intervals` farzandlarni **pk
tartibida** yuradi, mptt esa mavjud **birodarlar tartibini** saqlaydi
(`_rebuild_helper` qatorlarni `tree_id, lft` bo‘yicha o‘qiydi). Qonuniy
`move_to(target, "last-child")` tugunni birodarlar oxiriga ko‘chiradi, ya’ni
pk tartibi bilan birodarlar tartibi ajraladi. O‘lchangan (40 tugunli daraxt,
bitta qonuniy ko‘chirish): mptt ning `rebuild()` i **0 farq**, qayta hisoblash
esa **16 farq** ko‘rsatdi. Demak bu buzilish emas, **tekshiruvning soxta
ijobiysi**.

**Qaror.** `recompute_intervals` birodarlarni saqlangan `lft` bo‘yicha
tartiblaydi (pk — faqat teng bo‘lsa), ya’ni `rebuild()` nima qilsa, shuni
qiladi. Raqamlash baribir noldan qayta quriladi, shuning uchun haqiqiy
buzilish (bo‘sh oraliq, kesishish, noto‘g‘ri shox o‘lchami) avvalgidek
ushlanadi; ushlanmaydigan yagona narsa — birodarlarning qayta tartiblanishi,
u esa buzilish emas (mptt ning o‘z `rebuild()` i ham uni buzilish demaydi).
Test: qonuniy `move_to` dan keyin tekshiruv **o‘tishi** kerak, buzilgan
oraliqda esa **yiqilishi**.

**Natijaga ta’siri.** Vaqt o‘lchovlari (ρ, mediana, p95) bu kamchilikdan
mustaqil — ular o‘zgarmaydi. Yaxlitlik xulosalaridan **qulfli variantdagi
to‘rtta “buzildi”** bekor bo‘ladi (ular soxta), qulfsiz variantdagi
buzilishlar esa qoladi: u yerda tartibdan mustaqil invariantlar 27/27
bosqichda, har uch takrorda yiqilgan va 8 bosqichda Y1 sikli ham bor.

**Qayta o‘lchash.** Kod o‘zgargani uchun kalit yangilanadi; to‘liq pass
qaytadan o‘lchanadi. Bu bir vaqtning o‘zida D63c ning talabini ham bajaradi:
`20261016-093916` natijasida `deep_chain/100000` bloki bosim belgisi bilan
o‘lchangan (eng past `MemAvailable` 2,64 GB, `SwapFree` 1 MB). Birinchi
natija o‘chirilmaydi — u solishtirish uchun qoladi va “tekshiruvning
tartibga bog‘liq versiyasi bilan o‘lchangan” deb belgilanadi.


---

### D63h — qayta o‘lchash tanlab: faqat bosimdagi blok va parallel bosqichlar (2026-10-19, bajarish Junyi'dan keyin)

**Qaror (foydalanuvchi).** Avval Junyi (B qismi), H4 ning qayta o‘lchashi
keyin va **faqat tanlab**. To‘liq pass (≈ 6 soat) takrorlanmaydi.

**Nima qayta o‘lchanadi.**

- **(a) `deep_chain/100000` bloki** — butunligicha. `20261016-093916` da D63c
  bayrog‘i olgan **yagona** blok (eng past `MemAvailable` 2,64 GB,
  `SwapFree` 1 MB).
- **(b) barcha to‘qqiz blokning parallel bosqichi** — qulfsiz (2/4/8) va
  qulfli (8), D63g da tuzatilgan yaxlitlik tekshiruvi bilan. Parallel yozishdan
  keyingi daraxt saqlanmagan, shuning uchun tekshiruvni qayta ishlatib
  bo‘lmaydi — bosqichning o‘zi qayta o‘tkaziladi.

**Nima qayta o‘lchanmaydi.** Qolgan hamma katak — sakkiz blokning oltita
amali (ρ, mediana, p95, SQL soni, o‘zgargan qatorlar) — `20261016-093916`
natijasidan olinadi. Ular bosimsiz o‘lchangan va D63g ularga tegmaydi
(tuzatish faqat yaxlitlik tekshiruvida).

**Asosiy jadvalda nima turadi.**

- (a) uchun: **qayta o‘lchangan son** asosiy, birinchisi yonida (“bosim
  ostida”), ikkalasi orasidagi farq yoziladi (D63c).
- (b) uchun: **qayta tekshirilgan yaxlitlik** asosiy. O‘tkazuvchanlik (op/s)
  uchun esa birinchi pass'ning soni asosiy qoladi — D63g tekshiruvi bosqich
  **tugagandan keyin** ishlaydi, ya’ni o‘lchangan op/s ga ta’sir qilmagan;
  qayta o‘tkazilgan bosqichning op/s i yonida, solishtirish uchun beriladi.
  Istisno — `deep_chain/100000`: u (a) bo‘yicha butunligicha qayta
  o‘lchangani uchun uning op/s i ham yangi pass'dan olinadi.

**Kutiladigan natija (oldindan aytiladi, natijani o‘zgartirish uchun emas).**
`deep_chain/100000` dagi bosimni benchmark'ning o‘zi — CTE ning chuqur
zanjirdagi o‘qishi — yaratgan (D63f). Qayta o‘lchashda o‘sha kataklar yana
`statement_timeout` yoki xotira chegarasiga urilishi kutiladi va bu
“ishga tushirilmadi — xotira” / “timeout” bo‘lib qoladi; bu D63 qoidasini
o‘zgartirishga sabab emas.

**Kod.** Runner'da shakl va hajm filtri bor (`--shapes deep_chain --sizes
100000`) — (a) uchun yetadi. **Faqat parallel bosqichni** ishga tushiradigan
filtr yo‘q: u (b) dan oldin `--only-parallel` bayrog‘i sifatida qo‘shiladi
(amallar o‘tkazib yuboriladi, daraxt quriladi, parallel bosqich va yaxlitlik
tekshiruvi bajariladi) va test bilan qotiriladi. Kod o‘zgargani uchun
checkpoint kaliti yangilanadi — bu kutilgan.

**Boshlanish sharti** D63c dagidek (`MemAvailable ≥ 6 GB`, swap `< 200 MB`).


---

## 9-bosqich kodi — `benchmarks` app'i va H4 (2026-10-12, natijadan oldin)

D63 va D63a bo‘yicha yozildi. **Dissertatsiya natijasi yo‘q**: to‘liq run hali
ishga tushirilmagan (quyida `--quick` bor, u natija emas).

### Modullar

| Fayl | Nima qiladi |
|---|---|
| `benchmarks/models.py` | `MpttNode` (oraliq kodlash) va `CteNode` (platformaning o‘z usuli: `TreeNode`, `TreeQuerySet`, `(position, id)` tartibi) |
| `benchmarks/routers.py` | `benchmarks` app'i faqat `benchmark` alias'ida, boshqa hech narsa u yerda emas (ikki yo‘nalishda) |
| `benchmarks/generator.py` | uchta shakl (seed bilan), bitta `parent_id` ketma-ketligidan ikkala jadval, MPTT oraliqlari Python'da (`rebuild()` o‘rniga, test bilan tengligi tasdiqlangan), `parent_id` ketma-ketligining sha256'si |
| `benchmarks/operations.py` | oltita amal, har biri kutubxona hujjatidagi usulda; juftlashtirilgan nishonlar; CTE ko‘chirishida platformaning Y1 tekshiruvi (D63a) |
| `benchmarks/parallel.py` | 2/4/8 jarayon, har biri o‘z ulanishi bilan; qulfsiz va qulfli (`pg_advisory_xact_lock`) variantlar; xatolar turlari bo‘yicha sanaladi |
| `benchmarks/integrity.py` | Y1 (sikl, ildiz, dangling) ikkala usulda; MPTT uchun `lft < rght`, ichma-ichlik, takroriy chegaralar, `level`, qayta hisoblash bilan solishtirish |
| `benchmarks/runner.py` | o‘lchov tartibi (5+30, timeout, orqaga qaytarilgan tranzaksiya), ρ va juftlashtirilgan bootstrap, o‘qish qoidasi, checkpoint, CSV |
| `benchmarks/management/commands/run_tree_benchmark.py` | buyruq, ikki darvoza (dev bazasi emas; PostgreSQL) |
| `scripts/dj5433.sh` | DSN'ni konteyner muhitidan yasaydi, `config/.env` o‘qilmaydi va parol chiqmaydi |

O‘zgargan: `config/settings.py` (`mptt` va `benchmarks` INSTALLED_APPS'da,
`DATABASES["benchmark"]`, router), `experiments/tables.py`
(`render_tree_benchmark_report` va pozitsion tekshiruv), `experiments/run_h2.sh`
(`bench-quick|bench-full|bench-both`, skript rejimi va Django venv'i).

**Dev bazasiga tegilmadi.** Benchmark `neurolearn_bench` bazasida ishlaydi;
router dev bazasida `benchmarks_*` jadvallari paydo bo‘lishiga yo‘l qo‘ymaydi
(tekshirildi: dev bazasida 0 ta shunday jadval), buyruq esa alias dev bazasiga
tushsa to‘xtaydi (test bilan). Hech bir jadval o‘chirilmadi yoki tozalanmadi.

### Testlar

`benchmarks/tests`: **69 passed** (`scripts/dj5433.sh venv/bin/python -m pytest
benchmarks/tests`). Butun backend suite: **1206 passed, 51 skipped, 13
subtests** (4 daq 57 s); `experiments/.venv` da experiments suite: **393
passed, 2 skipped** (7 daq 59 s). `manage.py check` toza,
`makemigrations --check` — “No changes detected”.

Har bir yaxlitlik tekshiruvi ikki marta sinaladi: toza daraxtda o‘tadi,
ataylab buzilgan daraxtda (xom SQL bilan) yiqiladi. `generator.intervals`
mptt ning `rebuild()` i bilan uchta shaklda aynan teng — shuning uchun
100 000 tugunli daraxtda `rebuild()` ni chaqirmaslik tekshirilgan qisqartma,
taxmin emas.


## QADAM 8 — H4 benchmarki: `--quick` (2026-10-12, dissertatsiya natijasi emas)

### Ishga tushirishlar

| Run | Commit | Holat |
|---|---|---|
| `--quick` (1-urinish) | `2a8d1dc` | **ishlatilmaydi** — `deep_chain` ning `delete_branch` katagi `RecursionError` bilan tugadi (D63b shundan keldi); natija papkasi `feat(bench)` commit'iga tasodifan kirib qolgan va `4e9f2b9` da olib tashlandi |
| `--quick` (2-urinish) | `c420209` | **ishlatilmaydi** — o‘sha o‘chirish hali commit qilinmagan edi, shuning uchun provenance D54 ogohlantirishi bilan chiqdi |
| `--quick` (3-urinish) | `c420209` → natija `4e9f2b9` da toza daraxtdan | **saqlandi** — `experiments/results/tree-benchmark-quick/20261012-131931/`, `git_start`/`git_end` ikkalasi ham toza, `tables.verify` va pozitsion tekshiruv `[]` |

Sozlama: 10³ tugun, uchta shakl, 2 qizdirish + 5 takror, parallel 2/4 jarayon
× 5 s × 2 takror, timeout 120 s. Muhit: PostgreSQL 16.15 (Debian), 16 mantiqiy
yadro, governor **`powersave`** — absolyut vaqtlar shuning uchun past, lekin
da’vo nisbat (ρ) ustiga qurilgan.

### Nima ko‘rindi (quvur ishlayotganining dalili, natija emas)

Yozish amallarida CTE ustun: `course_like` da oxiriga barg ρ = 10,90,
eng chapga barg ρ = 11,55, ko‘chirish ρ = 2,11, o‘chirish ρ = 5,41 (hammasi
CI si 1 dan yuqori). `random` da ham shunday (1,58 … 9,58). **`deep_chain`
boshqacha**: ko‘chirish ρ = 0,11 va o‘chirish ρ = 0,87 — ya’ni 1 000 chuqur
zanjirda CTE ning Y1 tekshiruvi (rekursiv CTE, D63a) ko‘chirishni MPTT dan
sekin qiladi.

O‘qish amallarida MPTT ustun va farq katta: `course_like` ρ = 0,31 / 0,18,
`random` ρ = 0,25 / 0,15, `deep_chain` ρ = 0,019 / 0,025. D63 ning 1,5
chegarasidan oltita katak chiqdi.

Parallel yozish: **qulfsiz** variantda MPTT ning yaxlitligi har bir shakl va
jarayon sonida buzildi (Y1 va oraliqlar), CTE da esa faqat Y1 tekshiruvi bor
va u ushlab turdi; o‘tkazuvchanlik 4 jarayonda MPTT da 1,5–2 op/s ga tushdi
(oraliqlarni qayta yozish bilan to‘qnashuvlar), CTE da 184–487 op/s.
**Qulfli** variantda ikkala usul ham yaxlitligini saqladi va o‘tkazuvchanlik
tenglashdi (ρ 0,19 … 1,07).

Shu sozlamada o‘qish qoidasining xulosasi: **qo‘llab-quvvatlanmadi** (oltita
o‘qish katagi va `deep_chain` ning ikki yozish katagi sababli). **Bu
dissertatsiya natijasi emas**: 10³ tugun, 5 takror. To‘liq run 10³, 10⁴ va 10⁵
hajmlarda, 30 takror bilan ishga tushiriladi.


## QADAM 9 — H4 ning birinchi to‘liq run'i (2026-10-16)

### Ishga tushirish

| | |
|---|---|
| Unit | `neurolearn-h2-bench-full-20261016-085158` |
| Commit | `b8d6b3a`, `git_start`/`git_end` ikkalasi ham **toza** |
| Vaqt | 08:51:58 → 14:39:16 (**5 soat 47 daqiqa**), `finished bench-full (exit 0)` |
| Natija | `experiments/results/tree-benchmark/20261016-093916/` (`cb7aec4`) |
| Tekshiruvlar | `tables.verify` = [] va pozitsion tekshiruv = [] |
| Chegaralar | xotira capi 8 GiB, `statement_timeout` 120 000 ms (D63f) |
| Muhit | PostgreSQL 16.15, `shared_buffers` 128MB, `fsync` on, `synchronous_commit` on; i7-11800H, 16 mantiqiy yadro, governor **`powersave`**; RAM 14,89 GB, boshida bo‘sh 6,82 GB |

To‘qqizta blokning sakkiztasi **bosimsiz** o‘lchandi; `deep_chain/100000`
bloki D63c belgisini oldi (eng past `MemAvailable` 2,64 GB, `SwapFree` 1 MB)
— u qayta o‘lchanadi. Uzilish (D63e) hech bir blokda yo‘q.

### 1. Amallar: ρ = mediana(MPTT) / mediana(CTE)

ρ > 1 — CTE tezroq. Oraliq — juftlashtirilgan bootstrap (1 000 replika, 95 %).

| Shakl | Hajm | shox o‘qish | ajdod o‘qish | oxiriga barg | eng chapga barg | ko‘chirish | o‘chirish |
|---|---|---|---|---|---|---|---|
| kursga o‘xshash | 10³ | 0,33 | 0,17 | 5,65 | 5,13 | 1,88 | 2,97 |
| kursga o‘xshash | 10⁴ | 0,07 | 0,04 | 57,66 | 55,53 | 3,38 | 22,06 |
| kursga o‘xshash | 10⁵ | 0,02 | 0,006 | 410,00 | 595,25 | 1,15 | 134,62 |
| chuqur zanjir | 10³ | 0,02 | 0,03 | 8,90 | 13,59 | **0,13** | **0,92** |
| chuqur zanjir | 10⁴ | 0,002 | 0,002 | 48,42 | 96,07 | **0,010** | **0,86** |
| chuqur zanjir | 10⁵ | **xotira** | **xotira** | 412,09 | 1 240,00 | **timeout** | **0,82** |
| tasodifiy | 10³ | 0,27 | 0,17 | 10,06 | 10,23 | 1,98 | 4,44 |
| tasodifiy | 10⁴ | 0,05 | 0,03 | 70,99 | 70,95 | 2,72 | 35,44 |
| tasodifiy | 10⁵ | 0,006 | 0,003 | 679,14 | 764,18 | **0,76** | 283,02 |

Qalin yozilganlar — CTE **sekinroq** yoki son chiqmagan kataklar. Hamma
kataklarning CI si `tables.md` §1 da; 54 katakdan 51 tasida CI 1 ni kesmaydi
(ya’ni “taqqoslanadigan” faqat `deep_chain/1000` ning o‘chirishida).

**Son chiqmagan uchta katak** (`deep_chain/100000`): shox o‘qish va ajdod
o‘qish — **“ishga tushirilmadi — xotira”** (CTE ning rekursiv CTE'si har
qatorda ajdodlar massivini olib yuradi, 10⁵ chuqurlikda bu mashinaga
sig‘maydi: o‘lchangan o‘sish 2 000 → 0,86 s / 0,25 GB, 10 000 → 22,3 s /
4,50 GB); ko‘chirish — **“timeout”** (serverdagi 120 s chegarasi, D63f).
Taxmin yozilmadi.

### 2. Parallel yozish

Qulfsiz variantda 2/4/8 jarayon, qulfli variantda 8 jarayon (D63a), har biri
3 takror × 20 s. O‘tkazuvchanlik (op/s) va yaxlitlik:

| Shakl | Hajm | 2 (CTE/MPTT) | 4 (CTE/MPTT) | 8 (CTE/MPTT) | 8 qulfli (CTE/MPTT) |
|---|---|---|---|---|---|
| kursga o‘xshash | 10³ | 207,5 / 136,0 | 278,4 / 1,8 | 317,1 / 1,3 | 132,0 / 98,8 |
| kursga o‘xshash | 10⁴ | 115,1 / 3,5 | 199,4 / 2,6 | 266,0 / 0,9 | 65,5 / 9,9 |
| kursga o‘xshash | 10⁵ | 5,8 / 0,6 | 10,9 / 0,6 | 16,7 / 0,7 | 3,7 / 1,1 |
| chuqur zanjir | 10³ | 110,3 / 128,0 | 194,1 / 1,6 | 283,3 / 0,9 | 75,0 / 117,0 |
| chuqur zanjir | 10⁴ | 0,4 / 3,5 | 0,7 / 1,7 | 0,8 / 0,7 | 0,2 / 7,8 |
| chuqur zanjir | 10⁵ | 0,0 / 0,8 | 0,0 / 0,6 | 0,1 / 0,4 | 0,1 / 1,1 |
| tasodifiy | 10³ | 196,8 / 151,8 | 262,1 / 1,5 | 333,9 / 1,5 | 122,0 / 130,9 |
| tasodifiy | 10⁴ | 91,3 / 3,1 | 122,6 / 1,3 | 168,4 / 1,0 | 48,5 / 11,4 |
| tasodifiy | 10⁵ | 2,5 / 1,0 | 4,8 / 0,5 | 7,7 / 0,4 | 1,8 / 1,0 |

**Yaxlitlik.** Qulfsizda MPTT **27 bosqichning 27 tasida** buzildi va bu
tartibdan mustaqil invariantlar bo‘yicha (har uch takrorda): `lft < rght`,
ota oralig‘i ichida joylashish, takroriy chegaralar, `level`; sakkizta
bosqichda bundan tashqari **Y1 sikli** topildi. CTE qulfsizda 27 bosqichdan
26 tasida yaxlitligini saqladi (yagona istisno — `deep_chain/1000` ×8).
Qulfli variantda **CTE hamma joyda toza**.

Qulfli variantda MPTT to‘rtta bosqichda “buzildi” deb chiqqan edi, lekin bu
**tekshiruvning soxta ijobiysi** (D63g): o‘sha to‘rttasida faqat
`differs_from_rebuild` nolmas, tartibdan mustaqil invariantlar toza, va
hammasi qayta hisoblash yo‘li bilan tekshirilgan. Sabab — qayta hisoblash
birodarlarni pk tartibida yurgani; o‘lchangan: qonuniy `move_to` dan keyin
mptt ning `rebuild()` i 0 farq, qayta hisoblash 16 farq ko‘rsatadi. Tuzatildi
(`5e34934`).

### 3. D63 ning uchta sharti

| # | Shart | Bajarildimi | Qaysi kataklar |
|---|---|---|---|
| 1 | To‘rtta yozish amali **har** shakl va hajmda “CTE tezroq” | **yo‘q** | `deep_chain` ning ko‘chirishi (10³, 10⁴) va o‘chirishi (10³, 10⁴, 10⁵), `random/100000` ning ko‘chirishi |
| 2 | O‘qishda hech bir katakda CTE 1,5 barobardan ko‘proq sekin emas | **yo‘q** | 16 katak (barcha shakl va hajmlardagi ikkala o‘qish amali, `deep_chain/100000` dan tashqari — u son bermadi) |
| 3 | Parallel yozishdan keyin **qulfli** variantda CTE yaxlitligi buzilmagan | **ha** | buzilish yo‘q (12 qulfli bosqichning hammasida) |

**Umumiy xulosa: H4 qo‘llab-quvvatlanmadi.** Da’voning yozish qismi
kursga o‘xshash va tasodifiy shakllarda kuchli tasdiqlandi (ρ 1,15 … 764), ya’ni
**platformaning haqiqiy shakli** (kurs daraxti) uchun CTE yozishda bir necha
yuz barobar tezroq; lekin chuqur zanjirda ko‘chirish va o‘chirish MPTT
tomonida, va o‘qishda CTE hamma joyda sezilarli sekin.

**Alohida qator (qulfli o‘qish qoidasidan qat’i nazar):** qulfsiz parallel
yozishda **MPTT ning yaxlitligi har bir shakl, hajm va jarayon sonida
buzildi** — oraliq kodlash denormalizatsiya bo‘lgani uchun; CTE da
buziladigan ikkinchi nusxa yo‘q va uning Y1 tekshiruvi 27 dan 26 tasida
ushlab turdi. Platformaning yo‘li (advisory lock) ikkala usulni ham
yaxlit saqlaydi.

### 4. `--quick` ning uchta urinishi

| Urinish | Commit | Nega saqlanmadi / saqlandi |
|---|---|---|
| 1 (`20261012-113208`) | `2a8d1dc` | **texnik**: `deep_chain` ning `delete_branch` katagi `RecursionError` bilan tugadi (Django ning CASCADE kollektori har daraja uchun bitta freym; D63b shundan keldi) — katakda son yo‘q edi. Papka `feat(bench)` commit'iga tasodifan kirib qolgan va `4e9f2b9` da olib tashlandi |
| 2 (`20261012-113917`) | `c420209` | **texnik**: o‘sha o‘chirish hali commit qilinmagan edi, shuning uchun provenance D54 ogohlantirishi bilan chiqdi (`git_start.dirty = true`) — natija bitta kod holatidan ekani kafolatlanmaydi |
| 3 (`20261012-131931`) | `c420209`, commit `c12221c` | **saqlandi**: toza daraxtdan, ikkala uchida toza provenance, `tables.verify` va pozitsion tekshiruv [] |

Ikkala tashlangan urinish ham **natijasi yoqmagani uchun emas**, quvurning
texnik holati uchun tashlandi: birinchisida son chiqmagan katak bor edi,
ikkinchisida provenance kafolati yo‘q edi. Uchalasining ham xulosasi bir xil
(“qo‘llab-quvvatlanmadi”) edi.

### 5. Keyingi qadam

Natija **qayta o‘lchanadi** (D63c va D63g): `deep_chain/100000` bosim ostida
o‘lchangan, va yaxlitlik ustuni tartibga bog‘liq tekshiruv bilan olingan.
`20261016-093916` o‘chirilmaydi — u solishtirish uchun qoladi; qayta
o‘lchangan pass asosiy natija bo‘ladi. Vaqt o‘lchovlari (ρ) D63g dan
mustaqil, shuning uchun yuqoridagi ρ jadvali katta o‘zgarishga uchramaydi
deb kutiladi, lekin asosiy son yangi pass'dan olinadi.


## D61a / D62a — Junyi log'i, N va H1/H3 ning qolgan qarorlari (2026-10-19, kod va natijadan oldin)

### D61a — log va N

**Arxiv va ajratish.** `experiments/data/junyi.rar` — 1 295 551 222 bayt
(D61 dagi hajm), RAR5, sha256 `7335386710db473a475ac47f6049ab8f1031bb703e6937f2d5529b46293ff35e`.
`bsdtar 3.8.5` (libarchive 3.8.5) bilan **faqat**
`junyi_ProblemLog_original.csv` ajratildi (16 s): 2 668 566 436 bayt,
sha256 `a7c99ede1f9b19648fdcd953b6ca0b0282bd31f2f913bd9d26b23aa9fcb36a25`.
`junyi_ProblemLog_for_PSLC.txt` (9 728 744 960 bayt) **ochilmadi**.

**Inventarizatsiya (loyihaning o‘z yuklovchisi bilan o‘lchangan,
`junyi.inventory`, `verify=True`).**

| Ko‘rsatkich | Qiymat |
|---|---|
| qatorlar | **25 925 992** (hujjat: 25 925 992 — mos) |
| talabalar | **247 606** (hujjat: 247 606 — mos) |
| graf mashqlariga tegishli qatorlar | 25 925 992 — **100 %** (javob berilgan 722 mashqning hammasi mashqlar jadvalida; 835 tadan 113 tasiga javob yo‘q) |
| talaba boshiga javoblar | min 1, kvartillar 3 / 10 / 50, p90 220, p99 1 671, max 22 067, o‘rtacha 104,7 |
| mashq boshiga javoblar | min 1, kvartillar 2 122,5 / 8 474,5 / 34 558,3, p90 97 733, p99 396 478, max 895 736, o‘rtacha 35 908,6 |
| to‘g‘ri javoblar | 82,79 % |
| `live=FALSE` mashqlarga javoblar | 338 987 — **1,31 %** |
| `suggested` (platforma tavsiya qilgan) | 5 327 335 — **20,55 %** |
| `topic_mode` | 6 458 171 — 24,91 % |
| `review_mode` | 554 570 — 2,14 % |
| `earned_proficiency=true` qatorlar | 1 194 299 — 4,61 % |

**N jadvali** (seed `20261006`, talaba darajasida tanlov — run'ning o‘z
`select_learners` i bilan; H1 voqeasi — D62-5; H3 voqeasi — mashqning
dastlabki 3 urinishi, birinchi urinishdan oldin kamida bitta prerekvizit
ishlangan):

| N | javoblar | moslash to‘plami (0,8×) | H1 voqealari | H3 voqealari (javob) | fold fit bahosi |
|---|---|---|---|---|---|
| **2 000** | 252 737 | 202 190 | **9 664** | 26 938 | ≈ 37 daq |
| 5 000 | 524 196 | 419 357 | 19 525 | 54 200 | ≈ 76 daq |
| 8 000 | 798 988 | 639 190 | 29 713 | 82 249 | ≈ 116 daq |

Fit bahosi D61 dagi o‘lchovdan: 2,3 µs × javob × 4 752 nomzod.

**Qoida va tanlov.** H1 voqealari ≥ 5 000 bo‘lib, hisob vaqti (D61: moslash
to‘plami 270 000 ± 30 %, ya’ni fold fit ≈ 50 daqiqa atrofida) va xotira
chegarasida qoladigan **eng kichik N, 2 000 dan boshlab**. N = 2 000: H1
voqealari 9 664 ≥ 5 000 va moslash to‘plami 202 190 — oraliq ichida (−25 %).
Demak **N = 2 000** — D61 dagi qiymat o‘zgarmaydi. (D61 namunadan 336 000
javob kutgan edi; haqiqiy 252 737 — tanlovdagi talabalar o‘rtacha 126 ta
javob bergan, butun log bo‘yicha 104,7.)

### D62a — H1/H3 ning qolgan qarorlari

**(b) H3 ning tasodifiy arm'i.** Kontrast “asl − tasodifiy” statistikasi: har
bootstrap replikatida **20 seed'ning har biri uchun AUC** shu replikatdagi
javoblarda hisoblanadi va **o‘rtachalanadi**; bashoratlar o‘rtachalanmaydi.
Qo‘shimcha (o‘qish qoidasiga kirmaydi, tavsifiy): (i) asl grafning nuqtaviy
AUC'i 20 seed'ning **maksimumidan** yuqorimi (ha/yo‘q); (ii) bootstrap
replikatlarining qancha ulushida asl AUC 20 seed maksimumidan yuqori.

**(c) H1 ning `earned_proficiency` qoidasi** faqat voqeadan **qat’iy oldingi**
qatorlardan olinadi (talabaning oqimi tartibida: `time_done`, keyin
`problem_number`, keyin fayl tartibi). Voqea qatorining o‘z bayrog‘i va
undan keyingi qatorlar hech qachon ishlatilmaydi. Test bilan qotiriladi.

**(d) H1 sezgirligi.** Qo‘shimcha ustun: faqat w da **kamida k ta javobi
bor** voqealar bo‘yicha xato ulushi va qamrov (k = 3 va 5). Asosiy qoida
(D62-6: k tadan kam javobli voqea mavjud javoblari bo‘yicha baholanadi)
o‘zgarmaydi.

**(e) Holm oilalari.** H1 — ehtimoliy qoidaning ikki taqqoslashi
(bajarilganlik va o‘tish bali bilan) **bitta oila**; p qiymat bootstrap
taqsimotidan, ikki tomonlama: p = 2 · min(P(Δ* ≤ 0), P(Δ* ≥ 0)). H3 — uch
kontrast (teskari, tasodifiy, grafsiz) **har k uchun alohida oila** (k = 3 va
k = 5). Holm tuzatilgan p jadvalda beriladi; **D61 ning o‘qish qoidasi
(95 % CI nolni kesmasligi) o‘zgarmaydi**.

**(f) Cheklov.** Junyi platformasi mashqni uning prerekvizitlari
o‘zlashtirilgach **tavsiya qiladi** (`suggested`, butun log'ning 20,55 %):
talabalar w ga ko‘pincha platforma ularni yuborgani uchun keladi. Shuning
uchun H1 va H3 dagi ta’sirning bir qismi grafning “o‘zidan” emas,
platformaning shu graf bo‘yicha **yo‘naltirishidan** kelishi mumkin. Bu
cheklov H1/H3 natijalarining metadata'siga va o‘qish qoidasining “scope”
matniga yoziladi; tanlangan namunadagi `suggested` ulushi ham metadata'da
turadi.

**Kod nimani o‘zgartiradi (bu qarorlar asosida).** (b) “asl > 20 seed
maksimumi” qo‘shiladi (asosiy statistika allaqachon shunday hisoblanadi);
(c) kod allaqachon shunday, test qo‘shiladi; (d) yangi ustun; (e) H1 ga
bootstrap p va Holm qo‘shiladi, H3 da oila allaqachon har k uchun — test
bilan tasdiqlanadi; (f) metadata va scope matni.


### D64 — H3 ning D54 ogohlantirishi qabul qilinadi; untracked natija papkalari kod o‘zgarishi emas (2026-10-19)

**Holat.** To‘liq H3 natijasi (`experiments/results/junyi-h3/20261019-122423/`)
D54 ogohlantirishi bilan yozilgan: “ishchi daraxt ishga tushirish boshida
toza emas edi”. Provenance'da: `git_start` va `git_end` commit'i bir xil
(`2500c77`), ikkala uchidagi **yagona** o‘zgarish —
`?? experiments/results/junyi-h1/`, ya’ni `junyi-full` zanjirining birinchi
bosqichi yozgan, hali commit qilinmagan H1 natija papkasi.

**H3 uni o‘qimaydi (koddan).** `h3.py` da natijalarga yagona murojaat —
`results_dir(...)` (h3.py:828), u yoziladigan yo‘lni hisoblaydi; kirish
fayllari faqat mashqlar jadvali va log (h3.py:771–772; junyi.py:314, 915);
parametr fit yo‘li `h2.fit_parameters` → `h2_bounds.fit_all` → `_fit_task`
→ `fit_skill_params` (h2.py:149–151, h2_bounds.py:296–302) fayl o‘qimaydi,
`load_reference` (h2_bounds.py:360) faqat `h2_bounds.run` dan chaqiriladi
(:566); launcher H3 ga faqat `--workers` uzatadi (run_h2.sh:191).

**Qaror (foydalanuvchi, (a)).** H3 natijasi **qayta ishga tushirilmaydi va
qabul qilinadi**. Ogohlantirish natijaning metadata'sida **o‘zgarmasdan**
qoladi; bu yozuv uning sababini va nega natijaga ta’sir qilmaganini aytadi.
H1 natijasi (`20261019-102526`) ikkala uchida toza.

**Kelajak uchun.** Provenance `git status --porcelain` qatorlaridan
**`experiments/results/` ostidagi untracked (`??`) papka va fayllarni** kod
o‘zgarishi deb hisoblamaydi: ular alohida `untracked_results` ro‘yxatiga
yoziladi va `dirty`, `same_tree` va checkpoint'ning yoqilishiga ta’sir
qilmaydi. **Boshqa har qanday o‘zgarish avvalgidek dirty**, jumladan
commit qilingan natija faylining o‘zgarishi (`M experiments/results/...`) —
u natijani tahrirlash, D48 ning aynan qo‘riqlaydigan narsasi. Test bilan
qotiriladi. **Eski natijalarning metadata'si o‘zgartirilmaydi.**


## QADAM 10 — H1 va H3 Junyi'da (2026-10-19)

### Ishga tushirish

| | |
|---|---|
| Unit | `neurolearn-h2-junyi-full-20261019-144748` (`junyi-full`: avval H1, keyin H3), 5 worker |
| Commit | `2500c77` (ikkala bosqich) |
| H1 | 14:47:48 → 15:25:26, `exit 0`; `experiments/results/junyi-h1/20261019-102526/` (`abc8c5a`); provenance ikkala uchida **toza** |
| H3 | 15:25:26 → 17:24:23, `exit 0`; `experiments/results/junyi-h3/20261019-122423/` (`ac632d3`); D54 ogohlantirishi bilan — **D64** bo‘yicha qabul qilingan |
| Tekshiruvlar | ikkalasida `tables.verify` = [] va pozitsion tekshiruv = [] |
| Ma’lumot | 2 000 talaba (seed `20261006`), 252 737 javob; `suggested` ulushi namunada 0,2175 |

### H1 (τ = 0,95, δ = 0,10, `pass_mark` = 0,60, k = 3)

Voqealar: **9 664** (695 talaba, 504 mashq; 7 136 tasida barcha
prerekvizitlar ishlangan; o‘rtacha 1,581 prerekvizit).

| Qoida | Belgilangan | Qamrov | Xato ulushi |
|---|---|---|---|
| ehtimoliy (r ≥ τ) | 6 795 | 0,7031 | 0,1506 |
| II bob R (M, δ) | 6 803 | 0,7040 | 0,1510 |
| bajarilganlik | 7 136 | 0,7384 | 0,1666 |
| o‘tish bali | 9 239 | 0,9560 | 0,1527 |
| earned_proficiency (qo‘shimcha) | 6 532 | 0,6759 | 0,1464 |

Teng qamrov (τ validatsiyada; farq = ehtimoliy − qoida):

| Taqqoslash | τ (fold'lar) | Qamrov (ehtim. / qoida) | Farq [95 % CI] | p | Holm p | ≥ k javob: xato (ehtim. / qoida), voqea |
|---|---|---|---|---|---|---|
| bajarilganlik, k=3 | 0,028 / 0,007 / 0,006 / 0,009 / 0,017 | 0,7379 / 0,7384 | −0,000023 [−0,000336; 0,000193] | 0,92 | 0,92 | 0,1303 / 0,1303, 8 384 |
| o‘tish bali, k=3 | 0 / 0 / 0 / 0 / 0 | 1,0000 / 0,9560 | **+0,016669** [0,011738; 0,021936] | 0,000 | 0,000 | 0,1308 / 0,1207, 8 384 |
| bajarilganlik, k=5 | (o‘sha) | 0,7379 / 0,7384 | −0,000042 [−0,000353; 0,000162] | 0,832 | 0,832 | 0,0890 / 0,0891, 8 005 |
| o‘tish bali, k=5 | (o‘sha) | 1,0000 / 0,9560 | **+0,016449** [0,011813; 0,021625] | 0,000 | 0,000 | 0,0874 / 0,0783, 8 005 |

r_s(w) AUC: k = 3 — **0,5195** [0,5012; 0,5372] (1 637 muvaffaqiyatsiz);
k = 5 — 0,5232 [0,5038; 0,5421].

τ × δ (II bob R, k = 3): qamrov 0,7037–0,7093, xato ulushi 0,1510–0,1520
butun to‘rda; r ≥ τ qamrovi 0,7031–0,7085, xato ulushi 0,1506–0,1519.

**O‘qish qoidasi: qo‘llab-quvvatlanmadi.** Belgilagan shart — o‘tish bali
bilan taqqoslash: CI [0,011738; 0,021936] **nolning musbat tomonida**
(ehtimoliy qoida ko‘proq xato qiladi). Bajarilganlik bilan — aniqlanmadi
(CI nolni kesadi).

### H3 (BKT+IRT+Pre, 4 graf; 20 tasodifiy graf, hammasi qayta ulangan)

| k | asl | teskari | tasodifiy (20): o‘rtacha / min / max | grafsiz |
|---|---|---|---|---|
| 3 | 0,7824 [0,7755; 0,7891] | 0,7816 [0,7741; 0,7886] | 0,7772 / 0,7757 / 0,7785 (1-seed CI [0,7682; 0,7827]) | 0,7836 [0,7765; 0,7905] |
| 5 | 0,7924 [0,7859; 0,7986] | 0,7917 [0,7851; 0,7980] | 0,7881 / 0,7869 / 0,7894 (1-seed CI [0,7802; 0,7932]) | 0,7936 [0,7869; 0,7998] |

Butun to‘plam AUC: asl 0,7716, teskari 0,7704, tasodifiy-1 0,7675, grafsiz
0,7724. Javoblar: k = 3 — 54 798, k = 5 — 84 143.

| k | Kontrast | Farq [95 % CI] | DeLong p | Holm p |
|---|---|---|---|---|
| 3 | asl − teskari | +0,000806 [−0,000238; 0,001980] | 0,0749 | 0,0749 |
| 3 | asl − tasodifiy | **+0,005244** [0,004439; 0,006126] | 0,0000 | 0,0000 |
| 3 | asl − grafsiz | −0,001210 [−0,002459; 0,000106] | 0,0073 | 0,0146 |
| 5 | asl − teskari | +0,000719 [−0,000005; 0,001533] | 0,0198 | 0,0198 |
| 5 | asl − tasodifiy | **+0,004366** [0,003807; 0,005004] | 0,0000 | 0,0000 |
| 5 | asl − grafsiz | **−0,001166** [−0,002042; −0,000228] | 0,0002 | 0,0005 |

(DeLong tasodifiy oila uchun medianasi bo‘lgan arm — `tasodifiy-13` — ga qarshi.)

Asl > eng yaxshi tasodifiy: ikkala k da **ha**, replikatlarning **1,000**
ulushida. λ (validatsiyada): **0,25** — har fold'da va asl, teskari,
tasodifiy-1 arm'larida (gridning eng past qiymati).

**O‘qish qoidasi: k = 3 — aniqlanmadi, k = 5 — qo‘llab-quvvatlanmadi.**
Belgilagan kontrast: k = 5 da asl − grafsiz, CI [−0,002042; −0,000228]
nolning **manfiy** tomonida. Asl − tasodifiy ikkala k da qo‘llab-quvvatlaydi,
asl − teskari ikkala k da aniqlanmadi.

### Ikkalasi uchun (post-hoc, natija metadata'sida yo‘q)

Quyidagi ikki son run'ning o‘z yuklovchisi, seed'i va bo‘linishi bilan
keyin hisoblangan (fold parametrlari modelga tayyor holda uzatilgani uchun
standart parametr soni `metrics.json` ga yozilmagan; `suggested` bayrog‘i
`Answer` da yo‘q). Hisobning izchilligi: H1 voqealari soni 9 664 — run bilan
aynan mos.

- **Standart parametrda qolgan mashqlar** (moslash to‘plamida < 50 javob):
  fold'lar bo‘yicha 201 / 203 / 191 / 196 / 208 (javob berilgan 604–615
  mashqdan); test javoblarining shu mashqlarga tushgan ulushi 4,56 / 4,80 /
  1,85 / 2,37 / 4,13 %, pooled **3,63 %**. (Grid qidiruv `None` qaytargan
  kamdan-kam hol bu sanoqqa kirmaydi.)
- **H1 voqealarida `suggested` ulushi:** 3 093 / 9 664 = **0,3201**
  (butun namunada 0,2175).


## QADAM 11 — H4 ning tanlab qayta o‘lchanishi (D63h, 2026-10-19/20)

### Ishga tushirishlar (hammasi `9f97aa7`, ikkala uchida toza)

| Qism | Unit | Vaqt | Natija |
|---|---|---|---|
| (b) parallel, `course_like` + `random` | `…-bench-reselect-parallel-20261019-201708` | 20:17 → 21:14 | `tree-benchmark/20261019-161430` |
| (b) parallel, `deep_chain` 10³/10⁴ | o‘sha unit, 2-chaqiruv | 21:14 → 21:34 | `tree-benchmark/20261019-163435` |
| (a) `deep_chain/100000` butun | `…-bench-reselect-block-20261020-085302` | 08:53 → 10:04 | `tree-benchmark/20261020-050428` |

Uchalasida `tables.verify` = [] va pozitsion tekshiruv = []; keyingi
chaqiruvlar oldingisining commit qilinmagan papkasi yonida boshlangan va
provenance uni `untracked_results` ga yozgan (D64). (a) da 72 namuna,
180 s dan katta tanaffus yo‘q (D63e belgisi yo‘q; mashina run tugagandan
keyin uxlagan), eng past MemAvailable 5,64 GB, SwapFree 4 080 MB (D63c
belgisi yo‘q). (a) 71 daqiqa davom etdi (birinchi pass'da 228): CTE ning
ikki o‘qishi va ko‘chirishi bu safar serverdagi 120 s `statement_timeout`
ga birinchi urinishda urildi.

### (a) `deep_chain/100000` — asosiy son qayta o‘lchangan, birinchisi yonida

| Amal | ρ (qayta) [95 % CI] | ρ (birinchi, bosim ostida) | Xulosa (qayta / birinchi) |
|---|---|---|---|
| shox o‘qish | — (CTE timeout) | — (CTE xotira) | timeout / ishga tushirilmadi — xotira |
| ajdod o‘qish | — (CTE timeout) | — (CTE xotira) | timeout / ishga tushirilmadi — xotira |
| oxiriga barg | 281,43 [235,17; 365,02] | 412,09 [283,97; 500,77] | CTE tezroq / CTE tezroq |
| eng chapga barg | 422,46 [381,92; 453,00] | 1 240,00 [1 077,99; 1 428,34] | CTE tezroq / CTE tezroq |
| ko‘chirish | — (CTE timeout) | — (CTE timeout) | timeout / timeout |
| o‘chirish | 0,922 [0,796; 1,033] | 0,819 [0,784; 0,880] | **taqqoslanadigan** / MPTT tezroq |

Mediana (ms, qayta / birinchi): MPTT 699,4 / 559,2, 628,6 / 422,5,
472,1 / 376,9, 1 023,0 / 877,3, 1 074,3 / 975,5, 26 013,4 / 22 833,5;
CTE oxiriga 1,68 / 0,91, chapga 2,42 / 0,71, o‘chirish 28 212,4 / 27 894,7.

### (b) parallel bosqich — yaxlitlik D63g tekshiruvi bilan qayta

72 bosqichdan **8 tasida** xulosa o‘zgardi:

- **4 tasi — D63g artefaktining yo‘qolishi**: qulfli variantda MPTT
  `course_like/100000`, `deep_chain/10000`, `deep_chain/100000`,
  `random/100000` da birinchi pass'da “buzildi” edi (faqat
  `differs_from_rebuild`), qayta tekshiruvda **toza**. Endi qulfli variantda
  **ikkala usul ham to‘qqiz blokning hammasida toza**.
- **4 tasi — qulfsiz poyganing takror orasidagi farqi**: CTE ning Y1 i
  `course_like/1000` ×8 da buzildi (birinchi pass'da toza), `deep_chain/1000`
  ×8 da toza (birinchi pass'da buzilgan); MPTT `deep_chain/1000` ×8 va
  `deep_chain/10000` ×8 da bu safar Y1 sikli yo‘q (oraliqlar baribir buzilgan).

Qulfsiz variant: **MPTT oraliqlari 27/27 bosqichda buzilgan** (ikkala
pass'da ham), CTE ning Y1 i **27 dan 1 tasida** buzilgan (ikkala pass'da ham
bittadan, har xil blokda). O‘tkazuvchanlik uchun asosiy son — birinchi
pass'niki (D63h); `deep_chain/100000` niki qayta o‘lchangan.

### D63 qoidasi birlashtirilgan ma’lumot bilan

| # | Shart | Bajarildimi | Kataklar |
|---|---|---|---|
| 1 | yozish har joyda “CTE tezroq” | **yo‘q** | `deep_chain/1000` ko‘chirish 0,134 va o‘chirish 0,918 (taqqosl.), `deep_chain/10000` ko‘chirish 0,010 va o‘chirish 0,857, `deep_chain/100000` o‘chirish 0,922 (taqqosl.), `random/100000` ko‘chirish 0,758; `deep_chain/100000` ko‘chirish — timeout |
| 2 | o‘qishda 1,5 barobardan sekin emas | **yo‘q** | 16 katak (birinchi pass'dan, o‘zgarmagan); `deep_chain/100000` ning ikkalasi — timeout |
| 3 | qulfli parallel yozishdan keyin CTE yaxlitligi | **ha** | 9/9 blok toza |

**Umumiy: H4 qo‘llab-quvvatlanmadi** (birinchi pass'dagi xulosa
o‘zgarmadi). Alohida qator: qulfsiz parallel yozishda MPTT ning oraliq
kodlashi 27/27 bosqichda buziladi, qulflangan platforma yo‘lida esa ikkala
usul ham yaxlit.


---

## D65 — Hypothesis xossa testlari: tuzilishi va topilgani (10-bosqich, 2026-10-20)

**Ikki state machine.** Sof model — `neuro_model/tests/test_properties.py`;
PostgreSQL'dagi haqiqiy yozuvchilar — `curriculum/tests/test_kb_properties.py`.
Ikkalasi ham Hypothesis `RuleBasedStateMachine`: tasodifiy daraxt (kurs = ildiz,
topic = barg), tasodifiy prerekvizitlar va amallar ketma-ketligi. Amalni
qabul qilish yoki rad etishni testning o‘zi emas, production kodi hal qiladi:
sof tomonda `is_nested`, `find_cycle_chain` (Algoritm 2.1), `topological_order`
(Algoritm 2.2) va talabaning holati (TY1–TY4); Django tomonda `kb.*` servisi
(`KBError`), `process_submission` (`TopicClosed`) va arxivlangan mavzu uchun
400 yo‘li.

- Amallar: prerekvizit qo‘shish / o‘chirish / vaznini o‘zgartirish (yaroqsiz ω
  ham), tugunni ko‘chirish, tartibini o‘zgartirish, yangi topic/section,
  arxivlash (Django), javoblar seriyasi (aralash yoki bir xil javoblar ketma-
  ketligi; Django'da 4 tadan 3 tasi interfeys taklif qilgan ochiq mavzudan).
- Har qabul qilingan amaldan keyin: G_L'da sikl yo‘q (Algoritm 2.2 dan
  mustaqil DFS); topologik tartib barcha faol topic'larni bir martadan
  o‘z ichiga oladi va har bir qirraga mos; `missing_count` M bayroqlaridan
  qayta hisoblanganiga teng (Django'da ikki marta: resync'dan **oldin**
  inkremental Algoritm 2.3 yozgan qatorlar va `states_for` dan keyin hamma
  qatorlar, TY6); attempts / correct / accuracy, θ va b_q ning javob sonlari
  ledger'dan sanalganiga teng; ehtimolliklar [0, 1] da, θ ±4 ichida;
  2.5-tasdiq; TY5 va holatlar jadvali. Django'da qo‘shimcha: Y1, Y2, Y4,
  G_L SQL'dan (django-tree-queries CTE bilan Leaves) qayta qurilib snapshot
  bilan solishtiriladi, KB versiyasi KB amalida aniq 1 ga, javobda 0 ga oshadi.
- Rad etilgan amal: Django'da KB versiyasi, tugunlar, relatsiyalar, holat
  qatorlari, ledger id'lari, θ va b_q — hammasi amaldan oldingisiga teng; sof
  tomonda funksiyalarga mashinaning o‘z lug‘atlari beriladi, shuning uchun
  kirishni o‘zgartirgan funksiya ushlanadi.
- Deterministik: `derandomize=True`, `database=None` (diskda `.hypothesis/`
  yo‘q). Sof: 200 misol × 50 qadam (~6 s); Django: 40 misol × 20 qadam, har
  misol bitta savepoint ichida va oxirida rollback (~37 s).

**Testning o‘zi tekshirildi (ataylab kiritilgan xatolar, commit qilinmagan).**
Sof machine 4 tadan 4 tasini ushladi: `propagate` hisoblagichlarni
qaytarmaydi; TY5 buzilgan (`next_status` boshlangan mavzuni yopadi); Algoritm
2.1 sikl topmaydi; ochiq mavzuni qayta yopish shoxi yo‘q. Django machine 6
tadan 6 tasini: `propagate`; TY5; Algoritm 2.1 ham, `_fresh()` himoyasi ham
o‘chirilgan; versiya ikki marta oshadi; TY6 `resync` o‘chirilgan; rad etilgan
`add_prerequisite` oldin bitta qatorni yozib qo‘yadi. Bir yugurishdagi qamrov:
sof — 12 512 qabul qilingan amal, 649 ta M o‘zgarishi, 56 ochilish, 26 yopilish;
Django — 1 164 qabul qilingan javob, 75 M o‘zgarishi, 5 ochilish.

**Topilma: P(L) = 1.0 (D65a).** Hypothesis birinchi yugurishdayoq qisqartirib
berdi: PT = 0,5 bo‘lgan mavzuda ~8 ta to‘g‘ri javobdan keyin P(L) double'da
aynan 1.0 ga yaxlitlanadi; shundan keyingi noto‘g‘ri javobda posterior
P·S / (1 − fl(1 − S)) = **1,000000000000006**. PT o‘tishi uni 1.0 ga clamp
qiladi, shuning uchun ledger'ga yoziladigan hech bir qiymat [0, 1] dan
chiqmaydi (`posterior` faqat xotiradagi `StepResult` da). Lekin P(L) = 1.0
**yutuvchi holat**: undan keyin hech qanday javob P(L) ni τ − δ dan pastga
tushira olmaydi (matematik jihatdan P(L) < 1 bo‘lishi kerak edi). Model
kodiga tegilmadi (II bob formulalari). Test shuni aniq ifodalaydi: yoziladigan
qiymatlar qat’iy [0, 1] da, posterior 1e-12 aniqlikda; 2.5 ning qat’iy shakli
1e-9 < P(L) < 1 − 1e-9 da (double o‘zgarishni ajrata oladigan joyda), kuchsiz
shakli hamma joyda. Taklif (foydalanuvchi qarori): `bkt.posterior` ni [0, 1]
ga clamp qilish va P(L) ni 1 − ε bilan cheklash — bu natijalarni (juda kam
bo‘lsa ham) o‘zgartirishi mumkin, shuning uchun alohida qaror kerak.



## D66 — `submit_answer` SQL byudjeti: nima sanaladi, nima qilindi, nega ≤ 12 emas (10-bosqich, 2026-10-20)

**Sanash.** `assessments/tests/test_query_budget.py`: HTTP orqali, haqiqiy JWT
bilan (foydalanuvchi so‘rovi sanaladi) va haqiqiy tranzaksiyada
(`transaction=True`; oddiy test tranzaksiyasida view'ning `atomic` i SAVEPOINT
juftiga aylanadi, production'da esa u yo‘q). Django yuborgan har bir buyruq
sanaladi, faqat BEGIN/COMMIT dan tashqari (har yozuvchi so‘rovda bor, hech bir
reja ularni olib tashlay olmaydi); so‘rov ichidagi SAVEPOINT juftlari
(`get_or_create`) sanaladi. Har holatning aniq soni testda qotirilgan;
o‘zgarsa, test qaysi buyruqlar ishlaganini chiqaradi.

| Holat | Oldin (`2ce9ad4`) | Keyin |
|---|---|---|
| kursdagi birinchi javob (θ qatori yaratiladi) | 28 | 22 |
| oddiy javob (M o‘zgarmaydi) | 25 | **19** |
| M o‘zgaradi va voris ochiladi | 26 | **20** |
| `review_repeat` | 16 | **11** |
| yangi talabaning birinchi so‘rovi (holat qatorlari yaratiladi) | 34 | 28 |
| `next_question` (byudjetsiz) | 8 | 7 |
| `trajectory` (byudjetsiz; N+1 yo‘qligi `test_trajectory.py` da) | 5 | 5 |

**Olib tashlangan 6 ta qayta o‘qish** — barchasi bir tranzaksiya ichida allaqachon
qo‘lda bo‘lgan qiymatni qayta o‘qish edi:

1. `check_open` holatlarni `states_for` bilan ikkinchi marta o‘qirdi → endi
   `process_submission` o‘qigan `states` beriladi;
2. `record_attempt` (talaba, mavzu) advisory lock'ini qayta olardi → `lock_held=True`
   (lock orchestrator'da olingan va tranzaksiya oxirigacha turadi; qulflar
   to‘plami va tartibi o‘zgarmadi — Q1-14 da qayd etilgan no-op so‘rov);
3. `record_attempt` KB versiyasini qayta o‘qirdi → orchestrator'ning snapshot'i
   beriladi. Bu to‘g‘riroq ham: READ COMMITTED da parallel KB o‘zgarishi
   kelsa, ledger'dagi `course_id` θ qatorining kursidan farq qilishi mumkin edi;
   endi bir javobning hamma qiymati bitta snapshot'dan;
4–6. `get_next_question` mavzuni, KB versiyasini va θ ni qayta o‘qirdi →
   orchestrator ularni beradi (θ — Elo hozirgina yozgan qiymat, DB'dagi bilan
   bir xil double).

`next_question` view'ida ham `check_open` va tanlash bitta snapshot'dan (8 → 7).
Algoritm 2.4 tartibi, qulflar va natijalar o‘zgarmadi: 4-bo‘lim etalon
testlari, V-D1 parallellik testi (`test_ledger.py:423`, 10 ta parallel
`process_submission`) va verification oracle o‘tadi (QADAM 12).

**Nega ≤ 12 emas.** Qolgan 19 ta (oddiy javob): JWT foydalanuvchisi; choice +
savol + mavzu; KB versiyasi; advisory lock; holatlar; D25 oynasi; `TopicModelParams`;
P(L) ledger'dan; θ qatori FOR UPDATE; savol FOR UPDATE; θ UPDATE; b UPDATE;
holat qatori FOR UPDATE; holat UPDATE; `max(attempt_no)`; ledger INSERT; history
INSERT; keyingi savol; uning variantlari. Har biri Algoritm 2.4 ning alohida
o‘qishi, qulfi yoki yozuvi. 12 ga tushirish uchun quyidagilardan kamida 7 tasi
kerak — har biri qulfni, ma’lumot manbasini yoki yoziladigan narsani
o‘zgartiradi, ya’ni bu bosqichning “qulflar va natijalar o‘zgarmasin” shartiga
zid va alohida qaror talab qiladi:

- P(L) ni ledger o‘rniga holat qatoridan olish (D35 dagi qayta qurish kafolati) — −1;
- D25 oynasi va `max(attempt_no)` ni bitta ledger so‘roviga birlashtirish — −1;
- `TopicModelParams` ni snapshot bilan keshlash (kalibrlashda bekor qilish) — −1;
- θ va b yozuvlarini bitta CTE buyrug‘iga birlashtirish — −1;
- `UserKnowledgeHistory` qatorini olib tashlash yoki ledger ustidagi view qilish — −1;
- keyingi savolni javobdan ajratish yoki bitta so‘rovda olish — −1…−2;
- JWT foydalanuvchisini DB'siz ishlatish (o‘chirilgan akkaunt darhol bloklanmaydi) — −1.

V-F1 verification spetsifikatsiyasida yumshoq chegara (“buzilsa ham FAIL emas,
ogohlantirish”), shuning uchun test qotirilgan sonlar bilan o‘tadi va
byudjetdan oshgan holatlar uchun ogohlantirish chiqaradi.



## D67 — Coverage doirasi (10-bosqich, 2026-10-20)

`.coveragerc` (yangi): **umumiy** = backend'ning o‘z manba kodi — `accounts`,
`analytics`, `assessments`, `curriculum`, `benchmarks`, `config`, `neuro_model`.
Chiqarilgan: testlar, migratsiyalar, `verification/` (mustaqil suite),
`experiments/` (o‘z venv'ida, alohida suite), `scripts/`, `manage.py`,
`conftest.py` va `benchmarks/locustfile.py` (faqat Locust ichida ishlaydi).
**Servislar** = `*/services/*` (`assessments/services`, `curriculum/services`).
CI endi uchala maqsadni ham majburiy qiladi: `fail_under = 80` (umumiy),
`--include='neuro_model/*' --fail-under=95`, `--include='*/services/*'
--fail-under=85`. Oldin CI `coverage report` ni konfiguratsiyasiz chaqirardi —
test fayllari ham hisobga kirib, son ma’nosiz edi (audit 7.2 dagi 68 % ham shu
usulda olingan).



## D68 — Locust protokoli (10-bosqich, 2026-10-20, to‘liq yugurishdan oldin)

- **Ma’lumot (D13).** Alohida baza `<DATABASE_URL nomi>_locust` (shu Postgres
  serverida, yo‘q bo‘lsa yaratiladi, hech qachon o‘chirilmaydi). `seed_load_test`
  unda kamida bitta simulyatsiya qilinmagan akkaunt bo‘lsa, ishlamaydi.
  O‘quvchilar — `load-<run>-NN@simulated.invalid`, `is_simulated=True`, har
  yugurish o‘z yangi akkauntlari bilan (oldingi yugurishning progressi
  o‘tmaydi); parol har yugurishda generatsiya qilinadi va hech qayerga
  yozilmaydi. Dev baza faqat `CREATE DATABASE` uchun ochiladi.
- **Kurs (V-F2).** 500 topic (25 section × 20), 1 500 prerekvizit (topic →
  keyingi topic, ±40 o‘rin ichida; G_L qurilishi bo‘yicha asiklik), har
  topic'da 10 savol (b ∈ [−1,5; 1,5], 4 variant). Hammasi `kb.*` servisi
  orqali (Algoritm 2.1 va versiya har relatsiyada ishlaydi).
- **Server.** `manage.py runserver --noreload` (bitta jarayon, threaded):
  `requirements.lock` da WSGI server yo‘q, lock fayllar esa o‘zgarmaydi.
  **`DEBUG=False`**, Redis kesh (indeks 3), `DB_CONN_MAX_AGE=0` (standart),
  login throttle 100 000/minute (standart 5/minute — bitta IP dan 50 login
  aks holda 429 bo‘ladi; bu yuk testi uchun yagona o‘zgartirilgan sozlama).
- **Oqim.** CSRF → login → (`next_question` → `submit_answer` → `trajectory`)
  takrorlanadi; har so‘rovdan keyin 0,5–1,5 s kutish; javoblarning 75 % to‘g‘ri;
  o‘rganiladigan mavzu — trayektoriyaning boshi (Algoritm 2.5). `next_question`
  ning 403/404 javoblari API mo‘ljallagan javob — muvaffaqiyat deb sanaladi va
  o‘quvchi boshqa mavzuga o‘tadi; boshqa har qanday non-2xx — xato.
- **Yuk.** 50 foydalanuvchi, 5/s bilan ishga tushadi, 2 daqiqa, headless; shu
  paytda boshqa test yoki benchmark ishlamaydi. Oldin MemAvailable va swap
  yoziladi, yuk davomida har 5 s da namuna olinadi.
- **Natija.** `experiments/results/locust/<ts>/`: har endpoint uchun p50, p95,
  xato ulushi, RPS; server logidagi status kodlari; muhit (CPU, governor,
  xotira, Postgres sozlamalari); D54 provenance. V-F2 mo‘ljali (p95 < 300 ms)
  yumshoq — natija baholanadi, FAIL emas.
- **Cheklovlar.** `runserver` production server emas (bitta jarayon); Locust
  100 ms dan yuqori vaqtlarni ikki muhim raqamgacha yaxlitlaydi; CPU
  governor `powersave`.



## QADAM 12 — 10-bosqich, 1-qism: xossa testlari, `accounts`, SQL byudjeti, coverage, Locust, frontend (2026-10-20)

Boshlang‘ich holat: `2ce9ad4`, ishchi daraxt toza, Postgres 5433 ishlab turgan.
Ish davomida mashina bir marta qayta yuklandi (compose `--env-file config/.env
up -d` bilan qayta ko‘tarildi; `neurolearn`, `_bench`, `_locust` bazalari
joyida). Qarorlar D65–D68 (yuqorida) har biri o‘z commit'ida.

### Commit'lar

| Commit | Nima |
|---|---|
| `8f1f36f` | Hypothesis: sof model va KB servisi + javob yo‘li uchun ikki state machine (SN2, P1-9, D65) |
| `fbf2f4d` | `accounts`: hisobi tugagan refresh cookie → 401 (500 edi) + 27 ta yangi test (audit 7.1) |
| `601cea3` | `submit_answer` ichidagi 6 ta qayta o‘qish olib tashlandi; SQL sonlari testda qotirildi (P2-4, V-F1, D66) |
| `3e71a32` | `.coveragerc` va CI dagi uchta maqsad (7.2, D67) |
| `5ab628e` | Locust: `seed_load_test`, `locustfile.py`, `load_test.py` (SN3, D68) |
| `f41bfb0`, `98f7b5f` | Locust natijalari, 1-urinish (50 va 5 foydalanuvchi) — **D48 ga zid, almashtirildi** |
| `805f967` | `dj5433.sh`: suffiks benchmark bazasiga ham tegadi (ikki pytest bir test bazasini o‘chirib qo‘ymasin) |
| `80ddcd3`, `0e424d7` | Locust jadvali: har son `metrics.json` da, `tables.fmt` bilan, `tables.write` orqali (D48) |
| `e836b2f`, `4aee869` | Locust natijalari, qayta (50 va 5 foydalanuvchi) — asosiy natija |

### 0. Boshlang‘ich sonlar (`2ce9ad4`)

| Suite | Natija |
|---|---|
| Backend (`scripts/dj5433.sh venv/bin/python -m pytest`) | 1 230 passed, 51 skipped, 13 subtests |
| `experiments/.venv` — `experiments/tests` | 406 passed, 2 skipped |
| `benchmarks/tests` | 80 |
| `verification/tests` | 827 passed, 4 failed (3 ta N/A signali + `test_d48_every_result_has_sha256_commit_seed_and_command`) |
| Coverage (manba kodi; testlar, migratsiyalar, verification, experiments, scripts chiqarilgan) | `neuro_model` 99 % (503/5), servislar 97 % (932/28), umumiy 92 % (5 521/455) |

### 1. Hypothesis (SN2)

Tuzilishi, invariantlar, sozlamalar va kiritilgan xatolar bilan tekshiruv —
D65 da. Ikki test, birgalikda ~43 s: sof machine 200 misol × 50 qadam,
Django machine 40 misol × 20 qadam. Sof machine 4/4, Django machine 6/6
kiritilgan xatoni ushladi. Topilma D65a: P(L) double'da 1.0 ga yetadi va
yutuvchi holatga aylanadi; noto‘g‘ri javobning posteriori 1 + 6e-15 —
yoziladigan qiymatlar [0, 1] da qoladi, model kodi o‘zgartirilmadi.

### 2. `accounts` (audit 7.1)

`accounts/tests/test_accounts.py` — 27 test: ro‘yxatdan o‘tish (standart rol
— student, `is_staff`/`role`/`groups` so‘rovda e’tiborsiz, takroriy va
soft-delete qilingan email, mos kelmaydigan, qisqa, raqamli va keng tarqalgan
parollar), D15/Q0-6 rollar jadvali (6 xil akkaunt: rol, `is_instructor`,
`is_admin`, o‘qituvchi va admin endpoint'lari bir-biriga mos), profil faqat
ismni o‘zgartiradi, soft delete parol / access token / refresh cookie'ni
yopadi, D11 admin yo‘li orqali (rozilik bor → anonimlashtiriladi va login
bo‘lmaydi; yo‘q → o‘chiriladi), aylantirilgan cookie atributlari
(httpOnly, Secure, SameSite, path), logout cookie'ni o‘z path'ida
o‘chiradi, faqat eskirgan jti blacklist'da, cookie'ga mos kelmaydigan CSRF
token 403. `accounts` jami: 60 → 87 test.

**Topilgan xato (tuzatildi, `fbf2f4d`).** SimpleJWT refresh serializer'i
foydalanuvchini default manager orqali qidiradi, u soft-delete qilinganlarni
yashiradi: o‘chirilgan akkauntning refresh cookie'si `/api/accounts/token/refresh/`
da **500** berardi; nofaol akkaunt esa 401 berib cookie'ni qoldirardi. Endi
uchala holat (soft-delete, nofaol, hard-delete) 401 `token_not_valid` va cookie
o‘chiriladi; test har biri uchun.

### 3. SQL byudjeti (V-F1, P2-4)

Sanash va tafsilot — D66. Oldin → keyin (BEGIN/COMMIT sanalmaydi):

| Holat | Oldin | Keyin |
|---|---|---|
| oddiy javob | 25 | **19** |
| M o‘zgaradi, voris ochiladi | 26 | **20** |
| `review_repeat` | 16 | **11** |
| kursdagi birinchi javob | 28 | 22 |
| yangi talabaning birinchi so‘rovi | 34 | 28 |
| `next_question` | 8 | 7 |
| `trajectory` | 5 | 5 |

≤ 12 faqat `review_repeat` da bajarildi. Qolgan 19 ta Algoritm 2.4 ning
alohida o‘qishi/qulfi/yozuvi; 12 ga tushirish qulf, ma’lumot manbai yoki
yoziladigan narsani o‘zgartirishni talab qiladi (D66 dagi ro‘yxat) — bu
bosqich shartiga zid, foydalanuvchi qarori kerak. V-F1 yumshoq chegara:
test aniq sonlarni qotiradi va oshgan holatlar uchun ogohlantirish beradi.
Natijalar o‘zgarmaganining dalili: 4-bo‘lim etalon testlari, V-D1
parallellik testi (`test_ledger.py:423`) va verification oracle (pastda) —
o‘zgarishdan oldingi bilan bir xil.

### 4. Coverage (7.2)

Doira — D67 (`.coveragerc`), CI da majburiy.

| Qism | Oldin | Keyin | Maqsad |
|---|---|---|---|
| `neuro_model` | 99 % (503/5) | 99 % (503/5) | ≥ 95 % |
| servislar (`*/services/*`) | 97 % (932/28) | 97 % (937/28) | ≥ 85 % |
| umumiy | 92 % (5 521/455) | 90 % (5 794/562) | ≥ 80 % |

Maqsadlar boshidanoq bajarilgan edi, shuning uchun qatorni qoplash uchun test
qo‘shilmadi; qo‘shilgan testlar 1–3- va 5-bandlarning xatti-harakatini
tekshiradi. Umumiy son 92 → 90 % ga tushdi, chunki doiraga yangi
`benchmarks/load_test.py` kirdi (175 qatordan 102 tasi — subprocess
orkestratsiyasi, faqat haqiqiy yugurishda ishlaydi; uning hisoblovchi
qismlari — CSV o‘qish, status kodlari, jadval va D48 tekshiruvi —
`test_load_test.py` da). CI dagi uchala buyruq yakuniy ma’lumotda o‘tadi.

### 5. Locust (SN3, V-F2)

Protokol — D68 (yugurishdan oldin commit qilingan). `DEBUG=False`, bitta
`runserver` jarayoni, Redis kesh, alohida `neurolearn_locust` bazasi (faqat
simulyatsiya, D13), V-F2 kursi: 500 mavzu, 1 500 prerekvizit, 5 000 savol.

**Asosiy natija — `experiments/results/locust/20261020-085406` (`0e424d7`, ikkala uchida toza):**

| Endpoint | So‘rovlar | Xatolar | Xato ulushi | p50, ms | p95, ms | RPS |
|---|---|---|---|---|---|---|
| login | 50 | 0 | 0 | 1 000 | 2 300 | 0,419 |
| next_question | 520 | 0 | 0 | 1 700 | 2 600 | 4,363 |
| submit_answer | 501 | 0 | 0 | 4 500 | 15 000 | 4,203 |
| trajectory | 536 | 0 | 0 | 2 500 | 3 900 | 4,497 |
| jami | 1 657 | 0 | 0 | 2 400 | 6 300 | 13,902 |

Muhit: i7-11800H, 16 mantiqiy yadro, governor `powersave`; oldin MemAvailable
9 257 MB / 15 249 MB, swap bo‘sh 4 095 / 4 095 MB; yuk davomida eng past
MemAvailable 6 869 MB, swap ishlatilmadi (25 namuna). Server logida 1 647 ta
200.

**Bir xil protokolning birinchi urinishi — `20261020-070525` (`5ab628e`, toza):**
3 161 so‘rov, 0 xato, **26,542 RPS**; p50 / p95: next_question 900 / 1 300,
submit_answer 2 300 / 4 500, trajectory 1 100 / 1 600, login 830 / 1 600.
Oldin MemAvailable 6 937 MB, swap bo‘sh 1 864 / 4 095 MB.

**Post-hoc, 5 foydalanuvchi** (D68 da yo‘q; xizmat vaqtini navbatdan ajratish
uchun): `20261020-085659` (`e836b2f`): p50 / p95 next_question 120 / 240,
submit_answer 170 / 310, trajectory 170 / 310, 9,854 RPS, 0 xato;
birinchi urinish `20261020-070827`: 67 / 120, 87 / 160, 65 / 150, 12,206 RPS.

O‘qish:

- **Xatolar ulushi hamma yugurishda 0.** Kutilgan 403/404 (`next_question`)
  server logida 0–5 ta.
- **50 foydalanuvchida V-F2 mo‘ljali (p95 < 300 ms) bajarilmadi**, ikkala
  urinishda ham. Sabab — bitta jarayonning to‘yinishi: o‘tkazuvchanlik
  14–27 RPS da to‘xtaydi, kechikish navbatdan keladi (5 foydalanuvchida
  xuddi shu so‘rovlar p95 120–310 ms). Bu `runserver` ning bitta jarayoni
  haqidagi son, production konfiguratsiyasi haqida emas.
- **Ikki urinish orasidagi 2 barobar farq mashina holatidan.** Qayta
  yugurish qayta yuklashdan ~10 daqiqa keyin bo‘ldi: Postgres va page cache
  sovuq, desktop ilovalari ishga tushayotgan edi — metrics'dagi load
  (0,98 → 4,25) va `busiest_processes` (Chrome, Papers, JetBrains Toolbox,
  IDE) buni ko‘rsatadi. Birinchi urinishning sonlari to‘g‘ri, faqat
  `tables.md` D48 ga zid (pastda).
- Birinchi urinish papkalari (`070525`, `070827`) **o‘zgartirilmadi**
  (commit qilingan natija). Ularning `tables.md` sida `metrics.json` da yo‘q
  sonlar bor (300 ms mo‘ljali konstantadan, status kodlari lug‘at kalitlari,
  `fmt` dan tashqari formatlash) — shuning uchun verification'dagi
  `test_d48_every_number_in_every_tables_md_is_in_its_metrics_json` va
  experiments'dagi `test_the_published_results_verify_cell_by_cell` faqat shu
  ikki papka tufayli yiqiladi. Generator tuzatildi (`80ddcd3`, `0e424d7`),
  yangi papkalar ikkala tekshiruvdan o‘tadi.

### 6. Frontend (`~/Desktop/neuro/neuro`, `5251c45`, faqat tekshiruv)

| Tekshiruv | Natija |
|---|---|
| `npm run lint` | **0 error**, 8 warning — hammasi `react-refresh/only-export-components`: `components/ui/` dagi `badge.tsx:29`, `button.tsx:59`, `form.tsx:129`, `navigation-menu.tsx:111`, `sidebar.tsx:636`, `sonner.tsx:27`, `toggle.tsx:37` va `contexts/AuthContext.tsx:14` |
| `npx tsc --noEmit` | **0** xato |
| `npm test` (vitest) | **90 passed**, 14 fayl |
| `npm run build` | muvaffaqiyatli; ogohlantirish: `Hero3DBackground` chunk'i 850 kB (> 500 kB) |

Spetsifikatsiya (lint 0 error, tsc 0) bajarilgan. Tuzatish talab qilmaydi;
ixtiyoriy ro‘yxat: 8 ta fast-refresh ogohlantirishi (konstanta/funksiyalarni
alohida faylga chiqarish) va `Hero3DBackground` ni lazy-chunk'larga bo‘lish.
Build `dist/` ga yozadi, u `.gitignore` da — frontend daraxti toza qoldi.

### 7. Yakuniy tekshiruvlar (`4aee869`)

| Suite | Natija |
|---|---|
| Backend (`coverage run -m pytest`) | 1 269 passed, 51 skipped, 13 subtests, **1 failed** — experiments testlari Django venv'da ham yig‘iladi va o‘sha `test_the_published_results_verify_cell_by_cell` yiqiladi (5-band). Jami 1 270 = 1 230 + 40 yangi test (sof va Django xossa testlari 2, `accounts` 27, SQL byudjeti 3, Locust vositalari 8) |
| `experiments/.venv` — `experiments/tests` | 405 passed, 2 skipped, **1 failed** — `test_the_published_results_verify_cell_by_cell`, faqat `locust/20261020-070525` va `070827` tufayli (5-band) |
| `benchmarks/tests` | 88 passed (80 + 8) |
| `verification/tests` | 826 passed, **5 failed**: boshlang‘ich 4 ta + `test_d48_every_number_in_every_tables_md_is_in_its_metrics_json` (o‘sha ikki papka). SQL o‘zgarishidan keyin, ikki Locust papkasi qo‘shilishidan oldin: 827 / 4 — boshlang‘ich bilan aynan bir xil |
| `manage.py check` | toza |
| `makemigrations --check --dry-run` | No changes detected |

`verification/` ga tegilmadi. Uning `test_na_group_f_performance_is_still_unmeasured`
signali hali o‘tadi, chunki u `verification/tests/test_f_performance.py`
yo‘qligini tekshiradi — V-F endi o‘lchangan, lekin bu faylni verification
muallifi yozadi.

### Ochiq qolganlar

1. **SQL ≤ 12** oddiy javob (19) va M o‘zgarishi (20) uchun bajarilmadi — D66
   dagi variantlardan qaysi biri (agar bo‘lsa) qabul qilinishi foydalanuvchi
   qarori.
2. **V-F2 50 foydalanuvchida** bajarilmadi (bitta `runserver` jarayoni
   to‘yinadi). Bir necha worker'li WSGI server (masalan gunicorn) lock
   faylga qo‘shilishi kerak — foydalanuvchi qarori; keyin Locust tinch
   mashinada qayta yugurtiriladi.
3. **Birinchi Locust papkalari** (`070525`, `070827`) D48 ga zid va ikki
   tekshiruvni yiqitadi; commit qilingan natija bo‘lgani uchun tegilmadi.
   `git rm` qilish yoki qoldirish — foydalanuvchi qarori.
4. **D65a**: `bkt.posterior` ni [0, 1] ga clamp qilish va P(L) ni 1 − ε bilan
   cheklash taklifi (natijalarni juda oz o‘zgartirishi mumkin).
5. Frontend: 8 lint ogohlantirishi va 850 kB chunk (tuzatish shart emas).
6. 10-bosqichning 2-qismi: `REMEDIATION_REPORT.md` va `docs/THESIS_MAPPING.md`.


---

## D65a — posteriorni [0, 1] ga clamp qilish: protokol (2026-10-20, o‘zgarish va sanashdan oldin)

Foydalanuvchi qarori (10-bosqich, 2-qism, A3): `bkt.posterior` va PT
o‘tishidan keyingi P(L) [0, 1] ga clamp qilinadi; 1 − ε chegarasi
qo‘shilmaydi. PT o‘tishi (`bkt.transition`) allaqachon clamp qiladi, shuning
uchun kod o‘zgarishi faqat `bkt.posterior` da.

**Sanash (o‘zgarishdan oldin, natija o‘zgaradimi?).** Yangi skript
`experiments/clamp_count.py` H2 ning o‘z oqimini (ma’lumot, tozalash, D57
protokoli, 5-fold split, `h2.prepare` / `h2.fold_sets`) fit'siz qayta
o‘ynaydi: parametrlar D55 to‘liq yugurishining checkpoint'idan
(`experiments/.runs/checkpoints/h2-bounds-99bb9f9117e5e296`, `30ad4e4`,
asosiy sozlama `fit-0-*`, `h2_frozen.reusable_checkpoint` bilan topiladi).
BKT va BKT+IRT (λ=0) uchun, H2 dagidek o‘qitish fold'ida item'larni isitish va
test fold'ida bashorat. Har `bkt.posterior` chaqiruvida sanaladi:

- `posterior_clamped` — xom posterior [0, 1] dan tashqarida (yangi clamp ishlaydi);
- `transition_clamped` — xom P(L)′ [0, 1] dan tashqarida (mavjud clamp);
- `p_after_differs` — clamp qilingan va qilinmagan yo‘lda P(L)′ farq qiladi.

**Qoida.** `posterior_clamped` = 0 (BKT ham, BKT+IRT ham) → commit qilingan
natijalar o‘zgarmaydi deb yoziladi va clamp commit qilinadi. 0 bo‘lmasa →
to‘xtash va sonni foydalanuvchiga aytish (qaror shu). Junyi (H1/H3): per-skill
parametrlar saqlanmagan (checkpoint yo‘q, `metrics.json` dagi
`folds[].parameters` bo‘sh), 25,9 mln qatorni qayta fit qilish bu qarordan
tashqarida — (c) bajarilmaydi. THESIS_MAPPING ga F6 (raqamli himoya, θ clamp
kabi) qo‘shiladi.


---

### D65a — sanash natijasi (2026-10-20): **0 emas, to‘xtatildi**

`experiments/.venv/bin/python -m experiments.clamp_count` (34 s; ma’lumot
sha256 `f22e3fb7…`, 338 001 qator, 5 fold, checkpoint `h2-bounds-99bb9f9117e5e296`):

| Model | `bkt.step` chaqiruvlari | posterior [0, 1] dan tashqarida (yangi clamp) | P(L)′ [0, 1] dan tashqarida (mavjud clamp) | P(L)′ farq qiladi |
|---|---|---|---|---|
| BKT | 1 744 901 | **1 177** | 1 167 | 0 |
| BKT+IRT (λ=0) | 1 744 901 | **370** | 369 | 0 |

Qoida bo‘yicha (son 0 emas) ish to‘xtatildi va son foydalanuvchiga aytildi;
`bkt.posterior` **o‘zgartirilmadi**. Kuzatuv: 1 547 holatning hammasida
P(L)′ ikkala yo‘lda bir xil — posterior > 1 bo‘lsa mavjud o‘tish clamp'i
P(L)′ ni baribir 1.0 ga tushiradi, bashorat esa P(L) ning yangilanishdan
oldingi qiymatidan olinadi. Shuning uchun clamp commit qilingan sonlarni
o‘zgartirmasligi kutiladi, lekin bu qarorni foydalanuvchi qabul qiladi.
Junyi — parametrlar saqlanmagan, sanalmadi (protokolda yozilgan).


### D65a — qaror: clamp qo‘llanadi (foydalanuvchi, 2026-10-20, o‘zgarishdan oldin)

Asos: to‘liq qayta o‘ynashda P(L)′ 1 744 901 × 2 yangilanishning hech birida
o‘zgarmadi, bashorat esa yangilanishdan oldingi P(L) dan olinadi; “0 bo‘lmasa
to‘xta” qoidasi natijaga ta’sirni nazarda tutgan, o‘lchov uni 0 ko‘rsatdi.
Qo‘shimcha shartlar:

1. clamp'dan keyin `clamp_count.py` yangi kod bilan qayta yuguradi va barcha
   338 001 × 2 test bashorati hamda har bir P(L)′ eski (clamp'siz) kod
   natijasi bilan **bit-aniq** teng ekanini `assert` bilan tasdiqlaydi;
2. xom posterior manfiy bo‘lgan holatlar soni; ular uchun P(L)′ farqining
   analitik chegarasi va kuzatilgan maksimum;
3. Junyi: parametrlar saqlanmagan, qayta o‘ynalmaydi — analitik chegara bilan
   “hisobot aniqligida (6 xona) o‘zgarish yo‘q, qayta ishga tushirish talab
   qilinmaydi”;
4. THESIS_MAPPING: F6 — raqamli himoya (θ clamp kabi).


### D65a — bajarildi (2026-10-20)

`neuro_model/bkt.py::posterior` endi `min(1, max(0, …))` qaytaradi
(`transition` avvaldan clamp qiladi). `experiments/.venv/bin/python -m
experiments.clamp_count` (61 s) — har model ikki marta: yangi kod va
clamp'siz eski posterior bilan; `assert` bilan:

| Model | Test bashoratlari | P(L)′ | Bit-aniq teng | posterior > 1 | posterior < 0 | max \|ΔP(L)′\| |
|---|---|---|---|---|---|---|
| BKT | 338 001 | 1 744 901 | ha / ha | 1 177 | 0 | 0.0 |
| BKT+IRT (λ=0) | 338 001 | 1 744 901 | ha / ha | 370 | 0 | 0.0 |

**Manfiy posterior — analitik chegara.** Surat P·(1 − S) yoki P·S ≥ 0
(P, S ∈ [0, 1]), maxraj p̂ yoki 1 − p̂ ≥ 1e-12 (aks holda P qaytariladi), demak
xom posterior < 0 bo‘la olmaydi; bo‘lganda ham (−ε) |ΔP(L)′| = ε(1 − PT) ≤ ε.
Kuzatilgan: 0 holat, maksimum 0. **posterior > 1** da ikkala yo‘lda ham
P(L)′ = 1.0 (o‘tish clamp'i), farq aynan 0.

**Junyi (H1, H3).** Per-skill parametrlar saqlanmagan — qayta o‘ynalmaydi.
Yuqoridagi chegaraga ko‘ra clamp faqat xom posterior > 1 da ishlaydi va u
yerda P(L)′ ikkala kodda ham 1.0; bashorat yangilanishdan oldingi P(L) dan.
Shuning uchun hisobot aniqligida (6 xona) o‘zgarish yo‘q, qayta ishga
tushirish talab qilinmaydi. Commit qilingan H2, D55, D60, H1, H3 natijalari
o‘zgarmaydi.

Testlar: `test_the_posterior_is_clamped_once_p_l_has_rounded_to_one`
(`test_student.py`); Hypothesis machine'dagi posterior endi qat’iy [0, 1] da
tekshiriladi. `neuro_model` + 4-bo‘lim etalonlari + Django machine: 555 passed.


## D66a — `submit_answer` ≤ 12: birlashtirishlar va darvozalar (foydalanuvchi qarori, 2026-10-20, koddan oldin)

Faqat qulflar tartibi, tranzaksiya chegarasi va natijalarni o‘zgartirmaydigan
birlashtirishlar. Kutilgan sonlar: oddiy javob 19 → 12, M o‘zgarishi
20 → 12, `review_repeat` 11 → 8.

| # | Birlashtirish | Turi | −SQL |
|---|---|---|---|
| 1 | choice + savol + mavzu va KB versiyasi bitta SELECT'da (versiya — skalyar subquery) | o‘qish | 1 |
| 2 | D25 oynasi, `TopicModelParams`, ledger'dagi P(L) va `max(attempt_no)` — advisory lock'dan keyin, hech qanday yozuvdan oldin bitta SELECT'da (mavzu + Pre(w) bo‘yicha korrelyatsiyalangan subquery'lar) | o‘qish | 3 (review: 1) |
| 3 | keyingi savol va uning variantlari bitta SELECT'da (variantlar JSON massiv subquery) | o‘qish | 1 |
| 4 | θ va b_q yozuvlari bitta buyruqda (ma’lumot o‘zgartiruvchi CTE); ikkala qator oldin `FOR UPDATE` bilan qulflangan | yozuv | 1 |
| 5 | ledger va history qatorlari bitta buyruqda (CTE, `ledger.py` ichida — yagona yozuvchi) | yozuv | 1 |
| 6 | M o‘zgarganda javob berilgan holat qatori va vorislar bitta `UPDATE … CASE` da; vorislarning boshqa ustunlari joriy DB qiymatini saqlaydi (`ELSE <ustun>`), ya’ni eski qiymat yozilmaydi | yozuv | 1 (faqat M o‘zgarishida) |

Ta’sirlangan jadvallar: `assessments_choice`/`question`/`curriculum_topic`
(o‘qish), `curriculum_knowledgebaseversion` (o‘qish), `assessments_topicmodelparams`
(o‘qish), `assessments_assessmentattempt` (o‘qish, INSERT), `assessments_userknowledgehistory`
(INSERT), `assessments_userability` va `assessments_question` (UPDATE, avvalgidek
`QuerySet.update` darajasida — model `save()` i ilgari ham chaqirilmas edi),
`assessments_studenttopicstate` (UPDATE). Topic/KB tuzilmasiga yozilmaydi, KB
guard'lari (`kb_write`) ishtirok etmaydi. `AssessmentAttempt.save()` faqat
yangilashni taqiqlaydi; INSERT dagi cheklovlar (CHECK, FK) DB'da — xom
INSERT'ga ham amal qiladi. Xom SQL faqat parametrlangan, har birida nega ORM
emasligi izohi; ledger skan testiga xom `INSERT INTO assessments_assessmentattempt`
qidiruvi qo‘shiladi.

**Darvozalar** (birortasi o‘tmasa — o‘zgarish ishchi daraxtda bekor qilinadi,
son 19 qoladi, sababi yoziladi):

1. Oltin solishtirish: o‘zgarishdan **oldin** seed bilan stsenariy (≥ 200
   javob: oddiy, M o‘zgaradigan, `review_repeat`, yopiq mavzuga 403, test
   sessiyasi) ledger, history, holat va hisoblagichlar, θ, b_q va n_q, KB
   versiyasi, test sessiyasi va har javobning DTO'sini eksport qiladi
   (`assessments/tests/golden/answer_path.json`, commit qilinadi); o‘zgarishdan
   keyin xuddi shu stsenariy maydonma-maydon teng (id va vaqt tamg‘alari
   tartib raqami bilan almashtirilgan).
2. 4-bo‘lim etalon testlari, Hypothesis machine'lari, parallel javob testlari,
   `accounts`, butun backend suite.
3. `verification/` faqat ishga tushiriladi: natija o‘zgarishdan oldingi bilan
   bir xil.
4. So‘rovlar soni testda qotiriladi (≤ 12).


### D66a — bajarildi, hamma darvoza o‘tdi (2026-10-20)

| Holat | D66 dan oldin | D66 | D66a |
|---|---|---|---|
| oddiy javob | 25 | 19 | **12** |
| M o‘zgaradi, voris ochiladi | 26 | 20 | **12** |
| `review_repeat` | 16 | 11 | **8** |
| kursdagi birinchi javob (bir martalik) | 28 | 22 | 15 |
| yangi talabaning birinchi so‘rovi (bir martalik) | 34 | 28 | 21 |
| `next_question` | 8 | 7 | 6 |
| `trajectory` | 5 | 5 | 5 |

Oddiy javobning 12 ta buyrug‘i va vazifasi: (1) JWT foydalanuvchisi;
(2) choice + savol + mavzu + KB versiyasi; (3) (talaba, mavzu) advisory lock;
(4) holat qatorlari; (5) `answer_context` — D25 oynasi, `TopicModelParams`,
ledger'dagi P(L), `max(attempt_no)`; (6) θ qatori `FOR UPDATE`; (7) savol
`FOR UPDATE`; (8) θ va b_q UPDATE (CTE); (9) holat qatori `FOR UPDATE`;
(10) holat UPDATE (M o‘zgarsa vorislar bilan birga); (11) ledger + history
INSERT (CTE); (12) keyingi savol variantlari bilan. Qulflar (3), (6), (7),
(9) — o‘sha tartibda, o‘sha tranzaksiyada.

Darvozalar:
1. **Oltin solishtirish** (`206dad2` da o‘zgarishdan oldin yozilgan): 241
   javob, ledger 253 qator, history 214, holat 18, θ 3, savol 120, test
   sessiyasi 4, KB versiyasi va har qadam DTO'si — maydonma-maydon teng.
2. Backend: **1 273 passed**, 51 skipped, 13 subtests, 0 failed (4-bo‘lim
   etalonlari, Hypothesis machine'lari, V-D1 parallel testlari, `accounts`,
   oltin test ichida).
3. `verification/`: o‘zgarishdan oldin 826 passed / 5 failed, keyin 826 /
   o‘sha 5 (`test_d48_every_result_has_sha256_commit_seed_and_command`,
   `test_pending_stages[9]`, `test_pending_stages[10]`,
   `test_na_group_e_pipeline_run_all_is_not_implemented`,
   `test_na_group_h_benchmark_command_is_not_implemented`).
4. Xom SQL ikkita: `student_model.WRITE_THETA_AND_B_SQL` va
   `ledger.INSERT_WITH_HISTORY_SQL` — literal, parametrlangan, har birida
   nega ORM emasligi izohi; `test_raw_sql_names_the_models_columns_and_tables`
   ularni modellarga solishtiradi, ledger skan testi xom INSERT'ni ham
   qidiradi. Qolgan birlashtirishlar ORM: skalyar subquery, korrelyatsiyalangan
   subquery'lar, `ArraySubquery` + `JSONObject`, `UPDATE … CASE`.


## D68a — Locust'ning asosiy natijasi gunicorn'da (foydalanuvchi qarori, 2026-10-20, yugurishdan oldin)

- `gunicorn==26.2.0` (PyPI'da 2026-08-24; majburiy bog‘liqligi yo‘q)
  `requirements.txt` ga va hash'lari bilan `requirements.lock` ga qo‘shildi.
  `experiments/.venv` lock'i o‘zgarmaydi.
- **Asosiy natija:** gunicorn, `config.wsgi:application`, W sync worker,
  `DEBUG=False`, 50 foydalanuvchi, 2 daqiqa, D68 dagi qolgan hamma narsa
  (baza, kurs, oqim, Redis, throttle) o‘zgarmaydi; V-F2 chegarasi
  (p95 < 300 ms) o‘zgarmaydi. `runserver` natijalari (`085406`, `085659`) —
  qo‘shimcha.
- **W.** Ish yuki Python'da CPU'ga bog‘liq (snapshot, tayyorlik, Algoritm 2.4),
  Locust (bitta gevent jarayoni) va Postgres o‘sha mashinada: shuning uchun
  har fizik yadroga bitta sync worker (I/O uchun mo‘ljallangan 2n + 1 yuk
  generatori va bazani siqib qo‘yadi), giper-oqimlar ularga qoladi.
  W = min(C_fizik, ⌊(MemAvailable_min − R) / RSS_worker⌋):
  C_fizik = 8 (`lscpu`: 1 soket × 8 yadro × 2 oqim); MemAvailable_min = 6 GB
  (yugurish sharti); R = 2 GB (Postgres, Locust, OS uchun zaxira);
  RSS_worker = 124 MB — `load_test --probe` (1 worker, bitta o‘quvchining 62
  so‘rovidan keyin; master 28 MB). ⌊4 096 / 124⌋ = 33, demak **W = 8**.
- **Shartlar** (`load_test` o‘zi tekshiradi, bajarilmasa ishga tushmaydi):
  MemAvailable ≥ 6 GB, swap ishlatilgani < 200 MB, 2 soniyalik `top`
  namunasida ≥ 10 % CPU ishlatayotgan boshqa jarayon yo‘q; namuna ro‘yxati
  `metrics.json` ga (`busy_before`) yoziladi. `ps` ning umr bo‘yi o‘rtachasi
  (D68 da `busiest_processes`) endi bu qaror uchun ishlatilmaydi.


## D69 — D48 ga zid birinchi Locust papkalari olib tashlanadi (2026-10-20)

Foydalanuvchi qarori (10-bosqich, 2-qism, A1). `experiments/results/locust/20261020-070525`
(50 foydalanuvchi) va `…/20261020-070827` (5 foydalanuvchi, post-hoc)
`git rm` qilinadi. Sabab: ularning `tables.md` sida `metrics.json` da yo‘q
sonlar bor edi (300 ms mo‘ljali konstantadan, status kodlari lug‘at
kalitlari, `tables.fmt` dan tashqari formatlash) — generator xatosi (D48),
`80ddcd3` va `0e424d7` da tuzatilgan; ikkala yugurish o‘sha protokol bilan
qayta o‘tkazilgan (`20261020-085406`, `…085659`). Papkalar tarixda qoladi:
`070525` — `f41bfb0` da, `070827` — `98f7b5f` da qo‘shilgan
(`git show f41bfb0 -- experiments/results/locust/20261020-070525`). Ularning
sonlari QADAM 12 da saqlanib qolgan.


---

## Savollar va qarorlar

| # | Savol / ziddiyat | Qaror |
|---|---|---|
| Q0-1 | Ko‘rsatmada `NEUROLEARN_REMEDIATION.md` tilga olingan, lekin u repoda yo‘q edi | Chatdagi spetsifikatsiya o‘zgarishsiz `NEUROLEARN_REMEDIATION.md` ga saqlandi va commit qilindi (`4067215`) |
| Q0-2 | `~/.bashrc` `DATABASE_URL=…@HOST:PORT/…` shablonini eksport qiladi, natijada Django noto‘g‘ri bazaga ulanadi | Repodan tashqaridagi faylga tegilmadi. `config/.env` qiymatlari shell muhitidan ustun (`overwrite=True`, `config/settings.py:26`). Faylni o‘chirish uchun `DJANGO_ENV_FILE=""` (CI va deploy shunday ishlaydi) |
| Q0-3 | Lokal Redis 6379 portni band qilgan | Compose'dagi Redis host porti 6380. Postgres D1 bo‘yicha 5433 |
| Q0-4 | `docker compose` standart holatda ildizdagi `.env` ni o‘qiydi (3-qoida bo‘yicha unga tegish mumkin emas) | Compose faqat `--env-file config/.env` bilan ishga tushiriladi (README, `docker-compose.yml` sarlavhasi). Kuzatiladigan fayllarda parol yo‘q, qiymatlar `${VAR:?}` bilan majburiy |
| Q0-5 | `X_FRAME_OPTIONS="DENY"` frontend'dagi PDF iframe'ini (8080 → 8000) buzadi | Global qiymat `DENY`. Faqat media view (`config/media.py`) `xframe_options_exempt` + `Content-Security-Policy: frame-ancestors 'self' <FRONTEND_ORIGINS>`. Prod'da web-server shu siyosatni qo‘llashi kerak. **Tasdiqlandi** (foydalanuvchi, 2026-10-03) |
| Q0-6 | D15: `IsInstructor` = Instructor guruhi yoki `is_staff`. `Admin` guruhi va superuser qanday? | Ular ham instruktor deb hisoblanadi (oldin `Admin` guruhi yozish huquqiga ega edi). `get_role`: superuser yoki Admin → `admin`. **Tasdiqlandi** (foydalanuvchi, 2026-10-03) |
| Q0-7 | `Course.tsx` spetsifikatsiya bo‘yicha 7-bosqichda ko‘chiriladi, lekin 0-bosqichdagi ruxsat o‘zgarishi talabaning kurs sahifasini va shablonni yuklab olishni darhol buzadi | Ikkala frontend o‘zgarishi minimal hajmda 0-bosqichda qilindi (`6c5a0a7`), shunda ilova bosqichlar orasida ishlab turadi. 7-bosqichdagi qolgan ishlar o‘zgarmaydi. **Tasdiqlandi** (foydalanuvchi, 2026-10-03) |
| Q0-8 | `seed_data` uchun “demo foydalanuvchi” ta’rifi | staff/superuser, `is_simulated=True` yoki `accounts/demo.py` dagi `DEMO_EMAILS`. Boshqa har qanday akkaunt real deb hisoblanadi |
| Q0-9 | `--clear` endi mavzularni o‘chirmaydi, lekin simulyator mavjud slug'lar bilan to‘qnashardi | Simulyator `sim-` prefiksli alohida daraxtdan foydalanadi (`get_or_create`) va real kurikulumga tegmaydi. 8-bosqichda generativ qilib qayta yoziladi |
| Q0-10 | Testlar dev Redis'ga yozardi; `--nomigrations --reuse-db` data migratsiyalarini tekshirmaydi | `conftest.py`: har bir test uchun LocMem kesh. `pytest.ini`: migratsiyalar PostgreSQL'da har safar qo‘llanadi |
| Q0-11 | Test fixture'larida eski demo parol satri bor edi | Hech bir test parol bilan login qilmaydi, shuning uchun `password=None` (foydalanib bo‘lmaydigan parol) |
| Q0-12 | Django'ning tasodifiy kaliti `$`/`#` belgilarini o‘z ichiga olishi mumkin (compose va dotenv interpolatsiyasi) | `SECRET_KEY` `secrets.token_urlsafe(50)` bilan generatsiya qilinadi |
| Q0-13 | Dev PostgreSQL'ga `db.sqlite3` dan ko‘chirilgan ma’lumotlarda shaxsiy ma’lumot bo‘lishi mumkin | Ular faqat lokal docker volume'da (`neurolearn_pgdata`) turadi. Hisobotga faqat qatorlar soni chiqarildi |
| Q0-14 | `STUDENT_MODEL_ENGINE` va `MASTERY_THRESHOLD` eski konstantalari | Hozircha qoldirildi (`config/settings.py` “legacy” bo‘limi). 3- va 4-bosqichlarda olib tashlanadi |
| Q0-15 | drf-spectacular W001/W002 ogohlantirishlari | Xavfsizlikka aloqasi yo‘q. Tegishli view'lar 4–6-bosqichlarda qayta yozilganda serializer'lar qo‘shiladi. P2 sifatida kuzatiladi |
| Q0-16 | Frontend CI lint (71) va tsc (16) bo‘yicha qizil bo‘ladi | Bu kutilgan holat, 7-bosqichda 0 ga tushiriladi. CI masofada ishga tushirilmadi (push yo‘q), YAML sintaksisi tekshirildi |
| Q1-1 | Addendum kirish qismida “6-bo‘limdagi jadval” deyilgan, lekin bosqichlar jadvali 4-bo‘limda | 4-bo‘limdagi jadval ishlatildi (foydalanuvchi ham 4-bo‘limni ko‘rsatgan). Matnga tegilmadi |
| Q1-2 | `session` FK → `TestSessionResult`, lekin bu model spetsifikatsiyada 5-bosqichga yozilgan | Model 1-bosqichda yaratildi: vaznli ball, ballar, o‘tish bali, `passed`, `submitted_at`. Test sessiyasi bahoni shu yerga yozadi. 5-bosqichda javoblar model orqali o‘tadi; `started_at` kerak bo‘lsa, o‘shanda qo‘shiladi |
| Q1-3 | Prior “joriy holatdan” olinishi kerak, lekin holat qatorlari ifloslangan: test sessiyasi `mastery_percentage` ga 0–100 bahoni yozardi, cascade esa 0 urinish bilan P=1.0 yozardi | `prior_from_state`: holat faqat `total_attempts > 0` va `0 < p ≤ 1` bo‘lsa ishlatiladi, aks holda P(L0). Ifloslanish manbai ham to‘xtatildi: test sessiyasi endi bahoni `mastery_percentage` ga yozmaydi (D7 — II bobga yaqinroq). O‘tilgan testdagi `mastery_level` va global unlock 4–5-bosqichgacha qoldi |
| Q1-4 | Addendum 1-bosqichga faqat `review_repeat` enum qiymatini qo‘yadi, D25 qoidasining o‘zi esa qaysi bosqichda ekani aytilmagan | Qoida ledger'da hozir amalga oshirildi (`classify_source`): `adaptive` va `test_session` javoblariga qo‘llanadi, `seed`/`simulated` ga qo‘llanmaydi. Aks holda enum ishlatilmay qoladi va yodlangan javoblar logga “toza” bo‘lib tushadi. Oyna — yangi `THESIS_REVIEW_REPEAT_HOURS=24` (II bobda yo‘q, D25 dan; D6 konstantalari o‘zgarmadi). D25 dagi “iloji bo‘lsa boshqa savol” talabi uchun tanlash oynadagi savollarni oxiriga qo‘yadi (3-bosqich tanlash qoidasining bir qismi oldinroq qilindi) |
| Q1-5 | `attempt_no` qaysi qatorlarni sanaydi? | (talaba, mavzu) bo‘yicha barcha qatorlar, yozilish tartibida, bo‘shliqsiz (`review_repeat` va `legacy` ham). 8-bosqichdagi eksport filtrlangan to‘plam uchun urinish tartibini o‘zi qayta hisoblaydi. Legacy qatorlar `(answered_at, id)` bo‘yicha raqamlandi |
| Q1-6 | `attempt_no` va D25 tasnifi uchun qanday qulf? | Ikki kalitli `pg_advisory_xact_lock(1, hashtext('user:topic'))`. Bir kalitli lock maydoni 2-bosqichdagi KB lock'iga qoldirildi (PostgreSQL'da bu ikki maydon kesishmaydi). Tartib: advisory lock'lar (topic id bo‘yicha saralangan), keyin holat qatori `FOR UPDATE`. SQLite'da no-op (D1 bo‘yicha qo‘llab-quvvatlanmaydi) |
| Q1-7 | D11 faqat `question` va `topic` ni tilga oladi | `selected_choice` va `course` ham `PROTECT`, chunki savol tahrirlanganda variantlarni o‘chirish javoblarni CASCADE bilan o‘chirardi. `session` — `RESTRICT`: foydalanuvchi o‘chirilganda sessiya ham, javoblar ham birga o‘chadi. `history.attempt` — `CASCADE` (hosila qator). `user` → `CASCADE` hozircha qoladi, hard-delete siyosati 8-bosqichda |
| Q1-8 | Arxivlash semantikasi 2-bosqichdagi `archive_node` servisidan oldin kerak bo‘ldi | 1-bosqichda: DELETE → shox arxivlanadi, o‘qish endpoint'larida yashiriladi, javob berish va yangi bola qo‘shish rad etiladi. G_L ni qayta qurish va Y2/Y3 tekshiruvlari bilan birlashtirish 2-bosqichda. Javoblari bor savol uchun mos ravishda `is_active=False` |
| Q1-9 | 3-bosqichgacha log maydonlarini qanday to‘ldirish kerak? | Eski dvigatel aslida ishlatgan qiymatlar yoziladi, `engine_version="<dvigatel>/0"`. `hybrid_bkt_irt/0` θ ni P(G)/P(S) dan **oldin** yangilaydi (TM6 buzilishi) — log shuni ko‘rsatadi. b yangilanmaydi, shuning uchun `b_before = b_after`. `kb_version` 2-bosqichda, `readiness_score`/`was_ready` 4-bosqichda to‘ldiriladi. Bu davrdagi qatorlar eksperimentga baribir kirmaydi (rozilik — 8-bosqich) |
| Q1-10 | Eski `UserKnowledgeHistory` qatorlarini javoblarga bog‘lash | Bog‘lanmadi: ishonchli kalit yo‘q, vaqtga qarab taxminiy bog‘lash noto‘g‘ri bog‘lanish xavfini tug‘diradi. `attempt=NULL` qoldi |
| Q1-11 | `seed_thesis_demo` demo akkauntlarning **barcha** javoblarini o‘chirardi | 4-qoida bo‘yicha: seed yozmagan javob bo‘lsa, buyruq to‘xtaydi. O‘chirish faqat `--reset-demo-answers` bilan. Demo akkauntlar ro‘yxati `accounts.demo.DEMO_EMAILS` dan olinadi |
| Q1-12 | `answered_at`/`created_at` `auto_now_add` edi, shuning uchun seed'lar vaqtni keyin `update()` bilan o‘zgartirardi | `default=timezone.now`. Vaqtni faqat `seed`/`simulated` yozuvlari uchun berish mumkin (`record_attempt` tekshiradi). `UserKnowledgeHistory.created_at` javob vaqtiga teng qilinadi |
| Q1-13 | `test_bayesian.py` dagi parallellik testi bitta savolni ikki marta yuborardi va `OperationalError` ni yutardi | D25 bo‘yicha ikkinchi javob `review_repeat` bo‘ladi. Test ikki xil savol bilan qayta yozildi va endi xatolarni yutmaydi. 10-bosqichdagi to‘liq to‘plam o‘zgarmaydi |
| Q1-14 | `submit_answer` SQL soni oshdi (22 → 25) | Ma’lum va o‘lchangan. `record_attempt` advisory lock'ni qayta oladi (no-op so‘rov). Optimallash 10-bosqichdagi ≤ 12 byudjet bilan birga qilinadi |
| Q1-15 | Frontend repo'da bu sessiya qilmagan, commit qilinmagan o‘zgarishlar bor edi: tutor fayllari o‘chirilgan, landing/auth/profile/README matnlari o‘zgartirilgan | Foydalanuvchi “D24 bo‘yicha flag ortiga” variantini tanladi. O‘chirilgan fayllar qaytarildi va `VITE_ENABLE_TUTOR` ortiga o‘tkazildi (D24: “kod saqlanadi”). Matn o‘zgarishlari saqlanib, `7b549fd` ga kiritildi |
| Q1-16 | Dev bazada 31 ta savol farzandli tugunlarga biriktirilgan (Y4 buzilishi) | 1-bosqichda `topic` savolning hozirgi tuguni sifatida saqlanadi. 2-bosqichdagi `kind` migratsiyasi spetsifikatsiyaga ko‘ra shunday tugunni topganda to‘xtaydi va foydalanuvchidan so‘raydi |
| Q1-17 | Repoda kuzatilmaydigan `NEUROLEARN_VERIFICATION.md` bor | **O‘zgartirildi (foydalanuvchi, 2026-10-03, B2.1):** `NEUROLEARN_VERIFICATION.md`, `NEUROLEARN_UI_ADDENDUM.md` va `NEUROLEARN_B2FIX_B3.md` commit qilinadi; so‘ngra foydalanuvchi so‘rovi bilan `verification/` suite'i va `VERIFICATION_REPORT.md` ham commit qilindi, shunda keyingi sessiyalar tekshiruvni qayta ishga tushira oladi — ular topshiriqning bir qismi va keyingi sessiyalar ularni o‘qishi kerak. (`NEUROLEARN_UI_ADDENDUM.md` allaqachon `8bc4cea` da commit qilingan.) Oldingi qaror: commit qilinmadi, chunki so‘ralmagan edi. Uning V-C9, V-C12 va V-D1 talablari 1-bosqich testlarida hisobga olindi |
| Q1-18 | “Frontendni ham yuqorida aytilgani kabi o‘zgartir” — hajmi noaniq edi: 1-bosqichga moslashmi yoki addendum UI'si (7-bosqich)mi | Foydalanuvchi “1-bosqichga moslash” variantini tanladi. Faqat 1-bosqich backend o‘zgarishlari bilan bog‘liq qismlar qilindi. Addendum sahifalari B2/B4/B6 API'lariga bog‘liq, ular 7-bosqichda qilinadi. Yangi xabarlar hozircha inglizcha, chunki interfeys hali inglizcha; 7-bosqichda D20 bo‘yicha i18n'ga o‘tadi |
| Q2-1 | Dev bazada “Algorithm” ildizi (kurs) ga 31 ta savol biriktirilgan edi (Y4 buzilishi; spetsifikatsiya bo‘yicha to‘xtash va so‘rash kerak) | Foydalanuvchi “savollarni o‘chirish” ni tanladi. Ularga javob yo‘q edi. 31 ta savol va 124 ta variant migratsiyadan oldin, alohida amal sifatida o‘chirildi; zaxira `pg-20261003-1106-before-b2.dump`. Migratsiyaning o‘zi boshqa bazalarda bunday tugunni topsa, ma’lumotni o‘chirmaydi — to‘xtaydi |
| Q2-2 | Spetsifikatsiya: “savollari bor barg → topic; qolganlari → section”. Dev bazada 6 ta bo‘sh barg bor | Foydalanuvchi qarori: bo‘sh barg ham `topic` (II bob: topic — barg). `0011_kb_data` shunday ishlaydi |
| Q2-3 | Yangi tugun qaysi tur bo‘ladi? Topic ostida bola yaratish mumkinmi? | Standart: ildiz → course, aks holda topic. Topic ostida bola yaratish rad etiladi (`parent_is_topic`); avval uni section'ga o‘zgartirish kerak (savoli bo‘lmasa). Avtomatik o‘zgartirish qilinmaydi |
| Q2-4 | Spetsifikatsiyada `delete_node` va oddiy maydonlarni tahrirlash servisi yo‘q, lekin “API ... faqat shu servis orqali yozadi” | `update_node` (nom, slug, pass mark va boshqalar; strukturaviy o‘zgarishlarda versiya oshadi, aks holda oshmaydi) va `delete_node` (javob bo‘lsa — `archive_node`) qo‘shildi |
| Q2-5 | Arxivlangan tugunlar KB'da qanday? | Ular va ularga tegishli relatsiyalar snapshot'ga kirmaydi (G_L, pos). Relatsiya qatorlari bazada saqlanadi; arxivlangan tugunga yangi relatsiya qo‘shib bo‘lmaydi (`archived`) |
| Q2-6 | Graf API'da `edges` kaliti nimani bildiradi? | Mavjud frontend buzilmasligi uchun `edges` E_P (instruktor kiritgani) bo‘lib qoldi. G_L — yangi `leaf_edges` (`inherited`, `via`). `warnings` faqat instruktorlarga |
| Q2-7 | Prerekvizit API'da instruktorlar faqat o‘z mavzularini ko‘radimi? | Yo‘q: prerekvizitlar kurslararo bo‘lishi mumkin (D2), shuning uchun har qanday instruktor barcha faol tugunlar orasida relatsiya qo‘sha oladi. Egalik cheklovi kerak bo‘lsa — 7-bosqichda |
| Q2-8 | Ish davomida tizim qayta yuklandi; snap Docker'ning `neurolearn_pgdata` volume'i yo‘qoldi va dev baza bo‘sh bo‘lib qoldi | Bu sessiyadan tashqarida sodir bo‘ldi. Eng so‘nggi zaxira (`pg-20261003-1132-pre-b2-migrate.dump`) bo‘sh bazaga tiklandi. Qatorlar soni mos keldi, 2-bosqich migratsiyalari qayta qo‘llandi va natija avvalgisi bilan bir xil chiqdi. `db.sqlite3` o‘zgarmagan (`5c33c7d2…`) |
| Q2-9 | `benchmark_tree.py` MPTT ustunlariga bog‘liq edi | O‘chirildi; 9-bosqichda `benchmarks` app'i bilan almashtiriladi. Bu va `test_mptt_tree.py` ning o‘chirilishi xato bilan `5e5cb09` ga tushib qoldi (oldindan stage qilingan edi); tarix qayta yozilmadi |
| Q2-10 | 1-bosqichning migratsiya testi `curriculum 0009` holatiga qaytardi, bu MPTT ustunlarini qayta qo‘shishni talab qilardi | Test endi `curriculum 0012` (joriy) bilan `assessments 0005` kombinatsiyasidan boshlanadi. Curriculum migratsiyalari `assessments 0005` dan keyingilariga bog‘lanmaydi |
| Q8b-1 | Tarixda ikkita `commit --amend` bor (reflog): `c142506` ← `47d78ee` (faqat commit xabari o‘zgargan, daraxt bir xil) va `c1a683b` ← `3f54751` (`provenance.py`/`tables.py` ga 17 qator qo‘shilgan) | D54 bo‘yicha qayd etildi; tarix o‘zgartirilmadi. Bundan keyin amend/rebase/reset --hard ishlatilmaydi, xato xabar keyingi commit'da tuzatiladi |
| D56 | H2 dagi “DKT bilan taqqoslanadigan” iborasining ta’rifi | D56. “DKT bilan taqqoslanadigan” = BKT+IRT(λ=0) − DKT AUC farqi 95% CI pastki chegarasi ≥ −0,01. 0,01 — metodik tanlov, manbadan emas. 2026-10-08 da, to‘liq H2 natijasi mavjud bo‘lmagan paytda yozildi. |
| D57 | Ko‘p-skill'li masalada keyingi qator shu masalaning javobini ko‘radi (sizish) | D57: bashorat faqat talabaning qat’iy oldingi `order_id`'laridan; order qatorlari bir xil holatdan bashorat qilinadi, yangilanish order'dan keyin. Batafsil — “D57” bo‘limi. 2026-10-08, yangi natijadan oldin |
| D58 | D55 D57 protokolida qanday ishga tushiriladi va qanday o‘qiladi | D55 tavsifiy, asosiy natija (0,30; 0,10); uchta savol va Elo nuqtaviy farqi; takrorlanish darvozalari (6 xona) va DKT darvozasi (5e-4, metodik tanlov). Batafsil — “D58” bo‘limi. 2026-10-09, natijadan oldin |
| D59 | D55 ning L-BFGS-B tekshiruvi P0/PT grid'i torligi sababli o‘tmadi; DKT/AKT `problem_id` ni ko‘rmaydi | DEFAULT_GRID: P0 + 0,01; 0,95; PT + 0,005; 0,01; 0,02; 0,03; 0,5 (G/S o‘zgarmaydi); AKT-R (n_pid > 0) qo‘shimcha model; yangi H2 asosiy natija, eski tarixiy; L-BFGS-B 1 % qoladi. Batafsil — “D59” bo‘limi. 2026-10-09, koddan oldin |
| D65 | Hypothesis xossa testlari qanday quriladi; 2.5-tasdiq double'da qayerda qat’iy tekshiriladi | Ikki state machine (sof va PostgreSQL), qabul/rad production kodi bilan; 2.5 qat’iy shakli 1e-9 < P(L) < 1 − 1e-9 da, kuchsiz shakli hamma joyda; posterior 1e-12 aniqlikda. D65a topilmasi (P(L) = 1.0 yutuvchi holat) — model o‘zgartirilmadi, taklif foydalanuvchiga. Batafsil — “D65” bo‘limi. 2026-10-20 |
| D66 | `submit_answer` ≤ 12 SQL: nima sanaladi va qulflar/natijalar o‘zgarmasdan qancha kamaytirish mumkin | HTTP + JWT, haqiqiy tranzaksiya, BEGIN/COMMIT sanalmaydi; 6 ta qayta o‘qish olib tashlandi (25 → 19, 26 → 20, 16 → 11); qolgani alohida qaror talab qiladi, V-F1 yumshoq — test ogohlantiradi. Batafsil — “D66” bo‘limi. 2026-10-20 |
| D67 | Coverage'da “umumiy” va “servislar” nima | `.coveragerc`: backend manba kodi (testlar, migratsiyalar, verification, experiments, scripts chiqarilgan); servislar = `*/services/*`; uchala maqsad CI da majburiy. Batafsil — “D67” bo‘limi. 2026-10-20 |
| D68 | Locust qanday va qaysi ma’lumotda ishga tushiriladi | Alohida `<db>_locust` baza, faqat simulyatsiya (D13), V-F2 kursi (500/1 500), `DEBUG=False` `runserver`, 50 foydalanuvchi × 2 daqiqa, 403/404 kutilgan javob. Yugurishdan oldin commit qilindi. Batafsil — “D68” bo‘limi. 2026-10-20 |

---

## Bog‘liqlik matritsasi (audit topilmalari → vazifa)

Holatlar: **Bajarildi**; **Qisman**; **Kutilmoqda (Bn)** — rejadagi n-bosqichda bajariladi; **Kechiktirildi — sababi**.
Commit qisqartmalari: backend `1d6f286` (repo), `b44df84` (config), `f620171` (auth), `332d56f` (data), `4067215` (docs/CI), `8bc4cea` (addendum), `888a96f` (ledger), `960ba2c` (arxiv); `5e5cb09` (neuro_model), `79b907c` (KB); frontend `a751538`, `6c5a0a7`, `7b549fd` (tutor flag), `2fa1d99` (1-bosqichga moslash), `c259646` (2-bosqichga moslash).

### 0-bo‘lim (asosiy 5 muammo)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| #1 Test oqimi BKT'ni chetlab o‘tadi, 0–100 shkala | P0-1 (B5, B7) | Bajarildi | Backend: har bir test javobi `apply_one_answer` orqali Algoritm 2.4 dan o‘tadi. UI: mashq va test rejimlari aniq ajratildi, `useAdaptiveQuiz` ulandi, baho va P(L) alohida ko‘rsatiladi (`c2bb542`) |
| #2 KB modeli: MPTT, G_L yo‘q, Y2/Y3, qulf yo‘q | P0-4, P1-6, P1-7 (B2) | Bajarildi | `curriculum/services/kb.py`, `neuro_model/graph.py`, `5e5cb09`, `79b907c`; testlar `test_kb.py`, `test_kb_concurrency.py` |
| #3 Talaba modeli II bobga zid | P0-5 (B3) | Bajarildi | `neuro_model/` (bkt, irt, elo, init, student), `assessments/services/student_model.py`; testlar `neuro_model/tests/test_student.py`, `assessments/tests/test_student_model.py` |
| #4 Unlock 4 xil, global `is_unlocked`, cascade | P0-3, P0-6 (B4), P0-2 (B1) | Qisman | Cascade olib tashlandi (`888a96f`, test `test_mastering_a_section_does_not_touch_descendants`); unlock — B4 |
| #5 Log yaroqsiz, sun’iy yozuvlar; maxfiy ma’lumotlar repoda | P0-2, P1-1 (B1); P2-1 (B0) | Bajarildi | Maxfiy qism: `config/settings.py:33-60`, README (B0). Log: `assessments/models.py` (`AssessmentAttempt`), `assessments/services/ledger.py`, `888a96f`; testlar `test_ledger.py` |

### 1-bo‘lim (umumiy tuzilma)

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
| 1.3 Ildizdagi `.env` da token | 3-qoida, 8.4-Q6 | Qisman | `.gitignore:13` da borligi tekshirildi; tokenni bekor qilish foydalanuvchida |
| 1.3 `docker-compose` yo‘q | D1 | Bajarildi | `docker-compose.yml` |
| 1.3 `@supabase/supabase-js` `package.json` da yo‘q, client ishlatilmaydi | D17 (B7) | Bajarildi | `src/integrations/supabase/` butunlay o‘chirildi; `package.json` da supabase yo‘q (`c2bb542`) |
| 1.5 “updated” kabi commit xabarlari | B0 CI va hujjat | Bajarildi | Yangi commit'lar conventional formatda va ID'lar bilan |
| 1.5 Untracked `.agents/`, `graphify-out/` | 8.4-Q8 | Bajarildi | `.gitignore:23-24` |

### 2-bo‘lim (backend)

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
| 2.5 Rollar nomuvofiq (`Instructor` va `is_staff`) | D15, P2-5 | Qisman | Backend: `accounts/permissions.py`, `f620171`; frontend `AdminRoute` — B7 |
| 2.6 Advisory lock yo‘q | BB9 (B2) | Bajarildi | `pg_advisory_xact_lock(KB_LOCK_KEY)` — `curriculum/services/kb.py:_lock`, `79b907c`; mutatsion tekshiruvli poyga testi |
| 2.6 `SubmitTestSessionView` atomar emas | B5 | Bajarildi | Mantiq `assessments/services/test_session.py` ga ko‘chirildi, `@transaction.atomic`; read-modify-write olib tashlandi — hisoblagichlar `readiness.apply_answer` orqali `select_for_update` bilan siljiydi |
| 2.6 `dashboard.py:66` ortiqcha `atomic` | B5 | Bajarildi | Faqat o‘qiydigan endpoint'dan `@transaction.atomic` olib tashlandi (`analytics/views/dashboard.py`) |
| 2.6 SQLite `FOR UPDATE` ni e’tiborsiz qoldiradi | D1 | Bajarildi | Testlar PostgreSQL'da ishlaydi (`pytest.ini`, CI) |

### 3-bo‘lim (frontend)

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

### 4-bo‘lim (algoritmlar)

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
| 4.3 Chegara 3 joyda har xil | TY1, D6 (B4) | Qisman | D6 konstantalari bir joyda (`config/settings.py:266-285`); eski chegaralar B4 da olib tashlanadi |
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
| 4.6 p̂ saqlanmaydi | TM6, TM7 (B1, B3) | Qisman | `AssessmentAttempt.p_hat` va boshqa model maydonlari yoziladi (`888a96f`); II bob formulasi — B3 |
| 4.7 P(L0) o‘zgarmas 0.15 | TM5 (B3) | Bajarildi | `neuro_model/init.py::initial_mastery` — (1−λ)P0 + λm̄, c = τ − C_OFFSET |
| 4.7 Avlodlarga P=1.0 cascade | P0-2, D8 (B1) | Bajarildi | `_cascade_mastery_to_descendants` o‘chirildi (`888a96f`); test `test_mastering_a_section_does_not_touch_descendants` |
| 4.8 Kahn FIFO, lev yo‘q | GR2 (B2) | Bajarildi | `neuro_model/graph.py:topological_order` (heap, `(pos, id)`, lev), `5e5cb09` |
| 4.8 Sikl qoldig‘i jim qo‘shiladi | GR2 (B2) | Bajarildi | `CycleError(remaining)`, `5e5cb09`; test `test_cycle_error_lists_unordered_topics` |
| 4.8 Tugunlar grafida, G_L'da emas | GR2 (B2) | Bajarildi | `neuro_model/graph.py:expand`, `5e5cb09` |
| 4.8 Faqat testlarda ishlatiladi | B2, B6 | Qisman | Snapshot daraxt/graf API, savol tanlash va ledger'da ishlatiladi (`79b907c`); trayektoriya — B6 |
| 4.9 To‘rtta alohida evristika | TR2, ES7 (B6) | Bajarildi | To‘rtta evristika olib tashlandi; dashboard `trajectory.for_learner` dan foydalanadi, test `test_the_dashboard_reports_the_trajectory_not_four_heuristics` |
| 4.9 Sabablar yo‘q | TR3 (B6) | Bajarildi | Har bir element `{code, params}` qaytaradi (`review_impact`, `in_progress`, `ready`, `blocked`); matn frontend lug‘atida (D20) |
| 4.9 Tartib `position` bo‘yicha | D4 (B2, B6) | Qisman | Global `pos` (D4) — snapshot, daraxt API va admin shu tartibda (`79b907c`); trayektoriya — B6 |
| 4.9 Easy-skip sun’iy yozuvlar | P0-2, D8 (B1) | Bajarildi | `_maybe_skip_easy_questions` o‘chirildi (`888a96f`); testlar `test_easy_skip_probe_writes_only_real_answers`, `test_only_the_ledger_creates_attempts` |

### 5-bo‘lim (II bob talablari)

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
| TM7 Log maydonlari | B1 | Qisman | Maydonlar, cheklovlar va yozish yo‘li tayyor (`888a96f`). `kb_version` B2 da, `readiness_score`/`was_ready` B4 da to‘ldiriladi, II bob qiymatlari B3 dan |
| TY1 Histerezis M (τ, δ) | B4 | Bajarildi | `neuro_model/readiness.py::mastered_flag`; M saqlanadi, chunki band ichida avvalgi qiymatga bog‘liq |
| TY2 R faqat G_L orqali, fallback'siz | B4 | Bajarildi | `Pre(w)` snapshot'ning G_L'idan; ota tugunga fallback yo‘q, test `test_a_mastered_parent_does_not_open_its_child` |
| TY3 `missing_count` hisoblagichi | B4 | Bajarildi | `StudentTopicState.missing_count`, inkremental `propagate`, TY6 uchun `recompute_counters` |
| TY4 r_s(w) + tushuntirish | B4, B7 | Qisman | Backend: `readiness.readiness_at` r_s(w) va R_s(w) ni hisoblaydi va ular har bir javobda ledger'ga (`readiness_score`, `was_ready`) yoziladi; 403 tanasi yetishmayotganlarni nomi va P(L) bilan beradi. UI tushuntirishi — 7-bosqich |
| TY5 Boshlangan mavzu yopilmaydi | B4 | Bajarildi | `next_status` + DB cheklovi; test `test_ty5_a_new_prerequisite_does_not_close_a_started_topic` |
| TY6 KB versiyasi bo‘yicha qayta hisoblash | B4 | Bajarildi | `StudentTopicState.kb_version` va `readiness.resync` (O(n+m)); test `test_ty6_*` |
| TR1 5 ta holat | B4, B7 | Qisman | Backend bajarildi (B4): `TopicStatus` va o‘tishlar; `GET /api/config/model/` holatlar ro‘yxatini beradi. UI nishonlari — B7 |
| TR2 A–D guruhlari | B6 | Bajarildi | `neuro_model/trajectory.py::trajectory`; A — ta’sir ↓ va P ↑, B/C/D topologik tartibda |
| TR3 Sabablar | B6 | Bajarildi | `Reason(code, params)`; test sabab matn emas, kod va sonlar ekanini tasdiqlaydi |
| TR4 Need_s(g) | B6 | Bajarildi | `need` va `path_to`; etalon Need(t7) = {t4, t6}, yo‘l t4 → t6 → t7 |
| TR5 Frontend'da ko‘rsatish | B7 | Bajarildi | `NextStepCard` va `TrajectoryGroups` — A–D guruhlari sabablari bilan bosh sahifada va O‘quv yo‘lida (`c2bb542`) |
| EX1 Anonim pyKT eksporti | B8 | Kutilmoqda (B8) | — |
| EX2 Oflayn baholash | B8 | Kutilmoqda (B8) | — |
| EX3 Metrikalar | B8 | Kutilmoqda (B8) | — |
| EX4 Statistika | B8 | Kutilmoqda (B8) | — |
| EX5 Benchmark | B9 | Bajarildi (kod) | `benchmarks/` app'i: `MpttNode` va `CteNode`, uchta shakl, 10³–10⁵, oltita amal, parallel yozish (qulfsiz va qulfli), Y1 va oraliq tekshiruvlari, `manage.py run_tree_benchmark` (D63, D63a). Natija alohida bazada, D48 verify bilan |
| EX6 Rozilik va anonimlashtirish | B8 | Kutilmoqda (B8) | `is_simulated` belgisi qo‘shildi (`332d56f`) |
| SN1 Unit testlar | B2–B6, B10 | Bajarildi | II bob algoritmlari uchun unit va etalon testlar (B2–B6), B10 da xossa testlari (`8f1f36f`), `accounts` (`fbf2f4d`), SQL byudjeti (`601cea3`), Locust vositalari (`5ab628e`, `0e424d7`); backend 1 270 test, coverage `neuro_model` 99 %, servislar 97 %, umumiy 90 % (QADAM 12) |
| SN2 Hypothesis | B10 | Bajarildi | `neuro_model/tests/test_properties.py`, `curriculum/tests/test_kb_properties.py` — state machine'lar, 6 ta invariant + rad etilgan amal holatni o‘zgartirmaydi; kiritilgan xatolar 4/4 va 6/6 ushlandi (`8f1f36f`, D65) |
| SN3 Locust | B10 | Bajarildi | `benchmarks/locustfile.py`, `load_test.py`, `seed_load_test` (`5ab628e`, D68); natija `experiments/results/locust/20261020-085406` (50 foydalanuvchi, 0 xato) va post-hoc `085659` (5 foydalanuvchi) (`e836b2f`, `4aee869`). V-F2 mo‘ljali 50 foydalanuvchida bajarilmadi — QADAM 12 |

### ES (eski muammolar)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| ES1 DFS tugunlar grafida | B2 | Bajarildi | G_L bo‘yicha BFS, `5e5cb09` |
| ES2 θ=0.70 + fallback | B4 | Bajarildi | Qat’iy chegara va fallback olib tashlandi: M — τ/δ gisterezis, meros faqat G_L orqali |
| ES3 MPTT | B2 | Bajarildi | tree-queries, `79b907c` |
| ES4 Chiziqli G/S | B3 | Bajarildi | chiziqli G/S olib tashlandi, o‘rniga chegaralangan sigmoid |
| ES5 θ talaba×mavzu | B3 | Bajarildi | θ endi kurs bo‘yicha (D33) |
| ES6 η=0.3 | B3 | Bajarildi | K(n) = ELO_ALPHA/(1+ELO_BETA·n), o‘zgarmas η emas |
| ES7 Alohida tavsiya funksiyalari | B6 | Bajarildi | Bitta servis (`assessments/services/trajectory.py`); so‘rovlar byudjeti testi har qo‘shimcha mavzuga <0.5 so‘rov |
| ES8 Simulyatsiya va baholash | D13 (B0, B1, B8) | Qisman | `is_simulated` va alohida `sim-` daraxti (`332d56f`); `source=simulated` (`888a96f`, test `test_simulator_labels_its_rows`); generator — B8 |

### 6-bo‘lim (eksperimentlarga tayyorlik)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| Logda `topic`, `attempt_no`, p̂ yo‘q | P1-1 (B1) | Bajarildi | `assessments/models.py` (`AssessmentAttempt`), migratsiyalar `0006`–`0008`, `888a96f`; test `test_legacy_rows_are_numbered_and_labelled` |
| Easy-skip yozuvlari belgilanmagan | D8, D10 (B1) | Bajarildi | Mavjud qatorlar `source=legacy` (eksperimentdan chiqariladi), yangi sun’iy yozuvlar yo‘q (`888a96f`) |
| Test sessiyasi yozuvlarida tarix yo‘q | D7 (B5) | Bajarildi | `apply_one_answer` moslashuvchan yo‘l bilan bir xil: trace, tarix va `session` FK |
| Seed vaqt tamg‘alarini qayta yozadi | B1 | Bajarildi | `seed_thesis_demo.py`, `seed_data.py` vaqtni yaratishda beradi, `update()` yo‘q; ledger `update` ni bloklaydi (`888a96f`); test `test_seed_thesis_demo_writes_seed_rows_and_leaves_others_alone` |
| Tugun o‘chirilsa javoblar CASCADE bilan o‘chadi | D11 (B1) | Bajarildi | `960ba2c`; `test_archive.py` |
| Foydalanuvchi hard-delete javoblarni o‘chiradi | D11 (B8) | Kutilmoqda (B8) | — |
| `seed_data` so‘ramasdan hammasini o‘chiradi | P2-7 | Bajarildi | `curriculum/management/commands/seed_data.py:20-45`; testlar `test_seed_safety.py` |
| `simulate --clear` real akkauntlarni hard-delete qiladi | P2-7, P2-8 | Bajarildi | `assessments/management/commands/simulate_bkt_data.py:52-57` |
| Anonim eksport yo‘q | EX1 (B8) | Kutilmoqda (B8) | — |
| pyKT/pyBKT/DBE-KT22/ASSISTments yo‘q | EX2 (B8) | Qisman | ASSISTments 2009 (`datasets/assist09.py`, D50), pyKT DKT/AKT/AKT-R va pyBKT cross-check (D53, D59), Junyi (`datasets/junyi.py`, D61). DBE-KT22 — pastdagi qator |
| DBE-KT22 yuklovchisi (javoblar bilan) | 8b-3 | **Kechiktirildi — ma’lumot manbasi ochilmadi (D61)** | ADA kirish so‘rovi javobsiz qoldi; o‘rniga Junyi Academy (2015) ishlatiladi (D61, foydalanuvchi ruxsati bilan). DBE-KT22 **grafi** bor va ishlatilgan (`datasets/graphs.py`, D51; `graph_report` ikkala yo‘nalishda). Kod yozilmadi: ma’lumoti yo‘q yuklovchi son chiqarmaydi (D48) |
| Annotatsiya vositasi (`experiments/graphs/annotate.py`), Cohen κ | 8b-3 | **Kechiktirildi — annotator yo‘q (D61)** | Ikki mustaqil annotator yo‘q, shuning uchun κ “hisoblanmadi — annotator yo‘q” bo‘lib qoladi (D13). O‘rniga Junyi ning o‘z annotatsiya fayllari bilan **tavsifiy** moslik yozildi (D61: 1 131 juftlik, AUC 0,6824 / 0,5595) |
| AUC/RMSE/statistika yo‘q | EX3, EX4 (B8) | Kutilmoqda (B8) | — |
| Benchmark zaif | EX5 (B9) | Bajarildi (kod) | Eski `benchmark_tree.py` o‘chirilgan (`5e5cb09`); o‘rniga `benchmarks/` — PostgreSQL, yozish va parallel yozish, mediana va p95, uchta shakl, 10³–10⁵, yaxlitlik tekshiruvlari (D63) |
| Simulyator generativ emas | B8 | Kutilmoqda (B8) | — |
| H1 tayyorligi | B1, B4, B8 | Qisman | B1: `readiness_score`, `was_ready` maydonlari (`888a96f`). 8b-3: `experiments/h1.py` — to‘rtta qoida, teng qamrov uchun τ qidirish, τ×δ sezgirligi, r_s(w) AUC; r_s(w)/R/M `neuro_model.readiness` dan (D61, D62). Natija Junyi log'i yuklanishini kutadi |
| H2 tayyorligi | B3, B8 | Bajarildi | `experiments/h2.py`, to‘liq natija `experiments/results/assist09/20261010-060005/` (D53, D57, D59); sezgirliklar D55 va D60 |
| H3 tayyorligi | B3, B8 | Qisman | `experiments/h3.py` — BKT+IRT+Pre to‘rt graf arm'i bilan (asl, teskari, daraja saqlangan tasodifiy ×20, grafsiz), λ validatsiyada; `BKTFamily(graph=…)` (D61, D62). Natija Junyi log'i yuklanishini kutadi |
| H4 tayyorligi | B2, B9 | Qisman | B2: CTE (django-tree-queries) asosiy model, `79b907c`. B9: `benchmarks/` app'i va `run_tree_benchmark` (D63, D63a), ρ va juftlashtirilgan bootstrap bilan o‘qish qoidasi. To‘liq run kutilmoqda |

### 7-bo‘lim (testlar va sifat)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| 7.1 `test_test_session.py:140` 100.0 ni tasdiqlaydi | B5 | Bajarildi | Test endi `p_mastery` ∈ [0,1] ni, bahodan farqli bo‘lishini va `rebuild_student_states` natijasiga teng bo‘lishini tekshiradi |
| 7.1 Parallellik testi `OperationalError` ni yutadi | B10 | Bajarildi | Xatoni yutadigan test olib tashlangan (B1); PostgreSQL'da haqiqiy parallellik: `assessments/tests/test_ledger.py:423` (10 ta parallel `process_submission`, V-D1) va `:462`, `curriculum/tests/test_kb_concurrency.py:48`; ular B10 dagi qulf o‘zgarishidan keyin ham o‘tadi (`601cea3`) |
| 7.1 `accounts` testlari yo‘q | B10 | Bajarildi | `accounts/tests/test_accounts.py` (27 test: ro‘yxatdan o‘tish, D15/Q0-6 rollar, rozilik maydonlari, D11, JWT cookie, blacklist, CSRF) + mavjud 60 test = 87; topilgan 500 xatosi tuzatildi (`fbf2f4d`) |
| 7.1 Frontend testi trivial | B7 | Qisman | 9 ta yangi vitest testi (`apiError`, delete natijalari, tutor flag), `2fa1d99`, `7b549fd`; 7-bosqich testlari — B7 |
| 7.2 Coverage 68% | B10 | Bajarildi | `.coveragerc` (D67), CI da majburiy: `neuro_model` 99 % (≥ 95), servislar 97 % (≥ 85), umumiy 90 % (≥ 80) (`3e71a32`, QADAM 12) |
| 7.2 Lint 71 error | P2-6 (B7) | Bajarildi | lint: 71 error → **0 error** (8 ogohlantirish qoldi: 7 tasi shadcn `ui/` fayllarida, 1 tasi `AuthContext`) (`c2bb542`) |
| 7.2 tsc 18 xato | P2-6 (B7) | Bajarildi | tsc: 16 xato → **0** (`c2bb542`) |
| 7.2 Bundle 2.36 MB | B7 | Qisman | Tutor lazy chunk'ga ajratildi: asosiy bundle 2.22 MB (`7b549fd`); marshrutlar bo‘yicha `React.lazy` — B7 |
| 7.3 `SECRET_KEY` git'da | P2-1 | Bajarildi | `config/settings.py:35-40`; eski kalit tarixda qoldi (buzilgan deb hisoblanadi) |
| 7.3 `DEBUG=True` | P2-1 | Bajarildi | `config/settings.py:33` |
| 7.3 `ALLOWED_HOSTS=["*"]` | P2-1 | Bajarildi | `config/settings.py:42-45` |
| 7.3 CORS hammaga + credentials | P2-1 | Bajarildi | `config/settings.py:49-51` |
| 7.3 `X_FRAME_OPTIONS="ALLOWALL"` | P2-1 | Bajarildi | `config/settings.py:54`, `config/media.py` |
| 7.3 Demo parollar git'da | P2-1 | Bajarildi | `README.md`, `accounts/demo.py`, `332d56f` |
| 7.3 `.env` dagi token | 3-qoida | Qisman | gitignored ekani tekshirildi; bekor qilish foydalanuvchida |
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
| 7.4 Bir javobga 12–20 SQL | B10 (byudjet ≤ 12) | Qisman — ≤ 12 faqat `review_repeat` (11) da; oddiy javob 19, M o‘zgarishi 20: qolganini kamaytirish qulf/manba/yozuvni o‘zgartiradi (D66, foydalanuvchi qarori) | 25 → 19, 26 → 20, 16 → 11; aniq sonlar `assessments/tests/test_query_budget.py` da (`601cea3`) |

### 8.3 (ustuvorliklar ro‘yxati)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| P0-1 Test sessiyasi BKT'ni chetlab o‘tadi | B5, B7 | Qisman | Backend bajarildi (D7: javoblar model orqali, baho alohida). UI — B7 |
| P0-2 Cascade va easy-skip | B1 | Bajarildi | `888a96f`; `test_ledger.py` |
| P0-3 Talabaga xos tayyorlik | B4 | Bajarildi | `StudentTopicState` (user, topic) va `assessments/services/readiness.py` |
| P0-4 G_L, Y2, Y3, qulf | B2 | Bajarildi | `5e5cb09`, `79b907c` |
| P0-5 Talaba modeli | B3 | Bajarildi | `neuro_model/` + `assessments/services/student_model.py`, yagona dvigatel `thesis_hybrid/1` |
| P0-6 Yagona unlock servisi | B4 | Bajarildi | Yagona servis; to‘rtta eski implementatsiya olib tashlandi |
| P1-1 Logni kengaytirish | B1 | Bajarildi | `888a96f`; `test_ledger.py`, `test_ledger_migration.py` |
| P1-2 pyKT eksporti, rozilik | B8 | Kutilmoqda (B8) | — |
| P1-3 Oflayn baholash | B8 | Kutilmoqda (B8) | — |
| P1-4 Metrikalar va statistika | B8 | Kutilmoqda (B8) | — |
| P1-5 Benchmark | B9 | Kutilmoqda (B9) | — |
| P1-6 tree-queries'ga ko‘chirish | B2 | Bajarildi | `79b907c` |
| P1-7 Kahn, Desc*, κ, kesh | B2 | Bajarildi | `5e5cb09`, `79b907c` |
| P1-8 Trayektoriya | B6, B7 | Kutilmoqda | — |
| P1-9 Hypothesis va Locust | B10 | Bajarildi | SN2 va SN3 qatorlari (`8f1f36f`, `5ab628e`, `e836b2f`) |
| P2-1 Maxfiy qiymatlar va xavfsizlik sozlamalari | B0 | Bajarildi | `b44df84`, `332d56f` |
| P2-2 Requirements sinxronligi | B0 | Bajarildi | `1d6f286` |
| P2-3 `InvalidMove` → 400, Redis chidamliligi, prerekvizit API | B0 (Redis), B2 | Bajarildi | Redis (`b44df84`, `f620171`); Y1/400 va prerekvizit API (`79b907c`) |
| P2-4 N+1 | B2, B5, B10 | Bajarildi | Sikl tekshiruvi N+1 yo‘q (`79b907c`); `TestsListView`, `SubmitTestSession` — B5; `trajectory` so‘rovlari mavzu soniga bog‘liq emas (`test_trajectory.py`), `submit_answer` dagi qayta o‘qishlar olib tashlandi va sonlar qotirildi (`601cea3`) |
| P2-5 Rollarni bir xil qilish | B0 (backend), B7 (frontend) | Qisman | `accounts/permissions.py`, `f620171` |
| P2-6 Frontend lint/tsc, o‘lik kod | B7 | Qisman | `arms_cache` va CI (`a751538`); qolgani B7 |
| P2-7 Xavfli seed buyruqlari | B0 | Bajarildi | `332d56f` |
| P2-8 CASCADE va hard-delete | B0 (simulator), B1, 8a | Bajarildi | `simulate --clear` cheklandi (`332d56f`); PROTECT va arxivlash (`888a96f`, `960ba2c`); hard-delete siyosati D11 bo‘yicha: rozilik bo‘lsa javoblar psevdonim bilan qoladi, aks holda o‘chiriladi (`accounts/tasks.py`, `CustomUser.anonymise`, `dc3c35c`) |

### 8.4 (javob topilmagan savollar)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| Q1 Natijalar qaysi ma’lumotdan? | D13 | Bajarildi (qaror) | D13: simulyatsiya hech qachon natija uchun ishlatilmaydi |
| Q2 `db.sqlite3` da real ma’lumot bormi? | 2-qoida | Bajarildi (qaror) | Bor deb hisoblanadi; zaxira olindi, hisobotga faqat qatorlar soni chiqarildi |
| Q3 PostgreSQL | D1 | Bajarildi | `docker-compose.yml`, `b44df84` |
| Q4 Kurs modeli | D2 (B2) | Bajarildi | Kurs = ildiz (`kind=course`), `79b907c`; θ kurs bo‘yicha — B3 |
| Q5 α, β, λ va parametrlar manbasi | D6, `calibrate_bkt` (B3) | Bajarildi | Konstantalar `config/settings.py` `THESIS_MODEL`; kalibrlash `calibrate_bkt` (grid search, ixtiyoriy pyBKT) |
| Q6 `.env` dagi token | 3-qoida | Qisman | Fayl gitignored; bekor qilish foydalanuvchida |
| Q7 `token_blacklist` | D16 | Bajarildi | `config/settings.py:86`, test |
| Q8 `graphify-out/`, `.agents/` | B0 | Bajarildi | `.gitignore` (kuzatilmaydi) |

### UI qo‘shimchasi (`NEUROLEARN_UI_ADDENDUM.md`, D20–D29)

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
| A4-7 Bo‘lim va kurslar uchun `mastered/total` (D22) | B4 | Qisman | Backend: bo‘lim/kursda holat qatori yo‘q (D22), ular standart qiymatlar bilan keladi; `k / n` UI'da — 7-bosqich |
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
| D22 Holat faqat `topic` turida, bo‘lim/kurs — `k / n` | B2 (`kind`), B4 (backend), B7 (UI) | Qisman | B2 qismi (`kind`) bajarildi, `79b907c`; holatlar — B4, UI — B7 |
| D23 Soxta ma’lumot yo‘q, har bir son API'dan | B6 (endpoint'lar), B7 (grep), 7.1 (D40) | Bajarildi | Profil, xatolar, heatmap va qidiruv sahifasidagi soxta massivlar olib tashlandi; `grep` toza, buni test ham tekshiradi (`c2bb542`). Qidiruv `GET /api/learning/search/` ustida qaytdi: nomlar bilimlar bazasidan, holat va P(L) talaba holatidan, bo‘lmagan qiymat `null` (D40, `f7bd3af`, `02e3b2f`) |
| D24 `VITE_ENABLE_TUTOR=false`, menyuda yo‘q | B7 | Bajarildi | `src/lib/features.ts`, `src/App.tsx`, `src/components/layout/Header.tsx`, `7b549fd`; test `src/lib/features.test.ts` |
| D25 Xatolar backend'dan, “Qayta yechish”, `review_repeat` | B1 (ledger), B6 (endpoint), B7 (UI, `mistakeStorage` olib tashlash) | Qisman | B1 qismi bajarildi (A4-1); savol tanlash oynadagi savollarni oxiriga qo‘yadi (`question_selection.py`, test `test_next_question_prefers_questions_outside_the_window`) |
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
| 2.8 Profil: real ma’lumot, rozilik, hisobni o‘chirish, parol | B6, B7, 8a | Qisman | Real ma'lumot `GET /api/me/summary/` dan (`c2bb542`). Rozilik kartasi: beshta fakt va bitta tugma, bekor qilish keyingi eksportlarga tegishli ekani ochiq aytilgan (`3345a52`, test `Profile.consent.test.tsx`). Hisobni o'chirish va parolni almashtirish D42–D45 ga kirmaydi — qilinmadi; backend `DELETE /api/accounts/profile/` bor, interfeys yo'q |
| 2.9 Quiz: test natijasi (P(L) oldin → keyin, ochilgan mavzular), mashq rejimi, klaviatura | B5, B7 | Bajarildi | Test natijasida baho va model holati alohida; mashq rejimi bir vaqtda bitta savol, darhol tushuntirish, holat o‘zgarsa toast; klaviatura A–D va Enter (`c2bb542`) |
| 2.10 Xatolar ustida ishlash: `GET /api/learning/mistakes/`, guruhlash, “ko‘rib chiqilgan” belgisi | B6, B7 | Bajarildi | `MistakesView` va `MistakeReview` (`3add9ef`); sahifa mavzular bo‘yicha guruhlangan, “tozalash” tugmasi yo‘q, faqat “ko‘rib chiqildi” belgisi (`c2bb542`) |
| 2.11 Umumiy: loading/bo‘sh/xato holatlari, konsol, responsive, `React.lazy`, `data-testid`, `docs/ui/` skrinshotlari | B7, 7.1 (D41) | Qisman | loading/bo‘sh/xato holatlari, `React.lazy` barcha marshrutlarda, `data-testid` asosiy elementlarda (`c2bb542`). Skrinshotlar: `scripts/screenshots.mjs` — 13 sahifa × 1440/1280/768 px, o‘zbek tili, deterministik, `manifest.json` bilan; `docs/ui/README.md` (D41, `02e3b2f`, `f7bd3af`). PNG fayllar hali olinmagan — brauzer va to‘ldirilgan baza foydalanuvchi mashinasida |
| 3 Qabul: mock massivlar yo‘q; bir mavzu barcha sahifalarda bir xil holat va P(L) (vitest/Playwright); “2PL”, “PROOF”, “70%”, “dynamically match” matnlari yo‘q | B7 | Bajarildi | Mock massivlar yo‘q; bir mavzu to‘rtta sahifada bir xil holat va P(L) — `src/test/one-vocabulary.test.tsx`; taqiqlangan matnlar yo‘q (`c2bb542`) |
| 5 LLM tushuntirishlari dizayni (o‘qituvchi tasdiqlaydi, kesh, eksperimentga ta’sir nazorati) | — | Kechiktirildi — D26: 8–10-bosqichlardan keyin, flag ortida | — |
