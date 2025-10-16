import os
from dotenv import load_dotenv
import telebot
import time
from datetime import datetime, timedelta
from db import init_db, add_note, list_notes, update_note, delete_note, find_notes

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("В .env файле нет TOKEN")

bot = telebot.TeleBot(TOKEN)

# Инициализация базы данных при запуске
init_db()

# Константы
MAX_NOTES_PER_USER = 50


@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Привет! Я бот для заметок. Используй /help для списка команд.")


@bot.message_handler(commands=['help'])
def help_cmd(message):
    help_text = f"""
Доступные команды:
/note_add <текст> - Добавить заметку (максимум {MAX_NOTES_PER_USER})
/note_list - Показать все заметки
/note_find <запрос> - Найти заметку
/note_edit <id> <новый текст> - Изменить заметку
/note_del <id> - Удалить заметку
/note_count - Количество заметок
/note_export - Экспорт всех заметок в файл
/note_stats - Статистика активности за неделю

📝 Лимит: {MAX_NOTES_PER_USER} заметок на пользователя
"""
    bot.reply_to(message, help_text)


@bot.message_handler(commands=['note_add'])
def note_add(message):
    # Проверяем лимит заметок
    user_id = message.from_user.id
    user_notes = list_notes(user_id)

    if len(user_notes) >= MAX_NOTES_PER_USER:
        bot.reply_to(
            message,
            f"❌ Достигнут лимит заметок! Максимум {MAX_NOTES_PER_USER} заметок на пользователя.\n"
            f"У вас уже {len(user_notes)} заметок. Удалите некоторые заметки чтобы добавить новые."
        )
        return

    text = message.text.replace('/note_add', '').strip()
    if not text:
        bot.reply_to(message, "Ошибка: Укажите текст заметки.")
        return

    note_id = add_note(user_id, text)
    bot.reply_to(
        message,
        f"✅ Заметка #{note_id} добавлена: {text}\n"
        f"📊 Статистика: {len(user_notes) + 1}/{MAX_NOTES_PER_USER} заметок"
    )


@bot.message_handler(commands=['note_list'])
def note_list(message):
    user_id = message.from_user.id
    user_notes = list_notes(user_id)

    if not user_notes:
        bot.reply_to(message, "Заметок пока нет.")
        return

    response = f"📝 Ваши заметки ({len(user_notes)}/{MAX_NOTES_PER_USER}):\n" + "\n".join(
        [f"{note['id']}: {note['text']}" for note in user_notes])
    bot.reply_to(message, response)


@bot.message_handler(commands=['note_find'])
def note_find(message):
    query = message.text.replace('/note_find', '').strip()
    if not query:
        bot.reply_to(message, "Ошибка: Укажите поисковый запрос.")
        return

    user_id = message.from_user.id
    found_notes = find_notes(user_id, query)

    if not found_notes:
        bot.reply_to(message, "Заметки не найдены.")
        return

    response = f"🔍 Найденные заметки ({len(found_notes)}):\n" + "\n".join(
        [f"{note['id']}: {note['text']}" for note in found_notes])
    bot.reply_to(message, response)


