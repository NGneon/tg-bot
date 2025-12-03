import urllib.request
import urllib.parse
import json
import time
from datetime import datetime
import os
import sqlite3

BOT_TOKEN = os.environ.get('BOT_TOKEN', '8086950668:AAFPUcf3FINRtaHt9mtGJXfjdf5loOZwlTo')
DB_FILE = "bot_data.db"

def init_db():
    """Создаем БД если нет"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
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
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        chat_id INTEGER,
        message_type TEXT,
        message_text TEXT,
        timestamp TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        envelope TEXT,
        phone TEXT,
        timestamp TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✅ База данных: {DB_FILE}")

def save_user(user_info):
    """Сохраняем пользователя"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user_id = user_info['id']
        
        # Проверяем есть ли пользователь
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            # Обновляем
            cursor.execute(
                "UPDATE users SET username = ?, first_name = ?, last_name = ?, last_seen = ? WHERE user_id = ?",
                (user_info.get('username'), user_info.get('first_name'), user_info.get('last_name'), now, user_id)
            )
        else:
            # Добавляем нового
            cursor.execute(
                "INSERT INTO users (user_id, username, first_name, last_name, first_seen, last_seen) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, user_info.get('username'), user_info.get('first_name'), user_info.get('last_name'), now, now)
            )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения пользователя: {e}")
        return False

def save_message(user_id, chat_id, msg_type, text):
    """Сохраняем сообщение"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO messages (user_id, chat_id, message_type, message_text, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, chat_id, msg_type, text, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения сообщения: {e}")
        return False

def save_action(user_id, envelope, phone):
    """Сохраняем завершенную акцию"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO actions (user_id, envelope, phone, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, envelope, phone, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        
        conn.commit()
        conn.close()
        
        # Логируем
        print(f"\n" + "="*50)
        print(f"✅ СОХРАНЕНО В БАЗУ:")
        print(f"   👤 User ID: {user_id}")
        print(f"   📦 Конверт: {envelope}")
        print(f"   📱 Телефон: {phone}")
        print("="*50)
        
        # Показываем статистику
        show_stats()
        
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения акции: {e}")
        return False

