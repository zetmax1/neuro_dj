# Demo ma’lumotlar (`seed_demo`)

> **Sintetik ma’lumot — tadqiqot natijasi emas.** Bu yerdagi talabalar,
> ularning javoblari va o‘zlashtirish ko‘rsatkichlari simulyator tomonidan
> yaratilgan. Ular dissertatsiyadagi biror natija, jadval yoki xulosaga
> asos bo‘la olmaydi va tadqiqot eksportiga tushmaydi (D13, D44).

`manage.py seed_demo` platformani ko‘rsatish va qo‘lda sinash uchun o‘zbek
tilidagi (lotin) ikki kurs, ikki o‘qituvchi va 30 talabani yaratadi.
Talabalarning olti haftalik javoblari haqiqiy javob yo‘lidan —
`process_submission` (`POST /api/assessments/submit_answer/` ortidagi servis)
orqali o‘tadi: P(L), θ, b_q, tayyorlik (readiness) va trayektoriyani tizimning
o‘zi hisoblaydi, seed ularni jadvalga to‘g‘ridan-to‘g‘ri yozmaydi.

Kod: `assessments/management/commands/seed_demo.py`,
`assessments/demo_seed/` (`content.py` — kurslar va savollar, `people.py` —
ismlar va profillar, `simulator.py` — yashirin talaba, `store.py` — belgilar,
qurish, o‘chirish, hisobot). Testlar: `assessments/tests/test_seed_demo.py`.

## 1. Ishga tushirish

Postgres compose konteynerida (127.0.0.1:5433), `scripts/dj5433.sh` orqali —
u DSN’ni konteynerning o‘z muhitidan oladi va `config/.env` ni o‘qimaydi:

```bash
docker start neurolearn-postgres-1 neurolearn-redis-1   # konteynerlar to‘xtagan bo‘lsa
scripts/dj5433.sh venv/bin/python manage.py seed_demo                 # seed 20261021
scripts/dj5433.sh venv/bin/python manage.py seed_demo --password 'P'  # o‘z parolingiz bilan
```

| Parametr | Ma’nosi |
|---|---|
| `--seed N` | Ismlar, profillar va javoblarning seed’i (standart `20261021`) |
| `--password P` | Barcha demo akkauntlarning paroli |
| `--reset` | Demo ma’lumotlarni o‘chiradi va qaytadan yaratadi |
| `--delete` | Demo ma’lumotlarni faqat o‘chiradi |
| `--scale F` | Talaba va sessiyalar ulushi, (0, 1] — testlar uchun |

Buyruq taxminan bir daqiqa ishlaydi va oxirida profillar va talabalar
bo‘yicha jadvalni chiqaradi (3-bo‘lim).

**Parol.** Repozitoriyda parol saqlanmaydi. `--password` berilmasa, buyruq
tasodifiy parol yaratadi va uni **faqat akkaunt yaratgan ishga tushirishda
bir marta** chiqaradi; u faylga yoki logga yozilmaydi. Barcha 32 demo
akkaunt bitta parolga ega. Keyingi ishga tushirishlar (`--reset` siz)
parolni o‘zgartirmaydi; `--password` bilan esa yangisini o‘rnatadi.

**Qayta ishga tushirish dublikat yaratmaydi.** Kurslar slug bo‘yicha, savollar
matn bo‘yicha, akkauntlar email bo‘yicha qayta ishlatiladi; demo talabalar
mavjud bo‘lsa, simulyatsiya qayta ishlamaydi (“Demo learners already exist”).
Bir xil seed bilan `--reset` aynan bir xil javoblarni, holatlarni va
jadvalni beradi (vaqtlar o‘sha kunga nisbatan; `test_small_seed_is_deterministic`).

## 2. O‘chirish va nima demo hisoblanadi

```bash
scripts/dj5433.sh venv/bin/python manage.py seed_demo --delete   # faqat o‘chirish
scripts/dj5433.sh venv/bin/python manage.py seed_demo --reset    # o‘chirib, qayta yaratish
```

