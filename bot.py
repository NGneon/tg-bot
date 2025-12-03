import urllib.request
import urllib.parse
import json
import time
from datetime import datetime
import os
import sqlite3

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8086950668:AAFPUcf3FINRtaHt9mtGJXfjdf5loOZwlTo')  # ЗАМЕНИ НА СВОЙ!
DB_FILE = "/tmp/bot_data.db"  # Используем /tmp папку на Render

# ==================== БАЗА ДАННЫХ ====================
def init_db():
    """Создаем БД если нет"""
    try:
        print(f"🔄 Создаю базу данных: {DB_FILE}")
        print(f"📁 Текущая папка: {os.getcwd()}")
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            first_seen TEXT,
            last_seen TEXT
        )
        ''')
        
        # Таблица сообщений
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            chat_id INTEGER,
            message_type TEXT,
            message_text TEXT,
            timestamp TEXT
        )
        ''')
        
        # Таблица завершенных акций
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            envelope TEXT,
            phone TEXT,
            timestamp TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ База данных создана: {DB_FILE}")
        
        # Проверим что файл создался
        if os.path.exists(DB_FILE):
            print(f"📂 Файл БД существует, размер: {os.path.getsize(DB_FILE)} байт")
        else:
            print("❌ Файл БД не создан!")
            
        return True
    except Exception as e:
        print(f"❌ Ошибка создания БД: {e}")
        return False

def save_user(user_info):
    """Сохраняем пользователя"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user_id = user_info['id']
        
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            cursor.execute(
                "UPDATE users SET username = ?, first_name = ?, last_name = ?, last_seen = ? WHERE user_id = ?",
                (user_info.get('username'), user_info.get('first_name'), user_info.get('last_name'), now, user_id)
            )
        else:
            cursor.execute(
                "INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, user_info.get('username'), user_info.get('first_name'), user_info.get('last_name'), now, now)
            )
        
        conn.commit()
        conn.close()
        
        # Логируем в консоль
        username = user_info.get('username', 'нет')
        print(f"👤 Сохранен пользователь: {user_info.get('first_name')} (@{username}) ID: {user_id}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения пользователя: {e}")
        return False

def save_message(user_id, chat_id, msg_type, text):
    """Сохраняем сообщение"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO messages (user_id, chat_id, message_type, message_text, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, chat_id, msg_type, text, timestamp)
        )
        
        conn.commit()
        conn.close()
        
        # Логируем в консоль
        print(f"💬 Сообщение сохранено: {msg_type} - {text[:50]}")
        
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения сообщения: {e}")
        return False

def save_action(user_id, envelope, phone):
    """Сохраняем завершенную акцию"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute(
            "INSERT INTO actions (user_id, envelope, phone, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, envelope, phone, timestamp)
        )
        
        conn.commit()
        conn.close()
        
        # Логируем в консоль
        print(f"\n" + "="*50)
        print(f"✅ АКЦИЯ СОХРАНЕНА В БАЗУ!")
        print(f"   👤 User ID: {user_id}")
        print(f"   📦 Конверт: {envelope}")
        print(f"   📱 Телефон: {phone}")
        print(f"   🕐 Время: {timestamp}")
        print("="*50)
        
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения акции: {e}")
        return False

def show_db_stats():
    """Показываем статистику БД"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM messages")
        messages = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM actions")
        actions = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n📊 СТАТИСТИКА БАЗЫ ДАННЫХ:")
        print(f"   👥 Пользователей: {users}")
        print(f"   💬 Сообщений: {messages}")
        print(f"   ✅ Завершенных акций: {actions}")
        
        # Показываем последние акции
        if actions > 0:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM actions ORDER BY timestamp DESC LIMIT 3")
            recent = cursor.fetchall()
            conn.close()
            
            print(f"\n📋 Последние акции:")
            for action in recent:
                print(f"   Конверт: {action[2]}, Телефон: {action[3]}")
        
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")

# ==================== TELEGRAM API ====================
def telegram_request(method, data=None):
    """Отправляем запрос к Telegram API"""
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/{method}'
    
    try:
        if data:
            data_bytes = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=data_bytes, headers={'Content-Type': 'application/json'})
        else:
            req = urllib.request.Request(url)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Ошибка запроса {method}: {e}")
        return None

def send_message(chat_id, text, buttons=None):
    """Отправляем сообщение"""
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    if buttons:
        payload['reply_markup'] = buttons
    
    return telegram_request('sendMessage', payload)

def get_updates(offset=None):
    """Получаем обновления"""
    try:
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates'
        params = {'timeout': 30}
        if offset:
            params['offset'] = offset
        
        url_with_params = f"{url}?{urllib.parse.urlencode(params)}"
        req = urllib.request.Request(url_with_params)
        
        with urllib.request.urlopen(req, timeout=35) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Ошибка getUpdates: {e}")
        return None

# ==================== ЛОГИКА БОТА ====================
# Храним активные сессии
active_sessions = {}

def handle_start(chat_id, user_info):
    """Обработка /start"""
    # Сохраняем в БД
    save_user(user_info)
    save_message(user_info['id'], chat_id, 'command', '/start')
    
    # Создаем кнопки
    keyboard = {
        'inline_keyboard': [
            [{'text': 'Добро пожаловать в акцию!', 'callback_data': 'start_action'}],
            [{'text': 'Канал организаторов', 'url': 'https://t.me/poyezd_chudes'}]
        ]
    }
    
    text = f"Привет, {user_info.get('first_name', 'друг')}!\n\nДобро пожаловать в акцию \"Поезд Чудес\" 🚂🎄🎁"
    
    return send_message(chat_id, text, keyboard)

