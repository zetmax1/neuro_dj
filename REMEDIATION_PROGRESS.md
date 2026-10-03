# NeuroLearn — tuzatish jarayoni (REMEDIATION_PROGRESS)

> **Foydalanuvchi ko‘rsatmasi (asl matn):** Backend ildizida ikkita fayl bor: NEUROLEARN_REMEDIATION.md (topshiriq) va NEUROLEARN_AUDIT.md (audit). Avval ikkalasini to‘liq o‘qi. Keyin topshiriqdagi "Ish qoidalari"ga amal qilib, 0-bosqichdan boshla. Har bir bosqich oxirida REMEDIATION_PROGRESS.md ni yangila, commit qil va menga qisqa hisobot ber. Keyingi bosqichga men "davom et" deganimdan keyin o‘t. Agar REMEDIATION_PROGRESS.md allaqachon mavjud bo‘lsa, ishni u yerda to‘xtagan joydan davom ettir.

Branch: `thesis-model` (backend `~/Desktop/neuro_dj`, frontend `~/Desktop/neuro/neuro`). Push qilinmagan.

## Bosqichlar holati

| Bosqich | Holat | Backend commit'lari | Frontend commit'lari |
|---|---|---|---|
| 0 — Xavfsizlik, infratuzilma, ma’lumotlarni himoyalash | **Bajarildi** | `1d6f286`, `b44df84`, `f620171`, `332d56f`, `4067215` | `a751538`, `6c5a0a7` |
| 1 — Ma’lumot ifloslanishini to‘xtatish, javoblar logi | Kutilmoqda | — | — |
| 2 — Bilimlar bazasi modeli | Kutilmoqda | — | — |
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

## Savollar va qarorlar