Migratsiyasiz belgilar:

- **Akkaunt** demo hisoblanadi, agar uchala shart bajarilsa: `Demo (seed_demo)`
  auth guruhida, `is_simulated = True` va email `@example.com` da. Faqat domen
  yetarli emas — bazada boshqa `@example.com` akkauntlar ham bor.
- **Tugun** (kurs, bo‘lim, mavzu) demo hisoblanadi, agar u
  `demo--python-asoslari` yoki `demo--algoritmlar-asoslari` ildizi ostida
  bo‘lsa. Barcha demo slug’lar `demo--` bilan boshlanadi; `slugify` ketma-ket
  chiziqchalarni birlashtiradi, shuning uchun nomdan hosil bo‘lgan slug bunday
  boshlana olmaydi.

O‘chirishdan oldin buyruq demo kurslar ichida demo bo‘lmagan narsani
qidiradi: boshqa akkauntlarning javoblari yoki test sessiyalari, seed
yaratmagan tugunlar yoki savollar, biriktirilgan resurslar. Shunday narsa
bo‘lsa, **hech narsa o‘chirilmaydi** va buyruq nima topganini aytadi. Aks
holda demo akkauntlar (javoblari, holatlari, θ va tarix bilan) va ikki kurs
`kb.delete_node` orqali (prerekvizitlar, savollar va variantlar bilan)
o‘chiriladi. Boshqa akkauntlardan faqat ularning demo mavzular uchun
**boshlanmagan** `StudentTopicState` qatorlari ketadi — readiness servisi
bunday qatorni har bir mavzu uchun o‘zi yaratadi va kerak bo‘lganda qayta
yaratadi. `Student` va `Instructor` guruhlari o‘chirilmaydi.

Eslatma: `simulate_bkt_data --clear` barcha `is_simulated` akkauntlarni,
jumladan demo akkauntlarni ham o‘chiradi (kurslar qoladi). Shundan keyin
`seed_demo --reset` ni ishga tushiring.

## 3. Nima yaratiladi

### Kurslar

| Kurs | O‘qituvchi | Bo‘limlar | Mavzular | Savollar |
|---|---|---|---|---|
| Python dasturlash asoslari | `dilnoza.rahimova@example.com` (Dilnoza Rahimova) | 5 | 12 | 88 |
| Algoritmlar asoslari | `bekzod.tursunov@example.com` (Bekzod Tursunov) | 4 | 10 | 71 |

- Har mavzuda 7–8 savol, har birida 4 variant va bitta to‘g‘ri javob,
  izoh (`explanation`) bilan; qiyinlik uch darajada (oson / o‘rta / qiyin),
  b_q ning boshlang‘ich qiymati −1, 0, +1 atrofida, so‘ng uni Elo surib
  boradi. Matnlar oddiy matn: frontend markdown’ni ko‘rsatmaydi.
- Har bir tugun o‘z kursining o‘qituvchisiga tegishli (`Topic.instructor`),
  shuning uchun o‘qituvchi panelida har o‘qituvchi faqat o‘z kursini ko‘radi.
  Mavzu testi 5 savoldan iborat (`test_question_count = 5`).
- Hamma narsa `curriculum.services.kb` orqali yaratiladi (`ensure_node`,
  `ensure_prerequisite` → `add_prerequisite`): Y1–Y4 va sikl tekshiruvi
  (Algoritm 2.1) har qirrada ishlaydi. Demo kurslar ildizlar orasida
  `position = 0` da turadi, shuning uchun dasturiy tartibda mavjud kurslardan
  oldin keladi; mavjud tugunlarning o‘rni o‘zgarmaydi.

### Prerekvizitlar grafi

