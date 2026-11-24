# NEUROLEARN_YAKUNIY.md — himoya oldidan qolgan ishlar

Bu fayl Claude Code uchun topshiriq. U ikki repozitoriyga tegishli:
backend `zetmax1/neuro_dj` va frontend `zetmax1/neuro`, ikkalasida `thesis-model` branchi.
Boshlang‘ich holat: backend `thesis-model` = `6692a99`, oxirgi qaror raqami D71.

Bosqichlarni tartib bilan bajar. Har bir bosqich oxirida TO‘XTA va hisobot ber;
keyingi bosqichga faqat men “davom et” deganimdan keyin o‘t.

---

## 0. Buzilmaydigan qoidalar

1. **Muzlatilgan holatni belgilab qo‘y.** Hech narsa o‘zgartirmasdan oldin ikkala
   repozitoriyda hozirgi `thesis-model` uchiga annotatsiyali teg qo‘y:
   `thesis-v1-frozen`. Tegni push qil. Dissertatsiyadagi barcha natijalar shu tegdan
   qayta hosil bo‘lishi kerak.
2. **Git tarixini qayta yozma.** `filter-repo`, BFG, `rebase`, `push --force` ishlatilmaydi.
   Natija fayllaridagi (`metrics.json`, `env.txt`) commit hash’lar tarixga bog‘langan;
   tarix o‘zgarsa, ular yaroqsiz bo‘ladi.
3. **Mavjud natija papkalariga tegma.** `experiments/results/` va benchmark natijalaridagi
   bironta fayl o‘zgartirilmaydi va o‘chirilmaydi. Yangi natija faqat yangi papkaga yoziladi.
4. **Avval qaror, keyin kod, keyin natija.** Har bir yangi tahlil uchun avval
   `REMEDIATION_PROGRESS.md` ga qaror matni (D72 dan boshlab) alohida commit bilan yoziladi:
   nima o‘lchanadi, qanday qoida bilan o‘qiladi. Natijani ko‘rgandan keyin qoida o‘zgartirilmaydi.
5. **Qo‘lda yozilgan son yo‘q (D48).** `tables.md` faqat `metrics.json` dan yasaladi.
6. **Model formulalari va `_THESIS_DEFAULTS` qiymatlari o‘zgarmaydi.** 2-bosqichdagi yagona
   qo‘shimcha — standart qiymati eski xatti-harakatni saqlaydigan yangi ixtiyoriy parametr.
7. **To‘xtash shartlari.** Quyidagi hollarda ishni to‘xtat va menga yoz, o‘zing yechim tanlama:
   ma’lumot fayli tuzilishi kutilganidan farq qilsa; bitta ishga tushirishning taxminiy vaqti
   24 soatdan oshsa; mavjud test qizarsa va sababi shu topshiriqdagi o‘zgarish bo‘lmasa;
   qaror qoidasini bajarish uchun ma’lumot yetmasa.
8. Uzoq ishga tushirishlar avvalgidek systemd unit va checkpoint bilan bajariladi
   (kompyuter uxlab qolishi, OOM). Boshlashdan oldin bo‘sh xotirani tekshir.
9. Har bosqich oxirida: testlar, `REMEDIATION_PROGRESS.md`, `docs/THESIS_MAPPING.md`
   yangilanadi.

---

## 1-bosqich. Repozitoriy tartibi va xavfsizlik (natijalarga ta’sir qilmaydi)

### Backend (`neuro_dj`)
1. Teg: `thesis-v1-frozen` (0.1-band).
2. **`main` ni yangilash.** Hozir GitHub’da standart branch `main` bo‘lib, unda avgustdagi
   eski prototip turibdi (SQLite, MPTT, `SECRET_KEY` kod ichida, `DEBUG = True`).
   `main` `thesis-model` ning ajdodi ekanini tekshir
   (`git merge-base --is-ancestor main thesis-model`), so‘ng `main` ni fast-forward qil
   (`git merge --ff-only thesis-model`) va push qil. `thesis-model` branchi qoladi.
   Fast-forward mumkin bo‘lmasa — to‘xta.
3. **Eski kalit.** Tarixdagi eski `SECRET_KEY` (commit `bb80ec4` va eski `main`) hech bir
   ishlayotgan muhitda ishlatilmayotganini tekshir (`.env` fayllar, server sozlamalari).
   Tarix tozalanmaydi; `README.md` ga bitta jumla qo‘sh: tarixdagi kalit ishlab chiqish
   davriga tegishli va bekor qilingan.