| # | Savol / ziddiyat | Qaror |
|---|---|---|
| Q0-1 | Ko‘rsatmada `NEUROLEARN_REMEDIATION.md` tilga olingan, lekin u repoda yo‘q edi | Chatdagi spetsifikatsiya o‘zgarishsiz `NEUROLEARN_REMEDIATION.md` ga saqlandi va commit qilindi (`4067215`) |
| Q0-2 | `~/.bashrc` `DATABASE_URL=…@HOST:PORT/…` shablonini eksport qiladi, natijada Django noto‘g‘ri bazaga ulanadi | Repodan tashqaridagi faylga tegilmadi. `config/.env` qiymatlari shell muhitidan ustun (`overwrite=True`, `config/settings.py:26`). Faylni o‘chirish uchun `DJANGO_ENV_FILE=""` (CI va deploy shunday ishlaydi) |
| Q0-3 | Lokal Redis 6379 portni band qilgan | Compose'dagi Redis host porti 6380. Postgres D1 bo‘yicha 5433 |
| Q0-4 | `docker compose` standart holatda ildizdagi `.env` ni o‘qiydi (3-qoida bo‘yicha unga tegish mumkin emas) | Compose faqat `--env-file config/.env` bilan ishga tushiriladi (README, `docker-compose.yml` sarlavhasi). Kuzatiladigan fayllarda parol yo‘q, qiymatlar `${VAR:?}` bilan majburiy |
| Q0-5 | `X_FRAME_OPTIONS="DENY"` frontend'dagi PDF iframe'ini (8080 → 8000) buzadi | Global qiymat `DENY`. Faqat media view (`config/media.py`) `xframe_options_exempt` + `Content-Security-Policy: frame-ancestors 'self' <FRONTEND_ORIGINS>`. Prod'da web-server shu siyosatni qo‘llashi kerak |
| Q0-6 | D15: `IsInstructor` = Instructor guruhi yoki `is_staff`. `Admin` guruhi va superuser qanday? | Ular ham instruktor deb hisoblanadi (oldin `Admin` guruhi yozish huquqiga ega edi). `get_role`: superuser yoki Admin → `admin` |
| Q0-7 | `Course.tsx` spetsifikatsiya bo‘yicha 7-bosqichda ko‘chiriladi, lekin 0-bosqichdagi ruxsat o‘zgarishi talabaning kurs sahifasini va shablonni yuklab olishni darhol buzadi | Ikkala frontend o‘zgarishi minimal hajmda 0-bosqichda qilindi (`6c5a0a7`), shunda ilova bosqichlar orasida ishlab turadi. 7-bosqichdagi qolgan ishlar o‘zgarmaydi |
| Q0-8 | `seed_data` uchun “demo foydalanuvchi” ta’rifi | staff/superuser, `is_simulated=True` yoki `accounts/demo.py` dagi `DEMO_EMAILS`. Boshqa har qanday akkaunt real deb hisoblanadi |
| Q0-9 | `--clear` endi mavzularni o‘chirmaydi, lekin simulyator mavjud slug'lar bilan to‘qnashardi | Simulyator `sim-` prefiksli alohida daraxtdan foydalanadi (`get_or_create`) va real kurikulumga tegmaydi. 8-bosqichda generativ qilib qayta yoziladi |
| Q0-10 | Testlar dev Redis'ga yozardi; `--nomigrations --reuse-db` data migratsiyalarini tekshirmaydi | `conftest.py`: har bir test uchun LocMem kesh. `pytest.ini`: migratsiyalar PostgreSQL'da har safar qo‘llanadi |
| Q0-11 | Test fixture'larida eski demo parol satri bor edi | Hech bir test parol bilan login qilmaydi, shuning uchun `password=None` (foydalanib bo‘lmaydigan parol) |
| Q0-12 | Django'ning tasodifiy kaliti `$`/`#` belgilarini o‘z ichiga olishi mumkin (compose va dotenv interpolatsiyasi) | `SECRET_KEY` `secrets.token_urlsafe(50)` bilan generatsiya qilinadi |
| Q0-13 | Dev PostgreSQL'ga `db.sqlite3` dan ko‘chirilgan ma’lumotlarda shaxsiy ma’lumot bo‘lishi mumkin | Ular faqat lokal docker volume'da (`neurolearn_pgdata`) turadi. Hisobotga faqat qatorlar soni chiqarildi |
| Q0-14 | `STUDENT_MODEL_ENGINE` va `MASTERY_THRESHOLD` eski konstantalari | Hozircha qoldirildi (`config/settings.py` “legacy” bo‘limi). 3- va 4-bosqichlarda olib tashlanadi |
| Q0-15 | drf-spectacular W001/W002 ogohlantirishlari | Xavfsizlikka aloqasi yo‘q. Tegishli view'lar 4–6-bosqichlarda qayta yozilganda serializer'lar qo‘shiladi. P2 sifatida kuzatiladi |
| Q0-16 | Frontend CI lint (71) va tsc (16) bo‘yicha qizil bo‘ladi | Bu kutilgan holat, 7-bosqichda 0 ga tushiriladi. CI masofada ishga tushirilmadi (push yo‘q), YAML sintaksisi tekshirildi |

---

## Bog‘liqlik matritsasi (audit topilmalari → vazifa)

Holatlar: **Bajarildi**; **Qisman**; **Kutilmoqda (Bn)** — rejadagi n-bosqichda bajariladi; **Kechiktirildi — sababi**.
Commit qisqartmalari: backend `1d6f286` (repo), `b44df84` (config), `f620171` (auth), `332d56f` (data), `4067215` (docs/CI); frontend `a751538`, `6c5a0a7`.

### 0-bo‘lim (asosiy 5 muammo)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| #1 Test oqimi BKT'ni chetlab o‘tadi, 0–100 shkala | P0-1 (B5, B7) | Kutilmoqda (B5, B7) | — |
| #2 KB modeli: MPTT, G_L yo‘q, Y2/Y3, qulf yo‘q | P0-4, P1-6, P1-7 (B2) | Kutilmoqda (B2) | — |
| #3 Talaba modeli II bobga zid | P0-5 (B3) | Kutilmoqda (B3) | — |
| #4 Unlock 4 xil, global `is_unlocked`, cascade | P0-3, P0-6 (B4), P0-2 (B1) | Kutilmoqda (B1, B4) | — |
| #5 Log yaroqsiz, sun’iy yozuvlar; maxfiy ma’lumotlar repoda | P0-2, P1-1 (B1); P2-1 (B0) | Qisman | Maxfiy qism bajarildi: `config/settings.py:33-60`, README; log qismi — B1 |

