import urllib.request
import urllib.parse
import json
import time
from datetime import datetime
import os
import sqlite3

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8086950668:AAFPUcf3FINRtaHt9mtGJXfjdf5loOZwlTo')  # Замени на свой токен!
DB_FILE = "bot_database.db"  # Файл базы данных

# ==================== БАЗА ДАННЫХ ====================
def setup_database():
    """Создаем и настраиваем базу данных"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Таблица пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            created_at TEXT NOT NULL,
            last_activity TEXT NOT NULL
        )
        ''')
        
        # Таблица сообщений
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            chat_id INTEGER NOT NULL,
            message_type TEXT NOT NULL,
            message_text TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
        )
        ''')
        
        # Таблица завершенных акций (конверт + телефон)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            envelope_number TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            completed_at TEXT NOT NULL,
            FOREIGN KEY (telegram_id) REFERENCES users(telegram_id)
        )
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"✅ База данных создана: {DB_FILE}")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка создания БД: {e}")
        return False

def save_user(user_info):
    """Сохраняем или обновляем пользователя"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        telegram_id = user_info['id']
        username = user_info.get('username', '')
        first_name = user_info.get('first_name', '')
        last_name = user_info.get('last_name', '')
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Проверяем, есть ли пользователь
        cursor.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        if cursor.fetchone():
            # Обновляем
            cursor.execute('''
            UPDATE users SET 
                username = ?, 
                first_name = ?, 
                last_name = ?, 
                last_activity = ?
            WHERE telegram_id = ?
            ''', (username, first_name, last_name, now, telegram_id))
        else:
            # Добавляем нового
            cursor.execute('''
            INSERT INTO users (telegram_id, username, first_name, last_name, created_at, last_activity)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (telegram_id, username, first_name, last_name, now, now))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сохранения пользователя: {e}")
        return False

def save_message(telegram_id, chat_id, message_type, message_text):
    """Сохраняем сообщение"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO messages (telegram_id, chat_id, message_type, message_text, timestamp)
        VALUES (?, ?, ?, ?, ?)
        ''', (telegram_id, chat_id, message_type, message_text, timestamp))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сохранения сообщения: {e}")
        return False