4. **README.** “Work in progress on branch thesis-model” xatboshisini yakuniy tavsif bilan
   almashtir: papkalar tuzilishi (`neuro_model`, `curriculum`, `assessments`, `experiments`,
   `benchmarks`, `verification`), testlarni ishga tushirish, natijalarni qayta hosil qilish
   (`experiments/README.md` ga havola), `docs/THESIS_MAPPING.md` ga havola,
   `thesis-v1-frozen` tegi nima ekani.
5. **Masofaviy CI.** Push’dan keyin GitHub Actions natijasini ko‘r (`gh run list`,
   `gh run view`). Qizil bo‘lsa, sababini top. Model kodi va natijalarga tegmasdan
   tuzatib bo‘lsa — tuzat; aks holda to‘xta va yoz.

### Frontend (`neuro`)
1. Teg `thesis-v1-frozen`, so‘ng `main` ni xuddi shunday fast-forward qil.
2. `.env` git’da kuzatilmoqda: `git rm --cached .env`, `.gitignore` ga `.env` qo‘sh,
   `.env.example` qoladi.
3. HEAD’da Supabase kaliti yoki boshqa token yo‘qligini `grep` bilan tasdiqla va hisobotga yoz.
   (Tarixdagi `83afe20` commitidagi kalitni men Supabase panelida o‘zim bekor qilaman.)
4. Masofaviy CI yashil bo‘lishi kerak (lint, `tsc`, `vitest`, build).

**1-bosqich hisoboti:** teg va `main` hash’lari; CI havolalari va holati; o‘zgargan fayllar ro‘yxati.
TO‘XTA.

---

## 2-bosqich. D72 — P(L) uchun ixtiyoriy yuqori chegara va tavsiya etilgan sozlamalar

**Muammo.** Ketma-ket to‘g‘ri javoblardan keyin P(L) 1 ga juda yaqinlashadi va bir necha
noto‘g‘ri javob ham mavzuni takrorlashga qaytarmaydi (dissertatsiyada cheklov sifatida yozilgan).

**Qaror (avval `REMEDIATION_PROGRESS.md` ga yoz):**
- `neuro_model/bkt.py`: `transition` va `step` ga ixtiyoriy `p_max: float = 1.0` parametri
  qo‘shiladi; P(L)′ = min(p_max, …). Standart 1.0 da xatti-harakat bit darajasida o‘zgarmaydi.
- `config/settings.py`: `THESIS_MODEL` ga `"P_L_MAX": 1.0` (muhit o‘zgaruvchisi `THESIS_P_L_MAX`).
  Server qatlami shu qiymatni uzatadi. Eksperiment kodi o‘zgarmaydi (u standart 1.0 bilan ishlaydi).
- `_THESIS_DEFAULTS["LAMBDA"]` va `THESIS_FLAGS` standartlari **o‘zgarmaydi**.
  `config/.env.example` ga izoh bilan tavsiya etilgan ish sozlamalari qo‘shiladi:
  `THESIS_P_L_MAX=0.999` va `THESIS_LAMBDA=0.0`
  (sabab: H3 ning post-hoc tahlilida AUC λ oshgan sari kamaygan; mahalliy ma’lumotda
  foydasi ko‘rsatilmaguncha prerekvizitlardan olinadigan boshlang‘ich baho o‘chiriladi).

**Testlar:**
- `p_max = 1.0` da mavjud barcha etalon va xossa testlari o‘zgarishsiz o‘tadi.
- `p_max = 0.999`, standart parametrlar (P(T) = 0,20; G = 0,20; S = 0,05): P(L) chegarada
  turganida ketma-ket **uchta** noto‘g‘ri javobdan keyin P(L) < τ − δ = 0,85 bo‘ladi,
  ikkitadan keyin esa hali bo‘lmaydi.
- `experiments/reproduce.py` darvozalari (yoki `--quick` qayta hosil qilish) avvalgi sonlarni beradi.

**Hisobot:** commit hash; o‘zgargan testlar soni; yangi testlar. TO‘XTA.

---

## 3-bosqich. D73 — neyron modellarni to‘liq o‘qitish (H2 uchun sezgirlik tahlili)

**Nega kerak.** Asosiy natijada (`assist09/20261010-060005`) DKT besh qismning hammasida
10 epoch chegarasida to‘xtagan, validatsiya AUC esa hali o‘sayotgan edi. AKT va AKT-R
uchtadan qismda `patience = 2` sababli 3–4-epochda to‘xtagan. Demak H2 ning ikkinchi sharti
to‘liq o‘qitilmagan DKT ga nisbatan tekshirilgan.

