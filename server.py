#!/usr/bin/env python3
"""
Сервер для Mini-App Kayo Bot
Обрабатывает сохранение анкет через веб-интерфейс
"""

import json
import logging
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import sqlite3
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Путь к базе данных
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'bot', 'data', 'kayo.db')

class ProfileHandler(BaseHTTPRequestHandler):
    """Обработчик запросов для сохранения анкет"""
    
    def do_GET(self):
        """Обслуживание статических файлов"""
        if self.path == '/' or self.path == '/index.html':
            self.serve_file('index.html', 'text/html')
        elif self.path.endswith('.css'):
            self.serve_file(self.path[1:], 'text/css')
        elif self.path.endswith('.js'):
            self.serve_file(self.path[1:], 'application/javascript')
        else:
            self.send_error(404, 'File not found')
    
    def do_POST(self):
        """Обработка POST запросов"""
        if self.path == '/save_profile':
            self.save_profile()
        else:
            self.send_error(404, 'Endpoint not found')
    
    def serve_file(self, filename, content_type):
        """Отправка статического файла"""
        try:
            with open(filename, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, 'File not found')
    
    def save_profile(self):
        """Сохранение анкеты в базу данных"""
        try:
            # Получаем данные из запроса
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            user_id = data.get('user_id')
            username = data.get('username')
            
            if not user_id:
                self.send_error(400, 'User ID is required')
                return
            
            # Подключаемся к базе данных
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            # Создаем таблицу, если не существует
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id INTEGER PRIMARY KEY,
                    fursona_name TEXT,
                    species TEXT,
                    birth_date TEXT,
                    age INTEGER,
                    orientation TEXT,
                    city TEXT,
                    reference_photo TEXT,
                    looking_for TEXT,
                    personality_type TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Сохраняем анкету
            cursor.execute('''
                INSERT OR REPLACE INTO user_profiles 
                (user_id, fursona_name, species, birth_date, age, orientation, city, reference_photo, looking_for, personality_type, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                data.get('fursona_name'),
                data.get('species'),
                data.get('birth_date'),
                data.get('age'),
                data.get('orientation'),
                data.get('city'),
                data.get('reference_photo'),
                data.get('looking_for'),
                data.get('personality_type'),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Анкета сохранена для пользователя {user_id} ({username})")
            
            # Отправляем успешный ответ
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'success'}).encode('utf-8'))
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении анкеты: {e}")
            self.send_error(500, f'Internal server error: {e}')
    
    def log_message(self, format, *args):
        """Логирование запросов"""
        logger.info(f"{self.address_string()} - {format % args}")

def run_server(port=8080):
    """Запуск сервера"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ProfileHandler)
    logger.info(f"Сервер запущен на порту {port}")
    logger.info(f"Откройте http://localhost:{port} в браузере")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server()