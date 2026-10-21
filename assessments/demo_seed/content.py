"""
The two demo courses: tree, prerequisites and question bank (pure data).

Every slug starts with ``DEMO_PREFIX``. ``slugify`` collapses runs of dashes,
so no slug the platform derives from a name can start with ``demo--``; the
prefix is half of what tells demo nodes apart from everything else
(``store.py`` has the other half).

The prerequisite graph is built so that its longest chain is 5 topics
(4 edges), it has edges between sections, and three edges cross from
"Python dasturlash asoslari" into "Algoritmlar asoslari". Every question has
four choices and exactly one correct answer. Texts are plain (the frontend
does not render markdown), Uzbek Latin with ‘ for o‘/g‘ and ’ for the
glottal stop, as in the frontend's uz.json.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass

DEMO_PREFIX = "demo--"


@dataclass(frozen=True)
class QuestionSpec:
    difficulty: int  # assessments.models.DifficultyLevel: 1 easy, 2 medium, 3 hard
    text: str
    correct: str
    wrong: tuple[str, str, str]
    explanation: str

    def choices(self) -> list[tuple[str, bool]]:
        """The four choices; the correct one's place is fixed by the text, not by a seed."""
        slot = zlib.crc32(self.text.encode("utf-8")) % (len(self.wrong) + 1)
        options = [(text, False) for text in self.wrong]
        options.insert(slot, (self.correct, True))
        return options


@dataclass(frozen=True)
class TopicSpec:
    slug: str
    name: str
    description: str
    questions: tuple[QuestionSpec, ...]


@dataclass(frozen=True)
class SectionSpec:
    slug: str
    name: str
    description: str
    topics: tuple[TopicSpec, ...]


@dataclass(frozen=True)
class CourseSpec:
    slug: str
    name: str
    description: str
    instructor: str  # key of people.INSTRUCTORS
    sections: tuple[SectionSpec, ...]

    def topics(self) -> list[TopicSpec]:
        return [topic for section in self.sections for topic in section.topics]


def Q(difficulty: int, text: str, correct: str, wrong: tuple[str, str, str], explanation: str) -> QuestionSpec:
    return QuestionSpec(difficulty, text, correct, wrong, explanation)


# Item difficulty b_q at creation, by level; Elo moves it from there (3.3).
BASE_B = {1: -1.0, 2: 0.0, 3: 1.0}
B_STEP = 0.25


def initial_b(topic: TopicSpec, index: int) -> float:
    """b_q for the index-th question: the level's base, spread by ±B_STEP within the level."""
    level = topic.questions[index].difficulty
    rank = sum(1 for q in topic.questions[:index] if q.difficulty == level)
    return BASE_B[level] + ((rank % 3) - 1) * B_STEP


# ---------------------------------------------------------------------------
# Python dasturlash asoslari
# ---------------------------------------------------------------------------

PY_OZGARUVCHILAR = TopicSpec(
    "demo--py-ozgaruvchilar",
    "O‘zgaruvchilar va ma’lumot turlari",
    "O‘zgaruvchi yaratish, int, float, str va bool turlari, type() funksiyasi.",
    (
        Q(1, "Python’da x = 5 dan keyin type(x) nimani qaytaradi?",
          "<class 'int'>", ("<class 'float'>", "<class 'str'>", "<class 'number'>"),
          "5 butun son, shuning uchun uning turi int."),
        Q(1, "Quyidagilardan qaysi biri Python’da to‘g‘ri o‘zgaruvchi nomi?",
          "talaba_soni", ("2talaba", "talaba-soni", "class"),
          "Nom raqam bilan boshlanmaydi, chiziqcha ishlatilmaydi va kalit so‘z bo‘la olmaydi."),
        Q(2, "a = 7 / 2 dan keyin a ning qiymati qanday?",
          "3.5", ("3", "4", "3.0"),
          "/ operatori har doim float qaytaradi: 7 / 2 = 3.5."),
        Q(2, "int(\"12\") + 3 ifodasining natijasi nima?",
          "15", ("\"123\"", "TypeError xatosi", "\"15\""),
          "int() satrni butun songa aylantiradi, so‘ng 12 + 3 = 15."),
        Q(2, "bool(\"\") qanday qiymat qaytaradi?",
          "False", ("True", "None", "\"\""),
          "Bo‘sh satr mantiqiy kontekstda yolg‘on hisoblanadi."),
        Q(3, "x = 10, keyin y = x, so‘ng x = 20 bajarilsa, y ning qiymati qancha?",
          "10", ("20", "None", "30"),
          "y avvalgi 10 obyektiga bog‘langan; x ni qayta bog‘lash y ga ta’sir qilmaydi."),
        Q(3, "0.1 + 0.2 == 0.3 ifodasi nima qaytaradi?",
          "False", ("True", "TypeError xatosi", "0.3"),
          "Suzuvchi nuqtali sonlar ikkilik tizimda aniq ifodalanmaydi: 0.1 + 0.2 = 0.30000000000000004."),
    ),
)

PY_OPERATORLAR = TopicSpec(
    "demo--py-operatorlar",
    "Arifmetik va mantiqiy operatorlar",
    "+, -, *, /, //, %, ** operatorlari, taqqoslash va and, or, not.",
    (
        Q(1, "17 % 5 ning natijasi nima?",
          "2", ("3", "3.4", "12"),
          "% bo‘lishdan qolgan qoldiqni beradi: 17 = 3 · 5 + 2."),
        Q(1, "2 ** 3 nimaga teng?",
          "8", ("6", "9", "5"),
          "** daraja operatori: 2 ning kubi 8."),
        Q(2, "17 // 5 ning natijasi nima?",
          "3", ("3.4", "2", "4"),
          "// butun bo‘lish: kasr qismi tashlab yuboriladi."),
        Q(2, "not (3 > 2 and 2 > 5) qiymati qanday?",
          "True", ("False", "None", "Sintaksis xatosi"),
          "3 > 2 rost, 2 > 5 yolg‘on, and yolg‘on beradi, not uni rostga aylantiradi."),
        Q(2, "2 + 3 * 4 ifodasining qiymati qancha?",
          "14", ("20", "24", "9"),
          "Ko‘paytirish qo‘shishdan oldin bajariladi: 2 + 12 = 14."),
        Q(3, "-7 // 2 ning natijasi nima?",
          "-4", ("-3", "-3.5", "3"),
          "// manfiy cheksizlik tomon yaxlitlaydi: -3.5 dan -4 hosil bo‘ladi."),
        Q(3, "0 or \"salom\" ifodasi nimani qaytaradi?",
          "\"salom\"", ("True", "False", "0"),
          "or birinchi rost qiymatni qaytaradi; 0 yolg‘on bo‘lgani uchun \"salom\" qaytadi."),
        Q(3, "1 < 3 < 2 ifodasining qiymati qanday?",
          "False", ("True", "Sintaksis xatosi", "1"),
          "Zanjirli taqqoslash 1 < 3 and 3 < 2 deb o‘qiladi; ikkinchi qism yolg‘on."),
    ),
)