**Qaror matniga yoziladigan qoidalar (natijadan oldin):**
- Ma’lumot, tozalash, foldlar, seed (20261006), D57 baholash tartibi — asosiy natijadagi bilan aynan bir xil.
- O‘qitish: ko‘pi bilan 200 epoch, `patience = 10` (pyKT odatiga yaqin; pyKT hujjatidan
  tekshir, farq bo‘lsa qarorga yoz). Eng yaxshi validatsiya og‘irliklari saqlanadi.
- DKT uchun giperparametrlar to‘ri: vektor o‘lchami {64, 100, 200}, dropout {0,1; 0,3},
  learning rate {10⁻³; 10⁻⁴}. Har bir fold uchun eng yaxshi kombinatsiya faqat
  **validatsiya** AUC bo‘yicha tanlanadi; sinov qismi oxirgi baholashgacha ochilmaydi.
- AKT va AKT-R: arxitektura o‘zgarmaydi, learning rate {10⁻³; 10⁻⁴}, 200/10.
- Birinchi fold tugagach umumiy vaqtni hisobla; 24 soatdan oshsa — to‘xta va yoz.
- BKT+IRT prognozlari asosiy natijadagi bilan bir xil ekanini tekshir (pooled AUC 0,7239).
- Hisoblanadi: sozlangan DKT, AKT, AKT-R ning pooled AUC, RMSE va talabalar bo‘yicha
  bootstrap (1 000) ishonch oraliqlari; BKT+IRT − DKT va BKT+IRT − AKT-R farqlari [95 % CI].
- **O‘qish qoidasi.** H2 ning asosiy hukmi o‘zgarmaydi: u natijadan oldin belgilangan qoidaga
  ko‘ra chiqarilgan. Bu tahlil “post-hoc sezgirlik” deb belgilanadi va ikki xil o‘qiladi:
  (a) BKT+IRT − DKT farqining 95 % CI pastki chegarasi ≥ −0,01 bo‘lsa — “ikkinchi shart to‘liq
  o‘qitilgan DKT ga nisbatan ham bajariladi”; (b) aks holda — “ikkinchi shart faqat 10 epoch
  bilan cheklangan DKT ga nisbatan bajarilgan”. Qaysi biri chiqsa, o‘sha dissertatsiyaga yoziladi.

**Kod:** `experiments/models/neural.py` ga `patience` va to‘r parametrlari; `experiments/h2.py`
ga faqat neyron modellarni ishga tushiradigan rejim. Natija papkasi:
`experiments/results/assist09-neural-tuned/<vaqt>/`.

**Hisobot (faqat sonlar):** har fold uchun tanlangan kombinatsiya, bajarilgan epochlar,
validatsiya AUC; pooled jadval; ikki farq [CI]; o‘qish qoidasining natijasi; umumiy vaqt. TO‘XTA.

---

## 4-bosqich. D74 — H4 uchun uchinchi o‘qish usuli (so‘ralgan tugundan boshlanadigan CTE)

**Nega kerak.** O‘qishdagi sekinlik django-tree-queries so‘rovining shaklidan kelgan
(rekursiya jadvaldagi barcha ildizlardan boshlanadi). Dissertatsiya “rekursiyani so‘ralgan
tugundan boshlash” ni tavsiya qiladi, lekin bu o‘lchanmagan.

**Qaror matniga yoziladigan qoidalar:**
- Yangi usul nomi `cte_rooted`. Jadval — mavjud `CteNode`; yozish amallari o‘lchanmaydi
  (ular `cte` bilan bir xil).
- Ikki o‘qish amali qo‘lda yozilgan rekursiv CTE bilan:
  shoxni o‘qish — `WHERE id = %s` dan boshlab `parent_id` bo‘yicha pastga;
  ajdodlarni o‘qish — tugundan boshlab `parent_id` bo‘yicha yuqoriga.
  Natija model obyektlari sifatida olinadi (`Model.objects.raw` yoki teng yo‘l), chunki qolgan
  ikki usul ham obyekt qaytaradi.
- To‘g‘rilik testi: har ikki amal uchun qaytgan `id` lar to‘plami kutubxonaning
  `descendants()` / `ancestors()` natijasiga teng.
- O‘lchov D63 bilan aynan bir xil: 3 shakl × 10³, 10⁴, 10⁵ tugun, bir xil nishonlar va seed,
  5 isitish + 30 takror, bir xil vaqt chegarasi va xotira himoyasi (D63f).
- Hisoblanadi: mediana, p95, `cte_rooted / mptt` va `cte_rooted / cte` nisbatlari, D63 dagi
  interval usuli bilan.
- **O‘qish qoidasi.** H4 ning hukmi o‘zgarmaydi. Bu qo‘shimcha o‘lchov tavsiyani tekshiradi:
  barcha o‘qish kataklarida `cte_rooted` nested set dan ko‘pi bilan 1,5 barobar sekin bo‘lsa —
  “tavsiya tasdiqlandi”; aks holda qaysi kataklarda bajarilmagani yoziladi.

