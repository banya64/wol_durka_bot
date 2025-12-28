import json
import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from wakeonlan import send_magic_packet
import logging
import re

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Путь к файлу конфигурации
CONFIG_PATH = "/app/config.json"

# Чтение конфигурации из JSON
def load_config():
    try:
        with open(CONFIG_PATH, 'r') as config_file:
            config = json.load(config_file)
        return config
    except FileNotFoundError:
        logger.error(f"Файл конфигурации {CONFIG_PATH} не найден")
        raise
    except json.JSONDecodeError:
        logger.error(f"Ошибка в формате JSON файла {CONFIG_PATH}")
        raise

# Проверка формата MAC-адреса
def is_valid_mac(mac: str) -> bool:
    mac_pattern = re.compile(r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$')
    return bool(mac_pattern.match(mac))

# Загрузка конфигурации
config = load_config()
BOT_TOKEN = config.get("bot_token")
MAC_ADDRESS = config.get("mac_address")
BROADCAST_IP = config.get("broadcast_ip", "192.168.1.255")  # Значение по умолчанию
WHITELIST = config.get("whitelist", [])  # Список разрешенных user_id

# Проверка, что конфигурация загружена
if not BOT_TOKEN:
    logger.error("Токен бота не указан в конфигурации")
    raise ValueError("Токен бота обязателен")
if not MAC_ADDRESS or not is_valid_mac(MAC_ADDRESS):
    logger.error(f"Неверный или отсутствующий MAC-адрес: {MAC_ADDRESS}")
    raise ValueError("Неверный или отсутствующий MAC-адрес")
if not WHITELIST:
    logger.error("Список whitelist пуст")
    raise ValueError("Список whitelist не может быть пустым")

# Кнопки
keyboard = [["💡 Включить ПК"]]
markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# Проверка авторизации
def check_access(update: Update) -> bool:
    return update.effective_user.id in WHITELIST

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        await update.message.reply_text("⛔ У тебя нет доступа.")
        return
    await update.message.reply_text("Привет! Нажми кнопку, чтобы включить ПК.", reply_markup=markup)

# Обработка кнопки и текстовых сообщений
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_access(update):
        await update.message.reply_text("⛔ У тебя нет доступа.")
        return

    if update.message.text == "💡 Включить ПК":
        try:
            send_magic_packet(MAC_ADDRESS, ip_address=BROADCAST_IP)
            logger.info(f"Магический пакет отправлен на {MAC_ADDRESS} через {BROADCAST_IP}")
            await update.message.reply_text("✅ Магический пакет отправлен! ПК должен проснуться.")
        except ValueError as ve:
            logger.error(f"Ошибка при отправке пакета: {ve}")
            await update.message.reply_text(f"⚠️ Ошибка: Неверный MAC-адрес или IP. ({ve})")
        except OSError as ose:
            logger.error(f"Сетевая ошибка: {ose}")
            await update.message.reply_text(f"⚠️ Сетевая ошибка: {ose}")
        except Exception as e:
            logger.error(f"Неизвестная ошибка: {e}")
            await update.message.reply_text(f"⚠️ Неизвестная ошибка: {e}")
    else:
        await update.message.reply_text("Пожалуйста, используй кнопку для включения ПК.", reply_markup=markup)

# Обработка ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка в боте: {context.error}")
    if update:
        await update.message.reply_text("⚠️ Произошла ошибка, попробуй снова позже.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, button_handler))
    app.add_error_handler(error_handler)

    logger.info("Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()