PY_KIRITISH = TopicSpec(
    "demo--py-kiritish-chiqarish",
    "Kiritish va chiqarish",
    "input() va print() funksiyalari, f-satrlar, sep va end parametrlari.",
    (
        Q(1, "Foydalanuvchidan klaviatura orqali ma’lumot olish uchun qaysi funksiya ishlatiladi?",
          "input()", ("print()", "read()", "scan()"),
          "input() foydalanuvchi kiritgan qatorni o‘qiydi."),
        Q(1, "print(\"A\", \"B\") ekranga nima chiqaradi?",
          "A B", ("AB", "A,B", "(\"A\", \"B\")"),
          "print argumentlar orasiga standart holatda bitta bo‘sh joy qo‘yadi."),
        Q(2, "input() funksiyasi qaytaradigan qiymatning turi qanday?",
          "har doim str", ("har doim int", "kiritilganiga qarab int yoki str", "bool"),
          "input() doim satr qaytaradi; son kerak bo‘lsa int() bilan aylantiriladi."),
        Q(2, "ism = \"Ali\" bo‘lsa, print(f\"Salom, {ism}!\") nima chiqaradi?",
          "Salom, Ali!", ("Salom, {ism}!", "Salom, ism!", "f\"Salom, Ali!\""),
          "f-satr ichidagi {ism} o‘zgaruvchining qiymati bilan almashtiriladi."),
        Q(2, "print(1, 2, 3, sep=\"-\") natijasi qanday?",
          "1-2-3", ("1 2 3", "-1-2-3-", "123-"),
          "sep argumentlar orasiga qo‘yiladigan ajratuvchini belgilaydi."),
        Q(3, "print(\"a\", end=\"\") dan keyin print(\"b\") bajarilsa, ekranda nima bo‘ladi?",
          "ab bitta qatorda", ("a va b alohida qatorlarda", "a b", "faqat b"),
          "end=\"\" qator oxiridagi yangi qator belgisini olib tashlaydi."),
        Q(3, "yosh = input() ga 17 kiritildi. yosh + 1 nima beradi?",
          "TypeError xatosi", ("18", "\"171\"", "\"18\""),
          "yosh satr; satr va sonni + bilan qo‘shib bo‘lmaydi."),
    ),
)

PY_SHARTLAR = TopicSpec(
    "demo--py-shartlar",
    "Shart operatorlari (if, elif, else)",
    "Tarmoqlanish: if, elif, else, ichma-ich shartlar va shartli ifoda.",
    (
        Q(1, "Python’da shart blokini qaysi kalit so‘z boshlaydi?",
          "if", ("when", "case", "switch"),
          "Shart if kalit so‘zi bilan boshlanadi."),
        Q(1, "if blokining tanasi Python’da qanday ajratiladi?",
          "chekinish (indentatsiya) bilan", ("jingalak qavslar bilan", "begin va end so‘zlari bilan", "nuqtali vergul bilan"),
          "Python bloklarni qator boshidagi chekinish bilan belgilaydi."),
        Q(2, "x = 7. Agar x > 10 bo‘lsa \"katta\", aks holda x > 5 bo‘lsa (elif) \"o‘rta\", aks holda \"kichik\" chiqariladi. Nima chiqadi?",
          "o‘rta", ("katta", "kichik", "o‘rta va kichik"),
          "Birinchi shart yolg‘on, elif dagi shart rost, shuning uchun faqat \"o‘rta\" chiqadi."),
        Q(2, "a = 4 uchun \"juft\" if a % 2 == 0 else \"toq\" ifodasining qiymati qanday?",
          "\"juft\"", ("\"toq\"", "True", "0"),
          "4 % 2 == 0 rost, shuning uchun shartli ifoda \"juft\" ni beradi."),
        Q(2, "Bir nechta shartdan faqat birinchi rost bo‘lganini bajarish uchun qaysi tuzilma ishlatiladi?",
          "if … elif … else", ("bir nechta alohida if", "while", "try … except"),
          "elif zanjiri birinchi rost shartdan keyin qolganlarini tekshirmaydi."),
        Q(3, "x = 0. \"if x:\" bloki \"A\" ni, else bloki \"B\" ni chiqaradi. Nima chiqadi?",
          "B", ("A", "hech narsa", "Xato"),
          "0 mantiqiy kontekstda yolg‘on, shuning uchun else bajariladi."),
        Q(3, "Qaysi shart n ning 1 dan 10 gacha (ikkalasi ham kiradi) ekanini to‘g‘ri tekshiradi?",
          "1 <= n <= 10", ("1 < n < 10", "n >= 1 or n <= 10", "n in (1, 10)"),
          "or har qanday son uchun rost; (1, 10) esa faqat ikki elementli kortej."),
    ),
)

PY_SIKLLAR = TopicSpec(
    "demo--py-sikllar",
    "Sikllar (for va while)",
    "for va while sikllari, range(), break va continue.",
    (
        Q(1, "range(5) qaysi sonlarni hosil qiladi?",
          "0, 1, 2, 3, 4", ("1, 2, 3, 4, 5", "0, 1, 2, 3, 4, 5", "faqat 5"),
          "range(n) 0 dan boshlanadi va n ni o‘z ichiga olmaydi."),
        Q(1, "Siklni muddatidan oldin to‘xtatish uchun qaysi operator ishlatiladi?",
          "break", ("continue", "pass", "return 0"),
          "break siklni darhol tugatadi."),
        Q(2, "for i in range(2, 10, 3) sikli qaysi i qiymatlaridan o‘tadi?",
          "2, 5, 8", ("2, 5, 8, 11", "3, 6, 9", "2, 3, 4"),
          "2 dan boshlab 3 qadam bilan, 10 ga yetmasdan: 2, 5, 8."),
        Q(2, "continue operatori nima qiladi?",
          "joriy iteratsiyaning qolganini o‘tkazib, keyingisiga o‘tadi",
          ("siklni butunlay to‘xtatadi", "dasturni tugatadi", "siklni boshidan qayta boshlaydi"),
          "continue faqat joriy aylanishni tugatadi, sikl davom etadi."),
        Q(2, "s = 0, so‘ng for i in range(1, 5) siklida s += i bajarilsa, s nechaga teng bo‘ladi?",
          "10", ("15", "4", "5"),
          "1 + 2 + 3 + 4 = 10; range(1, 5) 5 ni o‘z ichiga olmaydi."),
        Q(3, "i = 0 dan boshlab while i < 3 siklining tanasida faqat i += 1 bajarilsa, tana necha marta bajariladi?",
          "3", ("2", "4", "cheksiz"),
          "i 0, 1, 2 bo‘lganda tana bajariladi; i = 3 da shart yolg‘on bo‘ladi."),
        Q(3, "Quyidagilardan qaysi biri cheksiz siklga olib keladi?",
          "i = 1; while i > 0 siklida i += 1",
          ("for i in range(10) siklida pass", "i = 5; while i > 0 siklida i -= 1", "while False siklida pass"),
          "i doim musbat qoladi, shuning uchun shart hech qachon yolg‘on bo‘lmaydi."),
        Q(3, "for … else tuzilmasida else bloki qachon bajariladi?",
          "sikl break siz tugaganda", ("faqat sikl bir marta ham aylanmaganda", "break bajarilganda", "har bir iteratsiyadan keyin"),
          "else sikl oxirigacha yetib, break bilan uzilmagan bo‘lsa bajariladi."),
    ),
)

PY_SATRLAR = TopicSpec(
    "demo--py-satrlar",
    "Satrlar bilan ishlash",
    "Satr indekslari, kesmalar, satr metodlari va satrlarning o‘zgarmasligi.",
    (
        Q(1, "s = \"Python\" bo‘lsa, s[0] nima?",
          "\"P\"", ("\"y\"", "\"n\"", "IndexError"),
          "Indekslar 0 dan boshlanadi."),
        Q(1, "len(\"salom\") nechaga teng?",
          "5", ("4", "6", "\"salom\""),
          "len() satrdagi belgilar sonini qaytaradi."),
        Q(2, "\"Python\"[1:4] kesmasi nimani qaytaradi?",
          "\"yth\"", ("\"ytho\"", "\"Pyt\"", "\"yt\""),
          "Kesma 1-indeksdan boshlanadi va 4-indeksni o‘z ichiga olmaydi."),
        Q(2, "\"salom\".upper() natijasi qanday?",
          "\"SALOM\"", ("\"Salom\"", "\"salom\"", "None"),
          "upper() barcha harflarni bosh harfga aylantirgan yangi satr qaytaradi."),
        Q(2, "\"a,b,c\".split(\",\") nimani qaytaradi?",
          "[\"a\", \"b\", \"c\"]", ("\"abc\"", "(\"a\", \"b\", \"c\")", "[\"a,b,c\"]"),
          "split() satrni ajratuvchi bo‘yicha bo‘lib, ro‘yxat qaytaradi."),
        Q(3, "s = \"kitob\"; s[0] = \"K\" bajarilsa nima bo‘ladi?",
          "TypeError: satrlar o‘zgarmas", ("s \"Kitob\" ga aylanadi", "yangi satr yaratilib, s o‘zgaradi", "IndexError"),
          "Satr elementini joyida o‘zgartirib bo‘lmaydi; yangi satr yaratish kerak."),
        Q(3, "\"Python\"[::-1] nimani beradi?",
          "\"nohtyP\"", ("\"Python\"", "\"P\"", "\"n\""),
          "-1 qadamli kesma satrni teskari tartibda qaytaradi."),
    ),
)