### 1-bo‘lim (umumiy tuzilma)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| 1.1 `.idea/` git'da kuzatiladi | B0 repo tozaligi | Bajarildi | `.gitignore`, `1d6f286` |
| 1.1 Bo‘sh `views.py` paketlar bilan to‘sib qo‘yilgan | B0 | Bajarildi | `1d6f286` |
| 1.2 `requirements.txt` to‘liq emas, `Pipfile` nomuvofiq | P2-2, D18 | Bajarildi | `requirements.txt`, `requirements-dev.txt`, `1d6f286`; toza venv tekshiruvi |
| 1.2 django-tree-queries o‘rnatilgan, lekin ishlatilmaydi | P1-6 (B2) | Kutilmoqda (B2) | `requirements.txt` ga qo‘shildi |
| 1.2 SQLite, PostgreSQL yo‘q | D1 | Bajarildi | `config/settings.py:153-156`, `docker-compose.yml`, `b44df84` |
| 1.2 Redis sozlangan, lekin hech narsa keshlanmaydi | GR1 (B2) | Kutilmoqda (B2) | — |
| 1.3 Redis bo‘lmasa yozuvdan keyin 500 | B0 | Bajarildi | `config/settings.py:170-185`, `curriculum/views/instructor.py:72-75`; test `test_topic_writes_survive_cache_backend[redis-down]` |
| 1.3 Env o‘zgaruvchilari yo‘q, `.env` ishlatilmaydi | P2-1 | Bajarildi | `config/settings.py:22-27`, `config/.env.example` |
| 1.3 Ildizdagi `.env` da token | 3-qoida, 8.4-Q6 | Qisman | `.gitignore:13` da borligi tekshirildi; tokenni bekor qilish foydalanuvchida |
| 1.3 `docker-compose` yo‘q | D1 | Bajarildi | `docker-compose.yml` |
| 1.3 `@supabase/supabase-js` `package.json` da yo‘q, client ishlatilmaydi | D17 (B7) | Kutilmoqda (B7) | — |
| 1.5 “updated” kabi commit xabarlari | B0 CI va hujjat | Bajarildi | Yangi commit'lar conventional formatda va ID'lar bilan |
| 1.5 Untracked `.agents/`, `graphify-out/` | 8.4-Q8 | Bajarildi | `.gitignore:23-24` |

