import telebot
from telebot import types
import time
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8086950668:AAFPUcf3FINRtaHt9mtGJXfjdf5loOZwlTo"
bot = telebot.TeleBot(TOKEN)

# Словарь для хранения данных (user_id: данные)
user_data = {}

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id in user_data:
        del user_data[user_id]  # Сбрасываем старые данные
    
    markup = types.InlineKeyboardMarkup()
    itembtna = types.InlineKeyboardButton('Добро пожаловать в акцию!', callback_data='welcome')
    itembtnb = types.InlineKeyboardButton('Перейти в канал организаторов', url='https://t.me/poyezd_chudes')
    markup.add(itembtna, itembtnb)
    
    bot.send_message(
        message.chat.id,
        f"Привет, {message.from_user.first_name}!\n\n"
        f"Добро пожаловать в акцию \"Поезд Чудес\" 🚂🎄🎁\n"
        f"Здесь вы можете выбрать желание ребёнка и подарить праздник.",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.from_user.id
    if user_id in user_data:
        del user_data[user_id]  # Сбрасываем старые данные
    
    if call.data == 'welcome':
        bot.send_message(call.message.chat.id, "Пожалуйста, напишите номер конверта, который вы выбрали.")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, handle_text)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id
    
    # Инициализируем данные пользователя
    if user_id not in user_data:
        user_data[user_id] = {}
    
    if 'number' not in user_data[user_id]:
        if message.text.isdigit():
            user_data[user_id]['number'] = int(message.text)
            msg = bot.reply_to(message, "Спасибо! Теперь напишите ваш номер телефона для обратной связи.")
            bot.register_next_step_handler(msg, process_phone_number)
        else:
            bot.reply_to(message, "Некорректный ввод номера конверта. Попробуйте ещё раз.")
    else:
        bot.reply_to(message, "Вы уже ввели номер конверта. Пожалуйста, следуйте инструкциям.")

def process_phone_number(message):
    user_id = message.from_user.id
    phone = message.text.strip()
    
    if len(phone) >= 10 and (phone.startswith('+') or phone.startswith('8') or phone.isdigit()):
        user_data[user_id]['phone'] = phone
        confirmation_message = f"Ваш конверт №{user_data[user_id]['number']}, номер телефона: {user_data[user_id]['phone']}. Все верно?"
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        itembtn_yes = types.KeyboardButton('Да')
        itembtn_no = types.KeyboardButton('Нет')
        markup.add(itembtn_yes, itembtn_no)
        
        bot.send_message(message.chat.id, confirmation_message, reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(message.chat.id, confirm_data)
    else:
        bot.reply_to(message, "Некорректный номер телефона. Повторите попытку.")

def confirm_data(message):
    user_id = message.from_user.id
    
    if message.text.lower() == 'да':
        bot.send_message(
            message.chat.id,
            f"Супер! Ваш конверт №{user_data[user_id]['number']} зафиксирован. "
            f"Обратная связь со стороны организаторов доступна тут @poyezd_chudes. "
            f"Спасибо за участие!"
        )
        logger.info(f"Конверт зарегистрирован: {user_id} - {user_data[user_id]}")
        
        # Очищаем данные
        if user_id in user_data:
            del user_data[user_id]
            
    elif message.text.lower() == 'нет':
        bot.send_message(message.chat.id, "Пожалуйста, введите данные заново.")
        if user_id in user_data:
            del user_data[user_id]
        start(message)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, выберите 'Да' или 'Нет'.")

# ЗАПУСК
if __name__ == '__main__':
    logger.info("🤖 Запуск Telegram бота на Render")
    logger.info("⚠️  Убедитесь, что бот не запущен на других сервисах!")
    
    while True:
        try:
            # Пытаемся удалить возможные вебхуки перед запуском
            try:
                bot.delete_webhook(drop_pending_updates=True)
                logger.info("Старые вебхуки удалены")
            except:
                pass
            
            # Запускаем polling
            logger.info("Начинаю polling...")
            bot.polling(
                none_stop=True,
                interval=0,
                timeout=20,
                skip_pending=True,  # Пропускаем старые сообщения
                allowed_updates=['message', 'callback_query']
            )
            
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            logger.info("Перезапуск через 5 секунд...")
            time.sleep(5)