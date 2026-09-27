import os
import json
import logging
import re
from pathlib import Path
from difflib import SequenceMatcher

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)


# ============================================================
# CONFIG
# ============================================================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("Не найдена переменная BOT_TOKEN")

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "knowledge.json"

STATIC_ADMIN_IDS = set()


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ============================================================
# DEFAULT DATA
# ============================================================

DEFAULT_DATA = {
    "settings": {
        "bot_name": "BezenvKitae Helper"
    },

    "rules": [
        "Не спамить.",
        "Не размещать заведомо ложную информацию.",
        "По контактам и услугам всегда проверяйте актуальность самостоятельно.",
        "Старые объявления могут быть неактуальны."
    ],

    "faq": [
        {
            "id": 1,
            "category": "housing",
            "question": "Где искать квартиру или жильё в Гуанчжоу?",
            "answer": (
                "Для поиска жилья в группе обсуждались 58, Ziroom и Welcee. "
                "Также можно искать через риелторов и местные чаты.\n\n"
                "Если нужен конкретный район, бюджет или срок аренды — "
                "напиши их."
            ),
            "keywords": [
                "квартира",
                "квартиру",
                "квартиры",
                "квартир",
                "жилье",
                "жильё",
                "жилья",
                "аренда",
                "арендовать",
                "снять",
                "снять квартиру",
                "снять жилье",
                "апартаменты",
                "комната",
                "комнату",
                "комнаты",
                "риелтор",
                "риэлтор",
                "58",
                "ziroom",
                "welcee"
            ]
        },

        {
            "id": 2,
            "category": "children",
            "question": "Где искать детский сад или школу?",
            "answer": (
                "В группе обсуждались частные и государственные детские сады, "
                "русские школы, группы родителей и районы, удобные для семей.\n\n"
                "Если нужен сад или школа, напиши город/район, возраст ребёнка "
                "и язык обучения."
            ),
            "keywords": [
                "детский сад",
                "садик",
                "сад",
                "детсад",
                "школа",
                "школу",
                "школы",
                "ребенок",
                "ребёнок",
                "ребенка",
                "ребёнка",
                "дети",
                "детей",
                "родители",
                "русская школа",
                "английский"
            ]
        },

        {
            "id": 3,
            "category": "medical",
            "question": "Где искать врача или медицинского переводчика?",
            "answer": (
                "В группе были контакты и рекомендации по русскоязычным и "
                "англоязычным врачам, стоматологам, клиникам и медицинским "
                "переводчикам.\n\n"
                "Напиши город, специальность врача и желаемый язык общения."
            ),
            "keywords": [
                "врач",
                "врача",
                "врачу",
                "врачи",
                "клиника",
                "клинику",
                "стоматолог",
                "стоматолога",
                "зуб",
                "зубы",
                "зубной",
                "дантист",
                "медицина",
                "медицинский",
                "переводчик",
                "переводчика",
                "акупунктура",
                "иголки",
                "терапевт",
                "доктор"
            ]
        },

        {
            "id": 4,
            "category": "pets",
            "question": "Вопросы по животным и перевозке питомцев",
            "answer": (
                "В группе обсуждались ввоз и вывоз собак, прививки, анализ на "
                "антитела, ветеринарные документы, государственные ветклиники "
                "и жильё с животными.\n\n"
                "Для перевозки животного нужно уточнять страну назначения, "
                "дату поездки и маршрут."
            ),
            "keywords": [
                "собака",
                "собаку",
                "собаки",
                "кот",
                "кота",
                "кошка",
                "кошку",
                "питомец",
                "питомца",
                "животное",
                "животных",
                "ветеринар",
                "вет",
                "прививка",
                "прививки",
                "антитела",
                "ветпаспорт",
                "карантин"
            ]
        },

        {
            "id": 5,
            "category": "transport",
            "question": "Где искать аренду автомобиля, скутера или мотоцикла?",
            "answer": (
                "В группе обсуждалась аренда автомобилей, скутеров и мотоциклов "
                "в Гуанчжоу и Фошане.\n\n"
                "Напиши город, тип транспорта и срок аренды."
            ),
            "keywords": [
                "машина",
                "машину",
                "авто",
                "автомобиль",
                "автомобиля",
                "аренда авто",
                "аренда машины",
                "прокат",
                "скутер",
                "скутера",
                "скутер",
                "мотоцикл",
                "мотоцикла",
                "байк",
                "байка",
                "спортбайк",
                "права",
                "водительские"
            ]
        },

        {
            "id": 6,
            "category": "cargo",
            "question": "Где искать карго из Китая в Россию?",
            "answer": (
                "В группе регулярно обсуждаются карго и доставка Китай → Россия, "
                "в том числе Гуанчжоу → Москва и Санкт-Петербург.\n\n"
                "Для поиска подходящего варианта напиши:\n"
                "• откуда\n"
                "• куда\n"
                "• вес/объём\n"
                "• что отправляешь\n"
                "• нужна ли доставка до двери."
            ),
            "keywords": [
                "карго",
                "cargo",
                "доставка",
                "доставку",
                "груз",
                "груза",
                "грузов",
                "посылка",
                "посылку",
                "отправить",
                "отправка",
                "перевезти",
                "перевозка",
                "москва",
                "питер",
                "санкт петербург",
                "беларусь",
                "доставка из китая"
            ]
        },

        {
            "id": 7,
            "category": "money",
            "question": "Вопросы по Alipay, WeChat Pay и банковским переводам",
            "answer": (
                "В группе обсуждались пополнение Alipay и WeChat Pay, переводы "
                "из России, китайские банковские карты и обмен рублей/юаней.\n\n"
                "Напиши конкретную ситуацию — например, откуда и куда нужно "
                "перевести деньги."
            ),
            "keywords": [
                "alipay",
                "алипей",
                "wechat",
                "weixin",
                "вичат",
                "деньги",
                "деньги",
                "перевод",
                "перевести",
                "рубли",
                "рублей",
                "юани",
                "юаней",
                "банк",
                "банка",
                "банковский",
                "карта",
                "карты",
                "сбер",
                "тинькофф",
                "тбанк",
                "обмен"
            ]
        },

        {
            "id": 8,
            "category": "visa",
            "question": "Вопросы по визам и пребыванию в Китае",
            "answer": (
                "В группе обсуждались визы, безвизовый въезд, бизнес-визы, "
                "сроки пребывания и выезды/повторные въезды.\n\n"
                "Важно: визовые правила могут меняться. Старое сообщение "
                "из группы нельзя автоматически считать актуальным.\n\n"
                "Для точного ответа нужно знать гражданство, тип визы, дату "
                "въезда и текущий маршрут."
            ),
            "keywords": [
                "виза",
                "визу",
                "визы",
                "визе",
                "безвиз",
                "безвизовый",
                "visa",
                "граница",
                "границу",
                "border",
                "border run",
                "выезд",
                "въезд",
                "пребывание",
                "90 дней",
                "30 дней"
            ]
        },

        {
            "id": 9,
            "category": "work",
            "question": "Где искать работу или подработку?",
            "answer": (
                "В группе публиковались вакансии и разовые подработки: переводы, "
                "закупки, работа с китайскими поставщиками, e-commerce, салоны, "
                "сопровождение мероприятий и другие варианты.\n\n"
                "Напиши город, навыки, знание китайского и какой формат работы нужен."
            ),
            "keywords": [
                "работа",
                "работу",
                "работы",
                "вакансия",
                "вакансии",
                "подработка",
                "подработку",
                "зарплата",
                "зарплату",
                "китайский",
                "hsk",
                "закупки",
                "закупщик",
                "байер",
                "менеджер",
                "e-commerce",
                "заработок"
            ]
        },

        {
            "id": 10,
            "category": "shopping",
            "question": "Где искать рынки и магазины?",
            "answer": (
                "В группе обсуждались рынки электроники, одежды, тканей, мебели, "
                "автозапчастей, продуктов и другие торговые места в Гуанчжоу, "
                "Фошане и Шэньчжэне.\n\n"
                "Напиши, что именно нужно купить и в каком городе."
            ),
            "keywords": [
                "рынок",
                "рынки",
                "рынок электроники",
                "магазин",
                "магазины",
                "электроника",
                "телефон",
                "телефоны",
                "айфон",
                "наушники",
                "одежда",
                "ткань",
                "ткани",
                "мебель",
                "запчасти",
                "продукты",
                "таобао",
                "taobao"
            ]
        },

        {
            "id": 11,
            "category": "business",
            "question": "Где искать поставщиков и фабрики?",
            "answer": (
                "В группе обсуждались китайские фабрики, поставщики, закупщики, "
                "инспекторы производства, посредники и сопровождение переговоров.\n\n"
                "Напиши товар, город и что именно нужно: найти фабрику, проверить "
                "производство, провести переговоры или организовать доставку."
            ),
            "keywords": [
                "фабрика",
                "фабрики",
                "фабрику",
                "поставщик",
                "поставщики",
                "поставщика",
                "производство",
                "товар",
                "товары",
                "закупка",
                "закупки",
                "посредник",
                "посредники",
                "инспектор",
                "проверка фабрики",
                "опт"
            ]
        },

        {
            "id": 12,
            "category": "language",
            "question": "Где найти переводчика?",
            "answer": (
                "В группе есть запросы на переводчиков для разных задач: бытовое "
                "общение, врачи, переговоры, фабрики, рынки тканей и закупки.\n\n"
                "Напиши город, язык и для чего нужен переводчик."
            ),
            "keywords": [
                "переводчик",
                "переводчика",
                "переводчики",
                "перевод",
                "перевести",
                "китаец",
                "китайский",
                "английский",
                "переговоры",
                "рынок тканей",
                "сопровождение"
            ]
        },

        {
            "id": 13,
            "category": "beauty",
            "question": "Где найти мастера красоты?",
            "answer": (
                "В группе обсуждались маникюр, педикюр, ресницы, волосы, окрашивание, "
                "наращивание и лазерная эпиляция, в том числе русскоязычные мастера.\n\n"
                "Напиши город/район и нужную услугу."
            ),
            "keywords": [
                "маникюр",
                "маникюра",
                "педикюр",
                "педикюра",
                "ногти",
                "ресницы",
                "ресниц",
                "волосы",
                "волос",
                "парикмахер",
                "окрашивание",
                "наращивание",
                "лазер",
                "эпиляция",
                "салон",
                "мастер",
                "мастера"
            ]
        },

        {
            "id": 14,
            "category": "leisure",
            "question": "Куда сходить и чем заняться?",
            "answer": (
                "В группе обсуждались бары, клубы, кальянные, спорт, теннис, "
                "русские мероприятия, open mic и различные варианты досуга "
                "в Гуанчжоу и Фошане.\n\n"
                "Напиши город и что хочется: спокойно посидеть, спорт, клуб, "
                "русская тусовка и т.д."
            ),
            "keywords": [
                "куда сходить",
                "куда пойти",
                "бар",
                "бары",
                "клуб",
                "клубы",
                "дискотека",
                "кальян",
                "кальянная",
                "теннис",
                "спорт",
                "open mic",
                "мероприятие",
                "мероприятия",
                "тусовка",
                "досуг"
            ]
        },

        {
            "id": 15,
            "category": "internet",
            "question": "Вопросы по VPN, интернету и связи",
            "answer": (
                "В группе обсуждались VPN, SIM-карты, China Mobile, Telegram, "
                "Instagram, YouTube и другие сервисы.\n\n"
                "Если нужен конкретный сервис — напиши его название и город."
            ),
            "keywords": [
                "vpn",
                "впн",
                "интернет",
                "телеграм",
                "telegram",
                "инстаграм",
                "instagram",
                "youtube",
                "сим",
                "sim",
                "симка",
                "симкарта",
                "china mobile",
                "связь"
            ]
        },

        {
            "id": 16,
            "category": "neighborhoods",
            "question": "Какой район выбрать для жизни?",
            "answer": (
                "В группе регулярно спрашивали про районы Гуанчжоу и Фошаня: "
                "стоимость жилья, метро, школы, русскоязычное окружение, рынки "
                "и удобство для семей.\n\n"
                "Напиши бюджет, место работы/учёбы и важные условия — например, "
                "метро, школа, тишина или русское окружение."
            ),
            "keywords": [
                "район",
                "районы",
                "где жить",
                "жить в",
                "выбрать район",
                "лучший район",
                "дешевый район",
                "дешёвый район",
                "метро",
                "русские",
                "русский район",
                "семья",
                "семейный",
                "фошань",
                "фошане",
                "гуанчжоу",
                "гуанчжоу"
            ]
        }
    ]
}


