# NeuroLearn: tuzatish va II bob modelini amalga oshirish spetsifikatsiyasi

Bu fayl Claude Code uchun ish topshirig‘i. U `NEUROLEARN_AUDIT.md` (audit hisoboti) bilan birga o‘qiladi.
Auditdagi har bir topilma — 0–8-bo‘limlar, BB1–SN3, ES1–ES8, P0-1…P2-8 va 8.4-savollar — shu yerdagi biror vazifaga bog‘langan.
Ish oxirida birorta topilma e’tibordan chetda qolmasligi kerak.

Repozitoriylar:
- backend — `~/Desktop/neuro_dj`;
- frontend — `~/Desktop/neuro/neuro`.

---

## 1. Ish qoidalari

1. **Branch.** Ikkala repozitoriyda ham `thesis-model` branch'ini och va ishni faqat shu branch'da qil. `push` qilma, tarixni qayta yozma (`rebase -i`, `reset --hard`, `push --force` taqiqlanadi).
2. **Zaxira nusxa.** Birinchi migratsiyadan oldin `db.sqlite3` ni `backups/db-YYYYMMDD-HHMM.sqlite3` ga nusxala. `backups/` ni `.gitignore` ga qo‘sh. `db.sqlite3` ni o‘chirma. Unda real talabalarning shaxsiy ma’lumotlari bo‘lishi mumkin deb hisobla: hisobot va loglarga undan hech qanday shaxsiy ma’lumot chiqarma.
3. **Backend `.env` fayli.** Unga tegma: ochma, o‘qima, ichidagini chop etma. Faqat u `.gitignore` da turganini tekshir. Undagi tokenni foydalanuvchining o‘zi bekor qiladi.
4. **Qaytarib bo‘lmaydigan amallardan oldin to‘xta va so‘ra.** Bunga quyidagilar kiradi:
   - ma’lumot saqlangan ustunni o‘chirish — u ko‘chirilgani tekshirilmagan bo‘lsa;
   - bazadagi har qanday ma’lumotni o‘chirish;
   - git remote'ni o‘zgartirish;
   - tizim paketlarini o‘rnatish;
   - ikkala repozitoriydan tashqaridagi fayllarni o‘zgartirish.
