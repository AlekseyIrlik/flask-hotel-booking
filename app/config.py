"""
Конфигурация приложения.
"""

import os
from datetime import timedelta

# Определяем базовую директорию проекта
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    """Базовая конфигурация."""
    # Безопасность
    SECRET_KEY = os.environ.get(
        'SECRET_KEY', 'dev-secret-key-change-in-production')

    # База данных SQLite - исправленный путь
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "instance", "hotel_booking.db")}'



    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # CSRF защита
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('CSRF_SECRET_KEY', 'csrf-secret-key')

    # Настройки сессии
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)

    # Настройки загрузки файлов
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  

    # Режим отладки
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