# ============================================================
# DATA
# ============================================================

def save_data(data):
    temp_file = DATA_FILE.with_suffix(".tmp")

    with open(temp_file, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    temp_file.replace(DATA_FILE)


def load_data():
    if not DATA_FILE.exists():
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if not isinstance(data, dict):
            raise ValueError("knowledge.json должен содержать JSON-объект")

        if "faq" not in data:
            data["faq"] = []

        if "rules" not in data:
            data["rules"] = []

        return data

    except Exception as error:
        logger.exception(
            "Ошибка чтения knowledge.json: %s",
            error
        )

        # Если файл битый — используем встроенную базу.
        return DEFAULT_DATA


DATA = load_data()


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize(text: str) -> str:
    text = text.lower()

    text = text.replace("ё", "е")
    text = text.replace("—", " ")
    text = text.replace("–", " ")
    text = text.replace("-", " ")

    text = re.sub(
        r"https?://\S+",
        " ",
        text
    )

    text = re.sub(
        r"[^a-zа-я0-9\s]",
        " ",
        text
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


def tokenize(text: str):
    return set(
        normalize(text).split()
    )


# ============================================================
# SIMPLE RUSSIAN WORD NORMALIZATION
# ============================================================

WORD_REPLACEMENTS = {
    # жильё
    "квартиру": "квартира",
    "квартиры": "квартира",
    "квартирой": "квартира",
    "квартире": "квартира",
    "квартир": "квартира",

    "жилья": "жилье",
    "жилью": "жилье",
    "жильем": "жилье",
    "жилье": "жилье",

    "комнату": "комната",
    "комнаты": "комната",
    "комнате": "комната",
    "комнатой": "комната",

    # дети
    "ребенка": "ребенок",
    "ребенку": "ребенок",
    "ребенком": "ребенок",
    "детей": "дети",
    "детям": "дети",

    # врачи
    "врача": "врач",
    "врачу": "врач",
    "врачи": "врач",
    "врачом": "врач",

    "клинику": "клиника",
    "клинике": "клиника",
    "клиник": "клиника",

    "стоматолога": "стоматолог",

    # животные
    "собаку": "собака",
    "собаки": "собака",
    "собакой": "собака",

    "кошку": "кошка",
    "кошки": "кошка",

    "кота": "кот",
    "коты": "кот",

    "питомца": "питомец",
    "питомцы": "питомец",

    # транспорт
    "машину": "машина",
    "машины": "машина",
    "машиной": "машина",

    "автомобиль": "авто",
    "автомобиля": "авто",

    "мотоцикла": "мотоцикл",
    "мотоциклы": "мотоцикл",

    "скутера": "скутер",

    # деньги
    "рублей": "рубли",
    "рубля": "рубли",
    "юаней": "юани",
    "юаня": "юани",

    "карты": "карта",
    "карту": "карта",

    # работа
    "работу": "работа",
    "работы": "работа",

    "вакансии": "вакансия",
    "вакансию": "вакансия",

    "подработку": "подработка",
    "подработки": "подработка",

    "зарплату": "зарплата",

    # покупки
    "рынки": "рынок",
    "магазины": "магазин",
    "магазина": "магазин",
    "ткани": "ткань",
    "тканей": "ткань",
    "товары": "товар",

    # поставщики
    "поставщики": "поставщик",
    "поставщика": "поставщик",
    "фабрики": "фабрика",
    "фабрику": "фабрика",
    "посредники": "посредник",

    # красота
    "маникюра": "маникюр",
    "педикюра": "педикюр",
    "мастера": "мастер",

    # виза
    "визу": "виза",
    "визы": "виза",
    "визе": "виза",

    # перевод
    "переводчика": "переводчик",
    "переводчики": "переводчик",

    # карго
    "посылку": "посылка",
    "посылки": "посылка",
    "груза": "груз",
    "грузов": "груз",
    "доставку": "доставка"
}


def canonical_word(word: str) -> str:
    return WORD_REPLACEMENTS.get(
        word,
        word
    )


def canonical_tokens(text: str):
    words = normalize(text).split()

    return {
        canonical_word(word)
        for word in words
    }


# ============================================================
# QUESTION DETECTION
# ============================================================

QUESTION_WORDS = {
    "где",
    "как",
    "кто",
    "что",
    "сколько",
    "какой",
    "какая",
    "какие",
    "какое",
    "можно",
    "нужен",
    "нужна",
    "нужно",
    "ищу",
    "ищем",
    "посоветуйте",
    "подскажите",
    "есть",
    "кто знает"
}


REQUEST_WORDS = {
    "ищу",
    "нужен",
    "нужна",
    "нужно",
    "посоветуйте",
    "подскажите",
    "помогите",
    "ищем",
    "где найти",
    "кто знает",
    "кто может",
    "кто подскажет",
    "можно узнать",
    "есть ли"
}


def is_question_like(text: str) -> bool:
    normalized = normalize(text)

    if "?" in text:
        return True

    for phrase in REQUEST_WORDS:
        if phrase in normalized:
            return True

    words = set(normalized.split())

    if words.intersection(QUESTION_WORDS):
        return True

    return False


# ============================================================
# FAQ SEARCH
# ============================================================

def score_faq(text: str, faq_item: dict) -> int:
    normalized = normalize(text)

    original_tokens = set(normalized.split())
    tokens = canonical_tokens(text)

    score = 0

    for keyword in faq_item.get("keywords", []):
        keyword_normalized = normalize(keyword)

        if not keyword_normalized:
            continue

        keyword_words = keyword_normalized.split()

        # ----------------------------------------------------
        # Точная фраза
        # ----------------------------------------------------

        if " " in keyword_normalized:
            if keyword_normalized in normalized:
                score += 8
                continue

            # Канонизируем слова фразы
            canonical_phrase = " ".join(
                canonical_word(word)
                for word in keyword_words
            )

            canonical_text = " ".join(
                canonical_word(word)
                for word in normalized.split()
            )

            if canonical_phrase in canonical_text:
                score += 7

            continue

        # ----------------------------------------------------
        # Точное слово
        # ----------------------------------------------------

        keyword_canonical = canonical_word(
            keyword_normalized
        )

        if keyword_canonical in tokens:
            score += 3
            continue

        # ----------------------------------------------------
        # Частичное совпадение
        # Например:
        # квартира / квартирой
        # переводчик / переводчики
        # ----------------------------------------------------

        for token in tokens:
            if len(keyword_canonical) < 4:
                continue

            if (
                len(token) >= 4
                and (
                    token.startswith(keyword_canonical)
                    or keyword_canonical.startswith(token)
                )
            ):
                score += 1
                break

        # ----------------------------------------------------
        # Небольшая защита от опечаток
        # ----------------------------------------------------

        if len(keyword_canonical) >= 5:
            for token in original_tokens:
                if len(token) < 5:
                    continue

                ratio = SequenceMatcher(
                    None,
                    keyword_canonical,
                    token
                ).ratio()

                if ratio >= 0.88:
                    score += 1
                    break

    return score


def find_best_faq(text: str):
    faq = DATA.get("faq", [])

    if not faq:
        return None, 0

    results = []

    for item in faq:
        score = score_faq(
            text,
            item
        )

        if score > 0:
            results.append(
                (score, item)
            )

    if not results:
        return None, 0

    results.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return results[0][1], results[0][0]


# ============================================================
# FAQ DISPLAY
# ============================================================

def format_faq_list():
    faq = DATA.get("faq", [])

    if not faq:
        return "📚 FAQ пока пуст."

    lines = [
        "📚 Список FAQ:\n"
    ]

    for item in faq:
        lines.append(
            f"#{item['id']} — {item['question']}"
        )

    return "\n".join(lines)


# ============================================================
# ADMIN
# ============================================================

async def get_admin_ids(update: Update):
    chat = update.effective_chat

    if not chat:
        return set(STATIC_ADMIN_IDS)

    admins = set(
        STATIC_ADMIN_IDS
    )

    try:
        administrators = await context_bot_get_admins(
            chat.id
        )

        for admin in administrators:
            if admin.user:
                admins.add(
                    admin.user.id
                )

    except Exception as error:
        logger.warning(
            "Не удалось получить администраторов: %s",
            error
        )

    return admins


async def context_bot_get_admins(chat_id: int):
    # Получаем объект бота через глобальный application.
    # Реализуется через telegram Bot API.
    return await GLOBAL_BOT.get_chat_administrators(
        chat_id
    )


async def is_admin(update: Update) -> bool:
    user = update.effective_user

    if not user:
        return False

    if user.id in STATIC_ADMIN_IDS:
        return True

    chat = update.effective_chat

    if not chat:
        return False

    try:
        member = await GLOBAL_BOT.get_chat_member(
            chat.id,
            user.id
        )

        return member.status in {
            "administrator",
            "creator"
        }

    except Exception as error:
        logger.warning(
            "Не удалось проверить администратора: %s",
            error
        )

        return False


# ============================================================
# COMMANDS
# ============================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "👋 Я на связи!\n\n"
        "Я помощник группы и умею искать информацию "
        "по базе группы.\n\n"
        "/help — помощь\n"
        "/faq — что умею искать\n"
        "/rules — правила\n"
        "/listfaq — список FAQ\n\n"
        "Или просто задай вопрос обычным сообщением."
    )


async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "🤖 Команды:\n\n"
        "/start — запуск\n"
        "/help — помощь\n"
        "/faq — категории\n"
        "/rules — правила\n"
        "/listfaq — список FAQ\n\n"
        "👑 Для администраторов:\n"
        "/addfaq вопрос | ответ\n"
        "/delfaq номер\n\n"
        "Также можно просто написать вопрос."
    )


