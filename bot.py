import telebot
from telebot import types
import time
import logging
import sys

# ========== НАСТРОЙКИ ==========
TOKEN = "8086950668:AAFPUcf3FINRtaHt9mtGJXfjdf5loOZwlTo"

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Глобальная блокировка - только один экземпляр
bot_instance_lock = False

# ========== СОЗДАНИЕ БОТА ==========
bot = telebot.TeleBot(TOKEN)

# ========== ОБРАБОТЧИКИ ==========
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    # Сбрасываем старые данные пользователя
    if user_id in user_data:
        del user_data[user_id]
    
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton('Добро пожаловать в акцию!', callback_data='welcome'),
        types.InlineKeyboardButton('Перейти в канал организаторов', url='https://t.me/poyezd_chudes')
    )
    
    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}!\n\n"
        f"Добро пожаловать в акцию \"Поезд Чудес\" 🚂🎄🎁\n"
        f"Здесь вы можете выбрать желание ребёнка и подарить праздник.",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == 'welcome':
        bot.send_message(call.message.chat.id, 
                        "Пожалуйста, напишите номер конверта, который вы выбрали.")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, handle_text)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {}
    
    if 'number' not in user_data[user_id]:
        if message.text.isdigit():
            user_data[user_id]['number'] = int(message.text)
            msg = bot.reply_to(message, 
                              "Спасибо! Теперь напишите ваш номер телефона для обратной связи.")
            bot.register_next_step_handler(msg, process_phone_number)
        else:
            bot.reply_to(message, "Некорректный ввод. Введите номер конверта цифрами.")
    else:
        bot.reply_to(message, "Вы уже ввели номер конверта.")

def process_phone_number(message):
    user_id = message.from_user.id
    phone = message.text.strip()
    
    if len(phone) >= 10 and (phone.startswith('+') or phone.startswith('8') or phone.isdigit()):
        user_data[user_id]['phone'] = phone
        confirmation = f"Ваш конверт №{user_data[user_id]['number']}, телефон: {user_data[user_id]['phone']}. Все верно?"
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Да'), types.KeyboardButton('Нет'))
        
        bot.send_message(message.chat.id, confirmation, reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(message.chat.id, confirm_data)
    else:
        bot.reply_to(message, "Некорректный номер телефона.")

def confirm_data(message):
    user_id = message.from_user.id
    
    if message.text.lower() == 'да':
        bot.send_message(
            message.chat.id,
            f"✅ Конверт №{user_data[user_id]['number']} зафиксирован!\n"
            f"Обратная связь: @poyezd_chudes\n"
            f"Спасибо за участие!"
        )
        logger.info(f"Конверт зарегистрирован: {user_data[user_id]}")
        if user_id in user_data:
            del user_data[user_id]
            
    elif message.text.lower() == 'нет':
        bot.send_message(message.chat.id, "Введите данные заново.")
        if user_id in user_data:
            del user_data[user_id]
        start(message)

# ========== ЗАПУСК ==========
def safe_polling():
    """Безопасный запуск polling с защитой от дублирования"""
    global bot_instance_lock
    
    if bot_instance_lock:
        logger.error("❌ Уже запущен другой экземпляр бота!")
        return
    
    bot_instance_lock = True
    
    try:
        # Удаляем возможные вебхуки
        logger.info("🔄 Удаляю старые вебхуки...")
        try:
            bot.delete_webhook(drop_pending_updates=True)
            logger.info("✅ Вебхуки удалены")
        except Exception as e:
            logger.warning(f"Не удалось удалить вебхуки: {e}")
        
        # Запускаем polling
        logger.info("🚀 Запуск Telegram бота...")
        logger.info("📡 Использую polling метод")
        logger.info("⚠️  Убедитесь что нет других запущенных экземпляров")
        
        bot.polling(
            none_stop=True,
            interval=0,
            timeout=20,
            skip_pending=True,  # Игнорируем старые сообщения
            allowed_updates=['message', 'callback_query']
        )
        
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        logger.info("Перезапуск через 10 секунд...")
        time.sleep(10)
        safe_polling()  # Рекурсивный перезапуск
    finally:
        bot_instance_lock = False

if __name__ == '__main__':
    # Ждем 5 секунд перед запуском (даем время остановиться другим экземплярам)
    logger.info("⏳ Жду 5 секунд перед запуском...")
    time.sleep(5)
    
    safe_polling()