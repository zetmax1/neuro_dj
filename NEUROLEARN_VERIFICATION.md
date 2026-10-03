# NeuroLearn: mustaqil tekshiruv (tester) topshirig‘i

Sen bu loyihada mustaqil tekshiruvchisan. Kodni boshqa sessiya yozgan, uning testlariga ham, `REMEDIATION_PROGRESS.md` dagi “Bajarildi” belgilariga ham ishonma. Vazifang: kod II bob modelini to‘g‘ri amalga oshirganini o‘zing yozgan testlar bilan isbotlash yoki rad etish.

Kirish ma’lumotlari:
- `NEUROLEARN_REMEDIATION.md` — 3-bo‘lim (formulalar va algoritmlar) va 4-bo‘lim (etalon misol va kutilgan qiymatlar);
- `NEUROLEARN_UI_ADDENDUM.md` — UI talablari;
- `REMEDIATION_PROGRESS.md` — qaysi bosqichlar bajarilgani.

---

## 1. Qoidalar

1. **Prototip kodiga tegma.** Yozish faqat quyidagi joylarda ruxsat etiladi:
   - backend'dagi `verification/` papkasi;
   - frontend'dagi `e2e/` papkasi;
   - `VERIFICATION_REPORT.md` fayli.

   Topilgan xatoni tuzatma, faqat hisobotga yoz.
2. **Etalon kod spetsifikatsiyadan yoziladi.** Etalon (oracle) — tekshirilayotgan kod bilan solishtiriladigan, mustaqil yozilgan kod. U `NEUROLEARN_REMEDIATION.md` ning 3-bo‘limidagi formulalar asosida yoziladi, prototip kodidan nusxa olinmaydi. Graf algoritmlari uchun etalon sifatida `networkx` ishlatiladi. U faqat `verification/requirements.txt` da bo‘ladi.
3. **Alohida baza.** Tekshiruv uchun alohida PostgreSQL bazasi yaratiladi (masalan, `neurolearn_verify`, xuddi shu compose servisida). Dev bazasiga ulanma.
4. **Takrorlanuvchanlik.** Tasodifiy jarayonlarning seed'i qotiriladi va hisobotga yoziladi.
5. **Bajarilmagan bosqichlar.** `REMEDIATION_PROGRESS.md` ga ko‘ra hali bajarilmagan bosqichga tegishli tekshiruv “N/A (Bn bajarilmagan)” deb belgilanadi va o‘tkazib yuboriladi.
6. **Til.** Hisobot o‘zbek tilida (lotin), texnik atamalar inglizcha.

---

## 2. Tekshiruvlar

Har bir tekshiruvning ID'si bor. Ular hisobot jadvalida ishlatiladi.

### A. Sof funksiyalar (`neuro_model`) — 3-bosqichdan keyin
- **V-A1.** 4-bo‘limdagi barcha sonli qiymatlar 1e-3 aniqlikda chiqadi:
  - BKT ketma-ketligi;
  - qiyin va oson savol hamda a=0 holati;
  - Elo;
  - prerekvizitlardan P(L0);
  - tayyorlik misoli (0.8921 → 0.9764).
- **V-A2. Differensial test.** Kamida 10 000 ta tasodifiy kirish uchun etalon va prototip natijalari 1e-9 aniqlikda bir xil bo‘lishi kerak. Tekshiriladigan funksiyalar: Bayes yangilanishi, PT o‘tishi, chegaralangan P(G)/P(S), γ formulalari, Elo va K(n), P(L0) va c chegarasi, ikki chegarali M qoidasi.
- **V-A3. Xossalar:**
  - P(G) ≤ 0.3 va P(S) ≤ 0.1, shuning uchun har doim P(G) + P(S) < 1;
  - 2.5-tasdiq: o‘tishdan oldingi posterior to‘g‘ri javobda oshadi, xatoda kamayadi;
  - barcha ehtimolliklar [0, 1] oralig‘ida;
  - θ ±`THETA_CLAMP` chegarasidan chiqmaydi;
  - a_q = 0 va λ = 0 bo‘lganda klassik BKT bilan aynan bir xil natija.
- **V-A4. Mutatsion test (ixtiyoriy, 30 daqiqagacha).** `mutmut` bilan `neuro_model` formulalarini sun’iy buzib, mavjud testlar buni ushlashini tekshir. Mutatsiya ballini hisobotga yoz.

### B. Bilimlar bazasi va graf — 2-bosqichdan keyin
- **V-B1.** Etalon kurs (4-bo‘lim): E_L dagi 10 ta qirra, topologik tartib, lev, |Desc\*|, ortiqcha qirralar, κ = 0. FIFO navbatdagi farqli tartib ham tekshiriladi.
- **V-B2.** Rad etilishi kerak bo‘lgan holatlar va ularning sababi:
  - (t8, t3) — `cycle`, zanjir t3 → t6 → t8;
  - (B3, t6) — `nested`;
  - t4 ni B3 ga ko‘chirish;
  - auditdagi uchta probe.