async def faq_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        "📚 Я могу искать информацию по таким темам:\n\n"
        "🏠 Жильё\n"
        "👶 Дети и школы\n"
        "🏥 Медицина\n"
        "🐕 Животные\n"
        "🚗 Транспорт\n"
        "📦 Карго и доставка\n"
        "💰 Деньги и банки\n"
        "🛂 Визы\n"
        "💼 Работа\n"
        "🛍 Магазины и рынки\n"
        "🏭 Поставщики и фабрики\n"
        "🎓 Переводчики и образование\n"
        "💅 Красота\n"
        "🎉 Досуг\n"
        "📱 Интернет и связь\n"
        "🗺 Районы\n\n"
        "Просто задай вопрос своими словами."
    )


async def rules_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    rules = DATA.get(
        "rules",
        []
    )

    if not rules:
        await update.message.reply_text(
            "📋 Правила пока не добавлены."
        )
        return

    text = "📋 Правила:\n\n"

    for index, rule in enumerate(
        rules,
        start=1
    ):
        text += f"{index}. {rule}\n"

    await update.message.reply_text(
        text
    )


async def list_faq_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        format_faq_list()
    )


# ============================================================
# ADMIN FAQ
# ============================================================

async def add_faq_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await is_admin(update):
        await update.message.reply_text(
            "⛔ Эта команда доступна только администраторам."
        )
        return

    raw_text = update.message.text

    parts = raw_text.split(
        "|",
        1
    )

    if len(parts) != 2:
        await update.message.reply_text(
            "Формат:\n\n"
            "/addfaq вопрос | ответ\n\n"
            "Например:\n"
            "/addfaq Где искать жильё? | Смотрите 58, Ziroom и Welcee."
        )
        return

    question = (
        parts[0]
        .replace(
            "/addfaq",
            "",
            1
        )
        .strip()
    )

    answer = parts[1].strip()

    if not question or not answer:
        await update.message.reply_text(
            "❌ Вопрос и ответ не должны быть пустыми."
        )
        return

    faq = DATA.setdefault(
        "faq",
        []
    )

    ids = [
        item.get("id", 0)
        for item in faq
        if isinstance(
            item.get("id", 0),
            int
        )
    ]

    new_id = max(
        ids,
        default=0
    ) + 1

    keywords = list(
        tokenize(question)
    )

    new_item = {
        "id": new_id,
        "category": "custom",
        "question": question,
        "answer": answer,
        "keywords": keywords
    }

    faq.append(
        new_item
    )

    save_data(
        DATA
    )

    await update.message.reply_text(
        f"✅ FAQ добавлен.\n\n"
        f"#{new_id} — {question}"
    )


