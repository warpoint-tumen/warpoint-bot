
# -*- coding: utf-8 -*-
import logging
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import random
import asyncio

TOKEN = "8318731976:AAGRLByy52ordZtigWkkQ-Ux2Hf7x7AiLIE"
YOUR_CHAT_ID = 412770085
ADMIN_PASSWORD = "1379"

tasks = []
tasks_status = {}
completed_history = []
evaluation_log = []
future_tasks = []
repeatable_tasks = {
    "monday": ["🗂️ План на неделю"],
    "friday": ["💸 Финансы"]
}

motivational_quotes = [
    "Даже самая длинная дорога начинается с первого шага.",
    "Сегодняшние усилия — это завтрашние победы!",
    "Ты создаёшь систему, а не просто решаешь задачи.",
    "Работаешь сам на себя — не жалей усилий!",
    "Каждый день — шанс стать лучше, чем вчера."
]

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Ваш chat_id: {update.effective_chat.id}")
    keyboard = [
        ["📋 Задачи на сегодня", "📆 Завтра"],
        ["🤖 AI-режим", "📊 Статистика"],
        ["➕ Добавить задачу", "⭐ Оценить день"],
        ["ℹ️ Справка"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Привет, Тумэн Баярович! Я на связи 💪", reply_markup=reply_markup)

async def tasks_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.date.today().strftime("%d.%m.%Y")
    if not tasks:
        await update.message.reply_text("Задачи на сегодня пока не добавлены.")
        return
    msg = f"📋 Задачи на сегодня ({today}):\n"
    for i, task in enumerate(tasks, 1):
        msg += f"{i}. {task} — [{tasks_status.get(i, 'не начато')}]\n"
    await update.message.reply_text(msg)

async def show_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if future_tasks:
        msg = "📆 План на завтра:\n"
        for i, task in enumerate(future_tasks, 1):
            msg += f"{i}. {task}\n"
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text("План на завтра пока не составлен.")

async def add_to_tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()
    if msg.startswith("/v_zavtra"):
        content = msg[9:].strip()
        if content:
            future_tasks.append(content)
            await update.message.reply_text(f"Задача добавлена в план на завтра: {content}")

async def show_ai_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quote = random.choice(motivational_quotes)
    done = sum(1 for s in tasks_status.values() if s == "выполнено")
    total = len(tasks)
    percent = int(done / total * 100) if total else 0
    await update.message.reply_text(f"🧠 Мотивация: {quote}\nСегодня: {done}/{total} задач ({percent}%)")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    done = sum(1 for _, _ in completed_history)
    postponed = sum(1 for s in tasks_status.values() if s == "перенесено")
    in_progress = sum(1 for s in tasks_status.values() if s == "в процессе")
    await update.message.reply_text(f"📊 Статистика:\n✅ Выполнено: {done}\n🔁 Перенесено: {postponed}\n🟡 В процессе: {in_progress}")

async def send_task_reminder(context: ContextTypes.DEFAULT_TYPE):
    task_text = context.job.data.get("text", "🔔 Напоминание о задаче")
    reply_markup = InlineKeyboardMarkup.from_button(
        InlineKeyboardButton("🔁 Напомнить позже", callback_data="remind_later")
    )
    await context.bot.send_message(chat_id=YOUR_CHAT_ID, text=task_text, reply_markup=reply_markup)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "remind_later":
        await query.edit_message_text(text="⏳ Напомню ещё раз через 10 минут...")
        context.job_queue.run_once(send_task_reminder, 600, data={"text": query.message.text})

async def protected_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and context.args[0] == ADMIN_PASSWORD:
        await update.message.reply_text("🔐 Доступ разрешён.")
    else:
        await update.message.reply_text("❌ Неверный пароль.")

def inject_repeating_tasks():
    weekday = datetime.datetime.today().strftime('%A').lower()
    repeated = repeatable_tasks.get(weekday, [])
    for task in repeated:
        tasks.append(task)
        tasks_status[len(tasks)] = "не начато"

async def monday_report():
    done = sum(1 for s in tasks_status.values() if s == "выполнено")
    total = len(tasks)
    return f"🗓️ Еженедельный отчёт:\nЗадач: {total}, выполнено: {done}\n🔥 Новая неделя — новые подвиги!"

async def update_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip().lower()
    if msg == "📋 задачи на сегодня":
        await tasks_today(update, context)
        return
    if msg == "📆 завтра":
        await show_tomorrow(update, context)
        return
    if msg == "⭐ оценить день":
        await update.message.reply_text("Оцени день по шкале от 1 до 5:")
        return
    if msg == "ℹ️ справка":
        await update.message.reply_text("Доступные команды:\n/tasks, /zavtra, /ai, /stats\n/v_zavtra [текст] — задача на завтра")
        return
    if msg == "➕ добавить задачу":
        await update.message.reply_text("Напиши новую задачу в формате: /v_zavtra Текст задачи")
        return
    if msg.startswith("/v_zavtra"):
        await add_to_tomorrow(update, context)
        return
    if msg == "/ai" or msg == "🤖 ai-режим":
        await show_ai_mode(update, context)
        return
    if msg == "/stats" or msg == "📊 статистика":
        await show_stats(update, context)
        return
    if msg in ["1", "2", "3", "4", "5"]:
        evaluation_log.append((datetime.date.today(), int(msg)))
        await update.message.reply_text("Спасибо! Оценка записана.")
        return
    parts = msg.split("-")
    if len(parts) == 2:
        try:
            num = int(parts[0].strip())
            action = parts[1].strip()
            if num in tasks_status:
                if "начал" in action:
                    tasks_status[num] = "в процессе"
                elif "готово" in action:
                    tasks_status[num] = "выполнено"
                    completed_history.append((datetime.datetime.now(), tasks[num - 1]))
                elif "перенос" in action:
                    tasks_status[num] = "перенесено"
                await update.message.reply_text(f"Обновлено: {num}. {tasks[num - 1]} — [{tasks_status[num]}]")
        except:
            pass

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tasks", tasks_today))
    app.add_handler(CommandHandler("zavtra", show_tomorrow))
    app.add_handler(CommandHandler("ai", show_ai_mode))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(CommandHandler("admin", protected_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), update_status))

    scheduler = BackgroundScheduler(timezone="Europe/Moscow")
    scheduler.add_job(inject_repeating_tasks, 'cron', hour=7, minute=0)
    scheduler.add_job(lambda: asyncio.run(app.bot.send_message(chat_id=YOUR_CHAT_ID, text=asyncio.run(monday_report()))), 'cron', day_of_week='mon', hour=9, minute=0)
    scheduler.start()

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
