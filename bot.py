import urllib.request
import urllib.parse
import json
import time
from datetime import datetime

BOT_TOKEN = '8086950668:AAFPUcf3FINRtaHt9mtGJXfjdf5loOZwlTo'
BASE_URL = f'https://api.telegram.org/bot{BOT_TOKEN}'

# Хранилище данных пользователей
user_data = {}

def set_bot_commands():
    """Установка команд меню бота"""
    url = f'{BASE_URL}/setMyCommands'
    commands = [
        {
            "command": "start",
            "description": "Начать акцию 'Поезд Чудес'"
        },
        {
            "command": "callback",
            "description": "Обратная связь с организаторами"
        }
    ]
    payload = {
        "commands": commands
    }
    return make_request(url, payload)

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

def send_message(chat_id, text, reply_markup=None, parse_mode='HTML'):
    """Отправка сообщения пользователю"""
    url = f'{BASE_URL}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': parse_mode
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

def handle_start_command(chat_id, user_first_name):
    """Обработка команды /start"""
    # Создаем инлайн-кнопки
    keyboard = {
        'inline_keyboard': [
            [
                {'text': 'Добро пожаловать в акцию!', 'callback_data': 'welcome'}
            ],
            [
                {'text': 'Перейти в канал организаторов', 'url': 'https://t.me/poyezd_chudes'}
            ]
        ]
    }
    
    welcome_text = (
        f"Привет, {user_first_name}!\n\n"
        "Добро пожаловать в акцию \"Поезд Чудес\" 🚂🎄🎁\n"
        "Здесь вы можете выбрать желание ребёнка и подарить праздник."
    )
    
    send_message(chat_id, welcome_text, reply_markup=keyboard)

def handle_callback_command(chat_id):
    """Обработка команды /callback"""
    send_message(chat_id, "Обратная связь со стороны организаторов доступна тут @poyezd_chudes")

def handle_welcome_callback(chat_id, message_id, callback_query_id):
    """Обработка нажатия на кнопку 'Добро пожаловать в акцию!'"""
    # Отвечаем на callback query
    answer_callback_query(callback_query_id)
    
    # Отправляем сообщение
    send_message(chat_id, "Пожалуйста, напишите номер конверта, который вы выбрали.")
    
    # Инициализируем данные пользователя
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]['state'] = 'waiting_envelope'

def handle_envelope(chat_id, text):
    """Обработка номера конверта"""
    if text.isdigit():
        user_data[chat_id]['number'] = int(text)
        user_data[chat_id]['state'] = 'waiting_phone'
        send_message(chat_id, "Спасибо! Теперь напишите ваш номер телефона для обратной связи.")
    else:
        send_message(chat_id, "Некорректный ввод номера конверта. Попробуйте ещё раз.")

def handle_phone(chat_id, text):
    """Обработка номера телефона"""
    phone = text.strip()
    # Простая проверка номера телефона
    if len(phone) >= 10 and (phone.startswith('+') or phone.startswith('8') or phone.isdigit()):
        user_data[chat_id]['phone'] = phone
        
        # Создаем клавиатуру с кнопками Да/Нет
        keyboard = {
            'keyboard': [
                [{'text': 'Да'}],
                [{'text': 'Нет'}]
            ],
            'resize_keyboard': True,
            'one_time_keyboard': True
        }
        
        number = user_data[chat_id]['number']
        phone_number = user_data[chat_id]['phone']
        
        confirmation_message = f"Ваш конверт №{number}, номер телефона: {phone_number}. Все верно?"
        send_message(chat_id, confirmation_message, reply_markup=keyboard)
        user_data[chat_id]['state'] = 'waiting_confirmation'
    else:
        send_message(chat_id, "Некорректный номер телефона. Повторите попытку.")

def handle_confirmation(chat_id, text):
    """Обработка подтверждения"""
    if text.lower() == 'да':
        number = user_data[chat_id]['number']
        send_message(chat_id, f"Супер! Ваш конверт №{number} зафиксирован. Обратная связь со стороны организаторов доступна тут @poyezd_chudes. Спасибо за участие!")
        print(f"Данные записаны: конверт {number}, телефон {user_data[chat_id]['phone']}")
        # Удаляем состояние пользователя
        if chat_id in user_data:
            del user_data[chat_id]
    elif text.lower() == 'нет':
        send_message(chat_id, "Пожалуйста, введите данные заново.")
        # Сбрасываем данные пользователя
        if chat_id in user_data:
            user_data[chat_id] = {'state': 'waiting_envelope'}
        send_message(chat_id, "Пожалуйста, напишите номер конверта, который вы выбрали.")
    else:
        send_message(chat_id, "Пожалуйста, выберите 'Да' или 'Нет'.")

def process_message(update):
    """Обработка текстового сообщения"""
    if 'message' in update:
        message = update['message']
        chat_id = message['chat']['id']
        text = message.get('text', '')
        user_first_name = message['from'].get('first_name', 'друг')
        
        # Обработка команды /start
        if text == '/start':
            handle_start_command(chat_id, user_first_name)
            # Инициализируем данные пользователя
            if chat_id in user_data:
                del user_data[chat_id]
            return
        
        # Обработка команды /callback
        elif text == '/callback':
            handle_callback_command(chat_id)
            return
        
        # Обработка обычных сообщений в зависимости от состояния
        if chat_id in user_data:
            state = user_data[chat_id].get('state', '')
            
            if state == 'waiting_envelope':
                handle_envelope(chat_id, text)
            elif state == 'waiting_phone':
                handle_phone(chat_id, text)
            elif state == 'waiting_confirmation':
                handle_confirmation(chat_id, text)
            else:
                # Если состояние неизвестно, отправляем приветствие
                handle_start_command(chat_id, user_first_name)
        else:
            # Если нет состояния, отправляем приветствие
            handle_start_command(chat_id, user_first_name)

def process_callback_query(update):
    """Обработка callback-запроса от инлайн-кнопок"""
    callback_query = update['callback_query']
    chat_id = callback_query['message']['chat']['id']
    message_id = callback_query['message']['message_id']
    callback_data = callback_query['data']
    callback_query_id = callback_query['id']
    
    # Обработка кнопки "Добро пожаловать в акцию!"
    if callback_data == 'welcome':
        handle_welcome_callback(chat_id, message_id, callback_query_id)

def main():
    """Основной цикл бота"""
    print(f"Бот запущен! {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Проверяем токен
    if BOT_TOKEN == 'ВАШ_ТОКЕН_БОТА':
        print("ОШИБКА: Замените 'ВАШ_ТОКЕН_БОТА' на реальный токен от @BotFather!")
        print("Пример: BOT_TOKEN = '1234567890:AAFmEXAMPLE_TOKEN_HERE'")
        return
    
    print(f"Используется токен: {BOT_TOKEN[:10]}...")
    
    # Устанавливаем команды меню бота
    print("Устанавливаю команды меню...")
    result = set_bot_commands()
    if result and result.get('ok'):
        print("Команды меню установлены успешно!")
    else:
        print(f"Ошибка установки команд: {result}")
    
    offset = None
    
    while True:
        try:
            updates = get_updates(offset)
            
            if updates and 'result' in updates:
                for update in updates['result']:
                    offset = update['update_id'] + 1
                    
                    # Обработка callback-запросов (нажатие на инлайн-кнопки)
                    if 'callback_query' in update:
                        process_callback_query(update)
                    # Обработка текстовых сообщений
                    elif 'message' in update:
                        process_message(update)
            
            # Небольшая пауза между запросами
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            print("\nБот остановлен.")
            break
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)

if __name__ == '__main__':
    main()