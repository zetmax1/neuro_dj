# experiments/data — ma'lumot bu yerga qo'yiladi

Bu papkadagi ma'lumot fayllari repoda **yo'q** va kuzatilmaydi. Sabab D49:
fayllarni foydalanuvchi qo'lda oladi, skriptlar internetdan o'zi yuklamaydi va
yo'lni argument sifatida qabul qiladi.

Nega shunday: ikki to'plam litsenziya ostida, bittasiga kirish so'rovi orqali
olinadi, va eng muhimi — o'zi qayta yuklab oladigan skript ikki ishga
tushirish bir xil baytlarni ko'rganini kafolatlay olmaydi. O'rniga natijaga
har bir faylning sha256 yoziladi (D48).

`NEUROLEARN_DATA` o'rnatilsa, yuklovchilar va testlar shu yo'ldan o'qiydi.

## Kutilgan joylashuv

```
experiments/data/
  assistments2009/
    as.csv
  kg/
    DBE-KT22.graphml
    Junyi-Prerequisites.graphml
    WDKG-Course.graphml
    WDKG-KnowledgePoints.graphml
```

## Qanday olinadi

```sh
cd ~/Desktop/neuro_dj/experiments/data

# 1. ASSISTments 2009-2010 skill builder (asl versiya) — javoblar
git clone --depth 1 --filter=blob:none --sparse \
    https://github.com/CAHLR/pyBKT-examples.git /tmp/pybkt-examples
git -C /tmp/pybkt-examples sparse-checkout set data
mkdir -p assistments2009 && cp /tmp/pybkt-examples/data/as.csv assistments2009/

# 2. To'rtta nashr etilgan prerekvizit grafi (CC BY 4.0)
git clone --depth 1 \
    https://github.com/ai-for-edu/Evaluating-Large-Language-Models-with-Educational-Knowledge-Graphs-on-Prerequisite-Relationships.git \
    /tmp/kc4edu
mkdir -p kg
cp /tmp/kc4edu/data/DBE-KT22/DBE-KT22.graphml kg/
cp /tmp/kc4edu/data/Junyi/Junyi-Prerequisites.graphml kg/
cp /tmp/kc4edu/data/WDKG/WDKG-Course.graphml kg/
cp /tmp/kc4edu/data/WDKG/WDKG-KnowledgePoints.graphml kg/

sha256sum assistments2009/as.csv kg/*.graphml
```

## Tekshirilgan sha256

Bu qiymatlar 8b-1 da ishga tushirilgan nusxalarning qiymatlari. Mos kelmasa
ham quvur to'xtamaydi (boshqacha paketlangan nusxa bo'lishi mumkin), lekin
`metadata` ga farq yoziladi. ASSISTments uchun haqiqiy tekshiruv — D50 ning
qatorlar soni, u mos kelmasa quvur **to'xtaydi**.

| Fayl | sha256 | Bayt | Manba |
|---|---|---|---|
| `assistments2009/as.csv` | `f22e3fb7872c1784ce93b0f9ebabbe0cbcac4f896fd8b4a11667b9715d77dbdc` | 83 201 940 | pyBKT-examples, commit `fc59290` |
| `kg/DBE-KT22.graphml` | `79ece343c01ceb3a6e46c01e70959692de0f6728846f703bdac5aa55f7961307` | 27 398 | KC4EDU, commit `ac0b6e0` |
| `kg/Junyi-Prerequisites.graphml` | `6272d524b6ccd83c349d298ef9699c1eca5c0be5b897860324fbe4a392ee61d2` | 273 184 | o'sha repo |
| `kg/WDKG-Course.graphml` | `a6475f00a343171e5cf9891f5ba1407b6fef7141ba830b8c6f277181d2ddae01` | 7 511 | o'sha repo |
| `kg/WDKG-KnowledgePoints.graphml` | `469032f4dc034bc57c7f7c4bea457a53352995200aca46309fa6a6be97486906` | 24 444 | o'sha repo |

## Hali yo'q

| Manba | Nima kerak | Holat |
|---|---|---|
| DBE-KT22 to'liq (javoblar bilan) | ADA, doi:10.26193/6DZWOH | kirish olinmadi (D49). Yuklovchi 8b-3 da `DBE_SCHEMA` bo'yicha yoziladi va sintetik fixture bilan test qilinadi |
| ASSISTments uchun o'qituvchilar grafi | `experiments/graphs/assist09_prereq.csv` | tuzilmagan. H1/H3 uni `--graph` bilan qabul qiladi (8b-3) |
| Mahalliy eksport | `manage.py export_research_data` | rozilik yig'ilgach (8a tayyor) |

Ularning hech biri yo'qligida H1 va H3 **ishga tushirilmaydi**, va jadvalda
"ishga tushirilmagan — ma'lumot yo'q" deb chiqadi. Taxminiy yoki maqoladan
olingan son hech qachon qo'yilmaydi (D48).

## Litsenziyalar

To'rtta graf CC BY 4.0 ostida (KC4EDU repozitoriysi). ASSISTments 2009-2010
skill builder ma'lumotlari ASSISTments platformasining ommaviy tadqiqot
to'plamidan. Har biri o'z manbasining shartlari bo'yicha ishlatiladi; fayllar
bu repoga qo'shilmaydi.