PY_ROYXATLAR = TopicSpec(
    "demo--py-royxatlar",
    "Ro‘yxatlar va kortejlar",
    "list va tuple, indekslash, append, insert va pop, ro‘yxat generatorlari.",
    (
        Q(1, "Ro‘yxat oxiriga element qo‘shish uchun qaysi metod ishlatiladi?",
          "append()", ("add()", "push()", "insert_end()"),
          "append() elementni ro‘yxat oxiriga qo‘shadi."),
        Q(1, "a = [10, 20, 30] bo‘lsa, a[-1] nima?",
          "30", ("10", "20", "IndexError"),
          "Manfiy indeks oxirdan sanaydi: -1 oxirgi element."),
        Q(2, "Ro‘yxat va kortejning asosiy farqi nimada?",
          "ro‘yxat o‘zgaruvchan, kortej o‘zgarmas",
          ("kortej faqat sonlarni saqlaydi", "ro‘yxat tartiblanmagan", "kortejning uzunligi doim 2"),
          "list ni yaratilgandan keyin o‘zgartirish mumkin, tuple ni esa yo‘q."),
        Q(2, "[x * 2 for x in range(3)] nimani hosil qiladi?",
          "[0, 2, 4]", ("[2, 4, 6]", "[0, 1, 2, 0, 1, 2]", "[0, 2, 4, 6]"),
          "range(3) 0, 1, 2 ni beradi; har biri 2 ga ko‘paytiriladi."),
        Q(2, "a = [1, 2, 3]; a.pop() dan keyin a qanday bo‘ladi?",
          "[1, 2]", ("[2, 3]", "[1, 2, 3]", "[]"),
          "Argumentsiz pop() oxirgi elementni olib tashlaydi."),
        Q(3, "a = [1, 2]; b = a; b.append(3) dan keyin a nima?",
          "[1, 2, 3]", ("[1, 2]", "[3]", "Xato"),
          "b va a bitta ro‘yxat obyektiga ishora qiladi."),
        Q(3, "[1, 2, 3, 4, 5][1::2] nimani qaytaradi?",
          "[2, 4]", ("[1, 3, 5]", "[2, 3]", "[1, 2]"),
          "1-indeksdan boshlab har ikkinchi element olinadi."),
        Q(3, "Bitta elementli kortej qanday yoziladi?",
          "(5,)", ("(5)", "[5]", "tuple 5"),
          "(5) shunchaki qavsdagi son; kortej uchun vergul kerak."),
    ),
)

PY_LUGATLAR = TopicSpec(
    "demo--py-lugatlar",
    "Lug‘atlar va to‘plamlar",
    "dict va set: kalit va qiymat juftlari, get(), items(), to‘plam amallari.",
    (
        Q(1, "d = {\"a\": 1, \"b\": 2} bo‘lsa, d[\"b\"] nima?",
          "2", ("1", "\"b\"", "KeyError"),
          "Lug‘atdan qiymat kalit bo‘yicha olinadi."),
        Q(1, "Takrorlanmaydigan elementlar to‘plamini saqlash uchun qaysi tur mos?",
          "set", ("list", "tuple", "str"),
          "set har bir elementni bir marta saqlaydi."),
        Q(2, "Kalit \"x\" mavjud bo‘lmasa, d.get(\"x\", 0) nima qaytaradi?",
          "0", ("KeyError", "None", "\"x\""),
          "get() kalit topilmasa ikkinchi argumentni qaytaradi."),
        Q(2, "len({1, 2, 2, 3, 3, 3}) nechaga teng?",
          "3", ("6", "4", "1"),
          "To‘plamda takrorlar saqlanmaydi: {1, 2, 3}."),
        Q(2, "Lug‘atni kalit va qiymat juftlari bo‘yicha aylanish uchun qaysi metod ishlatiladi?",
          "items()", ("keys()", "pairs()", "values()"),
          "items() (kalit, qiymat) juftlarini beradi."),
        Q(3, "Quyidagilardan qaysi biri lug‘at kaliti bo‘la olmaydi?",
          "[1, 2] ro‘yxati", ("(1, 2) korteji", "\"ism\" satri", "42 soni"),
          "Kalit xeshlanadigan bo‘lishi kerak; ro‘yxat o‘zgaruvchan, shuning uchun xeshlanmaydi."),
        Q(3, "{1, 2, 3} & {2, 3, 4} natijasi nima?",
          "{2, 3}", ("{1, 2, 3, 4}", "{1, 4}", "{1}"),
          "& to‘plamlar kesishmasini beradi."),
    ),
)

PY_FUNKSIYALAR = TopicSpec(
    "demo--py-funksiyalar",
    "Funksiyalarni aniqlash va chaqirish",
    "def, parametrlar va argumentlar, return, standart qiymatlar, ko‘rinish sohasi.",
    (
        Q(1, "Python’da funksiya qaysi kalit so‘z bilan aniqlanadi?",
          "def", ("function", "func", "fn"),
          "Funksiya def kalit so‘zi bilan aniqlanadi."),
        Q(1, "return operatori yo‘q funksiya nimani qaytaradi?",
          "None", ("0", "\"\"", "oxirgi hisoblangan qiymat"),
          "return bo‘lmasa funksiya None qaytaradi."),
        Q(2, "def f(a, b=2): return a * b bo‘lsa, f(3) nechaga teng?",
          "6", ("3", "5", "TypeError"),
          "b berilmagani uchun standart qiymat 2 ishlatiladi: 3 · 2 = 6."),
        Q(2, "def f(x): x = x + 1. n = 5; f(n) dan keyin n qancha?",
          "5", ("6", "None", "Xato"),
          "Funksiya ichidagi x mahalliy nom; n ning qiymati o‘zgarmaydi."),
        Q(2, "Funksiya ichida yaratilgan o‘zgaruvchi qayerda ko‘rinadi?",
          "faqat shu funksiya ichida", ("butun dasturda", "faqat modul boshida", "funksiya chaqirilgandan keyin hamma joyda"),
          "Mahalliy o‘zgaruvchilar funksiya tugaganda yo‘qoladi."),
        Q(3, "def f(*args): return len(args) bo‘lsa, f(1, 2, 3) nima qaytaradi?",
          "3", ("1", "6", "(1, 2, 3)"),
          "*args barcha pozitsion argumentlarni kortejga yig‘adi."),
        Q(3, "sq = lambda x: x * x bo‘lsa, sq(4) nima?",
          "16", ("8", "4", "lambda obyekti"),
          "lambda qisqa nomsiz funksiya; 4 · 4 = 16."),
        Q(3, "def f(a, lst=[]): lst.append(a); return lst. f(1) dan keyin f(2) nima qaytaradi?",
          "[1, 2]", ("[2]", "[1]", "[]"),
          "Standart qiymat bir marta yaratiladi va chaqiruvlar orasida saqlanib qoladi."),
    ),
)

