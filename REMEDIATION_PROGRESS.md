# NeuroLearn — tuzatish jarayoni (REMEDIATION_PROGRESS)

> **Foydalanuvchi ko‘rsatmasi (asl matn):** Backend ildizida ikkita fayl bor: NEUROLEARN_REMEDIATION.md (topshiriq) va NEUROLEARN_AUDIT.md (audit). Avval ikkalasini to‘liq o‘qi. Keyin topshiriqdagi "Ish qoidalari"ga amal qilib, 0-bosqichdan boshla. Har bir bosqich oxirida REMEDIATION_PROGRESS.md ni yangila, commit qil va menga qisqa hisobot ber. Keyingi bosqichga men "davom et" deganimdan keyin o‘t. Agar REMEDIATION_PROGRESS.md allaqachon mavjud bo‘lsa, ishni u yerda to‘xtagan joydan davom ettir.

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
| 3 — Talaba modeli | Kutilmoqda | — | — |
| 4 — Tayyorlik va holatlar | Kutilmoqda | — | — |
| 5 — Test sessiyasi modeldan o‘tadi | Kutilmoqda | — | — |
| 6 — Trayektoriya va API | Kutilmoqda | — | — |
| 7 — Frontend | Kutilmoqda | — | — |
| 8 — Eksperimentlar va rozilik | Kutilmoqda | — | — |
| 9 — Saqlash usullari benchmarki | Kutilmoqda | — | — |
| 10 — Sinovlar, samaradorlik, yakuniy hisobot | Kutilmoqda | — | — |

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
| Q1-17 | Repoda kuzatilmaydigan `NEUROLEARN_VERIFICATION.md` bor | Bu mustaqil tekshiruvchi sessiyaning topshirig‘i. Commit qilinmadi, chunki bu so‘ralmagan. Uning V-C9, V-C12 va V-D1 talablari 1-bosqich testlarida hisobga olindi |
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

---

## Bog‘liqlik matritsasi (audit topilmalari → vazifa)

Holatlar: **Bajarildi**; **Qisman**; **Kutilmoqda (Bn)** — rejadagi n-bosqichda bajariladi; **Kechiktirildi — sababi**.
Commit qisqartmalari: backend `1d6f286` (repo), `b44df84` (config), `f620171` (auth), `332d56f` (data), `4067215` (docs/CI), `8bc4cea` (addendum), `888a96f` (ledger), `960ba2c` (arxiv); `5e5cb09` (neuro_model), `79b907c` (KB); frontend `a751538`, `6c5a0a7`, `7b549fd` (tutor flag), `2fa1d99` (1-bosqichga moslash), `c259646` (2-bosqichga moslash).

### 0-bo‘lim (asosiy 5 muammo)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| #1 Test oqimi BKT'ni chetlab o‘tadi, 0–100 shkala | P0-1 (B5, B7) | Kutilmoqda (B5, B7) | — |
| #2 KB modeli: MPTT, G_L yo‘q, Y2/Y3, qulf yo‘q | P0-4, P1-6, P1-7 (B2) | Bajarildi | `curriculum/services/kb.py`, `neuro_model/graph.py`, `5e5cb09`, `79b907c`; testlar `test_kb.py`, `test_kb_concurrency.py` |
| #3 Talaba modeli II bobga zid | P0-5 (B3) | Kutilmoqda (B3) | — |
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
| 1.3 `@supabase/supabase-js` `package.json` da yo‘q, client ishlatilmaydi | D17 (B7) | Kutilmoqda (B7) | Tutor `VITE_ENABLE_TUTOR` ortida (`7b549fd`); ishlatilmaydigan client'ni olib tashlash — B7 |
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
| 2.4 `learning_path/tree` dagi `mastery_percentage` aslida `score` | D5 (B4) | Kutilmoqda (B4) | — |
| 2.5 JWT blacklist ishlamaydi | D16 | Bajarildi | `config/settings.py:86`; test `test_rotated_refresh_token_is_blacklisted` |
| 2.5 Rollar nomuvofiq (`Instructor` va `is_staff`) | D15, P2-5 | Qisman | Backend: `accounts/permissions.py`, `f620171`; frontend `AdminRoute` — B7 |
| 2.6 Advisory lock yo‘q | BB9 (B2) | Bajarildi | `pg_advisory_xact_lock(KB_LOCK_KEY)` — `curriculum/services/kb.py:_lock`, `79b907c`; mutatsion tekshiruvli poyga testi |
| 2.6 `SubmitTestSessionView` atomar emas | B5 | Qisman | B1: yozuvlar `transaction.atomic` ichida, holat qatori `select_for_update` bilan (`assessments/views/assessment.py`, `888a96f`). Servisga ko‘chirish — B5 |
| 2.6 `dashboard.py:66` ortiqcha `atomic` | B5 | Kutilmoqda (B5) | — |
| 2.6 SQLite `FOR UPDATE` ni e’tiborsiz qoldiradi | D1 | Bajarildi | Testlar PostgreSQL'da ishlaydi (`pytest.ini`, CI) |

