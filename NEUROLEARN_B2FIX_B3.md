# NeuroLearn — 2-bosqich tuzatishlari (B2.1) va 3-bosqich

Bu fayl `NEUROLEARN_REMEDIATION.md` va `NEUROLEARN_UI_ADDENDUM.md` ga qo‘shimcha. Unda:
- mustaqil tekshiruv (`VERIFICATION_REPORT.md`, commit `7825f2a`) topgan kamchiliklarni tuzatish vazifasi;
- 3-bosqich uchun oldindan berilgan qarorlar (D30–D38), ular aniqlashtirish savollarini kamaytirish uchun.

Ish tartibi: avval **B2.1**, keyin **3-bosqich**. B2.1 kichik, bir commit'da bajariladi.

---

## 0. Tasdiq

0, 1 va 2-bosqichlar qabul qilinadi. Tekshiruvdagi B guruhining 5 ta tekshiruvi (V-B1, V-B2, V-B3, V-B5, V-B6) o‘tdi, 4-bo‘limdagi barcha etalon qiymatlar mos keldi. Quyidagi qarorlar tasdiqlanadi: Q1-1…Q1-18 va Q2-1…Q2-10.

Bitta tuzatish bilan: **Q1-17** — `NEUROLEARN_VERIFICATION.md`, `NEUROLEARN_UI_ADDENDUM.md` va `NEUROLEARN_B2FIX_B3.md` fayllari repoda commit qilinsin. Ular topshiriqning bir qismi va keyingi sessiyalar ularni o‘qishi kerak.

---

## 1. B2.1 — tekshiruvdagi FAIL'larni tuzatish

Uchala kamchilikning ham ildiz sababi bitta: guard'lar to‘liq emas. Prototipning hech bir kod yo‘li bu yo‘llardan foydalanmaydi, shuning uchun bu “jonli xato” emas. Lekin 2-bosqichning maqsadi aynan “bitta validatsiya qilingan servis” edi, shuning uchun ular yopiladi.

### D30 — Teskari FK manageri guard ostiga olinadi (V-B4, 1 va 3-muammo)

- `Topic` va `TopicPrerequisite` modellarining `Meta` ichiga `base_manager_name = "objects"` qo‘shiladi.
- Sabab: Django teskari FK managerining `add()` va `set()` metodlari `self.model._base_manager` orqali yozadi. `base_manager_name` belgilanmagani uchun u guard'siz oddiy `Manager` bo‘lgan.
- Shart: `objects` manageri o‘qishda hech narsani filtrlamasligi kerak (Django talabi). Guard'lar faqat yozish metodlarida bo‘lgani uchun bu shart bajariladi. Agar `objects` biror joyda `filter(is_archived=False)` qilsa, bu qaror o‘zgaradi: u holda guard'li alohida `all_objects` manageri yaratilib, `base_manager_name` unga qaratiladi.
- Tekshirilishi kerak bo‘lgan yo‘llar (hammasi `KBWriteError` berishi shart):
  - `parent.children.add(node)`;
  - `parent.children.set([...])`;
  - `parent.children.remove(node)`;
  - `Topic._base_manager.filter(...).update(parent_id=...)`;
  - `TopicPrerequisite._base_manager.all().delete()`;
  - `Topic._base_manager.bulk_create([...])`.
- Regressiya xavfi: `base_manager_name` Django'ning ichki amallarida (`refresh_from_db`, FK validatsiyasi, `select_related` fallback) ishlatiladi. Ular faqat o‘qiydi, shuning uchun ta’sir qilmasligi kerak. Shunga qaramay, to‘liq `pytest` ishga tushirilib tasdiqlansin.

### D31 — KB versiyasi yaxlitligi (V-B4, 2-muammo)

Singleton qatorning mavjudligi invariant deb e’lon qilinadi.

- `KnowledgeBaseVersionQuerySet` `delete` va `bulk_create` ni ham bloklaydi.
- `KnowledgeBaseVersion.current()` qator yo‘q bo‘lsa `1` qaytarmaydi, balki `KBError(reason="version_missing")` beradi. Jim fallback olib tashlanadi.
- `_bump_version()` qatorni qayta yaratmaydi: `update(...)` natijasida `rowcount != 1` bo‘lsa, xato beradi. Qator faqat migratsiya orqali yaratiladi.
- Qatorga `instance_token` (UUID, qator yaratilganda bir marta beriladi) qo‘shiladi. Kesh kaliti `kb:snapshot:v<version>` o‘rniga `kb:snapshot:<instance_token>:v<version>` bo‘ladi. Shunda hisoblagich biror sabab bilan orqaga qaytsa ham, eski kesh yozuvi hech qachon qayta ishlatilmaydi.
- `updated_at` har bir versiya oshishida yangilanadi: `update(version=F("version") + 1, updated_at=timezone.now())`. `auto_now=True` `QuerySet.update()` da ishlamaydi (V-B6a).