PY_REKURSIYA = TopicSpec(
    "demo--py-rekursiya",
    "Rekursiya",
    "O‘zini chaqiradigan funksiya, bazaviy holat, chaqiruvlar steki va chuqurlik.",
    (
        Q(1, "Rekursiv funksiya deb nimaga aytiladi?",
          "o‘zini o‘zi chaqiradigan funksiyaga",
          ("faqat sikl ishlatadigan funksiyaga", "hech narsa qaytarmaydigan funksiyaga", "boshqa moduldan import qilingan funksiyaga"),
          "Rekursiv funksiya masalani o‘zining kichikroq nusxasiga keltiradi."),
        Q(1, "Rekursiyada bazaviy holat nima uchun kerak?",
          "rekursiyani to‘xtatish uchun", ("funksiyani tezlashtirish uchun", "xotirani tozalash uchun", "argumentlarni tekshirish uchun"),
          "Bazaviy holatsiz chaqiruvlar hech qachon tugamaydi."),
        Q(2, "def f(n): return 1 if n == 0 else n * f(n - 1) bo‘lsa, f(4) nechaga teng?",
          "24", ("10", "4", "120"),
          "Bu faktorial: 4 · 3 · 2 · 1 = 24."),
        Q(2, "Bazaviy holati yo‘q rekursiv funksiya chaqirilsa nima bo‘ladi?",
          "RecursionError: chuqurlik chegarasi oshadi",
          ("funksiya 0 qaytaradi", "dastur jimgina abadiy ishlaydi", "SyntaxError"),
          "Python rekursiya chuqurligini cheklaydi va chegaradan oshganda xato beradi."),
        Q(2, "def s(n): return 0 if n == 0 else n + s(n - 1) bo‘lsa, s(3) nima?",
          "6", ("3", "9", "0"),
          "3 + 2 + 1 + 0 = 6."),
        Q(3, "Fibonachchi sonlarini fib(n) = fib(n-1) + fib(n-2) bilan to‘g‘ridan-to‘g‘ri hisoblashning vaqt murakkabligi qanday?",
          "eksponensial, taxminan O(2ⁿ)", ("O(n)", "O(log n)", "O(n²)"),
          "Bir xil qiymatlar qayta-qayta hisoblanadi, chaqiruvlar soni eksponensial o‘sadi."),
        Q(3, "Har bir rekursiv chaqiruv haqidagi ma’lumot qayerda saqlanadi?",
          "chaqiruvlar stekida", ("navbatda", "lug‘atda", "diskdagi faylda"),
          "Har chaqiruv stekka yangi kadr qo‘shadi va qaytganda olib tashlanadi."),
    ),
)

PY_ISTISNOLAR = TopicSpec(
    "demo--py-istisnolar",
    "Istisnolarni qayta ishlash",
    "try, except, else, finally; ValueError, ZeroDivisionError va raise.",
    (
        Q(1, "Xato yuz berishi mumkin bo‘lgan kod qaysi blokka yoziladi?",
          "try", ("except", "finally", "catch"),
          "Xavfli kod try blokiga, xatoni ushlash except blokiga yoziladi."),
        Q(1, "10 / 0 qaysi istisnoni keltirib chiqaradi?",
          "ZeroDivisionError", ("ValueError", "TypeError", "OverflowError"),
          "Nolga bo‘lish ZeroDivisionError beradi."),
        Q(2, "int(\"abc\") qaysi istisnoni beradi?",
          "ValueError", ("TypeError", "NameError", "KeyError"),
          "Tur to‘g‘ri (satr), lekin qiymatni songa aylantirib bo‘lmaydi."),
        Q(2, "finally bloki qachon bajariladi?",
          "har doim, xato bo‘lsa ham, bo‘lmasa ham",
          ("faqat xato bo‘lganda", "faqat xato bo‘lmaganda", "return bo‘lsa hech qachon"),
          "finally resurslarni bo‘shatish uchun har doim bajariladi."),
        Q(2, "Istisnoni o‘zingiz qo‘zg‘atish uchun qaysi kalit so‘z ishlatiladi?",
          "raise", ("throw", "error", "except"),
          "raise ValueError(\"...\") kabi yoziladi."),
        Q(3, "try … except … else tuzilmasida else bloki qachon bajariladi?",
          "try blokida xato bo‘lmaganda", ("xato bo‘lganda", "har doim", "except dan oldin har doim"),
          "else faqat try muvaffaqiyatli tugaganda ishlaydi."),
        Q(3, "Nega turini ko‘rsatmasdan \"except:\" yozish odatda yomon amaliyot hisoblanadi?",
          "u barcha xatolarni, jumladan kutilmaganlarini ham yashiradi",
          ("u sintaksis xatosi", "u faqat ValueError ni ushlaydi", "u dasturni sekinlashtiradi"),
          "Kutilmagan xatolar ham jimgina yutilib, nosozlikni topish qiyinlashadi."),
    ),
)

PY_FAYLLAR = TopicSpec(
    "demo--py-fayllar",
    "Fayllar bilan ishlash",
    "open(), o‘qish va yozish rejimlari, with konstruksiyasi, satrma-satr o‘qish.",
    (
        Q(1, "Faylni faqat o‘qish uchun ochish rejimi qaysi?",
          "\"r\"", ("\"w\"", "\"a\"", "\"x\""),
          "\"r\" standart rejim: faqat o‘qish."),
        Q(1, "with open(...) as f: yozuvining afzalligi nimada?",
          "fayl blokdan chiqqanda avtomatik yopiladi", ("fayl tezroq o‘qiladi", "fayl shifrlanadi", "faylning nusxasi yaratiladi"),
          "with xato bo‘lsa ham faylni yopadi."),
        Q(2, "Mavjud fayl \"w\" rejimida ochilsa nima bo‘ladi?",
          "uning eski mazmuni o‘chiriladi", ("matn oxiriga qo‘shiladi", "xato beriladi", "fayl faqat o‘qiladi"),
          "\"w\" faylni bo‘shatib, boshidan yozadi."),
        Q(2, "Faylning oxiriga yozish uchun qaysi rejim ishlatiladi?",
          "\"a\"", ("\"w\"", "\"r\"", "\"x\""),
          "\"a\" (append) yangi matnni oxiriga qo‘shadi."),
        Q(2, "f.readlines() nimani qaytaradi?",
          "satrlar ro‘yxatini", ("bitta satrni", "fayl hajmini", "faqat birinchi satrni"),
          "readlines() har bir satrni ro‘yxat elementi qilib qaytaradi."),
        Q(3, "Mavjud bo‘lmagan fayl open(\"yoq.txt\") bilan ochilsa qaysi istisno chiqadi?",
          "FileNotFoundError", ("ValueError", "PermissionError", "KeyError"),
          "O‘qish rejimida fayl topilmasa FileNotFoundError beriladi."),
        Q(3, "Katta faylni xotirani tejab satrma-satr qayta ishlashning to‘g‘ri usuli qaysi?",
          "for line in f: …", ("f.read() ni bir marta chaqirish", "f.readlines()[0]", "f.write(line)"),
          "Fayl obyekti bo‘yicha aylanish satrlarni birma-bir o‘qiydi."),
    ),
)