### 3-bo‘lim (frontend)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| 3.1 Talaba sahifasi o‘qituvchi endpoint'idan foydalanadi | D15 | Bajarildi | `src/pages/Course.tsx:63-66`, `6c5a0a7` |
| 3.1 `AdminRoute` faqat `is_staff` ni tekshiradi | P2-5 (B7) | Kutilmoqda (B7) | — |
| 3.2 Tokenlar `localStorage` da | D16 (B7) | Kutilmoqda (B7) | — |
| 3.2 react-query ishlatilmaydi | D19 (B7) | Kutilmoqda (B7) | — |
| 3.3 Prerekvizit muharriri yo‘q | B7 | Kutilmoqda (B7) | — |
| 3.3 `KnowledgeGraph.tsx` o‘lik kod | P2-6 (B7) | Kutilmoqda (B7) | — |
| 3.4 3 ta holat (5 ta kerak) | TR1, TR5 (B7) | Kutilmoqda (B7) | — |
| 3.4 Bir tugun — ikki xil son | D5 (B4, B7) | Kutilmoqda (B4, B7) | — |
| 3.4 Yopiq tugunda umumiy toast | TY4 (B4, B7) | Kutilmoqda (B4, B7) | — |
| 3.4 Tavsiya sabablari frontend'da qattiq yozilgan | TR3 (B6, B7) | Kutilmoqda (B6, B7) | — |
| 3.4 “0.8%” / “100%” shkala xatosi | D5, P0-1 (B5, B7) | Kutilmoqda (B5, B7) | — |
| 3.4 `useAdaptiveQuiz` ulanmagan | P0-1 (B7) | Kutilmoqda (B7) | — |

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
| 4.3 Unlock 4 xil implementatsiya | P0-6 (B4) | Kutilmoqda (B4) | — |
| 4.3 Global `Topic.is_unlocked` | D9 (B4) | Kutilmoqda (B4) | — |
| 4.3 Ochiq mavzu qayta yopiladi | TY5 (B4) | Kutilmoqda (B4) | — |
| 4.3 Yopiq mavzuga javob berish mumkin | D9 (B4) | Kutilmoqda (B4) | — |
| 4.3 Chegara 3 joyda har xil | TY1, D6 (B4) | Qisman | D6 konstantalari bir joyda (`config/settings.py:266-285`); eski chegaralar B4 da olib tashlanadi |
| 4.4 BKT parametrlari global | TM1 (B3) | Kutilmoqda (B3) | — |
| 4.4 `_retrieve_prior` `algorithm_used` ni filtrlamaydi | B1 | Bajarildi | `_retrieve_prior` o‘chirildi, prior holatdan: `assessments/services/engines/bayesian.py:prior_from_state`, `888a96f`; test `test_hybrid_trace_is_stored_and_prior_comes_from_state` |
| 4.4 Test sessiyasi tarixga yozmaydi | D7 (B5) | Kutilmoqda (B5) | B1: javoblar ledger'da `session` FK bilan, baho `TestSessionResult` da (`888a96f`) |
| 4.4 Tarix attempt'ga FK'siz | B1 | Bajarildi | `UserKnowledgeHistory.attempt` (OneToOne), `888a96f`; eski qatorlar bog‘lanmagan (Q1-10) |
| 4.5 Chiziqli G/S | TM2, ES4 (B3) | Kutilmoqda (B3) | — |
| 4.5 P(G) 0.5 gacha chiqadi | TM2 (B3) | Kutilmoqda (B3) | — |
| 4.6 θ talaba×mavzu uchun | TM3, ES5 (B3) | Kutilmoqda (B3) | — |
| 4.6 b yangilanmaydi | TM4 (B3) | Kutilmoqda (B3) | — |
| 4.6 K o‘zgarmas | TM4, ES6 (B3) | Kutilmoqda (B3) | — |
| 4.6 θ cheklanmagan | D6 `THETA_CLAMP` (B3) | Kutilmoqda (B3) | Konstanta `config/settings.py:276` |
| 4.6 Tanlash va yangilashda θ nomuvofiq | B3 savol tanlash | Kutilmoqda (B3) | — |
| 4.6 p̂ saqlanmaydi | TM6, TM7 (B1, B3) | Qisman | `AssessmentAttempt.p_hat` va boshqa model maydonlari yoziladi (`888a96f`); II bob formulasi — B3 |
| 4.7 P(L0) o‘zgarmas 0.15 | TM5 (B3) | Kutilmoqda (B3) | — |
| 4.7 Avlodlarga P=1.0 cascade | P0-2, D8 (B1) | Bajarildi | `_cascade_mastery_to_descendants` o‘chirildi (`888a96f`); test `test_mastering_a_section_does_not_touch_descendants` |
| 4.8 Kahn FIFO, lev yo‘q | GR2 (B2) | Bajarildi | `neuro_model/graph.py:topological_order` (heap, `(pos, id)`, lev), `5e5cb09` |
| 4.8 Sikl qoldig‘i jim qo‘shiladi | GR2 (B2) | Bajarildi | `CycleError(remaining)`, `5e5cb09`; test `test_cycle_error_lists_unordered_topics` |
| 4.8 Tugunlar grafida, G_L'da emas | GR2 (B2) | Bajarildi | `neuro_model/graph.py:expand`, `5e5cb09` |
| 4.8 Faqat testlarda ishlatiladi | B2, B6 | Qisman | Snapshot daraxt/graf API, savol tanlash va ledger'da ishlatiladi (`79b907c`); trayektoriya — B6 |
| 4.9 To‘rtta alohida evristika | TR2, ES7 (B6) | Kutilmoqda (B6) | — |
| 4.9 Sabablar yo‘q | TR3 (B6) | Kutilmoqda (B6) | — |
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
| TM1 Mavzu bo‘yicha BKT parametrlari | B3 | Kutilmoqda (B3) | Standart qiymatlar `config/settings.py:277-280` |
| TM2 Sigmoid G/S | B3 | Kutilmoqda (B3) | Konstantalar `G_MAX`, `S_MAX`, `A_Q` tayyor |
| TM3 θ_s kurs bo‘yicha, b_q savol bo‘yicha | B3 | Kutilmoqda (B3) | — |
| TM4 Elo K(n) | B3 | Kutilmoqda (B3) | `ELO_ALPHA`, `ELO_BETA` tayyor |
| TM5 Prerekvizitli P(L0) | B3 | Kutilmoqda (B3) | `LAMBDA`, `C_OFFSET` tayyor |
| TM6 Algoritm 2.4 tartibi | B3 | Kutilmoqda (B3) | — |
| TM7 Log maydonlari | B1 | Qisman | Maydonlar, cheklovlar va yozish yo‘li tayyor (`888a96f`). `kb_version` B2 da, `readiness_score`/`was_ready` B4 da to‘ldiriladi, II bob qiymatlari B3 dan |
| TY1 Histerezis M (τ, δ) | B4 | Kutilmoqda (B4) | `TAU`, `DELTA` tayyor |
| TY2 R faqat G_L orqali, fallback'siz | B4 | Kutilmoqda (B4) | — |
| TY3 `missing_count` hisoblagichi | B4 | Kutilmoqda (B4) | — |
| TY4 r_s(w) + tushuntirish | B4, B7 | Kutilmoqda (B4, B7) | — |
| TY5 Boshlangan mavzu yopilmaydi | B4 | Kutilmoqda (B4) | — |
| TY6 KB versiyasi bo‘yicha qayta hisoblash | B4 | Kutilmoqda (B4) | — |
| TR1 5 ta holat | B4, B7 | Kutilmoqda (B4, B7) | — |
| TR2 A–D guruhlari | B6 | Kutilmoqda (B6) | — |
| TR3 Sabablar | B6 | Kutilmoqda (B6) | — |
| TR4 Need_s(g) | B6 | Kutilmoqda (B6) | — |
| TR5 Frontend'da ko‘rsatish | B7 | Kutilmoqda (B7) | — |
| EX1 Anonim pyKT eksporti | B8 | Kutilmoqda (B8) | — |
| EX2 Oflayn baholash | B8 | Kutilmoqda (B8) | — |
| EX3 Metrikalar | B8 | Kutilmoqda (B8) | — |
| EX4 Statistika | B8 | Kutilmoqda (B8) | — |
| EX5 Benchmark | B9 | Kutilmoqda (B9) | — |
| EX6 Rozilik va anonimlashtirish | B8 | Kutilmoqda (B8) | `is_simulated` belgisi qo‘shildi (`332d56f`) |
| SN1 Unit testlar | B2–B6, B10 | Qisman | B0: 17, B1: 32, B2: 300 ta tasodifiy + 57 ta yangi/qayta yozilgan test (`neuro_model/tests`, `test_tree.py`, `test_kb.py`, `test_dag.py`, `test_kb_concurrency.py`) |
| SN2 Hypothesis | B10 | Kutilmoqda (B10) | `hypothesis` `requirements-dev.txt` da |
| SN3 Locust | B10 | Kutilmoqda (B10) | `locust` `requirements-dev.txt` da |