29 qirra: Python ichida 16, Algoritmlar ichida 10, kurslararo 3
(`Rekursiya → Birlashtirib saralash`, `Rekursiya → Tez saralash`,
`Sikllar → Chiziqli qidiruv`). 17 qirra bo‘limlararo. Eng uzun zanjir —
5 mavzu (4 qirra), masalan
`O‘zgaruvchilar → Operatorlar → Shartlar → Istisnolar → Fayllar` va
`O‘zgaruvchilar → Operatorlar → Funksiyalar → Rekursiya → Birlashtirib saralash`.
Graf atsiklik (`test_prerequisite_graph_is_acyclic_and_guarded`), teskari
qirra qo‘shishga urinish `KBError("cycle")` bilan rad etiladi.

O‘qituvchi panelidagi KB ogohlantirishlarida 2 ta **ortiqcha qirra** ko‘rinadi:
`O‘zgaruvchilar → Satrlar` (`O‘zgaruvchilar → Kiritish va chiqarish → Satrlar`
orqali kelib chiqadi) va `Murakkablik → Ikkilik qidiruv`
(`Murakkablik → Chiziqli qidiruv → Ikkilik qidiruv` orqali). Ular xato emas,
GR3 ogohlantirishining namunasi sifatida qoldirilgan; κ = 0.

### Akkauntlar

2 o‘qituvchi (`Instructor` guruhi) va 30 talaba (`Student` guruhi). Hammasi
`is_simulated`, **tadqiqot roziligi o‘chiq** (`research_consent = False`),
email ASCII (`o‘ → o`, `g‘ → g`) va `@example.com` da; ism-familiyalar
takrorlanmaydi va jinsga mos (`Karimov` / `Karimova`). Yozilish:
Python — 20 talaba, Algoritmlar — 18, ikkalasida — 8.

## 4. Yashirin profillar va simulyator

Profil bazaga yozilmaydi — u faqat simulyator qanday javob berishini
belgilaydi. Har talabaning yashirin qobiliyati θ va har mavzu bo‘yicha
“biladi / bilmaydi” holati bor. Bilsa, to‘g‘ri javob ehtimoli 1 − slip;
bilmasa — guess; ikkalasi θ va savolning (kontentdagi) qiyinligiga bog‘liq.
Har javobdan keyin bilinmagan mavzu o‘rganish ehtimoli bilan o‘rganiladi
(prerekviziti bilinmasa, ikki marta sekinroq).

| Profil | Soni | Xulq |
|---|---|---|
| A’lochi | 4 | Yuqori θ, tez o‘rganadi, tavsiyaga 90 % amal qiladi; kursni odatda tugatadi |
| O‘rtacha | 10 | O‘rtacha θ va tezlik; tavsiyaga 75 % amal qiladi, qolgan holda ochiq mavzulardan birini tanlaydi |
| Sust | 5 | Past θ, sekin o‘rganadi, ko‘p xato qiladi; olti haftada bir necha mavzu |
| Bo‘shliqli | 4 | Tavsiyaga 20 % amal qiladi; ochiq mavzulardan eng chuqurini tanlab, asoslarni o‘tkazib yuboradi; vaqti-vaqti bilan yopiq ilg‘or mavzuga urinadi — readiness uni rad etadi |
| To‘xtab qolgan | 3 | Faqat dastlabki ikki haftada faol, keyin to‘xtaydi |
| Yangi | 2 | Ro‘yxatdan o‘tgan, birorta javob yo‘q (sovuq start) |
| Unutgan | 2 | 0–16 kunlarda o‘rganadi, 17–27 kunlarda tanaffus; qaytgach eski mavzularni takrorlaydi va ularni unutgani uchun xato qiladi: P(L) avval τ dan pastga tushadi, lekin M = 1 qoladi (gisterezis), so‘ng τ − δ dan pastda `review` ga o‘tadi; oxirgi sessiyasini ham eski mavzularni takrorlash bilan yakunlaydi |

Mavzu tanlash: talaba ko‘pincha tizim tavsiyasini — kurs trayektoriyasining
boshini (Algoritm 2.5: review → in_progress → open) oladi, profiliga qarab
chetga chiqadi. Kursida qiladigan ish qolmasa, tizimning “maqsadga yo‘l”ini
(Need_s(g), `path-to`) kuzatadi — shu tariqa faqat Algoritmlar kursidagi
talaba kurslararo prerekvizit uchun Python asoslariga o‘tishi mumkin.
Savolni har doim tizim tanlaydi (`get_next_question`).