def save_completed_action(telegram_id, envelope_number, phone_number):
    """Сохраняем завершенную акцию"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute('''
        INSERT INTO completed_actions (telegram_id, envelope_number, phone_number, completed_at)
        VALUES (?, ?, ?, ?)
        ''', (telegram_id, envelope_number, phone_number, completed_at))
        
        conn.commit()
        conn.close()
        
        # Показываем в консоли что сохранили
        print(f"\n💾 СОХРАНЕНО В БАЗУ:")
        print(f"   👤 User ID: {telegram_id}")
        print(f"   📦 Конверт: {envelope_number}")
        print(f"   📱 Телефон: {phone_number}")
        print(f"   🕐 Время: {completed_at}")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка сохранения акции: {e}")
        return False

# ==================== TELEGRAM БОТ ====================
def telegram_request(method, data=None):
    """Отправляем запрос к Telegram API"""
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/{method}'
    
    try:
        if data:
            data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        else:
            req = urllib.request.Request(url)
        
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
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
    params = {'timeout': 30}
    if offset:
        params['offset'] = offset
    
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?{urllib.parse.urlencode(params)}'
    response = telegram_request('getUpdates')
    
    if response and response.get('ok'):
        return response
    return None

# ==================== ЛОГИКА БОТА ====================
# Временное хранилище для активных сессий
active_sessions = {}

def handle_start(chat_id, user_info):
    """Обрабатываем /start"""
    # Сохраняем пользователя
    save_user(user_info)
    save_message(user_info['id'], chat_id, 'command', '/start')
    
    # Создаем кнопки
    keyboard = {
        'inline_keyboard': [
            [{'text': 'Добро пожаловать в акцию!', 'callback_data': 'start_aktion'}],
            [{'text': 'Канал организаторов', 'url': 'https://t.me/poyezd_chudes'}]
        ]
    }
    
    text = (
        f"Привет, {user_info.get('first_name', 'друг')}!\n\n"
        "Добро пожаловать в акцию \"Поезд Чудес\" 🚂\n"
        "Здесь вы можете выбрать желание ребёнка и подарить праздник."
    )
    
    send_message(chat_id, text, keyboard)

def handle_callback_command(chat_id, user_info):
    """Обрабатываем /callback"""
    save_message(user_info['id'], chat_id, 'command', '/callback')
    send_message(chat_id, "Обратная связь: @poyezd_chudes")

def handle_welcome_button(chat_id, user_info):
    """Обрабатываем нажатие кнопки приветствия"""
    save_message(user_info['id'], chat_id, 'button', 'start_aktion')
    
    # Начинаем диалог
    active_sessions[chat_id] = {
        'user_id': user_info['id'],
        'step': 'waiting_envelope'
    }
    
    send_message(chat_id, "Напишите номер конверта:")

def process_dialog(chat_id, text, user_info):
    """Обрабатываем диалог"""
    if chat_id not in active_sessions:
        return False
    
    session = active_sessions[chat_id]
    
    if session['step'] == 'waiting_envelope':
        # Сохраняем конверт
        session['envelope'] = text
        session['step'] = 'waiting_phone'
        send_message(chat_id, "Напишите ваш номер телефона:")
        save_message(user_info['id'], chat_id, 'message', f"Конверт: {text}")
        
    elif session['step'] == 'waiting_phone':
        # Сохраняем телефон
        session['phone'] = text
        session['step'] = 'waiting_confirm'
        save_message(user_info['id'], chat_id, 'message', f"Телефон: {text}")
        
        # Кнопки для подтверждения
        keyboard = {
            'keyboard': [[{'text': '✅ Да'}, {'text': '❌ Нет'}]],
            'resize_keyboard': True,
            'one_time_keyboard': True
        }
        
        send_message(
            chat_id,
            f"Проверьте данные:\nКонверт: {session['envelope']}\nТелефон: {session['phone']}\n\nВсё верно?",
            keyboard
        )
        
    elif session['step'] == 'waiting_confirm':
        if text.lower() in ['да', '✅ да']:
            # Сохраняем завершенную акцию
            save_completed_action(
                session['user_id'],
                session['envelope'],
                session['phone']
            )
            
            # Отправляем финальное сообщение
            send_message(
                chat_id,
                f"✅ Отлично! Конверт {session['envelope']} зафиксирован.\n"
                f"Спасибо за участие! Обратная связь: @poyezd_chudes"
            )
            
            # Удаляем сессию
            del active_sessions[chat_id]
            
        elif text.lower() in ['нет', '❌ нет']:
            # Начинаем заново
            session['step'] = 'waiting_envelope'
            send_message(chat_id, "Хорошо, начнем заново. Напишите номер конверта:")
        else:
            send_message(chat_id, "Пожалуйста, выберите Да или Нет")
    
    return True

# ==================== ГЛАВНЫЙ ЦИКЛ ====================
def main():
    """Запуск бота"""
    print("="*50)
    print("🤖 БОТ 'ПОЕЗД ЧУДЕС'")
    print("="*50)
    
    # Проверка токена
    if BOT_TOKEN == 'ВАШ_ТОКЕН_БОТА':
        print("❌ ЗАМЕНИТЕ 'ВАШ_ТОКЕН_БОТА' НА РЕАЛЬНЫЙ ТОКЕН!")
        print("   Получите у @BotFather в Telegram")
        return
    
    # Создаем базу данных
    if not setup_database():
        print("❌ Не удалось создать базу данных")
        return
    
    print("✅ База данных готова")
    print("✅ Бот запущен")
    print("👂 Ожидаю сообщения...")
    print("-"*50)
    
    offset = None
    
    try:
        while True:
            # Получаем обновления
            updates = get_updates(offset)
            
            if updates and updates.get('result'):
                for update in updates['result']:
                    offset = update['update_id'] + 1
                    
                    # Текстовое сообщение
                    if 'message' in update:
                        msg = update['message']
                        chat_id = msg['chat']['id']
                        text = msg.get('text', '').strip()
                        user_info = msg['from']
                        
                        # Сохраняем пользователя
                        save_user(user_info)
                        
                        # Логируем в консоль
                        username = user_info.get('username', 'без username')
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {user_info.get('first_name')}: {text}")
                        
                        # Обрабатываем команды
                        if text == '/start':
                            handle_start(chat_id, user_info)
                        elif text == '/callback':
                            handle_callback_command(chat_id, user_info)
                        else:
                            # Пробуем обработать как часть диалога
                            if not process_dialog(chat_id, text, user_info):
                                # Если не диалог, сохраняем как обычное сообщение
                                save_message(user_info['id'], chat_id, 'message', text)
                    
                    # Callback от кнопок
                    elif 'callback_query' in update:
                        callback = update['callback_query']
                        chat_id = callback['message']['chat']['id']
                        data = callback['data']
                        user_info = callback['from']
                        
                        # Сохраняем пользователя
                        save_user(user_info)
                        
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {user_info.get('first_name')}: [КНОПКА] {data}")
                        
                        if data == 'start_aktion':
                            handle_welcome_button(chat_id, user_info)
                        
                        # Отвечаем на callback (убираем часики)
                        telegram_request('answerCallbackQuery', {'callback_query_id': callback['id']})
            
            # Пауза
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Бот остановлен")
        print(f"💾 Все данные сохранены в: {DB_FILE}")
        print("="*50)

if __name__ == '__main__':
    main()