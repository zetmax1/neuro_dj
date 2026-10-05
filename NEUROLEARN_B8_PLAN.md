# NeuroLearn — 7.1 (kichik tuzatishlar) va 8-bosqich (8a / 8b)

Bu fayl `NEUROLEARN_REMEDIATION.md`, `NEUROLEARN_UI_ADDENDUM.md` va `NEUROLEARN_B2FIX_B3.md` ga qo‘shimcha. Unda:
- 7-bosqichdan keyin qolgan kichik ishlar (7.1);
- 8-bosqichni ikkiga bo‘lish va buning sababi;
- yangi qarorlar D39–D45.

---

## 0. Tasdiq

0–7-bosqichlar qabul qilinadi. Barcha Q qarorlari (Q0-1…Q7-x) tasdiqlanadi.

Alohida ta’kidlanadi: 7-bosqichda qilingan ikkita tanlov to‘g‘ri va saqlanadi.
- **dagre standart emas, `lev` joylashuvi standart.** Dissertatsiyaga rasm olishda bir xil graf har doim bir xil ko‘rinishi shart.
- **Soxta ma’lumotli sahifalarni olib tashlash.** `KnowledgeSearch`, `Profile` massivlari, `mistakeStorage`, `sampleQuestions` — ularning o‘rniga haqiqiy ma’lumot keldi.

---

## 1. Nega 8-bosqich ikkiga bo‘linadi

8-bosqichda ikki xil ish bor va ularning shoshilinchligi butunlay boshqacha.

- **Rozilik va eksport (8a)** — kichik ish, lekin u haqiqiy talaba ma’lumotini yig‘ishni ochadi. Ma’lumot yig‘ish esa haftalar davom etadi va uni tezlashtirib bo‘lmaydi.
- **Eksperimentlar quvuri (8b)** — katta ish, lekin u ochiq ma’lumotlar to‘plamlarida (DBE-KT22, ASSISTments) mahalliy ma’lumotsiz ham ishlay oladi.

Shuning uchun tartib: avval 8a, keyin ma’lumot yig‘ish boshlanadi va u fonda davom etadi, 8b esa shu vaqtda ochiq ma’lumotlarda qilinadi. Agar 8 bitta katta bosqich sifatida bajarilsa, ma’lumot yig‘ish bir necha hafta kech boshlanadi.

---

## 2. 7.1 — qolgan kichik ishlar

### D39 — Kurs konstruktorining tuzilmasi

Addendum 2.6 ikki narsani talab qilgan edi. Prerekvizit muharriri bajarildi — bu eng muhimi. Tuzilma esa o‘zgarmadi: mavjud kursni tahrirlash hamon 5 qadamli wizard orqali.