**Natija papkasi:** yangi `tree-benchmark-rooted/<vaqt>/`.
**Hisobot:** o‘qish bo‘yicha uch usulli jadval (mptt / cte / cte_rooted), o‘qish qoidasining natijasi. TO‘XTA.

---

## 5-bosqich. D75 — H2 ni XES3G5M to‘plamida takrorlash

> **Bekor qilindi (2026-11-24):** hisoblash quvvati va dastlabki himoyagacha vaqt
> yetmaydi. Bosqich ishga tushirilmaydi; qaror — `REMEDIATION_PROGRESS.md` D75,
> holat — `docs/THESIS_MAPPING.md` (D72–D75 jadvali). Quyidagi matn reja sifatida
> o‘zgarishsiz qoldirildi.

**Ma’lumot.** XES3G5M (NeurIPS 2023, MIT litsenziyasi). Fayllarni men
`github.com/ai4ed/XES3G5M` sahifasidagi Google Drive havolasidan qo‘lda yuklab, yo‘lini beraman.
Sen avval to‘plamning README va fayl tuzilishini o‘qi; tuzilish quyidagi rejaga mos kelmasa — to‘xta.

**Qaror matniga yoziladigan qoidalar (model natijasini ko‘rmasdan oldin):**
- Yuklovchi `experiments/datasets/xes3g5m.py`: savol darajasidagi ketma-ketliklar; bir nechta
  bilim komponentiga bog‘langan savol har bir komponent uchun alohida yozuvga ajratiladi va
  bitta `order` hisoblanadi (D57). Tozalash qoidalari, qatorlar soni va fayllarning SHA-256
  yig‘indisi qayd etiladi.
- Namuna: talabalardan 4 000 tasi tasodifiy tanlanadi (seed 20261006) — hajm ASSISTments 2009
  namunasiga yaqin bo‘lishi uchun. Birinchi fold vaqtidan umumiy vaqt 24 soatdan oshishi
  ko‘rinsa — to‘xta.
- Modellar: BKT, BKT+IRT (λ = 0), Elo/Rasch, PFA, DKT, AKT, AKT-R. Neyron modellar D73
  tartibida o‘qitiladi. BKT+IRT+Pre ishga tushirilmaydi: to‘plamdagi tuzilma prerekvizitlar
  grafi emas, bilim komponentlari ierarxiyasi.
- Ajratish, parametrlarni baholash, G_max/S_max chegaralari, statistika — D53, D56, D59 dagidek.
- **O‘qish qoidasi.** H2 ning ikki sharti o‘zgarishsiz qo‘llanadi. Ikkalasi bajarilsa —
  “takrorlandi”; faqat birinchisi bajarilsa — “qisman takrorlandi”; birinchisi bajarilmasa —
  “takrorlanmadi”. Har qanday natija dissertatsiyaga yoziladi.

**Natija papkasi:** `experiments/results/xes3g5m/<vaqt>/`.
**Hisobot:** namuna tavsifi (talaba, savol, komponent, yozuv, ko‘p komponentli savollar soni);
pooled jadval; ikki farq [CI]; dastlabki 3 va 5 javob ustunlari; o‘qish qoidasining natijasi. TO‘XTA.

---

## 6-bosqich (ixtiyoriy, faqat men so‘rasam). D76 — H1/H3 uchun ikkinchi to‘plamning yaroqliligi

Model ishga tushirilmaydi, faqat sanash: FoundationalASSIST (Hugging Face, CC-BY-NC-4.0) va
Common Core “Coherence Map” (`achievethecore/atc-coherence-map`) birga H1/H3 ni takrorlashga
yaraydimi. Hisobot: fayllarga kirish ochildimi; nechta masala standartga bog‘langan; shu
standartlar orasida nechta prerekvizit qirra bor; sikl bormi; nechta talaba kamida bitta
“prerekvizit → mavzu” juftligining ikkala tomonida javob bergan. Shu sonlardan keyin qarorni men chiqaraman.

---

## Yakuniy hisobot

(D75 bekor qilingani uchun yakuniy hisobot D72–D74 ni qamraydi.)

Barcha bosqichlar tugagach bitta qisqa hujjat: har bir qaror (D72–D75) uchun commit hash,
natija papkasi, `tables.md` ning o‘zi (ko‘chirma emas), ishga ketgan vaqt va rejadan
chetlanishlar (bo‘lsa, sababi bilan). Talqin yozma — faqat sonlar va o‘qish qoidasining natijasi.