Vaqt: javoblar oxirgi 6 hafta (42 kun, kechagi kun bilan tugaydi) bo‘ylab,
Toshkent vaqti bilan 09:00–21:00 oralig‘ida boshlanadigan sessiyalarga
yoyilgan, javoblar orasi 25–110 soniya. Ledger vaqtni faqat `seed` va
`simulated` qatorlar uchun qabul qiladi (D10), mahsulot kodi o‘zgarmagan.
Barcha talabalar bitta umumiy vaqt navbatida harakat qiladi, shuning uchun
b_q ning Elo yangilanishlari javoblar berilgan tartibda bo‘ladi va
`attempt_no` `answered_at` bilan bir xil tartibda o‘sadi. Simulyatsiya
davomida `django.utils.timezone.now` simulyatsiya vaqtini qaytaradi
(`SimClock.installed()`, faqat seed jarayoni ichida): savol tanlashdagi
“oxirgi 24 soatda javob berilgan” qoidasi va `updated_at` maydonlari javob
vaqtiga mos keladi.

## 5. Natija (seed 20261021)

Jami **3 113 javob** (2026-09-09 … 2026-10-20 UTC; sana ishga tushirilgan kunga
nisbatan siljiydi), barchasi `source = seed`. Bo‘shliqli talabalarning
40 urinishi yopiq mavzuga qilingan va readiness tomonidan rad etilgan (javob
yozilmagan). 30 talabadan 24 tasida (o‘zlashtirilgan mavzular to‘plami,
keyingi tavsiya) jufti har xil.

“P(L) ≥ τ” — p_mastery ≥ 0,95 bo‘lgan mavzular; “Tayyor” — barcha
prerekvizitlari o‘zlashtirilgan (M = 1), o‘zi esa o‘zlashtirilmagan mavzular;
“Keyingi tavsiya” — har kurs trayektoriyasining boshi, “—” — kursda qiladigan
ish qolmagan.

| Profil | Talaba | Javob (o‘rt.) | P(L) ≥ τ (o‘rt.) | Review (o‘rt.) | Tayyor (o‘rt.) | Keyingi tavsiya (ko‘p uchragan) |
|---|---|---|---|---|---|---|
| A’lochi | 4 | 101.5 | 17.0 | 0.0 | 0.5 | — ×4; Stek va navbat ×1 |
| O‘rtacha | 10 | 133.2 | 13.0 | 0.3 | 1.1 | — ×7; Lug‘atlar va to‘plamlar ×1 |
| Sust | 5 | 123.8 | 8.0 | 0.0 | 1.4 | Satrlar bilan ishlash ×2; Chiziqli qidiruv ×1 |
| Bo‘shliqli | 4 | 86.5 | 13.5 | 0.0 | 1.0 | Tez saralash (quick sort) ×2; Satrlar bilan ishlash ×1 |
| To‘xtab qolgan | 3 | 49.0 | 5.3 | 0.0 | 1.3 | Kiritish va chiqarish ×1; Chiziqli qidiruv ×1 |
| Yangi | 2 | 0.0 | 0.0 | 0.0 | 1.0 | Algoritm murakkabligi (Big-O) ×1; O‘zgaruvchilar va ma’lumot turlari ×1 |
| Unutgan | 2 | 131.5 | 11.0 | 1.0 | 3.5 | Sikllar (for va while) ×1; Joylashtirib saralash ×1 |

### Akkauntlar (parolsiz)

O‘qituvchilar: `dilnoza.rahimova@example.com` (Python dasturlash asoslari),
`bekzod.tursunov@example.com` (Algoritmlar asoslari).

