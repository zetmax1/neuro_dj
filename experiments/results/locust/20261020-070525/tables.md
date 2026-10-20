# Locust: 50 foydalanuvchi, 120 s

| Endpoint | So‘rovlar | Xatolar | Xato ulushi | p50, ms | p95, ms | RPS |
|---|---|---|---|---|---|---|
| login | 50 | 0 | 0.00% | 830 | 1600 | 0.42 |
| next_question | 1025 | 0 | 0.00% | 900 | 1300 | 8.61 |
| submit_answer | 995 | 0 | 0.00% | 2300 | 4500 | 8.35 |
| trajectory | 1041 | 0 | 0.00% | 1100 | 1600 | 8.74 |
| Aggregated | 3161 | 0 | 0.00% | 1200 | 3000 | 26.54 |

V-F2 mo‘ljali (p95 < 300 ms, yumshoq):
- `submit_answer`: p95 4500 ms — mo‘ljaldan yuqori
- `trajectory`: p95 1600 ms — mo‘ljaldan yuqori
- `next_question`: p95 1300 ms — mo‘ljaldan yuqori

## Muhit

- Server: django runserver (threaded, one process, --noreload); **DEBUG=False**; kesh Redis (redis://127.0.0.1:6380/3); `DB_CONN_MAX_AGE`=0
- Ma’lumotlar bazasi: `neurolearn_locust` (alohida, faqat simulyatsiya — D13); kurs: 500 mavzu, 1500 prerekvizit
- CPU: 11th Gen Intel(R) Core(TM) i7-11800H @ 2.30GHz, 16 mantiqiy yadro, governor ['powersave']
- Xotira oldin: MemAvailable 6937 MB / MemTotal 15249 MB; swap bo‘sh 1864 / 4095 MB
- Yuk davomida: eng past MemAvailable 6388 MB, eng past SwapFree 1864 MB (25 namuna)
- Server logidagi status kodlari: {'200': 3172, '404': 5}

## Manba

- commit `5ab628e`, dirty=False
- buyruq: `load_test.py`
- p50/p95 — Locust'ning o‘zi: 100 ms dan yuqorida vaqtlar ikki muhim raqamgacha yaxlitlangan.
