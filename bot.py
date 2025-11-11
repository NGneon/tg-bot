import telebot
from telebot import types
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables. Please add it to your Replit Secrets.")

bot = telebot.TeleBot(TOKEN)

user_data = {}

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    itembtna = types.KeyboardButton('Привет!')
    markup.add(itembtna)
    return markup

def get_confirmation_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.row(types.KeyboardButton('✅ Да, всё верно'), types.KeyboardButton('❌ Нет, начать заново'))
    return markup

def get_after_completion_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton('Привет!'))
    markup.row(types.KeyboardButton('🎁 Выбрать другой конверт'))
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}!\n\nДобро пожаловать в акцию \"Поезд Чудес\" 🚂🎄🎁\nЗдесь вы можете выбрать желание ребёнка и подарить праздник.\nНапишите номер конверта, который выбрали.", reply_markup=get_main_keyboard())

@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
📖 *Инструкция по использованию бота \"Поезд Чудес\"*

*Как принять участие:*
1️⃣ Отправьте /start для начала
2️⃣ Введите номер конверта, который вы выбрали
3️⃣ Укажите ваш номер телефона для связи
4️⃣ Подтвердите введённые данные
5️⃣ Получите подтверждение регистрации!

*Команды бота:*
/start - Начать выбор конверта
/help - Показать эту инструкцию

*Контакты организаторов:*
@poyezd_chudes

Спасибо, что дарите чудеса! 🎄✨
    """
    bot.send_message(message.chat.id, help_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    
    if message.text.lower() == 'привет' or message.text == 'Привет!':
        bot.send_message(message.chat.id, "Привет! Чтобы начать, введите номер конверта.", reply_markup=get_main_keyboard())
    
    elif message.text == '🎁 Выбрать другой конверт':
        if chat_id in user_data:
            user_data[chat_id].clear()
        bot.send_message(message.chat.id, "Отлично! Введите номер нового конверта:", reply_markup=get_main_keyboard())
    
    elif message.text == '✅ Да, всё верно':
        if chat_id in user_data and 'number' in user_data[chat_id] and 'phone' in user_data[chat_id]:
            envelope_number = user_data[chat_id]['number']
            phone = user_data[chat_id]['phone']
            bot.send_message(message.chat.id, f"Супер! Ваш конверт №{envelope_number} зафиксирован. Обратная связь со стороны организаторов доступна тут @poyezd_chudes. Спасибо за участие! 🎄", reply_markup=get_after_completion_keyboard())
            print(f"Данные записаны: пользователь {chat_id}, конверт {envelope_number}, телефон {phone}")
        else:
            bot.send_message(message.chat.id, "Произошла ошибка. Пожалуйста, начните заново с /start", reply_markup=get_main_keyboard())
    
    elif message.text == '❌ Нет, начать заново':
        if chat_id in user_data:
            user_data[chat_id].clear()
        bot.send_message(message.chat.id, "Хорошо! Давайте начнём заново. Введите номер конверта:", reply_markup=get_main_keyboard())
    
    elif message.text.isdigit():
        if chat_id not in user_data:
            user_data[chat_id] = {}
        user_data[chat_id]['number'] = int(message.text)
        msg = bot.send_message(message.chat.id, "Спасибо! Теперь напишите ваш номер телефона для обратной связи.", reply_markup=get_main_keyboard())
        bot.register_next_step_handler(msg, process_phone_number)
    
    else:
        bot.send_message(message.chat.id, "Некорректный ввод. Пожалуйста, введите номер конверта или используйте команду /start.", reply_markup=get_main_keyboard())

def process_phone_number(message):
    chat_id = message.chat.id
    phone = message.text.strip()
    
    if len(phone) >= 10 and (phone.startswith('+') or phone.isdigit()):
        user_data[chat_id]['phone'] = phone
        envelope_number = user_data[chat_id]['number']
        
        phone_masked = phone[:5] + '...' if len(phone) > 5 else phone
        
        confirmation_text = f"📋 *Проверьте введённые данные:*\n\n🎁 Конверт: №{envelope_number}\n📱 Телефон: {phone_masked}\n\nВсё верно?"
        
        bot.send_message(message.chat.id, confirmation_text, parse_mode='Markdown', reply_markup=get_confirmation_keyboard())
    else:
        msg = bot.send_message(message.chat.id, "Некорректный номер телефона. Повторите попытку.", reply_markup=get_main_keyboard())
        bot.register_next_step_handler(msg, process_phone_number)

if __name__ == '__main__':
    print("Бот запущен и готов к работе!")
    bot.polling(none_stop=True)