### ES (eski muammolar)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| ES1 DFS tugunlar grafida | B2 | Bajarildi | G_L bo‘yicha BFS, `5e5cb09` |
| ES2 θ=0.70 + fallback | B4 | Kutilmoqda (B4) | — |
| ES3 MPTT | B2 | Bajarildi | tree-queries, `79b907c` |
| ES4 Chiziqli G/S | B3 | Kutilmoqda (B3) | — |
| ES5 θ talaba×mavzu | B3 | Kutilmoqda (B3) | — |
| ES6 η=0.3 | B3 | Kutilmoqda (B3) | — |
| ES7 Alohida tavsiya funksiyalari | B6 | Kutilmoqda (B6) | — |
| ES8 Simulyatsiya va baholash | D13 (B0, B1, B8) | Qisman | `is_simulated` va alohida `sim-` daraxti (`332d56f`); `source=simulated` (`888a96f`, test `test_simulator_labels_its_rows`); generator — B8 |

### 6-bo‘lim (eksperimentlarga tayyorlik)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| Logda `topic`, `attempt_no`, p̂ yo‘q | P1-1 (B1) | Bajarildi | `assessments/models.py` (`AssessmentAttempt`), migratsiyalar `0006`–`0008`, `888a96f`; test `test_legacy_rows_are_numbered_and_labelled` |
| Easy-skip yozuvlari belgilanmagan | D8, D10 (B1) | Bajarildi | Mavjud qatorlar `source=legacy` (eksperimentdan chiqariladi), yangi sun’iy yozuvlar yo‘q (`888a96f`) |
| Test sessiyasi yozuvlarida tarix yo‘q | D7 (B5) | Kutilmoqda (B5) | B1: `source=test_session`, `session` FK (`888a96f`) |
| Seed vaqt tamg‘alarini qayta yozadi | B1 | Bajarildi | `seed_thesis_demo.py`, `seed_data.py` vaqtni yaratishda beradi, `update()` yo‘q; ledger `update` ni bloklaydi (`888a96f`); test `test_seed_thesis_demo_writes_seed_rows_and_leaves_others_alone` |
| Tugun o‘chirilsa javoblar CASCADE bilan o‘chadi | D11 (B1) | Bajarildi | `960ba2c`; `test_archive.py` |
| Foydalanuvchi hard-delete javoblarni o‘chiradi | D11 (B8) | Kutilmoqda (B8) | — |
| `seed_data` so‘ramasdan hammasini o‘chiradi | P2-7 | Bajarildi | `curriculum/management/commands/seed_data.py:20-45`; testlar `test_seed_safety.py` |
| `simulate --clear` real akkauntlarni hard-delete qiladi | P2-7, P2-8 | Bajarildi | `assessments/management/commands/simulate_bkt_data.py:52-57` |
| Anonim eksport yo‘q | EX1 (B8) | Kutilmoqda (B8) | — |
| pyKT/pyBKT/DBE-KT22/ASSISTments yo‘q | EX2 (B8) | Kutilmoqda (B8) | — |
| AUC/RMSE/statistika yo‘q | EX3, EX4 (B8) | Kutilmoqda (B8) | — |
| Benchmark zaif | EX5 (B9) | Kutilmoqda (B9) | — |
| Simulyator generativ emas | B8 | Kutilmoqda (B8) | — |
| H1 tayyorligi | B1, B4, B8 | Kutilmoqda | B1 qismi bajarildi: `readiness_score`, `was_ready` maydonlari (`888a96f`); to‘ldirish — B4 |
| H2 tayyorligi | B3, B8 | Kutilmoqda | — |
| H3 tayyorligi | B3, B8 | Kutilmoqda | — |
| H4 tayyorligi | B2, B9 | Kutilmoqda | B2 qismi bajarildi: CTE (django-tree-queries) asosiy model, `79b907c`; benchmark — B9 |

