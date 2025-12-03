import urllib.request
import urllib.parse
import urllib.error
import json
import time
from datetime import datetime
import os
import csv
from pathlib import Path
import sys

# Токен вашего бота - замените на ваш токен
BOT_TOKEN = 'ВАШ_ТОКЕН_БОТА'  # Например: '1234567890:AAFmEXAMPLE_TOKEN_HERE'
BASE_URL = f'https://api.telegram.org/bot{BOT_TOKEN}'

# Хранилище данных пользователей
user_data = {}

# Папка для логов
LOG_FOLDER = "bot_logs"
MESSAGES_LOG_FILE = os.path.join(LOG_FOLDER, "messages_log.csv")
USERS_LOG_FILE = os.path.join(LOG_FOLDER, "users_log.csv")

# Создаем папку для логов, если ее нет
Path(LOG_FOLDER).mkdir(exist_ok=True)

# Проверяем и создаем файлы логов с заголовками
def init_log_files():
    """Инициализация файлов логов с заголовками"""
    try:
        # Лог сообщений
        if not os.path.exists(MESSAGES_LOG_FILE):
            with open(MESSAGES_LOG_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'user_id', 'username', 'first_name', 'last_name', 
                               'chat_id', 'message_type', 'message_text', 'response_sent'])

        # Лог пользователей
        if not os.path.exists(USERS_LOG_FILE):
            with open(USERS_LOG_FILE, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['user_id', 'username', 'first_name', 'last_name', 
                               'first_seen', 'last_seen', 'total_messages'])
    except Exception as e:
        print(f"Ошибка при инициализации файлов логов: {e}")

# Глобальный словарь для отслеживания пользователей
users_tracking = {}