PYTHON = CourseSpec(
    "demo--python-asoslari",
    "Python dasturlash asoslari",
    "Python tilida dasturlashning asoslari: o‘zgaruvchilar, boshqaruv tuzilmalari, "
    "ma’lumotlar tuzilmalari, funksiyalar, istisnolar va fayllar.",
    "python",
    (
        SectionSpec("demo--py-kirish", "Python bilan tanishuv",
                    "Birinchi qadamlar: qiymatlar, ifodalar, kiritish va chiqarish.",
                    (PY_OZGARUVCHILAR, PY_OPERATORLAR, PY_KIRITISH)),
        SectionSpec("demo--py-boshqaruv", "Boshqaruv tuzilmalari",
                    "Dastur oqimini boshqarish: shartlar va sikllar.",
                    (PY_SHARTLAR, PY_SIKLLAR)),
        SectionSpec("demo--py-tuzilmalar", "Ma’lumotlar tuzilmalari",
                    "Satrlar, ro‘yxatlar, kortejlar, lug‘atlar va to‘plamlar.",
                    (PY_SATRLAR, PY_ROYXATLAR, PY_LUGATLAR)),
        SectionSpec("demo--py-funksiya-bolimi", "Funksiyalar",
                    "Kodni qayta ishlatish: funksiyalar va rekursiya.",
                    (PY_FUNKSIYALAR, PY_REKURSIYA)),
        SectionSpec("demo--py-xatolar-fayllar", "Xatolar va fayllar",
                    "Istisnolarni ushlash va fayllar bilan ishlash.",
                    (PY_ISTISNOLAR, PY_FAYLLAR)),
    ),
)


# ---------------------------------------------------------------------------
# Algoritmlar asoslari
# ---------------------------------------------------------------------------

ALG_MURAKKABLIK = TopicSpec(
    "demo--alg-murakkablik",
    "Algoritm murakkabligi (Big-O)",
    "Vaqt va xotira murakkabligi: O(1), O(log n), O(n), O(n log n), O(n²).",
    (
        Q(1, "Ro‘yxat elementiga indeks orqali murojaat qilishning vaqt murakkabligi qanday?",
          "O(1)", ("O(n)", "O(log n)", "O(n²)"),
          "Indeks bo‘yicha murojaat ro‘yxat uzunligiga bog‘liq emas."),
        Q(1, "n elementli ro‘yxatni bir marta to‘liq aylanib chiqish murakkabligi qanday?",
          "O(n)", ("O(1)", "O(n²)", "O(log n)"),
          "Har bir element bir martadan ko‘riladi."),
        Q(2, "Har biri n marta aylanadigan ikki ichma-ich sikl murakkabligi qanday?",
          "O(n²)", ("O(2n)", "O(n)", "O(n log n)"),
          "Ichki sikl tashqi siklning har bir qadamida n marta bajariladi."),
        Q(2, "Quyidagilardan qaysi biri eng tez o‘sadi?",
          "O(2ⁿ)", ("O(n²)", "O(n log n)", "O(n)"),
          "Eksponensial funksiya har qanday ko‘phaddan tez o‘sadi."),
        Q(2, "Big-O belgisi odatda nimani ifodalaydi?",
          "o‘sish tezligining yuqori chegarasini (odatda eng yomon holatda)",
          ("aniq ishlash vaqtini soniyalarda", "faqat eng yaxshi holatni", "kod qatorlari sonini"),
          "Big-O kirish hajmi o‘sganda vaqt qanday o‘sishini baholaydi."),
        Q(3, "3n² + 5n + 100 funksiyasining Big-O bahosi qanday?",
          "O(n²)", ("O(3n²)", "O(n² + n)", "O(100)"),
          "Eng tez o‘suvchi had qoladi, koeffitsiyentlar tashlab yuboriladi."),
        Q(3, "Har qadamda masala hajmini ikki marta kamaytiradigan algoritm murakkabligi qanday?",
          "O(log n)", ("O(n)", "O(n/2)", "O(n log n)"),
          "n ni 1 ga yetguncha ikkiga bo‘lish log₂ n qadam oladi."),
    ),
)

ALG_CHIZIQLI = TopicSpec(
    "demo--alg-chiziqli-qidiruv",
    "Chiziqli qidiruv",
    "Elementlarni birma-bir tekshirish; eng yaxshi, o‘rtacha va eng yomon holat.",
    (
        Q(1, "Chiziqli qidiruv qanday ishlaydi?",
          "elementlarni boshidan birma-bir tekshiradi",
          ("ro‘yxatni ikkiga bo‘lib qidiradi", "faqat oxirgi elementni tekshiradi", "avval saralaydi, keyin qidiradi"),
          "Chiziqli qidiruv kerakli element topilguncha ketma-ket yuradi."),
        Q(1, "Chiziqli qidiruv ro‘yxat saralangan bo‘lishini talab qiladimi?",
          "yo‘q, istalgan ro‘yxatda ishlaydi", ("ha, har doim", "faqat sonli ro‘yxatda", "faqat kamayish tartibida"),
          "Har bir element tekshirilgani uchun tartib muhim emas."),
        Q(2, "Chiziqli qidiruvning eng yomon holatdagi murakkabligi qanday?",
          "O(n)", ("O(1)", "O(log n)", "O(n²)"),
          "Eng yomon holatda barcha n element tekshiriladi."),
        Q(2, "Qidirilgan element ro‘yxatning birinchi elementi bo‘lsa, nechta taqqoslash bajariladi?",
          "1", ("n", "n/2", "0"),
          "Bu eng yaxshi holat: birinchi taqqoslashdayoq topiladi."),
        Q(2, "Element ro‘yxatda yo‘q bo‘lsa, n elementli ro‘yxatda nechta taqqoslash bo‘ladi?",
          "n", ("1", "n/2", "log n"),
          "Yo‘qligini bilish uchun hamma elementni ko‘rish kerak."),
        Q(3, "Element tasodifiy joyda bo‘lsa, o‘rtacha taqqoslashlar soni taxminan qancha?",
          "n/2", ("log n", "1", "n²"),
          "O‘rtacha holatda ro‘yxatning yarmi ko‘riladi."),
        Q(3, "Python’dagi x in royxat ifodasi ro‘yxat uchun qaysi qidiruvga mos keladi?",
          "chiziqli qidiruv, O(n)", ("ikkilik qidiruv, O(log n)", "xesh bo‘yicha qidiruv, O(1)", "graf bo‘yicha qidiruv"),
          "Ro‘yxatda in operatori elementlarni ketma-ket tekshiradi."),
    ),
)

ALG_IKKILIK = TopicSpec(
    "demo--alg-ikkilik-qidiruv",
    "Ikkilik qidiruv",
    "Saralangan massivda qidiruv oralig‘ini har qadamda ikkiga bo‘lish.",
    (
        Q(1, "Ikkilik qidiruv uchun massiv qanday bo‘lishi kerak?",
          "saralangan", ("teskari tartibda yozilgan", "faqat juft uzunlikda", "takrorlanuvchi elementlarsiz"),
          "Oraliqni tashlab yuborish faqat tartib bo‘lganda to‘g‘ri."),
        Q(1, "Ikkilik qidiruv har qadamda nimani tekshiradi?",
          "oraliqning o‘rtasidagi elementni", ("birinchi elementni", "oxirgi elementni", "tasodifiy elementni"),
          "O‘rtadagi element oraliqni ikkiga ajratadi."),
        Q(2, "Ikkilik qidiruvning vaqt murakkabligi qanday?",
          "O(log n)", ("O(n)", "O(1)", "O(n log n)"),
          "Har qadamda oraliq ikki marta qisqaradi."),
        Q(2, "1024 elementli saralangan massivda ikkilik qidiruv eng ko‘pi bilan taxminan nechta qadam qiladi?",
          "10–11", ("512", "1024", "32"),
          "log₂ 1024 = 10."),
        Q(2, "O‘rtadagi element qidirilgandan katta bo‘lsa, qidiruv qayerda davom etadi?",
          "chap yarmida", ("o‘ng yarmida", "boshidan qayta", "ikkala yarmida ham"),
          "Saralangan massivda kichik qiymatlar chapda joylashgan."),
        Q(3, "mid = (lo + hi) // 2 da lo = 3, hi = 8 bo‘lsa, mid nechaga teng?",
          "5", ("5.5", "6", "4"),
          "(3 + 8) // 2 = 11 // 2 = 5."),
        Q(3, "Saralanmagan massivga ikkilik qidiruv qo‘llansa nima bo‘ladi?",
          "natija noto‘g‘ri bo‘lishi mumkin", ("u avtomatik saralaydi", "u chiziqli qidiruvga aylanadi", "har doim xato beradi"),
          "Algoritm tartibga tayanadi; tartib bo‘lmasa kerakli yarmini tashlab yuborishi mumkin."),
        Q(3, "Python’dagi bisect moduli qaysi algoritmga asoslangan?",
          "ikkilik qidiruv", ("chiziqli qidiruv", "birlashtirib saralash", "BFS"),
          "bisect saralangan ro‘yxatda joyni ikkilik qidiruv bilan topadi."),
    ),
)

