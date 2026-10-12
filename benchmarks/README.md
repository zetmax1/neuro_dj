# benchmarks — H4: daraxtni saqlash usullari (9-bosqich)

Bu app bitta savolga javob beradi (D63):

> Bilimlar bazasining daraxti uchun qo‘shni ro‘yxat + rekursiv CTE (CTE usuli)
> **yozish** amallarida MPTT dan tez va parallel yozishda yaxlitligini
> saqlaydi; **o‘qish** amallarida MPTT bilan taqqoslanadigan bo‘lib qoladi.

Ikkita jadval bir xil daraxtni saqlaydi: `CteNode` — platformaning o‘zi
ishlatadigan usul (`django-tree-queries`, D3; `curriculum.Topic` bilan bir xil
baza, menejer va `(position, id)` tartibi), `MpttNode` — oraliq kodlash
(`django-mptt`, D3 bo‘yicha faqat shu app'da qoladi).

Eski `curriculum/management/commands/benchmark_tree.py` almashtirildi: u faqat
o‘qishni, faqat o‘rtacha vaqtni va SQLite'ni o‘lchagan (audit, EX5).

## Alohida baza

Benchmark 100 000 tugunli daraxtlar yozadi va har katakdan oldin **o‘z**
jadvallarini `TRUNCATE` qiladi, shuning uchun u alohida bazada ishlaydi:
`DATABASES["benchmark"]` — `BENCHMARK_DATABASE_URL` bo‘lsa shundan, aks holda
`default` ning sozlamalaridan `NAME` ga `_bench` qo‘shib. `BenchmarkRouter`
ikki yo‘nalishda ham ushlab turadi: `benchmarks` app'i faqat shu alias'da,
boshqa hech narsa esa u yerda emas. Buyruq alias dev bazasiga tushsa
**to‘xtaydi**.

```sh
# 1. Postgres (D1: compose, host porti 5433)
docker compose --env-file config/.env up -d

# 2. Bazani bir marta yaratish
docker exec neurolearn-postgres-1 bash -c \
    'createdb -U "$POSTGRES_USER" "${POSTGRES_DB}_bench"'

# 3. Migratsiyalar (router faqat benchmarks jadvallarini yaratadi)
scripts/dj5433.sh venv/bin/python manage.py migrate --database=benchmark

# 4. Quvurni sinash, keyin to‘liq run
scripts/dj5433.sh venv/bin/python manage.py run_tree_benchmark --quick
experiments/run_h2.sh bench-full          # systemd user unit, uzoq run uchun
```

`scripts/dj5433.sh` DSN'ni konteynerning o‘z muhitidan yasaydi va
`DJANGO_ENV_FILE=""` bilan `config/.env` ni o‘chiradi (fayl o‘qilmaydi ham,
o‘zgartirilmaydi ham; parol terminalga ham, unit muhitiga ham chiqmaydi).

> `manage.py makemigrations` ni o‘ramsiz ishga tushirsangiz, `neurolearn_bench`
> 5432 da yo‘qligi uchun ogohlantirish chiqadi. Bu faqat ogohlantirish:
> migratsiyalar `default` bo‘yicha tekshiriladi.

## O‘lchov tartibi (D63)

| Nima | Qanday |
|---|---|
| Daraxtlar | kursga o‘xshash (4 daraja, keng), chuqur zanjir, tasodifiy; 10³, 10⁴, 10⁵ tugun; seed `20261006` |
| Amallar | shoxni o‘qish, ajdodlarni o‘qish, oxiriga barg, eng chapga barg, shoxni ko‘chirish, shoxni o‘chirish |
| Takrorlar | 5 qizdirish + 30 takror; mediana, p95, SQL soni (`CaptureQueriesContext`), o‘zgargan qatorlar |
| Juftlashtirish | har takrorda ikkala usul **bir xil** nishon tugunda ishlaydi |
| O‘zgartiruvchi amallar | tranzaksiyada o‘lchanadi va orqaga qaytariladi, ya’ni har takror bir xil daraxtdan boshlanadi |
| Timeout | bitta takror `--timeout` dan oshsa, katak “timeout” bo‘ladi va son yozilmaydi |
| Parallel yozish | 2/4/8 jarayon, har biri o‘z ulanishi bilan, belgilangan vaqt; **qulfsiz** (usulning o‘zi) va **qulfli** (platformaning yo‘li, `pg_advisory_xact_lock`) variantlar (D63a) |
| Yaxlitlik | Y1 ikkala usulda; MPTT uchun `lft < rght`, oraliqlarning ichma-ichligi, `level` va qayta hisoblash bilan solishtirish |

Nisbat ρ = mediana(MPTT) / mediana(CTE) va uning juftlashtirilgan bootstrap
oralig‘i (1 000 replika) har katak uchun hisoblanadi; “tezroq” faqat oraliq 1
ni kesmasa aytiladi (D63).

Natija `experiments/results/tree-benchmark/<timestamp>/` ga yoziladi:
`metrics.json`, `tables.md` (D48 verify va pozitsion tekshiruv),
`measurements.csv` (har takrorning xom vaqti), `env.txt`. Har (shakl, hajm)
bloki uchun checkpoint `experiments/.runs/checkpoints/` da.

## Testlar

```sh
scripts/dj5433.sh venv/bin/python -m pytest benchmarks/tests -q
```

| Fayl | Nima tasdiqlanadi |
|---|---|
| `test_generator.py` | uchta shaklning xossalari, determinizm, `intervals` ning mptt `rebuild()` bilan aynan tengligi, ikkala jadval bir xil daraxtni saqlashi, ketma-ketlikning siljitilishi |
| `test_integrity.py` | har bir tekshiruv toza daraxtda o‘tadi va ataylab buzilgan daraxtda yiqiladi (sikl, ikkinchi ildiz, teskari oraliq, noto‘g‘ri `level`, takroriy chegaralar) |
| `test_operations.py` | nishonlar juftlashtirilgani va shox ichida bo‘lmasligi, ikki usulning o‘qishda bir xil javob berishi, yozishda bir xil daraxt qoldirishi, Y1 tekshiruvi (D63a) |
| `test_runner.py` | ρ va oraliq, uchta xulosa, timeout, o‘zgartiruvchi takrorning daraxtni o‘zgartirmasligi, o‘qish qoidasining har bir sharti, checkpoint, CSV |
| `test_command.py` | dev bazasini rad etishi, noma’lum alias, `--quick` uchidan-uchiga (D48 verify) va platformaning jadvallariga tegmasligi |

Vaqt o‘lchovlari testda tasdiqlanmaydi: ular mashinaga bog‘liq. Tasdiqlanadigan
narsa — tartib, juftlashtirish, qaytarilish va tekshiruvlarning ushlashi.