### 2-bo‘lim (backend)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| 2.2 `TopicPrerequisite` da ω yo‘q | BB3 (B2) | Kutilmoqda (B2) | — |
| 2.2 `Choice` ≤4 cheklovi `bulk_create` da ishlamaydi | B2 (Y4, import servisi) | Kutilmoqda (B2) | — |
| 2.2 Daraxt MPTT'da | D3, P1-6 (B2) | Kutilmoqda (B2) | — |
| 2.2 `orchestrator.py:23` noto‘g‘ri izoh | B0 | Bajarildi | `assessments/services/orchestrator.py:21-24`, `1d6f286` |
| 2.4 Prerekvizit uchun API yo‘q | B2 API | Kutilmoqda (B2) | — |
| 2.4 Graf va shablon AllowAny | D15 | Bajarildi | `curriculum/views/graph.py:34`, `assessments/views/instructor.py:235`, `f620171` |
| 2.4 `learning_path/tree` dagi `mastery_percentage` aslida `score` | D5 (B4) | Kutilmoqda (B4) | — |
| 2.5 JWT blacklist ishlamaydi | D16 | Bajarildi | `config/settings.py:86`; test `test_rotated_refresh_token_is_blacklisted` |
| 2.5 Rollar nomuvofiq (`Instructor` va `is_staff`) | D15, P2-5 | Qisman | Backend: `accounts/permissions.py`, `f620171`; frontend `AdminRoute` — B7 |
| 2.6 Advisory lock yo‘q | BB9 (B2) | Kutilmoqda (B2) | — |
| 2.6 `SubmitTestSessionView` atomar emas | B5 | Kutilmoqda (B5) | — |
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
| 4.1 Sikl tugunlar grafida DFS bilan | BB7, ES1 (B2) | Kutilmoqda (B2) | — |
| 4.1 Sikl zanjiri qaytarilmaydi | BB7 (B2) | Kutilmoqda (B2) | — |
| 4.1 Y2 tekshirilmaydi | BB6 (B2) | Kutilmoqda (B2) | — |
| 4.1 TOCTOU poyga holati | BB9 (B2) | Kutilmoqda (B2) | — |
| 4.1 `bulk_create`/`update` chetlab o‘tadi | B2 (guard) | Kutilmoqda (B2) | — |
| 4.1 Har bir tugun uchun SQL (N+1) | B2 | Kutilmoqda (B2) | — |
| 4.2 `InvalidMove` → 500 | BB5, P2-3 (B2) | Kutilmoqda (B2) | — |
| 4.2 Tugun o‘chirilsa javoblar CASCADE bilan o‘chadi | D11, P2-8 (B1) | Kutilmoqda (B1) | — |
| 4.2 Daraxt o‘zgarganda Y2/Y3 tekshirilmaydi | BB8 (B2) | Kutilmoqda (B2) | — |
| 4.3 Unlock 4 xil implementatsiya | P0-6 (B4) | Kutilmoqda (B4) | — |
| 4.3 Global `Topic.is_unlocked` | D9 (B4) | Kutilmoqda (B4) | — |
| 4.3 Ochiq mavzu qayta yopiladi | TY5 (B4) | Kutilmoqda (B4) | — |
| 4.3 Yopiq mavzuga javob berish mumkin | D9 (B4) | Kutilmoqda (B4) | — |
| 4.3 Chegara 3 joyda har xil | TY1, D6 (B4) | Qisman | D6 konstantalari bir joyda (`config/settings.py:266-285`); eski chegaralar B4 da olib tashlanadi |
| 4.4 BKT parametrlari global | TM1 (B3) | Kutilmoqda (B3) | — |
| 4.4 `_retrieve_prior` `algorithm_used` ni filtrlamaydi | B1 | Kutilmoqda (B1) | — |
| 4.4 Test sessiyasi tarixga yozmaydi | D7 (B5) | Kutilmoqda (B5) | — |
| 4.4 Tarix attempt'ga FK'siz | B1 | Kutilmoqda (B1) | — |
| 4.5 Chiziqli G/S | TM2, ES4 (B3) | Kutilmoqda (B3) | — |
| 4.5 P(G) 0.5 gacha chiqadi | TM2 (B3) | Kutilmoqda (B3) | — |
| 4.6 θ talaba×mavzu uchun | TM3, ES5 (B3) | Kutilmoqda (B3) | — |
| 4.6 b yangilanmaydi | TM4 (B3) | Kutilmoqda (B3) | — |
| 4.6 K o‘zgarmas | TM4, ES6 (B3) | Kutilmoqda (B3) | — |
| 4.6 θ cheklanmagan | D6 `THETA_CLAMP` (B3) | Kutilmoqda (B3) | Konstanta `config/settings.py:276` |
| 4.6 Tanlash va yangilashda θ nomuvofiq | B3 savol tanlash | Kutilmoqda (B3) | — |
| 4.6 p̂ saqlanmaydi | TM6, TM7 (B1, B3) | Kutilmoqda (B1, B3) | — |
| 4.7 P(L0) o‘zgarmas 0.15 | TM5 (B3) | Kutilmoqda (B3) | — |
| 4.7 Avlodlarga P=1.0 cascade | P0-2, D8 (B1) | Kutilmoqda (B1) | — |
| 4.8 Kahn FIFO, lev yo‘q | GR2 (B2) | Kutilmoqda (B2) | — |
| 4.8 Sikl qoldig‘i jim qo‘shiladi | GR2 (B2) | Kutilmoqda (B2) | — |
| 4.8 Tugunlar grafida, G_L'da emas | GR2 (B2) | Kutilmoqda (B2) | — |
| 4.8 Faqat testlarda ishlatiladi | B2, B6 | Kutilmoqda (B2, B6) | — |
| 4.9 To‘rtta alohida evristika | TR2, ES7 (B6) | Kutilmoqda (B6) | — |
| 4.9 Sabablar yo‘q | TR3 (B6) | Kutilmoqda (B6) | — |
| 4.9 Tartib `position` bo‘yicha | D4 (B2, B6) | Kutilmoqda (B2, B6) | — |
| 4.9 Easy-skip sun’iy yozuvlar | P0-2, D8 (B1) | Kutilmoqda (B1) | — |

