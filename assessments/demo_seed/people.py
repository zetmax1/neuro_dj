"""
Names, hidden profiles and the roster drawn from the seed (pure, no database).

A learner's profile is hidden: it is never written to the database. It only
decides how the simulator answers. Given the same seed and scale the roster —
names, emails, profiles, enrolments and every hidden parameter — is the same.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass

EMAIL_DOMAIN = "example.com"

# The two instructors, one per course (content.CourseSpec.instructor).
INSTRUCTORS: dict[str, tuple[str, str]] = {
    "python": ("Dilnoza", "Rahimova"),
    "algoritmlar": ("Bekzod", "Tursunov"),
}

MALE_NAMES = (
    "Aziz", "Jasur", "Sardor", "Otabek", "Javohir", "Shohruh", "Ulug‘bek", "Doniyor",
    "Sherzod", "Akmal", "Bobur", "Diyorbek", "Islom", "Jamshid", "Mirjalol", "Nodir",
    "Rustam", "Sanjar", "Temur", "Asilbek", "Farrux", "G‘ayrat", "Humoyun", "Ibrohim",
    "Mansur", "O‘tkir", "Zafar", "Behruz", "Elyor", "Lochinbek",
)
FEMALE_NAMES = (
    "Madina", "Nilufar", "Sevara", "Shahnoza", "Gulnora", "Feruza", "Kamola", "Laylo",
    "Malika", "Nargiza", "Ozoda", "Sabina", "Zarina", "Mohinur", "Dildora", "Gulchehra",
    "Munisa", "Nodira", "Iroda", "Yulduz", "Oydin", "Shahzoda", "Robiya", "Durdona",
    "Zebiniso", "Mehribon", "G‘uncha", "O‘g‘iloy", "Sitora", "Charos",
)
# Male forms; every one ends in -ov or -ev, so the female form adds "a".
SURNAMES = (
    "Karimov", "Toshmatov", "Abdullayev", "Yusupov", "Ergashev", "Xolmatov", "Nazarov",
    "Saidov", "Qodirov", "Mirzayev", "Sobirov", "Hamidov", "Jo‘rayev", "Olimov",
    "Rasulov", "Usmonov", "Islomov", "Azimov", "Yo‘ldoshev", "G‘ulomov", "Sharipov",
    "Normatov", "Ismoilov", "Fayzullayev", "Zokirov", "Boboyev", "Mahmudov", "Sultonov",
    "Qosimov", "Haydarov", "Aliyev", "Valiyev", "Hakimov", "Nurmatov", "Ochilov",
    "Po‘latov", "Shukurov", "Tojiyev", "Umarov", "Xudoyberdiyev",
)

_APOSTROPHES = re.compile(r"[‘’ʻʼ'`]")


def ascii_username(first_name: str, last_name: str) -> str:
    """'O‘g‘iloy', 'Yo‘ldosheva' -> 'ogiloy.yoldosheva' (o‘ -> o, g‘ -> g)."""
    username = f"{first_name}.{last_name}".lower()
    username = _APOSTROPHES.sub("", username)
    if not re.fullmatch(r"[a-z]+\.[a-z]+", username):
        raise ValueError(f"{first_name} {last_name} does not transliterate to plain ASCII.")
    return username


def email_for(first_name: str, last_name: str) -> str:
    return f"{ascii_username(first_name, last_name)}@{EMAIL_DOMAIN}"


def female_form(surname: str) -> str:
    return surname + "a"


# ---------------------------------------------------------------------------
# Hidden profiles
# ---------------------------------------------------------------------------

BOTH, PYTHON, ALGORITMLAR = "both", "python", "algoritmlar"

# The six weeks of the timeline are days 0..41; day 41 is yesterday.
TIMELINE_DAYS = 42


@dataclass(frozen=True)
class Profile:
    key: str
    label: str
    # One enrolment per learner of this profile: which course(s) they work in.
    enrolments: tuple[str, ...]
    theta: tuple[float, float]       # true ability
    prior: float                     # P(knows a topic before answering it)
    learn: tuple[float, float]       # P(learns the topic) per answer while not knowing it
    slip: float                      # base P(wrong | knows)
    guess: float                     # base P(right | does not know)
    sessions: tuple[int, int]
    windows: tuple[tuple[int, int], ...]  # active days, inclusive, within the timeline
    answers_per_session: tuple[int, int]
    follow: float                    # P(takes the system's recommendation)
    overpractice: int                # correct answers after M = 1 before moving on
    patience: int                    # wrong answers in a row before leaving the topic
    behaviour: str = "regular"       # "regular" | "gap" | "forgetter"


PROFILES: tuple[Profile, ...] = (
    Profile(
        "alochi", "A’lochi",
        (BOTH, PYTHON, ALGORITMLAR, BOTH),
        theta=(1.0, 1.6), prior=0.20, learn=(0.30, 0.42), slip=0.03, guess=0.15,
        sessions=(11, 14), windows=((0, 41),), answers_per_session=(8, 13),
        follow=0.9, overpractice=1, patience=4,
    ),
    Profile(
        "ortacha", "O‘rtacha",
        (BOTH, PYTHON, ALGORITMLAR, PYTHON, BOTH, ALGORITMLAR, PYTHON, BOTH, ALGORITMLAR, PYTHON),
        theta=(-0.3, 0.5), prior=0.08, learn=(0.11, 0.20), slip=0.08, guess=0.14,
        sessions=(10, 15), windows=((0, 41),), answers_per_session=(11, 17),
        follow=0.75, overpractice=1, patience=4,
    ),
    Profile(
        "sust", "Sust",
        (PYTHON, ALGORITMLAR, BOTH, PYTHON, ALGORITMLAR),
        theta=(-1.6, -0.8), prior=0.03, learn=(0.05, 0.09), slip=0.12, guess=0.12,
        sessions=(9, 13), windows=((0, 41),), answers_per_session=(8, 14),
        follow=0.6, overpractice=0, patience=5,
    ),
    Profile(
        "boshliqli", "Bo‘shliqli",
        (PYTHON, BOTH, ALGORITMLAR, PYTHON),
        theta=(0.0, 0.8), prior=0.10, learn=(0.22, 0.32), slip=0.06, guess=0.15,
        sessions=(8, 11), windows=((0, 41),), answers_per_session=(8, 12),
        follow=0.2, overpractice=0, patience=3, behaviour="gap",
    ),
    Profile(
        "toxtagan", "To‘xtab qolgan",
        (ALGORITMLAR, PYTHON, ALGORITMLAR),
        theta=(-0.4, 0.4), prior=0.08, learn=(0.18, 0.26), slip=0.08, guess=0.15,
        sessions=(4, 6), windows=((0, 13),), answers_per_session=(7, 12),
        follow=0.75, overpractice=0, patience=4,
    ),
    Profile(
        "yangi", "Yangi",
        (PYTHON, ALGORITMLAR),
        theta=(-0.2, 0.4), prior=0.10, learn=(0.20, 0.30), slip=0.07, guess=0.15,
        sessions=(0, 0), windows=(), answers_per_session=(0, 0),
        follow=0.8, overpractice=1, patience=4,
    ),
    Profile(
        "unutgan", "Unutgan",
        (BOTH, PYTHON),
        theta=(0.4, 1.0), prior=0.15, learn=(0.25, 0.35), slip=0.04, guess=0.15,
        sessions=(13, 15), windows=((0, 16), (28, 41)), answers_per_session=(8, 13),
        follow=0.8, overpractice=1, patience=4, behaviour="forgetter",
    ),
)

PROFILE_BY_KEY = {profile.key: profile for profile in PROFILES}


def profile_count(profile: Profile, scale: float) -> int:
    """Learners of this profile at ``scale``; at least one, at most the full list."""
    full = len(profile.enrolments)
    return max(1, min(full, round(full * scale)))


def scaled_sessions(bounds: tuple[int, int], scale: float) -> tuple[int, int]:
    low, high = bounds
    if high == 0:
        return (0, 0)
    return (max(1, round(low * scale)), max(1, round(high * scale)))


# ---------------------------------------------------------------------------
# The roster
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Person:
    index: int          # position in the roster: creation order and the learner's own RNG stream
    first_name: str
    last_name: str
    email: str
    gender: str         # "m" | "f"
    profile: str
    enrolment: str      # BOTH | PYTHON | ALGORITMLAR

    @property
    def courses(self) -> tuple[str, ...]:
        return (PYTHON, ALGORITMLAR) if self.enrolment == BOTH else (self.enrolment,)


def instructor_people() -> dict[str, tuple[str, str, str]]:
    """course key -> (first name, last name, email)."""
    return {
        key: (first, last, email_for(first, last))
        for key, (first, last) in INSTRUCTORS.items()
    }


def roster(seed: int, scale: float = 1.0, taken: frozenset[str] = frozenset()) -> list[Person]:
    """
    The learners for this seed and scale. ``taken`` holds emails already used
    by accounts that are not demo accounts; a name that would clash is skipped
    (the instructors' names are never drawn).
    """
    rng = random.Random(f"seed_demo:roster:{seed}")
    slots = [
        (profile.key, enrolment)
        for profile in PROFILES
        for enrolment in profile.enrolments[:profile_count(profile, scale)]
    ]
    rng.shuffle(slots)

    reserved_first = {first for first, _ in INSTRUCTORS.values()}
    reserved_last = {last.removesuffix("a") for _, last in INSTRUCTORS.values()}
    male = [n for n in MALE_NAMES if n not in reserved_first]
    female = [n for n in FEMALE_NAMES if n not in reserved_first]
    surnames = [s for s in SURNAMES if s not in reserved_last]
    rng.shuffle(male)
    rng.shuffle(female)
    rng.shuffle(surnames)

    people: list[Person] = []
    for index, (profile_key, enrolment) in enumerate(slots):
        gender = "f" if rng.random() < 0.5 else "m"
        names = female if gender == "f" else male
        if not names:  # one list ran out; the other still has names
            gender = "m" if gender == "f" else "f"
            names = female if gender == "f" else male
        first = names.pop()
        while True:
            if not surnames:
                raise ValueError("Not enough distinct surnames for this roster.")
            root = surnames.pop()
            last = female_form(root) if gender == "f" else root
            email = email_for(first, last)
            if email not in taken:
                break
        people.append(Person(index, first, last, email, gender, profile_key, enrolment))
    return people
