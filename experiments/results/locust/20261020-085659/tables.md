# Locust: 5 foydalanuvchi, 120 s

| Endpoint | So‘rovlar | Xatolar | Xato ulushi | p50, ms | p95, ms | RPS |
|---|---|---|---|---|---|---|
| login | 5 | 0 | 0 | 620 | 630 | 0.042 |
| next_question | 387 | 0 | 0 | 120 | 240 | 3.251 |
| submit_answer | 384 | 0 | 0 | 170 | 310 | 3.226 |
| trajectory | 392 | 0 | 0 | 170 | 310 | 3.293 |
| Aggregated | 1173 | 0 | 0 | 150 | 300 | 9.854 |

V-F2 mo‘ljali (p95 < 300 ms, yumshoq):
- `submit_answer`: p95 310 ms — mo‘ljaldan yuqori
- `trajectory`: p95 310 ms — mo‘ljaldan yuqori
- `next_question`: p95 240 ms — mo‘ljal ichida

## Muhit

- Server: django runserver (threaded, one process, --noreload); **DEBUG=False**; kesh Redis (redis://127.0.0.1:6380/3); `DB_CONN_MAX_AGE`=0
- Ma’lumotlar bazasi: `neurolearn_locust` (alohida, faqat simulyatsiya — D13); kurs: 500 mavzu, 1500 prerekvizit
- CPU: 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz, 16 mantiqiy yadro, governor powersave
- Xotira oldin: MemAvailable 7710 MB / MemTotal 15249 MB; swap bo‘sh 4095 / 4095 MB
- Yuk davomida: eng past MemAvailable 7561 MB, eng past SwapFree 4095 MB (25 namuna)
- Server logidagi status kodlari: 200 — 1175, 404 — 3

## Manba

- commit `e836b2f`, dirty=False
- buyruq: `load_test.py --users 5`
- p50/p95 — Locust'ning o‘zi: 100 ms dan yuqorida vaqtlar ikki muhim raqamgacha yaxlitlangan.