### 5-bo‘lim (II bob talablari)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| BB1 Kurs→bo‘lim→mavzu, `kind`, pos | B2 | Kutilmoqda (B2) | — |
| BB2 Qo‘shni ro‘yxat + CTE | D3, B2 | Kutilmoqda (B2) | — |
| BB3 ω vazni | B2 | Kutilmoqda (B2) | — |
| BB4 Meros G_L | B2 | Kutilmoqda (B2) | — |
| BB5 Y1 | B2 | Kutilmoqda (B2) | — |
| BB6 Y2 | B2 | Kutilmoqda (B2) | — |
| BB7 Y3 BFS + zanjir | B2 | Kutilmoqda (B2) | — |
| BB8 Daraxt o‘zgarganda tekshiruv | B2 | Kutilmoqda (B2) | — |
| BB9 Advisory lock | B2 | Kutilmoqda (B2) | PostgreSQL (D1) tayyor |
| BB10 Y4 | B2 | Kutilmoqda (B2) | — |
| GR1 Versiyaga bog‘langan kesh | B2 | Kutilmoqda (B2) | Redis/LocMem infratuzilmasi tayyor (`b44df84`) |
| GR2 Kahn + ustuvor navbat + lev + CycleError | B2 | Kutilmoqda (B2) | — |
| GR3 Desc*, ortiqcha qirralar, κ | B2 | Kutilmoqda (B2) | — |
| TM1 Mavzu bo‘yicha BKT parametrlari | B3 | Kutilmoqda (B3) | Standart qiymatlar `config/settings.py:277-280` |
| TM2 Sigmoid G/S | B3 | Kutilmoqda (B3) | Konstantalar `G_MAX`, `S_MAX`, `A_Q` tayyor |
| TM3 θ_s kurs bo‘yicha, b_q savol bo‘yicha | B3 | Kutilmoqda (B3) | — |
| TM4 Elo K(n) | B3 | Kutilmoqda (B3) | `ELO_ALPHA`, `ELO_BETA` tayyor |
| TM5 Prerekvizitli P(L0) | B3 | Kutilmoqda (B3) | `LAMBDA`, `C_OFFSET` tayyor |
| TM6 Algoritm 2.4 tartibi | B3 | Kutilmoqda (B3) | — |
| TM7 Log maydonlari | B1 | Kutilmoqda (B1) | — |
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
| SN1 Unit testlar | B2–B6, B10 | Qisman | 0-bosqich uchun 17 ta yangi test |
| SN2 Hypothesis | B10 | Kutilmoqda (B10) | `hypothesis` `requirements-dev.txt` da |
| SN3 Locust | B10 | Kutilmoqda (B10) | `locust` `requirements-dev.txt` da |

### ES (eski muammolar)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| ES1 DFS tugunlar grafida | B2 | Kutilmoqda (B2) | — |
| ES2 θ=0.70 + fallback | B4 | Kutilmoqda (B4) | — |
| ES3 MPTT | B2 | Kutilmoqda (B2) | — |
| ES4 Chiziqli G/S | B3 | Kutilmoqda (B3) | — |
| ES5 θ talaba×mavzu | B3 | Kutilmoqda (B3) | — |
| ES6 η=0.3 | B3 | Kutilmoqda (B3) | — |
| ES7 Alohida tavsiya funksiyalari | B6 | Kutilmoqda (B6) | — |
| ES8 Simulyatsiya va baholash | D13 (B0, B1, B8) | Qisman | `is_simulated` va alohida `sim-` daraxti (`332d56f`); `source=simulated` — B1; generator — B8 |