ALG_PUFAKCHALI = TopicSpec(
    "demo--alg-pufakchali",
    "Pufakchali va tanlab saralash",
    "Qo‘shni elementlarni almashtirish (bubble sort) va eng kichikni tanlash (selection sort).",
    (
        Q(1, "Pufakchali saralash qanday ishlaydi?",
          "qo‘shni elementlarni taqqoslab, noto‘g‘ri tartibdagilarini almashtiradi",
          ("massivni ikkiga bo‘lib birlashtiradi", "tayanch element atrofida bo‘ladi", "elementlarni xesh-jadvalga joylaydi"),
          "Katta elementlar har o‘tishda oxirga \"suzib chiqadi\"."),
        Q(1, "Pufakchali saralashning eng yomon holatdagi murakkabligi qanday?",
          "O(n²)", ("O(n log n)", "O(n)", "O(log n)"),
          "n ta o‘tish, har birida n ga yaqin taqqoslash."),
        Q(2, "Tanlab saralashda (selection sort) har o‘tishda nima qilinadi?",
          "qolgan qismdagi eng kichik element topilib, o‘z joyiga qo‘yiladi",
          ("qo‘shni juftlar almashtiriladi", "massiv ikkiga bo‘linadi", "element saralangan qismga suriladi"),
          "Har o‘tish saralangan qismni bitta elementga uzaytiradi."),
        Q(2, "[3, 1, 2] ustida pufakchali saralashning birinchi to‘liq o‘tishidan keyin massiv qanday bo‘ladi?",
          "[1, 2, 3]", ("[1, 3, 2]", "[3, 2, 1]", "[2, 1, 3]"),
          "3 va 1 almashadi, keyin 3 va 2 almashadi."),
        Q(2, "Pufakchali saralashning birinchi o‘tishidan keyin eng katta element qayerda bo‘ladi?",
          "massiv oxirida", ("massiv boshida", "o‘rtada", "noma’lum joyda"),
          "Eng katta element har taqqoslashda o‘ngga suriladi."),
        Q(3, "Almashtirish bo‘lmasa to‘xtaydigan pufakchali saralashning saralangan massivdagi murakkabligi qanday?",
          "O(n)", ("O(n²)", "O(log n)", "O(1)"),
          "Bitta o‘tishda almashtirish bo‘lmasa, algoritm to‘xtaydi."),
        Q(3, "Tanlab saralash nechta almashtirish (swap) bajaradi?",
          "ko‘pi bilan n − 1 ta", ("har doim n² ta", "taxminan n log n ta", "nolta"),
          "Har o‘tishda ko‘pi bilan bitta almashtirish bo‘ladi."),
    ),
)

ALG_JOYLASHTIRIB = TopicSpec(
    "demo--alg-joylashtirib",
    "Joylashtirib saralash",
    "Har bir elementni saralangan qismdagi o‘z joyiga qo‘yish (insertion sort).",
    (
        Q(1, "Joylashtirib saralash qaysi kundalik ishga o‘xshaydi?",
          "qo‘ldagi kartalarni birma-bir tartib bilan joylashga",
          ("kitoblarni tasodifiy taxlashga", "ro‘yxatni ikkiga bo‘lishga", "sonlarni yig‘ishga"),
          "Har yangi karta allaqachon tartiblangan kartalar orasiga qo‘yiladi."),
        Q(1, "Joylashtirib saralashning eng yomon holatdagi murakkabligi qanday?",
          "O(n²)", ("O(n log n)", "O(n)", "O(1)"),
          "Teskari tartibli massivda har element boshigacha suriladi."),
        Q(2, "Joylashtirib saralash qachon ayniqsa tez ishlaydi?",
          "massiv deyarli saralangan bo‘lsa", ("massiv teskari tartibda bo‘lsa", "elementlar juda katta bo‘lsa", "massiv juda uzun bo‘lsa"),
          "Elementlar o‘z joyiga yaqin bo‘lsa, kam surish kerak bo‘ladi."),
        Q(2, "[1, 3, 5, 2] da oxirgi element 2 joylashtirilgandan keyin massiv qanday bo‘ladi?",
          "[1, 2, 3, 5]", ("[2, 1, 3, 5]", "[1, 3, 2, 5]", "[1, 3, 5, 2]"),
          "2 o‘zidan katta 5 va 3 dan oldinga, 1 dan keyin qo‘yiladi."),
        Q(2, "Joylashtirib saralash qo‘shimcha qancha xotira talab qiladi?",
          "O(1)", ("O(n)", "O(log n)", "O(n²)"),
          "Saralash massivning o‘zida bajariladi."),
        Q(3, "Barqaror (stable) saralash nima?",
          "teng elementlarning dastlabki nisbiy tartibi saqlanadi",
          ("har doim O(n log n) da ishlaydi", "qo‘shimcha xotira ishlatmaydi", "faqat sonlarni saralaydi"),
          "Joylashtirib saralash barqaror: teng elementlar bir-biridan o‘tmaydi."),
        Q(3, "Allaqachon saralangan massivda joylashtirib saralash nechta taqqoslash bajaradi?",
          "n − 1 ta", ("n² ta", "0 ta", "n log n ta"),
          "Har bir element faqat oldingisi bilan bir marta taqqoslanadi."),
    ),
)

ALG_BIRLASHTIRIB = TopicSpec(
    "demo--alg-birlashtirib",
    "Birlashtirib saralash (merge sort)",
    "Bo‘l va hukmronlik qil: massivni yarmiga bo‘lib, rekursiv saralab birlashtirish.",
    (
        Q(1, "Birlashtirib saralash qaysi yondashuvga asoslangan?",
          "bo‘l va hukmronlik qil", ("ochko‘z (greedy) algoritm", "dinamik dasturlash", "tasodifiy tanlash"),
          "Masala ikki yarimga bo‘linadi, har biri alohida yechilib birlashtiriladi."),
        Q(1, "Birlashtirib saralashning vaqt murakkabligi qanday?",
          "O(n log n)", ("O(n²)", "O(n)", "O(log n)"),
          "log n daraja, har darajada O(n) birlashtirish."),
        Q(2, "Saralangan [1, 4] va [2, 3] birlashtirilsa nima hosil bo‘ladi?",
          "[1, 2, 3, 4]", ("[1, 4, 2, 3]", "[2, 3, 1, 4]", "[4, 3, 2, 1]"),
          "Har qadamda ikki ro‘yxat boshidagi kichigi olinadi."),
        Q(2, "Birlashtirib saralashning rekursiyasi qachon to‘xtaydi?",
          "qism massivda bitta yoki nolta element qolganda",
          ("massiv doim ikki elementli bo‘lganda", "tayanch element topilganda", "hech qachon"),
          "Bitta elementli massiv allaqachon saralangan — bu bazaviy holat."),
        Q(2, "Birlashtirib saralash qo‘shimcha qancha xotira talab qiladi?",
          "O(n)", ("O(1)", "O(log n)", "O(n²)"),
          "Birlashtirish uchun vaqtinchalik massiv kerak."),
        Q(3, "Birlashtirib saralashning rekursiya chuqurligi qancha?",
          "taxminan log₂ n", ("n", "n/2", "1"),
          "Har darajada massiv ikki marta kichrayadi."),
        Q(3, "Birlashtirib saralashning eng yomon holatdagi murakkabligi qanday?",
          "O(n log n), eng yaxshi holat bilan bir xil", ("O(n²)", "O(n)", "O(2ⁿ)"),
          "Bo‘linish kirish ma’lumotiga bog‘liq emas, shuning uchun baho har doim bir xil."),
    ),
)