5. **Har bir bosqichning ish tartibi:**
   1. kodni yoz;
   2. testlarni ishga tushir:
      - backend: `pytest` (PostgreSQL'da), `manage.py check`, `makemigrations --check`;
      - frontend: `lint`, `tsc --noEmit`, `vitest`, `build`;
   3. `REMEDIATION_PROGRESS.md` ni yangila;
   4. commit qil — xabarda ID'lar bo‘lsin, masalan `feat(kb): G_L va meros (BB4, BB7)`;
   5. chatga qisqa hisobot yoz;
   6. foydalanuvchi “davom et” deguncha kut.

   Foydalanuvchi bir nechta bosqichni ketma-ket bajarishga ruxsat bersa, shunday qil.
6. **Spetsifikatsiya bilan ziddiyat.** Agar bu fayl kod bilan yoki o‘z-o‘zi bilan zid kelsa, II bobga eng yaqin variantni tanla. Qarorni `REMEDIATION_PROGRESS.md` dagi “Savollar va qarorlar” bo‘limiga yoz. 2-bo‘limdagi konstantalarni sabab yozmasdan o‘zgartirma.
7. **Matematik qism alohida bo‘lsin.** Formulalar va graf algoritmlari Django'ga bog‘liq bo‘lmagan sof Python paketida yoziladi: `neuro_model/` (backend ildizida). Django servislari va `experiments/` aynan shu paketni import qiladi. Shunday qilib eksperimentda baholanadigan model va prototipda ishlaydigan model bir xil kod bo‘ladi.
8. **Testlar.** Iloji bo‘lsa, avval test yoz. 4-bo‘limdagi etalon qiymatlar 1e-3 aniqlikda o‘tishi shart.
9. **Til.** Kod, izohlar va commit sarlavhalari inglizcha bo‘lsin. `REMEDIATION_PROGRESS.md` va yakuniy hisobot o‘zbekcha (lotin yozuvida), texnik atamalar inglizcha qolsin.
10. **Bog‘liqlik matritsasi.** `REMEDIATION_PROGRESS.md` da auditdagi har bir topilma uchun bitta qator bo‘lsin: `Topilma | Vazifa | Holat (Bajarildi / Qisman / Kechiktirildi — sababi) | Dalil (fayl:qator, commit)`.

---

## 2. Qabul qilingan qarorlar (auditning 8.4-savollariga javoblar va arxitektura)

| # | Qaror |
|---|---|
| D1 | Asosiy ma’lumotlar bazasi PostgreSQL. U dev, testlar, eksperimentlar va benchmark uchun ishlatiladi. `docker-compose.yml` ichida `postgres:16` (host porti 5433, mavjud 5432 bilan to‘qnashmasligi uchun) va `redis:7` bo‘ladi. Ulanish `DATABASE_URL` orqali. Advisory lock va parallellik testlari tufayli SQLite testlar uchun qo‘llab-quvvatlanmaydi. |
| D2 | Kurs — bu ildiz `Topic` (`kind=course`). θ_s har bir (talaba, kurs) juftligi uchun saqlanadi. Prerekvizitlar kurslararo ham bo‘lishi mumkin. |
| D3 | Daraxt django-tree-queries (`TreeNode`) bilan saqlanadi, `parent_id` saqlanib qoladi. MPTT maydonlari `Topic` dan olib tashlanadi. django-mptt faqat `benchmarks` app'ida qoladi. |
| D4 | Global dastur tartibi `pos` — daraxtning preorder indeksi. Aka-uka tugunlar `(position, id)` bo‘yicha saralanadi. U har bir KB versiyasida qayta hisoblanadi va keshlanadi. `position` turli shoxlar orasida taqqoslanmaydi. |
| D5 | Barcha API'da yagona shkala ishlatiladi: `p_mastery ∈ [0, 1]`. Javoblar aniqligi alohida `accuracy` maydonida beriladi. UI foizga o‘zi aylantiradi. `mastery_percentage` frontend ko‘chirilgandan keyin olib tashlanadi. |
| D6 | Konstantalar bitta joyda — `settings.THESIS_MODEL` ichida, env orqali o‘zgartirsa bo‘ladi: `TAU=0.95`, `DELTA=0.10`, `G_MAX=0.30`, `S_MAX=0.10`, `A_Q=1.0`, `ELO_ALPHA=0.8`, `ELO_BETA=0.05`, `LAMBDA=0.5`, `C_OFFSET=0.05` (c = τ − 0.05), `THETA_CLAMP=4.0`. Mavzu parametrlarining standart qiymatlari: `P0=0.15`, `PT=0.20`, `G0=0.20`, `S0=0.05`. Mavzuga xos parametrlar `TopicModelParams` da saqlanadi va `calibrate_bkt` buyrug‘i bilan ma’lumotdan baholanadi. θ ni ±4 ga cheklash — raqamli xavfsizlik chorasi. Bu II bobda yo‘q, shuning uchun `THESIS_MAPPING.md` da qayd etiladi. |
| D7 | Test sessiyasidagi har bir javob Algoritm 2.4 orqali ketma-ket qayta ishlanadi (`source=test_session`). Imtihon bahosi (vaznli ball, o‘tdi/o‘tmadi) alohida `TestSessionResult` modelida saqlanadi. Bu baho `p_mastery` ga yozilmaydi va tayyorlikka ta’sir qilmaydi. |
| D8 | Easy-skip va avlodlarga cascade butunlay olib tashlanadi. Prototip kodi real javobdan boshqa hech qanday `AssessmentAttempt` yaratmaydi. Oson savollarni o‘tkazib yuborish kerak bo‘lsa, bu faqat savol tanlash siyosatida bajariladi. |
| D9 | Tayyorlik faqat bitta servis orqali aniqlanadi. `Topic.is_unlocked` va to‘rtta eski implementatsiya olib tashlanadi. Yopiq mavzuga so‘rov kelsa, 403 qaytadi va javobda yetishmayotgan prerekvizitlar ko‘rsatiladi. |
| D10 | `AssessmentAttempt` yagona ledger bo‘ladi (maydonlari 3-bosqichda). Mavjud qatorlar `source=legacy` deb belgilanadi va eksperimentlardan chiqarib tashlanadi. |
| D11 | O‘chirish siyosati: `AssessmentAttempt.question` va `topic` — `PROTECT`. Javoblari bor mavzu o‘chirilmaydi, `is_archived=True` qilinadi. Foydalanuvchi 30 kundan keyin hard-delete qilinganda: `research_consent=True` bo‘lsa, javoblari psevdonim bilan saqlanib qoladi; aks holda o‘chiriladi. |
| D12 | Foydalanuvchida `research_consent`, `research_consent_at` va `pseudonym` (tasodifiy, qaytarib bo‘lmaydigan) maydonlari bo‘ladi. Eksportda faqat psevdonim chiqadi: ism, email va IP chiqmaydi. |
| D13 | Simulyatsiya ma’lumotlari faqat testlar va pipeline'ni tekshirish uchun ishlatiladi, dissertatsiya natijalari uchun hech qachon ishlatilmaydi (ES8 javobi). Simulyatsiya qilingan foydalanuvchilarda `is_simulated=True`, javoblarida esa `source=simulated` bo‘ladi. |
| D14 | Eksperimentlar backend ildizidagi `experiments/` papkasida joylashadi. Ularning bog‘liqliklari alohida `experiments/requirements.txt` da. Ular eksport fayllarini o‘qiydi va `neuro_model` ni import qiladi. |
| D15 | Rollar bitta qoidaga keltiriladi: `IsInstructor` = `Instructor` guruhi yoki `is_staff`. Talaba o‘qituvchi endpoint'larini o‘qiy olmaydi, uning uchun alohida faqat o‘qish endpoint'lari bo‘ladi. |
| D16 | JWT: refresh token httpOnly + Secure + SameSite cookie'da, access token xotirada saqlanadi. `token_blacklist` app'i yoqiladi. |
| D17 | AI tutor dissertatsiya doirasidan tashqarida. U `VITE_ENABLE_TUTOR` flag'i ortida qoladi. Ishlatilmaydigan supabase client olib tashlanadi. Tutor saqlansa, uning bog‘liqligi `package.json` ga to‘g‘ri qo‘shiladi. |
| D18 | Backend bog‘liqliklari ikki faylda: `requirements.txt` (ishchi muhit, versiyalari qotirilgan) va `requirements-dev.txt` (testlar va vositalar). `Pipfile` va `Pipfile.lock` olib tashlanadi. |
| D19 | Frontend'da yangi yoki o‘zgartirilgan data hook'lari `@tanstack/react-query` ga o‘tadi. Oxirida provider hech qayerda ishlatilmasa, u olib tashlanadi. |

---

## 3. Model spetsifikatsiyasi (dissertatsiyaning II bobidan)

### 3.1 Bilimlar bazasi
- **Tugun turlari.** `kind ∈ {course, section, topic}`:
  - course — ildiz, otasi yo‘q;
  - topic — barg, farzandi bo‘lmaydi, savollar faqat shunga bog‘lanadi (Y4);
  - section — ichma-ich joylashishi mumkin.
- **Belgilashlar.** Anc(n) — n ning barcha ajdodlari. Leaves(n) — n ning ichidagi barcha mavzular (n ning o‘zi mavzu bo‘lsa, Leaves(n) = {n}).
- **Prerekvizitlar.** `E_P`: (x, y) — “y ni o‘rganishdan oldin x o‘zlashtirilishi kerak” degani. x va y istalgan tugun bo‘lishi mumkin. Har bir munosabatda vazn ω ∈ (0, 1], standart qiymati 1.
- **Meros grafi.** G_L = (L, E_L): (a, b) ∈ E_L, agar shunday (x, y) ∈ E_P mavjud bo‘lsaki, a ∈ Leaves(x) va b ∈ Leaves(y). Meros orqali hosil bo‘lgan qirraning vazni — uni hosil qilgan munosabatlar vaznlarining eng kattasi.
- **Y1.** Tugun ko‘chirilganda yangi ota tugun uning o‘zi ham, avlodi ham bo‘lmasligi kerak.
- **Y2.** x ≠ y, x ∉ Anc(y), y ∉ Anc(x).
- **Y3.** G_L'da sikl bo‘lmaydi.
- **Y4.** Har bir savol aynan bitta `topic` turidagi tugunga tegishli.
- **Algoritm 2.1 (yangi prerekvizit).**
  1. Y2 ni tekshir.
  2. X = Leaves(x). Leaves(y) dan BFS boshla.
  3. a mavzuning qo‘shnilari: har bir z ∈ {a} ∪ Anc(a) va har bir (z, t) ∈ E_P uchun Leaves(t) dagi mavzular.
  4. BFS biror a ∈ X ga yetsa, prerekvizitni rad et. `oldingi(b)` yozuvlari bo‘yicha zanjirni tiklab qaytar, masalan `["t3", "t6", "t8"]` va yangi qirra `t8 → t3`.
  5. Murakkabligi O(n·d + m).
- **Daraxt o‘zgarishi** (mavzu qo‘shish, ko‘chirish, arxivlash):
  1. tranzaksiya ichida qo‘lla;
  2. ta’sirlangan munosabatlar bo‘yicha Y2 ni tekshir;
  3. G_L ni qayta qur va Algoritm 2.2 bilan tekshir;
  4. biror shart buzilsa — rollback va 400.
- **Qulf va versiya.** E_P yoki daraxtni o‘zgartiruvchi barcha tranzaksiyalar boshida `pg_advisory_xact_lock(<doimiy kalit>)` chaqiriladi. Xuddi shu tranzaksiyada `KnowledgeBaseVersion.version` bittaga oshiriladi.

### 3.2 Graf hisob-kitoblari
- **Algoritm 2.2.**
  - Kahn algoritmi `heapq` asosidagi ustuvor navbat bilan, kalit `(pos, id)`.
  - Har bir chiqarilgan v uchun barcha w ∈ Succ(v) da `lev(w) = max(lev(w), lev(v)+1)`.
  - Tartibdagi mavzular soni n dan kam chiqsa, `CycleError` qaytariladi va unda tartibga tushmagan mavzular ko‘rsatiladi. Ularni jim oxiriga qo‘shib qo‘yish taqiqlanadi.
  - Murakkabligi O(m + n log n).
- **Desc\*.** Teskari topologik tartibda hisoblanadi: `Desc*(v) = ⋃_{w∈Succ(v)} ({w} ∪ Desc*(w))`. To‘plamlar Python `int` bitset sifatida saqlanadi.
- **Ortiqcha qirra.** (a, b) ortiqcha, agar a ning boshqa biror bevosita vorisi w uchun b ∈ Desc\*(w) bo‘lsa. Bunday qirra avtomatik o‘chirilmaydi, faqat o‘qituvchiga ogohlantirish chiqadi.
- **κ (tartib ziddiyatlari).** κ = |{(a, b) ∈ E_L : pos(b) < pos(a)}|. O‘qituvchiga ogohlantirish sifatida ko‘rsatiladi.
- **Kesh.** G_L, tartib, lev, Pre, Succ, Desc\*, pos, ortiqcha qirralar va κ KB versiyasiga bog‘langan kalit bilan keshlanadi. Redis ishlamay qolsa, LocMem kesh ishlatiladi va `DJANGO_REDIS_IGNORE_EXCEPTIONS=True` bo‘ladi.

### 3.3 Talaba modeli
- **Bazaviy qiymatlardan koeffitsiyentlar.** Mavzu parametrlari P0, PT, G0, S0 (shartlar: G0 < G_MAX, S0 < S_MAX). Ulardan:
  - γ_G = ln(G0 / (G_MAX − G0));
  - γ_S = ln(S0 / (S_MAX − S0)).
- **Guess va slip.**
  - P(G) = G_MAX · σ(γ_G + a_q(θ_s − b_q));
  - P(S) = S_MAX · σ(γ_S − a_q(θ_s − b_q)).
  - a_q = `A_Q` (standart 1). a_q = 0 bo‘lsa, model klassik BKT ga aylanadi.
- **Bashorat va Bayes yangilanishi.**
  - p̂ = P(L)(1 − P(S)) + (1 − P(L))P(G);
  - to‘g‘ri javobda: P(L|1) = P(L)(1 − P(S)) / p̂;
  - noto‘g‘ri javobda: P(L|0) = P(L)·P(S) / (1 − p̂);
  - so‘ngra o‘rganish o‘tishi: P(L)′ = P(L|x) + (1 − P(L|x))·PT.
- **Elo.**
  - p = σ(θ_s − b_q);
  - θ_s += K(n_s)(x − p);
  - b_q −= K(n_q)(x − p);
  - K(n) = ELO_ALPHA / (1 + ELO_BETA·n). Bu yerda n_s va n_q — talaba (kurs bo‘yicha) va savol uchun shu paytgacha berilgan javoblar soni.
- **Boshlang‘ich ehtimollik P(L0).**
  - m̄_s(w) — Pre(w) bo‘yicha ω vaznli o‘rtacha P(L_{s,u}). Talaba prerekvizitga hali javob bermagan bo‘lsa, u uchun shu prerekvizitning P0 qiymati olinadi.
  - P(L0)_{s,w} = min{(1 − λ)·P0(w) + λ·m̄_s(w), τ − C_OFFSET}.
  - Pre(w) bo‘sh bo‘lsa, P(L0)_{s,w} = P0(w). λ = 0 bo‘lsa, klassik BKT hosil bo‘ladi.
- **Algoritm 2.4 (javobni qayta ishlash tartibi qat’iy).**
  1. Talabaning shu mavzudagi birinchi urinishi bo‘lsa, P(L) ← P(L0)_{s,w}.
  2. P(G) va P(S) **eski** θ va b qiymatlaridan hisoblanadi.
  3. p̂ hisoblanadi va saqlanadi.
  4. Bayes yangilanishi.
  5. PT o‘tishi.
  6. Elo bo‘yicha θ va b yangilanadi.
  7. Algoritm 2.3 (tayyorlik) bajariladi.

  Hammasi bitta `transaction.atomic` ichida, `select_for_update` bilan qulflangan holat va qobiliyat qatorlarida bajariladi.
- **Ablatsiya bayroqlari.** `use_irt` va `use_prereq_init` bayroqlari quyidagi variantlarni beradi: BKT (ikkalasi ham false), BKT+IRT (`use_irt=true`, λ=0) va BKT+IRT+Pre (ikkalasi ham true). Prototip ham, eksperimentlar ham shu bitta kodni ishlatadi.

### 3.4 Tayyorlik va holatlar
- **O‘zlashtirish belgisi M.** P ≥ τ bo‘lsa M = 1; P < τ − δ bo‘lsa M = 0; ikkisining orasida M avvalgi qiymatini saqlaydi.
- **Tayyorlik R.** R_s(w) = 1 faqat barcha u ∈ Pre(w) uchun M_s(u) = 1 bo‘lganda. Pre(w) bo‘sh bo‘lsa, R = 1. Ota tugunga fallback yo‘q — meros faqat G_L orqali ishlaydi.
- **Tayyorlik bahosi.** r_s(w) = min_{u∈Pre(w)} P(L_{s,u}). Pre(w) bo‘sh bo‘lsa, r = 1.
- **Hisoblagich.** `missing_count_s(w)` — w ning M = 0 bo‘lgan bevosita prerekvizitlari soni. Yangi talaba uchun u |Pre(w)| ga teng.
- **Algoritm 2.3.**
  1. Javobdan keyin M_s(v) qayta hisoblanadi.
  2. M_s(v) o‘zgarmasa, ish shu yerda tugaydi.
  3. O‘zgarsa, har bir w ∈ Succ(v) uchun hisoblagich ∓1 qilinadi.
  4. Hisoblagich 0 ga tushsa va w yopiq bo‘lsa, w ochiladi.
  5. M_s(v) 1 dan 0 ga tushsa, v `review` holatiga o‘tadi.
- **Holatlar:** `closed`, `open`, `in_progress`, `mastered`, `review`. O‘tishlar:
  - closed → open, hisoblagich 0 ga tushganda;
  - open → in_progress, birinchi javobda;
  - in_progress → mastered, M = 1 bo‘lganda;
  - mastered → review, M 0 ga tushganda;
  - review → mastered, M yana 1 bo‘lganda;
  - open → closed — faqat o‘qituvchi yangi prerekvizit qo‘shganda va mavzu hali boshlanmagan bo‘lsa.
- **TY5.** Boshlangan mavzu (`in_progress`, `mastered`, `review`) hech qachon `closed` ga qaytmaydi.
- **TY6.** Talaba holatida `kb_version` saqlanadi. Har bir so‘rovda u joriy KB versiyasi bilan solishtiriladi. Mos kelmasa, hisoblagichlar M belgilaridan O(n + m) da qayta hisoblanadi.

### 3.5 Trayektoriya
- **Algoritm 2.5.** Ro‘yxat to‘rt guruhdan iborat:
  - A — `review` holatidagi mavzular. Tartib: ta’sir(v) kamayishi, so‘ng P o‘sishi. ta’sir(v) = |{w ∈ Desc\*(v) : M_s(w) = 0}|.
  - B — `in_progress` mavzular, topologik tartibda.
  - C — `open` mavzular, topologik tartibda.
  - D — `closed` mavzular, topologik tartibda. Har biriga M = 0 bo‘lgan bevosita prerekvizitlar biriktiriladi.
- **Sabab.** Har bir element tuzilmali sabab bilan qaytariladi: `{code, params}`, masalan `{"code": "review_impact", "params": {"impact": 4, "p": 0.80}}`. Matn frontend'da bitta lug‘at faylidan olinadi.
- **Maqsadli yo‘l Need_s(g).** Yopiq g uchun: Pre(g) dagi M = 0 bo‘lgan har bir u olinadi. Agar u ham yopiq bo‘lsa, uning prerekvizitlari uchun xuddi shu qidiruv rekursiv davom etadi. O‘zlashtirilgan yoki allaqachon ochilgan mavzuda qidiruv to‘xtaydi. Yo‘l — Need_s(g) topologik tartibda, oxirida g. Agar g ochiq bo‘lsa, yo‘l faqat [g] dan iborat.

---

## 4. Etalon misol va kutilgan qiymatlar (testlar uchun majburiy)

**Kurs “Ma’lumotlar tuzilmalari”** (`kind=course`):
- B1: t1 Massivlar, t2 Funksiyalar, t3 Ko‘rsatkichlar
- B2: t4 Rekursiya, t5 Ikkilik qidiruv
- B3: t6 Ikkilik qidiruv daraxti, t7 AVL daraxti, t8 Daraxtni aylanib chiqish

Bo‘limlar ham, ular ichidagi mavzular ham shu tartibda (`position`) joylashgan.

**E_P:** t1→t3, t1→t5, t2→t4, t3→t6, t5→t6, t6→t7, t6→t8, t4→B3.

**Graf bo‘yicha kutilgan natijalar:**

| Tekshiruv | Kutilgan natija |
|---|---|
| E_L | 10 ta qirra. t4→B3 dan t4→t6, t4→t7, t4→t8 qirralari hosil bo‘ladi |
| Topologik tartib | t1, t2, t3, t4, t5, t6, t7, t8. lev = 0, 0, 1, 1, 1, 2, 3, 3 |
| FIFO navbat bilan (taqqoslash testi) | t1, t2, t3, t5, t4, t6, t7, t8 |
| \|Desc\*\| | t1=5, t2=4, t3=3, t4=3, t5=3, t6=2, t7=0, t8=0 |
| Ortiqcha qirralar | t4→t7, t4→t8 |
| κ | 0 |
| (t8, t3) qo‘shish | Y3 bo‘yicha rad etiladi, zanjir t3 → t6 → t8 |
| (B3, t6) qo‘shish | Y2 bo‘yicha rad etiladi |
| t4 ni B3 ga ko‘chirish | Y2 bo‘yicha rad etiladi (t4 → B3 o‘ziga ishora qilib qoladi) |
| Audit probe'lari | (1) `B requires A` va `a1 requires b1` → sikl, rad etiladi. (2) Ajdod → avlod prerekviziti rad etiladi. (3) `B requires A`, A o‘zlashtirilmagan → b1 yopiq |

**BKT ketma-ketligi.** P0=0.3, G=0.2, S=0.1, T=0.1 va ketma-ket to‘g‘ri javoblar:

| Javoblar soni | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| P(L) | 0.6927 | 0.9192 | 0.9828 | 0.9965 |

**Guess va slip moslashuvi.** θ=0.5, P(L)=0.6, PT=0.1, G0=0.2, S0=0.05, G_MAX=0.3, S_MAX=0.1, a=1:

| Holat | P(G) | P(S) | p̂ | To‘g‘ri javobdan keyin P(L) | Noto‘g‘ri javobdan keyin P(L) |
|---|---|---|---|---|---|
| Qiyin savol, b=1.5 | 0.1272 | 0.0731 | 0.6070 | 0.9246 | 0.2005 |
| Oson savol, b=−0.5 | 0.2534 | 0.0269 | 0.6852 | 0.8669 | 0.1461 |
| a=0 (klassik BKT) | 0.20 | 0.05 | 0.65 | 0.8892 | 0.1771 |

**Elo.** θ=0.5, b=1.5, K=0.4, javob to‘g‘ri. Natija: p=0.2689, θ=0.7924, b=1.2076.

**Prerekvizitlardan P(L0).** P0=0.3, λ=0.5, vaznlar bir xil:
- prerekvizitlar 0.98, 0.96, 0.976 → m̄=0.972, P(L0)=0.636;
- prerekvizitlar 0.4, 0.5, 0.3 → P(L0)=0.35.

**Tayyorlik.** τ=0.95, δ=0.10. Boshlang‘ich holat: t1=0.97, t2=0.96, t3=0.98, t5=0.96 (M=1); t4=0.62 (`in_progress`).
- t4 ga G=0.2, S=0.1, T=0.1 bilan ikkita to‘g‘ri javob beriladi: P(L) 0.8921 ga, keyin 0.9764 ga ko‘tariladi.
- Birinchi javobdan keyin hisoblagichlar o‘zgarmaydi.
- Ikkinchi javobdan keyin t6 ochiladi. t7 va t8 hisoblagichlari 2 dan 1 ga tushadi.

**Trayektoriya.**
- Shu talaba uchun Need(t7) = {t4, t6}, yo‘l t4 → t6 → t7.
- Takrorlash ustuvorligi testi: t1=0.80 va t3=0.70 `review` holatida, t5 o‘zlashtirilgan, t6–t8 o‘zlashtirilmagan. Kutilgan tartib: t1 (ta’sir 4), keyin t3 (ta’sir 3).

**2.5-tasdiq (xossa testi).** Agar P(G) + P(S) < 1 bo‘lsa, P(L|1) > P(L) va P(L|0) < P(L). Bu o‘tishdan **oldingi** posterior uchun tekshiriladi.

Eslatma: PT o‘tishidan keyin noto‘g‘ri javoblarda ham P(L) o‘sishi mumkin. Bu klassik BKT xatti-harakati, test aynan shuni hujjatlashtirsin.

---

## 5. Bosqichlar

### Bosqich 0 — Xavfsizlik, infratuzilma va ma’lumotlarni himoyalash
Qamrab oladi: P2-1, P2-2, P2-7, P2-8 (qisman); audit 1.2, 1.3, 1.5, 2.5 (blacklist), 7.3; 8.4-savollar (3, 6, 7, 8).

**Branch va repo tozaligi**
- `thesis-model` branch'ini och, `db.sqlite3` zaxira nusxasini ol.
- `.gitignore` ga qo‘sh: `.idea/`, `.agents/`, `graphify-out/`, `backups/`; frontend'da `arms_cache/`. `.idea/` va `arms_cache/` ni `git rm --cached` bilan kuzatuvdan chiqar.
- Bo‘sh `curriculum/views.py` va `assessments/views.py` fayllarini o‘chir. `orchestrator.py:23` dagi noto‘g‘ri izohni tuzat.

**Bog‘liqliklar (D18)**
- Barcha import qilinadigan paketlarni qo‘sh: simplejwt, drf-spectacular, django-redis, celery, openpyxl, python-docx, django-unfold, django-tree-queries, psycopg.
- Test paketlarini (pytest-django, Faker, hypothesis, coverage, locust) `requirements-dev.txt` ga qo‘sh.
- `Pipfile` va `Pipfile.lock` ni olib tashla.
- Tekshiruv: scratchpad'dagi toza venv'ga `pip install -r requirements.txt -r requirements-dev.txt` va `pytest` ishlasin.

**Sozlamalar**
- Barcha sozlamalar env'dan o‘qilsin. Fayl sifatida `config/.env` ishlatiladi (gitignored), namunasi `config/.env.example` git'ga qo‘shiladi. Ildizdagi `.env` ga tegilmaydi.
- `SECRET_KEY` env'dan olinsin, `DEBUG=False` bo‘lganda u majburiy. Eski kalit git tarixida qolgani uchun u buzilgan hisoblanadi: yangisini ishlat.
- `DEBUG` standart qiymati `False`. `ALLOWED_HOSTS` va `CORS_ALLOWED_ORIGINS` env'dan olinsin. `CORS_ALLOW_ALL_ORIGINS` ni olib tashla.
- `X_FRAME_OPTIONS="DENY"`. `DEBUG=False` bo‘lganda secure cookie bayroqlari yoqilsin.
- `rest_framework_simplejwt.token_blacklist` ni `INSTALLED_APPS` ga qo‘sh va migratsiyani bajar.
- `DJANGO_REDIS_IGNORE_EXCEPTIONS=True`. Redis ishlamay qolsa, LocMem kesh ishlatilsin (`views/instructor.py:91` dagi 500 xatosi yo‘qolishi kerak).
- `THESIS_MODEL` sozlamalari D6 bo‘yicha.

**PostgreSQL (D1)**
- `docker-compose.yml` va `DATABASE_URL` ni qo‘sh.
- Ma’lumotlarni ko‘chirish skripti: `scripts/sqlite_to_postgres.sh` (`dumpdata`/`loaddata`; contenttypes va permissions bundan mustasno). Ko‘chirgandan keyin har bir jadvaldagi qatorlar sonini solishtir. SQLite fayli o‘zgarmay qoladi.

**Ruxsatlar (D15, P2-5 backend qismi)**
- `PrerequisiteGraphView` → `IsAuthenticated`. `DownloadQuestionTemplateView` → `IsInstructor`.
- O‘qituvchi uchun topics va resources endpoint'lari → `IsInstructor`; talabaga “ReadOnly” ruxsati olib tashlanadi.
- Talaba uchun alohida faqat o‘qish endpoint'lari: `/api/curriculum/topics/<id>/` va uning resurslari. `Course.tsx` 7-bosqichda shularga o‘tadi.
- Savollar banki va importi `is_staff` o‘rniga `IsInstructor` dan foydalanadi.
- `role` maydoni guruh va `is_staff` dan bir xil qoida bilan hisoblanadi.

**Ma’lumotlarni himoyalash**
- `seed_data` faqat `--yes-delete-all` bayrog‘i bilan ishlasin. Bazada demo bo‘lmagan foydalanuvchilar bo‘lsa, u ishlashni rad etsin.
- `simulate_bkt_data --clear` faqat `is_simulated=True` bo‘lgan foydalanuvchilarni o‘chirsin. Maydonni qo‘sh.
- Demo parollarni README va kod ichidan olib tashla. Seed parolni `DEMO_PASSWORD` env'dan olsin yoki tasodifiy parol yaratib, uni bir marta chop etsin.

**CI va hujjat**
- `.github/workflows/ci.yml` qo‘sh. Backend uchun: Postgres va Redis servislari, pytest, check, `makemigrations --check`. Frontend uchun: lint, tsc, vitest, build. Ikkinchisi frontend repo'da alohida workflow bo‘ladi.
- README'ni yangila: ishga tushirish tartibi, docker-compose, env'lar. Parollar yozilmasin.
- Commit xabarlari conventional formatda va ID'lar bilan yozilsin. “updated” kabi xabarlar ishlatilmasin.

**Qabul shartlari**
- Barcha testlar PostgreSQL'da o‘tadi.
- `grep` bilan tekshirilganda kuzatiladigan fayllarda maxfiy qiymat qolmagan.
- `manage.py check --deploy` (DEBUG=False) ogohlantirishlari hisobotga yozilgan.

### Bosqich 1 — Ma’lumot ifloslanishini to‘xtatish va javoblar logi
Qamrab oladi: P0-2, P1-1, TM7, ES8 (qisman), D8, D10, D11; audit 4.4 (`_retrieve_prior`, tarix FK), 4.7 (cascade), 4.9 (easy-skip), 6 (ma’lumot sifati xavflari).

**Sun’iy yozuvlarni to‘xtatish**
- `_maybe_skip_easy_questions` va `_cascade_mastery_to_descendants` ni olib tashla.
- Kod bo‘ylab grep qil: real javobdan tashqari `AssessmentAttempt` yaratadigan yo‘l qolmasin. Buni test ham tekshirsin.

**`AssessmentAttempt` ga yangi maydonlar**

| Maydon | Izoh |
|---|---|
| `topic` | FK, PROTECT, javob paytidagi qiymat |
| `course` | FK |
| `attempt_no` | Talaba×mavzu bo‘yicha 1 dan boshlanadi |
| `p_before`, `p_hat`, `p_after` | Yangilashdan oldingi P(L), bashorat, keyingi P(L) |
| `guess_used`, `slip_used` | Javobda ishlatilgan P(G) va P(S) |
| `theta_before`, `theta_after` | Talaba qobiliyati |
| `b_before`, `b_after` | Savol qiyinligi |
| `readiness_score` | Javob paytidagi r_s(w) |
| `was_ready` | Javob paytida mavzu tayyormidi |
| `source` | `adaptive` / `test_session` / `seed` / `simulated` / `legacy` |
| `session` | FK → `TestSessionResult`, null bo‘lishi mumkin |
| `engine_version` | Model versiyasi |
| `kb_version` | Javob paytidagi KB versiyasi |

**Migratsiyalar va bog‘liq o‘zgarishlar**
- Data migratsiyasi: mavjud qatorlar uchun `source=legacy`, `topic=question.topic`; `attempt_no` `answered_at` bo‘yicha hisoblanadi. Legacy qatorlar ichida easy-skip sun’iy yozuvlari ham bor. Ularni ajratib bo‘lmaydi, shuning uchun legacy qatorlar eksperimentlarga kirmaydi.
- `UserKnowledgeHistory` ga `attempt` FK qo‘sh. Prior endi tarixdan emas, joriy talaba holatidan olinadi. Bu `_retrieve_prior` dagi `algorithm_used` xatosini ham yo‘q qiladi.
- `on_delete` siyosatini D11 bo‘yicha o‘zgartir. `Topic` ga `is_archived` qo‘sh. Javoblari bor mavzu uchun DELETE so‘rovi arxivlashga aylansin.
- Seed buyruqlari `source=seed` yozsin va boshqa manbadagi qatorlarning vaqt tamg‘alariga tegmasin.

### Bosqich 2 — Bilimlar bazasi modeli
Qamrab oladi: P0-4, P1-6, P1-7, P2-3, BB1–BB10, GR1–GR3, ES1, ES3; audit 4.1, 4.2, 4.8, 7.4 (sikl tekshiruvidagi N+1).

**Daraxt va tugun turlari**
- Daraxtni django-tree-queries'ga ko‘chir (D3). MPTT maydonlarini olib tashla. `DraggableMPTTAdmin` o‘rniga tree-queries bilan ishlaydigan admin yoz. `test_mptt_tree.py` dagi 25 ta testni yangi semantikaga moslab qayta yoz.
- `kind` maydonini qo‘sh. Data migratsiyasi:
  - ildiz tugun → `course`;
  - savollari bor barg tugun → `topic`;
  - qolganlari → `section`.

  **Ham farzandi, ham savoli bo‘lgan tugun topilsa, to‘xta va foydalanuvchidan so‘ra.**
- Y4: savollar faqat `topic` turidagi tugunga bog‘lanadi. Bu serializer, import, admin va servisda tekshiriladi. `Choice` uchun ≤4 variant cheklovi `bulk_create` yo‘lida ham ishlasin (import servisida tekshir).

**Prerekvizitlar va servis**
- `TopicPrerequisite` ga `weight` (0, 1] maydonini va `CheckConstraint(topic ≠ prerequisite)` ni qo‘sh.
- `KnowledgeBaseVersion` singleton modelini yarat.
- `curriculum/services/kb.py` ni yoz: `add_prerequisite`, `update_weight`, `remove_prerequisite`, `create_node`, `move_node`, `archive_node`.
  - Har biri advisory lock ostida ishlaydi va KB versiyasini oshiradi.
  - API, admin (`save_model`/`delete_model`), import va seed faqat shu servis orqali yozadi.
  - `Model.save()` va `QuerySet.bulk_create/update` orqali chetlab o‘tishning oldi olinsin (guard + test).
- Algoritm 2.1 ni zanjir qaytarishi bilan amalga oshir.
- Y1 ni servisning o‘zida tekshir. `InvalidMove` va validatsiya xatolari 400 qaytarsin, 500 emas.

**API**
- O‘qituvchi uchun prerekvizitlar CRUD API: ro‘yxat (meros bilan kengaytirilgan ko‘rinish ham), yaratish, vaznni o‘zgartirish, o‘chirish. 400 javobida `{"reason": "cycle" | "nested" | ..., "chain": [...]}`.

**Graf servisi**
- `curriculum/services/graph.py` ni qayta yoz:
  - G_L ni qurish;
  - global `pos` (D4);
  - Algoritm 2.2 (ustuvor navbat, lev, `CycleError`);
  - Desc\* (bitset), ortiqcha qirralar va κ;
  - KB versiyasiga bog‘langan kesh.
- O‘qituvchi uchun ogohlantirishlar endpoint'i: ortiqcha qirralar va κ.
- Eski `topological_order` va `get_all_prerequisites` ni olib tashla. Hech narsani tozalamaydigan `_invalidate_tree_cache` ni versiyaga bog‘langan kesh bilan almashtir.

**Testlar**
- 4-bo‘limdagi graf qiymatlari va probe'lar.
- PostgreSQL'da parallellik testi: ikki thread bir vaqtda ikkita qirra qo‘shadi, ular birgalikda sikl hosil qiladi. Aynan bittasi muvaffaqiyatli bo‘lishi kerak.

### Bosqich 3 — Talaba modeli
Qamrab oladi: P0-5, TM1–TM6, ES4, ES5, ES6; audit 4.4, 4.5, 4.6, 4.7 va savol tanlashdagi θ nomuvofiqligi (`question_selection.py:66`).

**`neuro_model/` paketi**
- Tarkibi: `bkt.py`, `irt.py` (σ, chegaralangan guess/slip, γ), `elo.py`, `init.py` (P(L0)), `graph.py` (BFS, Kahn, Desc\*, Need — sof funksiyalar), `readiness.py`, `trajectory.py`.
- Type hint'lar bo‘lsin, Django import qilinmasin.

**Modellar**
- `TopicModelParams`: P0, PT, G0, S0, `source` (`default`/`fitted`), `fitted_at`.
- `UserAbility` (user, course) juftligi uchun saqlanadi va `n_answers` maydoniga ega bo‘ladi.
- `Question` ga `n_answers` qo‘shiladi. `b_q` endi Elo bilan yangilanadi.

**Dvigatel**
- Bitta dvigatel `thesis_hybrid`, `use_irt` va `use_prereq_init` bayroqlari bilan (3.3).
- Eski `bayesian`, `hybrid_bkt_irt` va `streak` dvigatellari hamda chiziqli modifier'lar olib tashlanadi. Klassik BKT bayroqlar orqali qayta hosil bo‘ladi.
- `orchestrator` Algoritm 2.4 ni aniq tartibda bajaradi. Yozuvlar `AssessmentAttempt` maydonlariga tushadi.

**Savol tanlash**
- Mavzu ichida, yaqinda javob berilmagan savollar orasidan |b_q − θ_s| eng kichik bo‘lgan savol tanlanadi. Teng bo‘lsa, `id` bo‘yicha.
- θ_s kurs bo‘yicha olinadi, shuning uchun tanlash va yangilash bir xil θ dan foydalanadi.

**Buyruqlar**
- `calibrate_bkt`: pyBKT EM yoki chegaralangan grid search (G ≤ 0.3, S ≤ 0.1). Faqat `adaptive` va `test_session` manbalaridagi, rozilik berilgan javoblarda ishlaydi. Natija `TopicModelParams` ga yoziladi. `--dry-run` rejimi bor.
- `rebuild_student_states`: talaba holatlarini javoblar logini xronologik qayta o‘ynash orqali deterministik qayta quradi. `--include-legacy` bayrog‘i faqat demo uchun.

**Testlar**
- 4-bo‘limdagi BKT, guess/slip, Elo va P(L0) qiymatlari.
- 2.5-tasdiq xossasi.
- a_q=0 va λ=0 bo‘lganda klassik BKT chiqishi.
- Tartib testi: p̂ yangilashdan oldingi θ va b dan hisoblanadi.

### Bosqich 4 — Tayyorlik va holatlar
Qamrab oladi: P0-3, P0-6, TY1–TY6, ES2; audit 4.3 (to‘rtta implementatsiya, global `is_unlocked`, qayta yopilish, yopiq mavzuga javob berish), 3.4 (ikki xil son), 2.4 (`learning_path/tree` dagi `mastery_percentage` aslida `score`).

**Talaba holati modeli**
- `StudentTopicState` modeli (yoki `UserKnowledgeState` ni qayta tuzish). Maydonlari: `p_mastery`, `mastered_flag`, `status`, `missing_count`, `started_at`, `kb_version`, `attempts`, `correct`, `accuracy`.
- Aralash shkaladagi eski qiymatlar ko‘chirilmaydi. Holatlar `rebuild_student_states` buyrug‘i bilan qayta quriladi.

**Yagona tayyorlik servisi**
- Vazifalari: yangi talaba uchun boshlang‘ich holat, Algoritm 2.3, TY5, TY6.
- Olib tashlanadi: `Topic.is_unlocked`, to‘rtta eski implementatsiya, ota tugunga fallback, `settings.MASTERY_THRESHOLD`, `orchestrator.MASTERY_THRESHOLD`.

**Endpoint'lar**
- `next_question`, `submit_answer` va `test_session` yopiq mavzuga 403 qaytaradi. Javob tanasi: `{"missing": [{"topic_id", "name", "p_mastery"}]}`.
- Daraxt, DAG, dashboard va testlar ro‘yxati API'lari bir xil `p_mastery`, `accuracy` va `status` maydonlarini qaytaradi.

**Testlar**
- 4-bo‘limdagi tayyorlik misoli.
- Meros probe'i.
- TY5 va TY6.
- 403 javoblari.

### Bosqich 5 — Test sessiyasi modeldan o‘tadi
Qamrab oladi: P0-1 (backend qismi), D7; audit 2.6 (`SubmitTestSessionView` atomar emas va read-modify-write), 7.1 (`test_test_session.py:140` dagi 100.0), 7.4 (`TestsListView` va `SubmitTestSession` N+1).

- `SubmitTestSessionView` ning mantig‘ini servisga ko‘chir. Servis atomar bo‘lsin va javoblarni ketma-ket Algoritm 2.4 orqali o‘tkazsin (`source=test_session`, `session` FK).
- `TestSessionResult` modeli: vaznli ball, `passed`, vaqtlar. U `p_mastery` va tayyorlikka ta’sir qilmaydi.
- `test_test_session.py` ni tuzat: `p_mastery` ∈ [0, 1] bo‘lishi va qayta o‘ynash natijasiga teng bo‘lishi tekshirilsin.
- N+1'larni tuzat. `dashboard.py:66` dagi ortiqcha `atomic` ni olib tashla.

### Bosqich 6 — Trayektoriya va API
Qamrab oladi: P1-8 (backend), TR1–TR4, ES7; audit 4.9.

- Trayektoriya servisi Algoritm 2.5 ni tuzilmali sabablari bilan amalga oshiradi.
- Endpoint'lar:
  - `GET /api/learning/trajectory/?course=<id>` — A, B, C, D guruhlari;
  - `GET /api/learning/path-to/<topic_id>/` — Need(g) va yo‘l.
- Dashboard shu servisdan foydalanadi. To‘rtta eski evristika olib tashlanadi. Tartib topologik bo‘ladi, `position` bo‘yicha emas.
- Testlar: Need(t7) va takrorlash ustuvorligi (4-bo‘lim). So‘rovlar soni byudjeti ham tekshirilsin.

### Bosqich 7 — Frontend
Qamrab oladi: P0-1 (UI), TR5, P2-5, P2-6, D16, D17, D19; audit 3.2–3.4, 7.2 (lint 71, tsc 18, bundle 2.36 MB), 7.3 (localStorage'dagi tokenlar).

**Shkala va adaptiv mashq**
- Foiz formatlash uchun bitta util yoz. Barcha `mastery_percentage` va `>= 70` larni `p_mastery` va `status` bilan almashtir. “0.8%” yoki “100%” kabi xatolar yo‘qolsin.
- Adaptiv mashqni ulash: `useAdaptiveQuiz` → `next_question`/`submit_answer`. QuizSession'da “Mashq” va “Test” rejimlari bo‘lsin. Ortiqcha qolgan `QuizEngine` ni olib tashla.

**Holatlar va talaba interfeysi**
- `CustomTopicNode` va daraxt rejimida 5 ta holat. Ranglar dissertatsiyadagi 2.3- va 2.4-rasmlarga mos:
  - mastered — yashil;
  - in_progress — ko‘k (aksent);
  - closed — kulrang uzuq chiziq;
  - open — neytral;
  - review — sariq.

  Legenda ham qo‘shilsin.
- `Course.tsx` o‘qituvchi endpoint'lari o‘rniga talaba uchun yozilgan faqat o‘qish endpoint'laridan foydalanadi.
- Yopiq tugun bosilganda yetishmayotgan prerekvizitlar ro‘yxati `p_mastery` bilan va “Yo‘lni ko‘rsat” tugmasi bilan chiqsin.
- Dashboard: A–D guruhlari sabablari bilan. Sabablar matni bitta lug‘at faylidan olinadi. Maqsadli mavzuni tanlash va yo‘lni ko‘rsatish ham bo‘lsin.

**O‘qituvchi interfeysi**
- React Flow'da prerekvizit muharriri: `onConnect` qirra qo‘shadi, qirrani o‘chirish va vaznni tahrirlash mumkin.
- 400 javobida sikl zanjiri yoki Y2 sababi ko‘rsatiladi.
- Ortiqcha qirralar va κ uchun ogohlantirishlar paneli bo‘lsin.
- Daraxtni ko‘chirishdagi xatolar ham foydalanuvchiga ko‘rsatilsin. Daraxtni drag-and-drop bilan tahrirlash ixtiyoriy, forma orqali tahrirlash yetarli.

**Rollar va kod tozaligi**
- Marshrut himoyasi API qaytargan `role` bo‘yicha ishlasin. `is_staff=False` bo‘lgan o‘qituvchi panelga kira olsin.
- O‘lik kodni olib tashla: `KnowledgeGraph.tsx`, ishlatilmaydigan supabase client. Tutor `VITE_ENABLE_TUTOR` flag'i ortiga o‘tsin.
- D19 bo‘yicha react-query.
- Frontend README'sini NeuroLearn uchun qayta yoz: Lovable/“Knowledge Bloom” shabloni matnini olib tashla, env'lar va ishga tushirish tartibini yoz.

**Sifat va xavfsizlik**
- lint — 0 error, tsc — 0 xato.
- Marshrutlar `React.lazy` bilan code-splitting qilinsin. Bundle hajmi oldin va keyin hisobotga yozilsin.
- D16 bo‘yicha auth. Backend'da cookie bilan ishlaydigan refresh view va CSRF himoyasi.
- vitest testlari: formatlash, status → rang mosligi, sabablarni ko‘rsatish, muharrirdagi xato holati.

### Bosqich 8 — Eksperimentlar va rozilik
Qamrab oladi: P1-2, P1-3, P1-4, EX1–EX4, EX6, ES8, D12–D14; audit 6.

**Rozilik**
- Rozilik maydonlarini qo‘sh, ro‘yxatdan o‘tish va profil sahifalarida rozilik checkbox'i va qisqa matn bo‘lsin.
- Hard-delete siyosati D11 bo‘yicha (`accounts/tasks.py`).

**Eksport**
- `export_research_data` buyrug‘i. Faqat rozilik bergan talabalar va `source ∈ {adaptive, test_session}` olinadi (bayroq bilan o‘zgartirsa bo‘ladi).
- Chiqish fayllari:
  - pyKT formati — pyKT repozitoriysidagi `data_preprocess` misollariga qarab mosla;
  - xom CSV;
  - KB grafi JSON: daraxt, E_P, E_L, ω;
  - metadata: versiyalar, filtrlar, qatorlar soni.
- Fayllarda faqat psevdonim bo‘ladi.

**`experiments/` papkasi**
- `README`, `requirements.txt`: pykt-toolkit, pyBKT, scikit-learn, scipy, pandas, CPU uchun torch.
- Yuklovchilar:
  - DBE-KT22 — fayllarni foydalanuvchi qo‘lda yuklab oladi, skript yo‘lini qabul qiladi. KC munosabatlari Y2/Y3 bo‘yicha tekshiriladi, sikl topilsa SCC'lar birlashtiriladi (Tarjan) va bu qayd etiladi.
  - ASSISTments 2009 — pyKT preprocess orqali.
  - Mahalliy eksport.
- Modellar:
  - BKT, BKT+IRT (λ=0) va BKT+IRT+Pre — `neuro_model` orqali;
  - pyBKT bilan kichik qism ma’lumotda o‘zaro tekshiruv;
  - Elo/Rasch;
  - PFA (KC bo‘yicha muvaffaqiyat/muvaffaqiyatsizliklar soni + logistik regressiya);
  - DKT va AKT — pyKT orqali.
- Ajratish: talabalar bo‘yicha 5 qism, o‘qitish talabalarining 20% validatsiyaga, seed'lar qotirilgan. Parametrlar faqat o‘qitish to‘plamida baholanadi. λ va τ validatsiyada tanlanadi.

**Metrikalar va statistika**
- `metrics.py`: AUC, RMSE, accuracy, dastlabki k ∈ {3, 5} urinish bo‘yicha alohida.
- `h1.py`:
  - qoidalar: ehtimoliy (r ≥ τ), bajarilganlik (har bir prerekvizit savoliga ≥ 1 javob), o‘tish bali (prerekvizitlar bo‘yicha aniqlik ≥ `pass_mark`);
  - teng qamrov τ ni qidirish orqali ta’minlanadi;
  - natijalar: xato ulushi, qamrov va r_s(w) bo‘yicha AUC.
- `stats.py`:
  - talabalar bo‘yicha bootstrap (1000) va 95% ishonch oralig‘i;
  - fast DeLong (Sun & Xu, 2014), u bootstrap natijasi bilan solishtirib test qilinadi;
  - Holm tuzatmasi.
- Sezgirlik tahlili: τ ∈ {0.70, 0.80, 0.90, 0.95}, δ ∈ {0.05, 0.10, 0.15}.

**Ishga tushirish**
- `run_all.py --dataset ... --models ... [--quick]`.
- Natijalar `experiments/results/<dataset>/<timestamp>/` ga yoziladi: `metrics.json`, `tables.md` (3.3-bo‘limga qo‘yishga tayyor), `env.txt`.
- DKT va AKT CI'da ishga tushirilmaydi.

**Simulyator**
- `simulate_bkt_data` ni generativ qilib qayta yoz: talaba×mavzu yashirin bilim holati, BKT o‘tishlari va prerekvizitlar ta’siri.
- U faqat sanity testlar uchun:
  - parametrlarni tiklash testi — fit generator parametrlarini ma’lum tolerans ichida qaytarishi kerak;
  - generatorda prerekvizit ta’siri bor bo‘lsa, Pre modeli dastlabki urinishlarda AUC ni oshirishi kerak.
- Natijalarga “simulated — dissertatsiya natijasi emas” belgisi qo‘yiladi.

### Bosqich 9 — Saqlash usullari benchmarki
Qamrab oladi: P1-5, EX5, H4; audit 6 (`benchmark_tree.py` ning kamchiliklari).

- `benchmarks` app'i, ikkita alohida jadval bilan: `MpttNode` (django-mptt) va `CteNode` (django-tree-queries). Faqat PostgreSQL'da ishlaydi.
- Daraxt generatori (seed bilan):
  - kursga o‘xshash: 3–5 daraja, keng;
  - chuqur zanjir;
  - tasodifiy: ota tugun mavjudlar orasidan tasodifiy tanlanadi.

  Hajmlar: 10³, 10⁴ va 10⁵ tugun.
- Amallar: shoxni o‘qish, ajdodlarni o‘qish, oxiriga barg qo‘shish, eng chapga barg qo‘shish, shoxni ko‘chirish, shoxni o‘chirish va parallel yozish.
- Parallel yozish: 2, 4 va 8 ta jarayon, har biri o‘z ulanishi bilan, belgilangan vaqt davomida aralash qo‘shish va ko‘chirish bajaradi. Keyin yaxlitlik tekshiriladi:
  - Y1: ota tugunlar zanjirida sikl yo‘q, har bir daraxtda bitta ildiz;
  - MPTT uchun: lft < rght, oraliqlar to‘qnashmaydi, `rebuild` bilan solishtirish.
- O‘lchash tartibi: 5 ta qizdirish (warm-up), keyin 30 ta takror. Har bir amal uchun yoziladi: mediana, p95, SQL so‘rovlar soni (`CaptureQueriesContext`) va o‘zgargan qatorlar soni (rowcount yig‘indisi yoki oldin/keyin solishtirish).
- Natijalar CSV va jamlangan jadval ko‘rinishida saqlanadi. Postgres versiyasi va apparat ma’lumoti ham yoziladi. Eski `benchmark_tree.py` almashtiriladi.

### Bosqich 10 — Sinovlar, samaradorlik va yakuniy hisobot
Qamrab oladi: P1-9, P2-4, SN1–SN3; audit 7.1 (parallellik testi `OperationalError` ni yutadi, `accounts` testlari yo‘q), 7.4.

**Xossalarga asoslangan testlar (Hypothesis).** Tasodifiy daraxtlar, prerekvizitlar va amallar ketma-ketligi yaratiladi. Har bir qabul qilingan amaldan keyin tekshiriladi:
- G_L'da sikl yo‘q;
- topologik tartib barcha qirralarga mos;
- hisoblagichlar qaytadan hisoblangan qiymatlarga teng;
- ehtimolliklar [0, 1] oralig‘ida;
- 2.5-tasdiq bajariladi;
- TY5 buzilmaydi.

**Boshqa testlar**
- Haqiqiy parallellik testlari PostgreSQL'da. Eski, xatoni yutadigan test olib tashlanadi.
- `accounts` testlari: ro‘yxatdan o‘tish, rollar, rozilik, o‘chirish siyosati, JWT cookie va blacklist.
- So‘rovlar byudjeti: `submit_answer` uchun ≤ 12 SQL. Aniq son testda qayd etiladi.
- Coverage maqsadlari: `neuro_model` ≥ 95%, servislar ≥ 85%, umumiy ≥ 80%.
- Locust: `locustfile.py` (login → `next_question` → `submit_answer` → `trajectory`). Lokal ravishda 50 foydalanuvchi bilan 2 daqiqa ishga tushiriladi. `submit_answer` va `trajectory` uchun p50 va p95 natija fayliga yoziladi.

**Yakuniy hujjatlar**
- `REMEDIATION_REPORT.md`:
  - auditdagi barcha topilmalar bo‘yicha bog‘liqlik matritsasi;
  - har bir natijani qayta hosil qilish buyruqlari;
  - qolgan xavflar;
  - dissertatsiyaga kiritilishi kerak bo‘lgan qiymatlar: kalibrlangan parametrlar, benchmark va eksperiment natijalari fayllari.
- `docs/THESIS_MAPPING.md` — II bobdagi har bir element qayerda amalga oshirilgani va qaysi test bilan tekshirilgani:

| II bob elementi | Kod (fayl:funksiya) | Test |
|---|---|---|
| Algoritm 2.1–2.5 | … | … |
| Formulalar | … | … |
| 2.1–2.6-tasdiqlar | … | … |
| Y1–Y4 | … | … |
| D6 dagi farqlar (masalan, θ ni cheklash) | … | … |

---

## 6. Tugallanganlik mezoni

Ish quyidagi barcha shartlar bajarilganda tugallangan hisoblanadi:
- 4-bo‘limdagi barcha etalon testlar o‘tadi;
- CI ikkala repozitoriyda yashil;
- bog‘liqlik matritsasida “Kechiktirildi” deb belgilangan har bir qatorning sababi yozilgan;
- `experiments/run_all.py --quick` va `run_tree_benchmark --quick` toza muhitda xatosiz ishlaydi.
