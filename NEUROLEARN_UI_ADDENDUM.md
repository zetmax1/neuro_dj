# NeuroLearn: qo‘shimcha spetsifikatsiya (UI va yangi qarorlar D20–D29)

Bu fayl `NEUROLEARN_REMEDIATION.md` ni to‘ldiradi. Unda yangi qarorlar va 7-bosqichdagi har bir sahifa uchun talablar bor. Ba’zi qarorlar 7-bosqichdan oldingi bosqichlarga ham ta’sir qiladi: ular uchun kerakli backend qismi 1-, 2-, 4- va 6-bosqichlarda tayyorlanishi kerak (6-bo‘limdagi jadval).

Agar UI masalasida bu fayl `NEUROLEARN_REMEDIATION.md` bilan zid kelsa, shu fayl ustun. Model, formulalar va algoritmlar bo‘yicha esa `NEUROLEARN_REMEDIATION.md` ning 3–4-bo‘limlari o‘zgarmaydi.

Hozirgi vizual uslub saqlanadi: toza, oq fon, indigo aksent, React Flow'dagi dinamik harakat. Asosiy maqsad yangi dizayn emas. Maqsad — UI'ni haqiqiy model bilan bog‘lash, soxta ma’lumotlarni yo‘q qilish va noto‘g‘ri da’volarni olib tashlash.

---

## 1. Yangi qarorlar

| # | Qaror |
|---|---|
| D20 | **Til.** Asosiy til — o‘zbek (lotin), inglizcha ixtiyoriy. Kutubxona — `react-i18next`, matnlar `src/locales/uz.json` va `en.json` da. Atamalar: o‘zlashtirilgan, o‘rganilmoqda, ochiq, yopiq, takrorlash kerak, prerekvizit, mashq, test. Barcha sarlavha va tugmalarda gapning faqat birinchi harfi katta bo‘ladi. Hozirgi aralash yozuv (“review mistakes”, “Continue Learning”, “mistake review”) bir xil qilinadi. |
| D21 | **Holatlar palitrasi.** Yagona manba — `src/lib/status.ts`:<br>• `mastered` — yashil;<br>• `in_progress` — indigo (hozirgi aksent);<br>• `open` — oq fon va neytral chegara;<br>• `closed` — kulrang uzuq chegara va qulf belgisi;<br>• `review` — sariq.<br>Bu palitra graf tugunlari, kartalar, issiqlik xaritasi va legendada bir xil ishlatiladi. Matn kontrasti WCAG AA ga mos bo‘lsin (hozir yopiq tugunlardagi matn juda och). |
| D22 | **Holat faqat mavzuda.** Holat faqat `kind=topic` turidagi tugunlarga beriladi. Bo‘lim va kursda holat bo‘lmaydi, ular “k / n o‘zlashtirilgan” va progress bar ko‘rsatadi. Kurs yoki bo‘lim hech qachon “In progress” yoki “Locked” deb belgilanmaydi. |
| D23 | **Soxta ma’lumot yo‘q.** Profil, xatolar sahifasi va tutor kontekstidagi barcha qattiq yozilgan qiymatlar olib tashlanadi. UI'dagi har bir son API'dan keladi. `grep` bilan tekshirilsin: sahifalarda mock massivlar qolmasin. |
| D24 | **AI tutor.** `VITE_ENABLE_TUTOR` flag'i standart holatda `false`. Menyuda ko‘rinmaydi, kod saqlanadi. Bu ish keyingi tadqiqot bosqichiga qoldirilgan. |
| D25 | **Xatolar backend'dan keladi.** `localStorage` dagi `mistakeStorage` olib tashlanadi. “Qayta yechish” tugmasi mashq sessiyasini ochadi va iloji bo‘lsa shu mavzuning boshqa savollarini tanlaydi. Agar aynan bir xil savol 24 soat ichida qayta yechilsa, javob `source=review_repeat` bilan yoziladi. Bunday javob BKT yangilanishiga va eksperimentlarga kirmaydi, chunki bir savolni yodlab olish P(L) ni sun’iy oshiradi. |
| D26 | **LLM tushuntirishlari (masalan, Gemini) hozir amalga oshirilmaydi.** Keyingi bosqich uchun dizayn 5-bo‘limda yozilgan. Hozir tushuntirish sifatida faqat o‘qituvchi yozgan `Question.explanation` ko‘rsatiladi. |
| D27 | **Profil haqiqiy ma’lumotda ishlaydi.** U `GET /api/me/summary/` dan keladi. Agar XP, achievements va “study hours” real ma’lumotdan hisoblanmasa, ular olib tashlanadi. Haftalik faollikni javob vaqtlaridan hisoblash mumkin. |
| D28 | **Menyu rolga qarab.**<br>• Talaba: Bosh sahifa, O‘quv yo‘li, Mashq va testlar, Xatolar ustida ishlash.<br>• O‘qituvchi: bularga qo‘shimcha Kurs konstruktori.<br>• Admin: bularga qo‘shimcha Foydalanuvchilar.<br>Rol API'dagi `role` maydonidan olinadi. “Kurslar” sahifasi O‘quv yo‘li bilan birlashtiriladi (2.4-band). |
| D29 | **UI'dagi matnlar haqiqatga mos.** Noto‘g‘ri da’volar olib tashlanadi: “Questions dynamically match your knowledge level” (test sessiyasi aslida stratifikatsiyalangan), “Achieving 70% or higher unlocks downstream topics”, “BKT + IRT PROOF”, “2PL”. Model konstantalari (τ, δ va boshqalar) UI'da qattiq yozilmaydi, ular `GET /api/config/model/` dan olinadi. |