ALG_TEZ = TopicSpec(
    "demo--alg-tez-saralash",
    "Tez saralash (quick sort)",
    "Tayanch (pivot) element atrofida bo‘lish va qismlarni rekursiv saralash.",
    (
        Q(1, "Tez saralashda massiv nima atrofida bo‘linadi?",
          "tayanch (pivot) element", ("doim o‘rtadagi indeks", "eng katta element", "birinchi va oxirgi elementlar yig‘indisi"),
          "Tayanchdan kichiklar bir tomonga, kattalar boshqa tomonga o‘tadi."),
        Q(1, "Tez saralashning o‘rtacha vaqt murakkabligi qanday?",
          "O(n log n)", ("O(n²)", "O(n)", "O(log n)"),
          "O‘rtacha holatda bo‘linishlar muvozanatli bo‘ladi."),
        Q(2, "Tez saralashning eng yomon holatdagi murakkabligi qanday?",
          "O(n²)", ("O(n log n)", "O(n)", "O(2ⁿ)"),
          "Tayanch har safar eng chekka qiymat bo‘lsa, bo‘linish muvozanatsiz bo‘ladi."),
        Q(2, "Tayanch sifatida doim birinchi element olinsa, qaysi kirishda eng yomon holat yuz beradi?",
          "allaqachon saralangan massivda", ("tasodifiy massivda", "teng qismlar hosil bo‘lganda", "bo‘sh massivda"),
          "Saralangan massivda birinchi element doim eng kichigi bo‘ladi."),
        Q(2, "Bo‘lishdan keyin tayanchdan chapdagi elementlar qanday bo‘ladi?",
          "tayanchdan kichik yoki unga teng", ("tayanchdan katta", "tasodifiy", "saralangan bo‘lishi shart"),
          "Bo‘lish qadami aynan shu xossani ta’minlaydi."),
        Q(3, "Eng yomon holatdan saqlanishning keng tarqalgan usuli qaysi?",
          "tayanchni tasodifiy yoki uchta qiymat medianasi bilan tanlash",
          ("doim birinchi elementni olish", "rekursiyani olib tashlash", "massivni teskari aylantirish"),
          "Bunday tanlov muvozanatsiz bo‘linish ehtimolini kamaytiradi."),
        Q(3, "Tez saralash barqaror (stable) saralashmi?",
          "odatiy joyida (in-place) ko‘rinishida yo‘q", ("ha, har doim", "faqat sonlar uchun ha", "faqat juft uzunlikda ha"),
          "Bo‘lishdagi almashtirishlar teng elementlar tartibini buzishi mumkin."),
    ),
)

ALG_STEK = TopicSpec(
    "demo--alg-stek-navbat",
    "Stek va navbat",
    "LIFO va FIFO tamoyillari, push va pop, navbatga qo‘shish va olish, collections.deque.",
    (
        Q(1, "Stek qaysi tamoyil asosida ishlaydi?",
          "LIFO: oxirgi kirgan birinchi chiqadi", ("FIFO: birinchi kirgan birinchi chiqadi", "tasodifiy tartib", "saralangan tartib"),
          "Stekda faqat ustki elementga murojaat qilinadi."),
        Q(1, "Navbat (queue) qaysi tamoyilga bo‘ysunadi?",
          "FIFO", ("LIFO", "eng kattasi birinchi", "eng kichigi birinchi"),
          "Navbatda birinchi qo‘shilgan element birinchi olinadi."),
        Q(2, "Bo‘sh stekka 1, 2, 3 qo‘shilib, bitta pop bajarilsa, qaysi element olinadi?",
          "3", ("1", "2", "hammasi"),
          "Oxirgi qo‘shilgan element birinchi olinadi."),
        Q(2, "Python’da navbatni samarali amalga oshirish uchun qaysi tuzilma tavsiya etiladi?",
          "collections.deque", ("pop(0) bilan oddiy ro‘yxat", "dict", "set"),
          "deque ikki uchidan ham O(1) da qo‘shish va olishga imkon beradi."),
        Q(2, "Brauzerdagi \"Orqaga\" tugmasi tarixini saqlash uchun qaysi tuzilma mos?",
          "stek", ("navbat", "to‘plam", "lug‘at"),
          "Eng oxirgi ochilgan sahifaga birinchi qaytiladi."),
        Q(3, "Qavslar muvozanatini, masalan (()()), tekshirish uchun qaysi tuzilma ishlatiladi?",
          "stek", ("navbat", "ikkilik qidiruv daraxti", "xesh-jadval"),
          "Ochuvchi qavs stekka qo‘yiladi, yopuvchisi uni olib tashlaydi."),
        Q(3, "Ro‘yxatda pop(0) amalining murakkabligi qanday?",
          "O(n)", ("O(1)", "O(log n)", "O(n²)"),
          "Birinchi element olingach, qolganlari bir pog‘ona chapga suriladi."),
    ),
)

ALG_GRAFLAR = TopicSpec(
    "demo--alg-graflar",
    "Graflar va ularni ifodalash",
    "Uchlar va qirralar, yo‘naltirilgan va yo‘naltirilmagan graflar, qo‘shnilik ro‘yxati va matritsasi.",
    (
        Q(1, "Graf nimalardan tashkil topadi?",
          "uchlar va qirralardan", ("faqat ildiz va barglardan", "kalit va qiymatlardan", "satr va ustunlardan"),
          "Graf G = (V, E): uchlar to‘plami va ularni bog‘lovchi qirralar."),
        Q(1, "Yo‘naltirilgan grafda qirra qanday bo‘ladi?",
          "bir uchdan ikkinchisiga yo‘nalishga ega", ("har doim ikki tomonlama", "vaznsiz bo‘lishi shart", "faqat o‘z-o‘ziga"),
          "u → v qirrasi v → u ni anglatmaydi."),
        Q(2, "n uchli graf uchun qo‘shnilik matritsasi qancha xotira egallaydi?",
          "O(n²)", ("O(n)", "O(n + m)", "O(log n)"),
          "Matritsa n × n o‘lchamli."),
        Q(2, "Siyrak (qirralari kam) graf uchun qaysi ifodalash xotirani tejaydi?",
          "qo‘shnilik ro‘yxati", ("qo‘shnilik matritsasi", "bitta satr", "saralangan massiv"),
          "Qo‘shnilik ro‘yxati faqat mavjud qirralarni saqlaydi: O(n + m)."),
        Q(2, "Uchning darajasi (degree) nima?",
          "unga tutashgan qirralar soni", ("uchdan ildizgacha masofa", "uchning tartib raqami", "grafdagi uchlar soni"),
          "Daraja uchning nechta qo‘shnisi borligini bildiradi."),
        Q(3, "n uchli yo‘naltirilmagan to‘liq grafda nechta qirra bor?",
          "n(n − 1)/2", ("n²", "n − 1", "2n"),
          "Har bir juft uch bitta qirra bilan bog‘langan."),
        Q(3, "Sikl yo‘q yo‘naltirilgan graf qanday ataladi?",
          "DAG (yo‘naltirilgan atsiklik graf)", ("to‘liq graf", "ikki bo‘lakli graf", "har doim daraxt"),
          "Prerekvizitlar grafi ham DAG bo‘lishi shart."),
    ),
)