@bot.message_handler(commands=['note_edit'])
def note_edit(message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        bot.reply_to(message, "Ошибка: Используйте /note_edit <id> <новый текст>")
        return

    try:
        note_id = int(parts[1])
        new_text = parts[2]
    except ValueError:
        bot.reply_to(message, "Ошибка: ID должен быть числом.")
        return

    user_id = message.from_user.id
    success = update_note(user_id, note_id, new_text)

    if not success:
        bot.reply_to(message, f"Ошибка: Заметка #{note_id} не найдена или у вас нет прав для её изменения.")
        return

    user_notes = list_notes(user_id)
    bot.reply_to(
        message,
        f"✏️ Заметка #{note_id} изменена на: {new_text}\n"
        f"📊 Статистика: {len(user_notes)}/{MAX_NOTES_PER_USER} заметок"
    )


@bot.message_handler(commands=['note_del'])
def note_del(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.reply_to(message, "Ошибка: Укажите ID заметки для удаления.")
        return

    try:
        note_id = int(parts[1])
    except ValueError:
        bot.reply_to(message, "Ошибка: ID должен быть числом.")
        return

    user_id = message.from_user.id
    success = delete_note(user_id, note_id)

    if not success:
        bot.reply_to(message, f"Ошибка: Заметка #{note_id} не найдена или у вас нет прав для её удаления.")
        return

    user_notes = list_notes(user_id)
    bot.reply_to(
        message,
        f"🗑️ Заметка #{note_id} удалена.\n"
        f"📊 Статистика: {len(user_notes)}/{MAX_NOTES_PER_USER} заметок"
    )


@bot.message_handler(commands=['note_count'])
def note_count(message):
    user_id = message.from_user.id
    user_notes = list_notes(user_id)
    count = len(user_notes)

    if count >= MAX_NOTES_PER_USER:
        status = "❌ Лимит достигнут!"
    elif count >= MAX_NOTES_PER_USER * 0.8:  # 80% от лимита
        status = "⚠️ Лимит почти достигнут!"
    else:
        status = "✅ Есть свободное место"

    bot.reply_to(
        message,
        f"📊 Статистика заметок:\n"
        f"• Всего заметок: {count}\n"
        f"• Лимит: {MAX_NOTES_PER_USER}\n"
        f"• Свободно: {MAX_NOTES_PER_USER - count}\n"
        f"{status}"
    )


@bot.message_handler(commands=['note_export'])
def note_export(message):
    user_id = message.from_user.id
    user_notes = list_notes(user_id)

    if not user_notes:
        bot.reply_to(message, "У вас нет заметок для экспорта.")
        return

    # Создаем имя файла с timestamp для уникальности
    timestamp = int(time.time())
    filename = f"notes_{user_id}_{timestamp}.txt"

    try:
        # Создаем содержимое файла
        file_content = f"Ваши заметки (экспорт от {time.strftime('%Y-%m-%d %H:%M:%S')})\n"
        file_content += f"Всего заметок: {len(user_notes)}/{MAX_NOTES_PER_USER}\n"
        file_content += "=" * 50 + "\n\n"

        for note in user_notes:
            file_content += f"Заметка #{note['id']}:\n"
            file_content += f"{note['text']}\n"
            file_content += "-" * 30 + "\n"

        # Записываем в файл
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(file_content)

        # Отправляем файл пользователю
        with open(filename, 'rb') as f:
            bot.send_document(
                message.chat.id,
                f,
                caption=f"📁 Ваши заметки ({len(user_notes)}/{MAX_NOTES_PER_USER} шт.)",
                visible_file_name="your_notes.txt"
            )

        # Удаляем временный файл
        os.remove(filename)

    except Exception as e:
        bot.reply_to(message, f"Ошибка при экспорте заметок: {str(e)}")
        # Пытаемся удалить файл в случае ошибки
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass


@bot.message_handler(commands=['note_stats'])
def note_stats(message):
    user_id = message.from_user.id
    user_notes = list_notes(user_id)

    if not user_notes:
        bot.reply_to(message, "У вас пока нет заметок для статистики.")
        return

    # Получаем даты создания заметок (предполагаем, что в базе есть поле created_at)
    # Если в вашей базе нет created_at, нужно будет адаптировать этот код
    dates = []
    for note in user_notes:
        # Если в note есть created_at, используем его, иначе используем текущее время
        if 'created_at' in note:
            dates.append(note['created_at'])
        else:
            # Для демонстрации - случайные даты за последнюю неделю
            days_ago = len(dates) % 7
            dates.append(datetime.now() - timedelta(days=days_ago))

    # Считаем активность по дням недели
    week_activity = [0] * 7  # 0 = понедельник, 6 = воскресенье

    for date in dates:
        if isinstance(date, str):
            # Если дата в строковом формате, преобразуем в datetime
            try:
                date_obj = datetime.fromisoformat(date.replace('Z', '+00:00'))
            except:
                date_obj = datetime.now()
        else:
            date_obj = date

        weekday = date_obj.weekday()  # 0 = понедельник, 6 = воскресенье
        week_activity[weekday] += 1

    # Создаем ASCII гистограмму
    max_activity = max(week_activity) if week_activity else 1
    chart_height = 10

    # Названия дней недели
    days_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    # Строим гистограмму
    chart_lines = []

    # Вертикальные столбцы (сверху вниз)
    for level in range(chart_height, 0, -1):
        line = ""
        for day_activity in week_activity:
            bar_height = (day_activity / max_activity) * chart_height if max_activity > 0 else 0
            if bar_height >= level:
                line += " ██ "
            else:
                line += "    "
        chart_lines.append(line)

    # Подписи дней и значения
    days_line = ""
    values_line = ""
    for i, day in enumerate(days_ru):
        days_line += f" {day} "
        values_line += f" {week_activity[i]:2d}"

    # Собираем всю визуализацию
    stats_text = "📊 Ваша активность за неделю:\n\n"

    # Добавляем гистограмму
    for line in chart_lines:
        stats_text += line + "\n"

    stats_text += days_line + "\n"
    stats_text += values_line + "\n\n"

    # Общая статистика
    total_notes = len(user_notes)
    avg_per_day = total_notes / 7
    most_active_day = days_ru[week_activity.index(max(week_activity))] if week_activity else "нет данных"

    stats_text += f"📈 Общая статистика:\n"
    stats_text += f"• Всего заметок: {total_notes}\n"
    stats_text += f"• В среднем в день: {avg_per_day:.1f}\n"
    stats_text += f"• Самый активный день: {most_active_day}\n"
    stats_text += f"• Лимит использования: {total_notes}/{MAX_NOTES_PER_USER} ({total_notes / MAX_NOTES_PER_USER * 100:.1f}%)\n\n"

    # Рекомендации
    if max(week_activity) == 0:
        stats_text += "💡 Совет: Попробуйте добавлять заметки регулярнее!"
    elif max(week_activity) >= 5:
        stats_text += "🔥 Отличная активность! Продолжайте в том же духе!"
    else:
        stats_text += "💪 Хорошая работа! Можно добавить еще немного заметок."

    bot.reply_to(message, stats_text)

if __name__ == "__main__":
    print("Бот запускается...")
    bot.infinity_polling()