---

## 2. Sahifalar bo‘yicha talablar (7-bosqich)

### 2.1 Bosh sahifa (Dashboard)
- Yuqoridagi 4 ta KPI kartasi almashtiriladi:
  - “O‘zlashtirilgan mavzular: k / n”;
  - “Takrorlash kerak: r”;
  - “Ochiq mavzular: o”;
  - “Oxirgi 7 kundagi javoblar”.

  Streak va “Weekly goal” tezisga aloqador emas, ular olib tashlanadi. P(L) qiymatlarining o‘rtachasi KPI sifatida ishlatilmaydi, chunki u mazmunsiz.
- **“Keyingi qadam” bloki** trayektoriya API'sidan keladi (A–D guruhlari). Birinchi element katta tugma bilan ko‘rsatiladi, qolganlari guruhlar bo‘yicha ro‘yxatda. Har bir elementda sabab matni bo‘ladi: u sabab kodidan i18n orqali olinadi.
- Hozir kurs ildizi (masalan, “Computer Science”) tavsiya sifatida chiqyapti. Bu xato: tavsiya faqat mavzuga beriladi.
- “Continue learning” tugmasi trayektoriyaning birinchi elementiga olib boradi.
- “Bilim xaritasi” kartalarida har bir kurs uchun “k / n o‘zlashtirilgan” va holatlar taqsimotining kichik chizig‘i ko‘rsatiladi.
- **Issiqlik xaritasi (heatmap).** Hozir bo‘sh, legendasi esa ko‘p rangli. Ikki yo‘l bor:
  - D21 palitrasidagi holatlar to‘ri qilib qayta yoziladi: har bir katak — bitta mavzu, bosilganda mavzuga o‘tadi;
  - yoki bilim xaritasini takrorlagani uchun olib tashlanadi.

  Birinchi variantni tanla.

### 2.2 O‘quv yo‘li (Learning Path) — dinamik ko‘rinish saqlanadi
- **Ikki qatlamli ko‘rinish (asosiy yangilik).** Bu dissertatsiyadagi 2.2- va 2.3-rasmlarga mos keladi.
  - React Flow'ning group/sub-flow tugunlari ishlatiladi: kurs va bo‘limlar — ramka (konteyner), mavzular — ularning ichidagi tugunlar.
  - Qirralar — G_L prerekvizitlari. O‘qituvchi bo‘limga qo‘ygan prerekvizit ramkaga kiruvchi bitta qalin qirra sifatida chiziladi.
  - Meros qilib olingan qirralar “ko‘rsatish/yashirish” tugmasi bilan uzuq chiziqda ko‘rsatiladi.
  - Hozirgi “Tree” va “DAG” rejimlari saqlanadi, bunga uchinchi rejim “Ikki qatlam” qo‘shiladi va u standart rejim bo‘ladi.