ALG_BFS_DFS = TopicSpec(
    "demo--alg-bfs-dfs",
    "Grafni aylanib chiqish (BFS va DFS)",
    "Kenglik bo‘yicha (navbat bilan) va chuqurlik bo‘yicha (stek yoki rekursiya bilan) qidiruv.",
    (
        Q(1, "BFS qaysi tuzilmadan foydalanadi?",
          "navbat", ("stek", "ustuvor navbat", "lug‘at"),
          "BFS uchlarni qatlamma-qatlam, navbat tartibida ko‘radi."),
        Q(1, "DFS odatda qanday amalga oshiriladi?",
          "stek yoki rekursiya bilan", ("faqat navbat bilan", "saralash bilan", "ikkilik qidiruv bilan"),
          "DFS bir yo‘ldan oxirigacha boradi, keyin orqaga qaytadi."),
        Q(2, "Vaznsiz grafda qirralar soni bo‘yicha eng qisqa yo‘lni qaysi algoritm topadi?",
          "BFS", ("DFS", "pufakchali saralash", "ikkilik qidiruv"),
          "BFS uchlarni boshlang‘ich uchdan masofa tartibida topadi."),
        Q(2, "Qo‘shnilik ro‘yxati bilan BFS ning murakkabligi qanday?",
          "O(V + E)", ("O(V² · E)", "O(log V)", "O(E²)"),
          "Har uch va har qirra bir martadan ko‘riladi."),
        Q(2, "Aylanishda bir uchni ikki marta qayta ishlamaslik uchun nima saqlanadi?",
          "tashrif buyurilgan uchlar to‘plami", ("qirralar soni", "grafning nusxasi", "faqat oxirgi uch"),
          "Ko‘rilgan uchlar belgilab boriladi."),
        Q(3, "A–B, A–C, B–D qirrali grafda A dan boshlangan BFS tartibi qaysi (qo‘shnilar alifbo tartibida)?",
          "A, B, C, D", ("A, B, D, C", "A, C, B, D", "D, B, C, A"),
          "Avval A ning qo‘shnilari B va C, keyin B ning qo‘shnisi D. A, B, D, C esa DFS tartibi."),
        Q(3, "Yo‘naltirilgan grafda siklni aniqlash uchun qaysi yondashuv ishlatiladi?",
          "DFS da joriy yo‘ldagi uchni qayta uchratish", ("BFS dagi navbat uzunligi", "uchlar sonini sanash", "qirralarni saralash"),
          "Joriy yo‘ldagi uchga qaytuvchi qirra siklni bildiradi."),
    ),
)

ALGORITMLAR = CourseSpec(
    "demo--algoritmlar-asoslari",
    "Algoritmlar asoslari",
    "Algoritmlarni tahlil qilish, qidiruv va saralash algoritmlari, stek, navbat va graflar.",
    "algoritmlar",
    (
        SectionSpec("demo--alg-tahlil-qidiruv", "Tahlil va qidiruv",
                    "Algoritm samaradorligini baholash va massivda qidirish.",
                    (ALG_MURAKKABLIK, ALG_CHIZIQLI, ALG_IKKILIK)),
        SectionSpec("demo--alg-oddiy-saralash", "Oddiy saralashlar",
                    "Kvadratik vaqtli, lekin tushunarli saralash algoritmlari.",
                    (ALG_PUFAKCHALI, ALG_JOYLASHTIRIB)),
        SectionSpec("demo--alg-samarali-saralash", "Samarali saralashlar",
                    "O(n log n) vaqtli rekursiv saralash algoritmlari.",
                    (ALG_BIRLASHTIRIB, ALG_TEZ)),
        SectionSpec("demo--alg-stek-graf", "Stek, navbat va graflar",
                    "Chiziqli tuzilmalar va graflarni aylanib chiqish.",
                    (ALG_STEK, ALG_GRAFLAR, ALG_BFS_DFS)),
    ),
)

COURSES: tuple[CourseSpec, ...] = (PYTHON, ALGORITMLAR)


# ---------------------------------------------------------------------------
# Prerequisites: (x, y, ω) — x must be mastered before y.
# ---------------------------------------------------------------------------

PREREQUISITES: tuple[tuple[str, str, float], ...] = (
    # Python
    ("demo--py-ozgaruvchilar", "demo--py-operatorlar", 1.0),
    ("demo--py-ozgaruvchilar", "demo--py-kiritish-chiqarish", 1.0),
    ("demo--py-ozgaruvchilar", "demo--py-satrlar", 1.0),
    ("demo--py-kiritish-chiqarish", "demo--py-satrlar", 0.5),
    ("demo--py-operatorlar", "demo--py-shartlar", 1.0),
    ("demo--py-operatorlar", "demo--py-sikllar", 1.0),
    ("demo--py-operatorlar", "demo--py-funksiyalar", 1.0),
    ("demo--py-sikllar", "demo--py-royxatlar", 1.0),
    ("demo--py-satrlar", "demo--py-royxatlar", 0.8),
    ("demo--py-royxatlar", "demo--py-lugatlar", 1.0),
    ("demo--py-funksiyalar", "demo--py-rekursiya", 1.0),
    ("demo--py-shartlar", "demo--py-rekursiya", 0.8),
    ("demo--py-shartlar", "demo--py-istisnolar", 1.0),
    ("demo--py-funksiyalar", "demo--py-istisnolar", 0.8),
    ("demo--py-satrlar", "demo--py-fayllar", 1.0),
    ("demo--py-istisnolar", "demo--py-fayllar", 1.0),
    # Algoritmlar
    ("demo--alg-murakkablik", "demo--alg-chiziqli-qidiruv", 1.0),
    ("demo--alg-murakkablik", "demo--alg-ikkilik-qidiruv", 1.0),
    ("demo--alg-chiziqli-qidiruv", "demo--alg-ikkilik-qidiruv", 1.0),
    ("demo--alg-murakkablik", "demo--alg-pufakchali", 1.0),
    ("demo--alg-pufakchali", "demo--alg-joylashtirib", 1.0),
    ("demo--alg-joylashtirib", "demo--alg-birlashtirib", 1.0),
    ("demo--alg-joylashtirib", "demo--alg-tez-saralash", 1.0),
    ("demo--alg-murakkablik", "demo--alg-stek-navbat", 0.8),
    ("demo--alg-stek-navbat", "demo--alg-graflar", 1.0),
    ("demo--alg-graflar", "demo--alg-bfs-dfs", 1.0),
    # Across the two courses
    ("demo--py-rekursiya", "demo--alg-birlashtirib", 1.0),
    ("demo--py-rekursiya", "demo--alg-tez-saralash", 0.8),
    ("demo--py-sikllar", "demo--alg-chiziqli-qidiruv", 0.7),
)


# ---------------------------------------------------------------------------
# Derived views of the data (no database)
# ---------------------------------------------------------------------------

def all_topics() -> list[TopicSpec]:
    return [topic for course in COURSES for topic in course.topics()]


def course_of_topic() -> dict[str, str]:
    return {topic.slug: course.slug for course in COURSES for topic in course.topics()}


def section_of_topic() -> dict[str, str]:
    return {
        topic.slug: section.slug
        for course in COURSES for section in course.sections for topic in section.topics
    }


def all_slugs() -> list[str]:
    slugs: list[str] = []
    for course in COURSES:
        slugs.append(course.slug)
        for section in course.sections:
            slugs.append(section.slug)
            slugs.extend(topic.slug for topic in section.topics)
    return slugs


def levels() -> dict[str, int]:
    """Longest chain of prerequisites ending at each topic, in edges (0 for a source)."""
    pre: dict[str, list[str]] = {topic.slug: [] for topic in all_topics()}
    for x, y, _ in PREREQUISITES:
        pre[y].append(x)
    memo: dict[str, int] = {}

    def level(slug: str, path: tuple[str, ...] = ()) -> int:
        if slug in path:
            raise ValueError(f"cycle through {slug}")
        if slug not in memo:
            memo[slug] = max((level(x, path + (slug,)) + 1 for x in pre[slug]), default=0)
        return memo[slug]

    return {slug: level(slug) for slug in pre}
