import urllib.request
import urllib.parse
import json
import time
from datetime import datetime

BOT_TOKEN = '8086950668:AAFPUcf3FINRtaHt9mtGJXfjdf5loOZwlTo'
BASE_URL = f'https://api.telegram.org/bot{BOT_TOKEN}'

user_states = {}
user_data = {}

STATE_START = "start"
STATE_WAITING_ENVELOPE = "waiting_envelope"
STATE_WAITING_PHONE = "waiting_phone"
STATE_CONFIRMATION = "confirmation"

def make_request(url, data=None, method='POST'):
    """Универсальная функция для HTTP запросов"""
    if data and method == 'POST':
        data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    else:
        req = urllib.request.Request(url)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Ошибка запроса: {e}")
        return None

def send_message(chat_id, text, reply_markup=None):
    """Отправка сообщения пользователю"""
    url = f'{BASE_URL}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    if reply_markup:
        payload['reply_markup'] = reply_markup
    
    return make_request(url, payload)

def edit_message_reply_markup(chat_id, message_id, reply_markup=None):
    """Изменение разметки сообщения (удаление кнопок)"""
    url = f'{BASE_URL}/editMessageReplyMarkup'
    payload = {
        'chat_id': chat_id,
        'message_id': message_id
    }
    
    if reply_markup is not None:
        payload['reply_markup'] = reply_markup
    
    return make_request(url, payload)

def get_updates(offset=None):
    """Получение обновлений от Telegram"""
    url = f'{BASE_URL}/getUpdates'
    params = {'timeout': 30}
    if offset:
        params['offset'] = offset
    
    url_with_params = f"{url}?{urllib.parse.urlencode(params)}"
    return make_request(url_with_params, method='GET')

def answer_callback_query(callback_query_id):
    """Ответ на callback query"""
    url = f'{BASE_URL}/answerCallbackQuery'
    payload = {'callback_query_id': callback_query_id}
    return make_request(url, payload)

def handle_start(chat_id, message_id=None):
    """Обработка команды /start - показ кнопок"""
    keyboard = {
        'inline_keyboard': [
            [
                {'text': 'Приветствие', 'callback_data': 'hello'},
                {'text': 'Обратная связь', 'callback_data': 'callback'}
            ]
        ]
    }
    
    send_message(chat_id, "Выберите действие:", reply_markup=keyboard)
    user_states[chat_id] = STATE_START

def handle_hello_callback(chat_id, message_id):
    """Обработка кнопки 'Приветствие'"""
    edit_message_reply_markup(chat_id, message_id, {'inline_keyboard': []})
    
    welcome_text = (
        "Добро пожаловать в акцию \"Поезд Чудес\"\n"
        "Здесь вы можете выбрать желание ребёнка и подарить праздник.\n\n"
        "---\n\n"
        "Добро пожаловать в акцию!\n"
        "Перейти в канал организа...\n\n"
        "Пожалуйста, напишите номер конверта, который вы выбрали."
    )
    
    send_message(chat_id, welcome_text)
    user_states[chat_id] = STATE_WAITING_ENVELOPE
    user_data[chat_id] = {}

def handle_callback_callback(chat_id, message_id):
    """Обработка кнопки 'Обратная связь'"""
    edit_message_reply_markup(chat_id, message_id, {'inline_keyboard': []})
    send_message(chat_id, "Обратная связь со стороны организаторов доступна тут @poyezd_ctudes")
    user_states[chat_id] = STATE_START

def handle_envelope(chat_id, text):
    """Обработка номера конверта"""
    user_data[chat_id]['envelope'] = text
    send_message(chat_id, "Спасибо! Теперь напишите ваш номер телефона для обратной связи.")
    user_states[chat_id] = STATE_WAITING_PHONE

def handle_phone(chat_id, text):
    """Обработка номера телефона"""
    user_data[chat_id]['phone'] = text
    
    keyboard = {
        'inline_keyboard': [
            [
                {'text': 'Да', 'callback_data': 'confirm_yes'},
                {'text': 'Нет', 'callback_data': 'confirm_no'}
            ]
        ]
    }
    
    envelope = user_data[chat_id]['envelope']
    phone = user_data[chat_id]['phone']
    
    send_message(chat_id, f"Ваш конверт №{envelope}, номер телефона: {phone}. Все верно?", 
                 reply_markup=keyboard)
    user_states[chat_id] = STATE_CONFIRMATION

def handle_confirmation(chat_id, message_id, callback_data):
    """Обработка подтверждения"""
    edit_message_reply_markup(chat_id, message_id, {'inline_keyboard': []})
    
    if callback_data == 'confirm_yes':
        envelope = user_data[chat_id]['envelope']
        send_message(chat_id, 
                    f"Супер! Ваш конверт №{envelope} зафиксирован. "
                    f"Обратная связь со стороны организаторов доступна тут @poyezd_ctudes. "
                    f"Спасибо за участие!")
    else:
        send_message(chat_id, "Давайте начнем сначала. Напишите номер конверта.")
        user_states[chat_id] = STATE_WAITING_ENVELOPE
    
    if chat_id in user_data:
        del user_data[chat_id]
    user_states[chat_id] = STATE_START

def process_message(update):
    """Обработка текстового сообщения"""
    if 'message' in update:
        message = update['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')
        
        if text == '/start':
            handle_start(chat_id)
            return
        
        if chat_id in user_states:
            state = user_states[chat_id]
            
            if state == STATE_WAITING_ENVELOPE:
                handle_envelope(chat_id, text)
            elif state == STATE_WAITING_PHONE:
                handle_phone(chat_id, text)
            else:
                handle_start(chat_id)

def process_callback_query(update):
    """Обработка callback-запроса от инлайн-кнопок"""
    callback_query = update['callback_query']
    chat_id = callback_query['message']['chat']['id']
    message_id = callback_query['message']['message_id']
    callback_data = callback_query['data']
    
    if callback_data == 'hello':
        handle_hello_callback(chat_id, message_id)
    elif callback_data == 'callback':
        handle_callback_callback(chat_id, message_id)
    elif callback_data in ['confirm_yes', 'confirm_no']:
        handle_confirmation(chat_id, message_id, callback_data)
    
    answer_callback_query(callback_query['id'])

def main():
    """Основной цикл бота"""
    print(f"Бот запущен! {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if BOT_TOKEN == 'ВАШ_ТОКЕН_БОТА':
        print("ОШИБКА: Замените 'ВАШ_ТОКЕН_БОТА' на реальный токен от @BotFather!")
        print("Пример: BOT_TOKEN = '1234567890:AAFmEXAMPLE_TOKEN_HERE'")
        return
    
    print(f"Используется токен: {BOT_TOKEN[:10]}...")
    
    offset = None
    
    while True:
        try:
            updates = get_updates(offset)
            
            if updates and 'result' in updates:
                for update in updates['result']:
                    offset = update['update_id'] + 1
                    
                    if 'callback_query' in update:
                        process_callback_query(update)
                    elif 'message' in update:
                        process_message(update)
            
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            print("\nБот остановлен.")
            break
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()