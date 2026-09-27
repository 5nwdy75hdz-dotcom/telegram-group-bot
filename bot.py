import os
import json
import logging
import re
from pathlib import Path
from typing import Optional

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

# ВАЖНО:
# Сюда можно вписать Telegram ID администраторов.
# Пока оставляем пустым — бот автоматически разрешит
# админские команды администраторам группы.
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
# DEFAULT KNOWLEDGE
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
                "Для поиска жилья в группе чаще всего обсуждали 58, Ziroom и Welcee. "
                "Также можно искать через риелторов и местные чаты.\n\n"
                "Если нужен конкретный район, бюджет или срок аренды — "
                "напиши их, и я попробую подобрать информацию из базы."
            ),
            "keywords": [
                "квартира",
                "жилье",
                "жильё",
                "аренда",
                "снять",
                "апартаменты",
                "комната",
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
                "школа",
                "ребенок",
                "ребёнок",
                "дети",
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
                "В группе были контакты и рекомендации по русскоязычным/англоязычным "
                "врачам, стоматологам, клиникам и медицинским переводчикам.\n\n"
                "Напиши город, специальность врача и желаемый язык общения."
            ),
            "keywords": [
                "врач",
                "клиника",
                "стоматолог",
                "зуб",
                "зубы",
                "дантист",
                "медицина",
                "переводчик",
                "акупунктура",
                "иголки",
                "терапевт"
            ]
        },

        {
            "id": 4,
            "category": "pets",
            "question": "Вопросы по животным и перевозке питомцев",
            "answer": (
                "В группе обсуждались ввоз и вывоз собак, прививки, анализ на антитела, "
                "ветеринарные документы, государственные ветклиники и жильё с животными.\n\n"
                "Для точных требований по перевозке животного нужно уточнять страну "
                "назначения, дату поездки и маршрут."
            ),
            "keywords": [
                "собака",
                "собаку",
                "кот",
                "кошка",
                "питомец",
                "животное",
                "ветеринар",
                "вет",
                "прививка",
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
                "авто",
                "автомобиль",
                "аренда авто",
                "прокат",
                "скутер",
                "мотоцикл",
                "байк",
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
                "груз",
                "посылка",
                "отправить",
                "перевезти",
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
                "В группе обсуждались пополнение Alipay и WeChat Pay, переводы из России, "
                "китайские банковские карты и обмен рублей/юаней.\n\n"
                "Напиши конкретную ситуацию — например, откуда и куда нужно перевести деньги."
            ),
            "keywords": [
                "alipay",
                "алипей",
                "wechat",
                "weixin",
                "вичат",
                "деньги",
                "перевод",
                "рубли",
                "юани",
                "банк",
                "карта",
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
                "В группе обсуждались визы, безвизовый въезд, бизнес-визы, сроки пребывания "
                "и выезды/повторные въезды.\n\n"
                "Важный момент: визовые правила могут меняться. Старое сообщение из группы "
                "нельзя автоматически считать актуальным.\n\n"
                "Для точного ответа нужно знать гражданство, тип визы, дату въезда "
                "и текущий маршрут."
            ),
            "keywords": [
                "виза",
                "визу",
                "безвиз",
                "безвизовый",
                "visa",
                "граница",
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
                "В группе публиковались вакансии и разовые подработки: "
                "переводы, закупки, работа с китайскими поставщиками, e-commerce, "
                "салоны, сопровождение мероприятий и другие варианты.\n\n"
                "Напиши город, навыки, знание китайского и какой формат работы нужен."
            ),
            "keywords": [
                "работа",
                "вакансия",
                "вакансии",
                "подработка",
                "подработку",
                "работу",
                "зарплата",
                "китаец",
                "китайский",
                "hsK",
                "закупки",
                "байер",
                "менеджер",
                "e-commerce"
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
                "магазин",
                "электроника",
                "телефон",
                "айфон",
                "наушники",
                "одежда",
                "ткань",
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
                "поставщик",
                "поставщики",
                "производство",
                "товар",
                "закупка",
                "закупки",
                "посредник",
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
                "В группе есть запросы на переводчиков для разных задач: "
                "бытовое общение, врачи, переговоры, фабрики, рынки тканей и закупки.\n\n"
                "Напиши город, язык и для чего нужен переводчик."
            ),
            "keywords": [
                "переводчик",
                "перевод",
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
                "педикюр",
                "ногти",
                "ресницы",
                "волосы",
                "парикмахер",
                "окрашивание",
                "наращивание",
                "лазер",
                "эпиляция",
                "салон",
                "мастер"
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
                "клуб",
                "дискотека",
                "кальян",
                "теннис",
                "спорт",
                "open mic",
                "мероприятие",
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
                "Напиши бюджет, место работы/учёбы и важные условия — "
                "например, метро, школа, тишина или русское окружение."
            ),
            "keywords": [
                "район",
                "где жить",
                "жить в",
                "лучший район",
                "дешевый район",
                "дешёвый район",
                "метро",
                "русские",
                "русский район",
                "семья",
                "фошань",
                "гуанчжоу",
                "фошане",
                "гуанчжоу"
            ]
        }
    ]
}


