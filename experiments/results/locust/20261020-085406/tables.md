# Locust: 50 foydalanuvchi, 120 s

| Endpoint | So‘rovlar | Xatolar | Xato ulushi | p50, ms | p95, ms | RPS |
|---|---|---|---|---|---|---|
| login | 50 | 0 | 0 | 1000 | 2300 | 0.419 |
| next_question | 520 | 0 | 0 | 1700 | 2600 | 4.363 |
| submit_answer | 501 | 0 | 0 | 4500 | 15000 | 4.203 |
| trajectory | 536 | 0 | 0 | 2500 | 3900 | 4.497 |
| Aggregated | 1657 | 0 | 0 | 2400 | 6300 | 13.902 |

V-F2 mo‘ljali (p95 < 300 ms, yumshoq):
- `submit_answer`: p95 15000 ms — mo‘ljaldan yuqori
- `trajectory`: p95 3900 ms — mo‘ljaldan yuqori
- `next_question`: p95 2600 ms — mo‘ljaldan yuqori

## Muhit

- Server: django runserver (threaded, one process, --noreload); **DEBUG=False**; kesh Redis (redis://127.0.0.1:6380/3); `DB_CONN_MAX_AGE`=0
- Ma’lumotlar bazasi: `neurolearn_locust` (alohida, faqat simulyatsiya — D13); kurs: 500 mavzu, 1500 prerekvizit
- CPU: 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz, 16 mantiqiy yadro, governor powersave
- Xotira oldin: MemAvailable 9257 MB / MemTotal 15249 MB; swap bo‘sh 4095 / 4095 MB
- Yuk davomida: eng past MemAvailable 6869 MB, eng past SwapFree 4095 MB (25 namuna)
- Server logidagi status kodlari: 200 — 1647

## Manba

- commit `0e424d7`, dirty=False
- buyruq: `load_test.py`
- p50/p95 — Locust'ning o‘zi: 100 ms dan yuqorida vaqtlar ikki muhim raqamgacha yaxlitlangan.