- **DAG joylashuvi.** Mavzular `lev` bo‘yicha ustunlarga joylashtiriladi (chapdan o‘ngga). Ustun ichidagi tartib `pos` bo‘yicha. Bu joylashuv deterministik bo‘ladi va II bobdagi “bosqich” tushunchasini ko‘rsatadi. Hozirgi dagre joylashuvi ixtiyoriy rejim sifatida qoladi.
- **O‘qiladiganlik.** Hozir “All curriculums” ko‘rinishida tugun matni o‘qib bo‘lmaydigan darajada mayda.
  - Umumiy ko‘rinishda faqat kurs ramkalari chiqadi (yig‘ilgan holatda). Bosilganda kurs ochiladi va unga zoom qilinadi.
  - Har qanday masshtabda tugun yozuvlari kamida 12 px balandlikda ko‘rinsin.
- **Tugunni bosganda yon panel ochiladi:**
  - holat va P(L);
  - yopiq mavzu uchun yetishmayotgan prerekvizitlar ro‘yxati, har biri o‘z P(L) qiymati va havolasi bilan;
  - “Mashq qilish” va “Shu mavzugacha yo‘l” tugmalari.
- **Maqsadli yo‘l.** “Shu mavzugacha yo‘l” bosilganda Need(g) bo‘yicha tugun va qirralar ajratib ko‘rsatiladi, qolganlari xiralashtiriladi. Yo‘l animatsiyali chiziladi — hozirgi dinamik uslubga mos.
- **Legenda.** D21 dagi 5 ta holat va qirra turlari (to‘g‘ridan-to‘g‘ri, meros).
- **Chap panel.** Kurslar ro‘yxatida “Mastery 0%” o‘rniga “k / n o‘zlashtirilgan” ko‘rsatiladi.

### 2.3 Mashq va testlar (Assessments)
- **Ikki rejim aniq ajratiladi:**
  - Adaptiv mashq — `next_question`/`submit_answer` orqali, BKT asosiy shu yerda ishlaydi;
  - Test — stratifikatsiyalangan imtihon, natijasi alohida baho.
- **Kartalar.**
  - Mavzular holati bilan ko‘rsatiladi. Yopiq mavzu kartasi faol emas: unda qulf belgisi va “yetishmaydi: …” yozuvi bo‘ladi, backend esa 403 qaytaradi.
  - Bo‘lim va kurs testlari “Bo‘lim testi (n mavzu)” deb belgilanadi.
  - Hamma kartada bir xil turgan “Medium” nishoni olib tashlanadi. Qiyinlik ko‘rsatilsa, u savollarning o‘rtacha b qiymatidan hisoblanadi.
  - Easy/Medium/Hard filtri ham shu qoidaga bo‘ysunadi yoki olib tashlanadi.
- “Mastery score” o‘rniga holat va P(L) ko‘rsatiladi. Test kartasida esa oxirgi test bahosi alohida “Test bahosi” deb ko‘rsatiladi.

### 2.4 Kurslar
- Bu sahifa O‘quv yo‘lining chap paneli va bosh sahifadagi bilim xaritasini takrorlaydi. Shuning uchun u alohida menyu bandi sifatida olib tashlanadi. Kurs katalogi O‘quv yo‘li sahifasining kirish ko‘rinishiga aylanadi (yig‘ilgan kurs ramkalari).
- “TOPIC COURSE · LOCKED/UNLOCKED” yozuvlari olib tashlanadi (D22).

### 2.5 Mavzu sahifasi (`/topic/:id`)
- **Joylashuv.** Hozirgi sahifa tor ustunda va mayda ko‘rinadi. Kontent kengligi boshqa sahifalar bilan bir xil bo‘lsin.
- **Diagnostika paneli.** “How is this calculated? BKT + IRT PROOF” o‘rniga “Qanday hisoblandi” sarlavhasi:
  - P(L) grafigida τ chizig‘i (`config/model` dan olinadi) bo‘ladi va har bir urinish nuqta bilan belgilanadi: to‘g‘ri — to‘ldirilgan, xato — bo‘sh;
  - urinishlar jadvali: savol, natija, p̂, P(G), P(S), P(L) oldin → keyin;
  - θ kurs bo‘yicha ko‘rsatiladi, “2PL” yozuvi “Rasch (a = 1)” ga almashtiriladi;
  - holat va yetishmayotgan prerekvizitlar;
  - “Mashq qilish” tugmasi.

  Bu panel himoyada modelning ishlashini ko‘rsatish uchun asosiy vosita bo‘ladi.