### 6-bo‘lim (eksperimentlarga tayyorlik)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| Logda `topic`, `attempt_no`, p̂ yo‘q | P1-1 (B1) | Kutilmoqda (B1) | — |
| Easy-skip yozuvlari belgilanmagan | D8, D10 (B1) | Kutilmoqda (B1) | — |
| Test sessiyasi yozuvlarida tarix yo‘q | D7 (B5) | Kutilmoqda (B5) | — |
| Seed vaqt tamg‘alarini qayta yozadi | B1 | Kutilmoqda (B1) | — |
| Tugun o‘chirilsa javoblar CASCADE bilan o‘chadi | D11 (B1) | Kutilmoqda (B1) | — |
| Foydalanuvchi hard-delete javoblarni o‘chiradi | D11 (B8) | Kutilmoqda (B8) | — |
| `seed_data` so‘ramasdan hammasini o‘chiradi | P2-7 | Bajarildi | `curriculum/management/commands/seed_data.py:20-45`; testlar `test_seed_safety.py` |
| `simulate --clear` real akkauntlarni hard-delete qiladi | P2-7, P2-8 | Bajarildi | `assessments/management/commands/simulate_bkt_data.py:52-57` |
| Anonim eksport yo‘q | EX1 (B8) | Kutilmoqda (B8) | — |
| pyKT/pyBKT/DBE-KT22/ASSISTments yo‘q | EX2 (B8) | Kutilmoqda (B8) | — |
| AUC/RMSE/statistika yo‘q | EX3, EX4 (B8) | Kutilmoqda (B8) | — |
| Benchmark zaif | EX5 (B9) | Kutilmoqda (B9) | — |
| Simulyator generativ emas | B8 | Kutilmoqda (B8) | — |
| H1 tayyorligi | B1, B4, B8 | Kutilmoqda | — |
| H2 tayyorligi | B3, B8 | Kutilmoqda | — |
| H3 tayyorligi | B3, B8 | Kutilmoqda | — |
| H4 tayyorligi | B2, B9 | Kutilmoqda | PostgreSQL tayyor (D1) |

### 7-bo‘lim (testlar va sifat)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| 7.1 `test_test_session.py:140` 100.0 ni tasdiqlaydi | B5 | Kutilmoqda (B5) | — |
| 7.1 Parallellik testi `OperationalError` ni yutadi | B10 | Kutilmoqda (B10) | Endi PostgreSQL'da ishlaydi |
| 7.1 `accounts` testlari yo‘q | B10 | Qisman | `accounts/tests/test_permissions.py`, `test_security_settings.py` (`f620171`) |
| 7.1 Frontend testi trivial | B7 | Kutilmoqda (B7) | — |
| 7.2 Coverage 68% | B10 | Kutilmoqda (B10) | — |
| 7.2 Lint 71 error | P2-6 (B7) | Kutilmoqda (B7) | Hozir 71 (o‘zgarmagan) |
| 7.2 tsc 18 xato | P2-6 (B7) | Qisman | 16 xato qoldi |
| 7.2 Bundle 2.36 MB | B7 | Kutilmoqda (B7) | — |
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
| 7.4 Sikl DFS N+1 | P2-4 (B2) | Kutilmoqda (B2) | — |
| 7.4 Easy-skip N+1 | D8 (B1) | Kutilmoqda (B1) | — |
| 7.4 `SubmitTestSession` N+1 | P2-4 (B5) | Kutilmoqda (B5) | — |
| 7.4 Keshlanmagan qayta hisoblashlar | GR1 (B2) | Kutilmoqda (B2) | — |
| 7.4 Bir javobga 12–20 SQL | B10 (byudjet ≤ 12) | Kutilmoqda (B10) | — |