- **V-B3. Tasodifiy taqqoslash.** Kamida 500 ta tasodifiy o‘rmon va prerekvizitlar to‘plami uchun natija `networkx` bilan solishtiriladi:
  - G_L — sodda yoyish bilan;
  - qo‘shishga ruxsat — `is_directed_acyclic_graph` bilan;
  - tartib — barcha qirralarga mosligi va `(pos, id)` bo‘yicha leksikografik eng kichik ekani;
  - lev — eng uzun yo‘l bilan;
  - Desc\* — `descendants` bilan;
  - ortiqcha qirralar — `transitive_reduction` bilan.
- **V-B4. Chetlab o‘tish urinishlari.** `bulk_create`, `QuerySet.update` va admin orqali yozish yaxlitlikni buza olmasligi kerak.
- **V-B5. Parallellik.** Ikki parallel tranzaksiya birgalikda sikl hosil qiladigan ikkita qirra qo‘shadi. Aynan bittasi muvaffaqiyatli bo‘lishi kerak. Test 20 marta takrorlanadi.
- **V-B6. KB versiyasi.** Har bir muvaffaqiyatli o‘zgarishdan keyin versiya aniq bittaga oshadi, rad etilgan o‘zgarishdan keyin esa o‘zgarmaydi.

### C. API orqali to‘liq ssenariylar — 4–6-bosqichlardan keyin
Ssenariylar faqat HTTP orqali bajariladi (DRF test client yoki live server).
- **V-C1.** O‘qituvchi etalon kursni API orqali quradi. Noto‘g‘ri amallarga 400 qaytadi va javobda sabab hamda zanjir bo‘ladi.
- **V-C2.** Talabaning boshlang‘ich holatlari: t1 va t2 ochiq, qolganlari yopiq. Yopiq mavzu uchun `missing` ro‘yxati to‘g‘ri.
- **V-C3.** Oldindan belgilangan javoblar ketma-ketligi uchun har bir javobdan keyingi `p_hat`, `p_before`, `p_after`, `guess_used`, `slip_used`, θ va b etalonning ketma-ket qayta o‘ynash natijasiga teng. Alohida tekshiriladi: `p_hat` yangilashdan **oldingi** holatdan hisoblangan.
- **V-C4.** t6 aynan kutilgan javobdan keyin ochiladi. Undan oldin t6 ga `next_question` va `submit_answer` so‘rovlari 403 qaytaradi va javobda yetishmayotgan prerekvizitlar bo‘ladi.
- **V-C5. TY5.** O‘qituvchi boshlangan mavzuga yangi prerekvizit qo‘shadi. Mavzu yopilmaydi, prerekvizit esa trayektoriyada takrorlash tavsiyasi sifatida chiqadi. Boshlanmagan ochiq mavzu esa yopiladi.
- **V-C6. TY6.** KB versiyasi o‘zgargach, talabaning navbatdagi so‘rovida hisoblagichlar qayta hisoblanadi va qaytadan hisoblangan qiymatga teng bo‘ladi.
- **V-C7. Trayektoriya.** Guruhlar tartibi to‘g‘ri, sabab kodlari mavjud. Takrorlash ustuvorligi: t1 (ta’sir 4), keyin t3 (ta’sir 3). Need(t7) = {t4, t6}.
- **V-C8. Test sessiyasi:**
  - har bir javob dvigateldan `source=test_session` bilan o‘tadi;
  - baho alohida saqlanadi va `p_mastery` ga yozilmaydi;
  - testdan o‘tish hech qanday mavzuni ochmaydi.
- **V-C9. Sun’iy yozuvlar yo‘q.** Ssenariy oxirida `AssessmentAttempt` qatorlari soni yuborilgan javoblar soniga aniq teng. `attempt_no` har bir talaba×mavzu uchun 1, 2, 3, … ketma-ketligida, bo‘shliqsiz.
- **V-C10. Yagona shkala.** Barcha endpoint'larda `p_mastery` ∈ [0, 1]. Bitta mavzu uchun daraxt, DAG, dashboard, trayektoriya va testlar ro‘yxati endpoint'lari bir xil qiymat qaytaradi.
- **V-C11. Ruxsatlar.** Anonim foydalanuvchi — 401. Talaba o‘qituvchi endpoint'lariga — 403. `is_staff=False` bo‘lgan o‘qituvchi o‘z endpoint'lariga kira oladi.
- **V-C12. Takroriy javob.** 24 soat ichida aynan bir xil savolga qayta javob `review_repeat` sifatida yoziladi va P(L) ni o‘zgartirmaydi (D25).

