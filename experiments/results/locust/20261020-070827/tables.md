# Locust: 5 foydalanuvchi, 120 s

| Endpoint | So‘rovlar | Xatolar | Xato ulushi | p50, ms | p95, ms | RPS |
|---|---|---|---|---|---|---|
| login | 5 | 0 | 0.00% | 450 | 470 | 0.04 |
| next_question | 480 | 0 | 0.00% | 67 | 120 | 4.04 |
| submit_answer | 476 | 0 | 0.00% | 87 | 160 | 4.00 |
| trajectory | 485 | 0 | 0.00% | 65 | 150 | 4.08 |
| Aggregated | 1451 | 0 | 0.00% | 76 | 150 | 12.21 |

V-F2 mo‘ljali (p95 < 300 ms, yumshoq):
- `submit_answer`: p95 160 ms — mo‘ljal ichida
- `trajectory`: p95 150 ms — mo‘ljal ichida
- `next_question`: p95 120 ms — mo‘ljal ichida

## Muhit

- Server: django runserver (threaded, one process, --noreload); **DEBUG=False**; kesh Redis (redis://127.0.0.1:6380/3); `DB_CONN_MAX_AGE`=0
- Ma’lumotlar bazasi: `neurolearn_locust` (alohida, faqat simulyatsiya — D13); kurs: 500 mavzu, 1500 prerekvizit
- CPU: 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz, 16 mantiqiy yadro, governor ['powersave']
- Xotira oldin: MemAvailable 6923 MB / MemTotal 15249 MB; swap bo‘sh 1864 / 4095 MB
- Yuk davomida: eng past MemAvailable 6469 MB, eng past SwapFree 1839 MB (25 namuna)
- Server logidagi status kodlari: {'200': 1463, '404': 4}

## Manba

- commit `f41bfb0`, dirty=False
- buyruq: `load_test.py --users 5`
- p50/p95 — Locust'ning o‘zi: 100 ms dan yuqorida vaqtlar ikki muhim raqamgacha yaxlitlangan.