def show_stats():
    """Показываем статистику"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM actions")
        actions = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"📊 Статистика: {users} пользователей, {actions} завершенных акций")
    except:
        pass

# ==================== TELEGRAM API ====================
def make_request(method, data=None):
    """Делаем запрос к Telegram API"""
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
    
    return make_request('sendMessage', payload)

def get_updates(offset=None):
    """Получаем обновления"""
    params = {'timeout': 30, 'limit': 100}
    if offset:
        params['offset'] = offset
    
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?{urllib.parse.urlencode(params)}'
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=35) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Ошибка getUpdates: {e}")
        return None

# ==================== ЛОГИКА БОТА ====================
# Храним активные диалоги
user_sessions = {}

def process_start(chat_id, user_info):
    """Обработка /start"""
    save_user(user_info)
    save_message(user_info['id'], chat_id, 'command', '/start')
    
    keyboard = {
        'inline_keyboard': [
            [{'text': 'Добро пожаловать в акцию!', 'callback_data': 'start_action'}],
            [{'text': 'Канал организаторов', 'url': 'https://t.me/poyezd_chudes'}]
        ]
    }
    
    text = f"Привет, {user_info.get('first_name', 'друг')}!\n\nДобро пожаловать в акцию \"Поезд Чудес\" 🚂🎄🎁"
    
    return send_message(chat_id, text, keyboard)

def process_callback_command(chat_id, user_info):
    """Обработка /callback"""
    save_message(user_info['id'], chat_id, 'command', '/callback')
    return send_message(chat_id, "Обратная связь: @poyezd_chudes")

def process_welcome_button(chat_id, user_info):
    """Обработка кнопки приветствия"""
    save_message(user_info['id'], chat_id, 'button', 'start_action')
    
    # Начинаем диалог
    user_sessions[chat_id] = {
        'user_id': user_info['id'],
        'step': 'waiting_envelope'
    }
    
    return send_message(chat_id, "Напишите номер конверта:")

def process_text_message(chat_id, text, user_info):
    """Обработка текстовых сообщений"""
    save_message(user_info['id'], chat_id, 'message', text)
    
    # Если есть активная сессия
    if chat_id in user_sessions:
        session = user_sessions[chat_id]
        
        if session['step'] == 'waiting_envelope':
            # Сохраняем конверт
            session['envelope'] = text
            session['step'] = 'waiting_phone'
            return send_message(chat_id, "Напишите номер телефона:")
        
        elif session['step'] == 'waiting_phone':
            # Сохраняем телефон
            session['phone'] = text
            session['step'] = 'waiting_confirm'
            
            keyboard = {
                'keyboard': [[{'text': '✅ Да'}, {'text': '❌ Нет'}]],
                'resize_keyboard': True,
                'one_time_keyboard': True
            }
            
            return send_message(
                chat_id,
                f"Проверьте:\nКонверт: {session['envelope']}\nТелефон: {session['phone']}\n\nВсё верно?",
                keyboard
            )
        
        elif session['step'] == 'waiting_confirm':
            if text.lower() in ['да', '✅ да']:
                # Сохраняем в БД
                save_action(session['user_id'], session['envelope'], session['phone'])
                
                # Отправляем финальное сообщение
                send_message(
                    chat_id,
                    f"✅ Отлично! Конверт {session['envelope']} зафиксирован.\nСпасибо! Обратная связь: @poyezd_chudes"
                )
                
                # Удаляем сессию
                del user_sessions[chat_id]
                
            elif text.lower() in ['нет', '❌ нет']:
                # Начинаем заново
                session['step'] = 'waiting_envelope'
                return send_message(chat_id, "Напишите номер конверта:")
            else:
                return send_message(chat_id, "Ответьте Да или Нет")
    
    return None

# ==================== ГЛАВНЫЙ ЦИКЛ ====================
def main():
    """Основная функция"""
    print("="*50)
    print("🤖 БОТ ЗАПУЩЕН")
    print("="*50)
    
    # Проверка токена
    if BOT_TOKEN == 'ВАШ_ТОКЕН_БОТА':
        print("❌ ЗАМЕНИТЕ 'ВАШ_ТОКЕН_БОТА' НА СВОЙ ТОКЕН!")
        return
    
    # Инициализируем БД
    init_db()
    
    print("✅ База данных готова")
    print("👂 Ожидаю сообщения...")
    print("-"*50)
    
    last_update_id = 0
    
    try:
        while True:
            # Получаем обновления
            updates = get_updates(last_update_id + 1 if last_update_id > 0 else None)
            
            if updates and updates.get('ok') and updates.get('result'):
                for update in updates['result']:
                    current_update_id = update['update_id']
                    
                    # Обновляем last_update_id
                    if current_update_id > last_update_id:
                        last_update_id = current_update_id
                    
                    # Обрабатываем сообщение
                    if 'message' in update:
                        msg = update['message']
                        chat_id = msg['chat']['id']
                        text = msg.get('text', '').strip()
                        user_info = msg['from']
                        
                        # Сохраняем пользователя
                        save_user(user_info)
                        
                        # Логируем
                        username = user_info.get('username', 'нет')
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {user_info.get('first_name')} (@{username}): {text}")
                        
                        # Обрабатываем
                        if text == '/start':
                            process_start(chat_id, user_info)
                        elif text == '/callback':
                            process_callback_command(chat_id, user_info)
                        else:
                            process_text_message(chat_id, text, user_info)
                    
                    # Обрабатываем callback от кнопок
                    elif 'callback_query' in update:
                        callback = update['callback_query']
                        chat_id = callback['message']['chat']['id']
                        data = callback['data']
                        user_info = callback['from']
                        
                        save_user(user_info)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {user_info.get('first_name')}: [КНОПКА] {data}")
                        
                        if data == 'start_action':
                            process_welcome_button(chat_id, user_info)
                        
                        # Отвечаем на callback
                        make_request('answerCallbackQuery', {'callback_query_id': callback['id']})
            
            # Пауза между проверками
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Бот остановлен")
        print(f"💾 Данные сохранены в: {DB_FILE}")
        show_stats()
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        time.sleep(5)
        main()  # Перезапуск при ошибке

if __name__ == '__main__':
    main()