### D. Parallel javoblar — 3–4-bosqichlardan keyin
- **V-D1.** Bitta talaba bir mavzuga 10 ta parallel javob yuboradi. Natijada:
  - `attempt_no` qiymatlari takrorlanmaydi va bo‘shliqsiz;
  - yakuniy P(L) javoblarni `attempt_no` tartibida ketma-ket qayta o‘ynash natijasiga teng;
  - xatolar jim yutilmaydi.

### E. Eksport va rozilik — 8-bosqichdan keyin
- **V-E1.** Eksportda email, ism va ichki `user_id` yo‘q, faqat psevdonim bor.
- **V-E2.** Rozilik bermagan talabalar va `legacy`, `seed`, `simulated`, `review_repeat` manbalaridagi javoblar eksportga kirmaydi.
- **V-E3.** pyKT formatidagi fayl pyKT preprocess tomonidan xatosiz o‘qiladi, qatorlar soni metadata bilan mos keladi.
- **V-E4.** `experiments/run_all.py --quick` simulyatsiya ma’lumotida ishlaydi. Natijada parametrlarni tiklash testi o‘tadi va “simulated — dissertatsiya natijasi emas” belgisi bor.

### F. Samaradorlik — 6-bosqichdan keyin
Bu bo‘limdagi chegaralar yumshoq: ular buzilsa ham FAIL emas, ogohlantirish beriladi.
- **V-F1.** `submit_answer` ≤ 12 SQL so‘rov. `trajectory` va graf endpoint'larining so‘rovlar soni mavzular soniga bog‘liq emas, ya’ni N+1 yo‘q.
- **V-F2.** 500 mavzu va 1500 prerekvizitdan iborat sun’iy kurs uchun keshdagi graf, `trajectory` va `submit_answer` ning lokal p95 kechikishi o‘lchanadi va hisobotga yoziladi. Mo‘ljal: < 300 ms.

### G. UI uchidan-uchiga testlar (Playwright) — 7-bosqichdan keyin
- **V-G1.** Talaba sifatida login. O‘quv yo‘lida tugunlarning holati va rangi API qaytargan holatga mos (`data-testid` orqali tekshiriladi).
- **V-G2.** Yopiq tugun bosilganda yetishmayotgan prerekvizitlar API bilan bir xil. “Shu mavzugacha yo‘l” Need(g) ni ajratib ko‘rsatadi.
- **V-G3.** Mashq rejimida to‘g‘ri javoblar ketma-ketligi yuboriladi. Mavzu kutilgan javobdan keyin “o‘zlashtirilgan” bo‘ladi va bog‘liq mavzu ochiladi — UI va API birga tekshiriladi.
- **V-G4.** Bosh sahifadagi “Keyingi qadam” trayektoriya API'sining birinchi elementiga teng.
- **V-G5.** O‘qituvchi prerekvizit muharririda sikl hosil qiluvchi qirra qo‘shmoqchi bo‘ladi. Zanjir grafda ajratiladi va matn bilan ko‘rsatiladi.
- **V-G6.** Profil va xatolar sahifasidagi har bir son API javobida bor. Interfeysda “2PL”, “PROOF”, “70%” matnlari yo‘q. AI tutor menyuda ko‘rinmaydi.
- **V-G7.** Barcha sahifalarda brauzer konsolida xato yo‘q. 1280 px va 768 px kengliklarda skrinshotlar `e2e/screenshots/` ga saqlanadi.

### H. Benchmark — 9-bosqichdan keyin
- **V-H1.** `run_tree_benchmark --quick` ishlaydi. Chiqish CSV'sida barcha amallar, hajmlar, mediana, p95, so‘rovlar soni va o‘zgargan qatorlar bor. Parallel yozishdan keyingi yaxlitlik tekshiruvi ikkala usul uchun ham natija beradi.

---

## 3. Hisobot (`VERIFICATION_REPORT.md`)

1. **Qisqa xulosa:** nechta PASS, FAIL, N/A; eng jiddiy 5 ta muammo.
2. **Jadval:** `ID | Nima tekshirildi | Kutilgan | Amaldagi | Natija | Dalil (test fayli::test nomi)`.
3. **Har bir FAIL uchun:**
   - minimal takrorlash yo‘li (kirish ma’lumoti va buyruq);
   - ehtimoliy sabab (fayl:qator);
   - u qaysi talabni (BB/TM/TY/TR/D) yoki gipotezani buzishi.
4. **Muhit:** seed'lar, versiyalar, buyruqlar, ishga tushirish vaqti.

Ish tugagach, chatda faqat 1-bandni (qisqa xulosani) va fayl yo‘lini ko‘rsat.