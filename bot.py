import urllib.request
import urllib.parse
import urllib.error
import json
import time
from datetime import datetime
import os
import sys
import sqlite3
from pathlib import Path

# Токен вашего бота - замените на ваш токен
BOT_TOKEN = '8086950668:AAFPUcf3FINRtaHt9mtGJXfjdf5loOZwlTo'  # Например: '1234567890:AAFmEXAMPLE_TOKEN_HERE'
BASE_URL = f'https://api.telegram.org/bot{BOT_TOKEN}'

# Хранилище данных пользователей
user_data = {}

# Настройки базы данных
DB_FILE = "bot_database.db"

# Инициализация базы данных
def init_database():
    """Инициализация базы данных SQLite"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Таблица сообщений
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            chat_id INTEGER NOT NULL,
            message_type TEXT NOT NULL,
            message_text TEXT NOT NULL,
            response_sent TEXT NOT NULL
        )
        ''')
        
        # Таблица пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            total_messages INTEGER DEFAULT 0
        )
        ''')
        
        # Таблица завершенных акций
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            envelope_number INTEGER NOT NULL,
            phone_number TEXT NOT NULL,
            completed_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"✓ База данных инициализирована: {DB_FILE}")
        print(f"  Таблицы: messages, users, completed_actions")
        
        # Показываем статистику
        show_database_stats()
        
    except Exception as e:
        print(f"✗ Ошибка при инициализации базы данных: {e}")
        # Пробуем альтернативный путь
        try:
            alt_db = "/tmp/bot_database.db" if os.name != 'nt' else "C:\\temp\\bot_database.db"
            global DB_FILE
            DB_FILE = alt_db
            init_database()
        except Exception as e2:
            print(f"✗ Критическая ошибка: не удалось создать БД: {e2}")

def show_database_stats():
    """Показать статистику базы данных"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Количество сообщений
        cursor.execute("SELECT COUNT(*) FROM messages")
        total_messages = cursor.fetchone()[0]
        
        # Количество пользователей
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        # Количество завершенных акций
        cursor.execute("SELECT COUNT(*) FROM completed_actions")
        total_completed = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"  Всего сообщений: {total_messages}")
        print(f"  Всего пользователей: {total_users}")
        print(f"  Завершенных акций: {total_completed}")
        
    except Exception as e:
        print(f"  Ошибка при получении статистики: {e}")