# ============================================================
# DATA
# ============================================================

def load_data():
    if not DATA_FILE.exists():
        save_data(DEFAULT_DATA)
        return DEFAULT_DATA.copy()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        if "faq" not in data:
            data["faq"] = []

        if "rules" not in data:
            data["rules"] = []

        return data

    except Exception as error:
        logger.exception("Ошибка чтения knowledge.json: %s", error)
        return DEFAULT_DATA.copy()


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


DATA = load_data()


# ============================================================
# HELPERS
# ============================================================

def normalize(text: str) -> str:
    text = text.lower().replace("ё", "е")

    text = re.sub(r"https?://\S+", " ", text)
    text = re.sub(r"[^a-zа-я0-9\s\-]", " ", text)

    text = re.sub(r"\s+", " ", text)

    return text.strip()


def tokenize(text: str):
    return set(normalize(text).split())


def is_question_like(text: str) -> bool:
    normalized = normalize(text)

    question_words = {
        "где",
        "как",
        "кто",
        "что",
        "сколько",
        "какой",
        "какая",
        "какие",
        "можно",
        "нужен",
        "нужна",
        "нужно",
        "подскажите",
        "посоветуйте",
        "ищу",
        "ищем",
        "есть",
        "кто знает",
        "подскажите пожалуйста"
    }

    if "?" in text:
        return True

    for word in question_words:
        if word in normalized:
            return True

    return False


def score_faq(text: str, faq_item: dict) -> int:
    normalized = normalize(text)
    tokens = tokenize(text)

    score = 0

    for keyword in faq_item.get("keywords", []):
        keyword_normalized = normalize(keyword)

        if not keyword_normalized:
            continue

        # Фраза
        if " " in keyword_normalized:
            if keyword_normalized in normalized:
                score += 4
            continue

        # Одно слово
        if keyword_normalized in tokens:
            score += 2

    return score


def find_best_faq(text: str):
    faq = DATA.get("faq", [])

    if not faq:
        return None, 0

    results = []

    for item in faq:
        score = score_faq(text, item)

        if score > 0:
            results.append((score, item))

    if not results:
        return None, 0

    results.sort(
        key=lambda x: x[0],
        reverse=True
    )

    best_score, best_item = results[0]

    return best_item, best_score


def format_faq_list():
    faq = DATA.get("faq", [])

    if not faq:
        return "📚 FAQ пока пуст."

    lines = ["📚 Разделы FAQ:\n"]

    for item in faq:
        lines.append(
            f"#{item['id']} — {item['question']}"
        )

    return "\n".join(lines)


def get_admin_ids(update: Update):
    chat = update.effective_chat

    if not chat:
        return set()

    try:
        admins = set(STATIC_ADMIN_IDS)

        administrators = chat.get_administrators()

        for admin in administrators:
            if admin.user:
                admins.add(admin.user.id)

        return admins

    except Exception as error:
        logger.warning(
            "Не удалось получить список администраторов: %s",
            error
        )

        return set(STATIC_ADMIN_IDS)