async def delete_faq_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not await is_admin(update):
        await update.message.reply_text(
            "⛔ Эта команда доступна только администраторам."
        )
        return

    raw_text = update.message.text

    value = (
        raw_text
        .replace(
            "/delfaq",
            "",
            1
        )
        .strip()
    )

    if not value.isdigit():
        await update.message.reply_text(
            "Формат:\n\n"
            "/delfaq номер"
        )
        return

    faq_id = int(value)

    faq = DATA.get(
        "faq",
        []
    )

    old_length = len(faq)

    DATA["faq"] = [
        item
        for item in faq
        if item.get("id") != faq_id
    ]

    if len(DATA["faq"]) == old_length:
        await update.message.reply_text(
            f"❌ FAQ #{faq_id} не найден."
        )
        return

    save_data(
        DATA
    )

    await update.message.reply_text(
        f"🗑 FAQ #{faq_id} удалён."
    )


# ============================================================
# NATURAL LANGUAGE
# ============================================================

async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.strip()

    if not text:
        return

    if text.startswith("/"):
        return

    normalized = normalize(
        text
    )

    if len(normalized) < 4:
        return

    faq_item, score = find_best_faq(
        text
    )

    if not faq_item:
        return

    question_like = is_question_like(
        text
    )

    # Для явного вопроса достаточно небольшого совпадения.
    #
    # Для обычного сообщения требуется более сильное совпадение,
    # чтобы бот не вмешивался в разговор.

    if question_like:
        minimum_score = 3
    else:
        minimum_score = 7

    if score < minimum_score:
        return

    logger.info(
        "FAQ match: score=%s category=%s text=%r",
        score,
        faq_item.get("category"),
        text
    )

    await update.message.reply_text(
        "🤖 Нашёл в базе информацию по этой теме:\n\n"
        f"{faq_item['answer']}"
    )


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):
    logger.exception(
        "Ошибка при обработке обновления:",
        exc_info=context.error
    )


# ============================================================
# MAIN
# ============================================================

GLOBAL_BOT = None


def main():
    global GLOBAL_BOT

    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    GLOBAL_BOT = application.bot

    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    application.add_handler(
        CommandHandler(
            "faq",
            faq_command
        )
    )

    application.add_handler(
        CommandHandler(
            "rules",
            rules_command
        )
    )

    application.add_handler(
        CommandHandler(
            "listfaq",
            list_faq_command
        )
    )

    application.add_handler(
        CommandHandler(
            "addfaq",
            add_faq_command
        )
    )

    application.add_handler(
        CommandHandler(
            "delfaq",
            delete_faq_command
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    application.add_error_handler(
        error_handler
    )

    logger.info(
        "🚀 BezenvKitae Helper запускается..."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
