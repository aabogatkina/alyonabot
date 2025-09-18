import os
from dotenv import load_dotenv
import telebot

load_dotenv()

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("Токен не найден в .env файле")

bot = telebot.TeleBot(TOKEN)

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! 👋")
@bot.message_handler(commands=['help'])
def help_cmd(message):
 bot.reply_to(message, "/start - начать\n/help - помощь")
# Запуск бота
if __name__ == "__main__":
    print("Бот запускается...")
    bot.polling()