def log_message(user_id, username, first_name, last_name, chat_id, message_type, message_text, response_sent):
    """Логирование сообщения пользователя"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with open(MESSAGES_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, user_id, username or "", first_name or "", last_name or "", 
                            chat_id, message_type, message_text, response_sent])
        
        # Обновляем информацию о пользователе
        update_user_info(user_id, username, first_name, last_name)
    except Exception as e:
        print(f"Ошибка при логировании сообщения: {e}")

def update_user_info(user_id, username, first_name, last_name):
    """Обновление информации о пользователе"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if user_id not in users_tracking:
            users_tracking[user_id] = {
                'username': username or "",
                'first_name': first_name or "",
                'last_name': last_name or "",
                'first_seen': timestamp,
                'last_seen': timestamp,
                'total_messages': 1
            }
            # Записываем нового пользователя в файл
            with open(USERS_LOG_FILE, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([user_id, username or "", first_name or "", last_name or "", 
                               timestamp, timestamp, 1])
        else:
            users_tracking[user_id]['last_seen'] = timestamp
            users_tracking[user_id]['total_messages'] += 1
            
            # Обновляем файл
            update_users_file()
    except Exception as e:
        print(f"Ошибка при обновлении информации о пользователе: {e}")

def update_users_file():
    """Обновление файла с пользователями"""
    try:
        with open(USERS_LOG_FILE, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['user_id', 'username', 'first_name', 'last_name', 
                           'first_seen', 'last_seen', 'total_messages'])
            
            for user_id, info in users_tracking.items():
                writer.writerow([user_id, info['username'], info['first_name'], info['last_name'],
                               info['first_seen'], info['last_seen'], info['total_messages']])
    except Exception as e:
        print(f"Ошибка при обновлении файла пользователей: {e}")

def show_logs_menu():
    """Показ меню логов в консоли"""
    print("\n" + "="*50)
    print("МЕНЮ ПРОСМОТРА ЛОГОВ")
    print("="*50)
    print("1. Показать последние 10 сообщений")
    print("2. Показать всех пользователей")
    print("3. Поиск сообщений по пользователю")
    print("4. Показать статистику")
    print("5. Очистить экран")
    print("6. Продолжить работу бота")
    print("="*50)
    print("Введите номер команды и нажмите Enter:")

def display_recent_messages(limit=10):
    """Показать последние сообщения"""
    try:
        with open(MESSAGES_LOG_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            if len(rows) <= 1:
                print("\nЛог сообщений пуст.")
                return
            
            print(f"\nПоследние {limit} сообщений:")
            print("-"*80)
            print(f"{'Время':<20} {'Пользователь':<25} {'Сообщение':<30}")
            print("-"*80)
            
            # Показываем последние limit сообщений (исключая заголовок)
            for row in reversed(rows[1:][-limit:]):
                timestamp = row[0]
                username = row[2] if row[2] else "без username"
                first_name = row[3] if row[3] else ""
                user_display = f"{first_name} (@{username})" if username != "без username" else first_name
                message = row[7][:30] + "..." if len(row[7]) > 30 else row[7]
                print(f"{timestamp:<20} {user_display:<25} {message:<30}")
                
    except Exception as e:
        print(f"Ошибка при чтении логов: {e}")

def display_all_users():
    """Показать всех пользователей"""
    try:
        with open(USERS_LOG_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            if len(rows) <= 1:
                print("\nНет зарегистрированных пользователей.")
                return
            
            print(f"\nВсе пользователи ({len(rows)-1} чел.):")
            print("-"*80)
            print(f"{'ID':<12} {'Имя':<15} {'Username':<15} {'Сообщений':<10} {'Первое':<20}")
            print("-"*80)
            
            for row in rows[1:]:
                user_id = row[0]
                username = row[1] if row[1] else "нет"
                first_name = row[2] if row[2] else ""
                total_msg = row[6]
                first_seen = row[4]
                print(f"{user_id:<12} {first_name:<15} @{username:<14} {total_msg:<10} {first_seen:<20}")
                
    except Exception as e:
        print(f"Ошибка при чтении пользователей: {e}")

def search_messages_by_user():
    """Поиск сообщений по пользователю"""
    user_id = input("\nВведите ID пользователя для поиска: ").strip()
    
    try:
        with open(MESSAGES_LOG_FILE, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            
            user_messages = []
            for row in rows[1:]:
                if row[1] == user_id:
                    user_messages.append(row)
            
            if not user_messages:
                print(f"Сообщений от пользователя {user_id} не найдено.")
                return
            
            print(f"\nНайдено {len(user_messages)} сообщений от пользователя {user_id}:")
            print("-"*80)
            print(f"{'Время':<20} {'Тип':<10} {'Сообщение':<50}")
            print("-"*80)
            
            for msg in user_messages[-20:]:  # Показываем последние 20 сообщений
                timestamp = msg[0]
                msg_type = msg[6]
                message = msg[7][:50] + "..." if len(msg[7]) > 50 else msg[7]
                print(f"{timestamp:<20} {msg_type:<10} {message:<50}")
                
    except Exception as e:
        print(f"Ошибка при поиске: {e}")

def show_statistics():
    """Показать статистику"""
    try:
        # Статистика сообщений
        if os.path.exists(MESSAGES_LOG_FILE):
            with open(MESSAGES_LOG_FILE, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                total_messages = len(rows) - 1 if len(rows) > 1 else 0
        else:
            total_messages = 0
        
        # Статистика пользователей
        if os.path.exists(USERS_LOG_FILE):
            with open(USERS_LOG_FILE, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                total_users = len(rows) - 1 if len(rows) > 1 else 0
        else:
            total_users = 0
        
        print("\n" + "="*50)
        print("СТАТИСТИКА БОТА")
        print("="*50)
        print(f"Всего пользователей: {total_users}")
        print(f"Всего сообщений: {total_messages}")
        print(f"Лог файлы:")
        print(f"  - Сообщения: {MESSAGES_LOG_FILE}")
        print(f"  - Пользователи: {USERS_LOG_FILE}")
        
        if os.path.exists(MESSAGES_LOG_FILE):
            print(f"Размер файла логов: {os.path.getsize(MESSAGES_LOG_FILE) / 1024:.2f} KB")
        print("="*50)
        
    except Exception as e:
        print(f"Ошибка при получении статистики: {e}")

def console_log_menu():
    """Меню управления логами в консоли"""
    import threading
    
    def menu_thread():
        while True:
            show_logs_menu()
            choice = input("Ваш выбор: ").strip()
            
            if choice == '1':
                display_recent_messages()
            elif choice == '2':
                display_all_users()
            elif choice == '3':
                search_messages_by_user()
            elif choice == '4':
                show_statistics()
            elif choice == '5':
                os.system('cls' if os.name == 'nt' else 'clear')
            elif choice == '6':
                print("Продолжаем работу бота...")
                break
            else:
                print("Неверный выбор. Попробуйте снова.")
            
            input("\nНажмите Enter чтобы продолжить...")
    
    # Запускаем меню в отдельном потоке
    menu_thread_instance = threading.Thread(target=menu_thread, daemon=True)
    menu_thread_instance.start()

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
    try:
        if data and method == 'POST':
            data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        else:
            req = urllib.request.Request(url)
        
        req.add_header('User-Agent', 'TelegramBot/1.0')
        
        with urllib.request.urlopen(req, timeout=30) as response:
            response_data = response.read().decode('utf-8')
            return json.loads(response_data)
            
    except urllib.error.HTTPError as e:
        print(f"HTTP ошибка {e.code}: {e.reason}")
        if e.code == 404:
            print(f"URL не найден: {url}")
        elif e.code == 401:
            print("Неверный токен бота!")
        return None
    except urllib.error.URLError as e:
        print(f"URL ошибка: {e.reason}")
        return None
    except json.JSONDecodeError as e:
        print(f"Ошибка декодирования JSON: {e}")
        return None
    except Exception as e:
        print(f"Ошибка запроса к {url}: {e}")
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
    
    response = make_request(url, payload)
    
    return response

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
    response = make_request(url_with_params, method='GET')
    
    if response and 'ok' in response:
        if response['ok']:
            return response
        else:
            print(f"Ошибка в ответе getUpdates: {response.get('description', 'Неизвестная ошибка')}")
    elif response is None:
        print("Пустой ответ от getUpdates")
    
    return None

def answer_callback_query(callback_query_id):
    """Ответ на callback query"""
    url = f'{BASE_URL}/answerCallbackQuery'
    payload = {'callback_query_id': callback_query_id}
    
    response = make_request(url, payload)
    
    if response and 'ok' in response:
        if not response['ok']:
            print(f"Ошибка в answerCallbackQuery: {response.get('description', 'Неизвестная ошибка')}")
    
    return response

def handle_start_command(chat_id, user_info):
    """Обработка команды /start"""
    # Логируем команду
    log_message(
        user_info['id'], user_info.get('username'), 
        user_info.get('first_name'), user_info.get('last_name'),
        chat_id, 'command', '/start', 'Приветственное сообщение'
    )
    
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
        f"Привет, {user_info.get('first_name', 'друг')}!\n\n"
        "Добро пожаловать в акцию \"Поезд Чудес\" 🚂🎄🎁\n"
        "Здесь вы можете выбрать желание ребёнка и подарить праздник."
    )
    
    send_message(chat_id, welcome_text, reply_markup=keyboard)

def handle_callback_command(chat_id, user_info):
    """Обработка команды /callback"""
    # Логируем команду
    log_message(
        user_info['id'], user_info.get('username'), 
        user_info.get('first_name'), user_info.get('last_name'),
        chat_id, 'command', '/callback', 'Ссылка на канал'
    )
    
    send_message(chat_id, "Обратная связь со стороны организаторов доступна тут @poyezd_chudes")

def handle_welcome_callback(chat_id, message_id, callback_query_id, user_info):
    """Обработка нажатия на кнопку 'Добро пожаловать в акцию!'"""
    # Отвечаем на callback query
    answer_callback_query(callback_query_id)
    
    # Логируем нажатие кнопки
    log_message(
        user_info['id'], user_info.get('username'), 
        user_info.get('first_name'), user_info.get('last_name'),
        chat_id, 'button', 'welcome', 'Запрос номера конверта'
    )
    
    # Отправляем сообщение
    send_message(chat_id, "Пожалуйста, напишите номер конверта, который вы выбрали.")
    
    # Инициализируем данные пользователя
    if chat_id not in user_data:
        user_data[chat_id] = {}
    user_data[chat_id]['state'] = 'waiting_envelope'

def handle_envelope(chat_id, text, user_info):
    """Обработка номера конверта"""
    if text.isdigit():
        user_data[chat_id]['number'] = int(text)
        user_data[chat_id]['state'] = 'waiting_phone'
        
        # Логируем ввод номера конверта
        log_message(
            user_info['id'], user_info.get('username'), 
            user_info.get('first_name'), user_info.get('last_name'),
            chat_id, 'message', f"Конверт: {text}", 'Запрос телефона'
        )
        
        send_message(chat_id, "Спасибо! Теперь напишите ваш номер телефона для обратной связи.")
    else:
        log_message(
            user_info['id'], user_info.get('username'), 
            user_info.get('first_name'), user_info.get('last_name'),
            chat_id, 'message', text, 'Ошибка ввода'
        )
        send_message(chat_id, "Некорректный ввод номера конверта. Попробуйте ещё раз.")

def handle_phone(chat_id, text, user_info):
    """Обработка номера телефона"""
    phone = text.strip()
    
    # Логируем ввод телефона
    log_message(
        user_info['id'], user_info.get('username'), 
        user_info.get('first_name'), user_info.get('last_name'),
        chat_id, 'message', f"Телефон: {text}", 'Подтверждение данных'
    )
    
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

def handle_confirmation(chat_id, text, user_info):
    """Обработка подтверждения"""
    # Логируем ответ
    log_message(
        user_info['id'], user_info.get('username'), 
        user_info.get('first_name'), user_info.get('last_name'),
        chat_id, 'message', text, 'Обработка подтверждения'
    )
    
    if text.lower() == 'да':
        number = user_data[chat_id]['number']
        phone = user_data[chat_id]['phone']
        
        # Логируем успешное завершение
        log_message(
            user_info['id'], user_info.get('username'), 
            user_info.get('first_name'), user_info.get('last_name'),
            chat_id, 'completion', f"Успешно: конверт {number}, телефон {phone}", 'Завершение акции'
        )
        
        send_message(chat_id, f"Супер! Ваш конверт №{number} зафиксирован. Обратная связь со стороны организаторов доступна тут @poyezd_chudes. Спасибо за участие!")
        
        # Выводим в консоль информацию о завершении
        print(f"\n[УСПЕХ] Пользователь {user_info.get('first_name')} (@{user_info.get('username')}) завершил акцию:")
        print(f"  Конверт: {number}")
        print(f"  Телефон: {phone}")
        print(f"  Время: {datetime.now().strftime('%H:%M:%S')}")
        
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
        user_info = message['from']
        user_id = user_info['id']
        
        # Выводим в консоль информацию о сообщении
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Сообщение от {user_info.get('first_name')} (@{user_info.get('username', 'нет')}):")
        print(f"  Текст: {text[:50]}{'...' if len(text) > 50 else ''}")
        
        # Обработка команды /start
        if text == '/start':
            handle_start_command(chat_id, user_info)
            # Инициализируем данные пользователя
            if chat_id in user_data:
                del user_data[chat_id]
            return
        
        # Обработка команды /callback
        elif text == '/callback':
            handle_callback_command(chat_id, user_info)
            return
        
        # Обработка обычных сообщений в зависимости от состояния
        if chat_id in user_data:
            state = user_data[chat_id].get('state', '')
            
            if state == 'waiting_envelope':
                handle_envelope(chat_id, text, user_info)
            elif state == 'waiting_phone':
                handle_phone(chat_id, text, user_info)
            elif state == 'waiting_confirmation':
                handle_confirmation(chat_id, text, user_info)
            else:
                # Если состояние неизвестно, отправляем приветствие
                handle_start_command(chat_id, user_info)
        else:
            # Логируем сообщение без контекста
            log_message(
                user_id, user_info.get('username'), 
                user_info.get('first_name'), user_info.get('last_name'),
                chat_id, 'message', text, 'Не распознано'
            )
            # Если нет состояния, отправляем приветствие
            handle_start_command(chat_id, user_info)

def process_callback_query(update):
    """Обработка callback-запроса от инлайн-кнопок"""
    callback_query = update['callback_query']
    chat_id = callback_query['message']['chat']['id']
    message_id = callback_query['message']['message_id']
    callback_data = callback_query['data']
    callback_query_id = callback_query['id']
    user_info = callback_query['from']
    
    # Выводим в консоль информацию о нажатии кнопки
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Кнопка от {user_info.get('first_name')} (@{user_info.get('username', 'нет')}):")
    print(f"  Кнопка: {callback_data}")
    
    # Обработка кнопки "Добро пожаловать в акцию!"
    if callback_data == 'welcome':
        handle_welcome_callback(chat_id, message_id, callback_query_id, user_info)

def test_api_connection():
    """Тестирование подключения к API Telegram"""
    print("Тестирую подключение к Telegram API...")
    
    # Тест 1: Проверка токена через getMe
    test_url = f'{BASE_URL}/getMe'
    print(f"Запрос: {test_url}")
    
    try:
        response = make_request(test_url, method='GET')
        if response and response.get('ok'):
            user = response.get('result', {})
            print(f"✓ Успешное подключение!")
            print(f"  Бот: {user.get('first_name')} (@{user.get('username')})")
            print(f"  ID бота: {user.get('id')}")
            return True
        else:
            print(f"✗ Ошибка: {response}")
            if response and 'description' in response:
                print(f"  Описание: {response['description']}")
            return False
    except Exception as e:
        print(f"✗ Исключение при тесте: {e}")
        return False

def main():
    """Основной цикл бота"""
    print(f"Бот запущен! {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Проверяем токен
    if BOT_TOKEN == 'ВАШ_ТОКЕН_БОТА':
        print("ОШИБКА: Замените 'ВАШ_ТОКЕН_БОТА' на реальный токен от @BotFather!")
        print("Пример: BOT_TOKEN = '1234567890:AAFmEXAMPLE_TOKEN_HERE'")
        print("Откройте файл и найдите строку с BOT_TOKEN = ...")
        input("Нажмите Enter для выхода...")
        return
    
    print(f"Используется токен: {BOT_TOKEN[:10]}...")
    
    # Тестируем подключение
    if not test_api_connection():
        print("Не удалось подключиться к Telegram API. Проверьте:")
        print("1. Правильность токена")
        print("2. Интернет-подключение")
        print("3. Доступность Telegram API")
        input("Нажмите Enter для выхода...")
        return
    
    # Инициализируем логи
    init_log_files()
    
    print(f"\nЛоги сохраняются в папке: {LOG_FOLDER}")
    print("Доступные команды:")
    print("  - В консоли: введите номер команды для просмотра логов")
    print("  - В Telegram: /start и /callback")
    
    # Запускаем меню просмотра логов
    import threading
    threading.Thread(target=console_log_menu, daemon=True).start()
    
    # Устанавливаем команды меню бота
    print("\nУстанавливаю команды меню...")
    result = set_bot_commands()
    if result and result.get('ok'):
        print("✓ Команды меню установлены успешно!")
    else:
        print(f"✗ Ошибка установки команд: {result}")
    
    print("\nОжидаю сообщения...")
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
            elif updates is None:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка получения обновлений")
                time.sleep(5)  # Ждем перед повторной попыткой
            
            # Небольшая пауза между запросами
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            print("\n\nБот остановлен.")
            break
        except Exception as e:
            print(f"\nОшибка в основном цикле: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)

if __name__ == '__main__':
    main()