### 7-bo‘lim (testlar va sifat)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| 7.1 `test_test_session.py:140` 100.0 ni tasdiqlaydi | B5 | Qisman | B1: baho `TestSessionResult` da, `mastery_percentage` o‘zgarmasligi tekshiriladi (`888a96f`); qayta o‘ynash bilan tenglik — B5 |
| 7.1 Parallellik testi `OperationalError` ni yutadi | B10 | Qisman | `test_bayesian.py::test_concurrent_answer_submissions` endi xatoni yutmaydi; yangi `test_parallel_*` testlari (`888a96f`); to‘liq to‘plam — B10 |
| 7.1 `accounts` testlari yo‘q | B10 | Qisman | `accounts/tests/test_permissions.py`, `test_security_settings.py` (`f620171`) |
| 7.1 Frontend testi trivial | B7 | Qisman | 9 ta yangi vitest testi (`apiError`, delete natijalari, tutor flag), `2fa1d99`, `7b549fd`; 7-bosqich testlari — B7 |
| 7.2 Coverage 68% | B10 | Kutilmoqda (B10) | — |
| 7.2 Lint 71 error | P2-6 (B7) | Kutilmoqda (B7) | Hozir 71 (o‘zgarmagan) |
| 7.2 tsc 18 xato | P2-6 (B7) | Qisman | 16 xato qoldi |
| 7.2 Bundle 2.36 MB | B7 | Qisman | Tutor lazy chunk'ga ajratildi: asosiy bundle 2.22 MB (`7b549fd`); marshrutlar bo‘yicha `React.lazy` — B7 |
| 7.3 `SECRET_KEY` git'da | P2-1 | Bajarildi | `config/settings.py:35-40`; eski kalit tarixda qoldi (buzilgan deb hisoblanadi) |
| 7.3 `DEBUG=True` | P2-1 | Bajarildi | `config/settings.py:33` |
| 7.3 `ALLOWED_HOSTS=["*"]` | P2-1 | Bajarildi | `config/settings.py:42-45` |
| 7.3 CORS hammaga + credentials | P2-1 | Bajarildi | `config/settings.py:49-51` |
| 7.3 `X_FRAME_OPTIONS="ALLOWALL"` | P2-1 | Bajarildi | `config/settings.py:54`, `config/media.py` |
| 7.3 Demo parollar git'da | P2-1 | Bajarildi | `README.md`, `accounts/demo.py`, `332d56f` |
| 7.3 `.env` dagi token | 3-qoida | Qisman | gitignored ekani tekshirildi; bekor qilish foydalanuvchida |
| 7.3 JWT `localStorage` da | D16 (B7) | Kutilmoqda (B7) | — |
| 7.3 AllowAny endpoint'lar | D15 | Bajarildi | `f620171`; test `test_anonymous_access_is_rejected` |
| 7.3 Talaba o‘qituvchi endpoint'larini o‘qiydi | D15 | Bajarildi | test `test_student_cannot_read_instructor_endpoints` |
| 7.3 Talaba yopiq mavzuga javob beradi | D9 (B4) | Kutilmoqda (B4) | — |
| 7.3 `arms_cache` git'da | B0 | Bajarildi | frontend `a751538` |
| 7.4 `TestsListView` N+1 | P2-4 (B5) | Kutilmoqda (B5) | — |
| 7.4 Sikl DFS N+1 | P2-4 (B2) | Bajarildi | Tekshiruv xotiradagi snapshot ustida, `5e5cb09`, `79b907c` |
| 7.4 Easy-skip N+1 | D8 (B1) | Bajarildi | Funksiya o‘chirildi (`888a96f`) |
| 7.4 `SubmitTestSession` N+1 | P2-4 (B5) | Kutilmoqda (B5) | — |
| 7.4 Keshlanmagan qayta hisoblashlar | GR1 (B2) | Bajarildi | Versiya kaliti bilan kesh, `79b907c` |
| 7.4 Bir javobga 12–20 SQL | B10 (byudjet ≤ 12) | Kutilmoqda (B10) | B1 dan keyin o‘lchandi: 25 (birinchi), 20 (keyingi), 15 (`review_repeat`); Q1-14 |

