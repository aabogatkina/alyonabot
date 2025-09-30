import os
from random import choice
from typing import List

import requests
from dotenv import load_dotenv
import telebot
from telebot import types
import logging

load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("В .env нет TOKEN")
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start(m: types.Message) -> None:
    bot.send_message(m.chat.id, "Привет! Я твой первый бот! Напиши /help\nИли воспользуйтесь кнопками ниже",
                        reply_markup=make_main_kb()
                 )

@bot.message_handler(commands=['help'])
def help_cmd(message):
    bot.reply_to(message, "/start - начать\n/help - помощь\n/about - о боте\n/sum - сумма чисел\n/hide - спрятать клавиатуру\n/weather - погода")
@bot.message_handler(commands=['about'])
def about_cmd(message):
    bot.reply_to(message, "Это бот, созданный с целью приобретения практических навыков по созданию Telegram бота\nАвтор: Верниковская Екатерина Андреевна\nВерсия: 1.0.2")

def is_int_token(t: str) -> bool:
    return t.strip().lstrip("-").isdigit()

def validate_user_input(text: str) -> bool:
    if not text or not text.strip():
        return False
    return True


def parse_ints_from_text(text: str) -> List[int]:
    """Выделяет из текста целые числа: нормализует запятые, игнорирует токены-команды."""
    text = text.replace(",", " ")
    tokens = [tok for tok in text.split() if not tok.startswith("/")]
    return [int(tok) for tok in tokens if is_int_token(tok)]

@bot.message_handler(commands=['sum'])
def cmd_sum(m):
    nums = parse_ints_from_text(m.text)
    if not nums:
        bot.reply_to(m, "Ты должен написать числа: /sum 2 3 10 или /sum 2, -5, 6")
    else:
        bot.reply_to(m, f"Сумма: {sum(nums)}")

def make_main_kb() -> types.ReplyKeyboardMarkup:
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("О боте", "Сумма")
    kb.row("/help")
    kb.row("/weather")
    return kb

@bot.message_handler(func=lambda m: m.text == "О боте")
def kb_about(m):
    about_cmd(m)

@bot.message_handler(func=lambda m: m.text == "Сумма")
def kb_sum(m):
    bot.send_message(m.chat.id, "Введи числа через пробел или запятую:")
    bot.register_next_step_handler(m, on_sum_numbers)

def on_sum_numbers(m):
    nums = parse_ints_from_text(m.text)
    if not nums:
        bot.reply_to(m, "Я не вижу чисел!!!!!! Пример: 2 3 10")
    else:
        bot.reply_to(m, f"Сумма: {sum(nums)}")

@bot.message_handler(commands=["hide"])
def hide_k(m):
    rm = types.ReplyKeyboardRemove()
    bot.send_message(m.chat.id, "Клавиатура спряталась",reply_markup=rm)

@bot.message_handler(commands=['confirm'])
def confirm_cmd(m):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("ДАААА", callback_data="confirm:yes"),
        types.InlineKeyboardButton("НЕЕЕЕТ", callback_data="confirm:no"),
    )
    bot.send_message(m.chat.id, "Подтвердить действие????", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm:"))
def on_confirm(c):
    choice = c.data.split(":", 1)[1]
    bot.answer_callback_query(c.id, "Принято!")

    bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    bot.send_message(c.message.chat.id, "Готово!" if choice == "yes" else "Отменено")

logging.basicConfig(
    level=logging.INFO,
    format="%(ascitime)s - %(levelname)s - %(message)s"
)

"""
@bot.message_handler(commands=['sum'])
def cmd_sum(m):
    logging.info(f"/sum от {m.from_user.first_name} {m.from_user.id}: {m.text}")
    nums = parse_ints_from_text(m.text)
    logging.info(f"распознаны числа: {nums}")
    bot.reply_to(m, f"Сумма: {sum(nums)}" if nums else "Пример: /sum 1 4 3")
"""

def fetch_weather_moscow_open_meteo() -> str:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 55.75,
        "longitude": 37.61,
        "current": "temperature_2m",
        "timezone": "Europe/Moscow"
    }
    try:
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        t = r.json()["current"]["temperature_2m"]
        return f"Россия, Москва: сейчас {round(t)}°C"
    except Exception:
        return "Не удалось получить погоду."

@bot.message_handler(commands=['weather'])
def weather_cmd(m):
    bot.reply_to(m, f"{fetch_weather_moscow_open_meteo()}" )

if __name__ == "__main__":
    bot.infinity_polling(skip_pending=True)