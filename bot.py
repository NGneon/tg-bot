import urllib.request
import urllib.parse
import json
import time
from datetime import datetime
import os
import sqlite3

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8086950668:AAFPUcf3FINRtaHt9mtGJXfjdf5loOZwlTo')
DB_FILE = "/tmp/bot_data.db"

# ==================== БАЗА ДАННЫХ ====================
def init_db():
    """Просто создаем БД"""
    try:
        print(f"Создаю БД: {DB_FILE}")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT
        )
        ''')
        
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
        print(f"✅ БД создана")
        return True
    except Exception as e:
        print(f"❌ Ошибка БД: {e}")
        return False

def save_action(user_id, envelope, phone):
    """Сохраняем данные"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO actions (user_id, envelope, phone, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, envelope, phone, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        
        conn.commit()
        conn.close()
        
        # ЛОГИРУЕМ В КОНСОЛЬ
        print(f"\n" + "="*50)
        print(f"✅ ДАННЫЕ СОХРАНЕНЫ:")
        print(f"   User ID: {user_id}")
        print(f"   Конверт: {envelope}")
        print(f"   Телефон: {phone}")
        print(f"   Время: {datetime.now().strftime('%H:%M:%S')}")
        print("="*50)
        
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return False

# ==================== TELEGRAM БОТ ====================
def telegram_request(method, data=None):
    """Простой запрос к API"""
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
        print(f"Ошибка API: {e}")
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
        response = telegram_request('getUpdates')
        
        if response and response.get('ok'):
            return response
        return None
    except Exception as e:
        print(f"Ошибка getUpdates: {e}")
        return None

# ==================== ЛОГИКА БОТА ====================
user_sessions = {}

def main():
    """Главная функция"""
    print("="*50)
    print("🤖 БОТ ЗАПУЩЕН")
    print("="*50)
    
    # Проверка токена
    if BOT_TOKEN == 'ВАШ_ТОКЕН_БОТА':
        print("❌ ОШИБКА: Замените 'ВАШ_ТОКЕН_БОТА' на свой токен!")
        return
    
    print(f"Токен: {BOT_TOKEN[:10]}...")
    
    # Создаем БД
    init_db()
    
    print("✅ Бот готов")
    print("Ожидаю сообщения...")
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
                        
                        # ВЫВОДИМ В КОНСОЛЬ
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {user_info.get('first_name')}: {text}")
                        
                        # Команда /start
                        if text == '/start':
                            keyboard = {
                                'inline_keyboard': [
                                    [{'text': 'Начать акцию', 'callback_data': 'start'}],
                                    [{'text': 'Канал', 'url': 'https://t.me/poyezd_chudes'}]
                                ]
                            }
                            send_message(chat_id, "Привет! Добро пожаловать в акцию.", keyboard)
                        
                        # Если есть активная сессия
                        elif chat_id in user_sessions:
                            session = user_sessions[chat_id]
                            
                            if session['step'] == 'waiting_envelope':
                                session['envelope'] = text
                                session['step'] = 'waiting_phone'
                                send_message(chat_id, "Напишите номер телефона:")
                                
                            elif session['step'] == 'waiting_phone':
                                session['phone'] = text
                                session['step'] = 'waiting_confirm'
                                
                                keyboard = {
                                    'keyboard': [[{'text': 'Да'}, {'text': 'Нет'}]],
                                    'resize_keyboard': True
                                }
                                
                                send_message(
                                    chat_id,
                                    f"Проверьте:\nКонверт: {session['envelope']}\nТелефон: {session['phone']}\n\nВсё верно?",
                                    keyboard
                                )
                                
                            elif session['step'] == 'waiting_confirm':
                                if text.lower() == 'да':
                                    # СОХРАНЯЕМ В БАЗУ
                                    save_action(session['user_id'], session['envelope'], session['phone'])
                                    
                                    send_message(
                                        chat_id,
                                        f"✅ Отлично! Конверт {session['envelope']} сохранен.\nСпасибо!"
                                    )
                                    
                                    del user_sessions[chat_id]
                                elif text.lower() == 'нет':
                                    session['step'] = 'waiting_envelope'
                                    send_message(chat_id, "Напишите номер конверта:")
                        
                    # Callback от кнопок
                    elif 'callback_query' in update:
                        callback = update['callback_query']
                        chat_id = callback['message']['chat']['id']
                        data = callback['data']
                        user_info = callback['from']
                        
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {user_info.get('first_name')}: нажал кнопку")
                        
                        if data == 'start':
                            user_sessions[chat_id] = {
                                'user_id': user_info['id'],
                                'step': 'waiting_envelope'
                            }
                            send_message(chat_id, "Напишите номер конверта:")
                        
                        telegram_request('answerCallbackQuery', {'callback_query_id': callback['id']})
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nБот остановлен")
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == '__main__':
    main()