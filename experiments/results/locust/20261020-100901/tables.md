# Locust: 50 foydalanuvchi, 120 s

| Endpoint | So‘rovlar | Xatolar | Xato ulushi | p50, ms | p95, ms | RPS |
|---|---|---|---|---|---|---|
| login | 50 | 0 | 0 | 500 | 710 | 0.419 |
| next_question | 3902 | 0 | 0 | 120 | 190 | 32.689 |
| submit_answer | 3868 | 0 | 0 | 140 | 210 | 32.404 |
| trajectory | 3942 | 0 | 0 | 190 | 280 | 33.024 |
| Aggregated | 11812 | 0 | 0 | 150 | 250 | 98.954 |

V-F2 mo‘ljali (p95 < 300 ms, yumshoq):
- `submit_answer`: p95 210 ms — mo‘ljal ichida
- `trajectory`: p95 280 ms — mo‘ljal ichida
- `next_question`: p95 190 ms — mo‘ljal ichida

## Muhit

- Server: gunicorn 26.2.0, 8 sync workers; **DEBUG=False**; kesh Redis (redis://127.0.0.1:6380/3); `DB_CONN_MAX_AGE`=0
- Ma’lumotlar bazasi: `neurolearn_locust` (alohida, faqat simulyatsiya — D13); kurs: 500 mavzu, 1500 prerekvizit
- CPU: 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz, 16 mantiqiy yadro, governor powersave
- Xotira oldin: MemAvailable 7526 MB / MemTotal 15249 MB; swap bo‘sh 4095 / 4095 MB
- Yuk davomida: eng past MemAvailable 6596 MB, eng past SwapFree 4095 MB (25 namuna)
- Server logidagi status kodlari: 200 — 11857, 404 — 30

## Manba

- commit `8f58a42`, dirty=False
- buyruq: `load_test.py --workers 8`
- p50/p95 — Locust'ning o‘zi: 100 ms dan yuqorida vaqtlar ikki muhim raqamgacha yaxlitlangan.