| Email | Ism-familiya | Profil | Kurs(lar) | Javob | P(L) ≥ τ | Review | Keyingi tavsiya |
|---|---|---|---|---|---|---|---|
| `malika.qodirova@example.com` | Malika Qodirova | A’lochi | Python + Algoritmlar | 115 | 19 | 0 | Python: — · Algoritmlar: Stek va navbat |
| `sevara.polatova@example.com` | Sevara Po‘latova | A’lochi | Python | 76 | 12 | 0 | Python: — |
| `shahnoza.normatova@example.com` | Shahnoza Normatova | A’lochi | Python + Algoritmlar | 120 | 21 | 0 | Python: — · Algoritmlar: Grafni aylanib chiqish (BFS va DFS) |
| `temur.zokirov@example.com` | Temur Zokirov | A’lochi | Algoritmlar | 95 | 16 | 0 | Algoritmlar: — |
| `elyor.hakimov@example.com` | Elyor Hakimov | O‘rtacha | Python + Algoritmlar | 144 | 11 | 0 | Python: Lug‘atlar va to‘plamlar · Algoritmlar: Stek va navbat |
| `feruza.mahmudova@example.com` | Feruza Mahmudova | O‘rtacha | Python | 134 | 12 | 0 | Python: — |
| `gulnora.boboyeva@example.com` | Gulnora Boboyeva | O‘rtacha | Python | 104 | 12 | 0 | Python: — |
| `islom.usmonov@example.com` | Islom Usmonov | O‘rtacha | Algoritmlar | 139 | 16 | 0 | Algoritmlar: — |
| `madina.valiyeva@example.com` | Madina Valiyeva | O‘rtacha | Python | 130 | 12 | 0 | Python: — |
| `munisa.sharipova@example.com` | Munisa Sharipova | O‘rtacha | Python | 78 | 8 | 1 | Python: Satrlar bilan ishlash |
| `oydin.rasulova@example.com` | Oydin Rasulova | O‘rtacha | Algoritmlar | 155 | 11 | 0 | Algoritmlar: Tez saralash (quick sort) |
| `ozoda.hamidova@example.com` | Ozoda Hamidova | O‘rtacha | Algoritmlar | 152 | 9 | 1 | Algoritmlar: Grafni aylanib chiqish (BFS va DFS) |
| `shohruh.islomov@example.com` | Shohruh Islomov | O‘rtacha | Python + Algoritmlar | 163 | 22 | 0 | Python: — · Algoritmlar: — |
| `sitora.abdullayeva@example.com` | Sitora Abdullayeva | O‘rtacha | Python + Algoritmlar | 133 | 17 | 1 | Python: Kiritish va chiqarish · Algoritmlar: — |
| `charos.mirzayeva@example.com` | Charos Mirzayeva | Sust | Algoritmlar | 89 | 6 | 0 | Algoritmlar: Chiziqli qidiruv |
| `diyorbek.shukurov@example.com` | Diyorbek Shukurov | Sust | Algoritmlar | 161 | 11 | 0 | Algoritmlar: Birlashtirib saralash (merge sort) |
| `gulchehra.yoldosheva@example.com` | Gulchehra Yo‘ldosheva | Sust | Python | 139 | 6 | 0 | Python: Satrlar bilan ishlash |
| `javohir.xudoyberdiyev@example.com` | Javohir Xudoyberdiyev | Sust | Python + Algoritmlar | 112 | 9 | 0 | Python: Funksiyalarni aniqlash va chaqirish · Algoritmlar: Stek va navbat |
| `kamola.sultonova@example.com` | Kamola Sultonova | Sust | Python | 118 | 8 | 0 | Python: Satrlar bilan ishlash |
| `asilbek.sobirov@example.com` | Asilbek Sobirov | Bo‘shliqli | Algoritmlar | 87 | 15 | 0 | Algoritmlar: Tez saralash (quick sort) |
| `farrux.nazarov@example.com` | Farrux Nazarov | Bo‘shliqli | Python + Algoritmlar | 92 | 17 | 0 | Python: Satrlar bilan ishlash · Algoritmlar: Tez saralash (quick sort) |
| `laylo.ergasheva@example.com` | Laylo Ergasheva | Bo‘shliqli | Python | 82 | 10 | 0 | Python: Istisnolarni qayta ishlash |
| `nilufar.xolmatova@example.com` | Nilufar Xolmatova | Bo‘shliqli | Python | 85 | 12 | 0 | Python: — |
| `gayrat.gulomov@example.com` | G‘ayrat G‘ulomov | To‘xtab qolgan | Python | 51 | 3 | 0 | Python: Kiritish va chiqarish |
| `jamshid.qosimov@example.com` | Jamshid Qosimov | To‘xtab qolgan | Algoritmlar | 53 | 8 | 0 | Algoritmlar: Chiziqli qidiruv |
| `shahzoda.umarova@example.com` | Shahzoda Umarova | To‘xtab qolgan | Algoritmlar | 43 | 5 | 0 | Algoritmlar: Grafni aylanib chiqish (BFS va DFS) |
| `ibrohim.yusupov@example.com` | Ibrohim Yusupov | Yangi | Algoritmlar | 0 | 0 | 0 | Algoritmlar: Algoritm murakkabligi (Big-O) |
| `sabina.aliyeva@example.com` | Sabina Aliyeva | Yangi | Python | 0 | 0 | 0 | Python: O‘zgaruvchilar va ma’lumot turlari |
| `doniyor.toshmatov@example.com` | Doniyor Toshmatov | Unutgan | Python + Algoritmlar | 131 | 11 | 1 | Python: Sikllar (for va while) · Algoritmlar: Joylashtirib saralash |
| `mohinur.jorayeva@example.com` | Mohinur Jo‘rayeva | Unutgan | Python | 132 | 11 | 1 | Python: Funksiyalarni aniqlash va chaqirish |