Qilinadigan ish:
- Konstruktor ikki rejimga bo‘linadi: **yangi kurs yaratish** (hozirgi wizard o‘zgarishsiz qoladi) va **mavjud kursni tahrirlash** (chapda daraxt, o‘ngda tanlangan tugun muharriri).
- Tahrirlash rejimida: tugun turi (`section` ↔ `topic`, servis ruxsat bergan hollarda), aka-uka tugunlar orasidagi tartib (yuqoriga/pastga), nom, tavsif, o‘tish bali.
- Prerekvizit muharriri alohida yorliq sifatida shu yerda ham ochiladi (hozir faqat wizard'ning 5-qadamida).
- Drag-and-drop shart emas. Tugmalar yetarli.

Sabab: hozir o‘qituvchi bitta mavzuning nomini o‘zgartirish uchun ham besh qadamli oqimdan o‘tadi. Himoyada “o‘qituvchi bilimlar bazasini qanday boshqaradi” degan savol beriladi, javob esa bitta ekranda ko‘rinishi kerak.

### D40 — Haqiqiy mavzu qidiruvi

`KnowledgeSearch` sahifasi 12 ta soxta tushuncha bilan qattiq yozilgani uchun olib tashlandi — bu to‘g‘ri qaror edi. Lekin qidiruvning o‘zi foydali, faqat u haqiqiy ma’lumot ustida ishlashi kerak.

Qilinadigan ish:
- Yuqori paneldagi qidiruv maydoni: mavzu nomi bo‘yicha, backend'dagi faol tugunlar orasidan.
- Natijada mavzu nomi, kursi, holati va P(L) ko‘rsatiladi; bosilganda O‘quv yo‘lida shu tugun tanlanadi.
- Backend: `GET /api/learning/search/?q=` — nom bo‘yicha `icontains`, arxivlanganlar chiqmaydi, natija 20 ta bilan cheklanadi.
- Yangi sahifa yaratilmaydi, bu — panel.

### D41 — Skrinshotlar

Addendum 2.11 bo‘yicha `docs/ui/` hali bo‘sh. Bu dissertatsiyaning 3.1-bo‘limi uchun kerak.

Agar bu muhitda brauzer ishlamasa, muqobil yo‘l: `seed_thesis_demo` bilan to‘ldirilgan bazada Playwright yoki `puppeteer` skripti yoziladi (`scripts/screenshots.*`), uni foydalanuvchi o‘z mashinasida ishga tushiradi. Skript sahifalar ro‘yxatini, kenglikni (1440, 1280, 768) va tilni (`uz`) qabul qiladi. Skriptning o‘zi — 7.1 ning natijasi; rasmlarni foydalanuvchi oladi.

---

## 3. 8a — rozilik va eksport

### D42 — Rozilik

- `CustomUser` ga: `research_consent` (boolean, standart `False`), `research_consent_at`, `research_pseudonym`.
- Rozilik **standart holatda yo‘q**. U faqat talabaning aniq harakati bilan beriladi.
- Qayerda so‘raladi: ro‘yxatdan o‘tishda ixtiyoriy belgi sifatida va profil sahifasida. Majburiy emas — rozilik bermagan talaba tizimdan to‘liq foydalanadi.
- Matn sodda bo‘lsin: qanday ma’lumot (javoblar va ularning vaqti), nima uchun (magistrlik dissertatsiyasi), ism va email chiqmasligi, istalgan vaqtda bekor qilish mumkinligi.
- **Bekor qilish** (`PATCH /api/me/consent/` bilan `false`) kelgusi eksportlardan chiqaradi. Allaqachon olingan eksport fayllari o‘zgarmaydi — buni matnda ochiq aytish kerak.
- Rozilik o‘zgarishi `research_consent_at` bilan qayd etiladi.

### D43 — Psevdonim

- `research_pseudonym` — tasodifiy, qaytarib bo‘lmaydigan (masalan, `secrets.token_hex(8)`), foydalanuvchi qatori yaratilganda beriladi.
- U foydalanuvchi id'si, email'i yoki ismidan hosil qilinmaydi.
- Eksportda faqat shu qiymat chiqadi. Ichki `user_id` ham chiqmaydi: u boshqa jadvallar bilan solishtirilsa, anonimlik yo‘qoladi.

### D44 — Eksport qamrovi

`export_research_data` buyrug‘i quyidagi javoblarni oladi:
- `source ∈ {adaptive, test_session}`;
- `engine_version` `thesis_hybrid` bilan boshlanadi;
- foydalanuvchida `research_consent=True` va `is_simulated=False`;
- mavzu arxivlanmagan.

Chiqarib tashlanadi: `legacy`, `seed`, `simulated`, `review_repeat`. Bayroqlar bilan kengaytirish mumkin (`--include-simulated` faqat quvurni sinash uchun), lekin standart holatda yo‘q.

Chiqish fayllari bitta papkaga yoziladi:
- pyKT formatidagi fayl;
- xom CSV (ledger ustunlari: p̂, P(G), P(S), P(L) oldin→keyin, θ, b, `attempt_no`, `readiness_score`, `was_ready`);
- bilimlar bazasi grafi JSON (daraxt, E_P, E_L, ω, `kind`, `pos`, `lev`);
- `metadata.json`: eksport sanasi, filtrlar, qatorlar soni, talabalar soni, `kb_version`, `engine_version`, kod commit'i.

Metadata muhim: dissertatsiyada “natijalar qaysi ma’lumotdan olingan” degan savolga aynan shu fayl javob beradi.

### D45 — Nazorat

- `--dry-run` faqat sonlarni chop etadi.
- Buyruq eksport qilingan talabalar sonini va rozilik bermagani uchun chiqarib tashlanganlar sonini alohida ko‘rsatadi.
- Test: eksport faylida email, ism va `user_id` yo‘qligi; rozilik bermagan talaba chiqmasligi; `review_repeat` qatorlari yo‘qligi.

---

## 4. 8b — eksperimentlar quvuri

Tafsilotlar `NEUROLEARN_REMEDIATION.md` ning 8-bosqichida. Bu yerda faqat qo‘shimchalar.

- **Ablatsiya allaqachon tayyor.** `use_irt` va `use_prereq_init` bayroqlari 3-bosqichda yozilgan, shuning uchun BKT, BKT+IRT (λ=0) va BKT+IRT+Pre uchun alohida implementatsiya yozilmaydi — bir xil kod, uch xil bayroq. Buni eksperiment kodida ham shunday ishlatish kerak: prototipda ishlaydigan model bilan baholanadigan model aynan bir xil bo‘lsin.
- **Ochiq ma’lumotlar birinchi.** DBE-KT22 va ASSISTments bilan quvur to‘liq ishlasin. Mahalliy ma’lumot keyin, u tayyor bo‘lganda, xuddi shu quvurdan o‘tadi.
- **DBE-KT22 ni qo‘lda yuklab olish kerak.** Skript fayl yo‘lini argument sifatida oladi, internetdan o‘zi yuklab olmaydi. KC munosabatlari Y2/Y3 bo‘yicha tekshiriladi; sikl topilsa, kuchli bog‘langan komponentlar birlashtiriladi va bu metadata'ga yoziladi.
- **Natijalar papkasi.** `experiments/results/<dataset>/<timestamp>/` ichida `metrics.json`, `tables.md` (3.3-bo‘limga qo‘yishga tayyor), `env.txt` (versiyalar, seed'lar, buyruq).
- **Simulyatsiya — faqat quvurni sinash uchun.** Natijalarda “simulated — dissertatsiya natijasi emas” belgisi bo‘lishi shart (D13).

---

## 5. Ish tartibi

1. **7.1** — D39, D40, D41. Bir commit. Tugagach to‘xta.
2. **8a** — D42–D45. Bir commit. Tugagach to‘xta.
3. **8b** — `NEUROLEARN_REMEDIATION.md` ning 8-bosqichi + 4-bo‘limdagi qo‘shimchalar.

Har bosqich oxirida odatdagidek: testlar, `REMEDIATION_PROGRESS.md`, `docs/THESIS_MAPPING.md`, commit, qisqa hisobot.

`docs/THESIS_MAPPING.md` ga 8a dan keyin yangi bo‘lim qo‘shiladi: rozilik va anonimlashtirish qaysi faylda, qaysi test bilan tekshiriladi. Bu himoyada etika savoliga javob bo‘ladi.