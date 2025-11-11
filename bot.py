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

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}!\n\nДобро пожаловать в акцию \"Поезд Чудес\" 🚂🎄🎁\nЗдесь вы можете выбрать желание ребёнка и подарить праздник.\nНапишите номер конверта, который выбрали.", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    if message.text.lower() == 'привет':
        bot.send_message(message.chat.id, "Привет! Чтобы начать, введите номер конверта.", reply_markup=get_main_keyboard())
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
        bot.send_message(message.chat.id, f"Супер! Ваш конверт №{envelope_number} зафиксирован. Обратная связь со стороны организаторов доступна тут @poyezd_chudes. Спасибо за участие!", reply_markup=get_main_keyboard())
        print(f"Данные записаны: пользователь {chat_id}, конверт {envelope_number}, телефон {phone}")
    else:
        msg = bot.send_message(message.chat.id, "Некорректный номер телефона. Повторите попытку.", reply_markup=get_main_keyboard())
        bot.register_next_step_handler(msg, process_phone_number)

if __name__ == '__main__':
    print("Бот запущен и готов к работе!")
    bot.polling(none_stop=True)