“Kurs(lar)” — talaba yozilgan kurs. Faqat Algoritmlar’ga yozilgan talaba
kurslararo prerekvizitlar uchun Python asoslarini ham o‘tishi mumkin, shuning
uchun uning “P(L) ≥ τ” soni 10 dan oshishi mumkin.

## 6. Cheklovlar va kuzatuvlar

- **Kursga yozilish va talabalar guruhi modeli yo‘q.** Platformada har bir
  kurs har bir talabaga ko‘rinadi; “yozilish” faqat simulyatorda — talaba
  qaysi kursda ishlashini belgilaydi. Shuning uchun dashboard’dagi umumiy
  trayektoriyada boshqa kurs mavzulari ham “ochiq” bo‘lib turadi. Guruh
  yaratilmadi (auth guruhlari — bu rollar).
- **Test sessiyalari simulyatsiya qilinmagan:** test javoblarini orqaga
  sanalab bo‘lmaydi (D10), barcha javoblar adaptiv yo‘ldan.
- `seed` manbali javoblarda D25 (24 soat ichida takrorlangan savol →
  `review_repeat`) qo‘llanmaydi — bu manba uchun tizimning o‘z qoidasi;
  simulyatsiya qilingan har javob kuzatuv sifatida hisoblanadi.
- **Savollari tugagan mavzu.** Tizim bir marta to‘g‘ri javob berilgan savolni
  qayta bermaydi (`assessments/services/question_selection.py`,
  `get_next_question`). Mavzuning barcha savollariga to‘g‘ri javob berilib,
  P(L) hali τ dan past bo‘lsa (yoki mavzu `review` ga tushsa), u mavzuni
  mashq qilib bo‘lmaydi — sahifa “Bu mavzuda savollar qolmadi” deydi. Bu
  seed’da 5 ta boshlangan mavzuda yuz bergan; 4 talabada trayektoriya boshi
  shunday mavzu (`munisa.sharipova` — Satrlar, `sitora.abdullayeva` —
  Kiritish va chiqarish, `ozoda.hamidova` — BFS va DFS, `elyor.hakimov` —
  Stek va navbat). Bu mahsulotning xatti-harakati; seed uni o‘zgartirmaydi.
- Mavzu va savollarning `created_at` i — seed ishga tushgan vaqt (KB versiya
  qatoriga ta’sir qilmaslik uchun ular soat bilan siljitilmaydi).