### 8.3 (ustuvorliklar ro‘yxati)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| P0-1 Test sessiyasi BKT'ni chetlab o‘tadi | B5, B7 | Kutilmoqda | — |
| P0-2 Cascade va easy-skip | B1 | Kutilmoqda (B1) | — |
| P0-3 Talabaga xos tayyorlik | B4 | Kutilmoqda (B4) | — |
| P0-4 G_L, Y2, Y3, qulf | B2 | Kutilmoqda (B2) | — |
| P0-5 Talaba modeli | B3 | Kutilmoqda (B3) | — |
| P0-6 Yagona unlock servisi | B4 | Kutilmoqda (B4) | — |
| P1-1 Logni kengaytirish | B1 | Kutilmoqda (B1) | — |
| P1-2 pyKT eksporti, rozilik | B8 | Kutilmoqda (B8) | — |
| P1-3 Oflayn baholash | B8 | Kutilmoqda (B8) | — |
| P1-4 Metrikalar va statistika | B8 | Kutilmoqda (B8) | — |
| P1-5 Benchmark | B9 | Kutilmoqda (B9) | — |
| P1-6 tree-queries'ga ko‘chirish | B2 | Kutilmoqda (B2) | — |
| P1-7 Kahn, Desc*, κ, kesh | B2 | Kutilmoqda (B2) | — |
| P1-8 Trayektoriya | B6, B7 | Kutilmoqda | — |
| P1-9 Hypothesis va Locust | B10 | Kutilmoqda (B10) | Paketlar `requirements-dev.txt` da |
| P2-1 Maxfiy qiymatlar va xavfsizlik sozlamalari | B0 | Bajarildi | `b44df84`, `332d56f` |
| P2-2 Requirements sinxronligi | B0 | Bajarildi | `1d6f286` |
| P2-3 `InvalidMove` → 400, Redis chidamliligi, prerekvizit API | B0 (Redis), B2 | Qisman | Redis qismi bajarildi (`b44df84`, `f620171`); qolgani B2 |
| P2-4 N+1 | B2, B5 | Kutilmoqda | — |
| P2-5 Rollarni bir xil qilish | B0 (backend), B7 (frontend) | Qisman | `accounts/permissions.py`, `f620171` |
| P2-6 Frontend lint/tsc, o‘lik kod | B7 | Qisman | `arms_cache` va CI (`a751538`); qolgani B7 |
| P2-7 Xavfli seed buyruqlari | B0 | Bajarildi | `332d56f` |
| P2-8 CASCADE va hard-delete | B0 (simulator), B1, B8 | Qisman | `simulate --clear` cheklandi (`332d56f`); PROTECT — B1; hard-delete siyosati — B8 |

### 8.4 (javob topilmagan savollar)

| Topilma | Vazifa | Holat | Dalil |
|---|---|---|---|
| Q1 Natijalar qaysi ma’lumotdan? | D13 | Bajarildi (qaror) | D13: simulyatsiya hech qachon natija uchun ishlatilmaydi |
| Q2 `db.sqlite3` da real ma’lumot bormi? | 2-qoida | Bajarildi (qaror) | Bor deb hisoblanadi; zaxira olindi, hisobotga faqat qatorlar soni chiqarildi |
| Q3 PostgreSQL | D1 | Bajarildi | `docker-compose.yml`, `b44df84` |
| Q4 Kurs modeli | D2 (B2) | Kutilmoqda (B2) | — |
| Q5 α, β, λ va parametrlar manbasi | D6, `calibrate_bkt` (B3) | Qisman | Konstantalar `config/settings.py:266-285`; kalibrlash — B3 |
| Q6 `.env` dagi token | 3-qoida | Qisman | Fayl gitignored; bekor qilish foydalanuvchida |
| Q7 `token_blacklist` | D16 | Bajarildi | `config/settings.py:86`, test |
| Q8 `graphify-out/`, `.agents/` | B0 | Bajarildi | `.gitignore` (kuzatilmaydi) |
