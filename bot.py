import os
import json
import time
from datetime import datetime
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import urllib.request
import urllib.parse
import urllib.error

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8086950668:AAFPUcf3FINRtaHt9mtGJXfjdf5loOZwlTo')
PORT = int(os.environ.get('PORT', 10000))
DB_FILE = "/tmp/bot_data.db"

# ==================== БАЗА ДАННЫХ ====================
def init_db():
    """Создаем базу данных"""
    try:
        print(f"📁 Создаю базу данных: {DB_FILE}")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            first_name TEXT,
            last_seen TEXT,
            created_at TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            envelope TEXT NOT NULL,
            phone TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ База данных создана")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания БД: {e}")
        return False

def save_user(user_info):
    """Сохраняем/обновляем пользователя"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user_id = user_info['id']
        
        # Проверяем есть ли пользователь
        cursor.execute("SELECT id FROM users WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            # Обновляем
            cursor.execute(
                "UPDATE users SET username = ?, first_name = ?, last_seen = ? WHERE user_id = ?",
                (user_info.get('username'), user_info.get('first_name'), now, user_id)
            )
        else:
            # Добавляем нового
            cursor.execute(
                "INSERT INTO users (user_id, username, first_name, last_seen, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, user_info.get('username'), user_info.get('first_name'), now, now)
            )
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения пользователя: {e}")
        return False

def save_action(user_id, envelope, phone):
    """Сохраняем действие пользователя"""
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
        
        # ЛОГИРУЕМ В КОНСОЛЬ
        print(f"\n" + "="*60)
        print(f"✅ ДАННЫЕ СОХРАНЕНЫ В БАЗУ!")
        print(f"   👤 User ID: {user_id}")
        print(f"   📦 Конверт: {envelope}")
        print(f"   📱 Телефон: {phone}")
        print(f"   🕐 Время: {timestamp}")
        print("="*60)
        
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения действия: {e}")
        return False

def get_db_stats():
    """Получаем статистику из БД"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        users_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM actions")
        actions_count = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT u.first_name, u.username, a.envelope, a.phone, a.timestamp 
            FROM actions a 
            LEFT JOIN users u ON a.user_id = u.user_id 
            ORDER BY a.timestamp DESC 
            LIMIT 10
        """)
        recent_actions = cursor.fetchall()
        
        conn.close()
        
        return {
            'users_count': users_count,
            'actions_count': actions_count,
            'recent_actions': recent_actions
        }
    except Exception as e:
        print(f"❌ Ошибка получения статистики: {e}")
        return {'users_count': 0, 'actions_count': 0, 'recent_actions': []}

# ==================== ВЕБ-СЕРВЕР ДЛЯ ПРОСМОТРА ДАННЫХ ====================
class BotWebHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Обработка GET запросов"""
        if self.path == '/':
            # Главная страница
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            stats = get_db_stats()
            
            html = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>🤖 Telegram Bot Monitor</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
                    .container {{ max-width: 1200px; margin: 0 auto; }}
                    .header {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                    .stats {{ display: flex; gap: 20px; margin-bottom: 20px; }}
                    .stat-card {{ background: white; padding: 20px; border-radius: 10px; flex: 1; text-align: center; }}
                    .stat-number {{ font-size: 2em; font-weight: bold; color: #2c3e50; }}
                    .stat-label {{ color: #7f8c8d; }}
                    table {{ width: 100%; background: white; border-collapse: collapse; border-radius: 10px; overflow: hidden; }}
                    th {{ background: #3498db; color: white; padding: 15px; text-align: left; }}
                    td {{ padding: 12px 15px; border-bottom: 1px solid #eee; }}
                    tr:hover {{ background: #f9f9f9; }}
                    .time {{ color: #7f8c8d; font-size: 0.9em; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🤖 Telegram Bot Monitor</h1>
                        <p>Бот "Поезд Чудес" - система мониторинга</p>
                        <p class="time">Обновлено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    
                    <div class="stats">
                        <div class="stat-card">
                            <div class="stat-number">{stats['users_count']}</div>
                            <div class="stat-label">👥 Пользователей</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{stats['actions_count']}</div>
                            <div class="stat-label">✅ Завершенных акций</div>
                        </div>
                    </div>
                    
                    <h2>📋 Последние акции</h2>
                    <table>
                        <tr>
                            <th>Имя</th>
                            <th>Username</th>
                            <th>Конверт</th>
                            <th>Телефон</th>
                            <th>Время</th>
                        </tr>
            '''
            
            if stats['recent_actions']:
                for action in stats['recent_actions']:
                    username = f"@{action[1]}" if action[1] else "нет"
                    html += f'''
                    <tr>
                        <td>{action[0] or 'Нет имени'}</td>
                        <td>{username}</td>
                        <td><strong>{action[2]}</strong></td>
                        <td>{action[3]}</td>
                        <td class="time">{action[4]}</td>
                    </tr>
                    '''
            else:
                html += '''
                    <tr>
                        <td colspan="5" style="text-align: center; padding: 40px; color: #7f8c8d;">
                            Нет данных. Бот ожидает сообщений...
                        </td>
                    </tr>
                '''
            
            html += '''
                    </table>
                    
                    <div style="margin-top: 30px; padding: 20px; background: white; border-radius: 10px;">
                        <h3>ℹ️ Информация</h3>
                        <p>• Все данные сохраняются в базу данных SQLite</p>
                        <p>• Страница обновляется при каждом обновлении</p>
                        <p>• Для теста отправьте боту /start в Telegram</p>
                    </div>
                </div>
                
                <script>
                    // Автообновление каждые 10 секунд
                    setTimeout(function() {{
                        location.reload();
                    }}, 10000);
                </script>
            </body>
            </html>
            '''
            
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/api/stats':
            # JSON API для статистики
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            stats = get_db_stats()
            response = {
                'status': 'ok',
                'timestamp': datetime.now().isoformat(),
                'data': stats
            }
            self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            
        elif self.path == '/api/raw':
            # Сырые данные из БД
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM actions ORDER BY timestamp DESC LIMIT 100")
                actions = cursor.fetchall()
                
                cursor.execute("SELECT * FROM users ORDER BY last_seen DESC LIMIT 100")
                users = cursor.fetchall()
                
                conn.close()
                
                response = {
                    'actions': actions,
                    'users': users
                }
                self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                
        else:
            self.send_error(404)

def start_web_server():
    """Запускаем веб-сервер для мониторинга"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), BotWebHandler)
        print(f"🌐 Веб-сервер запущен на порту {PORT}")
        print(f"   📊 Мониторинг: http://ваш-домен.onrender.com/")
        print(f"   📈 API статистики: http://ваш-домен.onrender.com/api/stats")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Ошибка веб-сервера: {e}")

# ==================== TELEGRAM БОТ ====================
def telegram_api(method, data=None):
    """Вызов API Telegram"""
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
        print(f"❌ Ошибка Telegram API: {e}")
        return None

def send_telegram_message(chat_id, text, buttons=None):
    """Отправка сообщения в Telegram"""
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    if buttons:
        payload['reply_markup'] = buttons
    
    return telegram_api('sendMessage', payload)

def get_telegram_updates(offset=None):
    """Получение обновлений от Telegram"""
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
        print(f"❌ Ошибка получения обновлений: {e}")
        return None

# Логика бота
user_sessions = {}

def process_start_command(chat_id, user_info):
    """Обработка команды /start"""
    save_user(user_info)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 👤 {user_info.get('first_name')}: /start")
    
    keyboard = {
        'inline_keyboard': [
            [{'text': 'Добро пожаловать в акцию!', 'callback_data': 'start_action'}],
            [{'text': 'Перейти в канал организаторов', 'url': 'https://t.me/poyezd_chudes'}]
        ]
    }
    
    message = (
        f"Привет, {user_info.get('first_name', 'друг')}!\n\n"
        "Добро пожаловать в акцию \"Поезд Чудес\" 🚂🎄🎁\n"
        "Здесь вы можете выбрать желание ребёнка и подарить праздник."
    )
    
    send_telegram_message(chat_id, message, keyboard)

def process_callback_command(chat_id, user_info):
    """Обработка команды /callback"""
    save_user(user_info)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 👤 {user_info.get('first_name')}: /callback")
    send_telegram_message(chat_id, "Обратная связь: @poyezd_chudes")

def handle_welcome_button(chat_id, user_info):
    """Обработка нажатия кнопки"""
    save_user(user_info)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔘 {user_info.get('first_name')}: начал акцию")
    
    user_sessions[chat_id] = {
        'user_id': user_info['id'],
        'step': 'waiting_envelope'
    }
    
    send_telegram_message(chat_id, "Напишите номер конверта:")

def process_user_message(chat_id, text, user_info):
    """Обработка сообщения пользователя"""
    save_user(user_info)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 💬 {user_info.get('first_name')}: {text}")
    
    # Если есть активная сессия
    if chat_id in user_sessions:
        session = user_sessions[chat_id]
        
        if session['step'] == 'waiting_envelope':
            session['envelope'] = text
            session['step'] = 'waiting_phone'
            send_telegram_message(chat_id, "Напишите номер телефона:")
            
        elif session['step'] == 'waiting_phone':
            session['phone'] = text
            session['step'] = 'waiting_confirm'
            
            keyboard = {
                'keyboard': [[{'text': '✅ Да'}, {'text': '❌ Нет'}]],
                'resize_keyboard': True,
                'one_time_keyboard': True
            }
            
            send_telegram_message(
                chat_id,
                f"Проверьте данные:\n\n📦 Конверт: {session['envelope']}\n📱 Телефон: {session['phone']}\n\nВсё верно?",
                keyboard
            )
            
        elif session['step'] == 'waiting_confirm':
            if text.lower() in ['да', '✅ да']:
                # СОХРАНЯЕМ В БАЗУ
                save_action(session['user_id'], session['envelope'], session['phone'])
                
                send_telegram_message(
                    chat_id,
                    f"✅ Отлично! Конверт {session['envelope']} зафиксирован.\nСпасибо за участие!"
                )
                
                del user_sessions[chat_id]
                
            elif text.lower() in ['нет', '❌ нет']:
                session['step'] = 'waiting_envelope'
                send_telegram_message(chat_id, "Напишите номер конверта:")

def telegram_bot():
    """Основной цикл Telegram бота"""
    print("🤖 Запускаю Telegram бота...")
    
    if BOT_TOKEN == 'ВАШ_ТОКЕН_БОТА':
        print("❌ Токен не установлен! Бот не будет работать")
        print("   Установите BOT_TOKEN в настройках Render")
        return
    
    # Проверяем подключение
    response = telegram_api('getMe')
    if response and response.get('ok'):
        bot_info = response['result']
        print(f"✅ Бот подключен: {bot_info.get('first_name')} (@{bot_info.get('username')})")
    else:
        print("❌ Не удалось подключиться к Telegram")
        return
    
    print("👂 Ожидаю сообщения от пользователей...")
    print("-"*60)
    
    last_update_id = 0
    
    try:
        while True:
            updates = get_telegram_updates(last_update_id + 1 if last_update_id > 0 else None)
            
            if updates and updates.get('ok') and updates.get('result'):
                for update in updates['result']:
                    current_id = update['update_id']
                    
                    if current_id > last_update_id:
                        last_update_id = current_id
                    
                    # Текстовое сообщение
                    if 'message' in update:
                        msg = update['message']
                        chat_id = msg['chat']['id']
                        text = msg.get('text', '').strip()
                        user_info = msg['from']
                        
                        if text == '/start':
                            process_start_command(chat_id, user_info)
                        elif text == '/callback':
                            process_callback_command(chat_id, user_info)
                        else:
                            process_user_message(chat_id, text, user_info)
                    
                    # Callback от кнопок
                    elif 'callback_query' in update:
                        callback = update['callback_query']
                        chat_id = callback['message']['chat']['id']
                        data = callback['data']
                        user_info = callback['from']
                        
                        if data == 'start_action':
                            handle_welcome_button(chat_id, user_info)
                        
                        telegram_api('answerCallbackQuery', {'callback_query_id': callback['id']})
            
            time.sleep(1)
            
    except Exception as e:
        print(f"❌ Ошибка в Telegram боте: {e}")
        import traceback
        traceback.print_exc()

# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================
def main():
    """Запуск всей системы"""
    print("="*60)
    print("🚀 TELEGRAM BOT SYSTEM")
    print("="*60)
    print(f"🕐 Запущено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 База данных: {DB_FILE}")
    
    # Инициализируем БД
    print("\n🗄️ Инициализация базы данных...")
    init_db()
    
    # Запускаем веб-сервер в отдельном потоке
    print("\n🌐 Запуск веб-мониторинга...")
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    
    # Запускаем Telegram бота в отдельном потоке
    print("\n🤖 Запуск Telegram бота...")
    bot_thread = threading.Thread(target=telegram_bot, daemon=True)
    bot_thread.start()
    
    print("\n" + "="*60)
    print("✅ СИСТЕМА ЗАПУЩЕНА!")
    print("="*60)
    print("📊 МОНИТОРИНГ:")
    print("   • Веб-интерфейс: http://ваш-домен.onrender.com/")
    print("   • Автообновление: каждые 10 секунд")
    print("   • Все данные сохраняются в базу")
    print("\n🤖 TELEGRAM БОТ:")
    print("   • Команды: /start, /callback")
    print("   • Диалог: конверт → телефон → подтверждение")
    print("   • Данные сохраняются автоматически")
    print("-"*60)
    
    # Бесконечный цикл
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Система остановлена")

if __name__ == '__main__':
    main()