### D32 — Servis chegarasida xatolarni o‘rash

Tekshiruv hisobotining “Qo‘shimcha kuzatishlar” bo‘limi bo‘yicha:

- `kb.update_weight(<mavjud bo‘lmagan id>, …)` → `KBError(reason="not_found")`, `DoesNotExist` emas.
- `kb.create_node(..., slug=<takrorlanuvchi>)` → `KBError(reason="duplicate_slug")`, `IntegrityError` emas.
- Umumiy qoida: `curriculum/services/kb.py` dan tashqariga faqat `KBError` yoki `KBWriteError` chiqadi. View qatlami ularni 400 `{reason, detail, …}` ga aylantiradi. Bu V-C1 uchun zarur.
- `delete_node` qaytaradigan `size` faqat shu amal arxivlagan tugunlarni sanaydi, oldindan arxivlanganlarni emas.

### D37 — O‘chirilgan daraxt testlari qayta yoziladi

Q2-9 bo‘yicha `test_mptt_tree.py` (25 ta test) o‘chirilgan, lekin uning o‘rniga tree-queries uchun ekvivalent testlar yozilmagan. Daraxt o‘qish amallari hozir faqat bilvosita tekshiriladi.

`curriculum/tests/test_tree.py` yoziladi. U MPTT'ga emas, xatti-harakatga qaratiladi:
- `descendants()`, `ancestors()`, `children` tartibi `(position, id)` bo‘yicha;
- `pos` preorder indeksi va `depth`;
- `Leaves(n)` har bir tur uchun;
- arxivlangan tugunlarning o‘qish natijalaridan chiqib ketishi;
- ko‘chirishdan keyin ajdod va avlodlar to‘plamining to‘g‘riligi;
- chuqurligi 5 dan katta daraxtda bir xil natijalar.

### D38 — Dev muhitini tozalash

Tekshiruv hisobotining 5-muammosi: dev Redis'da `:1:kb:snapshot:v1` kaliti (TTL ~23 soat) turibdi va dev baza versiyasi 1.

- D31 dagi `instance_token` bu muammoni kelajak uchun yopadi.
- Hozirgi kalitni tozalash kerak: `kb:snapshot*` naqshi bo‘yicha o‘chiriladi yoki butun dev keshi tozalanadi. Buyruq hisobotga yozilsin.
- Migratsiya `instance_token` ni mavjud qatorga beradi, shuning uchun eski kalitlar baribir ishlatilmay qoladi.

### B2.1 qabul shartlari

- Mustaqil tekshiruv qayta ishga tushirilganda V-B4 va V-B6 (shu jumladan V-B6a) PASS bo‘ladi. Boshqa B tekshiruvlari regressiyaga uchramaydi.
  Buyruq: `venv/bin/pytest --ds=verification.settings verification/tests -q`.
  Natija hisobotga yoziladi. Tekshiruv kodiga **tegilmaydi** — agar u xato deb hisoblansa, buni hisobotda asoslab yoz, o‘zgartirma.
- To‘liq `pytest` o‘tadi, `check` va `makemigrations --check` toza.
- Commit: `fix(kb): close guard bypasses found by verification (D30–D32, D37, D38)`.

---

## 2. 3-bosqich uchun oldindan berilgan qarorlar

3-bosqichning vazifalari `NEUROLEARN_REMEDIATION.md` ning 5-bo‘limida, formulalar 3.3-bo‘limda, kutilgan qiymatlar 4-bo‘limda. Quyidagilar faqat noaniq joylarni yopadi.

### D33 — `UserAbility` ni ko‘chirish

- `UserAbility` endi `(user, course)` juftligi uchun saqlanadi va `n_answers` maydoniga ega bo‘ladi.
- Mavjud 6 ta `(user, topic)` qatori **ko‘chirilmaydi**, o‘chiriladi. Sabab: ular eski dvigatelning mavzu darajasidagi θ qiymatlari, ularning yangi semantikada ma’nosi yo‘q. Migratsiya o‘chirilgan qatorlar sonini chop etadi.
- Barcha yangi qatorlar `theta=0`, `n_answers=0` dan boshlanadi.
- `Question.n_answers` ham 0 dan boshlanadi. Legacy javoblar bo‘yicha backfill qilinmaydi: ular eski dvigatelga tegishli va `b_q` ni noto‘g‘ri siljitadi.
- θ kursi — javob berilgan mavzuning ildiz tuguni. U ledger'dagi `course` snapshot'i bilan bir xil manbadan olinadi.

### D34 — Dvigatel va versiya