### 8.3 (ustuvorliklar ro‘yxati)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| P0-1 Test sessiyasi BKT'ni chetlab o‘tadi | B5, B7 | Qisman | B1: baho endi `mastery_percentage` ga yozilmaydi, `TestSessionResult` ga yoziladi (`888a96f`); model orqali o‘tish — B5, UI — B7 |
| P0-2 Cascade va easy-skip | B1 | Bajarildi | `888a96f`; `test_ledger.py` |
| P0-3 Talabaga xos tayyorlik | B4 | Kutilmoqda (B4) | — |
| P0-4 G_L, Y2, Y3, qulf | B2 | Bajarildi | `5e5cb09`, `79b907c` |
| P0-5 Talaba modeli | B3 | Kutilmoqda (B3) | — |
| P0-6 Yagona unlock servisi | B4 | Kutilmoqda (B4) | — |
| P1-1 Logni kengaytirish | B1 | Bajarildi | `888a96f`; `test_ledger.py`, `test_ledger_migration.py` |
| P1-2 pyKT eksporti, rozilik | B8 | Kutilmoqda (B8) | — |
| P1-3 Oflayn baholash | B8 | Kutilmoqda (B8) | — |
| P1-4 Metrikalar va statistika | B8 | Kutilmoqda (B8) | — |
| P1-5 Benchmark | B9 | Kutilmoqda (B9) | — |
| P1-6 tree-queries'ga ko‘chirish | B2 | Bajarildi | `79b907c` |
| P1-7 Kahn, Desc*, κ, kesh | B2 | Bajarildi | `5e5cb09`, `79b907c` |
| P1-8 Trayektoriya | B6, B7 | Kutilmoqda | — |
| P1-9 Hypothesis va Locust | B10 | Kutilmoqda (B10) | Paketlar `requirements-dev.txt` da |
| P2-1 Maxfiy qiymatlar va xavfsizlik sozlamalari | B0 | Bajarildi | `b44df84`, `332d56f` |
| P2-2 Requirements sinxronligi | B0 | Bajarildi | `1d6f286` |
| P2-3 `InvalidMove` → 400, Redis chidamliligi, prerekvizit API | B0 (Redis), B2 | Bajarildi | Redis (`b44df84`, `f620171`); Y1/400 va prerekvizit API (`79b907c`) |
| P2-4 N+1 | B2, B5 | Qisman | Sikl tekshiruvi N+1 yo‘q (`79b907c`); `TestsListView`, `SubmitTestSession` — B5 |
| P2-5 Rollarni bir xil qilish | B0 (backend), B7 (frontend) | Qisman | `accounts/permissions.py`, `f620171` |
| P2-6 Frontend lint/tsc, o‘lik kod | B7 | Qisman | `arms_cache` va CI (`a751538`); qolgani B7 |
| P2-7 Xavfli seed buyruqlari | B0 | Bajarildi | `332d56f` |
| P2-8 CASCADE va hard-delete | B0 (simulator), B1, B8 | Qisman | `simulate --clear` cheklandi (`332d56f`); PROTECT va arxivlash (`888a96f`, `960ba2c`); hard-delete siyosati — B8 |

