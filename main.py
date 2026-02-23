import telebot
from telebot import types
from telebot.types import LabeledPrice
import random

TOKEN = "8582163051:AAENwQwVf5TqTtf_D7Sl15R7-UT8HSeRrvc"
PAYMENT_PROVIDER_TOKEN = "ТВОЙ_PAYMENT_PROVIDER_TOKEN"  # Получить через BotFather
bot = telebot.TeleBot(TOKEN)

users = {}

MONKEYS = {
    "🐵 Обычная обезьяна": {"price": 0, "hp": 100, "happy": 50, "hunger": 50},
    "🦍 Горилла": {"price": 50, "hp": 300, "happy": 150, "hunger": 100},
    "🐸 Пепе обезьяна": {"price": 250, "hp": 1500, "happy": 800, "hunger": 600}
}

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    users[user_id] = {
        "name": None,
        "health": 100,
        "happiness": 50,
        "hunger": 50,
        "stars": 200,
        "level": 1,
        "owned": ["🐵 Обычная обезьяна"],
        "active": "🐵 Обычная обезьяна"
    }
    bot.send_message(message.chat.id, "🐒 Как назовёшь свою обезьянку?")
    bot.register_next_step_handler(message, save_name)

def save_name(message):
    users[message.from_user.id]["name"] = message.text
    show_menu(message.chat.id)

# ================= МЕНЮ =================
def show_menu(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎮 Мини-игра (10⭐)", "🍌 Покормить (5⭐)")
    markup.add("🛒 Магазин", "📊 Статистика")
    markup.add("💳 Пополнить звёзды")
    bot.send_message(chat_id, "Выбери действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def menu(message):
    user_id = message.from_user.id
    if user_id not in users:
        bot.send_message(message.chat.id, "Напиши /start")
        return

    user = users[user_id]

    # 🎮 Мини-игра
    if message.text == "🎮 Мини-игра (10⭐)":
        if user["stars"] < 10:
            bot.send_message(message.chat.id, "❌ Недостаточно звёзд")
            return
        user["stars"] -= 10
        win = random.choice([True, False])
        if win:
            reward = random.randint(15, 30)
            user["stars"] += reward
            user["happiness"] += 15
            bot.send_message(message.chat.id, f"🎉 Победа! +{reward}⭐")
        else:
            user["health"] -= 10
            bot.send_message(message.chat.id, "😢 Проигрыш! -10 ❤️")
        check_level(user)

    # 🍌 Покормить
    elif message.text == "🍌 Покормить (5⭐)":
        if user["stars"] < 5:
            bot.send_message(message.chat.id, "❌ Недостаточно звёзд")
            return
        user["stars"] -= 5
        user["health"] += 20
        user["hunger"] -= 20
        bot.send_message(message.chat.id, "🍌 Обезьяна сыта и здорова!")

    # 🛒 Магазин
    elif message.text == "🛒 Магазин":
        show_shop(message.chat.id)

    # 📊 Статистика
    elif message.text == "📊 Статистика":
        bot.send_message(message.chat.id,
            f"Имя: {user['name']}\n"
            f"Активная: {user['active']}\n"
            f"❤️ Здоровье: {user['health']}\n"
            f"🎉 Счастье: {user['happiness']}\n"
            f"🍌 Голод: {user['hunger']}\n"
            f"⭐ Звёзды: {user['stars']}\n"
            f"🏆 Уровень: {user['level']}"
        )

    # 💳 Пополнение через Telegram Payments
    elif message.text == "💳 Пополнить звёзды":
        prices = [LabeledPrice(label="100 ⭐", amount=100*100)]  # сумма в копейках
        bot.send_invoice(
            message.chat.id,
            title="Пополнение звёзд",
            description="Покупка 100 ⭐ для игры с обезьяной",
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="star-payment",
            payload="stars_100"
        )

    # Покупка обезьян
    elif "—" in message.text:
        buy_monkey(message, user)

# ================= МАГАЗИН =================
def show_shop(chat_id):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for monkey, data in MONKEYS.items():
        markup.add(f"{monkey} — {data['price']}⭐")
    markup.add("⬅ Назад")
    bot.send_message(chat_id, "Выбери обезьяну:", reply_markup=markup)

def buy_monkey(message, user):
    text = message.text.split(" — ")[0]
    monkey_data = MONKEYS[text]
    price = monkey_data["price"]

    if text in user["owned"]:
        user["active"] = text
        bot.send_message(message.chat.id, f"Теперь активна: {text}")
        show_menu(message.chat.id)
        return

    if user["stars"] < price:
        bot.send_message(message.chat.id, "❌ Недостаточно звёзд")
        return

    user["stars"] -= price
    user["owned"].append(text)
    user["active"] = text
    user["health"] = monkey_data["hp"]
    user["happiness"] = monkey_data["happy"]
    user["hunger"] = monkey_data["hunger"]

    bot.send_message(message.chat.id, f"🎉 Куплена {text} за {price}⭐")
    show_menu(message.chat.id)

# ================= УРОВЕНЬ =================
def check_level(user):
    if user["happiness"] >= 100:
        user["level"] += 1
        user["happiness"] = 50
        user["stars"] += 20

# ================= PAYMENTS =================
@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    payload = message.successful_payment.invoice_payload
    if payload == "stars_100":
        user = users[message.from_user.id]
        user["stars"] += 100
        bot.send_message(message.chat.id, "✅ Оплата прошла! Ты получил 100 ⭐")

# ================= START BOT =================
bot.polling()
