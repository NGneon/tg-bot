import os
import json
import time
from datetime import datetime
import sqlite3
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

# ==================== НАСТРОЙКИ ====================
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8086950668:AAFPUcf3FINRtaHt9mtGJXfjdf5loOZwlTo')
PORT = int(os.environ.get('PORT', 10000))
DB_FILE = "/tmp/bot_data.db"

# ==================== БАЗА ДАННЫХ ====================
def init_db():
    """Создаем простую базу данных"""
    try:
        print(f"📁 Создаю базу данных: {DB_FILE}")
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Таблица для действий пользователей
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_actions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_name TEXT,
            envelope TEXT NOT NULL,
            phone TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ База данных создана в: {DB_FILE}")
        
        # Проверяем
        if os.path.exists(DB_FILE):
            print(f"📊 Размер файла: {os.path.getsize(DB_FILE)} байт")
        else:
            print("❌ Файл не создан!")
            
        return True
    except Exception as e:
        print(f"❌ Ошибка создания БД: {e}")
        return False

def save_to_db(user_id, user_name, envelope, phone):
    """Сохраняем данные в базу"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor.execute(
            "INSERT INTO user_actions (user_id, user_name, envelope, phone, timestamp) VALUES (?, ?, ?, ?, ?)",
            (user_id, user_name, envelope, phone, timestamp)
        )
        
        conn.commit()
        conn.close()
        
        # ВЫВОДИМ В КОНСОЛЬ ДЛЯ ПРОВЕРКИ
        print(f"\n" + "="*60)
        print(f"✅ ДАННЫЕ СОХРАНЕНЫ В БАЗУ!")
        print(f"   👤 Пользователь: {user_name} (ID: {user_id})")
        print(f"   📦 Номер конверта: {envelope}")
        print(f"   📱 Номер телефона: {phone}")
        print(f"   🕐 Время: {timestamp}")
        print("="*60)
        
        # Показываем статистику
        show_db_stats()
        
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения в БД: {e}")
        return False

def show_db_stats():
    """Показываем статистику базы данных"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM user_actions")
        count = cursor.fetchone()[0]
        
        if count > 0:
            cursor.execute("SELECT * FROM user_actions ORDER BY timestamp DESC LIMIT 3")
            rows = cursor.fetchall()
            
            print(f"\n📊 В БАЗЕ ДАННЫХ: {count} записей")
            print("📋 Последние записи:")
            for row in rows:
                print(f"   👤 {row[2]}: конверт {row[3]}, тел. {row[4]}, время {row[5]}")
        else:
            print(f"\n📊 База данных пуста")
        
        conn.close()
    except Exception as e:
        print(f"❌ Ошибка чтения статистики: {e}")

