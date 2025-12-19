from app import create_app
import sys
import os

# Добавляем путь к проекту
path = '/home/yourusername/flask-hotel'
if path not in sys.path:
    sys.path.append(path)

# Импортируем приложение

application = create_app()

if __name__ == '__main__':
    application.run()