def log_message_to_db(user_id, username, first_name, last_name, chat_id, message_type, message_text, response_sent):
    """Логирование сообщения в базу данных"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Вставляем сообщение
        cursor.execute('''
        INSERT INTO messages (timestamp, user_id, username, first_name, last_name, chat_id, message_type, message_text, response_sent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (timestamp, user_id, username, first_name, last_name, chat_id, message_type, message_text, response_sent))
        
        # Обновляем информацию о пользователе
        update_user_in_db(user_id, username, first_name, last_name)
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Ошибка при логировании в БД: {e}")
        return False

def update_user_in_db(user_id, username, first_name, last_name):
    """Обновление информации о пользователе в базе данных"""
    try:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute("SELECT COUNT(*) FROM users WHERE user_id = ?", (user_id,))
        user_exists = cursor.fetchone()[0] > 0
        
        if not user_exists:
            # Добавляем нового пользователя
            cursor.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen, total_messages)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            ''', (user_id, username, first_name, last_name, timestamp, timestamp))
        else:
            # Обновляем существующего пользователя
            cursor.execute('''
            UPDATE users 
            SET username = ?, first_name = ?, last_name = ?, last_seen = ?, total_messages = total_messages + 1
            WHERE user_id = ?
            ''', (username, first_name, last_name, timestamp, user_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Ошибка при обновлении пользователя в БД: {e}")
        return False

def log_completed_action(user_id, envelope_number, phone_number):
    """Логирование завершенной акции"""
    try:
        completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO completed_actions (user_id, envelope_number, phone_number, completed_at)
        VALUES (?, ?, ?, ?)
        ''', (user_id, envelope_number, phone_number, completed_at))
        
        conn.commit()
        conn.close()
        
        # Также выводим в консоль
        print(f"\n[ЗАВЕРШЕНО] Акция завершена:")
        print(f"  User ID: {user_id}")
        print(f"  Конверт: {envelope_number}")
        print(f"  Телефон: {phone_number}")
        print(f"  Время: {completed_at}")
        
        return True
    except Exception as e:
        print(f"Ошибка при логировании завершенной акции: {e}")
        return False

def export_to_csv():
    """Экспорт данных из БД в CSV файлы"""
    try:
        # Создаем папку для экспорта
        export_folder = "bot_export"
        os.makedirs(export_folder, exist_ok=True)
        
        conn = sqlite3.connect(DB_FILE)
        
        # Экспорт сообщений
        messages_file = os.path.join(export_folder, "messages.csv")
        with open(messages_file, 'w', encoding='utf-8') as f:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM messages")
            rows = cursor.fetchall()
            
            if rows:
                # Заголовки
                f.write("id,timestamp,user_id,username,first_name,last_name,chat_id,message_type,message_text,response_sent\n")
                # Данные
                for row in rows:
                    f.write(f"{row['id']},{row['timestamp']},{row['user_id']},{row['username'] or ''},{row['first_name'] or ''},{row['last_name'] or ''},{row['chat_id']},{row['message_type']},{row['message_text']},{row['response_sent']}\n")
        
        # Экспорт пользователей
        users_file = os.path.join(export_folder, "users.csv")
        with open(users_file, 'w', encoding='utf-8') as f:
            cursor.execute("SELECT * FROM users")
            rows = cursor.fetchall()
            
            if rows:
                f.write("user_id,username,first_name,last_name,first_seen,last_seen,total_messages\n")
                for row in rows:
                    f.write(f"{row['user_id']},{row['username'] or ''},{row['first_name'] or ''},{row['last_name'] or ''},{row['first_seen']},{row['last_seen']},{row['total_messages']}\n")
        
        # Экспорт завершенных акций
        actions_file = os.path.join(export_folder, "completed_actions.csv")
        with open(actions_file, 'w', encoding='utf-8') as f:
            cursor.execute("SELECT * FROM completed_actions")
            rows = cursor.fetchall()
            
            if rows:
                f.write("id,user_id,envelope_number,phone_number,completed_at\n")
                for row in rows:
                    f.write(f"{row['id']},{row['user_id']},{row['envelope_number']},{row['phone_number']},{row['completed_at']}\n")
        
        conn.close()
        
        print(f"\n✓ Данные экспортированы в папку: {export_folder}")
        print(f"  Сообщения: {messages_file}")
        print(f"  Пользователи: {users_file}")
        print(f"  Завершенные акции: {actions_file}")
        
        return True
    except Exception as e:
        print(f"✗ Ошибка при экспорте в CSV: {e}")
        return False

# Остальные функции остаются такими же, но меняем log_message на log_message_to_db

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

def get_updates(offset=None):
    """Получение обновлений от Telegram"""
    try:
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
    except Exception as e:
        print(f"Ошибка в get_updates: {e}")
        return None

def answer_callback_query(callback_query_id):
    """Ответ на callback query"""
    try:
        url = f'{BASE_URL}/answerCallbackQuery'
        payload = {'callback_query_id': callback_query_id}
        
        response = make_request(url, payload)
        
        if response and 'ok' in response:
            if not response['ok']:
                print(f"Ошибка в answerCallbackQuery: {response.get('description', 'Неизвестная ошибка')}")
        
        return response
    except Exception as e:
        print(f"Ошибка в answer_callback_query: {e}")
        return None

def handle_start_command(chat_id, user_info):
    """Обработка команды /start"""
    # Логируем команду
    log_message_to_db(
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
    log_message_to_db(
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
    log_message_to_db(
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
        log_message_to_db(
            user_info['id'], user_info.get('username'), 
            user_info.get('first_name'), user_info.get('last_name'),
            chat_id, 'message', f"Конверт: {text}", 'Запрос телефона'
        )
        
        send_message(chat_id, "Спасибо! Теперь напишите ваш номер телефона для обратной связи.")
    else:
        log_message_to_db(
            user_info['id'], user_info.get('username'), 
            user_info.get('first_name'), user_info.get('last_name'),
            chat_id, 'message', text, 'Ошибка ввода'
        )
        send_message(chat_id, "Некорректный ввод номера конверта. Попробуйте ещё раз.")

def handle_phone(chat_id, text, user_info):
    """Обработка номера телефона"""
    phone = text.strip()
    
    # Логируем ввод телефона
    log_message_to_db(
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
    log_message_to_db(
        user_info['id'], user_info.get('username'), 
        user_info.get('first_name'), user_info.get('last_name'),
        chat_id, 'message', text, 'Обработка подтверждения'
    )
    
    if text.lower() == 'да':
        number = user_data[chat_id]['number']
        phone = user_data[chat_id]['phone']
        
        # Логируем успешное завершение в БД
        log_completed_action(user_info['id'], number, phone)
        
        log_message_to_db(
            user_info['id'], user_info.get('username'), 
            user_info.get('first_name'), user_info.get('last_name'),
            chat_id, 'completion', f"Успешно: конверт {number}, телефон {phone}", 'Завершение акции'
        )
        
        send_message(chat_id, f"Супер! Ваш конверт №{number} зафиксирован. Обратная связь со стороны организаторов доступна тут @poyezd_chudes. Спасибо за участие!")
        
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
            log_message_to_db(
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
    print(f"Текущая директория: {os.getcwd()}")
    print(f"Python версия: {sys.version}")
    start_web_viewer()
    print(f"🌐 Веб-интерфейс логов: http://ваш-домен.onrender.com")
    
    # Проверяем токен
    if BOT_TOKEN == 'ВАШ_ТОКЕН_БОТА':
        print("ОШИБКА: Замените 'ВАШ_ТОКЕН_БОТА' на реальный токен от @BotFather!")
        print("Пример: BOT_TOKEN = '1234567890:AAFmEXAMPLE_TOKEN_HERE'")
        return
    
    print(f"Используется токен: {BOT_TOKEN[:10]}...")
    
    # Инициализируем базу данных СРАЗУ
    init_database()
    
    # Тестируем подключение к Telegram
    if not test_api_connection():
        print("Не удалось подключиться к Telegram API.")
        return
    
    # Устанавливаем команды меню бота
    print("\nУстанавливаю команды меню...")
    result = set_bot_commands()
    if result and result.get('ok'):
        print("✓ Команды меню установлены успешно!")
    else:
        print(f"✗ Ошибка установки команд: {result}")
    
    print("\n" + "="*50)
    print("КОМАНДЫ ДЛЯ АДМИНИСТРАТОРА:")
    print("="*50)
    print("1. В любой момент можно вызвать export_to_csv() для экспорта в CSV")
    print("2. Все данные сохраняются в SQLite базу: bot_database.db")
    print("3. Для просмотра данных можно использовать SQLite браузер")
    print("4. Или запустить Python с функциями экспорта")
    print("="*50)
    print("\nОжидаю сообщения... (Ctrl+C для остановки)")
    
    # Экспорт в CSV при запуске (опционально)
    export_to_csv()
    
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
            print("\n\nБот остановлен.")
            print("Экспортирую данные в CSV перед выходом...")
            export_to_csv()
            break
        except Exception as e:
            print(f"\nОшибка в основном цикле: {e}")
            time.sleep(5)

from http.server import HTTPServer, BaseHTTPRequestHandler
import sqlite3
import json

class LogViewerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Логи Telegram бота</title>
                <style>
                    body { font-family: Arial; margin: 20px; }
                    table { border-collapse: collapse; width: 100%; }
                    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                    th { background-color: #f2f2f2; }
                    tr:nth-child(even) { background-color: #f9f9f9; }
                </style>
            </head>
            <body>
                <h1>📊 Логи Telegram бота</h1>
                
                <h2>📨 Последние 20 сообщений:</h2>
                <div id="messages"></div>
                
                <h2>👥 Пользователи:</h2>
                <div id="users"></div>
                
                <h2>✅ Завершенные акции:</h2>
                <div id="actions"></div>
                
                <script>
                    function loadData() {
                        fetch('/messages')
                            .then(r => r.text())
                            .then(html => document.getElementById('messages').innerHTML = html);
                        
                        fetch('/users')
                            .then(r => r.text())
                            .then(html => document.getElementById('users').innerHTML = html);
                        
                        fetch('/actions')
                            .then(r => r.text())
                            .then(html => document.getElementById('actions').innerHTML = html);
                    }
                    
                    // Загружаем данные при загрузке страницы и каждые 30 секунд
                    loadData();
                    setInterval(loadData, 30000);
                </script>
            </body>
            </html>
            '''
            self.wfile.write(html.encode('utf-8'))
        
        elif self.path == '/messages':
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM messages ORDER BY timestamp DESC LIMIT 20")
            rows = cursor.fetchall()
            conn.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = '<table><tr><th>Время</th><th>Пользователь</th><th>Тип</th><th>Сообщение</th><th>Ответ</th></tr>'
            for row in rows:
                html += f'''
                <tr>
                    <td>{row[1]}</td>
                    <td>{row[3] or ''} (@{row[2] or 'без username'})</td>
                    <td>{row[7]}</td>
                    <td>{row[8][:50]}{'...' if len(row[8]) > 50 else ''}</td>
                    <td>{row[9][:30]}{'...' if len(row[9]) > 30 else ''}</td>
                </tr>
                '''
            html += '</table>'
            self.wfile.write(html.encode('utf-8'))
        
        elif self.path == '/users':
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users ORDER BY last_seen DESC")
            rows = cursor.fetchall()
            conn.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = '<table><tr><th>ID</th><th>Имя</th><th>Username</th><th>Сообщений</th><th>Первое</th><th>Последнее</th></tr>'
            for row in rows:
                html += f'''
                <tr>
                    <td>{row[0]}</td>
                    <td>{row[2] or ''} {row[3] or ''}</td>
                    <td>@{row[1] or 'нет'}</td>
                    <td>{row[6]}</td>
                    <td>{row[4]}</td>
                    <td>{row[5]}</td>
                </tr>
                '''
            html += '</table>'
            self.wfile.write(html.encode('utf-8'))
        
        elif self.path == '/actions':
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM completed_actions ORDER BY completed_at DESC")
            rows = cursor.fetchall()
            conn.close()
            
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = '<table><tr><th>ID</th><th>User ID</th><th>Конверт</th><th>Телефон</th><th>Время</th></tr>'
            for row in rows:
                html += f'''
                <tr>
                    <td>{row[0]}</td>
                    <td>{row[1]}</td>
                    <td>{row[2]}</td>
                    <td>{row[3]}</td>
                    <td>{row[4]}</td>
                </tr>
                '''
            html += '</table>'
            self.wfile.write(html.encode('utf-8'))

def start_web_viewer():
    """Запуск веб-сервера для просмотра логов"""
    import threading
    def run_server():
        server = HTTPServer(('0.0.0.0', 8080), LogViewerHandler)
        print(f"🌐 Веб-интерфейс доступен по адресу: http://localhost:8080")
        print(f"   На Render будет доступен по вашему URL: https://ваш-проект.onrender.com")
        server.serve_forever()
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

if __name__ == '__main__':
    main()