async def is_admin(update: Update) -> bool:
    user = update.effective_user

    if not user:
        return False

    admin_ids = await get_admin_ids(update)

    return user.id in admin_ids


# ============================================================
# COMMANDS
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Я на связи!\n\n"
        "Я помощник группы и умею искать информацию "
        "по базе FAQ.\n\n"
        "Напиши:\n"
        "/help — помощь\n"
        "/faq — что я умею искать\n"
        "/rules — правила\n\n"
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
        "/faq — категории информации\n"
        "/rules — правила\n"
        "/listfaq — список FAQ\n\n"
        "👑 Администраторам:\n"
        "/addfaq вопрос | ответ\n"
        "/delfaq номер\n\n"
        "Можно просто написать вопрос обычным сообщением."
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
    rules = DATA.get("rules", [])

    if not rules:
        await update.message.reply_text(
            "📋 Правила пока не добавлены."
        )
        return

    text = "📋 Правила:\n\n"

    for index, rule in enumerate(rules, start=1):
        text += f"{index}. {rule}\n"

    await update.message.reply_text(text)


async def list_faq_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    await update.message.reply_text(
        format_faq_list()
    )


# ============================================================
# ADMIN COMMANDS
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

    parts = raw_text.split("|", 1)

    if len(parts) != 2:
        await update.message.reply_text(
            "Формат:\n\n"
            "/addfaq вопрос | ответ\n\n"
            "Например:\n"
            "/addfaq Где искать жильё? | Смотрите 58, Ziroom и Welcee."
        )
        return

    question = parts[0].replace("/addfaq", "").strip()
    answer = parts[1].strip()

    if not question or not answer:
        await update.message.reply_text(
            "❌ Вопрос и ответ не должны быть пустыми."
        )
        return

    faq = DATA.setdefault("faq", [])

    existing_ids = [
        item.get("id", 0)
        for item in faq
        if isinstance(item.get("id", 0), int)
    ]

    new_id = max(existing_ids, default=0) + 1

    keywords = list(tokenize(question))

    new_item = {
        "id": new_id,
        "category": "custom",
        "question": question,
        "answer": answer,
        "keywords": keywords
    }

    faq.append(new_item)

    save_data(DATA)

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

    value = raw_text.replace("/delfaq", "").strip()

    if not value.isdigit():
        await update.message.reply_text(
            "Формат:\n\n"
            "/delfaq номер\n\n"
            "Например:\n"
            "/delfaq 17"
        )
        return

    faq_id = int(value)

    faq = DATA.get("faq", [])

    old_length = len(faq)

    DATA["faq"] = [
        item for item in faq
        if item.get("id") != faq_id
    ]

    if len(DATA["faq"]) == old_length:
        await update.message.reply_text(
            f"❌ FAQ #{faq_id} не найден."
        )
        return

    save_data(DATA)

    await update.message.reply_text(
        f"🗑 FAQ #{faq_id} удалён."
    )


# ============================================================
# NATURAL LANGUAGE SEARCH
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

    # Команды обрабатываются отдельными handlers
    if text.startswith("/"):
        return

    normalized = normalize(text)

    # Очень короткие сообщения игнорируем
    if len(normalized) < 5:
        return

    faq_item, score = find_best_faq(text)

    # Низкая уверенность — молчим
    if not faq_item or score < 4:
        return

    # Если сообщение явно не вопрос и похоже на обычный разговор,
    # бот не вмешивается.
    if not is_question_like(text) and score < 6:
        return

    answer = faq_item["answer"]

    await update.message.reply_text(
        f"🤖 Похоже, это по теме «{faq_item['question']}».\n\n"
        f"{answer}"
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

def main():
    application = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("faq", faq_command)
    )

    application.add_handler(
        CommandHandler("rules", rules_command)
    )

    application.add_handler(
        CommandHandler("listfaq", list_faq_command)
    )

    application.add_handler(
        CommandHandler("addfaq", add_faq_command)
    )

    application.add_handler(
        CommandHandler("delfaq", delete_faq_command)
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_message
        )
    )

    application.add_error_handler(error_handler)

    logger.info(
        "🚀 Бот запускается..."
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