### 8.4 (javob topilmagan savollar)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| Q1 Natijalar qaysi ma’lumotdan? | D13 | Bajarildi (qaror) | D13: simulyatsiya hech qachon natija uchun ishlatilmaydi |
| Q2 `db.sqlite3` da real ma’lumot bormi? | 2-qoida | Bajarildi (qaror) | Bor deb hisoblanadi; zaxira olindi, hisobotga faqat qatorlar soni chiqarildi |
| Q3 PostgreSQL | D1 | Bajarildi | `docker-compose.yml`, `b44df84` |
| Q4 Kurs modeli | D2 (B2) | Bajarildi | Kurs = ildiz (`kind=course`), `79b907c`; θ kurs bo‘yicha — B3 |
| Q5 α, β, λ va parametrlar manbasi | D6, `calibrate_bkt` (B3) | Qisman | Konstantalar `config/settings.py:266-285`; kalibrlash — B3 |
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
| A4-6 Mavzu holatlari va P(L) | B4 | Kutilmoqda (B4) | — |
| A4-7 Bo‘lim va kurslar uchun `mastered/total` (D22) | B4 | Kutilmoqda (B4) | — |
| A4-8 Yopiq mavzuning yetishmayotgan prerekvizitlari | B4 | Kutilmoqda (B4) | — |
| A4-9 `GET /api/learning/mistakes/` (D25) | B6 | Kutilmoqda (B6) | Ma’lumot manbai tayyor: ledger'dagi `selected_choice`, `is_correct`, `source` (`888a96f`) |
| A4-10 `GET /api/me/summary/` (D27) | B6 | Kutilmoqda (B6) | — |
| A4-11 `GET /api/config/model/` (D29) | B6 | Kutilmoqda (B6) | Konstantalar bir joyda: `config/settings.py` `THESIS_MODEL` (shu jumladan `REVIEW_REPEAT_HOURS`) |
| A4-12 `GET /api/learning/topics/<id>/history/` — p̂, P(G), P(S), p_before, p_after, natija, vaqt | B6 | Kutilmoqda (B6) | Ustunlar ledger'da bor (`888a96f`); II bob qiymatlari B3 dan |
| A4-13 `PATCH /api/me/consent/` | B8 | Kutilmoqda (B8) | — |

