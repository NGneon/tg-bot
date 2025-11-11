import telebot
from telebot import types
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables. Please add it to your Replit Secrets.")

bot = telebot.TeleBot(TOKEN)

data = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    itembtna = types.KeyboardButton('Привет!')
    markup.add(itembtna)
    bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}!\n\nДобро пожаловать в акцию \"Поезд Чудес\" 🎅\nЗдесь вы можете выбрать желание ребёнка и подарить праздник.\nНапишите номер конверта, который выбрали.", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text.isdigit():
        data['number'] = int(message.text)
        msg = bot.reply_to(message, "Спасибо! Теперь напишите ваш номер телефона для обратной связи.")
        bot.register_next_step_handler(msg, process_phone_number)
    else:
        bot.reply_to(message, "Некорректный ввод номера конверта. Попробуйте ещё раз.")

def process_phone_number(message):
    phone = message.text.strip()
    if len(phone) >= 10 and (phone.startswith('+') or phone.isdigit()):
        data['phone'] = phone
        bot.send_message(message.chat.id, f"Супер! Ваш конверт №{data['number']} зафиксирован, обратная связь доступна по номеру {data['phone']}. Спасибо за участие!")
        print(f"Данные записаны: конверт {data['number']}, телефон {data['phone']}")
    else:
        msg = bot.reply_to(message, "Некорректный номер телефона. Повторите попытку.")
        bot.register_next_step_handler(msg, process_phone_number)

if __name__ == '__main__':
    print("Бот запущен и готов к работе!")
    bot.polling(none_stop=True)
