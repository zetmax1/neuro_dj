# Graf tahlili — 3.3-bo‘limga qo‘yishga tayyor

Bu fayl `metrics.json` dan avtomatik yasaladi (D48). Qo‘lda yozilgan son yo‘q;
`experiments/tests/test_tables.py` har bir sonning `metrics.json` da borligini
tekshiradi. Ma’lumoti yo‘q graf uchun qator soni emas, holati chiqadi.

## 1. Graf o‘lchamlari va Y3

| Graf | Yo‘nalish | Tugun | Fayldagi qirra | Qirra | O‘z-o‘ziga | Izolyatsiyalangan | DAG | Kuchsiz komp. | Ortiqcha | Eng uzun yo‘l | sha256 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| DBE-KT22 | prereq_to_dependent | 98 | 101 | 101 | 0 | 0 | ha | 8 | 9 | 5 | `79ece343c01c` |
| DBE-KT22 | dependent_to_prereq | 98 | 101 | 101 | 0 | 0 | ha | 8 | 9 | 5 | `79ece343c01c` |
| Junyi | prereq_to_dependent | 1004 | 740 | 738 | 2 | 73 | ha | 266 | 0 | 9 | `6272d524b6cc` |
| WDKG-Course | prereq_to_dependent | 46 | 73 | 72 | 1 | 0 | ha | 3 | 12 | 6 | `a6475f00a343` |
| WDKG-KnowledgePoints | prereq_to_dependent | 121 | 285 | 285 | 0 | 87 | ha | 88 | 0 | 1 | `469032f4dc03` |

## 2. Tranzitiv ortiqcha qirralar

**DBE-KT22** [prereq_to_dependent] — 9

- `Database Security` → `Access Control`
- `Discretionary access control (DAC)` → `REVOKE`
- `Discretionary access control (DAC)` → `Specifying Privileges - Views`
- `Entity-Relationship Model` → `Data Model`
- `Entity-Relationship Model` → `Entity`
- `Participation constraints` → `Relationship`
- `Role-Based Access Control (RBAC)` → `Access Control`
- `Superkey` → `Relational data model`
- `Transactions` → `ACID Properties`

**DBE-KT22** [dependent_to_prereq] — 9

- `ACID Properties` → `Transactions`
- `Access Control` → `Database Security`
- `Access Control` → `Role-Based Access Control (RBAC)`
- `Data Model` → `Entity-Relationship Model`
- `Entity` → `Entity-Relationship Model`
- `REVOKE` → `Discretionary access control (DAC)`
- `Relational data model` → `Superkey`
- `Relationship` → `Participation constraints`
- `Specifying Privileges - Views` → `Discretionary access control (DAC)`

**Junyi** [prereq_to_dependent] — 0

- yo‘q

**WDKG-Course** [prereq_to_dependent] — 12

- `大学物理B` → `工程水文学B`
- `工程材料` → `桥梁工程`
- `概率统计` → `工程经济学B`
- `概率统计` → `水利水能规划A`
- `水力学A` → `河床演变与河道整治`
- `水力学A` → `航道整治`
- `理论力学A` → `河流动力学`
- `高等数学A` → `3S系统`
- `高等数学A` → `工程材料`
- `高等数学A` → `工程水文学B`
- `高等数学A` → `建筑材料`
- `高等数学A` → `河流动力学`

**WDKG-KnowledgePoints** [prereq_to_dependent] — 0

- yo‘q

## 3. Y3 — sikl va kuchli bog‘langan komponentlar

Ishga tushirilgan graflarning hammasi asiklik; birlashtirish bo‘lmadi.

## 4. Tayyorlik yangilanishi: inkremental va to‘liq qayta hisoblash

Bitta javobdan keyin Algoritm 2.3 faqat |Succ(v)| tugunni ko‘radi; TY6 ning
to‘liq qayta hisoblashi har bir tugunni ko‘radi. Vaqtlar mashinaga bog‘liq,
shuning uchun ular testda tasdiqlanmaydi — tasdiqlanadigan narsa: inkremental
yo‘l ko‘radigan tugunlar soni to‘liqdan kichik yoki teng.

| Graf | Yo‘nalish | Namuna | Takror | Inkremental tugun (median) | To‘liq tugun | Inkremental µs (median / p95) | To‘liq µs (median / p95) | Tezlashish (median) |
|---|---|---|---|---|---|---|---|---|
| DBE-KT22 | prereq_to_dependent | 50 | 30 | 1 | 98 | 0.928 / 1.614 | 39.06 / 39.985 | 42.107× |
| DBE-KT22 | dependent_to_prereq | 50 | 30 | 1 | 98 | 0.903 / 1.712 | 38.847 / 39.066 | 43.017× |
| Junyi | prereq_to_dependent | 50 | 30 | 3 | 1004 | 1.401 / 2.059 | 396.605 / 401.192 | 283.188× |
| WDKG-Course | prereq_to_dependent | 27 | 30 | 2 | 46 | 1.11 / 2.145 | 19.8 / 20.066 | 17.842× |
| WDKG-KnowledgePoints | prereq_to_dependent | 19 | 30 | 15 | 121 | 3.647 / 3.77 | 51.99 / 52.723 | 14.256× |

## 5. Manba va ishga tushirish (D48)

- kod commit'i: `c1a683b`
- buyruq: `python -m experiments.graph_report`
- vaqt: 2026-10-06T05:23:48.942321+00:00
- python: 3.12.3, Linux-7.0.0-38-generic-x86_64-with-glibc2.39
- seed: sample_order = 20261006

| Fayl | sha256 | Bayt |
|---|---|---|
| `DBE-KT22` | `79ece343c01ceb3a6e46c01e70959692de0f6728846f703bdac5aa55f7961307` | 27398 |
| `Junyi` | `6272d524b6ccd83c349d298ef9699c1eca5c0be5b897860324fbe4a392ee61d2` | 273184 |
| `WDKG-Course` | `a6475f00a343171e5cf9891f5ba1407b6fef7141ba830b8c6f277181d2ddae01` | 7511 |
| `WDKG-KnowledgePoints` | `469032f4dc034bc57c7f7c4bea457a53352995200aca46309fa6a6be97486906` | 24444 |