- Yagona dvigatel nomi: `thesis_hybrid`. `engine_version = "thesis_hybrid/1"`.
- Eski dvigatellar (`bayesian`, `hybrid_bkt_irt`, `streak`) va `STUDENT_MODEL_ENGINE` sozlamasi olib tashlanadi (Q0-14). `MASTERY_THRESHOLD` 4-bosqichda olib tashlanadi.
- Klassik BKT alohida dvigatel sifatida saqlanmaydi: u `use_irt=False`, `use_prereq_init=False` bayroqlari bilan hosil bo‘ladi. Buni test tasdiqlaydi.

### D35 — `rebuild_student_states` qamrovi

- 3-bosqichdagi versiya ledger'ni xronologik qayta o‘ynab, `P(L)`, `θ` va `b` ni tiklaydi. Tayyorlik va holatlar 4-bosqichda qo‘shiladi.
- Standart holatda faqat `source ∈ {adaptive, test_session}` qatorlari ishlatiladi. `legacy`, `seed`, `simulated` va `review_repeat` chiqarib tashlanadi. `--include-legacy` bayrog‘i faqat demo uchun.
- Buyruq deterministik: ikki marta ishga tushirilganda natija bir xil bo‘ladi. Buni test tekshiradi.
- `--dry-run` rejimi bor.

### D36 — `calibrate_bkt`

- Standart usul — chegaralangan grid search (`G0 ≤ G_MAX`, `S0 ≤ S_MAX`), u `neuro_model` ichida yoziladi. Shunda qattiq tashqi bog‘liqlik bo‘lmaydi.
- pyBKT ixtiyoriy yo‘l sifatida qoladi (`--method=pybkt`) va faqat `requirements-dev.txt` da bo‘ladi. U o‘rnatilmagan bo‘lsa, buyruq tushunarli xabar bilan grid search'ga qaytadi.
- Kalibrlash faqat o‘qitish to‘plamidagi javoblarda ishlaydi va natijani `TopicModelParams` ga `source="fitted"` bilan yozadi. Ma’lumot yetarli bo‘lmasa (masalan, mavzuda 30 tadan kam javob), parametr `default` holatida qoldiriladi va buning sababi chop etiladi.

### Qo‘shimcha aniqlik

- **Birinchi urinishda prior.** `p_before` = P(L0), u prerekvizitlardan hisoblanadi. Prerekvizitning P(L) qiymati talabada yo‘q bo‘lsa, o‘sha prerekvizitning `P0(w)` qiymati olinadi (spetsifikatsiya 3.3).
- **`p_hat` tartibi.** Bashorat yangilashdan oldingi `θ` va `b` dan hisoblanadi (TM6, 3-qadam). Buni alohida test tekshiradi: `theta_before` bilan hisoblangan `p_hat` yoziladi, `theta_after` bilan emas.
- **Savol tanlash.** `|b_q − θ_s|` eng kichik bo‘lgan savol, θ kurs bo‘yicha olinadi. D25 oynasidagi savollar oxirgi navbatga qo‘yiladi (bu 1-bosqichda allaqachon bor).
- **`review_repeat`.** Bunday javob θ, b, P(L) va `n_answers` ni o‘zgartirmaydi, lekin ledger'ga yoziladi.
- **Chegaralar.** θ `±THETA_CLAMP` bilan cheklanadi. Bu II bobda yo‘q, shuning uchun `docs/THESIS_MAPPING.md` ga “farq” sifatida yoziladi (D6 allaqachon shunday deydi).

### 3-bosqich qabul shartlari

`NEUROLEARN_REMEDIATION.md` dagilarga qo‘shimcha:

- 4-bo‘limdagi barcha sonli qiymatlar test sifatida yozilgan va 1e-3 aniqlikda o‘tadi:
  - BKT ketma-ketligi 0.6927 / 0.9192 / 0.9828 / 0.9965;
  - qiyin savol 0.1272 / 0.0731 / 0.6070 / 0.9246 / 0.2005;
  - oson savol 0.2534 / 0.0269 / 0.6852 / 0.8669 / 0.1461;
  - a=0 holati 0.20 / 0.05 / 0.65 / 0.8892 / 0.1771;
  - Elo 0.2689 / 0.7924 / 1.2076;
  - P(L0) 0.636 va 0.35.
- 2.5-tasdiq xossa testi sifatida yozilgan.
- `neuro_model` da Django importi yo‘q. Buni statik skan tekshiradi (1-bosqichdagi `test_only_the_ledger_creates_attempts` kabi).
- Bosqich oxirida mustaqil tekshiruv qayta ishga tushiriladi: A guruhi (V-A1…V-A3) va V-D1 endi N/A bo‘lmasligi kerak.

---

## 3. Ish tartibi

1. B2.1 ni bajar, tekshiruv suite'ini ishga tushir, commit qil, qisqa hisobot ber va to‘xta.
2. “Davom et” javobidan keyin 3-bosqichni boshla.