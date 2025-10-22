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
    bot.reply_to(message, "/start - начать\n/help - помощь\n/about - о боте\n/sum - сумма чисел\n/hide - спрятать клавиатуру\n/show - показать клавиатуру\n/weather - погода\n/max - максимум чисел\n/min - минимум чисел")
@bot.message_handler(commands=['about'])
def about_cmd(message):
    bot.reply_to(message, "Это бот, созданный с целью приобретения практических навыков по созданию Telegram бота\nАвтор: Богаткина Алёнка\nВерсия: 1.0.3")

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
    kb.row("О боте", "Сумма", "Максимум", "Минимум")
    kb.row("/help")
    kb.row("/weather")
    kb.row("Спрятать клавиатуру", "Показать клавиатуру")
    return kb

@bot.message_handler(func=lambda m: m.text == "О боте")
def kb_about(m):
    about_cmd(m)

@bot.message_handler(func=lambda m: m.text == "Максимум")
def kb_max(m):
    bot.send_message(m.chat.id, "Введи числа через пробел или запятую:")
    bot.register_next_step_handler(m, on_max_numbers)

def on_max_numbers(m):
    nums = parse_ints_from_text(m.text)
    if not nums:
        bot.reply_to(m, "Я не вижу чисел!!!!!! Пример: 2 3 10")
    else:
        bot.reply_to(m, f"Максимум: {max(nums)}")

@bot.message_handler(func=lambda m: m.text == "Минимум")
def kb_min(m):
    bot.send_message(m.chat.id, "Введи числа через пробел или запятую:")
    bot.register_next_step_handler(m, on_min_numbers)

def on_min_numbers(m):
    nums = parse_ints_from_text(m.text)
    if not nums:
        bot.reply_to(m, "Я не вижу чисел!!!!!! Пример: 2 3 10")
    else:
        bot.reply_to(m, f"Минимум: {min(nums)}")

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

@bot.message_handler(commands=["show"])
def show_k(m):
    bot.send_message(m.chat.id, "Клавиатура показана", reply_markup=make_main_kb())

@bot.message_handler(func=lambda m: m.text == "Спрятать клавиатуру")
def kb_hide(m):
    hide_k(m)

@bot.message_handler(func=lambda m: m.text == "Показать клавиатуру")
def kb_show(m):
    show_k(m)

@bot.message_handler(commands=['confirm'])
def confirm_cmd(m):
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("Да", callback_data="confirm:yes"),
        types.InlineKeyboardButton("Нет", callback_data="confirm:no"),
        types.InlineKeyboardButton("Может быть", callback_data="confirm:maybe"),
        types.InlineKeyboardButton("Потом", callback_data="confirm:later"),
        types.InlineKeyboardButton("Нужна информация", callback_data="confirm:info"),
        types.InlineKeyboardButton("Отмена", callback_data="confirm:cancel")
    )
    bot.send_message(m.chat.id, "Подтвердить действие?", reply_markup=kb)

@bot.callback_query_handler(func=lambda c: c.data.startswith("confirm:"))
def on_confirm(c):
    choice = c.data.split(":", 1)[1]
    bot.answer_callback_query(c.id, "Запрос принят")

    bot.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    responses = {
        "yes": "Действие подтверждено.",
        "no": "Действие отклонено.",
        "maybe": "Напишите позже, когда будете готовы.",
        "later": "Используйте команду /confirm когда будете готовы.",
        "info": "Какая информация Вам нужна?",
        "cancel": "Действие отменено пользователем."
    }
    response_text = responses.get(choice, "Неизвестный выбор")
    bot.send_message(c.message.chat.id, response_text)

if __name__ == "__main__":
    bot.infinity_polling(skip_pending=True)