def handle_callback_command(chat_id, user_info):
    """Обработка /callback"""
    save_message(user_info['id'], chat_id, 'command', '/callback')
    return send_message(chat_id, "Обратная связь: @poyezd_chudes")

def handle_welcome_button(chat_id, user_info):
    """Обработка кнопки приветствия"""
    save_message(user_info['id'], chat_id, 'button', 'start_action')
    
    # Начинаем диалог
    active_sessions[chat_id] = {
        'user_id': user_info['id'],
        'step': 'waiting_envelope'
    }
    
    return send_message(chat_id, "Напишите номер конверта:")

def process_user_message(chat_id, text, user_info):
    """Обработка сообщений от пользователя"""
    # Сохраняем сообщение в БД
    save_message(user_info['id'], chat_id, 'message', text)
    
    # Если есть активная сессия
    if chat_id in active_sessions:
        session = active_sessions[chat_id]
        
        if session['step'] == 'waiting_envelope':
            # Сохраняем номер конверта
            session['envelope'] = text
            session['step'] = 'waiting_phone'
            return send_message(chat_id, "Напишите номер телефона:")
        
        elif session['step'] == 'waiting_phone':
            # Сохраняем номер телефона
            session['phone'] = text
            session['step'] = 'waiting_confirm'
            
            # Кнопки для подтверждения
            keyboard = {
                'keyboard': [[{'text': '✅ Да'}, {'text': '❌ Нет'}]],
                'resize_keyboard': True,
                'one_time_keyboard': True
            }
            
            return send_message(
                chat_id,
                f"Проверьте данные:\n\n📦 Конверт: {session['envelope']}\n📱 Телефон: {session['phone']}\n\nВсё верно?",
                keyboard
            )
        
        elif session['step'] == 'waiting_confirm':
            if text.lower() in ['да', '✅ да']:
                # СОХРАНЯЕМ В БАЗУ ДАННЫХ
                save_action(session['user_id'], session['envelope'], session['phone'])
                
                # Отправляем финальное сообщение
                send_message(
                    chat_id,
                    f"✅ Отлично! Конверт {session['envelope']} зафиксирован.\nСпасибо за участие! Обратная связь: @poyezd_chudes"
                )
                
                # Удаляем сессию
                del active_sessions[chat_id]
                return None
                
            elif text.lower() in ['нет', '❌ нет']:
                # Начинаем заново
                session['step'] = 'waiting_envelope'
                return send_message(chat_id, "Напишите номер конверта:")
            else:
                return send_message(chat_id, "Ответьте Да или Нет")
    
    return None

# ==================== ГЛАВНЫЙ ЦИКЛ ====================
def main():
    """Запуск бота"""
    print("="*50)
    print("🤖 БОТ 'ПОЕЗД ЧУДЕС'")
    print("="*50)
    print(f"🕐 Запущено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Рабочая папка: {os.getcwd()}")
    
    # Проверка токена
    if BOT_TOKEN == 'ВАШ_ТОКЕН_БОТА':
        print("❌ ОШИБКА: Замените 'ВАШ_ТОКЕН_БОТА' на свой токен!")
        print("   Получите у @BotFather в Telegram")
        return
    
    print(f"✅ Токен: {BOT_TOKEN[:10]}...")
    
    # Инициализируем БД
    print("\n🗄️ Инициализация базы данных...")
    if not init_db():
        print("⚠️ Будет работать без сохранения в БД")
    else:
        print("✅ База данных готова")
    
    print("\n👂 Бот запущен и ожидает сообщения...")
    print("-"*50)
    
    last_update_id = 0
    
    try:
        while True:
            # Получаем обновления
            updates = get_updates(last_update_id + 1 if last_update_id > 0 else None)
            
            if updates and updates.get('ok'):
                for update in updates['result']:
                    current_id = update['update_id']
                    
                    # Обновляем ID
                    if current_id > last_update_id:
                        last_update_id = current_id
                    
                    # Обрабатываем текстовое сообщение
                    if 'message' in update:
                        msg = update['message']
                        chat_id = msg['chat']['id']
                        text = msg.get('text', '').strip()
                        user_info = msg['from']
                        
                        # ЛОГИРУЕМ В КОНСОЛЬ
                        username = user_info.get('username', 'нет username')
                        first_name = user_info.get('first_name', '')
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 👤 {first_name} (@{username}): {text}")
                        
                        # Обрабатываем команды
                        if text == '/start':
                            handle_start(chat_id, user_info)
                        elif text == '/callback':
                            handle_callback_command(chat_id, user_info)
                        else:
                            # Пробуем обработать как часть диалога
                            response = process_user_message(chat_id, text, user_info)
                            if not response:
                                # Если не диалог и не команда, сохраняем как обычное сообщение
                                save_message(user_info['id'], chat_id, 'message', text)
                    
                    # Обрабатываем callback от кнопок
                    elif 'callback_query' in update:
                        callback = update['callback_query']
                        chat_id = callback['message']['chat']['id']
                        data = callback['data']
                        user_info = callback['from']
                        
                        # ЛОГИРУЕМ В КОНСОЛЬ
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔘 {user_info.get('first_name')}: нажал кнопку")
                        
                        if data == 'start_action':
                            handle_welcome_button(chat_id, user_info)
                        
                        # Отвечаем на callback
                        telegram_request('answerCallbackQuery', {'callback_query_id': callback['id']})
            
            # Небольшая пауза
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Бот остановлен")
        print("📊 Финальная статистика:")
        show_db_stats()
    except Exception as e:
        print(f"\n❌ Ошибка в основном цикле: {e}")
        import traceback
        traceback.print_exc()
        time.sleep(5)

if __name__ == '__main__':
    main()