**1-bo‘lim: qarorlar**

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| D20 Til: o‘zbek (lotin) asosiy, `react-i18next`, `uz.json`/`en.json`, atamalar va bosh harf qoidasi | B7 | Kutilmoqda (B7) | — |
| D21 Holatlar palitrasi `src/lib/status.ts`, WCAG AA | B7 | Kutilmoqda (B7) | — |
| D22 Holat faqat `topic` turida, bo‘lim/kurs — `k / n` | B2 (`kind`), B4 (backend), B7 (UI) | Qisman | B2 qismi (`kind`) bajarildi, `79b907c`; holatlar — B4, UI — B7 |
| D23 Soxta ma’lumot yo‘q, har bir son API'dan | B6 (endpoint'lar), B7 (grep) | Kutilmoqda (B6, B7) | — |
| D24 `VITE_ENABLE_TUTOR=false`, menyuda yo‘q | B7 | Bajarildi | `src/lib/features.ts`, `src/App.tsx`, `src/components/layout/Header.tsx`, `7b549fd`; test `src/lib/features.test.ts` |
| D25 Xatolar backend'dan, “Qayta yechish”, `review_repeat` | B1 (ledger), B6 (endpoint), B7 (UI, `mistakeStorage` olib tashlash) | Qisman | B1 qismi bajarildi (A4-1); savol tanlash oynadagi savollarni oxiriga qo‘yadi (`question_selection.py`, test `test_next_question_prefers_questions_outside_the_window`) |
| D26 LLM tushuntirishlari hozir amalga oshirilmaydi, faqat `Question.explanation` | — | Kechiktirildi — D26 bo‘yicha 8–10-bosqichlardan keyingi alohida bosqich (dizayn 5-bo‘limda) | Hozir tushuntirish manbai faqat `Question.explanation` |
| D27 Profil haqiqiy ma’lumotda (`/api/me/summary/`) | B6, B7 | Kutilmoqda (B6, B7) | — |
| D28 Menyu rolga qarab | B7 | Kutilmoqda (B7) | Backend `role` maydoni tayyor (`accounts/permissions.py:get_role`, `f620171`) |
| D29 Noto‘g‘ri da’volar olib tashlanadi, konstantalar `GET /api/config/model/` dan | B6, B7 | Kutilmoqda (B6, B7) | — |

