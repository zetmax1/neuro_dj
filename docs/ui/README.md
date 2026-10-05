# docs/ui — dissertatsiyaning 3.1-bo‘limi uchun interfeys skrinshotlari

Addendum 2.11 har bir sahifaning skrinshotini shu papkada talab qiladi: 1440 px
kenglik, o‘zbek tili, `seed_thesis_demo` bilan to‘ldirilgan baza. 7.1 bosqichi
(D41) skriptni beradi; rasmlarni foydalanuvchi o‘z mashinasida oladi, chunki
ishlayotgan brauzer, frontend va backend kerak.

## Qanday olinadi

```sh
# 1. Baza — faqat demo ma'lumot bilan
cd ~/Desktop/neuro_dj
docker compose --env-file config/.env up -d
venv/bin/python manage.py seed_thesis_demo
venv/bin/python manage.py runserver 8000

# 2. Frontend
cd ~/Desktop/neuro/neuro
npm run dev                                   # http://localhost:8080

# 3. Skript (Playwright ilovaning bog'liqligi emas, alohida o'rnatiladi)
npm i -D playwright && npx playwright install chromium
npm run screenshots -- --email <talaba_email> --password '<parol>' \
                      --out ~/Desktop/neuro_dj/docs/ui
npm run screenshots -- --email <staff_email>  --password '<parol>' \
                      --out ~/Desktop/neuro_dj/docs/ui
```

Ikki marta ishga tushirilishining sababi: o‘qituvchi va admin sahifalari rolga
bog‘langan (D15), talaba akkaunti bilan ular `/dashboard` ga qaytariladi va
skript ularni rasmga olmaydi — `manifest.json` ga «skipped» deb yoziladi.

Demo parol `DEMO_PASSWORD` dan olinadi yoki `seed_thesis_demo` bir marta chop
etadi (`accounts/demo.py`). Parol bu faylga yozilmaydi.

## Natija

```
docs/ui/
  uz/
    landing-1440.png        dashboard-1440.png      learning-path-1440.png
    assessment-1440.png     mistakes-1440.png       profile-1440.png
    topic-1440.png          practice-1440.png       course-structure-1440.png
    prerequisite-editor-1440.png                    users-1440.png
    …-1280.png, …-768.png
    manifest.json
```

`manifest.json` — qaysi rasm qaysi sahifadan, qaysi kenglikda, qaysi mavzu
id'si bilan va frontend'ning qaysi commit'idan olinganini yozadi. 3.1-bo‘limda
rasm ostida manba ko‘rsatilishi kerak bo‘lsa, javob shu faylda.

Rasmlar deterministik: viewport va piksel zichligi qotirilgan, mavzu
(colour scheme) har doim yorug‘, animatsiyalar o‘chirilgan, har bir kadrdan
oldin tarmoq va ilovaning yuklash indikatori kutiladi. Graf sahifalari `lev`
joylashuvida (standart, 7-bosqich), shuning uchun bir xil graf har doim bir xil
ko‘rinadi — himoyada rasmni qayta olish mumkin bo‘lishi shart.

## Nega rasmlar repoda yo‘q

PNG fayllar hozircha qo‘shilmagan: ularni olish uchun brauzer kerak va ular
`seed_thesis_demo` holatiga bog‘liq. Skript — 7.1 ning natijasi, rasmlar esa
dissertatsiya matni tayyorlanayotganda, yakuniy demo bazasi ustida olinadi.
Shu papkaga qo‘yilgandan keyin ular `git add docs/ui/uz/` bilan kuzatiladi.