- “Diagnostic Assessment” kartasidagi matn D29 bo‘yicha tuzatiladi: “Mavzu P(L) ≥ τ bo‘lganda o‘zlashtirilgan hisoblanadi. Bog‘liq mavzular shundan keyin ochiladi.”

### 2.6 Kurs konstruktori (Curriculum Builder)
- **Tuzilma.**
  - Chapda daraxt (outline), o‘ngda tanlangan tugun muharriri.
  - Hozirgi 4 qadamli wizard faqat yangi kurs yaratish uchun qoladi.
  - Muharrirda tugun turi (`section`/`topic`) va aka-uka tugunlar orasidagi tartib (yuqoriga/pastga) o‘zgartiriladi.
- **Yangi “Prerekvizitlar” qadami yoki sahifasi (dissertatsiyaning markaziy qismi; hozir UI'da umuman yo‘q):**
  - React Flow muharriri: `onConnect` qirra qo‘shadi, qirrani o‘chirish va ω vaznini tahrirlash mumkin;
  - meros qirralari uzuq chiziqda, faqat o‘qish uchun;
  - 400 javobida sikl zanjiri grafda qizil rangda ajratiladi va matn bilan tushuntiriladi;
  - Y2 xatosi ham tushuntiriladi;
  - ortiqcha qirralar va κ ogohlantirishlari alohida panelda ko‘rsatiladi.
- **Savollar.** Savol faqat `topic` turidagi tugunga biriktiriladi: UI boshqa tugunni tanlashga yo‘l qo‘ymaydi. Import xatolari qatorma-qator ko‘rsatiladi.

### 2.7 Foydalanuvchilar
- “Unnamed User” o‘rniga email'ning @ belgisigacha bo‘lgan qismi chiqadi.
- Rol bo‘yicha filtr bo‘ladi va har bir foydalanuvchiga rol berish mumkin bo‘ladi.
- Ustunlar va filtrlar:
  - tadqiqot roziligi (`research_consent`) ustuni — 8-bosqichdan keyin;
  - simulyatsiya qilingan foydalanuvchilar nishoni va ularni yashirish filtri;
  - foydalanuvchini faolsizlantirish.

### 2.8 Profil
- D27 bo‘yicha haqiqiy ma’lumotlar:
  - har bir kurs bo‘yicha k / n o‘zlashtirilgan;
  - takrorlash kerak bo‘lgan mavzular soni;
  - urinishlar soni;
  - kurs bo‘yicha θ, qisqa tushuntirish bilan;
  - so‘nggi faollik;
  - haftalik faollik (javob vaqtlaridan).
- Rozilikni boshqarish (8-bosqich), hisobni o‘chirish va parolni almashtirish.
- Joriy foydalanuvchining ismi ko‘rsatiladi (hozir “Learner” deb turibdi).

### 2.9 Quiz
- **Test rejimi.** Hozirgi dizayn saqlanadi. Natija ekranida quyidagilar ko‘rsatiladi:
  - test bahosi va o‘tish bali;
  - har bir mavzu bo‘yicha P(L) oldin → keyin;
  - holati o‘zgargan mavzular, masalan “Ikkilik qidiruv daraxti ochildi”.
- **Mashq rejimi** (yangi, `useAdaptiveQuiz`):
  - bir vaqtda bitta savol;
  - javobdan keyin darhol to‘g‘ri yoki xato ekanligi va `Question.explanation` ko‘rsatiladi;
  - holat o‘zgarsa, xabar (toast) chiqadi;
  - savolning qiyinlik nishoni ko‘rsatilmaydi.
- **Klaviatura.** A–D tugmalari variant tanlaydi, Enter tasdiqlaydi.

### 2.10 Xatolar ustida ishlash
- **Ma’lumot manbai.** Hozirgi ma’lumot soxta: “Loops Basics – mini quiz”, For/While Loops kabi mavzular backend'da yo‘q. Endi u `GET /api/learning/mistakes/` dan keladi (D25).
- **Ko‘rinish:**
  - mavzular bo‘yicha guruhlanadi;
  - har bir xato uchun: savol, talabaning javobi, to‘g‘ri javob, o‘qituvchi tushuntirishi, sana;
  - keyinroq to‘g‘ri yechilganmi — shu belgi bilan.
- “Qayta yechish” — D25 bo‘yicha. “Tozalash” tugmasi olib tashlanadi: backend logi o‘chirilmaydi, faqat “ko‘rib chiqilgan” deb belgilash mumkin.

### 2.11 Umumiy talablar
- Har bir ma’lumot ko‘rinishida loading, bo‘sh va xato holatlari bo‘lsin.
- Konsolda xato bo‘lmasin.
- Responsive bo‘lsin: 1280 px va 768 px kengliklarda tekshiriladi.
- Marshrutlar `React.lazy` bilan code-splitting qilinsin.
- Asosiy elementlarga `data-testid` qo‘shilsin (graf tugunlari, holat nishonlari, trayektoriya elementlari, prerekvizit muharriri, quiz variantlari). Bu mustaqil tekshiruv uchun kerak.
- 7-bosqich oxirida har bir sahifaning skrinshoti (1440 px, o‘zbek tilida) `docs/ui/` ga saqlansin. Bu skrinshotlar dissertatsiyaning 3.1-bo‘limida ishlatiladi.

---

## 3. Qabul shartlari (7-bosqich, `NEUROLEARN_REMEDIATION.md` dagilarga qo‘shimcha)
- `grep` bilan tekshirilganda sahifalarda mock ma’lumot massivlari qolmagan (D23).
- Bitta mavzu O‘quv yo‘li, bosh sahifa, mashq va testlar sahifasi hamda mavzu sahifasida bir xil holat va bir xil P(L) ni ko‘rsatadi. Buni vitest yoki Playwright testi tekshiradi.
- Interfeysda “2PL”, “PROOF”, “70%” va “dynamically match” matnlari qolmagan.

---

## 4. Backend uchun nima kerak va qaysi bosqichda

| Bosqich | Qo‘shimcha |
|---|---|
| 1 | `source` enum'iga `review_repeat` qiymati |
| 2 | Graf API qaytaradi:<br>• daraxt: `kind`, `pos`, `lev`;<br>• G_L qirralari: `inherited` belgisi va qirrani hosil qilgan E_P munosabatining id'si;<br>• o‘qituvchi kiritgan E_P qirralari alohida;<br>• ogohlantirishlar. |
| 4 | Mavzu holatlari va P(L); bo‘lim va kurslar uchun `mastered/total`; yopiq mavzuning yetishmayotgan prerekvizitlari |
| 6 | Endpoint'lar:<br>• `GET /api/learning/mistakes/`;<br>• `GET /api/me/summary/`;<br>• `GET /api/config/model/`;<br>• `GET /api/learning/topics/<id>/history/` — p̂, P(G), P(S), p_before, p_after, natija, vaqt. |
| 8 | Rozilik endpoint'i (`PATCH /api/me/consent/`) |

---

## 5. LLM tushuntirishlari (masalan, Gemini) — keyingi bosqich uchun dizayn, hozir amalga oshirilmaydi

Bu ish 8–10-bosqichlardan keyin, alohida bosqich sifatida qilinadi va flag ortida turadi. Tamoyillar:

1. **Faqat o‘qituvchi tomonida generatsiya qilinadi.** LLM har bir savol uchun bitta tushuntirish qoralamasini yozadi. Talabaning javobi va shaxsiy ma’lumotlari yuborilmaydi.
2. **O‘qituvchi tasdiqlaydi.** Qoralama `Question.explanation_draft` maydoniga yoziladi va manba belgisi (`llm`/`human`) qo‘yiladi. O‘qituvchi ko‘rib, tahrirlab, `explanation` ga tasdiqlaydi. Talabaga faqat tasdiqlangan matn ko‘rsatiladi.
3. **Natija keshlanadi.** Har bir savol uchun so‘rov bir marta yuboriladi. API kaliti env'dan olinadi. Rate limit va xarajat logi yuritiladi.
4. **Eksperimentga ta’sir nazorat qilinadi.** H1–H3 uchun ma’lumot yig‘ilayotganda tushuntirishlar manbai barcha talabalar uchun bir xil bo‘lishi kerak. Yig‘ish davrining o‘rtasida yangi tushuntirishlar yoqilmaydi, aks holda bu natijaga qo‘shimcha o‘zgaruvchi qo‘shadi.