**2–3-bo‘limlar: sahifalar va qabul shartlari (7-bosqich)**

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| 2.1 Bosh sahifa: KPI'lar, “Keyingi qadam” (A–D), holatlar issiqlik xaritasi | B6, B7 | Kutilmoqda (B6, B7) | — |
| 2.2 O‘quv yo‘li: “Ikki qatlam” rejimi, `lev`/`pos` joylashuvi, yon panel, Need(g) yo‘li, legenda | B2, B4, B6, B7 | Kutilmoqda (B7) | — |
| 2.3 Mashq va testlar: ikki rejim, yopiq karta va 403, qiyinlik o‘rtacha b dan | B4, B7 | Kutilmoqda (B4, B7) | — |
| 2.4 Kurslar sahifasi O‘quv yo‘liga birlashadi | B7 | Kutilmoqda (B7) | — |
| 2.5 Mavzu sahifasi: “Qanday hisoblandi” paneli (τ, urinishlar jadvali, Rasch) | B6 (history), B7 | Kutilmoqda (B6, B7) | Ma’lumot ustunlari ledger'da (`888a96f`) |
| 2.6 Kurs konstruktori: outline + muharrir, prerekvizit muharriri, sikl/Y2/κ ko‘rsatish | B2, B7 | Kutilmoqda (B2, B7) | — |
| 2.7 Foydalanuvchilar: email prefiksi, rol filtri, simulyatsiya nishoni, faolsizlantirish, rozilik ustuni | B7, B8 | Kutilmoqda (B7, B8) | `is_simulated` maydoni bor (`332d56f`) |
| 2.8 Profil: real ma’lumot, rozilik, hisobni o‘chirish, parol | B6, B7, B8 | Kutilmoqda (B6, B7, B8) | — |
| 2.9 Quiz: test natijasi (P(L) oldin → keyin, ochilgan mavzular), mashq rejimi, klaviatura | B5, B7 | Kutilmoqda (B5, B7) | Test bahosi `TestSessionResult` da (`888a96f`) |
| 2.10 Xatolar ustida ishlash: `GET /api/learning/mistakes/`, guruhlash, “ko‘rib chiqilgan” belgisi | B6, B7 | Kutilmoqda (B6, B7) | Ledger o‘zgarmas (`888a96f`), shuning uchun “ko‘rib chiqilgan” belgisi B6 da alohida jadvalda saqlanadi |
| 2.11 Umumiy: loading/bo‘sh/xato holatlari, konsol, responsive, `React.lazy`, `data-testid`, `docs/ui/` skrinshotlari | B7 | Kutilmoqda (B7) | — |
| 3 Qabul: mock massivlar yo‘q; bir mavzu barcha sahifalarda bir xil holat va P(L) (vitest/Playwright); “2PL”, “PROOF”, “70%”, “dynamically match” matnlari yo‘q | B7 | Kutilmoqda (B7) | — |
| 5 LLM tushuntirishlari dizayni (o‘qituvchi tasdiqlaydi, kesh, eksperimentga ta’sir nazorati) | — | Kechiktirildi — D26: 8–10-bosqichlardan keyin, flag ortida | — |
