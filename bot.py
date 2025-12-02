import telebot
from telebot import types
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = "8086950668:AAFPUcf3FINRtaHt9mtGJXfjdf5loOZwlTo"
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables. Please add it to your Replit Secrets.")

bot = telebot.TeleBot(TOKEN)

data = {}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    itembtna = types.InlineKeyboardButton('Добро пожаловать в акцию!', callback_data='welcome')
    itembtnb = types.InlineKeyboardButton('Перейти в канал организаторов', url='https://t.me/poyezd_chudes')
    markup.add(itembtna, itembtnb)
    bot.send_message(message.chat.id, f"Привет, {message.from_user.first_name}!\n\nДобро пожаловать в акцию \"Поезд Чудес\" 🚂🎄🎁\nЗдесь вы можете выбрать желание ребёнка и подарить праздник.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == 'welcome':
        bot.send_message(call.message.chat.id, "Пожалуйста, напишите номер конверта, который вы выбрали.")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, handle_text)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if 'number' not in data:
        if message.text.isdigit():
            data['number'] = int(message.text)
            msg = bot.reply_to(message, "Спасибо! Теперь напишите ваш номер телефона для обратной связи.")
            bot.register_next_step_handler(msg, process_phone_number)
        else:
            bot.reply_to(message, "Некорректный ввод номера конверта. Попробуйте ещё раз.")
    else:
        bot.reply_to(message, "Вы уже ввели номер конверта. Пожалуйста, следуйте инструкциям.")

def process_phone_number(message):
    phone = message.text.strip()
    # Проверяем валидность номера телефона (очень простая проверка)
    if len(phone) >= 10 and (phone.startswith('+') or phone.startswith('8') or phone.isdigit()):
        data['phone'] = phone
        confirmation_message = f"Ваш конверт №{data['number']}, номер телефона: {data['phone']}. Все верно?"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        itembtn_yes = types.KeyboardButton('Да')
        itembtn_no = types.KeyboardButton('Нет')
        markup.add(itembtn_yes, itembtn_no)
        bot.send_message(message.chat.id, confirmation_message, reply_markup=markup)
        bot.register_next_step_handler_by_chat_id(message.chat.id, confirm_data)
    else:
        bot.reply_to(message, "Некорректный номер телефона. Повторите попытку.")

def confirm_data(message):
    if message.text.lower() == 'да':
        bot.send_message(message.chat.id, f"Супер! Ваш конверт №{data['number']} зафиксирован. Обратная связь со стороны организаторов доступна тут @poyezd_chudes. Спасибо за участие!")
        print(f"Данные записаны: конверт {data['number']}, телефон {data['phone']}")
    elif message.text.lower() == 'нет':
        bot.send_message(message.chat.id, "Пожалуйста, введите данные заново.")
        data.clear()
        start(message)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, выберите 'Да' или 'Нет'.")

if __name__ == '__main__':
    bot.polling(none_stop=True)