# ==================== ПРОСТОЙ ВЕБ-СЕРВЕР ====================
class BotHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Обработка GET запросов для проверки работы"""
        if self.path == '/':
            # Главная страница
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>🤖 Telegram Bot Status</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .status { color: green; font-weight: bold; }
                    .time { color: #666; }
                </style>
            </head>
            <body>
                <h1>🤖 Telegram Bot работает!</h1>
                <p class="status">✅ Статус: Активен</p>
                <p class="time">🕐 Время сервера: ''' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '''</p>
                <p>📊 База данных: ''' + DB_FILE + '''</p>
            </body>
            </html>
            '''
            self.wfile.write(html.encode('utf-8'))
            
        elif self.path == '/status':
            # JSON статус
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            status = {
                'status': 'running',
                'timestamp': datetime.now().isoformat(),
                'database': DB_FILE,
                'bot_token_set': BOT_TOKEN != 'ВАШ_ТОКЕН_БОТА'
            }
            self.wfile.write(json.dumps(status).encode('utf-8'))
            
        elif self.path == '/db':
            # Просмотр базы данных
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            try:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM user_actions ORDER BY timestamp DESC LIMIT 50")
                rows = cursor.fetchall()
                conn.close()
                
                html = f'''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>📊 База данных бота</title>
                    <style>
                        body {{ font-family: Arial, sans-serif; margin: 20px; }}
                        table {{ border-collapse: collapse; width: 100%; }}
                        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                        th {{ background-color: #f2f2f2; }}
                        tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    </style>
                </head>
                <body>
                    <h1>📊 База данных бота</h1>
                    <p>Всего записей: {len(rows)}</p>
                    <table>
                        <tr>
                            <th>ID</th>
                            <th>User ID</th>
                            <th>Имя</th>
                            <th>Конверт</th>
                            <th>Телефон</th>
                            <th>Время</th>
                        </tr>
                '''
                
                for row in rows:
                    html += f'''
                    <tr>
                        <td>{row[0]}</td>
                        <td>{row[1]}</td>
                        <td>{row[2] or 'Нет имени'}</td>
                        <td>{row[3]}</td>
                        <td>{row[4]}</td>
                        <td>{row[5]}</td>
                    </tr>
                    '''
                
                html += '''
                    </table>
                    <p><a href="/">← Назад</a></p>
                </body>
                </html>
                '''
                
                self.wfile.write(html.encode('utf-8'))
            except Exception as e:
                self.wfile.write(f"Ошибка: {e}".encode('utf-8'))
                
        else:
            self.send_error(404)

def start_web_server():
    """Запускаем веб-сервер"""
    try:
        server = HTTPServer(('0.0.0.0', PORT), BotHandler)
        print(f"🌐 Веб-сервер запущен на порту {PORT}")
        print(f"   Статус: http://ваш-домен.onrender.com/")
        print(f"   База данных: http://ваш-домен.onrender.com/db")
        server.serve_forever()
    except Exception as e:
        print(f"❌ Ошибка веб-сервера: {e}")

# ==================== МОК-ТЕСТ БОТА ====================
# Вместо реального Telegram API будем имитировать работу
def simulate_bot():
    """Имитируем работу бота для тестирования"""
    print("\n🤖 Имитация работы Telegram бота...")
    print("   (Для теста можно 'сохранять' данные)")
    
    test_counter = 1
    
    while True:
        # Каждые 30 секунд имитируем "сохранение данных"
        time.sleep(30)
        
        # Тестовые данные
        user_id = 1000000 + test_counter
        user_name = f"Тестовый пользователь {test_counter}"
        envelope = str(100 + test_counter)
        phone = f"+7999000{test_counter:04d}"
        
        # Сохраняем в БД
        save_to_db(user_id, user_name, envelope, phone)
        
        test_counter += 1
        
        if test_counter > 5:  # Ограничим тест
            print("\n✅ Тест завершен. Бот работает!")
            print("📊 Все данные сохраняются в базу")
            break

# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================
def main():
    """Запуск приложения"""
    print("="*60)
    print("🚀 TELEGRAM BOT + DATABASE TEST")
    print("="*60)
    print(f"🕐 Запущено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Рабочая папка: {os.getcwd()}")
    print(f"🌐 Порт: {PORT}")
    
    # Проверяем токен
    if BOT_TOKEN == 'ВАШ_ТОКЕН_БОТА':
        print("⚠️ ВНИМАНИЕ: Используйте тестовый токен")
        print("   Для реального бота замените 'ВАШ_ТОКЕН_БОТА'")
    else:
        print(f"✅ Токен установлен: {BOT_TOKEN[:10]}...")
    
    # Инициализируем базу данных
    print("\n🗄️ Настраиваю базу данных...")
    init_db()
    
    # Запускаем веб-сервер в отдельном потоке
    print("\n🌐 Запускаю веб-сервер...")
    web_thread = threading.Thread(target=start_web_server, daemon=True)
    web_thread.start()
    
    # Запускаем имитацию бота в отдельном потоке
    print("\n🤖 Запускаю имитацию работы бота...")
    bot_thread = threading.Thread(target=simulate_bot, daemon=True)
    bot_thread.start()
    
    print("\n" + "="*60)
    print("✅ СИСТЕМА ЗАПУЩЕНА!")
    print("="*60)
    print("📊 ДЛЯ ПРОСМОТРА ДАННЫХ:")
    print(f"   1. Откройте: http://ваш-домен.onrender.com/")
    print(f"   2. Посмотрите базу: http://ваш-домен.onrender.com/db")
    print(f"   3. JSON статус: http://ваш-домен.onrender.com/status")
    print("\n📝 В консоли будут появляться данные при 'сохранении'")
    print("-"*60)
    
    # Бесконечный цикл для поддержания работы
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Приложение остановлено")
        show_db_stats()

if __name__ == '__main__':
    main()